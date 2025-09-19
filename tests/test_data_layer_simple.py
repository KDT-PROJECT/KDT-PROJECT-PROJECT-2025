"""
Data Layer 테스트 (간소화된 버전)
TDD 프로세스에 따른 테스트 코드 - 실제 구현된 클래스만 테스트
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from data.database_manager import DatabaseManager
from data.etl_service import ETLService


class TestDatabaseManager:
    """데이터베이스 관리자 테스트"""

    @pytest.fixture
    def db_manager(self):
        """데이터베이스 관리자 인스턴스"""
        with patch("data.database_manager.config") as mock_config:
            mock_config.database.host = "localhost"
            mock_config.database.port = 3306
            mock_config.database.user = "test_user"
            mock_config.database.password = "test_pass"
            mock_config.database.name = "test_db"
            mock_config.logging.level = "INFO"

            with patch("data.database_manager.create_engine") as mock_engine:
                mock_engine_instance = Mock()
                mock_engine.return_value = mock_engine_instance

                with patch("data.database_manager.sessionmaker") as mock_sessionmaker:
                    mock_session = Mock()
                    mock_sessionmaker.return_value = mock_session

                    return DatabaseManager()

    def test_database_manager_initialization(self, db_manager):
        """데이터베이스 관리자 초기화 테스트"""
        assert db_manager is not None
        assert hasattr(db_manager, "engine")
        assert hasattr(db_manager, "Session")

    @patch("data.database_manager.pd.read_sql")
    def test_execute_query_success(self, mock_read_sql, db_manager):
        """쿼리 실행 성공 테스트"""
        # 모의 결과 설정
        mock_df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        mock_read_sql.return_value = mock_df

        # 쿼리 실행
        result = db_manager.execute_query("SELECT * FROM test_table")

        # 검증
        assert result.equals(mock_df)
        mock_read_sql.assert_called_once()

    def test_get_session(self, db_manager):
        """세션 반환 테스트"""
        session = db_manager.get_session()
        assert session is not None


class TestETLService:
    """ETL 서비스 테스트"""

    @pytest.fixture
    def etl_service(self):
        """ETL 서비스 인스턴스"""
        with patch("data.etl_service.DatabaseManager") as mock_db_manager:
            mock_db_instance = Mock()
            mock_db_manager.return_value = mock_db_instance

            return ETLService()

    def test_etl_service_initialization(self, etl_service):
        """ETL 서비스 초기화 테스트"""
        assert etl_service is not None
        assert hasattr(etl_service, "db_manager")

    @patch("data.etl_service.pd.read_csv")
    def test_load_csv_success(self, mock_read_csv, etl_service):
        """CSV 로드 성공 테스트"""
        # 모의 데이터 설정
        mock_df = pd.DataFrame(
            {
                "region_name": ["강남구", "서초구"],
                "industry_name": ["음식점", "카페"],
                "date": ["2024-01-01", "2024-01-02"],
                "sales_amount": [1000000, 500000],
                "transaction_count": [100, 50],
            }
        )
        mock_read_csv.return_value = mock_df

        # CSV 로드
        result = etl_service.load_csv("test.csv")

        # 검증
        assert result.equals(mock_df)
        mock_read_csv.assert_called_once_with("test.csv")

    def test_load_csv_file_not_found(self, etl_service):
        """CSV 파일 없음 테스트"""
        with patch("data.etl_service.pd.read_csv") as mock_read_csv:
            mock_read_csv.side_effect = FileNotFoundError("File not found")

            with pytest.raises(Exception):  # ETLValidationError
                etl_service.load_csv("nonexistent.csv")

    def test_validate_data_success(self, etl_service):
        """데이터 검증 성공 테스트"""
        # 유효한 데이터
        valid_df = pd.DataFrame(
            {
                "region_name": ["강남구"],
                "industry_name": ["음식점"],
                "date": ["2024-01-01"],
                "sales_amount": [1000000],
                "transaction_count": [100],
            }
        )

        result = etl_service.validate_data(valid_df)
        assert result.equals(valid_df)

    def test_validate_data_missing_columns(self, etl_service):
        """필수 컬럼 누락 테스트"""
        # 필수 컬럼이 누락된 데이터
        invalid_df = pd.DataFrame(
            {
                "region_name": ["강남구"],
                "industry_name": ["음식점"],
                # date, sales_amount, transaction_count 누락
            }
        )

        with pytest.raises(Exception):  # ETLValidationError
            etl_service.validate_data(invalid_df)

    def test_remove_duplicates(self, etl_service):
        """중복 제거 테스트"""
        # 중복이 있는 데이터
        df_with_duplicates = pd.DataFrame(
            {
                "region_name": ["강남구", "강남구", "서초구"],
                "industry_name": ["음식점", "음식점", "카페"],
                "date": ["2024-01-01", "2024-01-01", "2024-01-02"],
                "sales_amount": [1000000, 1000000, 500000],
                "transaction_count": [100, 100, 50],
            }
        )

        result = etl_service.remove_duplicates(df_with_duplicates)
        assert len(result) == 2  # 중복 제거 후 2행
        assert len(df_with_duplicates) == 3  # 원본은 3행
