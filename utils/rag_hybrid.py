"""
Hybrid RAG (BM25 + Vector) 모듈 (TASK1 스텁)
PRD TASK3에서 FAISS/Chroma + sentence-transformers로 완전 구현 예정
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def index_pdfs(pdf_paths: List[str]) -> Dict[str, Any]:
    """
    PDF 파일들을 인덱싱하는 함수 (스텁)

    Args:
        pdf_paths: PDF 파일 경로 리스트

    Returns:
        인덱싱 결과
    """
    try:
        logger.info(f"PDF 인덱싱 시작: {len(pdf_paths)}개 파일")

        # TASK1 스텁: 파일 존재 확인만 수행
        # TODO: TASK3에서 PDF 파싱, 청킹, 벡터 인덱스 생성 구현

        indexed_count = 0
        for pdf_path in pdf_paths:
            if isinstance(pdf_path, str) and Path(pdf_path).exists():
                indexed_count += 1
            elif hasattr(pdf_path, 'name'):  # Streamlit UploadedFile
                indexed_count += 1

        result = {
            "status": "success",
            "total_files": len(pdf_paths),
            "indexed_files": indexed_count,
            "message": f"{indexed_count}개 파일이 인덱싱되었습니다 (스텁)",
            "chunks_created": indexed_count * 10,  # 가상 청크 수
            "vector_index_size": indexed_count * 100  # 가상 벡터 인덱스 크기
        }

        logger.info(f"PDF 인덱싱 완료 (스텁): {result}")
        return result

    except Exception as e:
        logger.error(f"PDF 인덱싱 실패: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "total_files": len(pdf_paths) if pdf_paths else 0,
            "indexed_files": 0
        }

def hybrid_search(query: str, top_k: int = 5, alpha: float = 0.5) -> List[Dict[str, Any]]:
    """
    Hybrid 검색 (BM25 + Vector) 함수 (스텁)

    Args:
        query: 검색 질의
        top_k: 반환할 결과 수
        alpha: BM25와 Vector 가중치 (0.5 = 동일 가중치)

    Returns:
        검색 결과 리스트
    """
    try:
        logger.info(f"Hybrid 검색 시작: '{query}', top_k={top_k}, alpha={alpha}")

        # TASK1 스텁: 더미 검색 결과 생성
        # TODO: TASK3에서 실제 BM25 + Vector 검색 구현

        dummy_results = []

        if "강남" in query or "창업" in query:
            dummy_results = [
                {
                    "text": "강남구는 서울시에서 창업 지원 프로그램이 가장 활발한 지역 중 하나입니다. 2024년 기준으로 다양한 스타트업 지원 센터가 운영되고 있습니다.",
                    "source": "서울창업지원센터_강남_2024.pdf",
                    "page": 12,
                    "url": "https://seoul-startup.go.kr/gangnam",
                    "score": 0.92,
                    "metadata": {
                        "doc_type": "startup_guide",
                        "year": 2024,
                        "region": "강남구"
                    }
                },
                {
                    "text": "창업 지원금 신청 요건: 1) 서울시 거주자, 2) 사업 경력 3년 이하, 3) 혁신적 아이디어 보유",
                    "source": "창업지원금_신청안내_2024.pdf",
                    "page": 5,
                    "url": "https://seoul-startup.go.kr/funding",
                    "score": 0.85,
                    "metadata": {
                        "doc_type": "funding_guide",
                        "year": 2024
                    }
                },
                {
                    "text": "서울창업허브는 예비창업자와 초기창업자를 위한 원스톱 창업지원 플랫폼입니다.",
                    "source": "서울창업허브_소개_2024.pdf",
                    "page": 1,
                    "url": "https://seoul-startup-hub.com",
                    "score": 0.78,
                    "metadata": {
                        "doc_type": "introduction",
                        "year": 2024
                    }
                }
            ]
        else:
            # 기본 더미 결과
            dummy_results = [
                {
                    "text": f"'{query}'와 관련된 정보를 찾았습니다. 이것은 스텁 결과입니다.",
                    "source": "sample_document.pdf",
                    "page": 1,
                    "url": "https://example.com",
                    "score": 0.75,
                    "metadata": {
                        "doc_type": "general",
                        "year": 2024
                    }
                }
            ]

        # top_k 제한 적용
        results = dummy_results[:top_k]

        logger.info(f"Hybrid 검색 완료 (스텁): {len(results)}개 결과")
        return results

    except Exception as e:
        logger.error(f"Hybrid 검색 실패: {str(e)}")
        return []

def get_index_stats() -> Dict[str, Any]:
    """
    인덱스 통계 정보 조회 (스텁)

    Returns:
        인덱스 통계
    """
    try:
        # 더미 통계 정보
        stats = {
            "total_documents": 50,
            "total_chunks": 500,
            "vector_dimension": 384,
            "bm25_vocabulary_size": 10000,
            "last_updated": "2024-09-18T06:00:00",
            "index_size_mb": 25.6
        }

        logger.info(f"인덱스 통계 조회 완료 (스텁): {stats}")
        return stats

    except Exception as e:
        logger.error(f"인덱스 통계 조회 실패: {str(e)}")
        return {}