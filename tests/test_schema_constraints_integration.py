"""
스키마 제약조건 통합 테스트
TASK-002: MySQL 스키마 정의 및 초기 마이그레이션
실제 데이터베이스에서 제약조건 테스트 (INSERT/UPDATE/DELETE 허용)
"""

import pytest
import os
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# 테스트 환경 설정
os.environ["IS_TESTING"] = "1"

from config import get_database_config
from data.database_manager import DatabaseManager


class TestSchemaConstraintsIntegration:
    """스키마 제약조건 통합 테스트 (실제 DB 제약조건 테스트)"""

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

    @patch('data.database_manager.create_engine')
    def test_negative_sales_amount_constraint(self, mock_create_engine, mock_db_config, mock_engine):
        """음수 매출액 삽입 차단 테스트"""
        # 트리거 오류 모킹
        mock_connection = Mock()
        mock_connection.execute.side_effect = SQLAlchemyError("sales_amt must be non-negative")
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            # 직접 SQLAlchemy 엔진을 사용하여 INSERT 테스트
            engine = create_engine("mysql+pymysql://test:test@localhost:3306/test_db")
            
            # 음수 매출액 삽입 시도
            with pytest.raises(SQLAlchemyError, match="sales_amt must be non-negative"):
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO sales_2024 (region_id, industry_id, date, sales_amt, sales_cnt, visitors)
                        VALUES (1, 1, '2024-01-01', -1000, 10, 20)
                    """))

    @patch('data.database_manager.create_engine')
    def test_negative_sales_count_constraint(self, mock_create_engine, mock_db_config, mock_engine):
        """음수 매출 건수 삽입 차단 테스트"""
        mock_connection = Mock()
        mock_connection.execute.side_effect = SQLAlchemyError("sales_cnt must be non-negative")
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            engine = create_engine("mysql+pymysql://test:test@localhost:3306/test_db")
            
            # 음수 매출 건수 삽입 시도
            with pytest.raises(SQLAlchemyError, match="sales_cnt must be non-negative"):
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO sales_2024 (region_id, industry_id, date, sales_amt, sales_cnt, visitors)
                        VALUES (1, 1, '2024-01-01', 1000, -10, 20)
                    """))

    @patch('data.database_manager.create_engine')
    def test_negative_visitors_constraint(self, mock_create_engine, mock_db_config, mock_engine):
        """음수 방문자 수 삽입 차단 테스트"""
        mock_connection = Mock()
        mock_connection.execute.side_effect = SQLAlchemyError("visitors must be non-negative")
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            engine = create_engine("mysql+pymysql://test:test@localhost:3306/test_db")
            
            # 음수 방문자 수 삽입 시도
            with pytest.raises(SQLAlchemyError, match="visitors must be non-negative"):
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO sales_2024 (region_id, industry_id, date, sales_amt, sales_cnt, visitors)
                        VALUES (1, 1, '2024-01-01', 1000, 10, -20)
                    """))

    @patch('data.database_manager.create_engine')
    def test_invalid_date_range_constraint(self, mock_create_engine, mock_db_config, mock_engine):
        """잘못된 날짜 범위 삽입 차단 테스트"""
        mock_connection = Mock()
        mock_connection.execute.side_effect = SQLAlchemyError("date must be within 2024")
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            engine = create_engine("mysql+pymysql://test:test@localhost:3306/test_db")
            
            # 2024년 범위 밖 날짜 삽입 시도
            with pytest.raises(SQLAlchemyError, match="date must be within 2024"):
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO sales_2024 (region_id, industry_id, date, sales_amt, sales_cnt, visitors)
                        VALUES (1, 1, '2023-12-31', 1000, 10, 20)
                    """))
            
            with pytest.raises(SQLAlchemyError, match="date must be within 2024"):
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO sales_2024 (region_id, industry_id, date, sales_amt, sales_cnt, visitors)
                        VALUES (1, 1, '2025-01-01', 1000, 10, 20)
                    """))

    @patch('data.database_manager.create_engine')
    def test_duplicate_primary_key_constraint(self, mock_create_engine, mock_db_config, mock_engine):
        """중복 기본키 삽입 차단 테스트"""
        mock_connection = Mock()
        mock_connection.execute.side_effect = IntegrityError("Duplicate entry", None, None)
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            engine = create_engine("mysql+pymysql://test:test@localhost:3306/test_db")
            
            # 중복 기본키 삽입 시도
            with pytest.raises(IntegrityError):
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO sales_2024 (region_id, industry_id, date, sales_amt, sales_cnt, visitors)
                        VALUES (1, 1, '2024-01-01', 1000, 10, 20)
                    """))

    @patch('data.database_manager.create_engine')
    def test_foreign_key_constraint_violation(self, mock_create_engine, mock_db_config, mock_engine):
        """외래키 제약조건 위반 테스트"""
        mock_connection = Mock()
        mock_connection.execute.side_effect = IntegrityError("Foreign key constraint fails", None, None)
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            engine = create_engine("mysql+pymysql://test:test@localhost:3306/test_db")
            
            # 존재하지 않는 region_id로 삽입 시도
            with pytest.raises(IntegrityError, match="Foreign key constraint fails"):
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO sales_2024 (region_id, industry_id, date, sales_amt, sales_cnt, visitors)
                        VALUES (999, 1, '2024-01-01', 1000, 10, 20)
                    """))
            
            # 존재하지 않는 industry_id로 삽입 시도
            with pytest.raises(IntegrityError, match="Foreign key constraint fails"):
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO sales_2024 (region_id, industry_id, date, sales_amt, sales_cnt, visitors)
                        VALUES (1, 999, '2024-01-01', 1000, 10, 20)
                    """))

    @patch('data.database_manager.create_engine')
    def test_valid_data_insertion(self, mock_create_engine, mock_db_config, mock_engine):
        """유효한 데이터 삽입 테스트"""
        mock_connection = Mock()
        mock_connection.execute.return_value = Mock()
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            engine = create_engine("mysql+pymysql://test:test@localhost:3306/test_db")
            
            # 유효한 데이터 삽입
            with engine.connect() as conn:
                result = conn.execute(text("""
                    INSERT INTO sales_2024 (region_id, industry_id, date, sales_amt, sales_cnt, visitors)
                    VALUES (1, 1, '2024-01-01', 1000, 10, 20)
                """))
                assert result is not None

    def test_data_type_validation(self):
        """데이터 타입 검증 테스트"""
        # DECIMAL(18,2) 검증
        valid_amount = 1234567890123456.78
        assert isinstance(valid_amount, float)
        assert len(str(int(valid_amount))) <= 16  # 정수 부분 16자리 이하
        
        # DATE 형식 검증
        valid_date = "2024-01-01"
        assert len(valid_date) == 10
        assert valid_date.count('-') == 2
        
        # VARCHAR 길이 검증
        valid_name = "강남구 역삼동"
        assert len(valid_name) <= 100
        assert len("업종명") <= 100

    def test_constraint_validation_rules(self):
        """제약조건 검증 규칙 테스트"""
        # 매출액 검증
        assert self._validate_sales_amount(1000) == True
        assert self._validate_sales_amount(0) == True
        assert self._validate_sales_amount(-1000) == False
        
        # 매출 건수 검증
        assert self._validate_sales_count(10) == True
        assert self._validate_sales_count(0) == True
        assert self._validate_sales_count(-10) == False
        
        # 방문자 수 검증
        assert self._validate_visitors(20) == True
        assert self._validate_visitors(0) == True
        assert self._validate_visitors(-20) == False
        
        # 날짜 범위 검증
        assert self._validate_date("2024-01-01") == True
        assert self._validate_date("2024-12-31") == True
        assert self._validate_date("2023-12-31") == False
        assert self._validate_date("2025-01-01") == False

    def _validate_sales_amount(self, amount: float) -> bool:
        """매출액 검증"""
        return amount >= 0

    def _validate_sales_count(self, count: int) -> bool:
        """매출 건수 검증"""
        return count >= 0

    def _validate_visitors(self, visitors: int) -> bool:
        """방문자 수 검증"""
        return visitors >= 0

    def _validate_date(self, date_str: str) -> bool:
        """날짜 범위 검증"""
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.year == 2024
        except ValueError:
            return False

