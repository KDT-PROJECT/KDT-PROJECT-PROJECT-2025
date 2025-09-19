<<<<<<< HEAD
"""
데이터베이스 관리 모듈
tech-stack.mdc 규칙에 따른 MySQL 연결 및 관리
"""

import logging
from contextlib import contextmanager
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from config import config

# 로깅 설정
logging.basicConfig(level=getattr(logging, config.logging.level))
logger = logging.getLogger(__name__)


class DatabaseManager:
    """데이터베이스 관리 클래스"""

    def __init__(self):
        self.engine = None
        self.Session = None
        self._initialize_connection()

    def _initialize_connection(self):
        """데이터베이스 연결 초기화"""
        try:
            connection_string = config.database.get_connection_string()
            self.engine = create_engine(
                connection_string, pool_pre_ping=True, pool_recycle=3600, echo=False
            )
            self.Session = sessionmaker(bind=self.engine)
            logger.info("데이터베이스 연결이 초기화되었습니다")
        except Exception as e:
            logger.error(f"데이터베이스 연결 초기화 실패: {e}")
            raise

    @contextmanager
    def get_session(self):
        """데이터베이스 세션 컨텍스트 매니저"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"데이터베이스 세션 오류: {e}")
            raise
        finally:
            session.close()

    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("데이터베이스 연결 테스트 성공")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {e}")
            return False

    def execute_schema_migration(self, schema_file_path: str) -> bool:
        """스키마 마이그레이션 실행"""
        try:
            with open(schema_file_path, encoding="utf-8") as f:
                schema_sql = f.read()

            with self.engine.connect() as conn:
                # 트랜잭션으로 실행
                trans = conn.begin()
                try:
                    # SQL 문을 세미콜론으로 분리하여 실행
                    for statement in schema_sql.split(";"):
                        statement = statement.strip()
                        if statement and not statement.startswith("--"):
                            conn.execute(text(statement))
                    trans.commit()
                    logger.info("스키마 마이그레이션이 성공적으로 실행되었습니다")
                    return True
                except Exception as e:
                    trans.rollback()
                    logger.error(f"스키마 마이그레이션 실행 실패: {e}")
                    return False
        except Exception as e:
            logger.error(f"스키마 파일 읽기 실패: {e}")
            return False

    def get_table_info(self, table_name: str) -> dict[str, Any] | None:
        """테이블 정보 조회"""
        try:
            inspector = inspect(self.engine)
            if not inspector.has_table(table_name):
                logger.warning(f"테이블 {table_name}이 존재하지 않습니다")
                return None

            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)

            return {
                "table_name": table_name,
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys,
            }
        except Exception as e:
            logger.error(f"테이블 정보 조회 실패: {e}")
            return None

    def get_all_tables(self) -> list[str]:
        """모든 테이블 목록 조회"""
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except Exception as e:
            logger.error(f"테이블 목록 조회 실패: {e}")
            return []

    def execute_query(self, query: str, params: dict | None = None) -> pd.DataFrame:
        """안전한 쿼리 실행 (SELECT만 허용)"""
        try:
            # SQL 가드 검증
            if not self._validate_sql_query(query):
                raise ValueError("허용되지 않는 SQL 쿼리입니다")

            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                df = pd.DataFrame(result.fetchall(), columns=result.keys())

                # 결과 행 수 제한
                if len(df) > config.security.max_result_rows:
                    logger.warning(
                        f"결과 행 수가 제한을 초과했습니다. {config.security.max_result_rows}행으로 제한합니다"
                    )
                    df = df.head(config.security.max_result_rows)

                logger.info(f"쿼리 실행 성공: {len(df)}행 반환")
                return df

        except Exception as e:
            logger.error(f"쿼리 실행 실패: {e}")
            raise

    def _validate_sql_query(self, query: str) -> bool:
        """SQL 쿼리 보안 검증"""
        query_upper = query.upper().strip()

        # SELECT만 허용
        if not query_upper.startswith("SELECT"):
            logger.warning("SELECT가 아닌 쿼리는 허용되지 않습니다")
            return False

        # 금지된 키워드 검사
        forbidden_keywords = [
            "INSERT",
            "UPDATE",
            "DELETE",
            "ALTER",
            "DROP",
            "TRUNCATE",
            "GRANT",
            "REVOKE",
            "CREATE",
            "EXEC",
            "EXECUTE",
            "CALL",
        ]

        for keyword in forbidden_keywords:
            if keyword in query_upper:
                logger.warning(f"금지된 키워드 {keyword}가 포함되어 있습니다")
                return False

        # 허용된 테이블만 조인 허용
        allowed_tables = config.security.get_allowed_tables_list()
        for table in allowed_tables:
            if table.upper() in query_upper:
                return True

        logger.warning("허용되지 않은 테이블이 포함되어 있습니다")
        return False

    def get_table_sample(self, table_name: str, limit: int = 10) -> pd.DataFrame:
        """테이블 샘플 데이터 조회"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"테이블 샘플 조회 실패: {e}")
            raise

    def get_table_count(self, table_name: str) -> int:
        """테이블 행 수 조회"""
        try:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            result = self.execute_query(query)
            return result["count"].iloc[0]
        except Exception as e:
            logger.error(f"테이블 행 수 조회 실패: {e}")
            return 0

    def close_connection(self):
        """데이터베이스 연결 종료"""
        if self.engine:
            self.engine.dispose()
            logger.info("데이터베이스 연결이 종료되었습니다")


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()


def get_database_manager() -> DatabaseManager:
    """데이터베이스 매니저 인스턴스 반환"""
    return db_manager
=======
"""
데이터베이스 관리 모듈
tech-stack.mdc 규칙에 따른 MySQL 연결 및 관리
"""

import logging
from contextlib import contextmanager
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from config import config

# 로깅 설정
logging.basicConfig(level=getattr(logging, config.logging.level))
logger = logging.getLogger(__name__)


class DatabaseManager:
    """데이터베이스 관리 클래스"""

    def __init__(self):
        self.engine = None
        self.Session = None
        self._initialize_connection()

    def _initialize_connection(self):
        """데이터베이스 연결 초기화"""
        try:
            connection_string = config.database.get_connection_string()
            self.engine = create_engine(
                connection_string, pool_pre_ping=True, pool_recycle=3600, echo=False
            )
            self.Session = sessionmaker(bind=self.engine)
            logger.info("데이터베이스 연결이 초기화되었습니다")
        except Exception as e:
            logger.error(f"데이터베이스 연결 초기화 실패: {e}")
            raise

    @contextmanager
    def get_session(self):
        """데이터베이스 세션 컨텍스트 매니저"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"데이터베이스 세션 오류: {e}")
            raise
        finally:
            session.close()

    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("데이터베이스 연결 테스트 성공")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {e}")
            return False

    def execute_schema_migration(self, schema_file_path: str) -> bool:
        """스키마 마이그레이션 실행"""
        try:
            with open(schema_file_path, encoding="utf-8") as f:
                schema_sql = f.read()

            with self.engine.connect() as conn:
                # 트랜잭션으로 실행
                trans = conn.begin()
                try:
                    # SQL 문을 세미콜론으로 분리하여 실행
                    for statement in schema_sql.split(";"):
                        statement = statement.strip()
                        if statement and not statement.startswith("--"):
                            conn.execute(text(statement))
                    trans.commit()
                    logger.info("스키마 마이그레이션이 성공적으로 실행되었습니다")
                    return True
                except Exception as e:
                    trans.rollback()
                    logger.error(f"스키마 마이그레이션 실행 실패: {e}")
                    return False
        except Exception as e:
            logger.error(f"스키마 파일 읽기 실패: {e}")
            return False

    def get_table_info(self, table_name: str) -> dict[str, Any] | None:
        """테이블 정보 조회"""
        try:
            inspector = inspect(self.engine)
            if not inspector.has_table(table_name):
                logger.warning(f"테이블 {table_name}이 존재하지 않습니다")
                return None

            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)

            return {
                "table_name": table_name,
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys,
            }
        except Exception as e:
            logger.error(f"테이블 정보 조회 실패: {e}")
            return None

    def get_all_tables(self) -> list[str]:
        """모든 테이블 목록 조회"""
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except Exception as e:
            logger.error(f"테이블 목록 조회 실패: {e}")
            return []

    def execute_query(self, query: str, params: dict | None = None) -> pd.DataFrame:
        """안전한 쿼리 실행 (SELECT만 허용)"""
        try:
            # SQL 가드 검증
            if not self._validate_sql_query(query):
                raise ValueError("허용되지 않는 SQL 쿼리입니다")

            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                df = pd.DataFrame(result.fetchall(), columns=result.keys())

                # 결과 행 수 제한
                if len(df) > config.security.max_result_rows:
                    logger.warning(
                        f"결과 행 수가 제한을 초과했습니다. {config.security.max_result_rows}행으로 제한합니다"
                    )
                    df = df.head(config.security.max_result_rows)

                logger.info(f"쿼리 실행 성공: {len(df)}행 반환")
                return df

        except Exception as e:
            logger.error(f"쿼리 실행 실패: {e}")
            raise

    def _validate_sql_query(self, query: str) -> bool:
        """SQL 쿼리 보안 검증"""
        query_upper = query.upper().strip()

        # SELECT만 허용
        if not query_upper.startswith("SELECT"):
            logger.warning("SELECT가 아닌 쿼리는 허용되지 않습니다")
            return False

        # 금지된 키워드 검사
        forbidden_keywords = [
            "INSERT",
            "UPDATE",
            "DELETE",
            "ALTER",
            "DROP",
            "TRUNCATE",
            "GRANT",
            "REVOKE",
            "CREATE",
            "EXEC",
            "EXECUTE",
            "CALL",
        ]

        for keyword in forbidden_keywords:
            if keyword in query_upper:
                logger.warning(f"금지된 키워드 {keyword}가 포함되어 있습니다")
                return False

        # 허용된 테이블만 조인 허용
        allowed_tables = config.security.get_allowed_tables_list()
        for table in allowed_tables:
            if table.upper() in query_upper:
                return True

        logger.warning("허용되지 않은 테이블이 포함되어 있습니다")
        return False

    def get_table_sample(self, table_name: str, limit: int = 10) -> pd.DataFrame:
        """테이블 샘플 데이터 조회"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"테이블 샘플 조회 실패: {e}")
            raise

    def get_table_count(self, table_name: str) -> int:
        """테이블 행 수 조회"""
        try:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            result = self.execute_query(query)
            return result["count"].iloc[0]
        except Exception as e:
            logger.error(f"테이블 행 수 조회 실패: {e}")
            return 0

    def close_connection(self):
        """데이터베이스 연결 종료"""
        if self.engine:
            self.engine.dispose()
            logger.info("데이터베이스 연결이 종료되었습니다")


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()


def get_database_manager() -> DatabaseManager:
    """데이터베이스 매니저 인스턴스 반환"""
    return db_manager
>>>>>>> b15a617 (first commit)
