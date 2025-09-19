"""
에러 처리 및 로깅 데코레이터
development-policy.mdc 규칙에 따른 데코레이터 구현
"""

import functools
import logging
import time
from typing import Any, Callable, Optional

from infrastructure.error_handler import ErrorHandler, ErrorType, StandardError, get_error_handler
from infrastructure.logging_service import StructuredLogger


def error_handler(
    error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
    retryable: bool = False,
    log_errors: bool = True,
    context: dict[str, Any] = None
):
    """
    에러 처리를 위한 데코레이터
    
    Args:
        error_type: 기본 에러 타입
        retryable: 리트라이 가능 여부
        log_errors: 에러 로깅 여부
        context: 추가 컨텍스트 정보
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            error_handler = get_error_handler()
            logger = StructuredLogger(f"decorator.{func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                
                if log_errors:
                    logger.info(
                        f"Function {func.__name__} executed successfully",
                        function=func.__name__,
                        context=context or {}
                    )
                
                return result
                
            except Exception as e:
                error = error_handler.handle_exception(
                    e,
                    error_type=error_type,
                    context=context or {},
                    retryable=retryable
                )
                
                if log_errors:
                    logger.error(
                        f"Function {func.__name__} failed",
                        function=func.__name__,
                        error_code=error.error_code,
                        error_type=error.error_type.value,
                        context=context or {}
                    )
                
                raise error
        
        return wrapper
    return decorator


def retry_on_error(
    max_attempts: int = 3,
    error_types: list[ErrorType] = None,
    base_delay: float = 1.0,
    context: dict[str, Any] = None
):
    """
    에러 발생 시 리트라이를 수행하는 데코레이터
    
    Args:
        max_attempts: 최대 시도 횟수
        error_types: 리트라이할 에러 타입 목록
        base_delay: 기본 지연 시간 (초)
        context: 추가 컨텍스트 정보
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            error_handler = get_error_handler()
            logger = StructuredLogger(f"retry.{func.__name__}")
            
            return error_handler.retry_with_backoff(
                func,
                *args,
                retry_config=error_handler.retry_config,
                error_types=error_types or [ErrorType.NETWORK_ERROR, ErrorType.TIMEOUT_ERROR],
                context=context or {},
                **kwargs
            )
        
        return wrapper
    return decorator


def performance_monitor(
    operation_name: str = None,
    log_latency: bool = True,
    log_args: bool = False,
    context: dict[str, Any] = None
):
    """
    성능 모니터링을 위한 데코레이터
    
    Args:
        operation_name: 작업 이름
        log_latency: 지연 시간 로깅 여부
        log_args: 인자 로깅 여부
        context: 추가 컨텍스트 정보
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = StructuredLogger(f"performance.{func.__name__}")
            operation = operation_name or func.__name__
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                latency_ms = (time.time() - start_time) * 1000
                
                if log_latency:
                    logger.log_performance(
                        operation=operation,
                        latency_ms=latency_ms,
                        success=True,
                        context=context or {}
                    )
                
                return result
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                
                if log_latency:
                    logger.log_performance(
                        operation=operation,
                        latency_ms=latency_ms,
                        success=False,
                        context=context or {}
                    )
                
                raise
        
        return wrapper
    return decorator


def validate_input(
    validation_rules: dict[str, Any],
    context: str = "input_validation"
):
    """
    입력 검증을 위한 데코레이터
    
    Args:
        validation_rules: 검증 규칙
        context: 검증 컨텍스트
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            error_handler = get_error_handler()
            logger = StructuredLogger(f"validation.{func.__name__}")
            
            # 첫 번째 인자가 딕셔너리인 경우 검증
            if args and isinstance(args[0], dict):
                validation_error = error_handler.validate_input(
                    args[0], validation_rules, context
                )
                
                if validation_error:
                    logger.error(
                        f"Input validation failed for {func.__name__}",
                        error_code=validation_error.error_code,
                        validation_context=context,
                        function=func.__name__
                    )
                    raise validation_error
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_execution(
    log_level: str = "INFO",
    include_result: bool = False,
    include_args: bool = False,
    context: dict[str, Any] = None
):
    """
    실행 로깅을 위한 데코레이터
    
    Args:
        log_level: 로그 레벨
        include_result: 결과 포함 여부
        include_args: 인자 포함 여부
        context: 추가 컨텍스트 정보
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = StructuredLogger(f"execution.{func.__name__}")
            
            log_data = {
                "function": func.__name__,
                "context": context or {}
            }
            
            if include_args:
                log_data["args"] = str(args)[:200]  # 인자 길이 제한
                log_data["kwargs"] = str(kwargs)[:200]
            
            # 함수 실행 전 로깅
            if log_level.upper() == "DEBUG":
                logger.debug(f"Executing {func.__name__}", **log_data)
            elif log_level.upper() == "INFO":
                logger.info(f"Executing {func.__name__}", **log_data)
            elif log_level.upper() == "WARNING":
                logger.warning(f"Executing {func.__name__}", **log_data)
            
            try:
                result = func(*args, **kwargs)
                
                if include_result:
                    log_data["result"] = str(result)[:200]  # 결과 길이 제한
                
                # 함수 실행 후 로깅
                if log_level.upper() == "DEBUG":
                    logger.debug(f"Completed {func.__name__}", **log_data)
                elif log_level.upper() == "INFO":
                    logger.info(f"Completed {func.__name__}", **log_data)
                
                return result
                
            except Exception as e:
                log_data["error"] = str(e)
                
                if log_level.upper() == "DEBUG":
                    logger.debug(f"Failed {func.__name__}", **log_data)
                elif log_level.upper() == "INFO":
                    logger.info(f"Failed {func.__name__}", **log_data)
                elif log_level.upper() == "WARNING":
                    logger.warning(f"Failed {func.__name__}", **log_data)
                
                raise
        
        return wrapper
    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type = Exception
):
    """
    서킷 브레이커 패턴을 구현하는 데코레이터
    
    Args:
        failure_threshold: 실패 임계값
        recovery_timeout: 복구 타임아웃 (초)
        expected_exception: 예상되는 예외 타입
    """
    def decorator(func: Callable) -> Callable:
        # 서킷 브레이커 상태를 저장하는 클래스 변수
        if not hasattr(func, '_circuit_breaker_state'):
            func._circuit_breaker_state = {
                'failures': 0,
                'last_failure_time': None,
                'state': 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
            }
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            state = func._circuit_breaker_state
            current_time = time.time()
            
            # 서킷이 열려있는 경우
            if state['state'] == 'OPEN':
                if current_time - state['last_failure_time'] < recovery_timeout:
                    raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
                else:
                    # 복구 시도 (HALF_OPEN 상태로 전환)
                    state['state'] = 'HALF_OPEN'
            
            try:
                result = func(*args, **kwargs)
                
                # 성공 시 실패 카운터 리셋
                if state['state'] == 'HALF_OPEN':
                    state['state'] = 'CLOSED'
                    state['failures'] = 0
                
                return result
                
            except expected_exception as e:
                state['failures'] += 1
                state['last_failure_time'] = current_time
                
                # 임계값 도달 시 서킷 열기
                if state['failures'] >= failure_threshold:
                    state['state'] = 'OPEN'
                
                raise e
        
        return wrapper
    return decorator


# 편의 함수들
def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
    context: dict[str, Any] = None,
    **kwargs
) -> Any:
    """
    안전한 함수 실행 (예외 발생 시 기본값 반환)
    
    Args:
        func: 실행할 함수
        *args: 함수 인자
        default_return: 예외 발생 시 반환할 기본값
        error_type: 에러 타입
        context: 컨텍스트 정보
        **kwargs: 함수 키워드 인자
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler = get_error_handler()
        error = error_handler.handle_exception(
            e, error_type=error_type, context=context or {}
        )
        
        logger = StructuredLogger("safe_execute")
        logger.warning(
            f"Safe execution failed, returning default value",
            function=func.__name__,
            error_code=error.error_code,
            context=context or {}
        )
        
        return default_return


def batch_process(
    items: list[Any],
    process_func: Callable,
    batch_size: int = 10,
    error_handling: str = "continue",  # "continue", "stop", "collect"
    context: dict[str, Any] = None
) -> list[Any]:
    """
    배치 처리를 위한 함수
    
    Args:
        items: 처리할 아이템 목록
        process_func: 처리 함수
        batch_size: 배치 크기
        error_handling: 에러 처리 방식
        context: 컨텍스트 정보
    """
    results = []
    errors = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        for item in batch:
            try:
                result = process_func(item)
                results.append(result)
            except Exception as e:
                error_handler = get_error_handler()
                error = error_handler.handle_exception(
                    e, context=context or {}
                )
                
                if error_handling == "continue":
                    continue
                elif error_handling == "stop":
                    raise error
                elif error_handling == "collect":
                    errors.append(error)
                    results.append(None)
    
    if errors and error_handling == "collect":
        logger = StructuredLogger("batch_process")
        logger.warning(
            f"Batch processing completed with {len(errors)} errors",
            total_items=len(items),
            successful_items=len([r for r in results if r is not None]),
            error_count=len(errors),
            context=context or {}
        )
    
    return results
