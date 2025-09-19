"""
표준화된 에러 처리 및 리트라이 메커니즘
development-policy.mdc 규칙에 따른 에러 모델 구현
"""

import json
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from infrastructure.logging_service import StructuredLogger


class ErrorType(Enum):
    """에러 타입 열거형"""
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    LLM_ERROR = "llm_error"
    RAG_ERROR = "rag_error"
    CACHE_ERROR = "cache_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    PERMISSION_ERROR = "permission_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """에러 심각도 열거형"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StandardError:
    """표준화된 에러 모델"""
    
    def __init__(
        self,
        error_type: ErrorType,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        error_code: str = None,
        details: dict[str, Any] = None,
        context: dict[str, Any] = None,
        timestamp: datetime = None,
        retryable: bool = False
    ):
        self.error_type = error_type
        self.message = message
        self.severity = severity
        self.error_code = error_code or f"{error_type.value}_{int(time.time())}"
        self.details = details or {}
        self.context = context or {}
        self.timestamp = timestamp or datetime.now()
        self.retryable = retryable
    
    def to_dict(self) -> dict[str, Any]:
        """에러를 딕셔너리로 변환"""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "severity": self.severity.value,
            "error_code": self.error_code,
            "details": self.details,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "retryable": self.retryable
        }
    
    def to_json(self) -> str:
        """에러를 JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def __str__(self) -> str:
        return f"[{self.error_type.value}] {self.message} (Code: {self.error_code})"
    
    def __repr__(self) -> str:
        return f"StandardError(type={self.error_type.value}, code={self.error_code}, message='{self.message}')"


class RetryConfig:
    """리트라이 설정"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class ErrorHandler:
    """표준화된 에러 핸들러"""
    
    def __init__(self):
        self.logger = StructuredLogger("error_handler")
        self.retry_config = RetryConfig()
        self.error_counts = {}
        self.circuit_breakers = {}
    
    def handle_exception(
        self,
        exception: Exception,
        error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
        context: dict[str, Any] = None,
        retryable: bool = False
    ) -> StandardError:
        """
        예외를 표준화된 에러로 변환
        
        Args:
            exception: 원본 예외
            error_type: 에러 타입
            context: 추가 컨텍스트
            retryable: 리트라이 가능 여부
            
        Returns:
            StandardError: 표준화된 에러 객체
        """
        try:
            # 에러 메시지 추출
            message = str(exception)
            if not message:
                message = f"Unknown {error_type.value} occurred"
            
            # 에러 세부 정보 구성
            details = {
                "exception_type": type(exception).__name__,
                "exception_module": getattr(exception, '__module__', 'unknown')
            }
            
            # 특정 예외 타입별 세부 정보 추가
            if hasattr(exception, 'errno'):
                details['errno'] = exception.errno
            if hasattr(exception, 'sqlstate'):
                details['sqlstate'] = exception.sqlstate
            if hasattr(exception, 'args'):
                details['args'] = list(exception.args)
            
            # 표준 에러 생성
            standard_error = StandardError(
                error_type=error_type,
                message=message,
                severity=self._determine_severity(error_type, exception),
                details=details,
                context=context or {},
                retryable=retryable
            )
            
            # 에러 로깅
            self._log_error(standard_error)
            
            # 에러 카운트 업데이트
            self._update_error_count(error_type)
            
            return standard_error
            
        except Exception as e:
            # 에러 처리 중 예외 발생 시 기본 에러 반환
            self.logger.error(f"Error in error handler: {e}")
            return StandardError(
                error_type=ErrorType.UNKNOWN_ERROR,
                message=f"Error handling failed: {str(e)}",
                severity=ErrorSeverity.CRITICAL,
                retryable=False
            )
    
    def _determine_severity(self, error_type: ErrorType, exception: Exception) -> ErrorSeverity:
        """에러 타입과 예외를 기반으로 심각도 결정"""
        severity_map = {
            ErrorType.VALIDATION_ERROR: ErrorSeverity.LOW,
            ErrorType.CACHE_ERROR: ErrorSeverity.LOW,
            ErrorType.NETWORK_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.TIMEOUT_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.DATABASE_ERROR: ErrorSeverity.HIGH,
            ErrorType.LLM_ERROR: ErrorSeverity.HIGH,
            ErrorType.RAG_ERROR: ErrorSeverity.HIGH,
            ErrorType.PERMISSION_ERROR: ErrorSeverity.HIGH,
            ErrorType.CONFIGURATION_ERROR: ErrorSeverity.CRITICAL,
            ErrorType.UNKNOWN_ERROR: ErrorSeverity.MEDIUM
        }
        
        return severity_map.get(error_type, ErrorSeverity.MEDIUM)
    
    def _log_error(self, error: StandardError):
        """에러 로깅"""
        log_data = error.to_dict()
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical error: {error.message}", **log_data)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"High severity error: {error.message}", **log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Medium severity error: {error.message}", **log_data)
        else:
            self.logger.info(f"Low severity error: {error.message}", **log_data)
    
    def _update_error_count(self, error_type: ErrorType):
        """에러 카운트 업데이트"""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
    
    def retry_with_backoff(
        self,
        func: Callable,
        *args,
        retry_config: RetryConfig = None,
        error_types: list[ErrorType] = None,
        context: dict[str, Any] = None,
        **kwargs
    ) -> Any:
        """
        백오프를 사용한 리트라이 실행
        
        Args:
            func: 실행할 함수
            *args: 함수 인자
            retry_config: 리트라이 설정
            error_types: 리트라이할 에러 타입 목록
            context: 컨텍스트 정보
            **kwargs: 함수 키워드 인자
            
        Returns:
            함수 실행 결과
        """
        config = retry_config or self.retry_config
        error_types = error_types or [ErrorType.NETWORK_ERROR, ErrorType.TIMEOUT_ERROR]
        
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                # 에러를 표준화
                standard_error = self.handle_exception(
                    e,
                    context=context,
                    retryable=True
                )
                
                # 리트라이 불가능한 에러인 경우 즉시 실패
                if not standard_error.retryable or standard_error.error_type not in error_types:
                    raise standard_error
                
                # 마지막 시도인 경우 실패
                if attempt == config.max_attempts - 1:
                    raise standard_error
                
                # 지연 시간 계산
                delay = self._calculate_delay(attempt, config)
                
                self.logger.warning(
                    f"Retry attempt {attempt + 1}/{config.max_attempts} after {delay:.2f}s",
                    function=func.__name__,
                    error_type=standard_error.error_type.value,
                    error_code=standard_error.error_code,
                    delay=delay,
                    context=context or {}
                )
                
                time.sleep(delay)
        
        # 이 지점에 도달하면 안 됨
        raise last_exception or Exception("Retry failed")
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """지연 시간 계산"""
        delay = config.base_delay * (config.exponential_base ** attempt)
        delay = min(delay, config.max_delay)
        
        if config.jitter:
            # 지터 추가 (±25%)
            import random
            jitter_factor = random.uniform(0.75, 1.25)
            delay *= jitter_factor
        
        return delay
    
    def validate_input(
        self,
        data: dict[str, Any],
        rules: dict[str, Any],
        context: str = "input_validation"
    ) -> Optional[StandardError]:
        """
        입력 데이터 검증
        
        Args:
            data: 검증할 데이터
            rules: 검증 규칙
            context: 검증 컨텍스트
            
        Returns:
            검증 실패 시 StandardError, 성공 시 None
        """
        try:
            for field, rule in rules.items():
                if field not in data:
                    if rule.get('required', False):
                        return StandardError(
                            error_type=ErrorType.VALIDATION_ERROR,
                            message=f"Required field '{field}' is missing",
                            severity=ErrorSeverity.LOW,
                            context={"field": field, "context": context}
                        )
                    continue
                
                value = data[field]
                
                # 타입 검증
                expected_type = rule.get('type')
                if expected_type and not isinstance(value, expected_type):
                    return StandardError(
                        error_type=ErrorType.VALIDATION_ERROR,
                        message=f"Field '{field}' must be of type {expected_type.__name__}",
                        severity=ErrorSeverity.LOW,
                        context={"field": field, "expected_type": expected_type.__name__, "actual_type": type(value).__name__, "context": context}
                    )
                
                # 길이 검증
                if isinstance(value, str):
                    min_length = rule.get('min_length')
                    max_length = rule.get('max_length')
                    
                    if min_length and len(value) < min_length:
                        return StandardError(
                            error_type=ErrorType.VALIDATION_ERROR,
                            message=f"Field '{field}' must be at least {min_length} characters long",
                            severity=ErrorSeverity.LOW,
                            context={"field": field, "min_length": min_length, "actual_length": len(value), "context": context}
                        )
                    
                    if max_length and len(value) > max_length:
                        return StandardError(
                            error_type=ErrorType.VALIDATION_ERROR,
                            message=f"Field '{field}' must be at most {max_length} characters long",
                            severity=ErrorSeverity.LOW,
                            context={"field": field, "max_length": max_length, "actual_length": len(value), "context": context}
                        )
                
                # 범위 검증
                if isinstance(value, (int, float)):
                    min_value = rule.get('min_value')
                    max_value = rule.get('max_value')
                    
                    if min_value is not None and value < min_value:
                        return StandardError(
                            error_type=ErrorType.VALIDATION_ERROR,
                            message=f"Field '{field}' must be at least {min_value}",
                            severity=ErrorSeverity.LOW,
                            context={"field": field, "min_value": min_value, "actual_value": value, "context": context}
                        )
                    
                    if max_value is not None and value > max_value:
                        return StandardError(
                            error_type=ErrorType.VALIDATION_ERROR,
                            message=f"Field '{field}' must be at most {max_value}",
                            severity=ErrorSeverity.LOW,
                            context={"field": field, "max_value": max_value, "actual_value": value, "context": context}
                        )
                
                # 정규식 검증
                pattern = rule.get('pattern')
                if pattern and isinstance(value, str):
                    import re
                    if not re.match(pattern, value):
                        return StandardError(
                            error_type=ErrorType.VALIDATION_ERROR,
                            message=f"Field '{field}' does not match required pattern",
                            severity=ErrorSeverity.LOW,
                            context={"field": field, "pattern": pattern, "context": context}
                        )
            
            return None
            
        except Exception as e:
            return StandardError(
                error_type=ErrorType.VALIDATION_ERROR,
                message=f"Validation error: {str(e)}",
                severity=ErrorSeverity.MEDIUM,
                context={"context": context}
            )
    
    def get_error_stats(self) -> dict[str, Any]:
        """에러 통계 반환"""
        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "circuit_breakers": self.circuit_breakers.copy()
        }
    
    def reset_error_counts(self):
        """에러 카운트 리셋"""
        self.error_counts.clear()
        self.circuit_breakers.clear()


# 전역 에러 핸들러 인스턴스
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """전역 에러 핸들러 인스턴스 반환"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


# 편의 함수들
def handle_exception(
    exception: Exception,
    error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
    context: dict[str, Any] = None,
    retryable: bool = False
) -> StandardError:
    """편의 함수: 예외 처리"""
    return get_error_handler().handle_exception(exception, error_type, context, retryable)


def retry_with_backoff(
    func: Callable,
    *args,
    retry_config: RetryConfig = None,
    error_types: list[ErrorType] = None,
    context: dict[str, Any] = None,
    **kwargs
) -> Any:
    """편의 함수: 리트라이 실행"""
    return get_error_handler().retry_with_backoff(
        func, *args, retry_config=retry_config, error_types=error_types, context=context, **kwargs
    )


def validate_input(
    data: dict[str, Any],
    rules: dict[str, Any],
    context: str = "input_validation"
) -> Optional[StandardError]:
    """편의 함수: 입력 검증"""
    return get_error_handler().validate_input(data, rules, context)


if __name__ == "__main__":
    # 테스트 코드
    error_handler = ErrorHandler()
    
    # 테스트 예외 처리
    try:
        raise ValueError("Test error")
    except Exception as e:
        error = error_handler.handle_exception(e, ErrorType.VALIDATION_ERROR)
        print(f"Error: {error}")
        print(f"JSON: {error.to_json()}")
    
    # 테스트 리트라이
    def failing_function():
        raise ConnectionError("Connection failed")
    
    try:
        result = error_handler.retry_with_backoff(
            failing_function,
            error_types=[ErrorType.NETWORK_ERROR]
        )
    except StandardError as e:
        print(f"Retry failed: {e}")
    
    print("Error handler test completed")