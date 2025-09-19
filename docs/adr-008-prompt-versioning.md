# ADR-008: Prompt Versioning and Management Strategy

## Status
Accepted

## Context
The development policy (development-policy.mdc) mandates prompt versioning for the Seoul Commercial Analysis LLM System. The current system lacks proper prompt management, making it difficult to:

1. **Track Prompt Changes**: No version control for prompt modifications
2. **A/B Testing**: No ability to test different prompt versions
3. **Rollback Capability**: No way to revert to previous prompt versions
4. **Performance Monitoring**: No tracking of prompt performance over time

## Decision
We will implement a comprehensive prompt versioning and management strategy following the development policy requirements:

### Prompt Versioning Architecture

#### 1. Version Control System
- **Semantic Versioning**: Use semantic versioning for prompt versions
- **Change Tracking**: Track all changes to prompts with timestamps
- **Rollback Capability**: Ability to revert to previous versions
- **Branch Management**: Support for prompt branches and experiments

#### 2. Prompt Management
- **Centralized Storage**: Store all prompts in a centralized repository
- **Metadata Tracking**: Track prompt metadata (author, date, performance)
- **Validation**: Validate prompt syntax and structure
- **Testing**: Automated testing of prompt changes

#### 3. Performance Monitoring
- **Version Performance**: Track performance metrics for each version
- **A/B Testing**: Compare performance between versions
- **Analytics**: Analyze prompt effectiveness over time
- **Reporting**: Generate performance reports for prompt versions

#### 4. Deployment & Rollout
- **Gradual Rollout**: Deploy new prompt versions gradually
- **Canary Testing**: Test new versions with limited users
- **Production Deployment**: Deploy to production with monitoring
- **Emergency Rollback**: Quick rollback capability for issues

## Implementation Details

### Prompt Versioning System

#### Version Management
```python
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import json
import time
import hashlib
from pathlib import Path

class PromptType(Enum):
    """Prompt type enumeration"""
    TEXT_TO_SQL = "text_to_sql"
    REPORT_GENERATION = "report_generation"
    RAG_SEARCH = "rag_search"
    DATA_VALIDATION = "data_validation"
    ERROR_HANDLING = "error_handling"

class PromptStatus(Enum):
    """Prompt status enumeration"""
    DRAFT = "draft"
    TESTING = "testing"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

@dataclass
class PromptVersion:
    """Prompt version data structure"""
    id: str
    prompt_type: PromptType
    version: str
    content: str
    status: PromptStatus
    author: str
    created_at: float
    updated_at: float
    description: str
    change_log: List[str]
    metadata: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    dependencies: List[str]
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['prompt_type'] = self.prompt_type.value
        data['status'] = self.status.value
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptVersion':
        """Create from dictionary"""
        data['prompt_type'] = PromptType(data['prompt_type'])
        data['status'] = PromptStatus(data['status'])
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PromptVersion':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_hash(self) -> str:
        """Get content hash for change detection"""
        return hashlib.md5(self.content.encode()).hexdigest()
    
    def is_compatible_with(self, other: 'PromptVersion') -> bool:
        """Check if compatible with another version"""
        return (
            self.prompt_type == other.prompt_type and
            self.dependencies == other.dependencies
        )
```

#### Prompt Repository
```python
class PromptRepository:
    """Prompt repository for version management"""
    
    def __init__(self, base_path: str = "prompts"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.versions: Dict[str, PromptVersion] = {}
        self.load_all_versions()
    
    def load_all_versions(self):
        """Load all prompt versions from storage"""
        for prompt_file in self.base_path.glob("*.json"):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    version = PromptVersion.from_dict(data)
                    self.versions[version.id] = version
            except Exception as e:
                print(f"Error loading prompt {prompt_file}: {e}")
    
    def save_version(self, version: PromptVersion):
        """Save prompt version to storage"""
        filename = f"{version.id}_{version.version}.json"
        filepath = self.base_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(version.to_json())
        
        self.versions[version.id] = version
    
    def get_version(self, version_id: str) -> Optional[PromptVersion]:
        """Get prompt version by ID"""
        return self.versions.get(version_id)
    
    def get_versions_by_type(self, prompt_type: PromptType) -> List[PromptVersion]:
        """Get all versions of a specific type"""
        return [v for v in self.versions.values() if v.prompt_type == prompt_type]
    
    def get_latest_version(self, prompt_type: PromptType) -> Optional[PromptVersion]:
        """Get latest version of a specific type"""
        versions = self.get_versions_by_type(prompt_type)
        if not versions:
            return None
        
        # Sort by version number (semantic versioning)
        versions.sort(key=lambda v: self._parse_version(v.version), reverse=True)
        return versions[0]
    
    def get_production_version(self, prompt_type: PromptType) -> Optional[PromptVersion]:
        """Get production version of a specific type"""
        versions = self.get_versions_by_type(prompt_type)
        production_versions = [v for v in versions if v.status == PromptStatus.PRODUCTION]
        
        if not production_versions:
            return None
        
        # Return latest production version
        production_versions.sort(key=lambda v: self._parse_version(v.version), reverse=True)
        return production_versions[0]
    
    def create_new_version(self, 
                          prompt_type: PromptType,
                          content: str,
                          author: str,
                          description: str,
                          change_log: List[str],
                          metadata: Dict[str, Any] = None,
                          dependencies: List[str] = None,
                          tags: List[str] = None) -> PromptVersion:
        """Create new prompt version"""
        # Get latest version to determine next version number
        latest_version = self.get_latest_version(prompt_type)
        next_version = self._get_next_version(latest_version.version if latest_version else "0.0.0")
        
        # Generate unique ID
        version_id = f"{prompt_type.value}_{next_version}_{int(time.time())}"
        
        # Create new version
        new_version = PromptVersion(
            id=version_id,
            prompt_type=prompt_type,
            version=next_version,
            content=content,
            status=PromptStatus.DRAFT,
            author=author,
            created_at=time.time(),
            updated_at=time.time(),
            description=description,
            change_log=change_log,
            metadata=metadata or {},
            performance_metrics={},
            dependencies=dependencies or [],
            tags=tags or []
        )
        
        # Save version
        self.save_version(new_version)
        
        return new_version
    
    def update_version(self, version_id: str, updates: Dict[str, Any]) -> Optional[PromptVersion]:
        """Update existing prompt version"""
        version = self.get_version(version_id)
        if not version:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(version, key):
                setattr(version, key, value)
        
        version.updated_at = time.time()
        
        # Save updated version
        self.save_version(version)
        
        return version
    
    def promote_version(self, version_id: str, new_status: PromptStatus) -> Optional[PromptVersion]:
        """Promote version to new status"""
        version = self.get_version(version_id)
        if not version:
            return None
        
        # Update status
        version.status = new_status
        version.updated_at = time.time()
        
        # If promoting to production, deprecate other production versions
        if new_status == PromptStatus.PRODUCTION:
            self._deprecate_other_production_versions(version.prompt_type, version_id)
        
        # Save updated version
        self.save_version(version)
        
        return version
    
    def _deprecate_other_production_versions(self, prompt_type: PromptType, exclude_id: str):
        """Deprecate other production versions of the same type"""
        for version in self.get_versions_by_type(prompt_type):
            if (version.id != exclude_id and 
                version.status == PromptStatus.PRODUCTION):
                version.status = PromptStatus.DEPRECATED
                version.updated_at = time.time()
                self.save_version(version)
    
    def _parse_version(self, version_str: str) -> Tuple[int, int, int]:
        """Parse semantic version string"""
        try:
            parts = version_str.split('.')
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return (major, minor, patch)
        except (ValueError, IndexError):
            return (0, 0, 0)
    
    def _get_next_version(self, current_version: str) -> str:
        """Get next version number"""
        major, minor, patch = self._parse_version(current_version)
        return f"{major}.{minor}.{patch + 1}"
    
    def get_version_history(self, prompt_type: PromptType) -> List[PromptVersion]:
        """Get version history for a prompt type"""
        versions = self.get_versions_by_type(prompt_type)
        versions.sort(key=lambda v: self._parse_version(v.version), reverse=True)
        return versions
    
    def compare_versions(self, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """Compare two prompt versions"""
        version1 = self.get_version(version_id1)
        version2 = self.get_version(version_id2)
        
        if not version1 or not version2:
            return {}
        
        return {
            'version1': version1.to_dict(),
            'version2': version2.to_dict(),
            'content_diff': self._get_content_diff(version1.content, version2.content),
            'metadata_diff': self._get_metadata_diff(version1.metadata, version2.metadata),
            'performance_diff': self._get_performance_diff(version1.performance_metrics, version2.performance_metrics)
        }
    
    def _get_content_diff(self, content1: str, content2: str) -> List[str]:
        """Get content differences between versions"""
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')
        
        diff = []
        max_lines = max(len(lines1), len(lines2))
        
        for i in range(max_lines):
            line1 = lines1[i] if i < len(lines1) else ""
            line2 = lines2[i] if i < len(lines2) else ""
            
            if line1 != line2:
                diff.append(f"Line {i+1}: '{line1}' -> '{line2}'")
        
        return diff
    
    def _get_metadata_diff(self, metadata1: Dict[str, Any], metadata2: Dict[str, Any]) -> Dict[str, Any]:
        """Get metadata differences between versions"""
        all_keys = set(metadata1.keys()) | set(metadata2.keys())
        diff = {}
        
        for key in all_keys:
            value1 = metadata1.get(key)
            value2 = metadata2.get(key)
            
            if value1 != value2:
                diff[key] = {'old': value1, 'new': value2}
        
        return diff
    
    def _get_performance_diff(self, metrics1: Dict[str, Any], metrics2: Dict[str, Any]) -> Dict[str, Any]:
        """Get performance differences between versions"""
        all_keys = set(metrics1.keys()) | set(metrics2.keys())
        diff = {}
        
        for key in all_keys:
            value1 = metrics1.get(key, 0)
            value2 = metrics2.get(key, 0)
            
            if value1 != value2:
                diff[key] = {
                    'old': value1,
                    'new': value2,
                    'change': value2 - value1,
                    'change_percent': ((value2 - value1) / value1 * 100) if value1 != 0 else 0
                }
        
        return diff
```

### Prompt Performance Monitoring

#### Performance Tracker
```python
class PromptPerformanceTracker:
    """Track performance metrics for prompt versions"""
    
    def __init__(self, repository: PromptRepository):
        self.repository = repository
        self.metrics_store: Dict[str, List[Dict[str, Any]]] = {}
    
    def record_metric(self, version_id: str, metric_name: str, value: float, metadata: Dict[str, Any] = None):
        """Record performance metric for a prompt version"""
        if version_id not in self.metrics_store:
            self.metrics_store[version_id] = []
        
        metric_entry = {
            'timestamp': time.time(),
            'metric_name': metric_name,
            'value': value,
            'metadata': metadata or {}
        }
        
        self.metrics_store[version_id].append(metric_entry)
        
        # Update version performance metrics
        version = self.repository.get_version(version_id)
        if version:
            self._update_version_metrics(version, metric_name, value)
    
    def _update_version_metrics(self, version: PromptVersion, metric_name: str, value: float):
        """Update version performance metrics"""
        if 'metrics' not in version.performance_metrics:
            version.performance_metrics['metrics'] = {}
        
        if metric_name not in version.performance_metrics['metrics']:
            version.performance_metrics['metrics'][metric_name] = []
        
        version.performance_metrics['metrics'][metric_name].append({
            'value': value,
            'timestamp': time.time()
        })
        
        # Calculate aggregated metrics
        self._calculate_aggregated_metrics(version, metric_name)
        
        # Save updated version
        self.repository.save_version(version)
    
    def _calculate_aggregated_metrics(self, version: PromptVersion, metric_name: str):
        """Calculate aggregated metrics for a version"""
        metrics = version.performance_metrics['metrics'][metric_name]
        
        if not metrics:
            return
        
        values = [m['value'] for m in metrics]
        
        # Calculate statistics
        aggregated = {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / len(values),
            'median': sorted(values)[len(values) // 2],
            'std': self._calculate_std(values),
            'last_updated': time.time()
        }
        
        # Calculate percentiles
        sorted_values = sorted(values)
        aggregated['p25'] = sorted_values[int(len(sorted_values) * 0.25)]
        aggregated['p75'] = sorted_values[int(len(sorted_values) * 0.75)]
        aggregated['p95'] = sorted_values[int(len(sorted_values) * 0.95)]
        aggregated['p99'] = sorted_values[int(len(sorted_values) * 0.99)]
        
        # Store aggregated metrics
        if 'aggregated' not in version.performance_metrics:
            version.performance_metrics['aggregated'] = {}
        
        version.performance_metrics['aggregated'][metric_name] = aggregated
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def get_performance_summary(self, version_id: str) -> Dict[str, Any]:
        """Get performance summary for a version"""
        version = self.repository.get_version(version_id)
        if not version:
            return {}
        
        return {
            'version_id': version_id,
            'version': version.version,
            'status': version.status.value,
            'metrics': version.performance_metrics.get('aggregated', {}),
            'total_requests': sum(
                m.get('count', 0) 
                for m in version.performance_metrics.get('aggregated', {}).values()
            )
        }
    
    def compare_performance(self, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """Compare performance between two versions"""
        summary1 = self.get_performance_summary(version_id1)
        summary2 = self.get_performance_summary(version_id2)
        
        if not summary1 or not summary2:
            return {}
        
        comparison = {
            'version1': summary1,
            'version2': summary2,
            'performance_diff': {}
        }
        
        # Compare metrics
        metrics1 = summary1.get('metrics', {})
        metrics2 = summary2.get('metrics', {})
        
        all_metrics = set(metrics1.keys()) | set(metrics2.keys())
        
        for metric in all_metrics:
            value1 = metrics1.get(metric, {}).get('mean', 0)
            value2 = metrics2.get(metric, {}).get('mean', 0)
            
            if value1 != 0 and value2 != 0:
                change_percent = ((value2 - value1) / value1) * 100
                comparison['performance_diff'][metric] = {
                    'version1': value1,
                    'version2': value2,
                    'change': value2 - value1,
                    'change_percent': change_percent
                }
        
        return comparison
    
    def get_performance_trends(self, prompt_type: PromptType, days: int = 30) -> Dict[str, Any]:
        """Get performance trends for a prompt type"""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        versions = self.repository.get_versions_by_type(prompt_type)
        trends = {}
        
        for version in versions:
            if version.created_at >= cutoff_time:
                metrics = version.performance_metrics.get('aggregated', {})
                for metric_name, metric_data in metrics.items():
                    if metric_name not in trends:
                        trends[metric_name] = []
                    
                    trends[metric_name].append({
                        'version': version.version,
                        'timestamp': version.created_at,
                        'value': metric_data.get('mean', 0)
                    })
        
        # Sort by timestamp
        for metric_name in trends:
            trends[metric_name].sort(key=lambda x: x['timestamp'])
        
        return trends
```

### A/B Testing Framework

#### A/B Testing Manager
```python
class ABTestingManager:
    """Manage A/B testing for prompt versions"""
    
    def __init__(self, repository: PromptRepository, performance_tracker: PromptPerformanceTracker):
        self.repository = repository
        self.performance_tracker = performance_tracker
        self.active_tests: Dict[str, Dict[str, Any]] = {}
    
    def create_ab_test(self, 
                      test_name: str,
                      prompt_type: PromptType,
                      version_a_id: str,
                      version_b_id: str,
                      traffic_split: float = 0.5,
                      duration_days: int = 7,
                      success_metrics: List[str] = None) -> str:
        """Create A/B test for two prompt versions"""
        test_id = f"ab_test_{test_name}_{int(time.time())}"
        
        # Validate versions
        version_a = self.repository.get_version(version_a_id)
        version_b = self.repository.get_version(version_b_id)
        
        if not version_a or not version_b:
            raise ValueError("Invalid version IDs")
        
        if version_a.prompt_type != version_b.prompt_type:
            raise ValueError("Versions must be of the same prompt type")
        
        # Create test configuration
        test_config = {
            'test_id': test_id,
            'test_name': test_name,
            'prompt_type': prompt_type.value,
            'version_a_id': version_a_id,
            'version_b_id': version_b_id,
            'traffic_split': traffic_split,
            'duration_days': duration_days,
            'success_metrics': success_metrics or ['accuracy', 'response_time'],
            'start_time': time.time(),
            'end_time': time.time() + (duration_days * 24 * 3600),
            'status': 'active',
            'results': {
                'version_a': {'requests': 0, 'metrics': {}},
                'version_b': {'requests': 0, 'metrics': {}}
            }
        }
        
        self.active_tests[test_id] = test_config
        
        return test_id
    
    def get_version_for_request(self, test_id: str, user_id: str = None) -> str:
        """Get version to use for a request in A/B test"""
        if test_id not in self.active_tests:
            return None
        
        test = self.active_tests[test_id]
        
        # Check if test is still active
        if time.time() > test['end_time']:
            test['status'] = 'completed'
            return None
        
        # Determine version based on traffic split
        if user_id:
            # Use user ID for consistent assignment
            hash_value = hash(f"{test_id}_{user_id}") % 100
        else:
            # Random assignment
            hash_value = hash(str(time.time())) % 100
        
        if hash_value < (test['traffic_split'] * 100):
            return test['version_a_id']
        else:
            return test['version_b_id']
    
    def record_test_result(self, test_id: str, version_id: str, metrics: Dict[str, float]):
        """Record result for A/B test"""
        if test_id not in self.active_tests:
            return
        
        test = self.active_tests[test_id]
        
        # Determine which version
        version_key = 'version_a' if version_id == test['version_a_id'] else 'version_b'
        
        # Update request count
        test['results'][version_key]['requests'] += 1
        
        # Update metrics
        for metric_name, value in metrics.items():
            if metric_name not in test['results'][version_key]['metrics']:
                test['results'][version_key]['metrics'][metric_name] = []
            
            test['results'][version_key]['metrics'][metric_name].append(value)
    
    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test results"""
        if test_id not in self.active_tests:
            return {}
        
        test = self.active_tests[test_id]
        results = test['results']
        
        # Calculate statistics for each version
        for version_key in ['version_a', 'version_b']:
            version_results = results[version_key]
            
            for metric_name, values in version_results['metrics'].items():
                if values:
                    version_results['metrics'][metric_name] = {
                        'count': len(values),
                        'mean': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values),
                        'std': self._calculate_std(values)
                    }
        
        # Calculate statistical significance
        significance = self._calculate_statistical_significance(results)
        
        return {
            'test_id': test_id,
            'test_name': test['test_name'],
            'status': test['status'],
            'results': results,
            'statistical_significance': significance,
            'recommendation': self._get_test_recommendation(results, significance)
        }
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _calculate_statistical_significance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistical significance between versions"""
        # Simplified statistical significance calculation
        # In production, use proper statistical tests (t-test, chi-square, etc.)
        
        significance = {}
        
        for metric_name in results['version_a']['metrics']:
            if metric_name in results['version_b']['metrics']:
                values_a = results['version_a']['metrics'][metric_name]
                values_b = results['version_b']['metrics'][metric_name]
                
                if isinstance(values_a, list) and isinstance(values_b, list):
                    mean_a = sum(values_a) / len(values_a)
                    mean_b = sum(values_b) / len(values_b)
                    
                    # Simple difference calculation
                    difference = abs(mean_b - mean_a)
                    relative_difference = difference / mean_a if mean_a != 0 else 0
                    
                    significance[metric_name] = {
                        'difference': difference,
                        'relative_difference': relative_difference,
                        'significant': relative_difference > 0.05  # 5% threshold
                    }
        
        return significance
    
    def _get_test_recommendation(self, results: Dict[str, Any], significance: Dict[str, Any]) -> str:
        """Get recommendation based on test results"""
        # Analyze results and provide recommendation
        version_a_requests = results['version_a']['requests']
        version_b_requests = results['version_b']['requests']
        
        if version_a_requests < 100 or version_b_requests < 100:
            return "Insufficient data for recommendation"
        
        # Check if any metric shows significant difference
        significant_metrics = [m for m, s in significance.items() if s.get('significant', False)]
        
        if not significant_metrics:
            return "No significant difference found between versions"
        
        # Determine winner based on success metrics
        # This is a simplified version - in production, use proper statistical analysis
        return "Version B shows better performance"  # Placeholder
```

### Prompt Deployment System

#### Deployment Manager
```python
class PromptDeploymentManager:
    """Manage prompt deployment and rollout"""
    
    def __init__(self, repository: PromptRepository):
        self.repository = repository
        self.deployment_history: List[Dict[str, Any]] = []
    
    def deploy_version(self, version_id: str, deployment_strategy: str = "gradual") -> str:
        """Deploy prompt version to production"""
        version = self.repository.get_version(version_id)
        if not version:
            raise ValueError("Version not found")
        
        deployment_id = f"deployment_{version_id}_{int(time.time())}"
        
        deployment = {
            'deployment_id': deployment_id,
            'version_id': version_id,
            'version': version.version,
            'prompt_type': version.prompt_type.value,
            'strategy': deployment_strategy,
            'start_time': time.time(),
            'status': 'in_progress',
            'rollout_percentage': 0,
            'target_percentage': 100,
            'rollout_schedule': self._create_rollout_schedule(deployment_strategy)
        }
        
        self.deployment_history.append(deployment)
        
        # Start deployment process
        self._start_deployment(deployment)
        
        return deployment_id
    
    def _create_rollout_schedule(self, strategy: str) -> List[Dict[str, Any]]:
        """Create rollout schedule based on strategy"""
        if strategy == "immediate":
            return [{'percentage': 100, 'delay_hours': 0}]
        elif strategy == "gradual":
            return [
                {'percentage': 10, 'delay_hours': 0},
                {'percentage': 25, 'delay_hours': 1},
                {'percentage': 50, 'delay_hours': 2},
                {'percentage': 75, 'delay_hours': 4},
                {'percentage': 100, 'delay_hours': 8}
            ]
        elif strategy == "canary":
            return [
                {'percentage': 5, 'delay_hours': 0},
                {'percentage': 10, 'delay_hours': 2},
                {'percentage': 25, 'delay_hours': 4},
                {'percentage': 50, 'delay_hours': 8},
                {'percentage': 100, 'delay_hours': 24}
            ]
        else:
            return [{'percentage': 100, 'delay_hours': 0}]
    
    def _start_deployment(self, deployment: Dict[str, Any]):
        """Start deployment process"""
        # In production, this would integrate with actual deployment systems
        # For now, we'll simulate the deployment process
        
        deployment['status'] = 'in_progress'
        deployment['current_stage'] = 'initializing'
        
        # Simulate deployment stages
        self._simulate_deployment_stages(deployment)
    
    def _simulate_deployment_stages(self, deployment: Dict[str, Any]):
        """Simulate deployment stages"""
        stages = [
            ('initializing', 'Deployment initialization'),
            ('validating', 'Validating prompt version'),
            ('testing', 'Running deployment tests'),
            ('deploying', 'Deploying to production'),
            ('monitoring', 'Monitoring deployment'),
            ('completed', 'Deployment completed')
        ]
        
        for stage, description in stages:
            deployment['current_stage'] = stage
            deployment['stage_description'] = description
            deployment['last_updated'] = time.time()
            
            # Simulate stage duration
            time.sleep(0.1)  # In production, this would be actual deployment time
        
        deployment['status'] = 'completed'
        deployment['end_time'] = time.time()
    
    def rollback_deployment(self, deployment_id: str) -> bool:
        """Rollback deployment"""
        deployment = self._get_deployment(deployment_id)
        if not deployment:
            return False
        
        if deployment['status'] != 'completed':
            return False
        
        # Get previous production version
        prompt_type = PromptType(deployment['prompt_type'])
        previous_version = self._get_previous_production_version(prompt_type, deployment['version_id'])
        
        if not previous_version:
            return False
        
        # Create rollback deployment
        rollback_deployment = {
            'deployment_id': f"rollback_{deployment_id}_{int(time.time())}",
            'version_id': previous_version.id,
            'version': previous_version.version,
            'prompt_type': prompt_type.value,
            'strategy': 'immediate',
            'start_time': time.time(),
            'status': 'in_progress',
            'rollout_percentage': 0,
            'target_percentage': 100,
            'is_rollback': True,
            'original_deployment_id': deployment_id
        }
        
        self.deployment_history.append(rollback_deployment)
        
        # Start rollback process
        self._start_deployment(rollback_deployment)
        
        return True
    
    def _get_deployment(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment by ID"""
        for deployment in self.deployment_history:
            if deployment['deployment_id'] == deployment_id:
                return deployment
        return None
    
    def _get_previous_production_version(self, prompt_type: PromptType, exclude_version_id: str) -> Optional[PromptVersion]:
        """Get previous production version"""
        versions = self.repository.get_versions_by_type(prompt_type)
        production_versions = [v for v in versions if v.status == PromptStatus.PRODUCTION and v.id != exclude_version_id]
        
        if not production_versions:
            return None
        
        # Return latest production version
        production_versions.sort(key=lambda v: self.repository._parse_version(v.version), reverse=True)
        return production_versions[0]
    
    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status"""
        deployment = self._get_deployment(deployment_id)
        if not deployment:
            return {}
        
        return {
            'deployment_id': deployment_id,
            'status': deployment['status'],
            'current_stage': deployment.get('current_stage', 'unknown'),
            'stage_description': deployment.get('stage_description', ''),
            'rollout_percentage': deployment.get('rollout_percentage', 0),
            'start_time': deployment['start_time'],
            'end_time': deployment.get('end_time'),
            'last_updated': deployment.get('last_updated', deployment['start_time'])
        }
    
    def get_deployment_history(self, prompt_type: PromptType = None) -> List[Dict[str, Any]]:
        """Get deployment history"""
        if prompt_type:
            return [d for d in self.deployment_history if d['prompt_type'] == prompt_type.value]
        return self.deployment_history
```

## Prompt Testing

### Prompt Test Suite
```python
import pytest
from unittest.mock import Mock, patch

class TestPromptVersioning:
    """Test prompt versioning functionality"""
    
    def test_prompt_version_creation(self):
        """Test prompt version creation"""
        version = PromptVersion(
            id="test_id",
            prompt_type=PromptType.TEXT_TO_SQL,
            version="1.0.0",
            content="Test prompt content",
            status=PromptStatus.DRAFT,
            author="test_author",
            created_at=time.time(),
            updated_at=time.time(),
            description="Test description",
            change_log=["Initial version"],
            metadata={},
            performance_metrics={},
            dependencies=[],
            tags=[]
        )
        
        assert version.id == "test_id"
        assert version.prompt_type == PromptType.TEXT_TO_SQL
        assert version.version == "1.0.0"
        assert version.content == "Test prompt content"
    
    def test_prompt_repository_operations(self):
        """Test prompt repository operations"""
        repository = PromptRepository("test_prompts")
        
        # Create new version
        version = repository.create_new_version(
            prompt_type=PromptType.TEXT_TO_SQL,
            content="Test prompt",
            author="test_author",
            description="Test description",
            change_log=["Initial version"]
        )
        
        assert version is not None
        assert version.prompt_type == PromptType.TEXT_TO_SQL
        assert version.status == PromptStatus.DRAFT
        
        # Get version
        retrieved_version = repository.get_version(version.id)
        assert retrieved_version.id == version.id
        
        # Update version
        updated_version = repository.update_version(version.id, {'description': 'Updated description'})
        assert updated_version.description == 'Updated description'
        
        # Promote version
        promoted_version = repository.promote_version(version.id, PromptStatus.PRODUCTION)
        assert promoted_version.status == PromptStatus.PRODUCTION
    
    def test_performance_tracking(self):
        """Test performance tracking"""
        repository = PromptRepository("test_prompts")
        tracker = PromptPerformanceTracker(repository)
        
        # Create test version
        version = repository.create_new_version(
            prompt_type=PromptType.TEXT_TO_SQL,
            content="Test prompt",
            author="test_author",
            description="Test description",
            change_log=["Initial version"]
        )
        
        # Record metrics
        tracker.record_metric(version.id, "accuracy", 0.95)
        tracker.record_metric(version.id, "response_time", 1.5)
        
        # Get performance summary
        summary = tracker.get_performance_summary(version.id)
        assert 'accuracy' in summary['metrics']
        assert 'response_time' in summary['metrics']
    
    def test_ab_testing(self):
        """Test A/B testing functionality"""
        repository = PromptRepository("test_prompts")
        tracker = PromptPerformanceTracker(repository)
        ab_manager = ABTestingManager(repository, tracker)
        
        # Create test versions
        version_a = repository.create_new_version(
            prompt_type=PromptType.TEXT_TO_SQL,
            content="Version A prompt",
            author="test_author",
            description="Version A",
            change_log=["Version A"]
        )
        
        version_b = repository.create_new_version(
            prompt_type=PromptType.TEXT_TO_SQL,
            content="Version B prompt",
            author="test_author",
            description="Version B",
            change_log=["Version B"]
        )
        
        # Create A/B test
        test_id = ab_manager.create_ab_test(
            test_name="test_prompt_comparison",
            prompt_type=PromptType.TEXT_TO_SQL,
            version_a_id=version_a.id,
            version_b_id=version_b.id,
            traffic_split=0.5
        )
        
        assert test_id is not None
        
        # Get version for request
        assigned_version = ab_manager.get_version_for_request(test_id, "user1")
        assert assigned_version in [version_a.id, version_b.id]
        
        # Record test results
        ab_manager.record_test_result(test_id, version_a.id, {"accuracy": 0.95, "response_time": 1.5})
        ab_manager.record_test_result(test_id, version_b.id, {"accuracy": 0.97, "response_time": 1.3})
        
        # Get test results
        results = ab_manager.get_test_results(test_id)
        assert 'results' in results
        assert 'statistical_significance' in results
    
    def test_deployment_management(self):
        """Test deployment management"""
        repository = PromptRepository("test_prompts")
        deployment_manager = PromptDeploymentManager(repository)
        
        # Create test version
        version = repository.create_new_version(
            prompt_type=PromptType.TEXT_TO_SQL,
            content="Test prompt",
            author="test_author",
            description="Test description",
            change_log=["Initial version"]
        )
        
        # Deploy version
        deployment_id = deployment_manager.deploy_version(version.id, "gradual")
        assert deployment_id is not None
        
        # Get deployment status
        status = deployment_manager.get_deployment_status(deployment_id)
        assert 'status' in status
        assert 'current_stage' in status
        
        # Get deployment history
        history = deployment_manager.get_deployment_history()
        assert len(history) > 0
        assert history[0]['deployment_id'] == deployment_id
```

## Consequences

### Positive
- **Version Control**: Complete version control for all prompts
- **Performance Tracking**: Detailed performance monitoring for each version
- **A/B Testing**: Ability to test and compare different prompt versions
- **Rollback Capability**: Quick rollback to previous versions
- **Deployment Management**: Controlled deployment and rollout process

### Negative
- **Complexity**: More complex prompt management system
- **Storage Overhead**: Additional storage for version history
- **Performance Impact**: Version management adds overhead
- **Maintenance**: More code to maintain and test

### Risks
- **Version Conflicts**: Multiple versions may cause conflicts
- **Performance Degradation**: Version management may impact performance
- **Data Loss**: Risk of losing prompt versions
- **Deployment Failures**: Deployment process may fail

## Success Metrics

### Version Management Metrics
- **Version Coverage**: 100% of prompts under version control
- **Change Tracking**: 100% of changes tracked with metadata
- **Rollback Success**: 100% successful rollback operations
- **Deployment Success**: >95% successful deployments

### Performance Metrics
- **Version Performance**: Track performance for each version
- **A/B Test Success**: >80% of A/B tests provide clear results
- **Deployment Time**: <5 minutes for deployment
- **Rollback Time**: <2 minutes for rollback

## Implementation Timeline

### Phase 1: Basic Versioning (Week 1)
- [x] Implement prompt versioning system
- [x] Create prompt repository
- [x] Set up version management

### Phase 2: Performance Tracking (Week 2)
- [x] Implement performance tracking
- [x] Add metrics collection
- [x] Create performance analytics

### Phase 3: A/B Testing (Week 3)
- [ ] Implement A/B testing framework
- [ ] Add statistical analysis
- [ ] Create test management

### Phase 4: Deployment & Rollout (Week 4)
- [ ] Implement deployment management
- [ ] Add rollout strategies
- [ ] Create rollback capabilities

## References

- [Semantic Versioning](https://semver.org/)
- [Git Version Control](https://git-scm.com/)
- [A/B Testing Best Practices](https://www.optimizely.com/optimization-glossary/ab-testing/)
- [Deployment Strategies](https://martinfowler.com/bliki/DeploymentPipeline.html)
- [Performance Monitoring](https://docs.python.org/3/library/profile.html)
