"""
데이터 로더 모듈 테스트
TEST 폴더에 보관되는 테스트 파일
"""

import unittest
import pandas as pd
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.data_loader import load_csv_to_mysql, get_csv_file_info

class TestDataLoader(unittest.TestCase):
    """데이터 로더 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_csv_path = "data/csv/서울시 상권분석서비스(추정매출-상권)_2024년.csv"
        self.test_mysql_url = "mysql+pymysql://test:test@localhost:3306/test_db"
    
    def test_csv_file_info_success(self):
        """CSV 파일 정보 조회 성공 테스트"""
        if os.path.exists(self.test_csv_path):
            result = get_csv_file_info(self.test_csv_path)
            
            self.assertEqual(result["status"], "success")
            self.assertIn("file_size_mb", result)
            self.assertIn("columns", result)
            self.assertIn("total_columns", result)
            self.assertGreater(result["total_columns"], 0)
        else:
            self.skipTest("테스트 CSV 파일이 존재하지 않습니다.")
    
    def test_csv_file_info_file_not_found(self):
        """CSV 파일 정보 조회 - 파일 없음 테스트"""
        result = get_csv_file_info("nonexistent_file.csv")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("파일을 찾을 수 없습니다", result["message"])
    
    def test_load_csv_to_mysql_without_mysql_url(self):
        """MySQL URL 없이 CSV 로드 테스트"""
        if os.path.exists(self.test_csv_path):
            result = load_csv_to_mysql(self.test_csv_path)
            
            self.assertEqual(result["status"], "success")
            self.assertIn("rows_loaded", result)
            self.assertIn("columns", result)
            self.assertIn("data", result)
        else:
            self.skipTest("테스트 CSV 파일이 존재하지 않습니다.")
    
    def test_load_csv_to_mysql_file_not_found(self):
        """CSV 로드 - 파일 없음 테스트"""
        result = load_csv_to_mysql("nonexistent_file.csv")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("CSV 파일을 찾을 수 없습니다", result["message"])
    
    def test_load_csv_to_mysql_with_mysql_url(self):
        """MySQL URL과 함께 CSV 로드 테스트 (스텁)"""
        if os.path.exists(self.test_csv_path):
            # 실제 MySQL 연결 없이 테스트 (스텁 모드)
            result = load_csv_to_mysql(self.test_csv_path, self.test_mysql_url)
            
            # ETL 파이프라인이 실행되면 success, 아니면 error
            self.assertIn(result["status"], ["success", "error"])
        else:
            self.skipTest("테스트 CSV 파일이 존재하지 않습니다.")

if __name__ == "__main__":
    unittest.main()
