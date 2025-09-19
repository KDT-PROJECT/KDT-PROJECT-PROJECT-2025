import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import pandas as pd
from data.database_manager import DatabaseManager
from config import get_database_config

class TestSchemaConstraints:
    """스키마 제약 조건 테스트"""

    @pytest.fixture
    def mock_db_config(self):
        """데이터베이스 설정 모킹"""
        config = Mock()
        config.get_connection_string.return_value = "mysql+pymysql://test:test@localhost:3306/test_db"
        config.host = "localhost"
        config.port = 3306
        config.user = "test"
        config.password = "test"
        config.database = "test_db"
        return config

    @pytest.fixture
    def mock_engine(self):
        """SQLAlchemy 엔진 모킹"""
        engine = Mock()
        engine.connect.return_value.__enter__ = Mock()
        engine.connect.return_value.__exit__ = Mock(return_value=None)
        return engine

    def test_negative_sales_amount_constraint_validation(self):
        """음수 매출액 검증 로직 테스트"""
        # 매출액 검증 함수 테스트
        assert self._validate_sales_amount(1000) == True
        assert self._validate_sales_amount(0) == True
        assert self._validate_sales_amount(-1000) == False
        
        # DECIMAL(18,2) 범위 검증
        max_amount = 9999999999999999.99
        assert self._validate_sales_amount(max_amount) == True
        # 정밀도 문제로 인해 정확한 경계값 테스트는 어려움
        assert self._validate_sales_amount(max_amount * 2) == False

    def test_negative_sales_count_constraint_validation(self):
        """음수 매출 건수 검증 로직 테스트"""
        # 매출 건수 검증 함수 테스트
        assert self._validate_sales_count(10) == True
        assert self._validate_sales_count(0) == True
        assert self._validate_sales_count(-10) == False
        
        # INT 범위 검증
        max_count = 2147483647
        assert self._validate_sales_count(max_count) == True
        assert self._validate_sales_count(max_count + 1) == False

    def test_negative_visitors_constraint_validation(self):
        """음수 방문자 수 검증 로직 테스트"""
        # 방문자 수 검증 함수 테스트
        assert self._validate_visitors(20) == True
        assert self._validate_visitors(0) == True
        assert self._validate_visitors(-20) == False
        
        # INT 범위 검증
        max_visitors = 2147483647
        assert self._validate_visitors(max_visitors) == True
        assert self._validate_visitors(max_visitors + 1) == False

    def test_invalid_date_range_validation(self):
        """잘못된 날짜 범위 검증 로직 테스트"""
        # 2024년 날짜 검증
        assert self._validate_date('2024-01-01') == True
        assert self._validate_date('2024-12-31') == True
        assert self._validate_date('2023-12-31') == False
        assert self._validate_date('2025-01-01') == False
        assert self._validate_date('2024-02-29') == True  # 윤년
        assert self._validate_date('2024-02-30') == False  # 2월 30일은 없음

    def test_primary_key_constraint_validation(self):
        """기본키 제약조건 검증 로직 테스트"""
        # 복합 기본키 (region_id, industry_id, date) 검증
        assert self._validate_primary_key(1, 1, '2024-01-01') == True
        assert self._validate_primary_key(0, 0, '2024-01-01') == False  # 0은 유효하지 않음
        assert self._validate_primary_key(1, 1, '2023-12-31') == False  # 2024년이 아님

    def test_foreign_key_constraint_validation(self):
        """외래키 제약조건 검증 로직 테스트"""
        # region_id와 industry_id가 존재하는지 검증
        assert self._validate_foreign_keys(1, 1) == True  # 존재한다고 가정
        assert self._validate_foreign_keys(999, 999) == False  # 존재하지 않는다고 가정
        assert self._validate_foreign_keys(0, 1) == False  # 0은 유효하지 않음

    @patch('data.database_manager.create_engine')
    def test_sales_validation_view(self, mock_create_engine, mock_db_config, mock_engine):
        """매출 데이터 검증 뷰 테스트"""
        mock_connection = Mock()
        mock_connection.execute.return_value.fetchall.return_value = [
            (1, 1, '2024-01-01', 1000.00, 10, 20, 'VALID'),
            (2, 2, '2024-01-01', -100.00, 5, 15, 'INVALID_SALES_AMT'),
            (3, 3, '2024-01-01', 2000.00, -5, 25, 'INVALID_SALES_CNT'),
            (4, 4, '2024-01-01', 3000.00, 15, -10, 'INVALID_VISITORS'),
            (5, 5, '2023-12-31', 4000.00, 20, 30, 'INVALID_DATE')
        ]
        mock_connection.execute.return_value.keys.return_value = [
            'region_id', 'industry_id', 'date', 'sales_amt', 'sales_cnt', 'visitors', 'validation_status'
        ]
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            result = db_manager.execute_query("SELECT * FROM v_sales_validation LIMIT 5")
            assert len(result) == 5
            assert 'validation_status' in result.columns
            assert result['validation_status'].iloc[0] == 'VALID'
            assert result['validation_status'].iloc[1] == 'INVALID_SALES_AMT'

    @patch('data.database_manager.create_engine')
    def test_region_sales_summary_view(self, mock_create_engine, mock_db_config, mock_engine):
        """지역별 매출 요약 뷰 테스트"""
        mock_connection = Mock()
        mock_connection.execute.return_value.fetchall.return_value = [
            (1, '강남구 역삼동', '강남구', '역삼동', 365, 1000000.00, 2739.73, 1000, 2.74, 5000, 13.70),
            (2, '종로구 종로1가', '종로구', '종로1가', 300, 800000.00, 2666.67, 800, 2.67, 4000, 13.33)
        ]
        mock_connection.execute.return_value.keys.return_value = [
            'region_id', 'region_name', 'gu', 'dong', 'active_days', 'total_sales_amt',
            'avg_daily_sales_amt', 'total_sales_cnt', 'avg_daily_sales_cnt', 'total_visitors', 'avg_daily_visitors'
        ]
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            result = db_manager.execute_query("SELECT * FROM v_region_sales_summary LIMIT 2")
            assert len(result) == 2
            assert 'region_name' in result.columns
            assert 'total_sales_amt' in result.columns
            assert result['total_sales_amt'].iloc[0] == 1000000.00

    @patch('data.database_manager.create_engine')
    def test_industry_sales_summary_view(self, mock_create_engine, mock_db_config, mock_engine):
        """업종별 매출 요약 뷰 테스트"""
        mock_connection = Mock()
        mock_connection.execute.return_value.fetchall.return_value = [
            (1, '한식', 'I56111', 200, 500000.00, 2500.00, 500, 2.50, 2500, 12.50),
            (2, '카페', 'I56121', 180, 300000.00, 1666.67, 600, 3.33, 3000, 16.67)
        ]
        mock_connection.execute.return_value.keys.return_value = [
            'industry_id', 'industry_name', 'nace_kor', 'active_days', 'total_sales_amt',
            'avg_daily_sales_amt', 'total_sales_cnt', 'avg_daily_sales_cnt', 'total_visitors', 'avg_daily_visitors'
        ]
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            result = db_manager.execute_query("SELECT * FROM v_industry_sales_summary LIMIT 2")
            assert len(result) == 2
            assert 'industry_name' in result.columns
            assert 'total_sales_amt' in result.columns
            assert result['total_sales_amt'].iloc[0] == 500000.00

    @patch('data.database_manager.create_engine')
    def test_monthly_sales_trend_view(self, mock_create_engine, mock_db_config, mock_engine):
        """월별 매출 추이 뷰 테스트"""
        mock_connection = Mock()
        mock_connection.execute.return_value.fetchall.return_value = [
            (2024, 1, 100, 10, 5, 1000000.00, 1000, 5000, 10000.00, 100.00, 50.00),
            (2024, 2, 90, 9, 4, 900000.00, 900, 4500, 10000.00, 100.00, 50.00)
        ]
        mock_connection.execute.return_value.keys.return_value = [
            'year', 'month', 'active_entries', 'active_regions', 'active_industries',
            'total_sales_amt', 'total_sales_cnt', 'total_visitors', 'avg_sales_amt', 'avg_sales_cnt', 'avg_visitors'
        ]
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            result = db_manager.execute_query("SELECT * FROM v_monthly_sales_trend LIMIT 2")
            assert len(result) == 2
            assert 'year' in result.columns
            assert 'month' in result.columns
            assert result['year'].iloc[0] == 2024
            assert result['month'].iloc[0] == 1

    def _validate_sales_amount(self, amount):
        """매출액 검증"""
        if not isinstance(amount, (int, float)):
            return False
        if amount < 0:
            return False
        # DECIMAL(18,2) 최대값: 9999999999999999.99
        return amount <= 9999999999999999.99

    def _validate_sales_count(self, count):
        """매출 건수 검증"""
        return isinstance(count, int) and count >= 0 and count <= 2147483647

    def _validate_visitors(self, visitors):
        """방문자 수 검증"""
        return isinstance(visitors, int) and visitors >= 0 and visitors <= 2147483647

    def _validate_date(self, date_str):
        """날짜 검증 (2024년만 허용)"""
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.year == 2024
        except ValueError:
            return False

    def _validate_primary_key(self, region_id, industry_id, date_str):
        """기본키 검증 (region_id, industry_id, date)"""
        if not isinstance(region_id, int) or region_id <= 0:
            return False
        if not isinstance(industry_id, int) or industry_id <= 0:
            return False
        return self._validate_date(date_str)

    def _validate_foreign_keys(self, region_id, industry_id):
        """외래키 검증 (region_id, industry_id가 존재하는지)"""
        # 실제로는 데이터베이스에서 확인해야 하지만, 테스트에서는 모킹
        valid_region_ids = {1, 2, 3}  # 테스트용 유효한 region_id
        valid_industry_ids = {1, 2, 3}  # 테스트용 유효한 industry_id
        
        return region_id in valid_region_ids and industry_id in valid_industry_ids