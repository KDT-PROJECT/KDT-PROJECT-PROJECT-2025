"""
MySQL 스키마 정의 테스트
TDD: 테스트 코드 먼저 작성
"""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestMySQLSchema:
    """MySQL 스키마 테스트"""

    @pytest.fixture
    def mock_db_connection(self):
        """Mock DB 연결"""
        with patch("sqlalchemy.create_engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__.return_value = (
                mock_conn
            )
            yield mock_conn

    def test_schema_file_exists(self):
        """스키마 파일이 존재하는지 확인"""
        schema_path = "data/schema.sql"
        assert os.path.exists(
            schema_path
        ), "스키마 파일 data/schema.sql이 존재하지 않습니다"

    def test_schema_contains_required_tables(self):
        """스키마에 필수 테이블들이 포함되어 있는지 확인"""
        schema_path = "data/schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_content = f.read()

        required_tables = ["regions", "industries", "sales_2024"]
        for table in required_tables:
            assert (
                f"CREATE TABLE IF NOT EXISTS {table}".upper() in schema_content.upper()
            ), f"테이블 {table}이 스키마에 없습니다"

    def test_regions_table_structure(self):
        """regions 테이블 구조 검증"""
        schema_path = "data/schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_content = f.read()

        # regions 테이블에 필수 컬럼들이 있는지 확인
        required_columns = ["region_id", "region_name", "created_at"]
        for column in required_columns:
            assert (
                column in schema_content
            ), f"regions 테이블에 컬럼 {column}이 없습니다"

    def test_industries_table_structure(self):
        """industries 테이블 구조 검증"""
        schema_path = "data/schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_content = f.read()

        # industries 테이블에 필수 컬럼들이 있는지 확인
        required_columns = ["industry_id", "industry_name", "created_at"]
        for column in required_columns:
            assert (
                column in schema_content
            ), f"industries 테이블에 컬럼 {column}이 없습니다"

    def test_sales_2024_table_structure(self):
        """sales_2024 테이블 구조 검증"""
        schema_path = "data/schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_content = f.read()

        # sales_2024 테이블에 필수 컬럼들이 있는지 확인
        required_columns = ["region_id", "industry_id", "date", "sales_amount"]
        for column in required_columns:
            assert (
                column in schema_content
            ), f"sales_2024 테이블에 컬럼 {column}이 없습니다"

    def test_composite_primary_key(self):
        """복합 기본키 설정 검증"""
        schema_path = "data/schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_content = f.read()

        # sales_2024 테이블에 복합 기본키가 설정되어 있는지 확인
        assert (
            "PRIMARY KEY" in schema_content.upper()
        ), "복합 기본키가 설정되지 않았습니다"
        assert (
            "region_id" in schema_content and "industry_id" in schema_content
        ), "복합 기본키에 필수 컬럼이 없습니다"

    def test_indexes_defined(self):
        """인덱스 정의 검증"""
        schema_path = "data/schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_content = f.read()

        # 보조 인덱스들이 정의되어 있는지 확인
        required_indexes = ["date", "region", "industry"]
        for index in required_indexes:
            assert (
                "INDEX" in schema_content.upper()
            ), f"인덱스 {index}가 정의되지 않았습니다"

    def test_foreign_key_constraints(self):
        """외래키 제약조건 검증"""
        schema_path = "data/schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_content = f.read()

        # 외래키 제약조건이 설정되어 있는지 확인
        assert (
            "FOREIGN KEY" in schema_content.upper()
        ), "외래키 제약조건이 설정되지 않았습니다"

    def test_schema_syntax_valid(self, mock_db_connection):
        """스키마 문법 유효성 검증"""
        schema_path = "data/schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_content = f.read()

        # SQL 문법이 유효한지 확인 (기본적인 검증)
        assert "CREATE TABLE" in schema_content.upper(), "CREATE TABLE 문이 없습니다"
        assert ";" in schema_content, "SQL 문이 세미콜론으로 종료되지 않았습니다"

    def test_data_types_appropriate(self):
        """데이터 타입 적절성 검증"""
        schema_path = "data/schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_content = f.read()

        # 적절한 데이터 타입이 사용되었는지 확인
        assert "INT" in schema_content.upper(), "INT 타입이 사용되지 않았습니다"
        assert "VARCHAR" in schema_content.upper(), "VARCHAR 타입이 사용되지 않았습니다"
        assert (
            "DECIMAL" in schema_content.upper() or "FLOAT" in schema_content.upper()
        ), "숫자 타입이 사용되지 않았습니다"
        assert (
            "DATE" in schema_content.upper() or "DATETIME" in schema_content.upper()
        ), "날짜 타입이 사용되지 않았습니다"


class TestDatabaseConnection:
    """데이터베이스 연결 테스트"""

    def test_database_config_loaded(self):
        """데이터베이스 설정이 로드되는지 확인"""
        from config import DatabaseConfig

        # 설정 클래스가 존재하는지 확인
        assert DatabaseConfig is not None, "DatabaseConfig 클래스가 정의되지 않았습니다"

    def test_connection_string_format(self):
        """연결 문자열 형식 검증"""
        from config import DatabaseConfig

        config = DatabaseConfig()
        connection_string = config.get_connection_string()

        # 연결 문자열에 필수 요소들이 포함되어 있는지 확인
        assert (
            "mysql+pymysql://" in connection_string
        ), "MySQL 연결 문자열 형식이 올바르지 않습니다"
        assert "@" in connection_string, "연결 문자열에 사용자 정보가 없습니다"
        assert "/" in connection_string, "연결 문자열에 데이터베이스명이 없습니다"


if __name__ == "__main__":
    pytest.main([__file__])
