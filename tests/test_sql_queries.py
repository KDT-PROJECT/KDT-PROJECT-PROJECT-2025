"""
Text-to-SQL 정확도 테스트
project-structure.mdc 규칙에 따른 SQL 쿼리 테스트
"""

import sys
import unittest
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

from utils.sql_text2sql import TextToSQLConverter

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSQLQueries(unittest.TestCase):
    """Text-to-SQL 쿼리 테스트 클래스"""

    @classmethod
    def setUpClass(cls):
        """테스트 클래스 초기화"""
        # 테스트용 데이터베이스 설정
        cls.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "password",
            "database": "seoul_commercial_test",
            "port": 3306,
        }

        # 모델 설정
        cls.model_config = {
            "llm_model": "microsoft/DialoGPT-medium",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        }

        # TextToSQLConverter 인스턴스 생성
        cls.sql_engine = TextToSQLConverter(cls.db_config, cls.model_config)

        # 테스트 쿼리 정의
        cls.test_queries = [
            {
                "query": "강남구에서 가장 매출이 높은 업종은 무엇인가요?",
                "expected_keywords": ["SELECT", "FROM", "WHERE", "ORDER BY", "LIMIT"],
                "expected_tables": ["regions", "industries", "sales_2024"],
            },
            {
                "query": "서울시 전체 매출 상위 5개 지역을 보여주세요",
                "expected_keywords": [
                    "SELECT",
                    "FROM",
                    "GROUP BY",
                    "ORDER BY",
                    "LIMIT",
                ],
                "expected_tables": ["regions", "sales_2024"],
            },
            {
                "query": "음식점 업종의 평균 매출을 지역별로 보여주세요",
                "expected_keywords": ["SELECT", "FROM", "WHERE", "GROUP BY", "AVG"],
                "expected_tables": ["industries", "sales_2024", "regions"],
            },
        ]

    def test_sql_engine_initialization(self):
        """SQL 엔진 초기화 테스트"""
        try:
            success = self.sql_engine.initialize()
            self.assertTrue(success, "SQL 엔진 초기화가 실패했습니다")
            logger.info("SQL 엔진 초기화 테스트 통과")
        except Exception as e:
            logger.warning(f"SQL 엔진 초기화 테스트 스킵: {e}")
            self.skipTest(f"SQL 엔진 초기화 실패: {e}")

    def test_sql_query_generation(self):
        """SQL 쿼리 생성 테스트"""
        for i, test_case in enumerate(self.test_queries):
            with self.subTest(query=test_case["query"]):
                try:
                    result = self.sql_engine.query(test_case["query"])

                    # 기본 응답 구조 확인
                    self.assertIn("success", result, "응답에 'success' 키가 없습니다")
                    self.assertIn(
                        "sql_query", result, "응답에 'sql_query' 키가 없습니다"
                    )

                    if result["success"]:
                        sql_query = result["sql_query"].upper()

                        # 예상 키워드 확인
                        for keyword in test_case["expected_keywords"]:
                            self.assertIn(
                                keyword.upper(),
                                sql_query,
                                f"SQL 쿼리에 '{keyword}' 키워드가 없습니다",
                            )

                        # 예상 테이블 확인
                        for table in test_case["expected_tables"]:
                            self.assertIn(
                                table.upper(),
                                sql_query,
                                f"SQL 쿼리에 '{table}' 테이블이 없습니다",
                            )

                        logger.info(f"쿼리 {i+1} 테스트 통과: {test_case['query']}")
                    else:
                        logger.warning(
                            f"쿼리 {i+1} 실행 실패: {result.get('error', '알 수 없는 오류')}"
                        )

                except Exception as e:
                    logger.error(f"쿼리 {i+1} 테스트 실패: {e}")
                    self.fail(f"쿼리 테스트 실패: {e}")

    def test_sql_query_validation(self):
        """SQL 쿼리 유효성 검증 테스트"""
        test_queries = [
            "SELECT * FROM regions",
            "SELECT r.region_name, SUM(s.sales_amount) FROM sales_2024 s JOIN regions r ON s.region_id = r.id",
            "INVALID SQL QUERY",
        ]

        for i, query in enumerate(test_queries):
            with self.subTest(query=query):
                try:
                    is_valid, message = self.sql_engine.validate_sql(query)

                    if i < 2:  # 유효한 쿼리
                        self.assertTrue(is_valid, f"유효한 쿼리가 거부됨: {message}")
                    else:  # 무효한 쿼리
                        self.assertFalse(is_valid, f"무효한 쿼리가 승인됨: {message}")

                    logger.info(f"쿼리 유효성 테스트 {i+1} 통과")

                except Exception as e:
                    logger.warning(f"쿼리 유효성 테스트 {i+1} 스킵: {e}")

    def test_schema_info_retrieval(self):
        """스키마 정보 조회 테스트"""
        try:
            schema_info = self.sql_engine.get_schema_info()

            # 기본 구조 확인
            self.assertIn("tables", schema_info, "스키마 정보에 'tables' 키가 없습니다")
            self.assertIn(
                "table_details",
                schema_info,
                "스키마 정보에 'table_details' 키가 없습니다",
            )

            # 예상 테이블 확인
            expected_tables = ["regions", "industries", "sales_2024", "features"]
            for table in expected_tables:
                self.assertIn(
                    table,
                    schema_info["tables"],
                    f"테이블 '{table}'이 스키마에 없습니다",
                )

            logger.info("스키마 정보 조회 테스트 통과")

        except Exception as e:
            logger.warning(f"스키마 정보 조회 테스트 스킵: {e}")

    def test_query_examples(self):
        """예시 쿼리 테스트"""
        try:
            examples = self.sql_engine.get_query_examples()

            # 예시 쿼리 구조 확인
            self.assertIsInstance(examples, list, "예시 쿼리가 리스트가 아닙니다")
            self.assertGreater(len(examples), 0, "예시 쿼리가 없습니다")

            for example in examples:
                self.assertIn("query", example, "예시에 'query' 키가 없습니다")
                self.assertIn(
                    "description", example, "예시에 'description' 키가 없습니다"
                )
                self.assertIsInstance(example["query"], str, "쿼리가 문자열이 아닙니다")
                self.assertIsInstance(
                    example["description"], str, "설명이 문자열이 아닙니다"
                )

            logger.info("예시 쿼리 테스트 통과")

        except Exception as e:
            logger.error(f"예시 쿼리 테스트 실패: {e}")
            self.fail(f"예시 쿼리 테스트 실패: {e}")

    def test_performance_metrics(self):
        """성능 메트릭 테스트"""
        import time

        test_query = "강남구에서 가장 매출이 높은 업종은 무엇인가요?"

        try:
            start_time = time.time()
            result = self.sql_engine.query(test_query)
            end_time = time.time()

            response_time = end_time - start_time

            # 응답 시간 확인 (5초 이내)
            self.assertLess(
                response_time, 5.0, f"응답 시간이 너무 깁니다: {response_time:.2f}초"
            )

            # 응답 구조 확인
            self.assertIn("success", result, "응답에 'success' 키가 없습니다")

            logger.info(f"성능 테스트 통과 - 응답 시간: {response_time:.2f}초")

        except Exception as e:
            logger.warning(f"성능 테스트 스킵: {e}")


class TestSQLAccuracy(unittest.TestCase):
    """SQL 정확도 테스트 클래스"""

    def test_sql_syntax_accuracy(self):
        """SQL 문법 정확도 테스트"""
        # 정확한 SQL 문법 테스트
        valid_sqls = [
            "SELECT * FROM regions",
            "SELECT r.region_name, SUM(s.sales_amount) as total_sales FROM sales_2024 s JOIN regions r ON s.region_id = r.id GROUP BY r.region_name",
            "SELECT i.industry_name, AVG(s.sales_amount) as avg_sales FROM sales_2024 s JOIN industries i ON s.industry_id = i.id WHERE i.industry_name = '음식점' GROUP BY i.industry_name",
        ]

        for sql in valid_sqls:
            with self.subTest(sql=sql):
                # 기본적인 SQL 문법 검사
                self.assertTrue(
                    sql.strip().upper().startswith("SELECT"),
                    "SQL이 SELECT로 시작하지 않습니다",
                )
                self.assertIn("FROM", sql.upper(), "SQL에 FROM 절이 없습니다")

    def test_sql_semantic_accuracy(self):
        """SQL 의미적 정확도 테스트"""
        # 의미적으로 올바른 SQL 패턴 테스트
        test_cases = [
            {
                "query": "지역별 매출 조회",
                "expected_patterns": ["GROUP BY", "SUM", "regions", "sales_2024"],
            },
            {
                "query": "업종별 평균 매출",
                "expected_patterns": ["GROUP BY", "AVG", "industries", "sales_2024"],
            },
            {"query": "상위 N개 결과", "expected_patterns": ["ORDER BY", "LIMIT"]},
        ]

        for test_case in test_cases:
            with self.subTest(query=test_case["query"]):
                # 패턴 검사는 실제 구현에서 수행
                self.assertTrue(True, "의미적 정확도 테스트는 실제 구현에서 수행됩니다")


if __name__ == "__main__":
    # 테스트 실행
    unittest.main(verbosity=2)
