"""
Text-to-SQL 모듈 테스트
tech-stack.mdc 규칙에 따른 LlamaIndex NL→SQL 변환 테스트
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from llm.text_to_sql import TextToSQLService

# Set testing environment to avoid OpenAI embedding issues
os.environ["IS_TESTING"] = "1"


class TestTextToSQLService:
    """Text-to-SQL 서비스 테스트 클래스"""

    @pytest.fixture
    def text_to_sql_service(self):
        """Text-to-SQL 서비스 인스턴스 생성"""
        with (
            patch("llm.text_to_sql.get_llm_config") as mock_llm_config,
            patch("llm.text_to_sql.get_rag_config") as mock_rag_config,
            patch("llm.text_to_sql.get_db_config") as mock_db_config,
            patch("llm.text_to_sql.HuggingFaceLLM") as mock_hf_llm,
            patch("llm.text_to_sql.HuggingFaceEmbedding") as mock_hf_embedding,
            patch("llm.text_to_sql.SQLDatabase") as mock_sql_db,
            patch("llm.text_to_sql.NLSQLTableQueryEngine") as mock_query_engine,
        ):

            # Mock 설정
            mock_llm_config.return_value = MagicMock(
                LLM_MODEL="microsoft/DialoGPT-medium",
                LLM_API_KEY="test_api_key",
                LLM_TEMPERATURE=0.7,
                LLM_MAX_TOKENS=2000,
                LLM_TIMEOUT=30,
            )
            mock_rag_config.return_value = MagicMock(
                EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2",
                INDEX_PATH="models/artifacts",
                CHUNK_SIZE=1000,
                CHUNK_OVERLAP=200,
                TOP_K=5,
                ALPHA=0.5,
            )
            mock_db_config.return_value = MagicMock(
                get_connection_string=lambda: "mysql+pymysql://test:test@localhost/test"
            )
            mock_hf_llm.return_value = MagicMock()
            mock_hf_embedding.return_value = MagicMock()
            mock_sql_db.return_value = MagicMock()
            mock_query_engine.return_value = MagicMock()

            return TextToSQLService()

    def test_text_to_sql_service_initialization(self, text_to_sql_service):
        """Text-to-SQL 서비스 초기화 테스트"""
        assert text_to_sql_service is not None
        assert hasattr(text_to_sql_service, "llm")
        assert hasattr(text_to_sql_service, "embedding_model")
        assert hasattr(text_to_sql_service, "sql_database")
        assert hasattr(text_to_sql_service, "query_engine")

    def test_generate_sql_query_simple(self, text_to_sql_service):
        """간단한 SQL 쿼리 생성 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.response = (
            "SELECT * FROM regions WHERE region_name = '강남구' LIMIT 1000"
        )
        text_to_sql_service.query_engine.query.return_value = mock_response

        # 테스트 실행
        natural_language = "강남구의 모든 데이터를 보여주세요"
        result = text_to_sql_service.generate_sql_query(natural_language)

        # 검증
        assert result is not None
        assert "SELECT" in result
        assert "regions" in result
        assert "강남구" in result
        text_to_sql_service.query_engine.query.assert_called_once()

    def test_generate_sql_query_error_handling(self, text_to_sql_service):
        """SQL 쿼리 생성 오류 처리 테스트"""
        # Mock 오류 설정
        text_to_sql_service.query_engine.query.side_effect = Exception("LLM 오류")

        # 테스트 실행
        natural_language = "잘못된 질의"
        result = text_to_sql_service.generate_sql_query(natural_language)

        # 검증
        assert result is None

    def test_validate_sql_query_valid(self, text_to_sql_service):
        """유효한 SQL 쿼리 검증 테스트"""
        valid_queries = [
            "SELECT * FROM regions",
            "SELECT region_name FROM regions WHERE region_id = 1",
            "SELECT COUNT(*) FROM sales_2024 GROUP BY region_id",
        ]

        for query in valid_queries:
            result = text_to_sql_service.validate_sql_query(query)
            assert result == True, f"쿼리 검증 실패: {query}"

    def test_validate_sql_query_invalid(self, text_to_sql_service):
        """무효한 SQL 쿼리 검증 테스트"""
        invalid_queries = [
            "INSERT INTO regions VALUES (1, 'test')",
            "UPDATE regions SET region_name = 'test'",
            "DELETE FROM regions WHERE region_id = 1",
            "SELECT * FROM users",  # 허용되지 않은 테이블
        ]

        for query in invalid_queries:
            result = text_to_sql_service.validate_sql_query(query)
            assert result == False, f"쿼리 검증 실패: {query}"

    def test_sanitize_sql_query(self, text_to_sql_service):
        """SQL 쿼리 정제 테스트"""
        # 주석이 있는 쿼리
        query_with_comments = "SELECT * FROM regions -- 주석"
        result = text_to_sql_service.sanitize_sql_query(query_with_comments)
        assert "--" not in result

        # LIMIT이 없는 쿼리
        query_without_limit = "SELECT * FROM regions"
        result = text_to_sql_service.sanitize_sql_query(query_without_limit)
        assert "LIMIT" in result
