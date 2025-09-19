"""
CSV 데이터 로더 모듈
PRD TASK2: CSV → MySQL ETL 로더 구현
"""

import pandas as pd
from typing import Dict, Any
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

def load_csv_to_mysql(csv_path: str, mysql_url: str = None) -> Dict[str, Any]:
    """
    CSV 파일을 MySQL에 로드하는 함수
    
    Args:
        csv_path: CSV 파일 경로
        mysql_url: MySQL 연결 URL (선택사항)
        
    Returns:
        로드 결과 딕셔너리
    """
    try:
        # CSV 파일 존재 확인
        if not os.path.exists(csv_path):
            return {"status": "error", "message": f"CSV 파일을 찾을 수 없습니다: {csv_path}"}
        
        # MySQL URL이 제공된 경우 ETL 파이프라인 실행
        if mysql_url:
            from pipelines.etl_csv_to_mysql import run_csv_to_mysql_etl
            return run_csv_to_mysql_etl(csv_path, mysql_url)
        
        # 기본 CSV 읽기 (스키마 검증용)
        df = pd.read_csv(csv_path, encoding='cp949')
        
        # 기본 검증
        if df.empty:
            return {"status": "error", "message": "CSV 파일이 비어있습니다."}
        
        # 필수 컬럼 검증
        required_columns = [
            '기준_년분기_코드', '상권_코드', '서비스_업종_코드', 
            '당월_매출_금액', '당월_매출_건수'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "status": "error", 
                "message": f"필수 컬럼이 누락되었습니다: {missing_columns}"
            }
        
        # 데이터 정제 (기본)
        df_cleaned = df.dropna(subset=required_columns)
        
        logger.info(f"CSV 로드 완료: {len(df_cleaned)}행, {len(df_cleaned.columns)}열")
        
        return {
            "status": "success",
            "rows_loaded": len(df_cleaned),
            "columns": list(df_cleaned.columns),
            "data": df_cleaned,
            "message": "CSV 파일이 성공적으로 로드되었습니다. MySQL에 저장하려면 mysql_url을 제공하세요."
        }
        
    except Exception as e:
        logger.error(f"CSV 로드 실패: {str(e)}")
        return {"status": "error", "message": str(e)}

def get_csv_file_info(csv_path: str) -> Dict[str, Any]:
    """
    CSV 파일 정보 조회
    
    Args:
        csv_path: CSV 파일 경로
        
    Returns:
        파일 정보 딕셔너리
    """
    try:
        if not os.path.exists(csv_path):
            return {"status": "error", "message": "파일을 찾을 수 없습니다."}
        
        # 파일 크기
        file_size = os.path.getsize(csv_path)
        
        # CSV 미리보기
        df = pd.read_csv(csv_path, encoding='cp949', nrows=5)
        
        return {
            "status": "success",
            "file_path": csv_path,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "columns": list(df.columns),
            "sample_data": df.to_dict('records'),
            "total_columns": len(df.columns)
        }
        
    except Exception as e:
        logger.error(f"CSV 파일 정보 조회 실패: {str(e)}")
        return {"status": "error", "message": str(e)}
