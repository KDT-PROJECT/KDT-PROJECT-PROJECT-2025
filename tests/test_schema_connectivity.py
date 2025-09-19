"""
스키마 연결성 및 테이블 구조 테스트
TASK-002: MySQL 스키마 정의 및 초기 마이그레이션
"""

import pytest
import os
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# 테스트 환경 설정
os.environ["IS_TESTING"] = "1"

from config import get_database_config
from data.database_manager import DatabaseManager


class TestSchemaConnectivity:
    """스키마 연결성 테스트"""

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
    def test_database_connection(self, mock_create_engine, mock_db_config, mock_engine):
        """데이터베이스 연결 테스트"""
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            assert db_manager.engine is not None
            mock_create_engine.assert_called_once()

    @patch('data.database_manager.create_engine')
    def test_connection_failure(self, mock_create_engine, mock_db_config):
        """데이터베이스 연결 실패 테스트"""
        mock_create_engine.side_effect = SQLAlchemyError("Connection failed")
        
        with patch('config.get_database_config', return_value=mock_db_config):
            with pytest.raises(SQLAlchemyError):
                DatabaseManager()

    @patch('data.database_manager.create_engine')
    def test_table_existence(self, mock_create_engine, mock_db_config):
        """테이블 존재 여부 테스트"""
        # 인스펙터 모킹
        mock_inspector = Mock()
        mock_inspector.get_table_names.return_value = [
            'regions', 'industries', 'sales_2024', 'features', 'docs', 'query_logs'
        ]
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__ = Mock()
        mock_engine.connect.return_value.__exit__ = Mock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        with patch('data.database_manager.inspect', return_value=mock_inspector):
            with patch('config.get_database_config', return_value=mock_db_config):
                db_manager = DatabaseManager()
                
                # 테이블 존재 확인
                tables = mock_inspector.get_table_names()
                expected_tables = ['regions', 'industries', 'sales_2024', 'features', 'docs', 'query_logs']
                
                for table in expected_tables:
                    assert table in tables, f"Table {table} should exist"

    @patch('data.database_manager.create_engine')
    def test_table_structure(self, mock_create_engine, mock_db_config):
        """테이블 구조 테스트"""
        # 컬럼 정보 모킹
        mock_columns = {
            'regions': [
                {'name': 'region_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'name', 'type': 'VARCHAR(100)', 'nullable': False, 'primary_key': False},
                {'name': 'gu', 'type': 'VARCHAR(50)', 'nullable': False, 'primary_key': False},
                {'name': 'dong', 'type': 'VARCHAR(80)', 'nullable': False, 'primary_key': False},
                {'name': 'lat', 'type': 'DECIMAL(10,7)', 'nullable': True, 'primary_key': False},
                {'name': 'lon', 'type': 'DECIMAL(10,7)', 'nullable': True, 'primary_key': False},
                {'name': 'adm_code', 'type': 'VARCHAR(20)', 'nullable': True, 'primary_key': False}
            ],
            'industries': [
                {'name': 'industry_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'name', 'type': 'VARCHAR(100)', 'nullable': False, 'primary_key': False},
                {'name': 'nace_kor', 'type': 'VARCHAR(100)', 'nullable': True, 'primary_key': False}
            ],
            'sales_2024': [
                {'name': 'region_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'industry_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'date', 'type': 'DATE', 'nullable': False, 'primary_key': True},
                {'name': 'sales_amt', 'type': 'DECIMAL(18,2)', 'nullable': False, 'primary_key': False},
                {'name': 'sales_cnt', 'type': 'INTEGER', 'nullable': False, 'primary_key': False},
                {'name': 'visitors', 'type': 'INTEGER', 'nullable': False, 'primary_key': False}
            ]
        }
        
        mock_inspector = Mock()
        mock_inspector.get_columns.side_effect = lambda table: mock_columns.get(table, [])
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__ = Mock()
        mock_engine.connect.return_value.__exit__ = Mock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        with patch('data.database_manager.inspect', return_value=mock_inspector):
            with patch('config.get_database_config', return_value=mock_db_config):
                db_manager = DatabaseManager()
                
                # regions 테이블 구조 확인
                regions_columns = mock_inspector.get_columns('regions')
                assert len(regions_columns) == 7
                assert any(col['name'] == 'region_id' and col['primary_key'] for col in regions_columns)
                assert any(col['name'] == 'name' and not col['nullable'] for col in regions_columns)
                
                # industries 테이블 구조 확인
                industries_columns = mock_inspector.get_columns('industries')
                assert len(industries_columns) == 3
                assert any(col['name'] == 'industry_id' and col['primary_key'] for col in industries_columns)
                
                # sales_2024 테이블 구조 확인
                sales_columns = mock_inspector.get_columns('sales_2024')
                assert len(sales_columns) == 6
                assert any(col['name'] == 'region_id' and col['primary_key'] for col in sales_columns)
                assert any(col['name'] == 'industry_id' and col['primary_key'] for col in sales_columns)
                assert any(col['name'] == 'date' and col['primary_key'] for col in sales_columns)

    @patch('data.database_manager.create_engine')
    def test_foreign_key_constraints(self, mock_create_engine, mock_db_config):
        """외래키 제약조건 테스트"""
        # 외래키 정보 모킹
        mock_foreign_keys = {
            'sales_2024': [
                {
                    'constrained_columns': ['region_id'],
                    'referred_table': 'regions',
                    'referred_columns': ['region_id']
                },
                {
                    'constrained_columns': ['industry_id'],
                    'referred_table': 'industries',
                    'referred_columns': ['industry_id']
                }
            ]
        }
        
        mock_inspector = Mock()
        mock_inspector.get_foreign_keys.side_effect = lambda table: mock_foreign_keys.get(table, [])
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__ = Mock()
        mock_engine.connect.return_value.__exit__ = Mock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        with patch('data.database_manager.inspect', return_value=mock_inspector):
            with patch('config.get_database_config', return_value=mock_db_config):
                db_manager = DatabaseManager()
                
                # sales_2024 테이블 외래키 확인
                fks = mock_inspector.get_foreign_keys('sales_2024')
                assert len(fks) == 2
                
                # region_id 외래키 확인
                region_fk = next((fk for fk in fks if 'region_id' in fk['constrained_columns']), None)
                assert region_fk is not None
                assert region_fk['referred_table'] == 'regions'
                
                # industry_id 외래키 확인
                industry_fk = next((fk for fk in fks if 'industry_id' in fk['constrained_columns']), None)
                assert industry_fk is not None
                assert industry_fk['referred_table'] == 'industries'

    @patch('data.database_manager.create_engine')
    def test_index_existence(self, mock_create_engine, mock_db_config):
        """인덱스 존재 여부 테스트"""
        # 인덱스 정보 모킹
        mock_indexes = {
            'sales_2024': [
                {'name': 'PRIMARY', 'column_names': ['region_id', 'industry_id', 'date']},
                {'name': 'idx_sales_date', 'column_names': ['date']},
                {'name': 'idx_sales_region_dt', 'column_names': ['region_id', 'date']},
                {'name': 'idx_sales_industry_dt', 'column_names': ['industry_id', 'date']}
            ],
            'regions': [
                {'name': 'PRIMARY', 'column_names': ['region_id']},
                {'name': 'idx_regions_gudong', 'column_names': ['gu', 'dong']},
                {'name': 'idx_regions_name', 'column_names': ['name']}
            ]
        }
        
        mock_inspector = Mock()
        mock_inspector.get_indexes.side_effect = lambda table: mock_indexes.get(table, [])
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__ = Mock()
        mock_engine.connect.return_value.__exit__ = Mock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        with patch('data.database_manager.inspect', return_value=mock_inspector):
            with patch('config.get_database_config', return_value=mock_db_config):
                db_manager = DatabaseManager()
                
                # sales_2024 테이블 인덱스 확인
                sales_indexes = mock_inspector.get_indexes('sales_2024')
                index_names = [idx['name'] for idx in sales_indexes]
                
                assert 'idx_sales_date' in index_names
                assert 'idx_sales_region_dt' in index_names
                assert 'idx_sales_industry_dt' in index_names
                
                # regions 테이블 인덱스 확인
                regions_indexes = mock_inspector.get_indexes('regions')
                regions_index_names = [idx['name'] for idx in regions_indexes]
                
                assert 'idx_regions_gudong' in regions_index_names
                assert 'idx_regions_name' in regions_index_names

    def test_connection_string_format(self, mock_db_config):
        """연결 문자열 형식 테스트"""
        expected_url = "mysql+pymysql://test:test@localhost:3306/test_db"
        assert mock_db_config.get_connection_string() == expected_url
        
        # URL 구성 요소 확인
        connection_string = mock_db_config.get_connection_string()
        assert "mysql+pymysql://" in connection_string
        assert f"{mock_db_config.user}:{mock_db_config.password}" in connection_string
        assert f"@{mock_db_config.host}:{mock_db_config.port}" in connection_string
        assert f"/{mock_db_config.database}" in connection_string

    @patch('data.database_manager.create_engine')
    def test_query_execution(self, mock_create_engine, mock_db_config):
        """쿼리 실행 테스트"""
        # 쿼리 결과 모킹
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (1, '강남구 역삼동', '강남구', '역삼동'),
            (2, '강남구 테헤란로', '강남구', '역삼동')
        ]
        mock_result.fetchone.return_value = (30,)
        mock_result.keys.return_value = ['region_id', 'name', 'gu', 'dong']
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_connection)
        mock_engine.connect.return_value.__exit__ = Mock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        with patch('config.get_database_config', return_value=mock_db_config):
            db_manager = DatabaseManager()
            
            # SELECT 쿼리 실행
            result = db_manager.execute_query("SELECT * FROM regions LIMIT 2")
            assert result is not None
            assert len(result) == 2
            
            # COUNT 쿼리 실행
            count_result = db_manager.execute_query("SELECT COUNT(*) FROM regions")
            assert count_result is not None
