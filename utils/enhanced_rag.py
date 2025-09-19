"""
강화된 RAG 시스템 - PDF 우선 검색 및 웹 검색 결합
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from dotenv import load_dotenv

# PDF 처리 라이브러리
try:
    import PyPDF2
    import pdfplumber
except ImportError:
    PyPDF2 = None
    pdfplumber = None

# 검색 및 임베딩 라이브러리
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import chromadb
except ImportError:
    SentenceTransformer = None
    np = None
    cosine_similarity = None
    chromadb = None

from .web_search import get_web_search_service

load_dotenv()
logger = logging.getLogger(__name__)

class EnhancedRAGService:
    def __init__(self):
        self.pdf_dir = Path("data/pdf")
        self.index_dir = Path("models/artifacts")
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # 임베딩 모델 초기화
        try:
            if SentenceTransformer:
                self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            else:
                self.embedding_model = None
                logger.warning("SentenceTransformer not available")
        except Exception as e:
            logger.warning(f"임베딩 모델 로드 실패: {e}")
            self.embedding_model = None

        # 웹 검색 서비스 초기화
        self.web_search = get_web_search_service()

        # PDF 문서 캐시
        self.pdf_cache = {}
        self.indexed_pdfs = set()

    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """PDF에서 텍스트 추출"""
        try:
            chunks = []

            if pdfplumber:
                # pdfplumber 사용 (더 정확한 텍스트 추출)
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        text = page.extract_text()
                        if text and text.strip():
                            # 청크 단위로 분할 (1000자 단위)
                            chunk_size = 1000
                            for i in range(0, len(text), chunk_size):
                                chunk_text = text[i:i + chunk_size]
                                if chunk_text.strip():
                                    chunks.append({
                                        'text': chunk_text.strip(),
                                        'source': os.path.basename(pdf_path),
                                        'page': page_num,
                                        'chunk_id': len(chunks)
                                    })

            elif PyPDF2:
                # PyPDF2 폴백
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        text = page.extract_text()
                        if text and text.strip():
                            chunk_size = 1000
                            for i in range(0, len(text), chunk_size):
                                chunk_text = text[i:i + chunk_size]
                                if chunk_text.strip():
                                    chunks.append({
                                        'text': chunk_text.strip(),
                                        'source': os.path.basename(pdf_path),
                                        'page': page_num,
                                        'chunk_id': len(chunks)
                                    })

            logger.info(f"PDF 텍스트 추출 완료: {pdf_path}, {len(chunks)}개 청크")
            return chunks

        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패: {pdf_path}, {str(e)}")
            return []

    def index_pdf_documents(self, pdf_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """PDF 문서들을 인덱싱"""
        try:
            if pdf_paths is None:
                # data/pdf 폴더의 모든 PDF 파일
                pdf_paths = list(self.pdf_dir.glob("*.pdf"))

            all_chunks = []
            indexed_files = 0

            for pdf_path in pdf_paths:
                pdf_path_str = str(pdf_path)
                if pdf_path_str not in self.indexed_pdfs:
                    chunks = self.extract_text_from_pdf(pdf_path_str)
                    if chunks:
                        all_chunks.extend(chunks)
                        self.indexed_pdfs.add(pdf_path_str)
                        indexed_files += 1

            # 청크를 캐시에 저장
            self.pdf_cache = {chunk['chunk_id']: chunk for chunk in all_chunks}

            return {
                'status': 'success',
                'total_files': len(pdf_paths),
                'indexed_files': indexed_files,
                'total_chunks': len(all_chunks),
                'message': f'{indexed_files}개 파일, {len(all_chunks)}개 청크 인덱싱 완료'
            }

        except Exception as e:
            logger.error(f"PDF 인덱싱 실패: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def search_pdf_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """PDF 문서에서 관련 정보 검색"""
        try:
            if not self.pdf_cache:
                logger.warning("인덱싱된 PDF가 없습니다")
                return []

            chunks = list(self.pdf_cache.values())
            chunk_texts = [chunk['text'] for chunk in chunks]

            # 단순 키워드 매칭으로 폴백
            query_lower = query.lower()
            scored_chunks = []

            for chunk in chunks:
                text_lower = chunk['text'].lower()
                score = 0

                # 키워드 포함 점수 계산
                query_words = query_lower.split()
                for word in query_words:
                    if word in text_lower:
                        score += text_lower.count(word) / len(text_lower)

                if score > 0:
                    scored_chunks.append({
                        'text': chunk['text'],
                        'source': chunk['source'],
                        'page': chunk['page'],
                        'score': score,
                        'search_type': 'pdf'
                    })

            # 점수 순으로 정렬
            scored_chunks.sort(key=lambda x: x['score'], reverse=True)

            results = scored_chunks[:top_k]
            logger.info(f"PDF 검색 완료: {len(results)}개 결과")
            return results

        except Exception as e:
            logger.error(f"PDF 검색 실패: {str(e)}")
            return []

    def search_specific_pdf(self, pdf_path: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """특정 PDF 파일에서만 검색"""
        try:
            # 해당 PDF 파일만 인덱싱
            chunks = self.extract_text_from_pdf(pdf_path)
            if not chunks:
                return []

            query_lower = query.lower()
            scored_chunks = []

            for chunk in chunks:
                text_lower = chunk['text'].lower()
                score = 0

                # 키워드 포함 점수 계산
                query_words = query_lower.split()
                for word in query_words:
                    if word in text_lower:
                        score += text_lower.count(word) / len(text_lower)

                if score > 0:
                    scored_chunks.append({
                        'text': chunk['text'],
                        'source': chunk['source'],
                        'page': chunk['page'],
                        'score': score,
                        'search_type': 'specific_pdf'
                    })

            # 점수 순으로 정렬
            scored_chunks.sort(key=lambda x: x['score'], reverse=True)

            results = scored_chunks[:top_k]
            logger.info(f"특정 PDF 검색 완료: {pdf_path}, {len(results)}개 결과")
            return results

        except Exception as e:
            logger.error(f"특정 PDF 검색 실패: {str(e)}")
            return []

    def hybrid_search(self, query: str, top_k: int = 10, pdf_threshold: float = 0.1) -> List[Dict[str, Any]]:
        """PDF 우선 검색 + 웹 검색 결합"""
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided to hybrid search")
                return []

            # 1단계: PDF 문서에서 검색 (안전한 호출)
            pdf_results = []
            try:
                pdf_results = self.search_pdf_documents(query, top_k)
            except Exception as e:
                logger.warning(f"PDF search failed in hybrid: {str(e)}")

            # PDF 결과가 충분하면 웹 검색 안 함
            if len(pdf_results) >= 3 and any(result.get('score', 0) > pdf_threshold for result in pdf_results):
                logger.info("PDF에서 충분한 결과 발견, 웹 검색 생략")
                return pdf_results[:top_k]

            # 2단계: PDF 결과가 부족하면 웹 검색 수행 (안전한 호출)
            logger.info("PDF 결과 부족, 웹 검색 실행")
            web_results = []
            try:
                web_results = self.web_search.hybrid_web_search(query, max_results=max(1, top_k//2))
            except Exception as e:
                logger.warning(f"Web search failed in hybrid: {str(e)}")

            # 웹 검색 결과 형식 맞추기 (안전한 처리)
            formatted_web_results = []
            for result in web_results:
                try:
                    formatted_result = {
                        'text': str(result.get('content', '')),
                        'source': str(result.get('url', '')),
                        'page': 'web',
                        'score': float(result.get('score', 0.5)),
                        'search_type': 'web',
                        'title': str(result.get('title', ''))
                    }
                    formatted_web_results.append(formatted_result)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping malformed web result: {e}")
                    continue

            # PDF와 웹 결과 결합 (안전한 처리)
            all_results = pdf_results + formatted_web_results

            # 안전한 정렬
            try:
                all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            except Exception as e:
                logger.warning(f"Failed to sort hybrid results: {str(e)}")

            final_results = all_results[:top_k]
            logger.info(f"하이브리드 검색 완료: PDF {len(pdf_results)}개 + 웹 {len(formatted_web_results)}개 = 총 {len(final_results)}개")
            return final_results

        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {str(e)}")
            # 실패 시 빈 리스트 대신 기본 더미 결과 반환
            return [{
                'text': f"'{query}'에 대한 검색 중 오류가 발생했습니다.",
                'source': 'error',
                'page': 'error',
                'score': 0.1,
                'search_type': 'error'
            }]

def get_enhanced_rag_service() -> EnhancedRAGService:
    """강화된 RAG 서비스 인스턴스 반환"""
    return EnhancedRAGService()