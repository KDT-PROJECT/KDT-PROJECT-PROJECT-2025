"""
Seoul Commercial Analysis LLM Application
TASK-004: Streamlit 프런트엔드(UI/UX) 구현 - 메인 애플리케이션
"""

import logging
import sys
import os
from pathlib import Path

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Import the new app structure
from utils.app_structure import get_app
from utils.database import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_database():
    """데이터베이스 초기화 함수"""
    try:
        logger.info("데이터베이스 초기화를 시작합니다...")
        
        # 데이터베이스 매니저 생성
        db_manager = DatabaseManager()
        
        # 데이터베이스 생성
        if db_manager.create_database():
            logger.info("데이터베이스 생성 완료")
        else:
            logger.error("데이터베이스 생성 실패")
            return False
        
        # 데이터베이스 연결
        if db_manager.connect():
            logger.info("데이터베이스 연결 완료")
        else:
            logger.error("데이터베이스 연결 실패")
            return False
        
        # 테이블 생성
        if db_manager.create_tables():
            logger.info("테이블 생성 완료")
        else:
            logger.error("테이블 생성 실패")
            return False
        
        # 샘플 데이터 삽입 (필요한 경우)
        insert_sample_data(db_manager)
        
        # 연결 해제
        db_manager.disconnect()
        
        logger.info("데이터베이스 초기화 완료")
        return True
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류 발생: {e}")
        return False


def insert_sample_data(db_manager: DatabaseManager):
    """샘플 데이터 삽입"""
    try:
        logger.info("샘플 데이터 삽입을 시작합니다...")
        
        # 샘플 지역 데이터
        sample_regions = pd.DataFrame({
            'name': ['강남구', '서초구', '송파구', '마포구', '홍대입구'],
            'gu': ['강남구', '서초구', '송파구', '마포구', '마포구'],
            'dong': ['역삼동', '서초동', '잠실동', '홍대입구역', '홍대입구역'],
            'lat': [37.5665, 37.4837, 37.5133, 37.5563, 37.5563],
            'lon': [126.9780, 127.0324, 127.1028, 126.9236, 126.9236],
            'adm_code': ['1168010100', '1165010100', '1171010100', '1144012100', '1144012100']
        })
        
        # 샘플 업종 데이터
        sample_industries = pd.DataFrame({
            'name': ['카페', '음식점', '편의점', '의류매장', '서점'],
            'nace_kor': ['I5610', 'I5610', 'G4711', 'G4741', 'G4761'],
            'category': ['음식업', '음식업', '소매업', '소매업', '소매업']
        })
        
        # 데이터 삽입
        if db_manager.insert_dataframe(sample_regions, 'regions', 'append'):
            logger.info("샘플 지역 데이터 삽입 완료")
        
        if db_manager.insert_dataframe(sample_industries, 'industries', 'append'):
            logger.info("샘플 업종 데이터 삽입 완료")
        
        logger.info("샘플 데이터 삽입 완료")
        
    except Exception as e:
        logger.error(f"샘플 데이터 삽입 중 오류 발생: {e}")


def main():
    """Main application entry point."""
    try:
        # 데이터베이스 초기화
        logger.info("애플리케이션 시작 - 데이터베이스 초기화 중...")
        if not initialize_database():
            logger.warning("데이터베이스 초기화에 실패했지만 애플리케이션을 계속 실행합니다.")
        
        # Get app instance
        app = get_app()
        
        # Run the application
        app.run()
        
    except Exception as e:
        logger.error(f"Error in main application: {e}")
        st.error(f"애플리케이션 실행 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()
