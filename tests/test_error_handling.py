"""
에러 처리 및 리트라이 메커니즘 테스트
TASK-015: 로깅/에러 표준화
"""

import pytest
import time
from unittest.mock import Mock, patch

from infrastructure.error_handler import (
    ErrorHandler, ErrorType, ErrorSeverity, StandardError, RetryConfig,
    get_error_handler, handle_exception, retry_with_backoff
)
from infrastructure.decorators import (
    error_handler, retry_on_error, performance_monitor, safe_execute
)


class TestErrorHandler:
    """에러 핸들러 테스트"""

    def test_create_error(self):
        """표준 에러 생성 테스트"""
        handler = ErrorHandler()
        
        error = handler.create_error(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Test validation error",
            severity=ErrorSeverity.MEDIUM,
            error_code="TEST_001",
            details={"field": "test_field"},
            context={"operation": "test_operation"}
        )
        
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.message == "Test validation error"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.error_code == "TEST_001"
        assert error.details["field"] == "test_field"
        assert error.context["operation"] == "test_operation"
        assert error.retryable is False

    def test_handle_exception(self):
        """예외 처리 테스트"""
        handler = ErrorHandler()
        
        # ValueError 예외 처리
        try:
            raise ValueError("Test value error")
        except Exception as e:
            error = handler.handle_exception(e, context={"test": "context"})
            
            assert error.error_type == ErrorType.VALIDATION_ERROR
            assert "Test value error" in error.message
            assert error.original_error == e
            assert error.context["test"] == "context"

    def test_handle_network_exception(self):
        """네트워크 예외 처리 테스트"""
        handler = ErrorHandler()
        
        try:
            raise ConnectionError("Test connection error")
        except Exception as e:
            error = handler.handle_exception(e)
            
            assert error.error_type == ErrorType.NETWORK_ERROR
            assert error.retryable is True

    def test_validate_input_success(self):
        """입력 검증 성공 테스트"""
        handler = ErrorHandler()
        
        data = {"name": "test", "age": 25, "email": "test@example.com"}
        rules = {
            "required_fields": ["name", "age"],
            "type_checks": {"age": int, "name": str},
            "range_checks": {"age": (0, 100)}
        }
        
        error = handler.validate_input(data, rules)
        assert error is None

    def test_validate_input_missing_field(self):
        """입력 검증 실패 - 필수 필드 누락"""
        handler = ErrorHandler()
        
        data = {"name": "test"}
        rules = {"required_fields": ["name", "age"]}
        
        error = handler.validate_input(data, rules)
        assert error is not None
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert "age" in error.message

    def test_validate_input_wrong_type(self):
        """입력 검증 실패 - 잘못된 타입"""
        handler = ErrorHandler()
        
        data = {"age": "not_a_number"}
        rules = {"type_checks": {"age": int}}
        
        error = handler.validate_input(data, rules)
        assert error is not None
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert "wrong type" in error.message

    def test_validate_input_out_of_range(self):
        """입력 검증 실패 - 범위 초과"""
        handler = ErrorHandler()
        
        data = {"age": 150}
        rules = {"range_checks": {"age": (0, 100)}}
        
        error = handler.validate_input(data, rules)
        assert error is not None
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert "out of range" in error.message

    def test_retry_with_backoff_success(self):
        """리트라이 성공 테스트"""
        handler = ErrorHandler()
        
        call_count = 0
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Test connection error")
            return "success"
        
        result = handler.retry_with_backoff(
            test_func,
            error_types=[ErrorType.NETWORK_ERROR]
        )
        
        assert result == "success"
        assert call_count == 2

    def test_retry_with_backoff_max_attempts(self):
        """리트라이 최대 시도 횟수 초과 테스트"""
        handler = ErrorHandler()
        
        def failing_func():
            raise ConnectionError("Test connection error")
        
        with pytest.raises(StandardError):
            handler.retry_with_backoff(
                failing_func,
                error_types=[ErrorType.NETWORK_ERROR]
            )

    def test_retry_with_backoff_non_retryable_error(self):
        """리트라이 불가능한 에러 테스트"""
        handler = ErrorHandler()
        
        def failing_func():
            raise ValueError("Test validation error")
        
        with pytest.raises(StandardError):
            handler.retry_with_backoff(
                failing_func,
                error_types=[ErrorType.NETWORK_ERROR]  # ValueError는 리트라이하지 않음
            )

    def test_get_error_summary(self):
        """에러 요약 테스트"""
        handler = ErrorHandler()
        
        errors = [
            handler.create_error(ErrorType.VALIDATION_ERROR, "Error 1"),
            handler.create_error(ErrorType.DATABASE_ERROR, "Error 2"),
            handler.create_error(ErrorType.VALIDATION_ERROR, "Error 3"),
        ]
        
        summary = handler.get_error_summary(errors)
        
        assert summary["total_errors"] == 3
        assert summary["error_type_counts"]["validation_error"] == 2
        assert summary["error_type_counts"]["database_error"] == 1
        assert summary["most_common_error"] == "validation_error"


class TestDecorators:
    """데코레이터 테스트"""

    def test_error_handler_decorator_success(self):
        """에러 핸들러 데코레이터 성공 테스트"""
        @error_handler(error_type=ErrorType.VALIDATION_ERROR)
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"

    def test_error_handler_decorator_failure(self):
        """에러 핸들러 데코레이터 실패 테스트"""
        @error_handler(error_type=ErrorType.VALIDATION_ERROR)
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(StandardError) as exc_info:
            test_func()
        
        assert exc_info.value.error_type == ErrorType.VALIDATION_ERROR

    def test_retry_on_error_decorator_success(self):
        """리트라이 데코레이터 성공 테스트"""
        call_count = 0
        
        @retry_on_error(max_attempts=3, error_types=[ErrorType.NETWORK_ERROR])
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Test connection error")
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 2

    def test_performance_monitor_decorator(self):
        """성능 모니터링 데코레이터 테스트"""
        @performance_monitor(operation_name="test_operation")
        def test_func():
            time.sleep(0.01)  # 10ms 지연
            return "success"
        
        result = test_func()
        assert result == "success"

    def test_safe_execute_success(self):
        """안전한 실행 성공 테스트"""
        def test_func():
            return "success"
        
        result = safe_execute(test_func, default_return="default")
        assert result == "success"

    def test_safe_execute_failure(self):
        """안전한 실행 실패 테스트"""
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(test_func, default_return="default")
        assert result == "default"

    def test_safe_execute_with_error_type(self):
        """안전한 실행 에러 타입 지정 테스트"""
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(
            test_func,
            default_return="default",
            error_type=ErrorType.VALIDATION_ERROR
        )
        assert result == "default"


class TestErrorTypes:
    """에러 타입 테스트"""

    def test_error_type_enum(self):
        """에러 타입 열거형 테스트"""
        assert ErrorType.VALIDATION_ERROR.value == "validation_error"
        assert ErrorType.DATABASE_ERROR.value == "database_error"
        assert ErrorType.LLM_ERROR.value == "llm_error"

    def test_error_severity_enum(self):
        """에러 심각도 열거형 테스트"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestStandardError:
    """표준 에러 테스트"""

    def test_standard_error_creation(self):
        """표준 에러 생성 테스트"""
        error = StandardError(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Test error",
            severity=ErrorSeverity.MEDIUM,
            error_code="TEST_001",
            details={"field": "test"},
            context={"operation": "test"},
            retryable=True
        )
        
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.message == "Test error"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.error_code == "TEST_001"
        assert error.details["field"] == "test"
        assert error.context["operation"] == "test"
        assert error.retryable is True

    def test_standard_error_to_dict(self):
        """표준 에러 딕셔너리 변환 테스트"""
        error = StandardError(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Test error",
            severity=ErrorSeverity.MEDIUM
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "validation_error"
        assert error_dict["message"] == "Test error"
        assert error_dict["severity"] == "medium"
        assert "timestamp" in error_dict

    def test_standard_error_to_json(self):
        """표준 에러 JSON 변환 테스트"""
        error = StandardError(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Test error",
            severity=ErrorSeverity.MEDIUM
        )
        
        error_json = error.to_json()
        assert isinstance(error_json, str)
        assert "validation_error" in error_json
        assert "Test error" in error_json

    def test_standard_error_str(self):
        """표준 에러 문자열 표현 테스트"""
        error = StandardError(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Test error",
            error_code="TEST_001"
        )
        
        error_str = str(error)
        assert "[validation_error] Test error (Code: TEST_001)" in error_str


class TestRetryConfig:
    """리트라이 설정 테스트"""

    def test_retry_config_default(self):
        """리트라이 설정 기본값 테스트"""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_retry_config_custom(self):
        """리트라이 설정 사용자 정의 테스트"""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False
        )
        
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False


class TestGlobalFunctions:
    """전역 함수 테스트"""

    def test_get_error_handler_singleton(self):
        """에러 핸들러 싱글톤 테스트"""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is handler2

    def test_handle_exception_global(self):
        """전역 예외 처리 함수 테스트"""
        try:
            raise ValueError("Test error")
        except Exception as e:
            error = handle_exception(e, context={"test": "context"})
            
            assert error.error_type == ErrorType.VALIDATION_ERROR
            assert "Test error" in error.message

    def test_retry_with_backoff_global(self):
        """전역 리트라이 함수 테스트"""
        call_count = 0
        
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Test connection error")
            return "success"
        
        result = retry_with_backoff(
            test_func,
            error_types=[ErrorType.NETWORK_ERROR]
        )
        
        assert result == "success"
        assert call_count == 2


if __name__ == "__main__":
    pytest.main([__file__])
