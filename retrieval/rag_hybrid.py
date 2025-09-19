"""
Hybrid RAG 모듈
PRD TASK1: BM25 + Vector 검색 스텁
"""

import logging
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def index_pdfs(pdf_paths: List[str]) -> Dict[str, Any]:
    """
    PDF 파일들을 인덱싱하는 함수 (스텁)
    
    Args:
        pdf_paths: PDF 파일 경로 리스트
        
    Returns:
        인덱싱 결과 딕셔너리
    """
    try:
        if not pdf_paths:
            return {"status": "error", "message": "PDF 파일이 제공되지 않았습니다."}
        
        indexed_count = 0
        total_chunks = 0
        
        for pdf_path in pdf_paths:
            if os.path.exists(pdf_path):
                # PDF 파일 존재 확인
                file_size = os.path.getsize(pdf_path)
                if file_size > 0:
                    indexed_count += 1
                    # 청킹 시뮬레이션 (실제로는 PDF 파싱 필요)
                    total_chunks += 10  # 가정: PDF당 10개 청크
        
        logger.info(f"PDF 인덱싱 완료: {indexed_count}개 파일, {total_chunks}개 청크")
        
        return {
            "status": "success",
            "files_indexed": indexed_count,
            "total_chunks": total_chunks,
            "index_path": "models/artifacts/vector_index"
        }
        
    except Exception as e:
        logger.error(f"PDF 인덱싱 실패: {str(e)}")
        return {"status": "error", "message": str(e)}

def hybrid_search(query: str, top_k: int = 5, alpha: float = 0.5) -> List[Dict[str, Any]]:
    """
    하이브리드 검색 수행 (BM25 + Vector) (스텁)
    
    Args:
        query: 검색 질의
        top_k: 반환할 결과 수
        alpha: BM25와 Vector의 가중치 (0.5 = 균등)
        
    Returns:
        검색 결과 리스트
    """
    try:
        if not query or len(query.strip()) == 0:
            return []
        
        # 스텁 검색 결과 생성
        mock_results = [
            {
                "text": f"'{query}'에 대한 관련 정보입니다. 이는 서울 상권 분석과 관련된 중요한 데이터입니다.",
                "source": "서울창업정보_2024.pdf",
                "page": 15,
                "url": "https://example.com/seoul-startup-info",
                "score": 0.95,
                "metadata": {
                    "section": "상권 분석",
                    "year": 2024,
                    "region": "강남구"
                }
            },
            {
                "text": f"'{query}'와 관련된 정책 정보가 포함된 문서입니다. 창업 지원 정책과 상권 활성화 방안이 설명되어 있습니다.",
                "source": "서울창업정보_2024.pdf",
                "page": 23,
                "url": "https://example.com/seoul-startup-info",
                "score": 0.87,
                "metadata": {
                    "section": "정책 정보",
                    "year": 2024,
                    "region": "전체"
                }
            },
            {
                "text": f"'{query}'에 대한 통계 데이터와 분석 결과가 포함된 섹션입니다.",
                "source": "서울창업정보_2024.pdf",
                "page": 8,
                "url": "https://example.com/seoul-startup-info",
                "score": 0.82,
                "metadata": {
                    "section": "통계 분석",
                    "year": 2024,
                    "region": "서울시"
                }
            }
        ]
        
        # top_k만큼 반환
        results = mock_results[:top_k]
        
        logger.info(f"하이브리드 검색 완료: '{query}' -> {len(results)}개 결과")
        
        return results
        
    except Exception as e:
        logger.error(f"하이브리드 검색 실패: {str(e)}")
        return []

def get_document_metadata(doc_id: str) -> Optional[Dict[str, Any]]:
    """
    문서 메타데이터 조회 (스텁)

    Args:
        doc_id: 문서 ID

    Returns:
        문서 메타데이터 딕셔너리
    """
    try:
        # 스텁 메타데이터
        return {
            "doc_id": doc_id,
            "title": "서울창업정보 2024",
            "source": "서울시청",
            "url": "https://example.com/seoul-startup-info",
            "published_date": "2024-01-01",
            "file_size": 1024000,
            "page_count": 50,
            "language": "ko"
        }

    except Exception as e:
        logger.error(f"메타데이터 조회 실패: {str(e)}")
        return None

class RAGService:
    """RAG 서비스 클래스"""

    def __init__(self):
        self.indexed_documents = []
        self.vector_index = None

    def index_documents(self, pdf_paths: List[str]) -> Dict[str, Any]:
        """문서 인덱싱"""
        return index_pdfs(pdf_paths)

    def search(self, query: str, top_k: int = 5, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """하이브리드 검색"""
        return hybrid_search(query, top_k, alpha)

    def get_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """메타데이터 조회"""
        return get_document_metadata(doc_id)

def get_rag_service() -> RAGService:
    """
    RAG 서비스 인스턴스 반환

    Returns:
        RAGService 인스턴스
    """
    return RAGService()