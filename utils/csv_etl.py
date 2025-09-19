"""
CSV to MySQL ETL 모듈
서울시 상권분석 데이터를 MySQL에 로드
"""

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text
import logging
import os
from dotenv import load_dotenv
import glob
from typing import Dict, List, Any
import pymysql

load_dotenv()
logger = logging.getLogger(__name__)

class CSVETLService:
    def __init__(self):
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = int(os.getenv('DB_PORT', 3306))
        self.db_user = os.getenv('DB_USER', 'test')
        self.db_password = os.getenv('DB_PASSWORD', 'test')
        self.db_name = os.getenv('DB_NAME', 'test_db')

        # MySQL 연결 엔진 생성
        try:
            self.engine = create_engine(
                f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}",
                echo=False,
                pool_recycle=3600
            )
            logger.info("MySQL 연결 엔진 생성 완료")
        except Exception as e:
            logger.error(f"MySQL 연결 실패: {str(e)}")
            self.engine = None

    def read_csv_with_encoding(self, file_path: str) -> pd.DataFrame:
        """CSV 파일을 올바른 인코딩으로 읽기"""
        encodings = ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig']

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"CSV 파일 읽기 성공: {os.path.basename(file_path)}, encoding: {encoding}")
                return df
            except Exception as e:
                continue

        logger.error(f"CSV 파일 읽기 실패: {file_path}")
        return None

    def create_commercial_table(self) -> bool:
        """상권분석 테이블 생성"""
        try:
            with self.engine.connect() as conn:
                # 기존 테이블 삭제
                conn.execute(text("DROP TABLE IF EXISTS commercial_analysis"))

                # 새 테이블 생성
                create_table_sql = """
                CREATE TABLE commercial_analysis (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    기준년분기코드 VARCHAR(10),
                    상권구분코드 VARCHAR(10),
                    상권구분코드명 VARCHAR(50),
                    상권코드 VARCHAR(20),
                    상권코드명 VARCHAR(100),
                    서비스업종코드 VARCHAR(20),
                    서비스업종코드명 VARCHAR(100),
                    당월매출금액 BIGINT,
                    당월매출건수 INT,
                    월요일매출금액 BIGINT,
                    화요일매출금액 BIGINT,
                    수요일매출금액 BIGINT,
                    목요일매출금액 BIGINT,
                    금요일매출금액 BIGINT,
                    토요일매출금액 BIGINT,
                    일요일매출금액 BIGINT,
                    시간대00_06매출금액 BIGINT,
                    시간대06_11매출금액 BIGINT,
                    시간대11_14매출금액 BIGINT,
                    시간대14_17매출금액 BIGINT,
                    시간대17_21매출금액 BIGINT,
                    시간대21_24매출금액 BIGINT,
                    남성매출금액 BIGINT,
                    여성매출금액 BIGINT,
                    연령대10매출금액 BIGINT,
                    연령대20매출금액 BIGINT,
                    연령대30매출금액 BIGINT,
                    연령대40매출금액 BIGINT,
                    연령대50매출금액 BIGINT,
                    연령대60이상매출금액 BIGINT,
                    월요일매출건수 INT,
                    화요일매출건수 INT,
                    수요일매출건수 INT,
                    목요일매출건수 INT,
                    금요일매출건수 INT,
                    토요일매출건수 INT,
                    일요일매출건수 INT,
                    시간대00_06매출건수 INT,
                    시간대06_11매출건수 INT,
                    시간대11_14매출건수 INT,
                    시간대14_17매출건수 INT,
                    시간대17_21매출건수 INT,
                    시간대21_24매출건수 INT,
                    남성매출건수 INT,
                    여성매출건수 INT,
                    연령대10매출건수 INT,
                    연령대20매출건수 INT,
                    연령대30매출건수 INT,
                    연령대40매출건수 INT,
                    연령대50매출건수 INT,
                    연령대60이상매출건수 INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_기준년분기코드 (기준년분기코드),
                    INDEX idx_상권코드 (상권코드),
                    INDEX idx_서비스업종코드 (서비스업종코드)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """

                conn.execute(text(create_table_sql))
                conn.commit()
                logger.info("상권분석 테이블 생성 완료")
                return True

        except Exception as e:
            logger.error(f"테이블 생성 실패: {str(e)}")
            return False

    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼명 정리 - 실제 CSV 컬럼명 기반"""
        # 실제 CSV 컬럼명을 DB 컬럼명으로 매핑
        column_mapping = {
            '기준_년분기_코드': '기준년분기코드',
            '상권_구분_코드': '상권구분코드',
            '상권_구분_코드_명': '상권구분코드명',
            '상권_코드': '상권코드',
            '상권_코드_명': '상권코드명',
            '서비스_업종_코드': '서비스업종코드',
            '서비스_업종_코드_명': '서비스업종코드명',
            '당월_매출_금액': '당월매출금액',
            '당월_매출_건수': '당월매출건수',
            '월요일_매출_금액': '월요일매출금액',
            '화요일_매출_금액': '화요일매출금액',
            '수요일_매출_금액': '수요일매출금액',
            '목요일_매출_금액': '목요일매출금액',
            '금요일_매출_금액': '금요일매출금액',
            '토요일_매출_금액': '토요일매출금액',
            '일요일_매출_금액': '일요일매출금액',
            '시간대_00~06_매출_금액': '시간대00_06매출금액',
            '시간대_06~11_매출_금액': '시간대06_11매출금액',
            '시간대_11~14_매출_금액': '시간대11_14매출금액',
            '시간대_14~17_매출_금액': '시간대14_17매출금액',
            '시간대_17~21_매출_금액': '시간대17_21매출금액',
            '시간대_21~24_매출_금액': '시간대21_24매출금액',
            '남성_매출_금액': '남성매출금액',
            '여성_매출_금액': '여성매출금액',
            '연령대_10_매출_금액': '연령대10매출금액',
            '연령대_20_매출_금액': '연령대20매출금액',
            '연령대_30_매출_금액': '연령대30매출금액',
            '연령대_40_매출_금액': '연령대40매출금액',
            '연령대_50_매출_금액': '연령대50매출금액',
            '연령대_60_이상_매출_금액': '연령대60이상매출금액',
            '월요일_매출_건수': '월요일매출건수',
            '화요일_매출_건수': '화요일매출건수',
            '수요일_매출_건수': '수요일매출건수',
            '목요일_매출_건수': '목요일매출건수',
            '금요일_매출_건수': '금요일매출건수',
            '토요일_매출_건수': '토요일매출건수',
            '일요일_매출_건수': '일요일매출건수',
            '시간대_건수~06_매출_건수': '시간대00_06매출건수',
            '시간대_건수~11_매출_건수': '시간대06_11매출건수',
            '시간대_건수~14_매출_건수': '시간대11_14매출건수',
            '시간대_건수~17_매출_건수': '시간대14_17매출건수',
            '시간대_건수~21_매출_건수': '시간대17_21매출건수',
            '시간대_건수~24_매출_건수': '시간대21_24매출건수',
            '남성_매출_건수': '남성매출건수',
            '여성_매출_건수': '여성매출건수',
            '연령대_10_매출_건수': '연령대10매출건수',
            '연령대_20_매출_건수': '연령대20매출건수',
            '연령대_30_매출_건수': '연령대30매출건수',
            '연령대_40_매출_건수': '연령대40매출건수',
            '연령대_50_매출_건수': '연령대50매출건수',
            '연령대_60_이상_매출_건수': '연령대60이상매출건수'
        }

        # 컬럼명 변경
        df_cleaned = df.rename(columns=column_mapping)

        # DB 테이블 구조에 맞는 컬럼만 선택
        target_columns = [
            '기준년분기코드', '상권구분코드', '상권구분코드명', '상권코드', '상권코드명',
            '서비스업종코드', '서비스업종코드명', '당월매출금액', '당월매출건수',
            '월요일매출금액', '화요일매출금액', '수요일매출금액', '목요일매출금액',
            '금요일매출금액', '토요일매출금액', '일요일매출금액',
            '시간대00_06매출금액', '시간대06_11매출금액', '시간대11_14매출금액',
            '시간대14_17매출금액', '시간대17_21매출금액', '시간대21_24매출금액',
            '남성매출금액', '여성매출금액',
            '연령대10매출금액', '연령대20매출금액', '연령대30매출금액',
            '연령대40매출금액', '연령대50매출금액', '연령대60이상매출금액',
            '월요일매출건수', '화요일매출건수', '수요일매출건수', '목요일매출건수',
            '금요일매출건수', '토요일매출건수', '일요일매출건수',
            '시간대00_06매출건수', '시간대06_11매출건수', '시간대11_14매출건수',
            '시간대14_17매출건수', '시간대17_21매출건수', '시간대21_24매출건수',
            '남성매출건수', '여성매출건수',
            '연령대10매출건수', '연령대20매출건수', '연령대30매출건수',
            '연령대40매출건수', '연령대50매출건수', '연령대60이상매출건수'
        ]

        # 존재하는 컬럼만 선택
        existing_columns = [col for col in target_columns if col in df_cleaned.columns]

        return df_cleaned[existing_columns]

    def process_csv_file(self, file_path: str) -> Dict[str, Any]:
        """단일 CSV 파일 처리"""
        try:
            # CSV 파일 읽기
            df = self.read_csv_with_encoding(file_path)
            if df is None:
                return {"status": "error", "message": "CSV 파일 읽기 실패"}

            # 컬럼명 정리
            df_cleaned = self.clean_column_names(df)

            # 결측값 처리
            df_cleaned = df_cleaned.fillna(0)

            # 데이터 타입 변환
            numeric_columns = [col for col in df_cleaned.columns if '매출' in col or '건수' in col]
            for col in numeric_columns:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce').fillna(0)

            # MySQL에 데이터 삽입
            if self.engine:
                df_cleaned.to_sql(
                    'commercial_analysis',
                    con=self.engine,
                    if_exists='append',
                    index=False,
                    chunksize=1000
                )

                logger.info(f"CSV 파일 처리 완료: {os.path.basename(file_path)}, {len(df_cleaned)}건")
                return {
                    "status": "success",
                    "file": os.path.basename(file_path),
                    "rows": len(df_cleaned),
                    "columns": len(df_cleaned.columns)
                }
            else:
                return {"status": "error", "message": "데이터베이스 연결 없음"}

        except Exception as e:
            logger.error(f"CSV 파일 처리 실패: {file_path}, {str(e)}")
            return {"status": "error", "message": str(e)}

    def load_all_csv_files(self) -> Dict[str, Any]:
        """모든 CSV 파일을 MySQL에 로드"""
        try:
            if not self.engine:
                return {"status": "error", "message": "데이터베이스 연결 실패"}

            # 테이블 생성
            if not self.create_commercial_table():
                return {"status": "error", "message": "테이블 생성 실패"}

            # CSV 파일 목록 가져오기
            csv_files = glob.glob("data/csv/*.csv")
            if not csv_files:
                return {"status": "error", "message": "CSV 파일을 찾을 수 없습니다"}

            results = []
            total_rows = 0

            for csv_file in csv_files:
                result = self.process_csv_file(csv_file)
                results.append(result)
                if result["status"] == "success":
                    total_rows += result["rows"]

            # 최종 통계
            successful_files = [r for r in results if r["status"] == "success"]

            return {
                "status": "success",
                "total_files": len(csv_files),
                "successful_files": len(successful_files),
                "total_rows": total_rows,
                "results": results,
                "message": f"{len(successful_files)}개 파일, {total_rows}건 로드 완료"
            }

        except Exception as e:
            logger.error(f"CSV 로드 실패: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_table_info(self) -> Dict[str, Any]:
        """테이블 정보 조회"""
        try:
            if not self.engine:
                return {"status": "error", "message": "데이터베이스 연결 실패"}

            with self.engine.connect() as conn:
                # 테이블 존재 확인
                result = conn.execute(text("SHOW TABLES LIKE 'commercial_analysis'"))
                if not result.fetchone():
                    return {"status": "error", "message": "테이블이 존재하지 않습니다"}

                # 행 수 조회
                row_count = conn.execute(text("SELECT COUNT(*) FROM commercial_analysis")).scalar()

                # 컬럼 정보 조회
                columns = conn.execute(text("DESCRIBE commercial_analysis")).fetchall()

                # 샘플 데이터 조회
                sample_data = conn.execute(text("SELECT * FROM commercial_analysis LIMIT 5")).fetchall()

                return {
                    "status": "success",
                    "row_count": row_count,
                    "columns": [{"name": col[0], "type": col[1]} for col in columns],
                    "sample_data": [dict(row._mapping) for row in sample_data]
                }

        except Exception as e:
            logger.error(f"테이블 정보 조회 실패: {str(e)}")
            return {"status": "error", "message": str(e)}

def get_csv_etl_service() -> CSVETLService:
    """CSV ETL 서비스 인스턴스 반환"""
    return CSVETLService()