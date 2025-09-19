<<<<<<< HEAD
"""
ETL 서비스 모듈
CSV → MySQL 데이터 변환 및 적재
tech-stack.mdc 규칙에 따른 구현
"""

import logging
import os
from typing import Any

import pandas as pd

from data.database_manager import get_database_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLValidationError(Exception):
    """ETL 검증 오류"""

    pass


class ETLService:
    """ETL 서비스 클래스"""

    def __init__(self):
        self.db_manager = get_database_manager()
        self.required_columns = [
            "region_name",
            "industry_name",
            "date",
            "sales_amount",
            "transaction_count",
        ]

    def load_csv(self, file_path: str) -> pd.DataFrame:
        """CSV 파일 로딩"""
        try:
            if not os.path.exists(file_path):
                raise ETLValidationError(f"파일이 존재하지 않습니다: {file_path}")

            # CSV 파일 읽기
            df = pd.read_csv(file_path, encoding="utf-8")
            logger.info(f"CSV 파일 로딩 완료: {len(df)}행")

            return df
        except Exception as e:
            logger.error(f"CSV 파일 로딩 실패: {e}")
            raise ETLValidationError(f"CSV 파일 로딩 실패: {e}")

    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 검증 및 정제"""
        try:
            original_count = len(df)
            logger.info(f"데이터 검증 시작: {original_count}행")

            # 필수 컬럼 확인
            missing_columns = set(self.required_columns) - set(df.columns)
            if missing_columns:
                raise ETLValidationError(f"필수 컬럼이 없습니다: {missing_columns}")

            # 데이터 복사
            validated_df = df.copy()

            # 1. 결측값 처리
            validated_df = validated_df.dropna(subset=self.required_columns)
            logger.info(f"결측값 제거 후: {len(validated_df)}행")

            # 2. 중복 제거
            validated_df = self.remove_duplicates(validated_df)
            logger.info(f"중복 제거 후: {len(validated_df)}행")

            # 3. 데이터 타입 변환 및 검증
            validated_df = self._convert_data_types(validated_df)

            # 4. 비즈니스 규칙 검증
            validated_df = self._validate_business_rules(validated_df)

            final_count = len(validated_df)
            removed_count = original_count - final_count

            if removed_count > 0:
                logger.warning(f"검증 과정에서 {removed_count}행이 제거되었습니다")

            logger.info(f"데이터 검증 완료: {final_count}행")
            return validated_df

        except Exception as e:
            logger.error(f"데이터 검증 실패: {e}")
            raise ETLValidationError(f"데이터 검증 실패: {e}")

    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 타입 변환"""
        try:
            # 날짜 변환
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            # 숫자 타입 변환
            df["sales_amount"] = pd.to_numeric(df["sales_amount"], errors="coerce")
            df["transaction_count"] = pd.to_numeric(
                df["transaction_count"], errors="coerce"
            )

            # 문자열 타입 정리
            df["region_name"] = df["region_name"].astype(str).str.strip()
            df["industry_name"] = df["industry_name"].astype(str).str.strip()

            # 변환 실패한 행 제거
            df = df.dropna(subset=["date", "sales_amount", "transaction_count"])

            return df
        except Exception as e:
            logger.error(f"데이터 타입 변환 실패: {e}")
            raise ETLValidationError(f"데이터 타입 변환 실패: {e}")

    def _validate_business_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """비즈니스 규칙 검증"""
        try:
            # 1. 매출 금액이 음수인 경우 제거
            df = df[df["sales_amount"] >= 0]

            # 2. 거래 건수가 음수인 경우 제거
            df = df[df["transaction_count"] >= 0]

            # 3. 빈 문자열 제거
            df = df[df["region_name"].str.len() > 0]
            df = df[df["industry_name"].str.len() > 0]

            # 4. 날짜 범위 검증 (2024년 데이터만 허용)
            df = df[df["date"].dt.year == 2024]

            return df
        except Exception as e:
            logger.error(f"비즈니스 규칙 검증 실패: {e}")
            raise ETLValidationError(f"비즈니스 규칙 검증 실패: {e}")

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """중복 제거"""
        try:
            # 지역명, 업종명, 날짜 기준으로 중복 제거
            duplicate_columns = ["region_name", "industry_name", "date"]
            df_cleaned = df.drop_duplicates(subset=duplicate_columns, keep="first")

            removed_count = len(df) - len(df_cleaned)
            if removed_count > 0:
                logger.info(f"중복 제거: {removed_count}행")

            return df_cleaned
        except Exception as e:
            logger.error(f"중복 제거 실패: {e}")
            raise ETLValidationError(f"중복 제거 실패: {e}")

    def transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 변환"""
        try:
            logger.info("데이터 변환 시작")

            # 데이터 복사
            transformed_df = df.copy()

            # 1. 지역 ID 매핑
            transformed_df["region_id"] = transformed_df["region_name"].apply(
                lambda x: self.get_region_id(x)
            )

            # 2. 업종 ID 매핑
            transformed_df["industry_id"] = transformed_df["industry_name"].apply(
                lambda x: self.get_industry_id(x)
            )

            # 3. 평균 거래 금액 계산
            transformed_df["avg_transaction_amount"] = (
                transformed_df["sales_amount"] / transformed_df["transaction_count"]
            ).round(2)

            # 4. 날짜 형식 변환
            transformed_df["date"] = transformed_df["date"].dt.date

            # 5. 최종 컬럼 선택
            final_columns = [
                "region_id",
                "industry_id",
                "date",
                "sales_amount",
                "transaction_count",
                "avg_transaction_amount",
            ]

            transformed_df = transformed_df[final_columns]

            logger.info(f"데이터 변환 완료: {len(transformed_df)}행")
            return transformed_df

        except Exception as e:
            logger.error(f"데이터 변환 실패: {e}")
            raise ETLValidationError(f"데이터 변환 실패: {e}")

    def get_region_id(self, region_name: str) -> int:
        """지역 ID 조회"""
        try:
            query = """
                SELECT region_id FROM regions 
                WHERE region_name = %s
            """
            result = self.db_manager.execute_query(query, {"region_name": region_name})

            if len(result) > 0:
                return result["region_id"].iloc[0]
            else:
                logger.warning(f"지역을 찾을 수 없습니다: {region_name}")
                raise ETLValidationError(f"지역을 찾을 수 없습니다: {region_name}")

        except Exception as e:
            logger.error(f"지역 ID 조회 실패: {e}")
            raise ETLValidationError(f"지역 ID 조회 실패: {e}")

    def get_industry_id(self, industry_name: str) -> int:
        """업종 ID 조회"""
        try:
            query = """
                SELECT industry_id FROM industries 
                WHERE industry_name = %s
            """
            result = self.db_manager.execute_query(
                query, {"industry_name": industry_name}
            )

            if len(result) > 0:
                return result["industry_id"].iloc[0]
            else:
                logger.warning(f"업종을 찾을 수 없습니다: {industry_name}")
                raise ETLValidationError(f"업종을 찾을 수 없습니다: {industry_name}")

        except Exception as e:
            logger.error(f"업종 ID 조회 실패: {e}")
            raise ETLValidationError(f"업종 ID 조회 실패: {e}")

    def load_to_database(self, df: pd.DataFrame) -> bool:
        """데이터베이스에 데이터 로딩"""
        try:
            logger.info(f"데이터베이스 로딩 시작: {len(df)}행")

            # 배치 크기 설정
            batch_size = 1000
            total_rows = len(df)

            for i in range(0, total_rows, batch_size):
                batch_df = df.iloc[i : i + batch_size]
                self._insert_batch(batch_df)

                logger.info(f"배치 로딩 완료: {i + len(batch_df)}/{total_rows}행")

            logger.info("데이터베이스 로딩 완료")
            return True

        except Exception as e:
            logger.error(f"데이터베이스 로딩 실패: {e}")
            raise ETLValidationError(f"데이터베이스 로딩 실패: {e}")

    def _insert_batch(self, df: pd.DataFrame):
        """배치 데이터 삽입"""
        try:
            # INSERT 쿼리 생성
            insert_query = """
                INSERT INTO sales_2024 
                (region_id, industry_id, date, sales_amount, transaction_count, avg_transaction_amount)
                VALUES (%(region_id)s, %(industry_id)s, %(date)s, %(sales_amount)s, %(transaction_count)s, %(avg_transaction_amount)s)
                ON DUPLICATE KEY UPDATE
                sales_amount = VALUES(sales_amount),
                transaction_count = VALUES(transaction_count),
                avg_transaction_amount = VALUES(avg_transaction_amount),
                updated_at = CURRENT_TIMESTAMP
            """

            # 데이터를 딕셔너리 리스트로 변환
            data_dict = df.to_dict("records")

            # 배치 삽입 실행
            with self.db_manager.get_session() as session:
                for record in data_dict:
                    session.execute(insert_query, record)

        except Exception as e:
            logger.error(f"배치 삽입 실패: {e}")
            raise ETLValidationError(f"배치 삽입 실패: {e}")

    def run_etl_pipeline(self, csv_file_path: str) -> bool:
        """ETL 파이프라인 전체 실행"""
        try:
            logger.info(f"ETL 파이프라인 시작: {csv_file_path}")

            # 1. CSV 로딩
            raw_data = self.load_csv(csv_file_path)

            # 2. 데이터 검증
            validated_data = self.validate_data(raw_data)

            # 3. 데이터 변환
            transformed_data = self.transform_data(validated_data)

            # 4. 데이터베이스 로딩
            success = self.load_to_database(transformed_data)

            if success:
                logger.info("ETL 파이프라인 완료")
                return True
            else:
                logger.error("ETL 파이프라인 실패")
                return False

        except Exception as e:
            logger.error(f"ETL 파이프라인 실행 실패: {e}")
            raise ETLValidationError(f"ETL 파이프라인 실행 실패: {e}")

    def get_etl_statistics(self) -> dict[str, Any]:
        """ETL 통계 정보 조회"""
        try:
            stats = {}

            # 테이블별 행 수 조회
            tables = ["regions", "industries", "sales_2024"]
            for table in tables:
                count = self.db_manager.get_table_count(table)
                stats[f"{table}_count"] = count

            # 최근 데이터 날짜 조회
            query = "SELECT MAX(date) as latest_date FROM sales_2024"
            result = self.db_manager.execute_query(query)
            if len(result) > 0:
                stats["latest_data_date"] = result["latest_date"].iloc[0]

            return stats

        except Exception as e:
            logger.error(f"ETL 통계 조회 실패: {e}")
            return {}


# 전역 ETL 서비스 인스턴스
etl_service = ETLService()


def get_etl_service() -> ETLService:
    """ETL 서비스 인스턴스 반환"""
    return etl_service
=======
"""
ETL 서비스 모듈
CSV → MySQL 데이터 변환 및 적재
tech-stack.mdc 규칙에 따른 구현
"""

import logging
import os
from typing import Any

import pandas as pd

from data.database_manager import get_database_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLValidationError(Exception):
    """ETL 검증 오류"""

    pass


class ETLService:
    """ETL 서비스 클래스"""

    def __init__(self):
        self.db_manager = get_database_manager()
        self.required_columns = [
            "region_name",
            "industry_name",
            "date",
            "sales_amount",
            "transaction_count",
        ]

    def load_csv(self, file_path: str) -> pd.DataFrame:
        """CSV 파일 로딩"""
        try:
            if not os.path.exists(file_path):
                raise ETLValidationError(f"파일이 존재하지 않습니다: {file_path}")

            # CSV 파일 읽기
            df = pd.read_csv(file_path, encoding="utf-8")
            logger.info(f"CSV 파일 로딩 완료: {len(df)}행")

            return df
        except Exception as e:
            logger.error(f"CSV 파일 로딩 실패: {e}")
            raise ETLValidationError(f"CSV 파일 로딩 실패: {e}")

    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 검증 및 정제"""
        try:
            original_count = len(df)
            logger.info(f"데이터 검증 시작: {original_count}행")

            # 필수 컬럼 확인
            missing_columns = set(self.required_columns) - set(df.columns)
            if missing_columns:
                raise ETLValidationError(f"필수 컬럼이 없습니다: {missing_columns}")

            # 데이터 복사
            validated_df = df.copy()

            # 1. 결측값 처리
            validated_df = validated_df.dropna(subset=self.required_columns)
            logger.info(f"결측값 제거 후: {len(validated_df)}행")

            # 2. 중복 제거
            validated_df = self.remove_duplicates(validated_df)
            logger.info(f"중복 제거 후: {len(validated_df)}행")

            # 3. 데이터 타입 변환 및 검증
            validated_df = self._convert_data_types(validated_df)

            # 4. 비즈니스 규칙 검증
            validated_df = self._validate_business_rules(validated_df)

            final_count = len(validated_df)
            removed_count = original_count - final_count

            if removed_count > 0:
                logger.warning(f"검증 과정에서 {removed_count}행이 제거되었습니다")

            logger.info(f"데이터 검증 완료: {final_count}행")
            return validated_df

        except Exception as e:
            logger.error(f"데이터 검증 실패: {e}")
            raise ETLValidationError(f"데이터 검증 실패: {e}")

    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 타입 변환"""
        try:
            # 날짜 변환
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            # 숫자 타입 변환
            df["sales_amount"] = pd.to_numeric(df["sales_amount"], errors="coerce")
            df["transaction_count"] = pd.to_numeric(
                df["transaction_count"], errors="coerce"
            )

            # 문자열 타입 정리
            df["region_name"] = df["region_name"].astype(str).str.strip()
            df["industry_name"] = df["industry_name"].astype(str).str.strip()

            # 변환 실패한 행 제거
            df = df.dropna(subset=["date", "sales_amount", "transaction_count"])

            return df
        except Exception as e:
            logger.error(f"데이터 타입 변환 실패: {e}")
            raise ETLValidationError(f"데이터 타입 변환 실패: {e}")

    def _validate_business_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """비즈니스 규칙 검증"""
        try:
            # 1. 매출 금액이 음수인 경우 제거
            df = df[df["sales_amount"] >= 0]

            # 2. 거래 건수가 음수인 경우 제거
            df = df[df["transaction_count"] >= 0]

            # 3. 빈 문자열 제거
            df = df[df["region_name"].str.len() > 0]
            df = df[df["industry_name"].str.len() > 0]

            # 4. 날짜 범위 검증 (2024년 데이터만 허용)
            df = df[df["date"].dt.year == 2024]

            return df
        except Exception as e:
            logger.error(f"비즈니스 규칙 검증 실패: {e}")
            raise ETLValidationError(f"비즈니스 규칙 검증 실패: {e}")

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """중복 제거"""
        try:
            # 지역명, 업종명, 날짜 기준으로 중복 제거
            duplicate_columns = ["region_name", "industry_name", "date"]
            df_cleaned = df.drop_duplicates(subset=duplicate_columns, keep="first")

            removed_count = len(df) - len(df_cleaned)
            if removed_count > 0:
                logger.info(f"중복 제거: {removed_count}행")

            return df_cleaned
        except Exception as e:
            logger.error(f"중복 제거 실패: {e}")
            raise ETLValidationError(f"중복 제거 실패: {e}")

    def transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 변환"""
        try:
            logger.info("데이터 변환 시작")

            # 데이터 복사
            transformed_df = df.copy()

            # 1. 지역 ID 매핑
            transformed_df["region_id"] = transformed_df["region_name"].apply(
                lambda x: self.get_region_id(x)
            )

            # 2. 업종 ID 매핑
            transformed_df["industry_id"] = transformed_df["industry_name"].apply(
                lambda x: self.get_industry_id(x)
            )

            # 3. 평균 거래 금액 계산
            transformed_df["avg_transaction_amount"] = (
                transformed_df["sales_amount"] / transformed_df["transaction_count"]
            ).round(2)

            # 4. 날짜 형식 변환
            transformed_df["date"] = transformed_df["date"].dt.date

            # 5. 최종 컬럼 선택
            final_columns = [
                "region_id",
                "industry_id",
                "date",
                "sales_amount",
                "transaction_count",
                "avg_transaction_amount",
            ]

            transformed_df = transformed_df[final_columns]

            logger.info(f"데이터 변환 완료: {len(transformed_df)}행")
            return transformed_df

        except Exception as e:
            logger.error(f"데이터 변환 실패: {e}")
            raise ETLValidationError(f"데이터 변환 실패: {e}")

    def get_region_id(self, region_name: str) -> int:
        """지역 ID 조회"""
        try:
            query = """
                SELECT region_id FROM regions 
                WHERE region_name = %s
            """
            result = self.db_manager.execute_query(query, {"region_name": region_name})

            if len(result) > 0:
                return result["region_id"].iloc[0]
            else:
                logger.warning(f"지역을 찾을 수 없습니다: {region_name}")
                raise ETLValidationError(f"지역을 찾을 수 없습니다: {region_name}")

        except Exception as e:
            logger.error(f"지역 ID 조회 실패: {e}")
            raise ETLValidationError(f"지역 ID 조회 실패: {e}")

    def get_industry_id(self, industry_name: str) -> int:
        """업종 ID 조회"""
        try:
            query = """
                SELECT industry_id FROM industries 
                WHERE industry_name = %s
            """
            result = self.db_manager.execute_query(
                query, {"industry_name": industry_name}
            )

            if len(result) > 0:
                return result["industry_id"].iloc[0]
            else:
                logger.warning(f"업종을 찾을 수 없습니다: {industry_name}")
                raise ETLValidationError(f"업종을 찾을 수 없습니다: {industry_name}")

        except Exception as e:
            logger.error(f"업종 ID 조회 실패: {e}")
            raise ETLValidationError(f"업종 ID 조회 실패: {e}")

    def load_to_database(self, df: pd.DataFrame) -> bool:
        """데이터베이스에 데이터 로딩"""
        try:
            logger.info(f"데이터베이스 로딩 시작: {len(df)}행")

            # 배치 크기 설정
            batch_size = 1000
            total_rows = len(df)

            for i in range(0, total_rows, batch_size):
                batch_df = df.iloc[i : i + batch_size]
                self._insert_batch(batch_df)

                logger.info(f"배치 로딩 완료: {i + len(batch_df)}/{total_rows}행")

            logger.info("데이터베이스 로딩 완료")
            return True

        except Exception as e:
            logger.error(f"데이터베이스 로딩 실패: {e}")
            raise ETLValidationError(f"데이터베이스 로딩 실패: {e}")

    def _insert_batch(self, df: pd.DataFrame):
        """배치 데이터 삽입"""
        try:
            # INSERT 쿼리 생성
            insert_query = """
                INSERT INTO sales_2024 
                (region_id, industry_id, date, sales_amount, transaction_count, avg_transaction_amount)
                VALUES (%(region_id)s, %(industry_id)s, %(date)s, %(sales_amount)s, %(transaction_count)s, %(avg_transaction_amount)s)
                ON DUPLICATE KEY UPDATE
                sales_amount = VALUES(sales_amount),
                transaction_count = VALUES(transaction_count),
                avg_transaction_amount = VALUES(avg_transaction_amount),
                updated_at = CURRENT_TIMESTAMP
            """

            # 데이터를 딕셔너리 리스트로 변환
            data_dict = df.to_dict("records")

            # 배치 삽입 실행
            with self.db_manager.get_session() as session:
                for record in data_dict:
                    session.execute(insert_query, record)

        except Exception as e:
            logger.error(f"배치 삽입 실패: {e}")
            raise ETLValidationError(f"배치 삽입 실패: {e}")

    def run_etl_pipeline(self, csv_file_path: str) -> bool:
        """ETL 파이프라인 전체 실행"""
        try:
            logger.info(f"ETL 파이프라인 시작: {csv_file_path}")

            # 1. CSV 로딩
            raw_data = self.load_csv(csv_file_path)

            # 2. 데이터 검증
            validated_data = self.validate_data(raw_data)

            # 3. 데이터 변환
            transformed_data = self.transform_data(validated_data)

            # 4. 데이터베이스 로딩
            success = self.load_to_database(transformed_data)

            if success:
                logger.info("ETL 파이프라인 완료")
                return True
            else:
                logger.error("ETL 파이프라인 실패")
                return False

        except Exception as e:
            logger.error(f"ETL 파이프라인 실행 실패: {e}")
            raise ETLValidationError(f"ETL 파이프라인 실행 실패: {e}")

    def get_etl_statistics(self) -> dict[str, Any]:
        """ETL 통계 정보 조회"""
        try:
            stats = {}

            # 테이블별 행 수 조회
            tables = ["regions", "industries", "sales_2024"]
            for table in tables:
                count = self.db_manager.get_table_count(table)
                stats[f"{table}_count"] = count

            # 최근 데이터 날짜 조회
            query = "SELECT MAX(date) as latest_date FROM sales_2024"
            result = self.db_manager.execute_query(query)
            if len(result) > 0:
                stats["latest_data_date"] = result["latest_date"].iloc[0]

            return stats

        except Exception as e:
            logger.error(f"ETL 통계 조회 실패: {e}")
            return {}


# 전역 ETL 서비스 인스턴스
etl_service = ETLService()


def get_etl_service() -> ETLService:
    """ETL 서비스 인스턴스 반환"""
    return etl_service
>>>>>>> b15a617 (first commit)
