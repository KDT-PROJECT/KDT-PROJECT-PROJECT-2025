# ADR-005: Structured Logging System

## Status
Accepted

## Context
The development policy (development-policy.mdc) mandates a comprehensive logging system for the Seoul Commercial Analysis LLM System. The current system lacks structured logging, making it difficult to:

1. **Debug Issues**: No detailed error tracking and context
2. **Monitor Performance**: No performance metrics and timing information
3. **Audit Operations**: No audit trail for security and compliance
4. **Analyze Usage**: No user behavior and system usage analytics

## Decision
We will implement a comprehensive structured logging system following the development policy requirements:

### Logging Architecture

#### 1. Structured JSON Logging
- **Consistent Format**: All logs in JSON format with standardized fields
- **Context Preservation**: Maintain request context across operations
- **Metadata Enrichment**: Add relevant metadata to all log entries

#### 2. Multi-Level Logging
- **Application Logs**: Business logic and user operations
- **System Logs**: Infrastructure and performance metrics
- **Security Logs**: Security events and audit trails
- **Error Logs**: Detailed error information and stack traces

#### 3. Log Aggregation & Analysis
- **Centralized Logging**: Aggregate logs from all components
- **Real-time Monitoring**: Live log analysis and alerting
- **Historical Analysis**: Long-term log storage and analysis

#### 4. Performance & Security
- **Minimal Overhead**: Efficient logging with minimal performance impact
- **Data Protection**: Secure logging without sensitive information
- **Compliance**: Meet audit and compliance requirements

## Implementation Details

### Structured JSON Logging

#### Log Entry Structure
```python
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
import json
import time
import uuid
from enum import Enum

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Log category enumeration"""
    APPLICATION = "APPLICATION"
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    AUDIT = "AUDIT"

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: float
    level: LogLevel
    category: LogCategory
    message: str
    service: str
    operation: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary"""
        data = asdict(self)
        data['level'] = self.level.value
        data['category'] = self.category.value
        return data
    
    def to_json(self) -> str:
        """Convert log entry to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
```

#### Logger Implementation
```python
import logging
import sys
from typing import Dict, Any, Optional
from contextvars import ContextVar
import threading

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)

class StructuredLogger:
    """Structured JSON logger"""
    
    def __init__(self, name: str, service: str):
        self.name = name
        self.service = service
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create console handler with JSON formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create file handler for detailed logs
        file_handler = logging.FileHandler('logs/application.log')
        file_handler.setLevel(logging.DEBUG)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def _create_log_entry(self, 
                         level: LogLevel, 
                         category: LogCategory, 
                         message: str, 
                         operation: str,
                         metadata: Optional[Dict[str, Any]] = None,
                         error_details: Optional[Dict[str, Any]] = None,
                         performance_metrics: Optional[Dict[str, Any]] = None) -> LogEntry:
        """Create structured log entry"""
        return LogEntry(
            timestamp=time.time(),
            level=level,
            category=category,
            message=message,
            service=self.service,
            operation=operation,
            request_id=request_id_var.get(),
            user_id=user_id_var.get(),
            session_id=session_id_var.get(),
            metadata=metadata,
            error_details=error_details,
            performance_metrics=performance_metrics
        )
    
    def debug(self, message: str, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        log_entry = self._create_log_entry(LogLevel.DEBUG, LogCategory.APPLICATION, message, operation, metadata)
        self.logger.debug(log_entry.to_json())
    
    def info(self, message: str, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Log info message"""
        log_entry = self._create_log_entry(LogLevel.INFO, LogCategory.APPLICATION, message, operation, metadata)
        self.logger.info(log_entry.to_json())
    
    def warning(self, message: str, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        log_entry = self._create_log_entry(LogLevel.WARNING, LogCategory.APPLICATION, message, operation)
        self.logger.warning(log_entry.to_json())
    
    def error(self, message: str, operation: str, error_details: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Log error message"""
        log_entry = self._create_log_entry(LogLevel.ERROR, LogCategory.APPLICATION, message, operation, metadata, error_details)
        self.logger.error(log_entry.to_json())
    
    def critical(self, message: str, operation: str, error_details: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Log critical message"""
        log_entry = self._create_log_entry(LogLevel.CRITICAL, LogCategory.APPLICATION, message, operation, metadata, error_details)
        self.logger.critical(log_entry.to_json())
    
    def security(self, message: str, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Log security event"""
        log_entry = self._create_log_entry(LogLevel.WARNING, LogCategory.SECURITY, message, operation, metadata)
        self.logger.warning(log_entry.to_json())
    
    def performance(self, message: str, operation: str, metrics: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Log performance metrics"""
        log_entry = self._create_log_entry(LogLevel.INFO, LogCategory.PERFORMANCE, message, operation, metadata, performance_metrics=metrics)
        self.logger.info(log_entry.to_json())
    
    def audit(self, message: str, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Log audit event"""
        log_entry = self._create_log_entry(LogLevel.INFO, LogCategory.AUDIT, message, operation, metadata)
        self.logger.info(log_entry.to_json())
```

### Context Management

#### Request Context
```python
from contextlib import contextmanager
from typing import Optional

class RequestContext:
    """Manage request context for logging"""
    
    @staticmethod
    @contextmanager
    def set_context(request_id: Optional[str] = None, 
                   user_id: Optional[str] = None, 
                   session_id: Optional[str] = None):
        """Set request context for logging"""
        # Store previous values
        prev_request_id = request_id_var.get()
        prev_user_id = user_id_var.get()
        prev_session_id = session_id_var.get()
        
        try:
            # Set new context
            if request_id:
                request_id_var.set(request_id)
            if user_id:
                user_id_var.set(user_id)
            if session_id:
                session_id_var.set(session_id)
            
            yield
            
        finally:
            # Restore previous context
            if prev_request_id:
                request_id_var.set(prev_request_id)
            if prev_user_id:
                user_id_var.set(prev_user_id)
            if prev_session_id:
                session_id_var.set(prev_session_id)
    
    @staticmethod
    def get_current_context() -> Dict[str, Optional[str]]:
        """Get current request context"""
        return {
            'request_id': request_id_var.get(),
            'user_id': user_id_var.get(),
            'session_id': session_id_var.get()
        }
```

### Specialized Loggers

#### Application Logger
```python
class ApplicationLogger:
    """Application-specific logger"""
    
    def __init__(self, service: str):
        self.logger = StructuredLogger(f"app.{service}", service)
    
    def log_user_action(self, action: str, details: Dict[str, Any]):
        """Log user action"""
        self.logger.audit(
            f"User action: {action}",
            "user_action",
            metadata=details
        )
    
    def log_sql_query(self, query: str, execution_time: float, result_count: int):
        """Log SQL query execution"""
        self.logger.performance(
            "SQL query executed",
            "sql_execution",
            metrics={
                'execution_time': execution_time,
                'result_count': result_count,
                'query_length': len(query)
            },
            metadata={'query': query[:100]}  # Truncate for security
        )
    
    def log_llm_request(self, model: str, prompt_length: int, response_time: float, token_count: int):
        """Log LLM request"""
        self.logger.performance(
            "LLM request processed",
            "llm_request",
            metrics={
                'model': model,
                'prompt_length': prompt_length,
                'response_time': response_time,
                'token_count': token_count
            }
        )
    
    def log_rag_search(self, query: str, result_count: int, search_time: float):
        """Log RAG search"""
        self.logger.performance(
            "RAG search executed",
            "rag_search",
            metrics={
                'result_count': result_count,
                'search_time': search_time,
                'query_length': len(query)
            },
            metadata={'query': query[:100]}
        )
```

#### Security Logger
```python
class SecurityLogger:
    """Security-specific logger"""
    
    def __init__(self):
        self.logger = StructuredLogger("security", "security")
    
    def log_authentication(self, user_id: str, success: bool, ip_address: str):
        """Log authentication attempt"""
        self.logger.security(
            f"Authentication {'successful' if success else 'failed'}",
            "authentication",
            metadata={
                'user_id': user_id,
                'success': success,
                'ip_address': ip_address
            }
        )
    
    def log_authorization(self, user_id: str, resource: str, action: str, allowed: bool):
        """Log authorization check"""
        self.logger.security(
            f"Authorization {'granted' if allowed else 'denied'}",
            "authorization",
            metadata={
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'allowed': allowed
            }
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event"""
        self.logger.security(
            f"Security event: {event_type}",
            "security_event",
            metadata=details
        )
    
    def log_data_access(self, user_id: str, data_type: str, operation: str, record_count: int):
        """Log data access"""
        self.logger.audit(
            f"Data access: {operation}",
            "data_access",
            metadata={
                'user_id': user_id,
                'data_type': data_type,
                'operation': operation,
                'record_count': record_count
            }
        )
```

#### Performance Logger
```python
class PerformanceLogger:
    """Performance-specific logger"""
    
    def __init__(self):
        self.logger = StructuredLogger("performance", "performance")
    
    def log_operation_timing(self, operation: str, duration: float, metadata: Optional[Dict[str, Any]] = None):
        """Log operation timing"""
        self.logger.performance(
            f"Operation completed: {operation}",
            operation,
            metrics={
                'duration': duration,
                'duration_ms': duration * 1000
            },
            metadata=metadata
        )
    
    def log_memory_usage(self, operation: str, memory_mb: float, peak_memory_mb: float):
        """Log memory usage"""
        self.logger.performance(
            f"Memory usage: {operation}",
            operation,
            metrics={
                'memory_mb': memory_mb,
                'peak_memory_mb': peak_memory_mb
            }
        )
    
    def log_cache_performance(self, cache_type: str, hit_rate: float, total_requests: int):
        """Log cache performance"""
        self.logger.performance(
            f"Cache performance: {cache_type}",
            "cache_performance",
            metrics={
                'hit_rate': hit_rate,
                'total_requests': total_requests,
                'miss_rate': 1 - hit_rate
            }
        )
    
    def log_system_metrics(self, cpu_percent: float, memory_percent: float, disk_percent: float):
        """Log system metrics"""
        self.logger.performance(
            "System metrics",
            "system_metrics",
            metrics={
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent
            }
        )
```

### Log Analysis & Monitoring

#### Log Analyzer
```python
import re
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import json

class LogAnalyzer:
    """Analyze and monitor logs"""
    
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.log_entries = []
    
    def load_logs(self, lines: int = 1000):
        """Load recent log entries"""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                lines_list = f.readlines()
                recent_lines = lines_list[-lines:] if len(lines_list) > lines else lines_list
                
                for line in recent_lines:
                    try:
                        log_entry = json.loads(line.strip())
                        self.log_entries.append(log_entry)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            self.log_entries = []
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns"""
        error_entries = [entry for entry in self.log_entries if entry.get('level') == 'ERROR']
        
        error_patterns = defaultdict(int)
        error_operations = defaultdict(int)
        
        for entry in error_entries:
            message = entry.get('message', '')
            operation = entry.get('operation', '')
            
            # Extract error patterns
            if 'timeout' in message.lower():
                error_patterns['timeout'] += 1
            elif 'connection' in message.lower():
                error_patterns['connection'] += 1
            elif 'validation' in message.lower():
                error_patterns['validation'] += 1
            elif 'permission' in message.lower():
                error_patterns['permission'] += 1
            
            error_operations[operation] += 1
        
        return {
            'total_errors': len(error_entries),
            'error_patterns': dict(error_patterns),
            'error_operations': dict(error_operations)
        }
    
    def analyze_performance_metrics(self) -> Dict[str, Any]:
        """Analyze performance metrics"""
        performance_entries = [entry for entry in self.log_entries if entry.get('category') == 'PERFORMANCE']
        
        operation_times = defaultdict(list)
        cache_hit_rates = defaultdict(list)
        
        for entry in performance_entries:
            operation = entry.get('operation', '')
            metrics = entry.get('performance_metrics', {})
            
            if 'duration' in metrics:
                operation_times[operation].append(metrics['duration'])
            
            if 'hit_rate' in metrics:
                cache_hit_rates[operation].append(metrics['hit_rate'])
        
        # Calculate statistics
        performance_stats = {}
        for operation, times in operation_times.items():
            if times:
                performance_stats[operation] = {
                    'avg_duration': sum(times) / len(times),
                    'max_duration': max(times),
                    'min_duration': min(times),
                    'count': len(times)
                }
        
        cache_stats = {}
        for operation, rates in cache_hit_rates.items():
            if rates:
                cache_stats[operation] = {
                    'avg_hit_rate': sum(rates) / len(rates),
                    'min_hit_rate': min(rates),
                    'max_hit_rate': max(rates)
                }
        
        return {
            'performance_stats': performance_stats,
            'cache_stats': cache_stats
        }
    
    def analyze_security_events(self) -> Dict[str, Any]:
        """Analyze security events"""
        security_entries = [entry for entry in self.log_entries if entry.get('category') == 'SECURITY']
        
        security_events = defaultdict(int)
        failed_authentications = 0
        denied_authorizations = 0
        
        for entry in security_entries:
            message = entry.get('message', '')
            metadata = entry.get('metadata', {})
            
            if 'authentication' in message.lower():
                if not metadata.get('success', True):
                    failed_authentications += 1
            
            if 'authorization' in message.lower():
                if not metadata.get('allowed', True):
                    denied_authorizations += 1
            
            # Count security event types
            if 'prompt injection' in message.lower():
                security_events['prompt_injection'] += 1
            elif 'sql injection' in message.lower():
                security_events['sql_injection'] += 1
            elif 'pii detected' in message.lower():
                security_events['pii_detected'] += 1
        
        return {
            'total_security_events': len(security_entries),
            'failed_authentications': failed_authentications,
            'denied_authorizations': denied_authorizations,
            'security_event_types': dict(security_events)
        }
    
    def generate_log_report(self) -> Dict[str, Any]:
        """Generate comprehensive log report"""
        self.load_logs()
        
        return {
            'timestamp': time.time(),
            'total_entries': len(self.log_entries),
            'error_analysis': self.analyze_error_patterns(),
            'performance_analysis': self.analyze_performance_metrics(),
            'security_analysis': self.analyze_security_events()
        }
```

### Log Configuration

#### Logging Configuration
```python
import logging.config
import os

def setup_logging():
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'format': '%(message)s',
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
            },
            'simple': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'json',
                'filename': 'logs/application.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json',
                'filename': 'logs/error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'security_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'WARNING',
                'formatter': 'json',
                'filename': 'logs/security.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10
            }
        },
        'loggers': {
            'app': {
                'level': 'DEBUG',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'security': {
                'level': 'WARNING',
                'handlers': ['console', 'security_file'],
                'propagate': False
            },
            'performance': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'file', 'error_file']
        }
    }
    
    logging.config.dictConfig(logging_config)
```

## Logging Integration

### Service Integration
```python
# Example integration in services
class DatabaseService:
    def __init__(self):
        self.logger = ApplicationLogger("database")
    
    def execute_query(self, query: str) -> pd.DataFrame:
        start_time = time.time()
        
        try:
            result = self._execute_sql(query)
            execution_time = time.time() - start_time
            
            self.logger.log_sql_query(query, execution_time, len(result))
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(
                f"SQL query failed: {str(e)}",
                "sql_execution",
                error_details={'error': str(e), 'query': query[:100]},
                metadata={'execution_time': execution_time}
            )
            raise

class LLMService:
    def __init__(self):
        self.logger = ApplicationLogger("llm")
    
    def generate_response(self, prompt: str, model: str) -> str:
        start_time = time.time()
        
        try:
            response = self._call_llm(prompt, model)
            response_time = time.time() - start_time
            
            self.logger.log_llm_request(
                model, len(prompt), response_time, len(response.split())
            )
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(
                f"LLM request failed: {str(e)}",
                "llm_request",
                error_details={'error': str(e), 'model': model},
                metadata={'response_time': response_time}
            )
            raise
```

## Consequences

### Positive
- **Better Debugging**: Detailed error tracking and context
- **Performance Monitoring**: Real-time performance metrics
- **Security Auditing**: Complete audit trail for compliance
- **Usage Analytics**: User behavior and system usage insights
- **Operational Visibility**: Clear view of system health

### Negative
- **Storage Overhead**: Log files require disk space
- **Performance Impact**: Logging adds processing overhead
- **Complexity**: More complex logging infrastructure
- **Maintenance**: Log rotation and cleanup required

### Risks
- **Log Volume**: Excessive logging may impact performance
- **Sensitive Data**: Risk of logging sensitive information
- **Storage Issues**: Log files may fill up disk space
- **Privacy Concerns**: User data in logs

## Success Metrics

### Logging Metrics
- **Log Coverage**: 100% of critical operations logged
- **Log Quality**: Structured JSON format for all logs
- **Performance Impact**: <5% overhead from logging
- **Storage Efficiency**: Log rotation and cleanup working

### Monitoring Metrics
- **Error Detection**: 100% of errors logged with context
- **Performance Tracking**: All operations timed and logged
- **Security Events**: All security events logged and monitored
- **Audit Compliance**: Complete audit trail available

## Implementation Timeline

### Phase 1: Basic Logging (Week 1)
- [x] Implement structured JSON logging
- [x] Create specialized loggers
- [x] Set up log configuration

### Phase 2: Context Management (Week 2)
- [x] Implement request context tracking
- [x] Add metadata enrichment
- [x] Create context management utilities

### Phase 3: Log Analysis (Week 3)
- [ ] Implement log analysis tools
- [ ] Add performance monitoring
- [ ] Create security event analysis

### Phase 4: Integration & Monitoring (Week 4)
- [ ] Integrate logging into all services
- [ ] Set up log monitoring and alerting
- [ ] Create log dashboards

## References

- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [Structured Logging with JSON](https://www.elastic.co/guide/en/ecs/current/ecs-log.html)
- [Log Analysis and Monitoring](https://www.elastic.co/guide/en/elasticsearch/reference/current/logs.html)
- [Security Logging Guidelines](https://owasp.org/www-community/Logging_Cheat_Sheet)
- [Performance Monitoring](https://docs.python.org/3/library/profile.html)
