"""
설정 관리 서비스
development-policy.mdc 규칙에 따른 .env 기반 설정 관리
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""

    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def connection_url(self) -> str:
        """MySQL 연결 URL 생성"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class LLMConfig:
    """LLM 설정"""

    model_name: str
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30


@dataclass
class RAGConfig:
    """RAG 설정"""

    embedding_model: str
    index_path: str
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    alpha: float = 0.5  # 하이브리드 검색 가중치


@dataclass
class SecurityConfig:
    """보안 설정"""

    max_query_length: int = 5000
    max_execution_time: int = 30
    max_result_rows: int = 10000
    allowed_tables: list = None

    def __post_init__(self):
        if self.allowed_tables is None:
            self.allowed_tables = ["sales_2024", "regions", "industries", "features"]


class ConfigService:
    """설정 관리 서비스"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self._load_environment()
        self._validate_required_vars()

    def _load_environment(self):
        """환경 변수 로드"""
        if self.env_file.exists():
            with open(self.env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()

    def _validate_required_vars(self):
        """필수 환경 변수 검증"""
        required_vars = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

    def get_database_config(self) -> DatabaseConfig:
        """데이터베이스 설정 반환"""
        return DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )

    def get_llm_config(self) -> LLMConfig:
        """LLM 설정 반환"""
        return LLMConfig(
            model_name=os.getenv("LLM_MODEL", "microsoft/DialoGPT-medium"),
            api_key=os.getenv("LLM_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30")),
        )

    def get_rag_config(self) -> RAGConfig:
        """RAG 설정 반환"""
        return RAGConfig(
            embedding_model=os.getenv(
                "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            index_path=os.getenv("INDEX_PATH", "models/artifacts"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            top_k=int(os.getenv("TOP_K", "5")),
            alpha=float(os.getenv("ALPHA", "0.5")),
        )

    def get_security_config(self) -> SecurityConfig:
        """보안 설정 반환"""
        return SecurityConfig(
            max_query_length=int(os.getenv("MAX_QUERY_LENGTH", "5000")),
            max_execution_time=int(os.getenv("MAX_EXECUTION_TIME", "30")),
            max_result_rows=int(os.getenv("MAX_RESULT_ROWS", "10000")),
            allowed_tables=(
                os.getenv("ALLOWED_TABLES", "").split(",")
                if os.getenv("ALLOWED_TABLES")
                else None
            ),
        )

    def get_config_dict(self) -> dict[str, Any]:
        """전체 설정을 딕셔너리로 반환"""
        return {
            "database": self.get_database_config(),
            "llm": self.get_llm_config(),
            "rag": self.get_rag_config(),
            "security": self.get_security_config(),
        }

    def save_config(self, config: dict[str, Any], file_path: str = "config.json"):
        """설정을 JSON 파일로 저장"""
        config_dict = {}

        for key, value in config.items():
            if hasattr(value, "__dict__"):
                config_dict[key] = value.__dict__
            else:
                config_dict[key] = value

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

    def load_config(self, file_path: str = "config.json") -> dict[str, Any]:
        """JSON 파일에서 설정 로드"""
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
