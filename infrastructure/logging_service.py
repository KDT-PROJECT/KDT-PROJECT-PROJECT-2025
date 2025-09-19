"""
구조화된 로깅 서비스
development-policy.mdc 규칙에 따른 JSON 로그 구현
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


class StructuredLogger:
    """구조화된 JSON 로그를 제공하는 로거"""

    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # 로그 파일 설정 (회전: 10MB/5files)
        self.log_file = self.log_dir / f"{name}.log"

        # 로거 설정
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 핸들러가 없으면 추가
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file, encoding="utf-8")
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _create_log_entry(
        self,
        level: str,
        message: str,
        query_id: str | None = None,
        latency_ms: float | None = None,
        mode: str | None = None,
        rows: int | None = None,
        hits: int | None = None,
        errors: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """구조화된 로그 엔트리 생성"""

        # 민감정보 마스킹
        masked_kwargs = self._mask_sensitive_data(kwargs)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
            "query_id": query_id,
            "latency_ms": latency_ms,
            "mode": mode,
            "rows": rows,
            "hits": hits,
            "errors": errors or [],
            **masked_kwargs,
        }

        return log_entry

    def _mask_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """민감정보 마스킹"""
        sensitive_keys = ["password", "api_key", "token", "secret", "key"]
        masked_data = {}

        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                masked_data[key] = "***MASKED***"
            elif isinstance(value, dict):
                masked_data[key] = self._mask_sensitive_data(value)
            else:
                masked_data[key] = value

        return masked_data

    def info(self, message: str, **kwargs):
        """INFO 레벨 로그"""
        log_entry = self._create_log_entry("INFO", message, **kwargs)
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))

    def debug(self, message: str, **kwargs):
        """DEBUG 레벨 로그"""
        log_entry = self._create_log_entry("DEBUG", message, **kwargs)
        self.logger.debug(json.dumps(log_entry, ensure_ascii=False))

    def warning(self, message: str, **kwargs):
        """WARNING 레벨 로그"""
        log_entry = self._create_log_entry("WARNING", message, **kwargs)
        self.logger.warning(json.dumps(log_entry, ensure_ascii=False))

    def error(self, message: str, **kwargs):
        """ERROR 레벨 로그"""
        log_entry = self._create_log_entry("ERROR", message, **kwargs)
        self.logger.error(json.dumps(log_entry, ensure_ascii=False))

    def log_query(
        self,
        query_id: str,
        query: str,
        mode: str,
        latency_ms: float,
        rows: int | None = None,
        hits: int | None = None,
        errors: list[str] | None = None,
    ):
        """쿼리 실행 로그"""
        self.info(
            f"Query executed: {mode}",
            query_id=query_id,
            query=query[:100] + "..." if len(query) > 100 else query,
            mode=mode,
            latency_ms=latency_ms,
            rows=rows,
            hits=hits,
            errors=errors,
        )

    def log_performance(
        self, operation: str, latency_ms: float, success: bool, **kwargs
    ):
        """성능 로그"""
        level = "INFO" if success else "WARNING"
        self.info(
            f"Performance: {operation}",
            operation=operation,
            latency_ms=latency_ms,
            success=success,
            **kwargs,
        )


class LoggingService:
    """로깅 서비스 싱글톤"""

    _instance = None
    _loggers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_logger(self, name: str) -> StructuredLogger:
        """로거 인스턴스 반환"""
        if name not in self._loggers:
            self._loggers[name] = StructuredLogger(name)
        return self._loggers[name]

    def get_system_logger(self) -> StructuredLogger:
        """시스템 로거 반환"""
        return self.get_logger("system")

    def get_sql_logger(self) -> StructuredLogger:
        """SQL 로거 반환"""
        return self.get_logger("sql")

    def get_rag_logger(self) -> StructuredLogger:
        """RAG 로거 반환"""
        return self.get_logger("rag")

    def get_report_logger(self) -> StructuredLogger:
        """보고서 로거 반환"""
        return self.get_logger("report")