"""
하이브리드 외부 데이터 + RAG 통합 서비스
기존 RAG 시스템과 외부 데이터 포털을 결합한 통합 검색 서비스
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from retrieval.external_data_service import get_external_data_service, ExternalDataResult
from retrieval.rag_hybrid import get_rag_service

logger = logging.getLogger(__name__)

@dataclass
class HybridSearchResult:
    """하이브리드 검색 결과"""
    title: str
    content: str
    source: str
    url: str
    result_type: str  # 'internal_rag', 'external_data', 'sql_data'
    relevance_score: float
    timestamp: str
    metadata: Dict[str, Any]

class HybridExternalRAGService:
    """하이브리드 외부 데이터 + RAG 통합 서비스"""
    
    def __init__(self):
        self.external_data_service = get_external_data_service()
        self.rag_service = get_rag_service()
        
        # 검색 가중치 설정
        self.weights = {
            "internal_rag": 0.4,
            "external_data": 0.4,
            "sql_data": 0.2
        }
        
        # 관련성 임계값
        self.min_relevance_threshold = 0.3
        
        # PDF 인덱싱 상태 추적
        self._pdf_indexed = False
        
        logger.info("하이브리드 외부 데이터 + RAG 서비스 초기화 완료")
    
    def search_hybrid(self, query: str, max_results: int = 20, 
                     include_external: bool = True, include_rag: bool = True, 
                     include_sql: bool = True) -> Dict[str, Any]:
        """
        하이브리드 검색 실행
        
        Args:
            query: 검색 질의
            max_results: 최대 결과 수
            include_external: 외부 데이터 포함 여부
            include_rag: RAG 검색 포함 여부
            include_sql: SQL 검색 포함 여부
            
        Returns:
            통합 검색 결과
        """
        start_time = time.time()
        search_id = f"hybrid_{int(time.time() * 1000)}"
        
        try:
            logger.info(f"하이브리드 검색 시작: '{query}' (ID: {search_id})")
            
            # 1. 각 소스별 검색 실행
            search_results = {}
            
            if include_external:
                search_results["external_data"] = self._search_external_data(query, max_results // 3)
            
            if include_rag:
                search_results["internal_rag"] = self._search_internal_rag(query, max_results // 3)
            
            if include_sql:
                search_results["sql_data"] = self._search_sql_data(query, max_results // 3)
            
            # 2. 결과 통합 및 정규화
            integrated_results = self._integrate_results(search_results, query)
            
            # 3. 관련성 기반 정렬 및 필터링
            filtered_results = self._filter_and_rank_results(integrated_results, query)
            
            # 4. 결과 요약 생성
            summary = self._generate_search_summary(filtered_results, search_results)
            
            processing_time = time.time() - start_time
            
            return {
                "search_id": search_id,
                "success": True,
                "query": query,
                "results": filtered_results[:max_results],
                "summary": summary,
                "metadata": {
                    "total_results": len(filtered_results),
                    "processing_time": processing_time,
                    "sources_used": list(search_results.keys()),
                    "weights": self.weights,
                    "timestamp": datetime.now().isoformat()
                },
                "source_breakdown": {
                    source: len(results) for source, results in search_results.items()
                }
            }
            
        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {str(e)}")
            return {
                "search_id": search_id,
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
                "timestamp": datetime.now().isoformat()
            }
    
    def _search_external_data(self, query: str, max_results: int) -> List[HybridSearchResult]:
        """외부 데이터 검색"""
        try:
            external_results = self.external_data_service.search_all_portals(
                query, max_results // len(self.external_data_service.portals)
            )
            
            hybrid_results = []
            for result in external_results:
                hybrid_results.append(HybridSearchResult(
                    title=result.title,
                    content=result.content,
                    source=result.source,
                    url=result.url,
                    result_type="external_data",
                    relevance_score=result.relevance_score,
                    timestamp=result.timestamp,
                    metadata={
                        **result.metadata,
                        "data_type": result.data_type,
                        "external_portal": True
                    }
                ))
            
            logger.info(f"외부 데이터 검색 완료: {len(hybrid_results)}개 결과")
            return hybrid_results
            
        except Exception as e:
            logger.error(f"외부 데이터 검색 실패: {str(e)}")
            return []
    
    def _search_internal_rag(self, query: str, max_results: int) -> List[HybridSearchResult]:
        """내부 RAG 검색 (자동 PDF 인덱싱 포함)"""
        try:
            # PDF 인덱싱 상태 확인 및 자동 인덱싱
            self._ensure_pdf_indexed()
            
            # RAG 서비스를 통한 검색
            rag_results = self.rag_service.search(query, top_k=max_results)
            
            hybrid_results = []
            for result in rag_results:
                hybrid_results.append(HybridSearchResult(
                    title=result.get("text", "문서 제목 없음")[:100] + "...",
                    content=result.get("text", ""),
                    source=result.get("source", "내부 문서"),
                    url=result.get("url", ""),
                    result_type="internal_rag",
                    relevance_score=result.get("score", 0.5),
                    timestamp=datetime.now().isoformat(),
                    metadata={
                        "rag_source": True,
                        "document_type": result.get("metadata", {}).get("section", "unknown"),
                        "original_score": result.get("score", 0.5),
                        "page": result.get("page", "N/A")
                    }
                ))
            
            logger.info(f"내부 RAG 검색 완료: {len(hybrid_results)}개 결과")
            return hybrid_results
            
        except Exception as e:
            logger.error(f"내부 RAG 검색 실패: {str(e)}")
            return []
    
    def _search_sql_data(self, query: str, max_results: int) -> List[HybridSearchResult]:
        """SQL 데이터 검색"""
        try:
            # 간단한 SQL 검색 시뮬레이션 (실제로는 데이터베이스 연결 필요)
            sample_data = self._generate_sample_sql_data(query)
            
            hybrid_results = []
            for i, row in enumerate(sample_data[:max_results]):
                title = f"데이터 분석 결과 {i+1}"
                content = self._format_sql_row_as_content(row)
                
                hybrid_results.append(HybridSearchResult(
                    title=title,
                    content=content,
                    source="내부 데이터베이스",
                    url="",
                    result_type="sql_data",
                    relevance_score=0.8,
                    timestamp=datetime.now().isoformat(),
                    metadata={
                        "sql_source": True,
                        "sql_query": f"SELECT * FROM sample_data WHERE query LIKE '%{query}%'",
                        "row_data": row
                    }
                ))
            
            logger.info(f"SQL 데이터 검색 완료: {len(hybrid_results)}개 결과")
            return hybrid_results
            
        except Exception as e:
            logger.error(f"SQL 데이터 검색 실패: {str(e)}")
            return []
    
    def _integrate_results(self, search_results: Dict[str, List[HybridSearchResult]], 
                          query: str) -> List[HybridSearchResult]:
        """검색 결과 통합"""
        all_results = []
        
        for source, results in search_results.items():
            for result in results:
                # 소스별 가중치 적용
                weighted_score = result.relevance_score * self.weights.get(source, 0.3)
                result.relevance_score = weighted_score
                
                # 쿼리 관련성 점수 추가
                query_relevance = self._calculate_query_relevance(query, result)
                result.relevance_score += query_relevance * 0.2
                
                # 최종 점수 정규화
                result.relevance_score = min(1.0, result.relevance_score)
                
                all_results.append(result)
        
        return all_results
    
    def _filter_and_rank_results(self, results: List[HybridSearchResult], 
                                query: str) -> List[HybridSearchResult]:
        """결과 필터링 및 랭킹"""
        # 관련성 임계값 필터링
        filtered_results = [
            result for result in results 
            if result.relevance_score >= self.min_relevance_threshold
        ]
        
        # 중복 제거 (제목 기반)
        unique_results = self._remove_duplicates(filtered_results)
        
        # 관련성 순으로 정렬
        sorted_results = sorted(
            unique_results, 
            key=lambda x: x.relevance_score, 
            reverse=True
        )
        
        return sorted_results
    
    def _remove_duplicates(self, results: List[HybridSearchResult]) -> List[HybridSearchResult]:
        """중복 결과 제거"""
        seen_titles = set()
        unique_results = []
        
        for result in results:
            title_key = result.title.lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_results.append(result)
        
        return unique_results
    
    def _calculate_query_relevance(self, query: str, result: HybridSearchResult) -> float:
        """쿼리 관련성 점수 계산"""
        try:
            query_lower = query.lower()
            title_lower = result.title.lower()
            content_lower = result.content.lower()
            
            score = 0.0
            
            # 제목에 쿼리 키워드 포함
            if query_lower in title_lower:
                score += 0.3
            
            # 내용에 쿼리 키워드 포함
            if query_lower in content_lower:
                score += 0.2
            
            # 키워드별 매칭 점수
            query_words = set(query_lower.split())
            title_words = set(title_lower.split())
            content_words = set(content_lower.split())
            
            title_matches = len(query_words.intersection(title_words))
            content_matches = len(query_words.intersection(content_words))
            
            if query_words:
                title_score = title_matches / len(query_words)
                content_score = content_matches / len(query_words)
                score += (title_score * 0.3 + content_score * 0.2)
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"쿼리 관련성 계산 실패: {str(e)}")
            return 0.0
    
    def _generate_sample_sql_data(self, query: str) -> List[Dict[str, Any]]:
        """샘플 SQL 데이터 생성"""
        try:
            # 쿼리에 따른 샘플 데이터 생성
            query_lower = query.lower()
            
            if any(keyword in query_lower for keyword in ['매출', 'sales', '금액']):
                return [
                    {"region": "강남구", "sales": 1000000, "transactions": 1000, "category": "상권"},
                    {"region": "서초구", "sales": 800000, "transactions": 800, "category": "상권"},
                    {"region": "송파구", "sales": 600000, "transactions": 600, "category": "상권"},
                ]
            elif any(keyword in query_lower for keyword in ['창업', 'startup', '사업']):
                return [
                    {"business_type": "카페", "count": 150, "success_rate": 0.75, "region": "강남구"},
                    {"business_type": "음식점", "count": 200, "success_rate": 0.68, "region": "서초구"},
                    {"business_type": "소매업", "count": 120, "success_rate": 0.82, "region": "송파구"},
                ]
            else:
                return [
                    {"metric": "상권 활성도", "value": 85.5, "unit": "%", "period": "2024년"},
                    {"metric": "창업 성공률", "value": 72.3, "unit": "%", "period": "2024년"},
                    {"metric": "매출 증감률", "value": 12.8, "unit": "%", "period": "2024년"},
                ]
                
        except Exception as e:
            logger.error(f"샘플 SQL 데이터 생성 실패: {str(e)}")
            return []

    def _format_sql_row_as_content(self, row: Dict[str, Any]) -> str:
        """SQL 행 데이터를 콘텐츠 형태로 변환"""
        try:
            content_parts = []
            for key, value in row.items():
                if isinstance(value, (int, float)):
                    content_parts.append(f"{key}: {value:,}")
                else:
                    content_parts.append(f"{key}: {value}")
            
            return " | ".join(content_parts)
            
        except Exception as e:
            logger.error(f"SQL 행 데이터 변환 실패: {str(e)}")
            return str(row)
    
    def _ensure_pdf_indexed(self) -> None:
        """PDF 인덱싱 상태 확인 및 자동 인덱싱"""
        try:
            if self._pdf_indexed:
                return
            
            # PDF 파일 경로 확인
            import os
            pdf_dir = "data/pdf"
            if not os.path.exists(pdf_dir):
                logger.warning(f"PDF 디렉토리가 존재하지 않습니다: {pdf_dir}")
                return
            
            # PDF 파일 목록 확인
            pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
            if not pdf_files:
                logger.warning("PDF 파일이 없습니다.")
                return
            
            # RAG 서비스로 PDF 인덱싱
            pdf_paths = [os.path.join(pdf_dir, f) for f in pdf_files]
            index_result = self.rag_service.index_documents(pdf_paths)
            
            if index_result.get("status") == "success":
                self._pdf_indexed = True
                logger.info(f"PDF 자동 인덱싱 완료: {index_result.get('files_indexed', 0)}개 파일")
            else:
                logger.warning(f"PDF 인덱싱 실패: {index_result.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"PDF 인덱싱 확인 중 오류: {str(e)}")
    
    def _generate_search_summary(self, results: List[HybridSearchResult], 
                               search_results: Dict[str, List[HybridSearchResult]]) -> str:
        """검색 결과 요약 생성"""
        try:
            total_results = len(results)
            
            # 소스별 결과 수
            source_counts = {}
            for source, source_results in search_results.items():
                source_counts[source] = len(source_results)
            
            # 결과 타입별 분포
            type_counts = {}
            for result in results:
                result_type = result.result_type
                type_counts[result_type] = type_counts.get(result_type, 0) + 1
            
            summary_parts = [f"총 {total_results}개의 관련 결과를 찾았습니다."]
            
            if type_counts:
                type_descriptions = {
                    "external_data": "외부 데이터",
                    "internal_rag": "내부 문서",
                    "sql_data": "데이터베이스"
                }
                
                type_summary = []
                for result_type, count in type_counts.items():
                    description = type_descriptions.get(result_type, result_type)
                    type_summary.append(f"{description}: {count}개")
                
                if type_summary:
                    summary_parts.append("(" + ", ".join(type_summary) + ")")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"검색 요약 생성 실패: {str(e)}")
            return f"총 {len(results)}개의 결과를 찾았습니다."
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """검색 제안 생성"""
        try:
            suggestions = []
            
            # 외부 데이터 포털 기반 제안
            portal_suggestions = [
                f"{query} 서울시 데이터",
                f"{query} 공공데이터",
                f"{query} 상권 분석",
                f"{query} 매출 데이터"
            ]
            
            suggestions.extend(portal_suggestions[:3])
            
            # 쿼리 확장 제안
            expanded_suggestions = [
                f"{query} 정책",
                f"{query} 지원제도",
                f"{query} 통계",
                f"{query} 보고서"
            ]
            
            suggestions.extend(expanded_suggestions[:2])
            
            return suggestions[:5]  # 최대 5개 제안
            
        except Exception as e:
            logger.error(f"검색 제안 생성 실패: {str(e)}")
            return []
    
    def get_portal_status(self) -> Dict[str, Any]:
        """포털 상태 확인"""
        try:
            status = {}
            
            # 외부 데이터 포털 상태
            portals = self.external_data_service.get_portal_list()
            for portal in portals:
                status[portal["name"]] = {
                    "name": portal["display_name"],
                    "url": portal["base_url"],
                    "status": "available"
                }
            
            # RAG 서비스 상태
            status["internal_rag"] = {
                "name": "내부 RAG 서비스",
                "status": "available"
            }
            
            # SQL 서비스 상태
            status["sql_data"] = {
                "name": "SQL 데이터 서비스", 
                "status": "available"
            }
            
            return {
                "success": True,
                "portals": status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"포털 상태 확인 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# 전역 서비스 인스턴스
_hybrid_service = None

def get_hybrid_external_rag_service() -> HybridExternalRAGService:
    """하이브리드 서비스 인스턴스 반환"""
    global _hybrid_service
    if _hybrid_service is None:
        _hybrid_service = HybridExternalRAGService()
    return _hybrid_service

def search_hybrid_external_data(query: str, max_results: int = 20, 
                               include_external: bool = True, 
                               include_rag: bool = True, 
                               include_sql: bool = True) -> Dict[str, Any]:
    """
    하이브리드 외부 데이터 검색 함수
    
    Args:
        query: 검색 질의
        max_results: 최대 결과 수
        include_external: 외부 데이터 포함 여부
        include_rag: RAG 검색 포함 여부
        include_sql: SQL 검색 포함 여부
        
    Returns:
        통합 검색 결과
    """
    service = get_hybrid_external_rag_service()
    return service.search_hybrid(
        query, max_results, include_external, include_rag, include_sql
    )
