"""
CSV to MySQL ETL 파이프라인
PRD TASK2: CSV 데이터를 MySQL에 저장하는 ETL 구현
"""

import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text
from pathlib import Path
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class SeoulCommercialETL:
    """서울 상권 데이터 ETL 클래스"""
    
    def __init__(self, mysql_url: str):
        """
        ETL 클래스 초기화
        
        Args:
            mysql_url: MySQL 연결 URL
        """
        self.mysql_url = mysql_url
        self.engine = None
        self.connection = None
        
    def connect(self) -> bool:
        """데이터베이스 연결"""
        try:
            self.engine = create_engine(self.mysql_url, echo=False)
            self.connection = self.engine.connect()
            logger.info("데이터베이스 연결 성공")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {str(e)}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
        if self.engine:
            self.engine.dispose()
        logger.info("데이터베이스 연결 해제")
    
    def load_csv_data(self, csv_path: str) -> pd.DataFrame:
        """
        CSV 파일 로드
        
        Args:
            csv_path: CSV 파일 경로
            
        Returns:
            로드된 데이터프레임
        """
        try:
            # CSV 파일 읽기 (cp949 인코딩)
            df = pd.read_csv(csv_path, encoding='cp949')
            logger.info(f"CSV 파일 로드 완료: {len(df)}행, {len(df.columns)}열")
            return df
        except Exception as e:
            logger.error(f"CSV 파일 로드 실패: {str(e)}")
            raise
    
    def clean_and_transform_data(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        데이터 정제 및 변환
        
        Args:
            df: 원본 데이터프레임
            
        Returns:
            변환된 데이터프레임 딕셔너리
        """
        try:
            # 기본 데이터 정제
            df = df.dropna(subset=['기준_년분기_코드', '상권_코드', '서비스_업종_코드'])
            
            # 지역 데이터 추출
            regions_df = df[['상권_코드', '상권_코드_명']].drop_duplicates()
            regions_df = regions_df.rename(columns={
                '상권_코드': 'region_code',
                '상권_코드_명': 'region_name'
            })
            regions_df['gu'] = regions_df['region_name'].str.split(' ').str[0]
            regions_df['dong'] = regions_df['region_name'].str.split(' ').str[1] if len(regions_df['region_name'].str.split(' ')) > 1 else ''
            regions_df['region_id'] = range(1, len(regions_df) + 1)
            
            # 업종 데이터 추출
            industries_df = df[['서비스_업종_코드', '서비스_업종_코드_명']].drop_duplicates()
            industries_df = industries_df.rename(columns={
                '서비스_업종_코드': 'industry_code',
                '서비스_업종_코드_명': 'industry_name'
            })
            industries_df['industry_id'] = range(1, len(industries_df) + 1)
            
            # 상권 데이터 추출
            commercial_areas_df = df[['상권_코드', '상권_코드_명', '상권_구분_코드', '상권_구분_코드_명']].drop_duplicates()
            commercial_areas_df = commercial_areas_df.rename(columns={
                '상권_코드': 'area_code',
                '상권_코드_명': 'area_name',
                '상권_구분_코드': 'area_type_code',
                '상권_구분_코드_명': 'area_type_name'
            })
            commercial_areas_df['area_id'] = range(1, len(commercial_areas_df) + 1)
            
            # 매출 데이터 변환
            sales_df = df.copy()
            sales_df = sales_df.rename(columns={
                '기준_년분기_코드': 'quarter_code',
                '당월_매출_금액': 'monthly_sales_amount',
                '당월_매출_건수': 'monthly_sales_count',
                '주중_매출_금액': 'weekday_sales_amount',
                '주말_매출_금액': 'weekend_sales_amount',
                '남성_매출_금액': 'male_sales_amount',
                '여성_매출_금액': 'female_sales_amount',
                '10대_매출_금액': 'teen_sales_amount',
                '20대_매출_금액': 'twenties_sales_amount',
                '30대_매출_금액': 'thirties_sales_amount',
                '40대_매출_금액': 'forties_sales_amount',
                '50대_매출_금액': 'fifties_sales_amount',
                '60대_이상_매출_금액': 'sixties_plus_sales_amount',
                '시간대_00~06_매출_금액': 'time_00_06_sales_amount',
                '시간대_06~11_매출_금액': 'time_06_11_sales_amount',
                '시간대_11~14_매출_금액': 'time_11_14_sales_amount',
                '시간대_14~17_매출_금액': 'time_14_17_sales_amount',
                '시간대_17~21_매출_금액': 'time_17_21_sales_amount',
                '시간대_21~24_매출_금액': 'time_21_24_sales_amount',
                '남성_매출_건수': 'male_sales_count',
                '여성_매출_건수': 'female_sales_count',
                '10대_매출_건수': 'teen_sales_count',
                '20대_매출_건수': 'twenties_sales_count',
                '30대_매출_건수': 'thirties_sales_count',
                '40대_매출_건수': 'forties_sales_count',
                '50대_매출_건수': 'fifties_sales_count',
                '60대_이상_매출_건수': 'sixties_plus_sales_count',
                '시간대_건수~06_매출_건수': 'time_00_06_sales_count',
                '시간대_건수~11_매출_건수': 'time_06_11_sales_count',
                '시간대_건수~14_매출_건수': 'time_11_14_sales_count',
                '시간대_건수~17_매출_건수': 'time_14_17_sales_count',
                '시간대_건수~21_매출_건수': 'time_17_21_sales_count',
                '시간대_건수~24_매출_건수': 'time_21_24_sales_count'
            })
            
            # 날짜 변환 (분기 코드를 날짜로 변환)
            sales_df['sales_date'] = pd.to_datetime(sales_df['quarter_code'].astype(str).str[:4] + '-' + 
                                                   sales_df['quarter_code'].astype(str).str[4:5].replace('1', '01').replace('2', '04').replace('3', '07').replace('4', '10') + '-01')
            
            # 숫자 컬럼 정제
            numeric_columns = [col for col in sales_df.columns if 'amount' in col or 'count' in col]
            for col in numeric_columns:
                if col in sales_df.columns:
                    sales_df[col] = pd.to_numeric(sales_df[col], errors='coerce').fillna(0)
            
            # ID 매핑
            region_mapping = dict(zip(regions_df['region_code'], regions_df['region_id']))
            industry_mapping = dict(zip(industries_df['industry_code'], industries_df['industry_id']))
            area_mapping = dict(zip(commercial_areas_df['area_code'], commercial_areas_df['area_id']))
            
            sales_df['area_id'] = sales_df['상권_코드'].map(area_mapping)
            sales_df['industry_id'] = sales_df['서비스_업종_코드'].map(industry_mapping)
            
            # 필요한 컬럼만 선택
            sales_columns = ['quarter_code', 'area_id', 'industry_id', 'sales_date'] + numeric_columns
            sales_df = sales_df[sales_columns].dropna(subset=['area_id', 'industry_id'])
            
            logger.info(f"데이터 변환 완료: 지역 {len(regions_df)}개, 업종 {len(industries_df)}개, 상권 {len(commercial_areas_df)}개, 매출 {len(sales_df)}개")
            
            return {
                'regions': regions_df,
                'industries': industries_df,
                'commercial_areas': commercial_areas_df,
                'sales': sales_df
            }
            
        except Exception as e:
            logger.error(f"데이터 변환 실패: {str(e)}")
            raise
    
    def create_tables(self):
        """테이블 생성"""
        try:
            # 스키마 파일 읽기
            schema_path = Path(__file__).parent.parent / "schema" / "0001_init.sql"
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # SQL 실행
            self.connection.execute(text(schema_sql))
            self.connection.commit()
            logger.info("테이블 생성 완료")
            
        except Exception as e:
            logger.error(f"테이블 생성 실패: {str(e)}")
            raise
    
    def insert_data(self, data_dict: Dict[str, pd.DataFrame]):
        """데이터 삽입"""
        try:
            # 지역 데이터 삽입
            if not data_dict['regions'].empty:
                data_dict['regions'].to_sql('regions', self.connection, if_exists='replace', index=False, method='multi')
                logger.info(f"지역 데이터 삽입 완료: {len(data_dict['regions'])}행")
            
            # 업종 데이터 삽입
            if not data_dict['industries'].empty:
                data_dict['industries'].to_sql('industries', self.connection, if_exists='replace', index=False, method='multi')
                logger.info(f"업종 데이터 삽입 완료: {len(data_dict['industries'])}행")
            
            # 상권 데이터 삽입
            if not data_dict['commercial_areas'].empty:
                data_dict['commercial_areas'].to_sql('commercial_areas', self.connection, if_exists='replace', index=False, method='multi')
                logger.info(f"상권 데이터 삽입 완료: {len(data_dict['commercial_areas'])}행")
            
            # 매출 데이터 삽입 (배치 처리)
            if not data_dict['sales'].empty:
                batch_size = 1000
                total_rows = len(data_dict['sales'])
                
                for i in range(0, total_rows, batch_size):
                    batch_df = data_dict['sales'].iloc[i:i+batch_size]
                    batch_df.to_sql('sales_2024', self.connection, if_exists='append', index=False, method='multi')
                    logger.info(f"매출 데이터 배치 삽입: {i+1}-{min(i+batch_size, total_rows)}/{total_rows}")
                
                logger.info(f"매출 데이터 삽입 완료: {total_rows}행")
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"데이터 삽입 실패: {str(e)}")
            self.connection.rollback()
            raise
    
    def run_etl(self, csv_path: str) -> Dict[str, Any]:
        """
        전체 ETL 프로세스 실행
        
        Args:
            csv_path: CSV 파일 경로
            
        Returns:
            ETL 실행 결과
        """
        start_time = time.time()
        
        try:
            # 1. 연결
            if not self.connect():
                return {"status": "error", "message": "데이터베이스 연결 실패"}
            
            # 2. 테이블 생성
            self.create_tables()
            
            # 3. CSV 로드
            df = self.load_csv_data(csv_path)
            
            # 4. 데이터 변환
            data_dict = self.clean_and_transform_data(df)
            
            # 5. 데이터 삽입
            self.insert_data(data_dict)
            
            # 6. 결과 반환
            execution_time = time.time() - start_time
            
            result = {
                "status": "success",
                "execution_time": execution_time,
                "regions_count": len(data_dict['regions']),
                "industries_count": len(data_dict['industries']),
                "commercial_areas_count": len(data_dict['commercial_areas']),
                "sales_count": len(data_dict['sales']),
                "message": "ETL 프로세스 완료"
            }
            
            logger.info(f"ETL 프로세스 완료: {execution_time:.2f}초")
            return result
            
        except Exception as e:
            logger.error(f"ETL 프로세스 실패: {str(e)}")
            return {"status": "error", "message": str(e)}
        
        finally:
            self.disconnect()

def run_csv_to_mysql_etl(csv_path: str, mysql_url: str) -> Dict[str, Any]:
    """
    CSV to MySQL ETL 실행 함수
    
    Args:
        csv_path: CSV 파일 경로
        mysql_url: MySQL 연결 URL
        
    Returns:
        ETL 실행 결과
    """
    etl = SeoulCommercialETL(mysql_url)
    return etl.run_etl(csv_path)
