"""
SQL Text-to-SQL 모듈 테스트
TEST 폴더에 보관되는 테스트 파일
"""

import unittest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.sql_text2sql import nl_to_sql, validate_sql

class TestSQLText2SQL(unittest.TestCase):
    """SQL Text-to-SQL 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.schema_prompt = "테이블: sales_2024, regions, industries"
        self.llm_cfg = {"model": "test-model"}
    
    def test_nl_to_sql_basic_query(self):
        """기본 자연어 질의 테스트"""
        query = "강남구 매출 분석"
        result = nl_to_sql(query, self.schema_prompt, self.llm_cfg)
        
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("SELECT"))
        self.assertIn("LIMIT", result)
    
    def test_nl_to_sql_empty_query(self):
        """빈 질의 테스트"""
        query = ""
        result = nl_to_sql(query, self.schema_prompt, self.llm_cfg)
        
        self.assertEqual(result, "SELECT 1 as error WHERE 1=0")
    
    def test_nl_to_sql_sales_query(self):
        """매출 관련 질의 테스트"""
        query = "2024년 월별 매출 추세"
        result = nl_to_sql(query, self.schema_prompt, self.llm_cfg)
        
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("SELECT"))
        self.assertIn("sales_amt", result)
        self.assertIn("LIMIT", result)
    
    def test_nl_to_sql_region_query(self):
        """지역 관련 질의 테스트"""
        query = "지역별 매출 순위"
        result = nl_to_sql(query, self.schema_prompt, self.llm_cfg)
        
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("SELECT"))
        self.assertIn("region", result)
        self.assertIn("LIMIT", result)
    
    def test_nl_to_sql_forbidden_keywords(self):
        """금지된 키워드 테스트"""
        query = "DELETE FROM sales_2024"
        result = nl_to_sql(query, self.schema_prompt, self.llm_cfg)
        
        self.assertEqual(result, "SELECT 1 as error WHERE 1=0")
    
    def test_validate_sql_valid_select(self):
        """유효한 SELECT 쿼리 검증 테스트"""
        sql = "SELECT * FROM sales_2024 LIMIT 10"
        result = validate_sql(sql)
        
        self.assertTrue(result["valid"])
        self.assertIn("sql", result)
    
    def test_validate_sql_invalid_insert(self):
        """유효하지 않은 INSERT 쿼리 검증 테스트"""
        sql = "INSERT INTO sales_2024 VALUES (1, 2, 3)"
        result = validate_sql(sql)
        
        self.assertFalse(result["valid"])
        self.assertIn("SELECT 쿼리만 허용", result["message"])
    
    def test_validate_sql_forbidden_keywords(self):
        """금지된 키워드 검증 테스트"""
        sql = "SELECT * FROM sales_2024; DROP TABLE sales_2024;"
        result = validate_sql(sql)
        
        self.assertFalse(result["valid"])
        self.assertIn("금지된 키워드", result["message"])
    
    def test_validate_sql_adds_limit(self):
        """LIMIT 자동 추가 테스트"""
        sql = "SELECT * FROM sales_2024"
        result = validate_sql(sql)
        
        self.assertTrue(result["valid"])
        self.assertIn("LIMIT 1000", result["sql"])

if __name__ == "__main__":
    unittest.main()
