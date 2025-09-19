"""
설정 관리 모듈
tech-stack.mdc 규칙에 따른 환경 설정
"""

import os

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# .env 파일 로드
load_dotenv()


class DatabaseConfig(BaseSettings):
    """데이터베이스 설정"""

    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=3306, env="DB_PORT")
    user: str = Field(default="seoul_ro", env="DB_USER")
    password: str = Field(default="seoul_ro_password_2024", env="DB_PASSWORD")
    database: str = Field(default="seoul_commercial", env="DB_NAME")
    
    # 추가 필드들 (extra_forbidden 오류 해결)
    mysql_user_ro: str = Field(default="seoul_ro", env="MYSQL_USER_RO")
    mysql_pwd_ro: str = Field(default="seoul_ro_password_2024", env="MYSQL_PWD_RO")
    mysql_url_ro: str = Field(default="mysql+pymysql://seoul_ro:seoul_ro_password_2024@localhost:3306/seoul_commercial", env="MYSQL_URL_RO")
    hf_model: str = Field(default="microsoft/DialoGPT-medium", env="HF_MODEL")
    llm_model: str = Field(default="microsoft/DialoGPT-medium", env="LLM_MODEL")
    hf_api_key: str = Field(default="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", env="HF_API_KEY")
    hf_temperature: str = Field(default="0.7", env="HF_TEMPERATURE")
    hf_max_tokens: str = Field(default="2000", env="HF_MAX_TOKENS")
    hf_timeout: str = Field(default="30", env="HF_TIMEOUT")
    anthropic_api_key: str = Field(default="sk-ant-api03-sEUwjLJ5D51...2lNqFwIAT_cYvg-GWn_SgAA", env="ANTHROPIC_API_KEY")
    serper_api_key: str = Field(default="8d3f4ba5afc9a6b61fdb653d642f7446eba2ce55", env="SERPER_API_KEY")
    tavily_api_key: str = Field(default="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", env="TAVILY_API_KEY")
    claude_model: str = Field(default="claude-3-5-sonnet-20241022", env="CLAUDE_MODEL")
    claude_max_tokens: str = Field(default="1500", env="CLAUDE_MAX_TOKENS")
    max_search_results: str = Field(default="10", env="MAX_SEARCH_RESULTS")
    user_agent: str = Field(default="Mozilla/5.0 (Windows NT ...x64) AppleWebKit/537.36", env="USER_AGENT")
    request_timeout: str = Field(default="30", env="REQUEST_TIMEOUT")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    index_path: str = Field(default="models/artifacts", env="INDEX_PATH")
    chunk_size: str = Field(default="1000", env="CHUNK_SIZE")
    chunk_overlap: str = Field(default="200", env="CHUNK_OVERLAP")
    top_k: str = Field(default="5", env="TOP_K")
    alpha: str = Field(default="0.5", env="ALPHA")
    max_query_length: str = Field(default="5000", env="MAX_QUERY_LENGTH")
    max_execution_time: str = Field(default="30", env="MAX_EXECUTION_TIME")
    max_result_rows: str = Field(default="10000", env="MAX_RESULT_ROWS")
    allowed_tables: str = Field(default="sales_2024,regions,industries,features", env="ALLOWED_TABLES")
    gemini_api_key: str = Field(default="AIzaSyCBq39sdhXGZuBBdpZlB0mdjOdYxWP3oJQ", env="GEMINI_API_KEY")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_dir: str = Field(default="logs", env="LOG_DIR")
    is_testing: str = Field(default="false", env="IS_TESTING")
    debug: str = Field(default="false", env="DEBUG")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # 추가 필드 허용

    def get_connection_string(self) -> str:
        """데이터베이스 연결 문자열 반환"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_connection_params(self) -> dict:
        """데이터베이스 연결 파라미터 반환"""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "charset": "utf8mb4",
            "autocommit": True,
        }


class LLMConfig(BaseSettings):
    """LLM 설정"""

    model: str = Field(default="microsoft/DialoGPT-medium", env="LLM_MODEL")
    api_key: str | None = Field(default=None, env="LLM_API_KEY")
    temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    timeout: int = Field(default=30, env="LLM_TIMEOUT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # 추가 필드 허용


class RAGConfig(BaseSettings):
    """RAG 설정"""

    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL"
    )
    index_path: str = Field(default="models/artifacts", env="INDEX_PATH")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    top_k: int = Field(default=5, env="TOP_K")
    alpha: float = Field(default=0.5, env="ALPHA")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # 추가 필드 허용


class SecurityConfig(BaseSettings):
    """보안 설정"""

    max_query_length: int = Field(default=5000, env="MAX_QUERY_LENGTH")
    max_execution_time: int = Field(default=30, env="MAX_EXECUTION_TIME")
    max_result_rows: int = Field(default=10000, env="MAX_RESULT_ROWS")
    allowed_tables: str = Field(
        default="sales_2024,regions,industries,features,docs,query_logs,v_sales_validation,v_region_sales_summary,v_industry_sales_summary,v_monthly_sales_trend", env="ALLOWED_TABLES"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # 추가 필드 허용

    def get_allowed_tables_list(self) -> list:
        """허용된 테이블 목록 반환"""
        return [table.strip() for table in self.allowed_tables.split(",")]


class GeminiConfig(BaseSettings):
    """Gemini API 설정"""

    api_key: str | None = Field(default=None, env="GEMINI_API_KEY")
    GEMINI_API_KEY: str | None = Field(default=None, env="GEMINI_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # 추가 필드 허용


class LoggingConfig(BaseSettings):
    """로깅 설정"""

    level: str = Field(default="INFO", env="LOG_LEVEL")
    directory: str = Field(default="logs", env="LOG_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # 추가 필드 허용


class AppConfig:
    """애플리케이션 전체 설정"""

    def __init__(self):
        self.database = DatabaseConfig()
        self.llm = LLMConfig()
        self.rag = RAGConfig()
        self.security = SecurityConfig()
        self.gemini = GeminiConfig()
        self.logging = LoggingConfig()

    def validate_config(self) -> bool:
        """설정 유효성 검증"""
        try:
            # 필수 설정 검증
            assert self.database.host, "DB_HOST가 설정되지 않았습니다"
            assert self.database.user, "DB_USER가 설정되지 않았습니다"
            assert self.database.database, "DB_NAME이 설정되지 않았습니다"

            # 로깅 디렉토리 생성
            os.makedirs(self.logging.directory, exist_ok=True)

            # 인덱스 디렉토리 생성
            os.makedirs(self.rag.index_path, exist_ok=True)

            return True
        except Exception as e:
            print(f"설정 검증 실패: {e}")
            return False


# 전역 설정 인스턴스
config = AppConfig()

# 설정 검증
if not config.validate_config():
    raise RuntimeError("애플리케이션 설정 검증에 실패했습니다")


# 편의 함수들
def get_database_config() -> DatabaseConfig:
    """데이터베이스 설정 반환 (get_db_config의 별칭)"""
    return config.database

def get_db_config() -> DatabaseConfig:
    return config.database


def get_llm_config() -> LLMConfig:
    return config.llm


def get_rag_config() -> RAGConfig:
    return config.rag


def get_security_config() -> SecurityConfig:
    return config.security


def get_gemini_config() -> GeminiConfig:
    return config.gemini


def get_logging_config() -> LoggingConfig:
    return config.logging
