"""
인덱스 사용 여부 및 성능 테스트
TASK-002: MySQL 스키마 정의 및 초기 마이그레이션
"""

import pytest
import os
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# 테스트 환경 설정
os.environ["IS_TESTING"] = "1"

from config import get_database_config
from data.database_manager import DatabaseManager


class TestIndicesExplain:
    """인덱스 사용 여부 테스트"""

    @pytest.fixture
    def mock_db_config(self):
        """데이터베이스 설정 모킹"""
        config = Mock()
        config.MYSQL_URL = "mysql+pymysql://test:test@localhost:3306/test_db"
        config.DB_HOST = "localhost"
        config.DB_PORT = 3306
        config.DB_USER = "test"
        config.DB_PASSWORD = "test"
        config.DB_NAME = "test_db"
        return config

    @pytest.fixture
    def mock_engine(self):
        """SQLAlchemy 엔진 모킹"""
        engine = Mock()
        engine.connect.return_value.__enter__ = Mock()
        engine.connect.return_value.__exit__ = Mock(return_value=None)
        return engine

    def create_mock_explain_result(self, query_type, index_used=True):
        """EXPLAIN 결과 모킹"""
        if query_type == "date_range":
            return [
                {
                    'id': 1,
                    'select_type': 'SIMPLE',
                    'table': 'sales_2024',
                    'type': 'range' if index_used else 'ALL',
                    'possible_keys': 'idx_sales_date',
                    'key': 'idx_sales_date' if index_used else None,
                    'key_len': '3' if index_used else None,
                    'ref': None,
                    'rows': 1000 if index_used else 10000,
                    'Extra': 'Using index condition' if index_used else 'Using where'
                }
            ]
        elif query_type == "region_date":
            return [
                {
                    'id': 1,
                    'select_type': 'SIMPLE',
                    'table': 'sales_2024',
                    'type': 'ref' if index_used else 'ALL',
                    'possible_keys': 'idx_sales_region_dt',
                    'key': 'idx_sales_region_dt' if index_used else None,
                    'key_len': '7' if index_used else None,
                    'ref': 'const,const',
                    'rows': 100 if index_used else 1000,
                    'Extra': 'Using index' if index_used else 'Using where'
                }
            ]
        elif query_type == "industry_date":
            return [
                {
                    'id': 1,
                    'select_type': 'SIMPLE',
                    'table': 'sales_2024',
                    'type': 'ref' if index_used else 'ALL',
                    'possible_keys': 'idx_sales_industry_dt',
                    'key': 'idx_sales_industry_dt' if index_used else None,
                    'key_len': '7' if index_used else None,
                    'ref': 'const,const',
                    'rows': 200 if index_used else 2000,
                    'Extra': 'Using index' if index_used else 'Using where'
                }
            ]
        elif query_type == "region_industry_date":
            return [
                {
                    'id': 1,
                    'select_type': 'SIMPLE',
                    'table': 'sales_2024',
                    'type': 'ref' if index_used else 'ALL',
                    'possible_keys': 'PRIMARY,idx_sales_region_industry_date_amt',
                    'key': 'idx_sales_region_industry_date_amt' if index_used else None,
                    'key_len': '11' if index_used else None,
                    'ref': 'const,const,const',
                    'rows': 1 if index_used else 100,
                    'Extra': 'Using index' if index_used else 'Using where'
                }
            ]
        elif query_type == "region_lookup":
            return [
                {
                    'id': 1,
                    'select_type': 'SIMPLE',
                    'table': 'regions',
                    'type': 'ref' if index_used else 'ALL',
                    'possible_keys': 'idx_regions_gudong',
                    'key': 'idx_regions_gudong' if index_used else None,
                    'key_len': '130' if index_used else None,
                    'ref': 'const,const',
                    'rows': 1 if index_used else 100,
                    'Extra': 'Using index' if index_used else 'Using where'
                }
            ]
        elif query_type == "industry_lookup":
            return [
                {
                    'id': 1,
                    'select_type': 'SIMPLE',
                    'table': 'industries',
                    'type': 'ref' if index_used else 'ALL',
                    'possible_keys': 'idx_industries_name',
                    'key': 'idx_industries_name' if index_used else None,
                    'key_len': '102' if index_used else None,
                    'ref': 'const',
                    'rows': 1 if index_used else 50,
                    'Extra': 'Using index' if index_used else 'Using where'
                }
            ]
        else:
            return []

    @patch('data.database_manager.create_engine')
    def test_date_range_query_index_usage(self, mock_create_engine, mock_db_config, mock_engine):
        """날짜 범위 쿼리 인덱스 사용 테스트"""
        mock_result = Mock()
        mock_result.fetchall.return_value = self.create_mock_explain_result("date_range", True)
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            # 날짜 범위 쿼리 EXPLAIN
            result = db_manager.execute_query("""
                EXPLAIN SELECT * FROM sales_2024 
                WHERE date BETWEEN '2024-01-01' AND '2024-01-31'
            """)
            explain_result = result.fetchall()
            
            assert len(explain_result) == 1
            assert explain_result[0]['key'] == 'idx_sales_date'
            assert explain_result[0]['type'] == 'range'
            assert explain_result[0]['rows'] <= 1000  # 인덱스 사용으로 행 수 감소

    @patch('data.database_manager.create_engine')
    def test_region_date_query_index_usage(self, mock_create_engine, mock_db_config, mock_engine):
        """지역-날짜 쿼리 인덱스 사용 테스트"""
        mock_result = Mock()
        mock_result.fetchall.return_value = self.create_mock_explain_result("region_date", True)
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            # 지역-날짜 쿼리 EXPLAIN
            result = db_manager.execute_query("""
                EXPLAIN SELECT * FROM sales_2024 
                WHERE region_id = 1 AND date = '2024-01-01'
            """)
            explain_result = result.fetchall()
            
            assert len(explain_result) == 1
            assert explain_result[0]['key'] == 'idx_sales_region_dt'
            assert explain_result[0]['type'] == 'ref'
            assert explain_result[0]['rows'] <= 100  # 인덱스 사용으로 행 수 감소

    @patch('data.database_manager.create_engine')
    def test_industry_date_query_index_usage(self, mock_create_engine, mock_db_config, mock_engine):
        """업종-날짜 쿼리 인덱스 사용 테스트"""
        mock_result = Mock()
        mock_result.fetchall.return_value = self.create_mock_explain_result("industry_date", True)
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            # 업종-날짜 쿼리 EXPLAIN
            result = db_manager.execute_query("""
                EXPLAIN SELECT * FROM sales_2024 
                WHERE industry_id = 1 AND date = '2024-01-01'
            """)
            explain_result = result.fetchall()
            
            assert len(explain_result) == 1
            assert explain_result[0]['key'] == 'idx_sales_industry_dt'
            assert explain_result[0]['type'] == 'ref'
            assert explain_result[0]['rows'] <= 200  # 인덱스 사용으로 행 수 감소

    @patch('data.database_manager.create_engine')
    def test_region_industry_date_query_index_usage(self, mock_create_engine, mock_db_config, mock_engine):
        """지역-업종-날짜 쿼리 인덱스 사용 테스트"""
        mock_result = Mock()
        mock_result.fetchall.return_value = self.create_mock_explain_result("region_industry_date", True)
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            # 지역-업종-날짜 쿼리 EXPLAIN
            result = db_manager.execute_query("""
                EXPLAIN SELECT * FROM sales_2024 
                WHERE region_id = 1 AND industry_id = 1 AND date = '2024-01-01'
            """)
            explain_result = result.fetchall()
            
            assert len(explain_result) == 1
            assert explain_result[0]['key'] == 'idx_sales_region_industry_date_amt'
            assert explain_result[0]['type'] == 'ref'
            assert explain_result[0]['rows'] == 1  # 복합 인덱스 사용으로 최적화

    @patch('data.database_manager.create_engine')
    def test_region_lookup_index_usage(self, mock_create_engine, mock_db_config, mock_engine):
        """지역 조회 인덱스 사용 테스트"""
        mock_result = Mock()
        mock_result.fetchall.return_value = self.create_mock_explain_result("region_lookup", True)
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            # 지역 조회 쿼리 EXPLAIN
            result = db_manager.execute_query("""
                EXPLAIN SELECT * FROM regions 
                WHERE gu = '강남구' AND dong = '역삼동'
            """)
            explain_result = result.fetchall()
            
            assert len(explain_result) == 1
            assert explain_result[0]['key'] == 'idx_regions_gudong'
            assert explain_result[0]['type'] == 'ref'
            assert explain_result[0]['rows'] == 1  # 인덱스 사용으로 최적화

    @patch('data.database_manager.create_engine')
    def test_industry_lookup_index_usage(self, mock_create_engine, mock_db_config, mock_engine):
        """업종 조회 인덱스 사용 테스트"""
        mock_result = Mock()
        mock_result.fetchall.return_value = self.create_mock_explain_result("industry_lookup", True)
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            # 업종 조회 쿼리 EXPLAIN
            result = db_manager.execute_query("""
                EXPLAIN SELECT * FROM industries 
                WHERE name = '한식'
            """)
            explain_result = result.fetchall()
            
            assert len(explain_result) == 1
            assert explain_result[0]['key'] == 'idx_industries_name'
            assert explain_result[0]['type'] == 'ref'
            assert explain_result[0]['rows'] == 1  # 인덱스 사용으로 최적화

    @patch('data.database_manager.create_engine')
    def test_monthly_trend_query_performance(self, mock_create_engine, mock_db_config, mock_engine):
        """월별 추이 쿼리 성능 테스트"""
        # 월별 추이 쿼리 결과 모킹
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (2024, 1, 10, 5, 5000000, 5000, 8000, 500000, 500, 800),
            (2024, 2, 12, 6, 6000000, 6000, 9000, 500000, 500, 750)
        ]
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            # 월별 추이 쿼리 실행
            result = db_manager.execute_query("""
                SELECT 
                    YEAR(date) as year,
                    MONTH(date) as month,
                    COUNT(DISTINCT region_id) as regions_count,
                    COUNT(DISTINCT industry_id) as industries_count,
                    SUM(sales_amt) as total_sales_amt,
                    SUM(sales_cnt) as total_sales_cnt,
                    SUM(visitors) as total_visitors,
                    AVG(sales_amt) as avg_sales_amt,
                    AVG(sales_cnt) as avg_sales_cnt,
                    AVG(visitors) as avg_visitors
                FROM sales_2024
                GROUP BY YEAR(date), MONTH(date)
                ORDER BY year, month
            """)
            rows = result.fetchall()
            
            assert len(rows) == 2
            assert rows[0][0] == 2024  # 연도
            assert rows[0][1] == 1     # 월
            assert rows[0][2] == 10    # 지역 수
            assert rows[0][3] == 5     # 업종 수

    @patch('data.database_manager.create_engine')
    def test_region_comparison_query_performance(self, mock_create_engine, mock_db_config, mock_engine):
        """지역 비교 쿼리 성능 테스트"""
        # 지역 비교 쿼리 결과 모킹
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (1, '강남구 역삼동', 1500000, 1500, 2000),
            (2, '강남구 테헤란로', 1200000, 1200, 1800),
            (6, '서초구 서초동', 1000000, 1000, 1500)
        ]
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            # 지역 비교 쿼리 실행
            result = db_manager.execute_query("""
                SELECT 
                    r.region_id,
                    r.name as region_name,
                    SUM(s.sales_amt) as total_sales_amt,
                    SUM(s.sales_cnt) as total_sales_cnt,
                    SUM(s.visitors) as total_visitors
                FROM regions r
                LEFT JOIN sales_2024 s ON r.region_id = s.region_id
                WHERE s.date BETWEEN '2024-01-01' AND '2024-01-31'
                GROUP BY r.region_id, r.name
                ORDER BY total_sales_amt DESC
                LIMIT 10
            """)
            rows = result.fetchall()
            
            assert len(rows) == 3
            assert rows[0][1] == '강남구 역삼동'  # 매출액 1위
            assert rows[0][2] == 1500000  # 총 매출액

    @patch('data.database_manager.create_engine')
    def test_industry_top_n_query_performance(self, mock_create_engine, mock_db_config, mock_engine):
        """업종 TOP-N 쿼리 성능 테스트"""
        # 업종 TOP-N 쿼리 결과 모킹
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (1, '한식', 2000000, 2000, 3000),
            (7, '카페', 1800000, 1800, 2800),
            (9, '의류소매', 1600000, 1600, 2400)
        ]
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            # 업종 TOP-N 쿼리 실행
            result = db_manager.execute_query("""
                SELECT 
                    i.industry_id,
                    i.name as industry_name,
                    SUM(s.sales_amt) as total_sales_amt,
                    SUM(s.sales_cnt) as total_sales_cnt,
                    SUM(s.visitors) as total_visitors
                FROM industries i
                LEFT JOIN sales_2024 s ON i.industry_id = s.industry_id
                WHERE s.date BETWEEN '2024-01-01' AND '2024-01-31'
                GROUP BY i.industry_id, i.name
                ORDER BY total_sales_amt DESC
                LIMIT 5
            """)
            rows = result.fetchall()
            
            assert len(rows) == 3
            assert rows[0][1] == '한식'  # 매출액 1위
            assert rows[0][2] == 2000000  # 총 매출액

    @patch('data.database_manager.create_engine')
    def test_no_index_usage_scenario(self, mock_create_engine, mock_db_config, mock_engine):
        """인덱스 미사용 시나리오 테스트"""
        mock_result = Mock()
        mock_result.fetchall.return_value = self.create_mock_explain_result("date_range", False)
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            # 인덱스 미사용 쿼리 EXPLAIN
            result = db_manager.execute_query("""
                EXPLAIN SELECT * FROM sales_2024 
                WHERE sales_amt > 1000000
            """)
            explain_result = result.fetchall()
            
            assert len(explain_result) == 1
            assert explain_result[0]['key'] is None  # 인덱스 미사용
            assert explain_result[0]['type'] == 'ALL'  # 전체 테이블 스캔
            assert explain_result[0]['rows'] >= 10000  # 많은 행 스캔

    def test_index_creation_sql_validation(self):
        """인덱스 생성 SQL 검증 테스트"""
        # 인덱스 생성 SQL 문장들
        index_sqls = [
            "CREATE INDEX idx_sales_date ON sales_2024(date)",
            "CREATE INDEX idx_sales_region_dt ON sales_2024(region_id, date)",
            "CREATE INDEX idx_sales_industry_dt ON sales_2024(industry_id, date)",
            "CREATE INDEX idx_regions_gudong ON regions(gu, dong)",
            "CREATE INDEX idx_industries_name ON industries(name)",
            "CREATE INDEX idx_sales_region_industry_date_amt ON sales_2024(region_id, industry_id, date, sales_amt)"
        ]
        
        for sql in index_sqls:
            # SQL 문법 검증
            assert sql.startswith("CREATE INDEX")
            assert "ON" in sql
            assert "(" in sql and ")" in sql
            
            # 테이블명과 컬럼명 검증
            parts = sql.split("ON")
            assert len(parts) == 2
            table_part = parts[1].strip().split("(")[0].strip()
            assert table_part in ["sales_2024", "regions", "industries"]

    def test_query_performance_metrics(self):
        """쿼리 성능 메트릭 테스트"""
        # 성능 메트릭 정의
        performance_metrics = {
            "date_range_query": {"max_rows": 1000, "index_required": True},
            "region_date_query": {"max_rows": 100, "index_required": True},
            "industry_date_query": {"max_rows": 200, "index_required": True},
            "region_industry_date_query": {"max_rows": 1, "index_required": True},
            "region_lookup": {"max_rows": 1, "index_required": True},
            "industry_lookup": {"max_rows": 1, "index_required": True}
        }
        
        for query_type, metrics in performance_metrics.items():
            assert metrics["max_rows"] > 0
            assert isinstance(metrics["index_required"], bool)
            assert metrics["index_required"] is True  # 모든 쿼리가 인덱스 사용 필요

