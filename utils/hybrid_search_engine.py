"""Hybrid Search Engine: PDF Documents + Web Search + Answer Generation"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .pdf_document_processor import PDFDocumentProcessor
from llm.gemini_service import get_gemini_service

class HybridSearchEngine:
    """Hybrid search engine combining PDF documents and web search with AI-powered answer generation"""

    def __init__(self):
        """Initialize hybrid search engine"""
        self.logger = logging.getLogger(__name__)

        # Initialize PDF processor
        self.pdf_processor = PDFDocumentProcessor()

        # Initialize Gemini service for answer generation
        self.gemini_service = get_gemini_service()

        # Ensure PDF index is built
        self._ensure_pdf_index()

    def _ensure_pdf_index(self):
        """Ensure PDF index is built and up to date"""
        try:
            stats = self.pdf_processor.get_index_stats()
            if stats["total_chunks"] == 0:
                self.logger.info("Building PDF index for the first time...")
                self.pdf_processor.process_all_pdfs()
            else:
                self.logger.info(f"PDF index loaded with {stats['total_chunks']} chunks from {stats['total_files']} files")
        except Exception as e:
            self.logger.error(f"Error ensuring PDF index: {e}")

    def search_pdfs(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search PDF documents

        Args:
            query: Search query
            top_k: Number of top results to return

        Returns:
            List of PDF search results
        """
        try:
            results = self.pdf_processor.search(query, top_k=top_k, min_score=0.3)

            # Format results for consistency
            formatted_results = []
            for result in results:
                formatted_result = {
                    "type": "pdf",
                    "title": result["metadata"].get("filename", "Unknown PDF"),
                    "content": result["content"],
                    "score": result["score"],
                    "source": f"PDF: {result['metadata'].get('filename', 'Unknown')}",
                    "metadata": result["metadata"]
                }
                formatted_results.append(formatted_result)

            return formatted_results

        except Exception as e:
            self.logger.error(f"Error searching PDFs: {e}")
            return []

    def search_web(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search web using WebSearch tool

        Args:
            query: Search query
            max_results: Maximum number of web results

        Returns:
            List of web search results
        """
        try:
            # Import WebSearch here to avoid circular imports
            from utils.web_search_client import WebSearchClient

            web_client = WebSearchClient()
            results = web_client.search(query, max_results=max_results)

            # Format results for consistency
            formatted_results = []
            for result in results:
                formatted_result = {
                    "type": "web",
                    "title": result.get("title", "Web Result"),
                    "content": result.get("content", result.get("snippet", "")),
                    "score": result.get("relevance_score", 0.5),
                    "source": f"Web: {result.get('url', 'Unknown URL')}",
                    "url": result.get("url"),
                    "metadata": {
                        "url": result.get("url"),
                        "publish_date": result.get("date_published")
                    }
                }
                formatted_results.append(formatted_result)

            return formatted_results

        except Exception as e:
            self.logger.error(f"Error searching web: {e}")
            return []

    def hybrid_search(self, query: str, pdf_results: int = 5,
                     web_results: int = 3) -> Dict[str, Any]:
        """
        Perform hybrid search combining PDF and web results

        Args:
            query: Search query
            pdf_results: Number of PDF results to fetch
            web_results: Number of web results to fetch

        Returns:
            Combined search results with metadata
        """
        self.logger.info(f"Performing hybrid search for: {query}")

        search_results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "pdf_results": [],
            "web_results": [],
            "combined_results": [],
            "search_stats": {}
        }

        try:
            # Perform searches in parallel
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit search tasks
                pdf_future = executor.submit(self.search_pdfs, query, pdf_results)
                web_future = executor.submit(self.search_web, query, web_results)

                # Get results
                search_results["pdf_results"] = pdf_future.result()
                search_results["web_results"] = web_future.result()

            # Combine and rank results
            all_results = search_results["pdf_results"] + search_results["web_results"]

            # Sort by score (descending)
            all_results.sort(key=lambda x: x["score"], reverse=True)
            search_results["combined_results"] = all_results

            # Generate search statistics
            search_results["search_stats"] = {
                "total_pdf_results": len(search_results["pdf_results"]),
                "total_web_results": len(search_results["web_results"]),
                "total_combined_results": len(all_results),
                "avg_pdf_score": sum(r["score"] for r in search_results["pdf_results"]) / max(len(search_results["pdf_results"]), 1),
                "avg_web_score": sum(r["score"] for r in search_results["web_results"]) / max(len(search_results["web_results"]), 1)
            }

            self.logger.info(f"Hybrid search completed: {search_results['search_stats']['total_combined_results']} total results")

        except Exception as e:
            self.logger.error(f"Error in hybrid search: {e}")
            search_results["error"] = str(e)

        return search_results

    def generate_answer(self, query: str, search_results: List[Dict[str, Any]],
                       max_context_length: int = 4000) -> Dict[str, Any]:
        """
        Generate AI-powered answer based on search results

        Args:
            query: Original user query
            search_results: Combined search results from hybrid search
            max_context_length: Maximum length of context to send to AI

        Returns:
            Generated answer with sources and metadata
        """
        try:
            if not search_results:
                return {
                    "answer": "죄송합니다. 검색 결과를 찾을 수 없어 답변을 생성할 수 없습니다.",
                    "sources": [],
                    "confidence": 0.0
                }

            # Prepare context from search results
            context_parts = []
            sources = []

            for i, result in enumerate(search_results[:10]):  # Use top 10 results
                context_part = f"[출처 {i+1}] {result['source']}\n{result['content'][:500]}...\n"

                # Check context length
                potential_context = "\n".join(context_parts + [context_part])
                if len(potential_context) > max_context_length:
                    break

                context_parts.append(context_part)
                sources.append({
                    "index": i + 1,
                    "title": result["title"],
                    "source": result["source"],
                    "type": result["type"],
                    "score": result["score"]
                })

            context = "\n".join(context_parts)

            # Generate answer using Gemini
            prompt = self._create_answer_prompt(query, context)

            answer_response = self.gemini_service.generate_response(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.3
            )

            if answer_response.get("success"):
                answer = answer_response["response"]
                confidence = min(0.9, max(0.3, sum(r["score"] for r in search_results[:5]) / 5))
            else:
                answer = "죄송합니다. 답변 생성 중 오류가 발생했습니다."
                confidence = 0.0

            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "context_used": len(context_parts),
                "query": query
            }

        except Exception as e:
            self.logger.error(f"Error generating answer: {e}")
            return {
                "answer": f"답변 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "confidence": 0.0
            }

    def _create_answer_prompt(self, query: str, context: str) -> str:
        """Create prompt for answer generation"""
        return f"""당신은 서울 상권 분석 및 창업 지원 전문가입니다.
주어진 문서들과 웹 검색 결과를 바탕으로 사용자의 질문에 정확하고 도움이 되는 답변을 제공해주세요.

사용자 질문: {query}

관련 자료:
{context}

답변 작성 가이드라인:
1. 주어진 자료를 바탕으로 정확한 정보를 제공하세요
2. 구체적인 수치, 날짜, 프로그램명 등이 있다면 명시하세요
3. 관련 출처를 [출처 번호] 형태로 인용하세요
4. 만약 충분한 정보가 없다면 솔직히 말씀해주세요
5. 창업 지원이나 상권 분석과 관련된 실용적인 조언을 포함하세요
6. 한국어로 자연스럽고 이해하기 쉽게 작성하세요

답변:"""

    def search_and_answer(self, query: str, pdf_results: int = 5,
                         web_results: int = 3) -> Dict[str, Any]:
        """
        Complete search and answer pipeline

        Args:
            query: User query
            pdf_results: Number of PDF results to fetch
            web_results: Number of web results to fetch

        Returns:
            Complete response with search results and generated answer
        """
        # Perform hybrid search
        search_data = self.hybrid_search(query, pdf_results, web_results)

        # Generate answer
        answer_data = self.generate_answer(query, search_data["combined_results"])

        # Combine results
        complete_response = {
            "success": True,
            "query": query,
            "timestamp": search_data["timestamp"],
            "answer": answer_data["answer"],
            "confidence": answer_data["confidence"],
            "sources": answer_data["sources"],
            "search_results": {
                "pdf_results": search_data["pdf_results"],
                "web_results": search_data["web_results"],
                "stats": search_data["search_stats"]
            },
            "metadata": {
                "context_used": answer_data.get("context_used", 0),
                "total_sources": len(answer_data["sources"])
            }
        }

        return complete_response

    def rebuild_pdf_index(self) -> Dict[str, Any]:
        """
        Rebuild PDF index from scratch

        Returns:
            Status of index rebuild operation
        """
        try:
            self.logger.info("Rebuilding PDF index...")
            self.pdf_processor.process_all_pdfs(force_reindex=True)

            stats = self.pdf_processor.get_index_stats()

            return {
                "success": True,
                "message": "PDF index rebuilt successfully",
                "stats": stats
            }

        except Exception as e:
            self.logger.error(f"Error rebuilding PDF index: {e}")
            return {
                "success": False,
                "message": f"Error rebuilding PDF index: {str(e)}"
            }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get status of the hybrid search system

        Returns:
            System status information
        """
        try:
            pdf_stats = self.pdf_processor.get_index_stats()

            status = {
                "pdf_processor": {
                    "status": "ready" if pdf_stats["index_exists"] else "not_ready",
                    "total_chunks": pdf_stats["total_chunks"],
                    "total_files": pdf_stats["total_files"],
                    "model_name": pdf_stats["model_name"]
                },
                "gemini_service": {
                    "status": "ready" if self.gemini_service else "not_ready"
                },
                "overall_status": "ready" if pdf_stats["index_exists"] and self.gemini_service else "not_ready"
            }

            return status

        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {
                "overall_status": "error",
                "error": str(e)
            }

# Global instance
_hybrid_search_engine = None

def get_hybrid_search_engine() -> HybridSearchEngine:
    """Get singleton instance of hybrid search engine"""
    global _hybrid_search_engine
    if _hybrid_search_engine is None:
        _hybrid_search_engine = HybridSearchEngine()
    return _hybrid_search_engine