"""
Infrastructure Layer 테스트
TDD 프로세스에 따른 테스트 코드
"""

import os
import tempfile

import pytest

from infrastructure.cache_service import CacheService
from infrastructure.config_service import ConfigService, DatabaseConfig
from infrastructure.logging_service import StructuredLogger


class TestStructuredLogger:
    """구조화된 로거 테스트"""

    def test_logger_creation(self):
        """로거 생성 테스트"""
        logger = StructuredLogger("test_logger")
        assert logger.name == "test_logger"
        assert logger.log_dir.exists()

    def test_log_entry_creation(self):
        """로그 엔트리 생성 테스트"""
        logger = StructuredLogger("test_logger")
        log_entry = logger._create_log_entry(
            "INFO", "Test message", query_id="test_123", latency_ms=100.5
        )

        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Test message"
        assert log_entry["query_id"] == "test_123"
        assert log_entry["latency_ms"] == 100.5
        assert "timestamp" in log_entry

    def test_sensitive_data_masking(self):
        """민감정보 마스킹 테스트"""
        logger = StructuredLogger("test_logger")
        data = {
            "username": "test_user",
            "password": "secret123",
            "api_key": "key_12345",
            "normal_data": "safe_data",
        }

        masked_data = logger._mask_sensitive_data(data)

        assert masked_data["username"] == "test_user"
        assert masked_data["password"] == "***MASKED***"
        assert masked_data["api_key"] == "***MASKED***"
        assert masked_data["normal_data"] == "safe_data"


class TestConfigService:
    """설정 서비스 테스트"""

    def test_database_config_creation(self):
        """데이터베이스 설정 생성 테스트"""
        config = DatabaseConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        assert config.host == "localhost"
        assert config.port == 3306
        assert (
            config.connection_url
            == "mysql+pymysql://test_user:test_pass@localhost:3306/test_db"
        )

    def test_config_service_with_env_file(self):
        """환경 파일을 사용한 설정 서비스 테스트"""
        # 임시 환경 파일 생성
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".env") as f:
            f.write("DB_HOST=test_host\n")
            f.write("DB_PORT=3307\n")
            f.write("DB_USER=test_user\n")
            f.write("DB_PASSWORD=test_pass\n")
            f.write("DB_NAME=test_db\n")
            f.write("LLM_MODEL=test_model\n")
            temp_file = f.name

        try:
            config_service = ConfigService(temp_file)
            db_config = config_service.get_database_config()

            assert db_config.host == "test_host"
            assert db_config.port == 3307
            assert db_config.user == "test_user"
            assert db_config.password == "test_pass"
            assert db_config.database == "test_db"

        finally:
            os.unlink(temp_file)

    def test_missing_required_vars(self):
        """필수 환경 변수 누락 테스트"""
        # 기존 환경 변수 백업
        original_env = {}
        required_vars = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]
        for var in required_vars:
            original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        try:
            with pytest.raises(
                ValueError, match="Missing required environment variables"
            ):
                ConfigService()
        finally:
            # 환경 변수 복원
            for var, value in original_env.items():
                if value is not None:
                    os.environ[var] = value


class TestCacheService:
    """캐시 서비스 테스트"""

    def test_cache_creation(self):
        """캐시 생성 테스트"""
        cache = CacheService(max_size=10, ttl_seconds=60)
        assert cache.max_size == 10
        assert cache.ttl_seconds == 60
        assert len(cache.cache) == 0

    def test_cache_set_get(self):
        """캐시 저장/조회 테스트"""
        cache = CacheService()

        # 값 저장
        cache.set("test_query", "sql", "value1")
        assert cache.get("test_query", "sql") == "value1"
        assert len(cache.cache) == 1

    def test_cache_expiration(self):
        """캐시 만료 테스트"""
        cache = CacheService(ttl_seconds=1)  # 1초 TTL

        cache.set("test_query", "sql", "value1")
        assert cache.get("test_query", "sql") == "value1"

        # 1초 대기 후 만료 확인
        import time

        time.sleep(1.1)
        assert cache.get("test_query", "sql") is None

    def test_cache_lru_eviction(self):
        """LRU 캐시 제거 테스트"""
        cache = CacheService(max_size=2)

        cache.set("query1", "sql", "value1")
        cache.set("query2", "sql", "value2")
        cache.set("query3", "sql", "value3")  # query1이 제거되어야 함

        assert cache.get("query1", "sql") is None
        assert cache.get("query2", "sql") == "value2"
        assert cache.get("query3", "sql") == "value3"

    def test_cache_key_generation(self):
        """캐시 키 생성 테스트"""
        cache = CacheService()

        key1 = cache._generate_key("query1", "sql", param1="value1")
        key2 = cache._generate_key("query1", "sql", param1="value1")
        key3 = cache._generate_key("query1", "sql", param1="value2")

        assert key1 == key2  # 동일한 인자
        assert key1 != key3  # 다른 인자

    def test_singleton_pattern(self):
        """싱글톤 패턴 테스트"""
        from infrastructure.cache_service import get_cache_service

        service1 = get_cache_service()
        service2 = get_cache_service()

        assert service1 is service2

    def test_get_cache_service(self):
        """캐시 서비스 인스턴스 반환 테스트"""
        from infrastructure.cache_service import get_cache_service

        cache1 = get_cache_service()
        cache2 = get_cache_service()

        assert cache1 is cache2

    def test_query_cache(self):
        """쿼리 캐시 테스트"""
        from infrastructure.cache_service import get_query_cache

        query_cache = get_query_cache()

        # SQL 결과 캐시 테스트
        query_cache.set_sql_result("test_query", {"data": "test_data"})
        result = query_cache.get_sql_result("test_query")
        assert result == {"data": "test_data"}

        # RAG 결과 캐시 테스트
        query_cache.set_rag_result("test_query", {"docs": "test_docs"})
        result = query_cache.get_rag_result("test_query")
        assert result == {"docs": "test_docs"}

        # Mixed 결과 캐시 테스트
        query_cache.set_mixed_result("test_query", {"mixed": "test_mixed"})
        result = query_cache.get_mixed_result("test_query")
        assert result == {"mixed": "test_mixed"}


if __name__ == "__main__":
    pytest.main([__file__])
