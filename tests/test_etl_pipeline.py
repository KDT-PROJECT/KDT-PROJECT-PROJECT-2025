"""
CSV→MySQL ETL 파이프라인 테스트
TDD: 테스트 코드 먼저 작성
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest


class TestETLService:
    """ETL 서비스 테스트"""

    @pytest.fixture
    def sample_csv_data(self):
        """샘플 CSV 데이터 생성"""
        return pd.DataFrame(
            {
                "region_name": ["강남구", "서초구", "송파구", "강남구", "서초구"],
                "industry_name": ["음식점업", "소매업", "숙박업", "음식점업", "소매업"],
                "date": pd.to_datetime(
                    [
                        "2024-01-01",
                        "2024-01-01",
                        "2024-01-01",
                        "2024-01-02",
                        "2024-01-02",
                    ]
                ),
                "sales_amount": [1000000, 2000000, 1500000, 1200000, 1800000],
                "transaction_count": [100, 200, 150, 120, 180],
            }
        )

    @pytest.fixture
    def sample_csv_with_issues(self):
        """문제가 있는 샘플 CSV 데이터"""
        return pd.DataFrame(
            {
                "region_name": ["강남구", "", "송파구", "강남구", None],
                "industry_name": ["음식점업", "소매업", "", "음식점업", "소매업"],
                "date": [
                    "2024-01-01",
                    "invalid_date",
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-02",
                ],
                "sales_amount": [1000000, -500000, 1500000, 1200000, 1800000],
                "transaction_count": [100, 200, 150, 120, 180],
            }
        )

    def test_etl_service_initialization(self):
        """ETL 서비스 초기화 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()
        assert etl_service is not None
        assert hasattr(etl_service, "db_manager")

    def test_csv_loading(self, sample_csv_data):
        """CSV 로딩 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()

        # 임시 CSV 파일 생성
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            sample_csv_data.to_csv(f.name, index=False, encoding="utf-8")
            temp_file = f.name

        try:
            # CSV 로딩 테스트
            loaded_data = etl_service.load_csv(temp_file)

            assert isinstance(loaded_data, pd.DataFrame)
            assert len(loaded_data) == 5
            assert "region_name" in loaded_data.columns
            assert "industry_name" in loaded_data.columns
            assert "date" in loaded_data.columns
            assert "sales_amount" in loaded_data.columns
        finally:
            os.unlink(temp_file)

    def test_data_validation(self, sample_csv_data):
        """데이터 검증 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()

        # 정상 데이터 검증
        validated_data = etl_service.validate_data(sample_csv_data)
        assert len(validated_data) == 5
        assert validated_data["sales_amount"].min() >= 0

        # 문제가 있는 데이터 검증
        problem_data = pd.DataFrame(
            {
                "region_name": ["강남구", "", "송파구"],
                "industry_name": ["음식점업", "소매업", ""],
                "date": ["2024-01-01", "invalid_date", "2024-01-01"],
                "sales_amount": [1000000, -500000, 1500000],
                "transaction_count": [100, 200, 150],
            }
        )

        validated_problem_data = etl_service.validate_data(problem_data)
        # 문제가 있는 행들이 제거되어야 함
        assert len(validated_problem_data) < len(problem_data)

    def test_duplicate_removal(self):
        """중복 제거 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()

        # 중복 데이터 생성
        duplicate_data = pd.DataFrame(
            {
                "region_name": ["강남구", "강남구", "서초구", "강남구"],
                "industry_name": ["음식점업", "음식점업", "소매업", "음식점업"],
                "date": ["2024-01-01", "2024-01-01", "2024-01-01", "2024-01-01"],
                "sales_amount": [1000000, 1000000, 2000000, 1000000],
                "transaction_count": [100, 100, 200, 100],
            }
        )

        cleaned_data = etl_service.remove_duplicates(duplicate_data)
        assert len(cleaned_data) == 2  # 중복 제거 후 2개 행만 남아야 함

    def test_data_transformation(self, sample_csv_data):
        """데이터 변환 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()

        # Mock 데이터베이스 매니저
        def mock_execute_query(query, params=None):
            if "region_id" in query:
                return pd.DataFrame({"region_id": [1]})
            elif "industry_id" in query:
                return pd.DataFrame({"industry_id": [1]})
            else:
                return pd.DataFrame()

        with patch.object(
            etl_service.db_manager, "execute_query", side_effect=mock_execute_query
        ):
            transformed_data = etl_service.transform_data(sample_csv_data)

            # 변환된 데이터 검증
            assert "region_id" in transformed_data.columns
            assert "industry_id" in transformed_data.columns
            assert "avg_transaction_amount" in transformed_data.columns

            # 평균 거래 금액 계산 검증
            expected_avg = (
                transformed_data["sales_amount"] / transformed_data["transaction_count"]
            )
            assert np.allclose(transformed_data["avg_transaction_amount"], expected_avg)

    def test_region_industry_mapping(self):
        """지역/업종 매핑 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()

        # Mock 데이터베이스 매니저
        with patch.object(etl_service.db_manager, "execute_query") as mock_query:
            # 지역 ID 조회 Mock 응답 설정
            mock_query.return_value = pd.DataFrame({"region_id": [1]})

            region_id = etl_service.get_region_id("강남구")
            assert region_id == 1

            # 업종 ID 조회 Mock 응답 설정
            mock_query.return_value = pd.DataFrame({"industry_id": [1]})

            industry_id = etl_service.get_industry_id("음식점업")
            assert industry_id == 1

    def test_data_loading_to_database(self, sample_csv_data):
        """데이터베이스 로딩 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()

        # Mock 데이터베이스 매니저
        def mock_execute_query(query, params=None):
            if "region_id" in query:
                return pd.DataFrame({"region_id": [1]})
            elif "industry_id" in query:
                return pd.DataFrame({"industry_id": [1]})
            else:
                return pd.DataFrame()

        with (
            patch.object(
                etl_service.db_manager, "execute_query", side_effect=mock_execute_query
            ),
            patch.object(etl_service.db_manager, "get_session") as mock_session,
        ):

            # Mock 세션 설정
            mock_session.return_value.__enter__.return_value = MagicMock()

            # 변환된 데이터 생성
            transformed_data = etl_service.transform_data(sample_csv_data)

            # 데이터베이스 로딩 테스트
            result = etl_service.load_to_database(transformed_data)
            assert result is True

    def test_etl_pipeline_full_flow(self, sample_csv_data):
        """ETL 파이프라인 전체 플로우 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()

        # 임시 CSV 파일 생성
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            sample_csv_data.to_csv(f.name, index=False, encoding="utf-8")
            temp_file = f.name

        try:
            # Mock 데이터베이스 매니저
            def mock_execute_query(query, params=None):
                if "region_id" in query:
                    return pd.DataFrame({"region_id": [1]})
                elif "industry_id" in query:
                    return pd.DataFrame({"industry_id": [1]})
                else:
                    return pd.DataFrame()

            with (
                patch.object(
                    etl_service.db_manager,
                    "execute_query",
                    side_effect=mock_execute_query,
                ),
                patch.object(etl_service.db_manager, "get_session") as mock_session,
            ):

                # Mock 세션 설정
                mock_session.return_value.__enter__.return_value = MagicMock()

                # 전체 ETL 파이프라인 실행
                result = etl_service.run_etl_pipeline(temp_file)
                assert result is True
        finally:
            os.unlink(temp_file)

    def test_error_handling(self):
        """에러 처리 테스트"""
        from data.etl_service import ETLService, ETLValidationError

        etl_service = ETLService()

        # 존재하지 않는 파일 로딩 테스트
        with pytest.raises(ETLValidationError):
            etl_service.load_csv("nonexistent_file.csv")

        # 잘못된 데이터 형식 테스트
        invalid_data = pd.DataFrame({"invalid_column": [1, 2, 3]})

        with pytest.raises(ETLValidationError):
            etl_service.validate_data(invalid_data)

    def test_logging_functionality(self, sample_csv_data):
        """로깅 기능 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()

        # Mock 로거
        with patch("data.etl_service.logger") as mock_logger:
            etl_service.validate_data(sample_csv_data)

            # 로깅이 호출되었는지 확인
            assert mock_logger.info.called or mock_logger.debug.called


class TestDataValidation:
    """데이터 검증 테스트"""

    def test_sales_amount_validation(self):
        """매출 금액 검증 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()

        # 음수 매출 테스트
        negative_sales_data = pd.DataFrame(
            {
                "region_name": ["강남구"],
                "industry_name": ["음식점업"],
                "date": ["2024-01-01"],
                "sales_amount": [-1000000],
                "transaction_count": [100],
            }
        )

        validated_data = etl_service.validate_data(negative_sales_data)
        assert len(validated_data) == 0  # 음수 매출은 제거되어야 함

    def test_date_validation(self):
        """날짜 검증 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()

        # 잘못된 날짜 형식 테스트
        invalid_date_data = pd.DataFrame(
            {
                "region_name": ["강남구"],
                "industry_name": ["음식점업"],
                "date": ["invalid_date"],
                "sales_amount": [1000000],
                "transaction_count": [100],
            }
        )

        validated_data = etl_service.validate_data(invalid_date_data)
        assert len(validated_data) == 0  # 잘못된 날짜는 제거되어야 함

    def test_missing_value_handling(self):
        """결측값 처리 테스트"""
        from data.etl_service import ETLService

        etl_service = ETLService()

        # 결측값이 있는 데이터
        missing_data = pd.DataFrame(
            {
                "region_name": ["강남구", None, "서초구"],
                "industry_name": ["음식점업", "소매업", None],
                "date": ["2024-01-01", "2024-01-01", "2024-01-01"],
                "sales_amount": [1000000, 2000000, 1500000],
                "transaction_count": [100, 200, 150],
            }
        )

        validated_data = etl_service.validate_data(missing_data)
        # 결측값이 있는 행들이 제거되어야 함
        assert len(validated_data) < len(missing_data)


if __name__ == "__main__":
    pytest.main([__file__])
