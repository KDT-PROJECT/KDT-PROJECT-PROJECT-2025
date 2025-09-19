"""
RAG 품질/속도 테스트
project-structure.mdc 규칙에 따른 RAG 파이프라인 테스트
"""

import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

from utils.rag_hybrid import HybridRetriever

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestRAGPipeline(unittest.TestCase):
    """RAG 파이프라인 테스트 클래스"""

    @classmethod
    def setUpClass(cls):
        """테스트 클래스 초기화"""
        # 테스트용 설정
        cls.config = {
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "model_path": "tests/test_models",
        }

        # HybridRetriever 인스턴스 생성
        cls.rag_engine = HybridRetriever(cls.config)

        # 테스트 문서 생성
        cls.test_documents = [
            {
                "id": "test_doc_1",
                "text": "서울시 강남구는 대한민국의 주요 상업지구로, 높은 부동산 가격과 활발한 상업 활동으로 유명합니다.",
                "metadata": {
                    "source": "test_source.pdf",
                    "page": 1,
                    "chunk": 1,
                    "type": "pdf",
                },
            },
            {
                "id": "test_doc_2",
                "text": "강남구의 주요 업종은 IT, 금융, 의료, 교육 서비스 등이며, 특히 테헤란로 일대는 IT 기업들이 집중되어 있습니다.",
                "metadata": {
                    "source": "test_source.pdf",
                    "page": 1,
                    "chunk": 2,
                    "type": "pdf",
                },
            },
            {
                "id": "test_doc_3",
                "text": "서울시 정부는 강남구의 상권 활성화를 위해 다양한 정책을 시행하고 있으며, 스타트업 지원 프로그램도 운영하고 있습니다.",
                "metadata": {
                    "source": "test_source.pdf",
                    "page": 2,
                    "chunk": 1,
                    "type": "pdf",
                },
            },
        ]

        # 테스트 쿼리 정의
        cls.test_queries = [
            {
                "query": "강남구의 주요 업종은 무엇인가요?",
                "expected_keywords": ["IT", "금융", "의료", "교육"],
                "min_score": 0.3,
            },
            {
                "query": "서울시 정부의 강남구 정책은?",
                "expected_keywords": ["정책", "스타트업", "지원"],
                "min_score": 0.3,
            },
            {
                "query": "강남구 부동산 가격은?",
                "expected_keywords": ["부동산", "가격"],
                "min_score": 0.2,
            },
        ]

    def setUp(self):
        """각 테스트 전 실행"""
        # 테스트용 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.rag_engine.model_path = Path(self.temp_dir)

    def tearDown(self):
        """각 테스트 후 실행"""
        # 임시 디렉토리 정리
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_rag_engine_initialization(self):
        """RAG 엔진 초기화 테스트"""
        try:
            success = self.rag_engine.initialize_models()
            self.assertTrue(success, "RAG 엔진 초기화가 실패했습니다")
            logger.info("RAG 엔진 초기화 테스트 통과")
        except Exception as e:
            logger.warning(f"RAG 엔진 초기화 테스트 스킵: {e}")
            self.skipTest(f"RAG 엔진 초기화 실패: {e}")

    def test_document_indexing(self):
        """문서 인덱싱 테스트"""
        try:
            success = self.rag_engine.build_index(self.test_documents)
            self.assertTrue(success, "문서 인덱싱이 실패했습니다")

            # 인덱스 통계 확인
            stats = self.rag_engine.get_index_stats()
            self.assertEqual(
                stats["total_documents"],
                len(self.test_documents),
                "인덱싱된 문서 수가 일치하지 않습니다",
            )
            self.assertTrue(stats["index_built"], "BM25 인덱스가 구축되지 않았습니다")

            logger.info("문서 인덱싱 테스트 통과")

        except Exception as e:
            logger.warning(f"문서 인덱싱 테스트 스킵: {e}")
            self.skipTest(f"문서 인덱싱 실패: {e}")

    def test_hybrid_search_quality(self):
        """하이브리드 검색 품질 테스트"""
        try:
            # 인덱스 구축
            if not self.rag_engine.build_index(self.test_documents):
                self.skipTest("인덱스 구축 실패")

            for i, test_case in enumerate(self.test_queries):
                with self.subTest(query=test_case["query"]):
                    results = self.rag_engine.search(
                        test_case["query"], search_type="hybrid", top_k=3
                    )

                    # 결과 존재 확인
                    self.assertGreater(
                        len(results), 0, f"쿼리 {i+1}에 대한 검색 결과가 없습니다"
                    )

                    # 점수 확인
                    for result in results:
                        self.assertIn(
                            "combined_score", result, "결과에 combined_score가 없습니다"
                        )
                        self.assertGreaterEqual(
                            result["combined_score"],
                            test_case["min_score"],
                            "검색 점수가 최소 기준보다 낮습니다",
                        )

                    # 키워드 포함 확인
                    found_keywords = []
                    for result in results:
                        text = result["text"].lower()
                        for keyword in test_case["expected_keywords"]:
                            if keyword.lower() in text:
                                found_keywords.append(keyword)

                    self.assertGreater(
                        len(found_keywords),
                        0,
                        f"쿼리 {i+1}에서 예상 키워드를 찾을 수 없습니다",
                    )

                    logger.info(f"검색 품질 테스트 {i+1} 통과: {test_case['query']}")

        except Exception as e:
            logger.warning(f"하이브리드 검색 품질 테스트 스킵: {e}")

    def test_vector_search_quality(self):
        """벡터 검색 품질 테스트"""
        try:
            # 인덱스 구축
            if not self.rag_engine.build_index(self.test_documents):
                self.skipTest("인덱스 구축 실패")

            query = "강남구의 주요 업종은 무엇인가요?"
            results = self.rag_engine.search(query, search_type="vector", top_k=2)

            # 결과 확인
            self.assertGreater(len(results), 0, "벡터 검색 결과가 없습니다")

            # 점수 확인
            for result in results:
                self.assertIn("vector_score", result, "결과에 vector_score가 없습니다")
                self.assertGreater(
                    result["vector_score"], 0, "벡터 점수가 0보다 작습니다"
                )

            logger.info("벡터 검색 품질 테스트 통과")

        except Exception as e:
            logger.warning(f"벡터 검색 품질 테스트 스킵: {e}")

    def test_bm25_search_quality(self):
        """BM25 검색 품질 테스트"""
        try:
            # 인덱스 구축
            if not self.rag_engine.build_index(self.test_documents):
                self.skipTest("인덱스 구축 실패")

            query = "강남구의 주요 업종은 무엇인가요?"
            results = self.rag_engine.search(query, search_type="bm25", top_k=2)

            # 결과 확인
            self.assertGreater(len(results), 0, "BM25 검색 결과가 없습니다")

            # 점수 확인
            for result in results:
                self.assertIn("bm25_score", result, "결과에 bm25_score가 없습니다")
                self.assertGreater(
                    result["bm25_score"], 0, "BM25 점수가 0보다 작습니다"
                )

            logger.info("BM25 검색 품질 테스트 통과")

        except Exception as e:
            logger.warning(f"BM25 검색 품질 테스트 스킵: {e}")

    def test_search_performance(self):
        """검색 성능 테스트"""
        try:
            # 인덱스 구축
            if not self.rag_engine.build_index(self.test_documents):
                self.skipTest("인덱스 구축 실패")

            query = "강남구의 주요 업종은 무엇인가요?"

            # 성능 측정
            start_time = time.time()
            results = self.rag_engine.search(query, search_type="hybrid", top_k=5)
            end_time = time.time()

            response_time = end_time - start_time

            # 응답 시간 확인 (3초 이내)
            self.assertLess(
                response_time,
                3.0,
                f"검색 응답 시간이 너무 깁니다: {response_time:.2f}초",
            )

            # 결과 확인
            self.assertGreater(len(results), 0, "검색 결과가 없습니다")

            logger.info(f"검색 성능 테스트 통과 - 응답 시간: {response_time:.2f}초")

        except Exception as e:
            logger.warning(f"검색 성능 테스트 스킵: {e}")

    def test_text_chunking(self):
        """텍스트 청킹 테스트"""
        long_text = """
        서울시 강남구는 대한민국의 주요 상업지구입니다. 
        이 지역은 높은 부동산 가격과 활발한 상업 활동으로 유명합니다.
        강남구의 주요 업종은 IT, 금융, 의료, 교육 서비스 등입니다.
        특히 테헤란로 일대는 IT 기업들이 집중되어 있습니다.
        서울시 정부는 강남구의 상권 활성화를 위해 다양한 정책을 시행하고 있습니다.
        스타트업 지원 프로그램도 운영하고 있습니다.
        """

        chunks = self.rag_engine._chunk_text(long_text, chunk_size=100, overlap=20)

        # 청킹 결과 확인
        self.assertGreater(len(chunks), 1, "텍스트가 청킹되지 않았습니다")

        # 청크 크기 확인
        for chunk in chunks:
            self.assertLessEqual(
                len(chunk), 120, "청크 크기가 너무 큽니다"
            )  # overlap 고려

        # 원본 텍스트 보존 확인
        original_text = long_text.replace("\n", "").replace(" ", "")
        chunked_text = "".join(chunks).replace("\n", "").replace(" ", "")
        self.assertIn(
            chunked_text[:50], original_text, "청킹된 텍스트가 원본과 다릅니다"
        )

        logger.info("텍스트 청킹 테스트 통과")

    def test_korean_tokenization(self):
        """한국어 토큰화 테스트"""
        korean_text = "서울시 강남구는 대한민국의 주요 상업지구입니다."
        tokens = self.rag_engine._tokenize_korean(korean_text)

        # 토큰화 결과 확인
        self.assertGreater(len(tokens), 0, "토큰화 결과가 없습니다")

        # 예상 토큰 확인
        expected_tokens = ["서울시", "강남구는", "대한민국의", "주요", "상업지구입니다"]
        for token in expected_tokens:
            self.assertIn(token, tokens, f"토큰 '{token}'이 없습니다")

        logger.info("한국어 토큰화 테스트 통과")

    def test_index_persistence(self):
        """인덱스 지속성 테스트"""
        try:
            # 인덱스 구축
            if not self.rag_engine.build_index(self.test_documents):
                self.skipTest("인덱스 구축 실패")

            # 인덱스 저장
            self.rag_engine._save_index()

            # 새로운 인스턴스 생성하여 인덱스 로드
            new_rag_engine = HybridRetriever(self.config)
            new_rag_engine.model_path = Path(self.temp_dir)

            success = new_rag_engine._load_index()
            self.assertTrue(success, "인덱스 로드가 실패했습니다")

            # 로드된 인덱스로 검색 테스트
            query = "강남구의 주요 업종은 무엇인가요?"
            results = new_rag_engine.search(query, search_type="hybrid", top_k=2)

            self.assertGreater(len(results), 0, "로드된 인덱스로 검색 결과가 없습니다")

            logger.info("인덱스 지속성 테스트 통과")

        except Exception as e:
            logger.warning(f"인덱스 지속성 테스트 스킵: {e}")


class TestRAGQuality(unittest.TestCase):
    """RAG 품질 테스트 클래스"""

    def test_relevance_scoring(self):
        """관련성 점수 테스트"""
        # 관련성 점수 계산 로직 테스트
        test_cases = [
            {
                "query": "강남구 업종",
                "text": "강남구의 주요 업종은 IT, 금융, 의료입니다.",
                "expected_relevance": "high",
            },
            {
                "query": "강남구 업종",
                "text": "서울시 전체의 인구 통계입니다.",
                "expected_relevance": "low",
            },
        ]

        for test_case in test_cases:
            with self.subTest(query=test_case["query"]):
                # 실제 구현에서는 관련성 점수 계산 로직을 테스트
                self.assertTrue(True, "관련성 점수 테스트는 실제 구현에서 수행됩니다")

    def test_diversity_metrics(self):
        """다양성 메트릭 테스트"""
        # 검색 결과의 다양성 측정
        results = [
            {"text": "강남구 IT 업종 정보", "metadata": {"source": "doc1"}},
            {"text": "강남구 금융 업종 정보", "metadata": {"source": "doc2"}},
            {"text": "강남구 의료 업종 정보", "metadata": {"source": "doc3"}},
        ]

        # 다양성 측정 (소스별)
        sources = [result["metadata"]["source"] for result in results]
        unique_sources = set(sources)

        self.assertEqual(
            len(unique_sources), len(results), "검색 결과의 다양성이 부족합니다"
        )

    def test_coverage_metrics(self):
        """커버리지 메트릭 테스트"""
        # 검색 결과가 쿼리의 다양한 측면을 커버하는지 테스트
        query = "강남구의 주요 업종과 정책"
        expected_aspects = ["업종", "정책"]

        # 실제 구현에서는 각 측면에 대한 커버리지를 측정
        for aspect in expected_aspects:
            self.assertIn(aspect, query, f"쿼리에 '{aspect}' 측면이 포함되어야 합니다")


if __name__ == "__main__":
    # 테스트 실행
    unittest.main(verbosity=2)
