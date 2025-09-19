"""
데이터베이스 연결 및 스키마 관리 모듈
"""

import logging
from typing import Any

import mysql.connector
import pandas as pd
from mysql.connector import Error
from sqlalchemy import create_engine

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """MySQL 데이터베이스 관리 클래스"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        user: str = "seoul_ro",
        password: str = "seoul_ro_password_2024",
        database: str = "seoul_commercial",
    ):
        """
        데이터베이스 매니저 초기화

        Args:
            host: MySQL 호스트
            port: MySQL 포트
            user: 사용자명
            password: 비밀번호
            database: 데이터베이스명
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.engine = None

    def connect(self) -> bool:
        """데이터베이스 연결"""
        try:
            # MySQL 연결
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
            )

            # SQLAlchemy 엔진 생성
            connection_string = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
            self.engine = create_engine(connection_string, echo=False)

            logger.info(f"데이터베이스 '{self.database}'에 성공적으로 연결되었습니다.")
            return True

        except Error as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False

    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("데이터베이스 연결이 해제되었습니다.")

    def create_database(self) -> bool:
        """데이터베이스 생성"""
        try:
            # 데이터베이스 없이 연결
            temp_connection = mysql.connector.connect(
                host=self.host, port=self.port, user=self.user, password=self.password
            )

            cursor = temp_connection.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            temp_connection.commit()
            cursor.close()
            temp_connection.close()

            logger.info(f"데이터베이스 '{self.database}'가 생성되었습니다.")
            return True

        except Error as e:
            logger.error(f"데이터베이스 생성 실패: {e}")
            return False

    def create_tables(self) -> bool:
        """테이블 생성"""
        try:
            if not self.connection:
                self.connect()

            cursor = self.connection.cursor()

            # 테이블 생성 SQL
            tables_sql = {
                "regions": """
                    CREATE TABLE IF NOT EXISTS regions (
                        region_id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        gu VARCHAR(50) NOT NULL,
                        dong VARCHAR(50) NOT NULL,
                        lat DECIMAL(10, 8),
                        lon DECIMAL(11, 8),
                        adm_code VARCHAR(10),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_gu_dong (gu, dong),
                        INDEX idx_adm_code (adm_code)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                "industries": """
                    CREATE TABLE IF NOT EXISTS industries (
                        industry_id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        nace_kor VARCHAR(20),
                        category VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_name (name),
                        INDEX idx_category (category)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                "sales_2024": """
                    CREATE TABLE IF NOT EXISTS sales_2024 (
                        region_id INT NOT NULL,
                        industry_id INT NOT NULL,
                        date DATE NOT NULL,
                        sales_amt BIGINT DEFAULT 0,
                        sales_cnt INT DEFAULT 0,
                        visitors INT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (region_id, industry_id, date),
                        FOREIGN KEY (region_id) REFERENCES regions(region_id),
                        FOREIGN KEY (industry_id) REFERENCES industries(industry_id),
                        INDEX idx_date (date),
                        INDEX idx_sales_amt (sales_amt)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                "features": """
                    CREATE TABLE IF NOT EXISTS features (
                        region_id INT NOT NULL,
                        industry_id INT NOT NULL,
                        feat_json JSON,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        PRIMARY KEY (region_id, industry_id),
                        FOREIGN KEY (region_id) REFERENCES regions(region_id),
                        FOREIGN KEY (industry_id) REFERENCES industries(industry_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                "docs": """
                    CREATE TABLE IF NOT EXISTS docs (
                        doc_id INT AUTO_INCREMENT PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        source VARCHAR(100),
                        url VARCHAR(500),
                        published_date DATE,
                        meta_json JSON,
                        content_text LONGTEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_title (title),
                        INDEX idx_source (source),
                        INDEX idx_published_date (published_date)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
            }

            # 테이블 생성 실행
            for table_name, sql in tables_sql.items():
                cursor.execute(sql)
                logger.info(f"테이블 '{table_name}' 생성 완료")

            self.connection.commit()
            cursor.close()

            logger.info("모든 테이블이 성공적으로 생성되었습니다.")
            return True

        except Error as e:
            logger.error(f"테이블 생성 실패: {e}")
            return False

    def execute_query(self, query: str) -> pd.DataFrame | None:
        """SQL 쿼리 실행"""
        try:
            if not self.engine:
                self.connect()

            result = pd.read_sql(query, self.engine)
            return result

        except Exception as e:
            logger.error(f"쿼리 실행 실패: {e}")
            return None

    def insert_dataframe(
        self, df: pd.DataFrame, table_name: str, if_exists: str = "append"
    ) -> bool:
        """DataFrame을 테이블에 삽입"""
        try:
            if not self.engine:
                self.connect()

            df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
            logger.info(f"데이터가 '{table_name}' 테이블에 성공적으로 삽입되었습니다.")
            return True

        except Exception as e:
            logger.error(f"데이터 삽입 실패: {e}")
            return False

    def get_table_info(self) -> dict[str, Any]:
        """테이블 정보 조회"""
        try:
            if not self.connection:
                self.connect()

            cursor = self.connection.cursor()

            # 테이블 목록 조회
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]

            table_info = {}
            for table in tables:
                # 테이블 구조 조회
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()

                # 레코드 수 조회
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]

                table_info[table] = {"columns": columns, "count": count}

            cursor.close()
            return table_info

        except Error as e:
            logger.error(f"테이블 정보 조회 실패: {e}")
            return {}

    def __enter__(self):
        """Context manager 진입"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.disconnect()


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()