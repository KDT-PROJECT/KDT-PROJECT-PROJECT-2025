# ADR-006: Comprehensive Error Handling Strategy

## Status
Accepted

## Context
The development policy (development-policy.mdc) mandates comprehensive error handling for the Seoul Commercial Analysis LLM System. The current system lacks robust error handling, making it difficult to:

1. **Handle Failures Gracefully**: No proper error recovery and fallback mechanisms
2. **Provide User Feedback**: No clear error messages and user guidance
3. **Debug Issues**: No detailed error context and debugging information
4. **Maintain System Stability**: No error isolation and system protection

## Decision
We will implement a comprehensive error handling strategy following the development policy requirements:

### Error Handling Architecture

#### 1. Error Classification
- **System Errors**: Infrastructure and system-level failures
- **Business Logic Errors**: Application logic and validation failures
- **User Input Errors**: Invalid user input and request errors
- **External Service Errors**: Third-party service and API failures

#### 2. Error Response Strategy
- **Graceful Degradation**: Fallback mechanisms for non-critical failures
- **User-Friendly Messages**: Clear, actionable error messages
- **Error Recovery**: Automatic retry and recovery mechanisms
- **Error Isolation**: Prevent errors from cascading

#### 3. Error Monitoring & Alerting
- **Real-time Monitoring**: Immediate error detection and alerting
- **Error Analytics**: Error pattern analysis and trend monitoring
- **Performance Impact**: Monitor error impact on system performance
- **User Impact**: Track error impact on user experience

#### 4. Error Documentation & Testing
- **Error Scenarios**: Document all possible error scenarios
- **Error Testing**: Comprehensive error scenario testing
- **Error Recovery Testing**: Test error recovery mechanisms
- **Error Performance Testing**: Test error handling performance

## Implementation Details

### Error Classification System

#### Error Types
```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import traceback
import time

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ErrorCategory(Enum):
    """Error categories"""
    SYSTEM = "SYSTEM"
    BUSINESS_LOGIC = "BUSINESS_LOGIC"
    USER_INPUT = "USER_INPUT"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"

class ErrorCode(Enum):
    """Standardized error codes"""
    # System Errors
    DATABASE_CONNECTION_FAILED = "DB_001"
    DATABASE_QUERY_FAILED = "DB_002"
    DATABASE_TIMEOUT = "DB_003"
    
    # Business Logic Errors
    INVALID_QUERY_FORMAT = "BL_001"
    QUERY_EXECUTION_FAILED = "BL_002"
    DATA_VALIDATION_FAILED = "BL_003"
    
    # User Input Errors
    INVALID_INPUT_FORMAT = "UI_001"
    MISSING_REQUIRED_FIELD = "UI_002"
    INPUT_TOO_LONG = "UI_003"
    
    # External Service Errors
    LLM_SERVICE_UNAVAILABLE = "ES_001"
    LLM_RESPONSE_INVALID = "ES_002"
    LLM_TIMEOUT = "ES_003"
    
    # Security Errors
    AUTHENTICATION_FAILED = "SEC_001"
    AUTHORIZATION_DENIED = "SEC_002"
    INVALID_TOKEN = "SEC_003"
    
    # Performance Errors
    RESPONSE_TIMEOUT = "PERF_001"
    MEMORY_LIMIT_EXCEEDED = "PERF_002"
    CPU_LIMIT_EXCEEDED = "PERF_003"

@dataclass
class ErrorDetails:
    """Detailed error information"""
    error_code: ErrorCode
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    technical_details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: float = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error details to dictionary"""
        return {
            'error_code': self.error_code.value,
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'user_message': self.user_message,
            'technical_details': self.technical_details,
            'stack_trace': self.stack_trace,
            'context': self.context,
            'timestamp': self.timestamp,
            'request_id': self.request_id,
            'user_id': self.user_id
        }
```

#### Custom Exception Classes
```python
class BaseSystemError(Exception):
    """Base class for all system errors"""
    
    def __init__(self, error_details: ErrorDetails):
        self.error_details = error_details
        super().__init__(error_details.message)

class DatabaseError(BaseSystemError):
    """Database-related errors"""
    pass

class BusinessLogicError(BaseSystemError):
    """Business logic errors"""
    pass

class UserInputError(BaseSystemError):
    """User input validation errors"""
    pass

class ExternalServiceError(BaseSystemError):
    """External service errors"""
    pass

class SecurityError(BaseSystemError):
    """Security-related errors"""
    pass

class PerformanceError(BaseSystemError):
    """Performance-related errors"""
    pass

# Specific error classes
class DatabaseConnectionError(DatabaseError):
    """Database connection failed"""
    pass

class DatabaseQueryError(DatabaseError):
    """Database query execution failed"""
    pass

class DatabaseTimeoutError(DatabaseError):
    """Database operation timed out"""
    pass

class InvalidQueryFormatError(BusinessLogicError):
    """Invalid query format"""
    pass

class QueryExecutionError(BusinessLogicError):
    """Query execution failed"""
    pass

class DataValidationError(BusinessLogicError):
    """Data validation failed"""
    pass

class InvalidInputFormatError(UserInputError):
    """Invalid input format"""
    pass

class MissingRequiredFieldError(UserInputError):
    """Missing required field"""
    pass

class InputTooLongError(UserInputError):
    """Input too long"""
    pass

class LLMServiceUnavailableError(ExternalServiceError):
    """LLM service unavailable"""
    pass

class LLMResponseInvalidError(ExternalServiceError):
    """LLM response invalid"""
    pass

class LLMTimeoutError(ExternalServiceError):
    """LLM request timed out"""
    pass

class AuthenticationFailedError(SecurityError):
    """Authentication failed"""
    pass

class AuthorizationDeniedError(SecurityError):
    """Authorization denied"""
    pass

class InvalidTokenError(SecurityError):
    """Invalid token"""
    pass

class ResponseTimeoutError(PerformanceError):
    """Response timeout"""
    pass

class MemoryLimitExceededError(PerformanceError):
    """Memory limit exceeded"""
    pass

class CPULimitExceededError(PerformanceError):
    """CPU limit exceeded"""
    pass
```

### Error Handler Implementation

#### Main Error Handler
```python
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps

class ErrorHandler:
    """Main error handler for the system"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.error_handlers = {}
        self.recovery_strategies = {}
        self.fallback_handlers = {}
    
    def register_error_handler(self, error_type: type, handler: Callable):
        """Register error handler for specific error type"""
        self.error_handlers[error_type] = handler
    
    def register_recovery_strategy(self, error_type: type, strategy: Callable):
        """Register recovery strategy for specific error type"""
        self.recovery_strategies[error_type] = strategy
    
    def register_fallback_handler(self, error_type: type, handler: Callable):
        """Register fallback handler for specific error type"""
        self.fallback_handlers[error_type] = handler
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle error and return appropriate response"""
        try:
            # Log error
            self._log_error(error, context)
            
            # Get error details
            error_details = self._extract_error_details(error, context)
            
            # Try recovery strategy
            if type(error) in self.recovery_strategies:
                recovery_result = self._try_recovery(error, context)
                if recovery_result['success']:
                    return recovery_result
            
            # Use specific error handler
            if type(error) in self.error_handlers:
                return self.error_handlers[type(error)](error, context)
            
            # Use fallback handler
            if type(error) in self.fallback_handlers:
                return self.fallback_handlers[type(error)](error, context)
            
            # Default error handling
            return self._default_error_response(error_details)
            
        except Exception as handler_error:
            # Error in error handling - critical situation
            self.logger.critical(f"Error handler failed: {handler_error}")
            return self._critical_error_response()
    
    def _log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log error with context"""
        error_details = self._extract_error_details(error, context)
        
        log_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_code': error_details.error_code.value,
            'severity': error_details.severity.value,
            'context': context or {},
            'timestamp': error_details.timestamp
        }
        
        if error_details.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical error: {log_data}")
        elif error_details.severity == ErrorSeverity.HIGH:
            self.logger.error(f"High severity error: {log_data}")
        elif error_details.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Medium severity error: {log_data}")
        else:
            self.logger.info(f"Low severity error: {log_data}")
    
    def _extract_error_details(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorDetails:
        """Extract error details from exception"""
        if isinstance(error, BaseSystemError):
            return error.error_details
        
        # Extract details from standard exceptions
        error_code = self._map_exception_to_error_code(error)
        category = self._map_exception_to_category(error)
        severity = self._map_exception_to_severity(error)
        
        return ErrorDetails(
            error_code=error_code,
            category=category,
            severity=severity,
            message=str(error),
            user_message=self._get_user_friendly_message(error_code),
            technical_details={'exception_type': type(error).__name__},
            stack_trace=traceback.format_exc(),
            context=context
        )
    
    def _map_exception_to_error_code(self, error: Exception) -> ErrorCode:
        """Map exception to error code"""
        error_mapping = {
            ConnectionError: ErrorCode.DATABASE_CONNECTION_FAILED,
            TimeoutError: ErrorCode.DATABASE_TIMEOUT,
            ValueError: ErrorCode.INVALID_INPUT_FORMAT,
            KeyError: ErrorCode.MISSING_REQUIRED_FIELD,
            TypeError: ErrorCode.INVALID_INPUT_FORMAT,
            AttributeError: ErrorCode.INVALID_INPUT_FORMAT,
            IndexError: ErrorCode.INVALID_INPUT_FORMAT,
            FileNotFoundError: ErrorCode.SYSTEM_ERROR,
            PermissionError: ErrorCode.AUTHORIZATION_DENIED,
            MemoryError: ErrorCode.MEMORY_LIMIT_EXCEEDED
        }
        
        return error_mapping.get(type(error), ErrorCode.SYSTEM_ERROR)
    
    def _map_exception_to_category(self, error: Exception) -> ErrorCategory:
        """Map exception to category"""
        category_mapping = {
            ConnectionError: ErrorCategory.SYSTEM,
            TimeoutError: ErrorCategory.PERFORMANCE,
            ValueError: ErrorCategory.USER_INPUT,
            KeyError: ErrorCategory.USER_INPUT,
            TypeError: ErrorCategory.USER_INPUT,
            AttributeError: ErrorCategory.USER_INPUT,
            IndexError: ErrorCategory.USER_INPUT,
            FileNotFoundError: ErrorCategory.SYSTEM,
            PermissionError: ErrorCategory.SECURITY,
            MemoryError: ErrorCategory.PERFORMANCE
        }
        
        return category_mapping.get(type(error), ErrorCategory.SYSTEM)
    
    def _map_exception_to_severity(self, error: Exception) -> ErrorSeverity:
        """Map exception to severity"""
        severity_mapping = {
            ConnectionError: ErrorSeverity.HIGH,
            TimeoutError: ErrorSeverity.MEDIUM,
            ValueError: ErrorSeverity.LOW,
            KeyError: ErrorSeverity.LOW,
            TypeError: ErrorSeverity.LOW,
            AttributeError: ErrorSeverity.LOW,
            IndexError: ErrorSeverity.LOW,
            FileNotFoundError: ErrorSeverity.HIGH,
            PermissionError: ErrorSeverity.HIGH,
            MemoryError: ErrorSeverity.CRITICAL
        }
        
        return severity_mapping.get(type(error), ErrorSeverity.MEDIUM)
    
    def _get_user_friendly_message(self, error_code: ErrorCode) -> str:
        """Get user-friendly error message"""
        user_messages = {
            ErrorCode.DATABASE_CONNECTION_FAILED: "데이터베이스 연결에 실패했습니다. 잠시 후 다시 시도해주세요.",
            ErrorCode.DATABASE_QUERY_FAILED: "데이터베이스 쿼리 실행에 실패했습니다. 입력을 확인해주세요.",
            ErrorCode.DATABASE_TIMEOUT: "데이터베이스 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.",
            ErrorCode.INVALID_QUERY_FORMAT: "쿼리 형식이 올바르지 않습니다. 다시 입력해주세요.",
            ErrorCode.QUERY_EXECUTION_FAILED: "쿼리 실행에 실패했습니다. 입력을 확인해주세요.",
            ErrorCode.DATA_VALIDATION_FAILED: "데이터 검증에 실패했습니다. 입력을 확인해주세요.",
            ErrorCode.INVALID_INPUT_FORMAT: "입력 형식이 올바르지 않습니다. 다시 입력해주세요.",
            ErrorCode.MISSING_REQUIRED_FIELD: "필수 필드가 누락되었습니다. 모든 필드를 입력해주세요.",
            ErrorCode.INPUT_TOO_LONG: "입력이 너무 깁니다. 더 짧게 입력해주세요.",
            ErrorCode.LLM_SERVICE_UNAVAILABLE: "AI 서비스가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.",
            ErrorCode.LLM_RESPONSE_INVALID: "AI 응답을 처리할 수 없습니다. 다시 시도해주세요.",
            ErrorCode.LLM_TIMEOUT: "AI 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.",
            ErrorCode.AUTHENTICATION_FAILED: "인증에 실패했습니다. 로그인 정보를 확인해주세요.",
            ErrorCode.AUTHORIZATION_DENIED: "접근 권한이 없습니다. 관리자에게 문의해주세요.",
            ErrorCode.INVALID_TOKEN: "유효하지 않은 토큰입니다. 다시 로그인해주세요.",
            ErrorCode.RESPONSE_TIMEOUT: "응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.",
            ErrorCode.MEMORY_LIMIT_EXCEEDED: "메모리 사용량이 초과되었습니다. 더 간단한 요청을 시도해주세요.",
            ErrorCode.CPU_LIMIT_EXCEEDED: "시스템 리소스가 부족합니다. 잠시 후 다시 시도해주세요."
        }
        
        return user_messages.get(error_code, "알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    
    def _try_recovery(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Try to recover from error"""
        try:
            recovery_strategy = self.recovery_strategies[type(error)]
            result = recovery_strategy(error, context)
            return {'success': True, 'result': result}
        except Exception as recovery_error:
            self.logger.warning(f"Recovery strategy failed: {recovery_error}")
            return {'success': False, 'error': recovery_error}
    
    def _default_error_response(self, error_details: ErrorDetails) -> Dict[str, Any]:
        """Default error response"""
        return {
            'success': False,
            'error': {
                'code': error_details.error_code.value,
                'message': error_details.user_message,
                'timestamp': error_details.timestamp,
                'request_id': error_details.request_id
            }
        }
    
    def _critical_error_response(self) -> Dict[str, Any]:
        """Critical error response"""
        return {
            'success': False,
            'error': {
                'code': 'CRITICAL_ERROR',
                'message': '시스템에 심각한 오류가 발생했습니다. 관리자에게 문의해주세요.',
                'timestamp': time.time()
            }
        }
```

### Error Recovery Strategies

#### Database Error Recovery
```python
class DatabaseErrorRecovery:
    """Database error recovery strategies"""
    
    def __init__(self, db_service):
        self.db_service = db_service
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    def recover_connection_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
        """Recover from database connection error"""
        for attempt in range(self.max_retries):
            try:
                # Try to reconnect
                self.db_service.reconnect()
                
                # Retry the original operation
                if context and 'original_operation' in context:
                    return context['original_operation']()
                
                return True
                
            except Exception as retry_error:
                if attempt == self.max_retries - 1:
                    raise retry_error
                
                time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        return False
    
    def recover_query_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
        """Recover from database query error"""
        if context and 'query' in context:
            query = context['query']
            
            # Try to simplify the query
            simplified_query = self._simplify_query(query)
            
            try:
                return self.db_service.execute_query(simplified_query)
            except Exception:
                # If simplification fails, return empty result
                return pd.DataFrame()
        
        return None
    
    def _simplify_query(self, query: str) -> str:
        """Simplify complex query"""
        # Remove complex joins and subqueries
        simplified = query
        
        # Remove ORDER BY clauses
        simplified = re.sub(r'ORDER\s+BY\s+[^;]+', '', simplified, flags=re.IGNORECASE)
        
        # Remove LIMIT clauses
        simplified = re.sub(r'LIMIT\s+\d+', '', simplified, flags=re.IGNORECASE)
        
        # Add basic LIMIT
        if 'LIMIT' not in simplified.upper():
            simplified += ' LIMIT 100'
        
        return simplified
```

#### LLM Error Recovery
```python
class LLMErrorRecovery:
    """LLM error recovery strategies"""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.max_retries = 2
        self.retry_delay = 2  # seconds
    
    def recover_service_unavailable(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
        """Recover from LLM service unavailable error"""
        for attempt in range(self.max_retries):
            try:
                # Try to reconnect to LLM service
                self.llm_service.reconnect()
                
                # Retry the original operation
                if context and 'original_operation' in context:
                    return context['original_operation']()
                
                return True
                
            except Exception as retry_error:
                if attempt == self.max_retries - 1:
                    raise retry_error
                
                time.sleep(self.retry_delay * (2 ** attempt))
        
        return False
    
    def recover_timeout_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
        """Recover from LLM timeout error"""
        if context and 'prompt' in context:
            prompt = context['prompt']
            
            # Try with a shorter prompt
            shortened_prompt = self._shorten_prompt(prompt)
            
            try:
                return self.llm_service.generate_response(shortened_prompt)
            except Exception:
                # If shortening fails, return a generic response
                return "죄송합니다. 현재 AI 서비스에 문제가 있어 정확한 응답을 제공할 수 없습니다."
        
        return None
    
    def _shorten_prompt(self, prompt: str) -> str:
        """Shorten prompt to reduce processing time"""
        # Keep only the essential parts
        lines = prompt.split('\n')
        essential_lines = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['query', 'question', 'analyze', 'find']):
                essential_lines.append(line)
        
        if essential_lines:
            return '\n'.join(essential_lines[:3])  # Keep first 3 essential lines
        
        return prompt[:500]  # Fallback to first 500 characters
```

### Error Handling Decorators

#### Error Handling Decorator
```python
def handle_errors(error_handler: ErrorHandler, context: Optional[Dict[str, Any]] = None):
    """Decorator to handle errors in functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as error:
                # Add function context
                error_context = context or {}
                error_context.update({
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                })
                
                # Handle error
                return error_handler.handle_error(error, error_context)
        
        return wrapper
    return decorator

def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """Decorator to retry function on error"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    last_error = error
                    
                    if attempt == max_retries - 1:
                        raise error
                    
                    time.sleep(delay * (backoff_factor ** attempt))
            
            raise last_error
        
        return wrapper
    return decorator

def fallback_on_error(fallback_func: Callable):
    """Decorator to use fallback function on error"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as error:
                try:
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    raise error  # Raise original error if fallback fails
        
        return wrapper
    return decorator
```

### Error Monitoring & Analytics

#### Error Monitor
```python
class ErrorMonitor:
    """Monitor and analyze errors"""
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.error_timestamps = defaultdict(list)
        self.error_contexts = defaultdict(list)
        self.performance_impact = defaultdict(list)
    
    def record_error(self, error: Exception, context: Optional[Dict[str, Any]] = None, performance_impact: float = 0.0):
        """Record error occurrence"""
        error_type = type(error).__name__
        timestamp = time.time()
        
        self.error_counts[error_type] += 1
        self.error_timestamps[error_type].append(timestamp)
        
        if context:
            self.error_contexts[error_type].append(context)
        
        if performance_impact > 0:
            self.performance_impact[error_type].append(performance_impact)
    
    def get_error_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for time window"""
        cutoff_time = time.time() - (time_window_hours * 3600)
        
        stats = {}
        for error_type in self.error_counts:
            recent_timestamps = [ts for ts in self.error_timestamps[error_type] if ts >= cutoff_time]
            
            stats[error_type] = {
                'count': len(recent_timestamps),
                'rate_per_hour': len(recent_timestamps) / time_window_hours,
                'last_occurrence': max(recent_timestamps) if recent_timestamps else None,
                'avg_performance_impact': self._calculate_avg_performance_impact(error_type)
            }
        
        return stats
    
    def _calculate_avg_performance_impact(self, error_type: str) -> float:
        """Calculate average performance impact for error type"""
        impacts = self.performance_impact[error_type]
        return sum(impacts) / len(impacts) if impacts else 0.0
    
    def detect_error_patterns(self) -> List[Dict[str, Any]]:
        """Detect error patterns and trends"""
        patterns = []
        
        for error_type in self.error_counts:
            timestamps = self.error_timestamps[error_type]
            
            if len(timestamps) >= 5:  # Need at least 5 occurrences
                # Check for increasing trend
                recent_count = len([ts for ts in timestamps if ts >= time.time() - 3600])  # Last hour
                older_count = len([ts for ts in timestamps if time.time() - 7200 <= ts < time.time() - 3600])  # Hour before
                
                if recent_count > older_count * 1.5:  # 50% increase
                    patterns.append({
                        'type': 'increasing_trend',
                        'error_type': error_type,
                        'recent_count': recent_count,
                        'older_count': older_count,
                        'increase_percentage': (recent_count - older_count) / older_count * 100
                    })
        
        return patterns
    
    def get_error_recommendations(self) -> List[str]:
        """Get recommendations based on error analysis"""
        recommendations = []
        stats = self.get_error_statistics()
        
        for error_type, stat in stats.items():
            if stat['rate_per_hour'] > 10:  # High error rate
                recommendations.append(f"High error rate for {error_type}: {stat['rate_per_hour']:.1f} errors/hour")
            
            if stat['avg_performance_impact'] > 1.0:  # High performance impact
                recommendations.append(f"High performance impact for {error_type}: {stat['avg_performance_impact']:.2f}s average")
        
        return recommendations
```

## Error Testing

### Error Test Suite
```python
import pytest
from unittest.mock import Mock, patch

class TestErrorHandling:
    """Test error handling functionality"""
    
    def test_database_connection_error_recovery(self):
        """Test database connection error recovery"""
        db_service = Mock()
        db_service.reconnect.side_effect = [Exception(), Exception(), None]
        
        recovery = DatabaseErrorRecovery(db_service)
        
        with pytest.raises(Exception):
            recovery.recover_connection_error(Exception())
        
        # Should succeed on third attempt
        db_service.reconnect.side_effect = [Exception(), Exception(), None]
        result = recovery.recover_connection_error(Exception())
        assert result is True
    
    def test_llm_timeout_error_recovery(self):
        """Test LLM timeout error recovery"""
        llm_service = Mock()
        llm_service.generate_response.return_value = "Shortened response"
        
        recovery = LLMErrorRecovery(llm_service)
        
        context = {'prompt': 'This is a very long prompt that might cause timeout issues'}
        result = recovery.recover_timeout_error(Exception(), context)
        
        assert result == "Shortened response"
        llm_service.generate_response.assert_called_once()
    
    def test_error_classification(self):
        """Test error classification"""
        error_handler = ErrorHandler(Mock())
        
        # Test database error
        db_error = ConnectionError("Connection failed")
        error_details = error_handler._extract_error_details(db_error)
        
        assert error_details.error_code == ErrorCode.DATABASE_CONNECTION_FAILED
        assert error_details.category == ErrorCategory.SYSTEM
        assert error_details.severity == ErrorSeverity.HIGH
    
    def test_user_friendly_messages(self):
        """Test user-friendly error messages"""
        error_handler = ErrorHandler(Mock())
        
        message = error_handler._get_user_friendly_message(ErrorCode.DATABASE_CONNECTION_FAILED)
        assert "데이터베이스 연결에 실패했습니다" in message
        
        message = error_handler._get_user_friendly_message(ErrorCode.INVALID_INPUT_FORMAT)
        assert "입력 형식이 올바르지 않습니다" in message
    
    def test_error_monitoring(self):
        """Test error monitoring and analytics"""
        monitor = ErrorMonitor()
        
        # Record some errors
        for i in range(5):
            monitor.record_error(ConnectionError("Connection failed"))
        
        for i in range(3):
            monitor.record_error(ValueError("Invalid input"))
        
        stats = monitor.get_error_statistics()
        
        assert 'ConnectionError' in stats
        assert stats['ConnectionError']['count'] == 5
        assert 'ValueError' in stats
        assert stats['ValueError']['count'] == 3
    
    def test_error_handling_decorator(self):
        """Test error handling decorator"""
        error_handler = ErrorHandler(Mock())
        
        @handle_errors(error_handler)
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error']['code'] == ErrorCode.INVALID_INPUT_FORMAT.value
    
    def test_retry_decorator(self):
        """Test retry decorator"""
        call_count = 0
        
        @retry_on_error(max_retries=3, delay=0.1)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "Success"
        
        result = flaky_function()
        
        assert result == "Success"
        assert call_count == 3
    
    def test_fallback_decorator(self):
        """Test fallback decorator"""
        def fallback_func():
            return "Fallback result"
        
        @fallback_on_error(fallback_func)
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        
        assert result == "Fallback result"
```

## Consequences

### Positive
- **Improved Reliability**: Better error handling and recovery
- **Better User Experience**: Clear error messages and guidance
- **Easier Debugging**: Detailed error context and logging
- **System Stability**: Error isolation and graceful degradation
- **Operational Visibility**: Error monitoring and analytics

### Negative
- **Complexity**: More complex error handling logic
- **Performance Overhead**: Error handling adds processing time
- **Maintenance**: More error handling code to maintain
- **Testing Overhead**: More error scenarios to test

### Risks
- **Error Masking**: Recovery strategies may hide real issues
- **Infinite Loops**: Retry mechanisms may cause infinite loops
- **Resource Exhaustion**: Recovery attempts may consume resources
- **False Positives**: Error detection may trigger false alarms

## Success Metrics

### Error Handling Metrics
- **Error Recovery Rate**: >80% of recoverable errors handled
- **User Error Clarity**: 100% of errors have user-friendly messages
- **Error Response Time**: <1s for error handling
- **Error Isolation**: 0% error cascading

### System Reliability Metrics
- **System Uptime**: >99.5% availability
- **Error Rate**: <1% of requests result in errors
- **Recovery Time**: <30s for automatic recovery
- **User Impact**: <5% of users affected by errors

## Implementation Timeline

### Phase 1: Basic Error Handling (Week 1)
- [x] Implement error classification system
- [x] Create custom exception classes
- [x] Set up basic error handler

### Phase 2: Error Recovery (Week 2)
- [x] Implement recovery strategies
- [x] Add retry mechanisms
- [x] Create fallback handlers

### Phase 3: Error Monitoring (Week 3)
- [ ] Implement error monitoring
- [ ] Add error analytics
- [ ] Create error dashboards

### Phase 4: Testing & Integration (Week 4)
- [ ] Implement error testing
- [ ] Integrate error handling into all services
- [ ] Create error documentation

## References

- [Python Exception Handling](https://docs.python.org/3/tutorial/errors.html)
- [Error Handling Best Practices](https://docs.python.org/3/howto/errors.html)
- [Graceful Degradation](https://en.wikipedia.org/wiki/Graceful_degradation)
- [Error Recovery Strategies](https://en.wikipedia.org/wiki/Error_recovery)
- [System Reliability Engineering](https://sre.google/sre-book/table-of-contents/)
