"""
캐시 서비스 모듈
system-architecture.mdc 규칙에 따른 세션 캐시 및 성능 최적화
"""

import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class CacheService:
    """세션 캐시 및 성능 최적화 서비스"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        캐시 서비스 초기화

        Args:
            max_size: 최대 캐시 항목 수
            ttl_seconds: 캐시 TTL (초)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: dict[str, dict[str, Any]] = {}
        self.access_times: dict[str, float] = {}
        self.hit_count = 0
        self.miss_count = 0

        logger.info(f"캐시 서비스 초기화: max_size={max_size}, ttl={ttl_seconds}s")

    def _generate_key(self, query: str, mode: str, **kwargs) -> str:
        """캐시 키 생성"""
        # 쿼리와 모드를 기반으로 해시 키 생성
        key_data = {"query": query, "mode": mode, **kwargs}
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _is_expired(self, timestamp: float) -> bool:
        """캐시 항목 만료 여부 확인"""
        return time.time() - timestamp > self.ttl_seconds

    def _cleanup_expired(self):
        """만료된 캐시 항목 정리"""
        current_time = time.time()
        expired_keys = [
            key
            for key, timestamp in self.access_times.items()
            if current_time - timestamp > self.ttl_seconds
        ]

        for key in expired_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)

        if expired_keys:
            logger.debug(f"만료된 캐시 항목 {len(expired_keys)}개 정리")

    def _evict_lru(self):
        """LRU 방식으로 캐시 항목 제거"""
        if len(self.cache) >= self.max_size:
            # 가장 오래된 항목 찾기
            oldest_key = min(
                self.access_times.keys(), key=lambda k: self.access_times[k]
            )
            self.cache.pop(oldest_key, None)
            self.access_times.pop(oldest_key, None)
            logger.debug(f"LRU 캐시 항목 제거: {oldest_key}")

    def get(self, query: str, mode: str, **kwargs) -> Any | None:
        """
        캐시에서 데이터 조회

        Args:
            query: 검색 쿼리
            mode: 분석 모드 (sql, rag, mixed)
            **kwargs: 추가 파라미터

        Returns:
            캐시된 데이터 또는 None
        """
        key = self._generate_key(query, mode, **kwargs)

        # 만료된 항목 정리
        self._cleanup_expired()

        if key in self.cache:
            cache_entry = self.cache[key]

            # TTL 확인
            if not self._is_expired(cache_entry["timestamp"]):
                # 접근 시간 업데이트
                self.access_times[key] = time.time()
                self.hit_count += 1
                logger.debug(f"캐시 히트: {key}")
                return cache_entry["data"]
            else:
                # 만료된 항목 제거
                self.cache.pop(key, None)
                self.access_times.pop(key, None)
                logger.debug(f"만료된 캐시 항목 제거: {key}")

        self.miss_count += 1
        logger.debug(f"캐시 미스: {key}")
        return None

    def set(self, query: str, mode: str, data: Any, **kwargs) -> None:
        """
        캐시에 데이터 저장

        Args:
            query: 검색 쿼리
            mode: 분석 모드 (sql, rag, mixed)
            data: 저장할 데이터
            **kwargs: 추가 파라미터
        """
        key = self._generate_key(query, mode, **kwargs)

        # 캐시 크기 확인 및 LRU 제거
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        # 캐시 항목 저장
        self.cache[key] = {
            "data": data,
            "timestamp": time.time(),
            "query": query,
            "mode": mode,
        }
        self.access_times[key] = time.time()

        logger.debug(f"캐시 저장: {key}")

    def invalidate(self, query: str = None, mode: str = None) -> int:
        """
        캐시 무효화

        Args:
            query: 특정 쿼리 (None이면 모든 쿼리)
            mode: 특정 모드 (None이면 모든 모드)

        Returns:
            무효화된 항목 수
        """
        if query is None and mode is None:
            # 모든 캐시 무효화
            count = len(self.cache)
            self.cache.clear()
            self.access_times.clear()
            logger.info(f"전체 캐시 무효화: {count}개 항목")
            return count

        # 조건부 무효화
        keys_to_remove = []
        for key, cache_entry in self.cache.items():
            if query and cache_entry["query"] != query:
                continue
            if mode and cache_entry["mode"] != mode:
                continue
            keys_to_remove.append(key)

        for key in keys_to_remove:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)

        logger.info(f"조건부 캐시 무효화: {len(keys_to_remove)}개 항목")
        return len(keys_to_remove)

    def get_stats(self) -> dict[str, Any]:
        """캐시 통계 반환"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0

        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl_seconds,
        }

    def clear(self) -> None:
        """전체 캐시 클리어"""
        self.cache.clear()
        self.access_times.clear()
        self.hit_count = 0
        self.miss_count = 0
        logger.info("캐시 클리어 완료")

    def get_cache_info(self) -> list[dict[str, Any]]:
        """캐시 정보 반환 (디버깅용)"""
        cache_info = []
        current_time = time.time()

        for key, cache_entry in self.cache.items():
            age = current_time - cache_entry["timestamp"]
            is_expired = self._is_expired(cache_entry["timestamp"])

            cache_info.append(
                {
                    "key": key,
                    "query": cache_entry["query"],
                    "mode": cache_entry["mode"],
                    "age_seconds": age,
                    "is_expired": is_expired,
                    "last_access": self.access_times.get(key, 0),
                }
            )

        return sorted(cache_info, key=lambda x: x["last_access"], reverse=True)


class QueryCache:
    """쿼리별 캐시 관리"""

    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service

    def get_sql_result(self, query: str, **kwargs) -> Any | None:
        """SQL 결과 캐시 조회"""
        return self.cache_service.get(query, "sql", **kwargs)

    def set_sql_result(self, query: str, result: Any, **kwargs) -> None:
        """SQL 결과 캐시 저장"""
        self.cache_service.set(query, "sql", result, **kwargs)

    def get_rag_result(self, query: str, **kwargs) -> Any | None:
        """RAG 결과 캐시 조회"""
        return self.cache_service.get(query, "rag", **kwargs)

    def set_rag_result(self, query: str, result: Any, **kwargs) -> None:
        """RAG 결과 캐시 저장"""
        self.cache_service.set(query, "rag", result, **kwargs)

    def get_mixed_result(self, query: str, **kwargs) -> Any | None:
        """혼합 결과 캐시 조회"""
        return self.cache_service.get(query, "mixed", **kwargs)

    def set_mixed_result(self, query: str, result: Any, **kwargs) -> None:
        """혼합 결과 캐시 저장"""
        self.cache_service.set(query, "mixed", result, **kwargs)


# 전역 캐시 서비스 인스턴스
_cache_service = None


def get_cache_service() -> CacheService:
    """캐시 서비스 인스턴스 반환"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def get_query_cache() -> QueryCache:
    """쿼리 캐시 인스턴스 반환"""
    return QueryCache(get_cache_service())
