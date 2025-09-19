# ADR-004: Performance Optimization Strategy

## Status
Accepted

## Context
The development policy (development-policy.mdc) mandates specific performance targets for the Seoul Commercial Analysis LLM System:

1. **Response Time**: P95 ≤ 3s (with caching)
2. **Throughput**: Handle concurrent requests efficiently
3. **Resource Usage**: Optimize memory and CPU utilization
4. **Scalability**: Support growing data volumes

## Decision
We will implement a comprehensive performance optimization strategy focusing on caching, query optimization, and resource management:

### Performance Optimization Layers

#### 1. Caching Strategy
- **Multi-Level Caching**: Application, database, and LLM response caching
- **Cache Invalidation**: Smart invalidation based on data changes
- **Cache Warming**: Pre-populate frequently accessed data

#### 2. Query Optimization
- **SQL Query Optimization**: Index optimization and query rewriting
- **LLM Query Optimization**: Prompt optimization and response caching
- **RAG Optimization**: Vector search and BM25 optimization

#### 3. Resource Management
- **Memory Optimization**: Efficient data structures and garbage collection
- **CPU Optimization**: Parallel processing and async operations
- **I/O Optimization**: Batch operations and connection pooling

#### 4. Monitoring & Profiling
- **Performance Metrics**: Response time, throughput, resource usage
- **Profiling**: Identify bottlenecks and optimization opportunities
- **Alerting**: Proactive performance issue detection

## Implementation Details

### Caching Strategy

#### Multi-Level Caching
```python
from functools import lru_cache
import redis
import pickle
from typing import Any, Optional, Dict
import hashlib
import time

class CacheManager:
    """Multi-level cache management"""
    
    def __init__(self, redis_url: str = None):
        self.redis_client = redis.from_url(redis_url) if redis_url else None
        self.local_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache (Redis -> Local -> Default)"""
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    self.cache_stats['hits'] += 1
                    return pickle.loads(value)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Try local cache
        if key in self.local_cache:
            self.cache_stats['hits'] += 1
            return self.local_cache[key]
        
        # Cache miss
        self.cache_stats['misses'] += 1
        return default
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache (Redis + Local)"""
        # Set in Redis
        if self.redis_client:
            try:
                serialized = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Set in local cache
        self.local_cache[key] = value
        
        # Evict oldest entries if cache is full
        if len(self.local_cache) > 1000:
            oldest_key = min(self.local_cache.keys())
            del self.local_cache[oldest_key]
            self.cache_stats['evictions'] += 1
    
    def invalidate(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        # Invalidate Redis
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Invalidate local cache
        keys_to_remove = [k for k in self.local_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.local_cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hit_rate': hit_rate,
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'local_cache_size': len(self.local_cache)
        }

# Cache decorators
def cache_result(ttl: int = 3600, key_func: callable = None):
    """Cache function result"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hashlib.md5(str(args).encode()).hexdigest()}"
            
            # Try to get from cache
            cache_manager = CacheManager()
            cached_result = cache_manager.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

def cache_sql_result(ttl: int = 1800):
    """Cache SQL query results"""
    def decorator(func):
        def wrapper(sql_query: str, *args, **kwargs):
            # Generate cache key from SQL query
            cache_key = f"sql:{hashlib.md5(sql_query.encode()).hexdigest()}"
            
            cache_manager = CacheManager()
            cached_result = cache_manager.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Execute SQL and cache result
            result = func(sql_query, *args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
```

#### LLM Response Caching
```python
class LLMResponseCache:
    """Cache LLM responses for similar queries"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.similarity_threshold = 0.85
    
    def get_cached_response(self, query: str, model: str) -> Optional[str]:
        """Get cached response for similar query"""
        # Generate query embedding for similarity search
        query_embedding = self._get_query_embedding(query)
        
        # Search for similar cached queries
        cache_key = f"llm_cache:{model}"
        cached_queries = self.cache_manager.get(cache_key, {})
        
        for cached_query, cached_response in cached_queries.items():
            similarity = self._calculate_similarity(query_embedding, cached_query)
            if similarity >= self.similarity_threshold:
                return cached_response
        
        return None
    
    def cache_response(self, query: str, response: str, model: str):
        """Cache LLM response"""
        cache_key = f"llm_cache:{model}"
        cached_queries = self.cache_manager.get(cache_key, {})
        
        # Store query embedding and response
        query_embedding = self._get_query_embedding(query)
        cached_queries[query_embedding] = response
        
        # Limit cache size
        if len(cached_queries) > 1000:
            # Remove oldest entries
            oldest_keys = list(cached_queries.keys())[:100]
            for key in oldest_keys:
                del cached_queries[key]
        
        self.cache_manager.set(cache_key, cached_queries, ttl=7200)
    
    def _get_query_embedding(self, query: str) -> str:
        """Get query embedding for similarity comparison"""
        # Use sentence transformer for embedding
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding = model.encode(query)
        return embedding.tobytes()
    
    def _calculate_similarity(self, embedding1: bytes, embedding2: bytes) -> float:
        """Calculate cosine similarity between embeddings"""
        import numpy as np
        
        vec1 = np.frombuffer(embedding1, dtype=np.float32)
        vec2 = np.frombuffer(embedding2, dtype=np.float32)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
```

### Query Optimization

#### SQL Query Optimization
```python
class SQLOptimizer:
    """Optimize SQL queries for better performance"""
    
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.query_cache = {}
        self.index_recommendations = {}
    
    def optimize_query(self, sql_query: str) -> str:
        """Optimize SQL query"""
        # Parse and analyze query
        parsed_query = self._parse_query(sql_query)
        
        # Apply optimizations
        optimized_query = self._apply_optimizations(parsed_query)
        
        # Generate index recommendations
        self._generate_index_recommendations(parsed_query)
        
        return optimized_query
    
    def _parse_query(self, sql_query: str) -> dict:
        """Parse SQL query into components"""
        # Simple query parsing (in production, use sqlparse library)
        query_lower = sql_query.lower().strip()
        
        return {
            'original': sql_query,
            'type': 'SELECT' if query_lower.startswith('select') else 'OTHER',
            'tables': self._extract_tables(sql_query),
            'columns': self._extract_columns(sql_query),
            'where_clause': self._extract_where_clause(sql_query),
            'joins': self._extract_joins(sql_query)
        }
    
    def _apply_optimizations(self, parsed_query: dict) -> str:
        """Apply query optimizations"""
        optimized = parsed_query['original']
        
        # Add LIMIT if not present
        if 'limit' not in optimized.lower():
            optimized += ' LIMIT 1000'
        
        # Optimize WHERE clause
        if parsed_query['where_clause']:
            optimized = self._optimize_where_clause(optimized, parsed_query['where_clause'])
        
        # Optimize JOINs
        if parsed_query['joins']:
            optimized = self._optimize_joins(optimized, parsed_query['joins'])
        
        return optimized
    
    def _generate_index_recommendations(self, parsed_query: dict):
        """Generate index recommendations"""
        recommendations = []
        
        # Recommend indexes for WHERE clauses
        if parsed_query['where_clause']:
            for condition in parsed_query['where_clause']:
                if '=' in condition or '>' in condition or '<' in condition:
                    column = condition.split()[0]
                    table = parsed_query['tables'][0] if parsed_query['tables'] else 'unknown'
                    recommendations.append(f"CREATE INDEX idx_{table}_{column} ON {table}({column})")
        
        # Recommend indexes for JOINs
        if parsed_query['joins']:
            for join in parsed_query['joins']:
                if 'on' in join.lower():
                    join_condition = join.split('on')[1].strip()
                    if '=' in join_condition:
                        column = join_condition.split('=')[0].strip()
                        table = join.split()[1] if len(join.split()) > 1 else 'unknown'
                        recommendations.append(f"CREATE INDEX idx_{table}_{column} ON {table}({column})")
        
        self.index_recommendations[parsed_query['original']] = recommendations
    
    def get_index_recommendations(self, sql_query: str) -> list:
        """Get index recommendations for query"""
        return self.index_recommendations.get(sql_query, [])
```

#### LLM Query Optimization
```python
class LLMQueryOptimizer:
    """Optimize LLM queries for better performance"""
    
    def __init__(self):
        self.prompt_cache = {}
        self.response_cache = {}
    
    def optimize_prompt(self, prompt: str, context: str = None) -> str:
        """Optimize prompt for better LLM performance"""
        # Remove unnecessary whitespace
        optimized = ' '.join(prompt.split())
        
        # Add context if provided
        if context:
            optimized = f"Context: {context}\n\nQuery: {optimized}"
        
        # Add performance hints
        optimized += "\n\nPlease provide a concise and accurate response."
        
        return optimized
    
    def batch_queries(self, queries: list, batch_size: int = 5) -> list:
        """Batch multiple queries for efficient processing"""
        batches = []
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            batches.append(batch)
        
        return batches
    
    def preprocess_queries(self, queries: list) -> list:
        """Preprocess queries for better performance"""
        processed = []
        
        for query in queries:
            # Remove duplicates
            if query not in processed:
                # Optimize individual query
                optimized = self.optimize_prompt(query)
                processed.append(optimized)
        
        return processed
```

### Resource Management

#### Memory Optimization
```python
import gc
import psutil
from typing import Dict, Any

class MemoryManager:
    """Manage memory usage and optimization"""
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.memory_usage = {}
        self.gc_threshold = 0.8  # Trigger GC at 80% memory usage
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """Check current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    def optimize_memory(self):
        """Optimize memory usage"""
        memory_usage = self.check_memory_usage()
        
        # Trigger garbage collection if memory usage is high
        if memory_usage['percent'] > self.gc_threshold * 100:
            gc.collect()
            logger.info(f"Garbage collection triggered. Memory usage: {memory_usage['percent']:.1f}%")
        
        # Clear caches if memory is still high
        if memory_usage['percent'] > 90:
            self._clear_caches()
            logger.warning(f"Memory usage high ({memory_usage['percent']:.1f}%), caches cleared")
    
    def _clear_caches(self):
        """Clear application caches"""
        # Clear local caches
        if hasattr(self, 'local_cache'):
            self.local_cache.clear()
        
        # Clear LLM response cache
        if hasattr(self, 'llm_cache'):
            self.llm_cache.clear()
        
        # Force garbage collection
        gc.collect()
    
    def monitor_memory(self, func):
        """Decorator to monitor memory usage of functions"""
        def wrapper(*args, **kwargs):
            start_memory = self.check_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_memory = self.check_memory_usage()
                memory_diff = end_memory['rss_mb'] - start_memory['rss_mb']
                
                if memory_diff > 100:  # More than 100MB increase
                    logger.warning(f"Function {func.__name__} used {memory_diff:.1f}MB of memory")
                
                # Optimize memory if needed
                self.optimize_memory()
        
        return wrapper
```

#### Async Operations
```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import List, Any, Callable

class AsyncProcessor:
    """Handle async operations for better performance"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def process_queries_async(self, queries: List[str], processor_func: Callable) -> List[Any]:
        """Process multiple queries asynchronously"""
        tasks = []
        
        for query in queries:
            task = asyncio.create_task(
                self._run_in_executor(processor_func, query)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        return valid_results
    
    async def _run_in_executor(self, func: Callable, *args) -> Any:
        """Run function in thread executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)
    
    async def batch_process(self, items: List[Any], batch_size: int, processor_func: Callable) -> List[Any]:
        """Process items in batches asynchronously"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await self.process_queries_async(batch, processor_func)
            results.extend(batch_results)
        
        return results
```

### Performance Monitoring

#### Performance Metrics
```python
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from collections import defaultdict, deque

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    timestamp: float
    metadata: Dict[str, Any] = None

class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self, max_metrics: int = 1000):
        self.metrics = defaultdict(lambda: deque(maxlen=max_metrics))
        self.start_times = {}
        self.performance_targets = {
            'response_time_p95': 3.0,  # 3 seconds
            'throughput': 100,  # requests per minute
            'memory_usage': 80,  # 80% max
            'cpu_usage': 80  # 80% max
        }
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str, metadata: Dict[str, Any] = None):
        """End timing an operation and record metric"""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.record_metric('response_time', duration, metadata)
            del self.start_times[operation]
    
    def record_metric(self, name: str, value: float, metadata: Dict[str, Any] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.metrics[name].append(metric)
    
    def get_metric_stats(self, name: str, window_minutes: int = 60) -> Dict[str, float]:
        """Get statistics for a metric"""
        if name not in self.metrics:
            return {}
        
        # Filter metrics by time window
        cutoff_time = time.time() - (window_minutes * 60)
        recent_metrics = [
            m for m in self.metrics[name] 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        values = [m.value for m in recent_metrics]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / len(values),
            'p95': self._calculate_percentile(values, 95),
            'p99': self._calculate_percentile(values, 99)
        }
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def check_performance_targets(self) -> Dict[str, bool]:
        """Check if performance targets are met"""
        results = {}
        
        for target_name, target_value in self.performance_targets.items():
            if target_name == 'response_time_p95':
                stats = self.get_metric_stats('response_time')
                actual_value = stats.get('p95', 0)
                results[target_name] = actual_value <= target_value
            elif target_name == 'throughput':
                stats = self.get_metric_stats('throughput')
                actual_value = stats.get('mean', 0)
                results[target_name] = actual_value >= target_value
            elif target_name in ['memory_usage', 'cpu_usage']:
                # These would be system metrics
                results[target_name] = True  # Placeholder
        
        return results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        report = {
            'timestamp': time.time(),
            'targets_met': self.check_performance_targets(),
            'metrics': {}
        }
        
        for metric_name in self.metrics.keys():
            report['metrics'][metric_name] = self.get_metric_stats(metric_name)
        
        return report

# Performance decorator
def monitor_performance(monitor: PerformanceMonitor, operation_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor.start_timer(operation_name)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.end_timer(operation_name, {
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                })
        
        return wrapper
    return decorator
```

## Performance Testing

### Performance Test Suite
```python
import pytest
import time
import asyncio
from unittest.mock import Mock, patch

class TestPerformance:
    """Performance test suite"""
    
    def test_response_time_target(self):
        """Test that response time meets P95 ≤ 3s target"""
        monitor = PerformanceMonitor()
        
        # Simulate multiple requests
        for i in range(100):
            monitor.start_timer(f'request_{i}')
            time.sleep(0.1)  # Simulate processing time
            monitor.end_timer(f'request_{i}')
        
        stats = monitor.get_metric_stats('response_time')
        assert stats['p95'] <= 3.0, f"P95 response time {stats['p95']:.2f}s exceeds 3s target"
    
    def test_cache_performance(self):
        """Test cache performance and hit rates"""
        cache_manager = CacheManager()
        
        # Test cache hit rate
        for i in range(100):
            cache_manager.set(f'key_{i}', f'value_{i}')
        
        hits = 0
        for i in range(100):
            if cache_manager.get(f'key_{i}') is not None:
                hits += 1
        
        hit_rate = hits / 100
        assert hit_rate >= 0.9, f"Cache hit rate {hit_rate:.2f} is below 90% target"
    
    def test_memory_usage(self):
        """Test memory usage optimization"""
        memory_manager = MemoryManager()
        
        # Simulate memory-intensive operation
        large_data = [i for i in range(1000000)]
        
        start_memory = memory_manager.check_memory_usage()
        
        # Process data
        processed_data = [x * 2 for x in large_data]
        
        # Optimize memory
        memory_manager.optimize_memory()
        
        end_memory = memory_manager.check_memory_usage()
        
        # Memory should be optimized
        assert end_memory['percent'] < 90, "Memory usage should be below 90%"
    
    @pytest.mark.asyncio
    async def test_async_processing(self):
        """Test async processing performance"""
        async_processor = AsyncProcessor()
        
        # Test async query processing
        queries = [f"query_{i}" for i in range(10)]
        
        def mock_processor(query: str) -> str:
            time.sleep(0.1)  # Simulate processing
            return f"result_{query}"
        
        start_time = time.time()
        results = await async_processor.process_queries_async(queries, mock_processor)
        end_time = time.time()
        
        # Should process faster than sequential
        duration = end_time - start_time
        assert duration < 1.0, f"Async processing took {duration:.2f}s, should be < 1s"
        assert len(results) == 10, "Should process all queries"
```

## Consequences

### Positive
- **Improved Performance**: Faster response times and higher throughput
- **Better User Experience**: Reduced waiting times
- **Resource Efficiency**: Optimal memory and CPU usage
- **Scalability**: Support for growing data volumes
- **Cost Optimization**: Reduced infrastructure costs

### Negative
- **Complexity**: More complex caching and optimization logic
- **Memory Overhead**: Caching requires additional memory
- **Cache Invalidation**: Complex cache management
- **Development Overhead**: More time for optimization

### Risks
- **Cache Staleness**: Outdated cached data
- **Memory Leaks**: Improper cache management
- **Performance Regression**: Changes may degrade performance
- **Over-optimization**: Premature optimization

## Success Metrics

### Performance Targets
- **Response Time**: P95 ≤ 3s (with caching)
- **Throughput**: 100+ requests per minute
- **Memory Usage**: <80% of available memory
- **CPU Usage**: <80% of available CPU

### Optimization Metrics
- **Cache Hit Rate**: >90% for frequently accessed data
- **Query Optimization**: 50%+ reduction in query execution time
- **Memory Efficiency**: <10% memory growth over time
- **Async Processing**: 3x+ improvement in batch operations

## Implementation Timeline

### Phase 1: Caching Implementation (Week 1)
- [x] Implement multi-level caching
- [x] Add LLM response caching
- [x] Create cache management system

### Phase 2: Query Optimization (Week 2)
- [x] Implement SQL query optimization
- [x] Add LLM query optimization
- [x] Create index recommendations

### Phase 3: Resource Management (Week 3)
- [ ] Implement memory optimization
- [ ] Add async processing
- [ ] Create resource monitoring

### Phase 4: Performance Monitoring (Week 4)
- [ ] Implement performance metrics
- [ ] Add performance testing
- [ ] Create performance dashboards

## References

- [High Performance Python - Micha Gorelick](https://www.oreilly.com/library/view/high-performance-python/9781449361747/)
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [Redis Caching Best Practices](https://redis.io/docs/manual/patterns/distributed-locks/)
- [SQL Query Optimization](https://use-the-index-luke.com/)
- [Async Programming in Python](https://docs.python.org/3/library/asyncio.html)
