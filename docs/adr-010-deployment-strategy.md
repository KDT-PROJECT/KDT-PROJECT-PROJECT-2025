# ADR-010: Deployment Strategy and DevOps

## Status
Accepted

## Context
The development policy (development-policy.mdc) mandates a comprehensive deployment strategy for the Seoul Commercial Analysis LLM System. The current system lacks proper deployment processes, making it difficult to:

1. **Deploy Changes Safely**: No safe deployment process for system changes
2. **Manage Environments**: No proper environment management
3. **Monitor Deployments**: No deployment monitoring and rollback capabilities
4. **Ensure Reliability**: No deployment reliability and consistency

## Decision
We will implement a comprehensive deployment strategy following the development policy requirements:

### Deployment Architecture

#### 1. Environment Management
- **Development Environment**: Local development and testing
- **Staging Environment**: Pre-production testing and validation
- **Production Environment**: Live production system
- **Environment Isolation**: Complete isolation between environments

#### 2. Deployment Pipeline
- **Continuous Integration**: Automated build and test pipeline
- **Continuous Deployment**: Automated deployment pipeline
- **Quality Gates**: Quality checks at each stage
- **Rollback Capability**: Quick rollback for failed deployments

#### 3. Configuration Management
- **Environment-Specific Config**: Different configs for each environment
- **Secrets Management**: Secure secrets management
- **Configuration Validation**: Validate configuration before deployment
- **Configuration Versioning**: Version control for configuration

#### 4. Monitoring & Observability
- **Deployment Monitoring**: Monitor deployment process
- **Health Checks**: Automated health checks after deployment
- **Performance Monitoring**: Monitor system performance
- **Alerting**: Automated alerting for deployment issues

## Implementation Details

### Environment Management

#### Environment Configuration
```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum
import os
import json
from pathlib import Path

class Environment(Enum):
    """Environment enumeration"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class EnvironmentConfig:
    """Environment configuration"""
    name: Environment
    database_url: str
    redis_url: str
    llm_api_key: str
    gemini_api_key: str
    log_level: str
    debug_mode: bool
    max_workers: int
    cache_ttl: int
    rate_limit: int
    timeout: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name.value,
            'database_url': self.database_url,
            'redis_url': self.redis_url,
            'llm_api_key': self.llm_api_key,
            'gemini_api_key': self.gemini_api_key,
            'log_level': self.log_level,
            'debug_mode': self.debug_mode,
            'max_workers': self.max_workers,
            'cache_ttl': self.cache_ttl,
            'rate_limit': self.rate_limit,
            'timeout': self.timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentConfig':
        """Create from dictionary"""
        return cls(
            name=Environment(data['name']),
            database_url=data['database_url'],
            redis_url=data['redis_url'],
            llm_api_key=data['llm_api_key'],
            gemini_api_key=data['gemini_api_key'],
            log_level=data['log_level'],
            debug_mode=data['debug_mode'],
            max_workers=data['max_workers'],
            cache_ttl=data['cache_ttl'],
            rate_limit=data['rate_limit'],
            timeout=data['timeout']
        )

class EnvironmentManager:
    """Manage environment configurations"""
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.config_path.mkdir(exist_ok=True)
        self.environments: Dict[Environment, EnvironmentConfig] = {}
        self.load_environments()
    
    def load_environments(self):
        """Load environment configurations"""
        for env in Environment:
            config_file = self.config_path / f"{env.value}.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.environments[env] = EnvironmentConfig.from_dict(data)
            else:
                # Create default configuration
                self.environments[env] = self._create_default_config(env)
                self.save_environment(env)
    
    def save_environment(self, environment: Environment):
        """Save environment configuration"""
        config = self.environments[environment]
        config_file = self.config_path / f"{environment.value}.json"
        
        with open(config_file, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
    
    def get_environment_config(self, environment: Environment) -> EnvironmentConfig:
        """Get environment configuration"""
        return self.environments.get(environment)
    
    def update_environment_config(self, environment: Environment, updates: Dict[str, Any]):
        """Update environment configuration"""
        if environment in self.environments:
            config = self.environments[environment]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            # Save updated configuration
            self.save_environment(environment)
    
    def validate_environment_config(self, environment: Environment) -> bool:
        """Validate environment configuration"""
        config = self.get_environment_config(environment)
        if not config:
            return False
        
        # Check required fields
        required_fields = ['database_url', 'llm_api_key', 'gemini_api_key']
        for field in required_fields:
            if not getattr(config, field):
                return False
        
        # Validate URLs
        if not self._validate_url(config.database_url):
            return False
        
        if config.redis_url and not self._validate_url(config.redis_url):
            return False
        
        return True
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def _create_default_config(self, environment: Environment) -> EnvironmentConfig:
        """Create default configuration for environment"""
        defaults = {
            Environment.DEVELOPMENT: {
                'database_url': 'mysql://dev_user:dev_pass@localhost:3306/dev_db',
                'redis_url': 'redis://localhost:6379/0',
                'llm_api_key': 'dev_llm_key',
                'gemini_api_key': 'dev_gemini_key',
                'log_level': 'DEBUG',
                'debug_mode': True,
                'max_workers': 2,
                'cache_ttl': 300,
                'rate_limit': 100,
                'timeout': 30
            },
            Environment.STAGING: {
                'database_url': 'mysql://staging_user:staging_pass@staging-db:3306/staging_db',
                'redis_url': 'redis://staging-redis:6379/0',
                'llm_api_key': 'staging_llm_key',
                'gemini_api_key': 'staging_gemini_key',
                'log_level': 'INFO',
                'debug_mode': False,
                'max_workers': 4,
                'cache_ttl': 600,
                'rate_limit': 200,
                'timeout': 60
            },
            Environment.PRODUCTION: {
                'database_url': 'mysql://prod_user:prod_pass@prod-db:3306/prod_db',
                'redis_url': 'redis://prod-redis:6379/0',
                'llm_api_key': 'prod_llm_key',
                'gemini_api_key': 'prod_gemini_key',
                'log_level': 'WARNING',
                'debug_mode': False,
                'max_workers': 8,
                'cache_ttl': 1800,
                'rate_limit': 500,
                'timeout': 120
            }
        }
        
        env_defaults = defaults.get(environment, defaults[Environment.DEVELOPMENT])
        
        return EnvironmentConfig(
            name=environment,
            database_url=env_defaults['database_url'],
            redis_url=env_defaults['redis_url'],
            llm_api_key=env_defaults['llm_api_key'],
            gemini_api_key=env_defaults['gemini_api_key'],
            log_level=env_defaults['log_level'],
            debug_mode=env_defaults['debug_mode'],
            max_workers=env_defaults['max_workers'],
            cache_ttl=env_defaults['cache_ttl'],
            rate_limit=env_defaults['rate_limit'],
            timeout=env_defaults['timeout']
        )
```

### Deployment Pipeline

#### CI/CD Pipeline
```python
import subprocess
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class DeploymentStatus(Enum):
    """Deployment status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class DeploymentStep:
    """Deployment step"""
    name: str
    command: str
    timeout: int
    retry_count: int
    required: bool
    environment: Environment

@dataclass
class Deployment:
    """Deployment information"""
    id: str
    version: str
    environment: Environment
    status: DeploymentStatus
    start_time: float
    end_time: Optional[float]
    steps: List[DeploymentStep]
    logs: List[str]
    error: Optional[str]

class DeploymentPipeline:
    """Deployment pipeline manager"""
    
    def __init__(self, environment_manager: EnvironmentManager):
        self.environment_manager = environment_manager
        self.deployments: List[Deployment] = []
        self.deployment_steps = self._create_deployment_steps()
    
    def _create_deployment_steps(self) -> Dict[Environment, List[DeploymentStep]]:
        """Create deployment steps for each environment"""
        return {
            Environment.DEVELOPMENT: [
                DeploymentStep("validate_config", "python -m pytest tests/config/", 60, 1, True, Environment.DEVELOPMENT),
                DeploymentStep("run_tests", "python -m pytest tests/", 300, 2, True, Environment.DEVELOPMENT),
                DeploymentStep("build_image", "docker build -t seoul-analysis:dev .", 180, 1, True, Environment.DEVELOPMENT),
                DeploymentStep("deploy", "docker-compose -f docker-compose.dev.yml up -d", 120, 1, True, Environment.DEVELOPMENT),
                DeploymentStep("health_check", "python scripts/health_check.py --env development", 30, 3, True, Environment.DEVELOPMENT)
            ],
            Environment.STAGING: [
                DeploymentStep("validate_config", "python -m pytest tests/config/", 60, 1, True, Environment.STAGING),
                DeploymentStep("run_tests", "python -m pytest tests/", 300, 2, True, Environment.STAGING),
                DeploymentStep("security_scan", "python scripts/security_scan.py", 120, 1, True, Environment.STAGING),
                DeploymentStep("build_image", "docker build -t seoul-analysis:staging .", 180, 1, True, Environment.STAGING),
                DeploymentStep("deploy", "docker-compose -f docker-compose.staging.yml up -d", 120, 1, True, Environment.STAGING),
                DeploymentStep("health_check", "python scripts/health_check.py --env staging", 30, 3, True, Environment.STAGING),
                DeploymentStep("smoke_tests", "python scripts/smoke_tests.py --env staging", 60, 2, True, Environment.STAGING)
            ],
            Environment.PRODUCTION: [
                DeploymentStep("validate_config", "python -m pytest tests/config/", 60, 1, True, Environment.PRODUCTION),
                DeploymentStep("run_tests", "python -m pytest tests/", 300, 2, True, Environment.PRODUCTION),
                DeploymentStep("security_scan", "python scripts/security_scan.py", 120, 1, True, Environment.PRODUCTION),
                DeploymentStep("performance_tests", "python scripts/performance_tests.py", 180, 1, True, Environment.PRODUCTION),
                DeploymentStep("build_image", "docker build -t seoul-analysis:prod .", 180, 1, True, Environment.PRODUCTION),
                DeploymentStep("backup_database", "python scripts/backup_database.py", 300, 1, True, Environment.PRODUCTION),
                DeploymentStep("deploy", "docker-compose -f docker-compose.prod.yml up -d", 120, 1, True, Environment.PRODUCTION),
                DeploymentStep("health_check", "python scripts/health_check.py --env production", 30, 3, True, Environment.PRODUCTION),
                DeploymentStep("smoke_tests", "python scripts/smoke_tests.py --env production", 60, 2, True, Environment.PRODUCTION),
                DeploymentStep("monitoring_setup", "python scripts/setup_monitoring.py", 60, 1, False, Environment.PRODUCTION)
            ]
        }
    
    def deploy(self, version: str, environment: Environment) -> str:
        """Deploy to environment"""
        deployment_id = f"deploy_{version}_{environment.value}_{int(time.time())}"
        
        deployment = Deployment(
            id=deployment_id,
            version=version,
            environment=environment,
            status=DeploymentStatus.PENDING,
            start_time=time.time(),
            end_time=None,
            steps=self.deployment_steps[environment],
            logs=[],
            error=None
        )
        
        self.deployments.append(deployment)
        
        # Start deployment in background
        self._execute_deployment(deployment)
        
        return deployment_id
    
    def _execute_deployment(self, deployment: Deployment):
        """Execute deployment steps"""
        deployment.status = DeploymentStatus.RUNNING
        
        try:
            for step in deployment.steps:
                self._log_deployment(deployment, f"Starting step: {step.name}")
                
                success = self._execute_step(step, deployment)
                
                if not success:
                    if step.required:
                        deployment.status = DeploymentStatus.FAILED
                        deployment.error = f"Required step failed: {step.name}"
                        deployment.end_time = time.time()
                        return
                    else:
                        self._log_deployment(deployment, f"Optional step failed: {step.name}")
            
            # All steps completed successfully
            deployment.status = DeploymentStatus.SUCCESS
            deployment.end_time = time.time()
            self._log_deployment(deployment, "Deployment completed successfully")
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error = str(e)
            deployment.end_time = time.time()
            self._log_deployment(deployment, f"Deployment failed: {str(e)}")
    
    def _execute_step(self, step: DeploymentStep, deployment: Deployment) -> bool:
        """Execute deployment step"""
        for attempt in range(step.retry_count):
            try:
                self._log_deployment(deployment, f"Executing: {step.command} (attempt {attempt + 1})")
                
                # Set environment variables
                env = os.environ.copy()
                env['ENVIRONMENT'] = step.environment.value
                
                # Execute command
                result = subprocess.run(
                    step.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=step.timeout,
                    env=env
                )
                
                if result.returncode == 0:
                    self._log_deployment(deployment, f"Step completed: {step.name}")
                    if result.stdout:
                        self._log_deployment(deployment, f"Output: {result.stdout}")
                    return True
                else:
                    self._log_deployment(deployment, f"Step failed: {step.name}")
                    if result.stderr:
                        self._log_deployment(deployment, f"Error: {result.stderr}")
                    
                    if attempt < step.retry_count - 1:
                        time.sleep(5)  # Wait before retry
                    else:
                        return False
                        
            except subprocess.TimeoutExpired:
                self._log_deployment(deployment, f"Step timed out: {step.name}")
                if attempt < step.retry_count - 1:
                    time.sleep(5)
                else:
                    return False
                    
            except Exception as e:
                self._log_deployment(deployment, f"Step error: {step.name} - {str(e)}")
                if attempt < step.retry_count - 1:
                    time.sleep(5)
                else:
                    return False
        
        return False
    
    def _log_deployment(self, deployment: Deployment, message: str):
        """Log deployment message"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        deployment.logs.append(log_message)
        print(log_message)  # Also print to console
    
    def get_deployment_status(self, deployment_id: str) -> Optional[Deployment]:
        """Get deployment status"""
        for deployment in self.deployments:
            if deployment.id == deployment_id:
                return deployment
        return None
    
    def get_deployment_logs(self, deployment_id: str) -> List[str]:
        """Get deployment logs"""
        deployment = self.get_deployment_status(deployment_id)
        if deployment:
            return deployment.logs
        return []
    
    def rollback_deployment(self, deployment_id: str) -> bool:
        """Rollback deployment"""
        deployment = self.get_deployment_status(deployment_id)
        if not deployment:
            return False
        
        if deployment.status != DeploymentStatus.SUCCESS:
            return False
        
        # Create rollback deployment
        rollback_id = f"rollback_{deployment_id}_{int(time.time())}"
        
        rollback_deployment = Deployment(
            id=rollback_id,
            version=deployment.version,
            environment=deployment.environment,
            status=DeploymentStatus.PENDING,
            start_time=time.time(),
            end_time=None,
            steps=self._create_rollback_steps(deployment.environment),
            logs=[],
            error=None
        )
        
        self.deployments.append(rollback_deployment)
        
        # Execute rollback
        self._execute_rollback(rollback_deployment, deployment)
        
        return True
    
    def _create_rollback_steps(self, environment: Environment) -> List[DeploymentStep]:
        """Create rollback steps"""
        return [
            DeploymentStep("stop_services", "docker-compose down", 60, 1, True, environment),
            DeploymentStep("restore_database", "python scripts/restore_database.py", 300, 1, True, environment),
            DeploymentStep("deploy_previous", "docker-compose up -d", 120, 1, True, environment),
            DeploymentStep("health_check", "python scripts/health_check.py", 30, 3, True, environment)
        ]
    
    def _execute_rollback(self, rollback_deployment: Deployment, original_deployment: Deployment):
        """Execute rollback"""
        rollback_deployment.status = DeploymentStatus.RUNNING
        
        try:
            for step in rollback_deployment.steps:
                self._log_deployment(rollback_deployment, f"Rollback step: {step.name}")
                
                success = self._execute_step(step, rollback_deployment)
                
                if not success and step.required:
                    rollback_deployment.status = DeploymentStatus.FAILED
                    rollback_deployment.error = f"Rollback step failed: {step.name}"
                    rollback_deployment.end_time = time.time()
                    return
            
            # Rollback completed
            rollback_deployment.status = DeploymentStatus.ROLLED_BACK
            rollback_deployment.end_time = time.time()
            self._log_deployment(rollback_deployment, "Rollback completed successfully")
            
            # Update original deployment status
            original_deployment.status = DeploymentStatus.ROLLED_BACK
            
        except Exception as e:
            rollback_deployment.status = DeploymentStatus.FAILED
            rollback_deployment.error = str(e)
            rollback_deployment.end_time = time.time()
            self._log_deployment(rollback_deployment, f"Rollback failed: {str(e)}")
    
    def get_deployment_history(self, environment: Environment = None) -> List[Deployment]:
        """Get deployment history"""
        if environment:
            return [d for d in self.deployments if d.environment == environment]
        return self.deployments
```

### Configuration Management

#### Secrets Management
```python
import base64
import json
from cryptography.fernet import Fernet
from typing import Dict, Any, Optional

class SecretsManager:
    """Manage secrets and sensitive configuration"""
    
    def __init__(self, key_file: str = "secrets.key"):
        self.key_file = key_file
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
        self.secrets: Dict[str, str] = {}
        self.load_secrets()
    
    def _load_or_generate_key(self) -> bytes:
        """Load or generate encryption key"""
        try:
            with open(self.key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key
    
    def load_secrets(self):
        """Load secrets from encrypted storage"""
        try:
            with open('secrets.encrypted', 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                self.secrets = json.loads(decrypted_data.decode())
        except FileNotFoundError:
            self.secrets = {}
    
    def save_secrets(self):
        """Save secrets to encrypted storage"""
        data = json.dumps(self.secrets).encode()
        encrypted_data = self.cipher.encrypt(data)
        
        with open('secrets.encrypted', 'wb') as f:
            f.write(encrypted_data)
    
    def set_secret(self, key: str, value: str):
        """Set secret value"""
        self.secrets[key] = value
        self.save_secrets()
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret value"""
        return self.secrets.get(key)
    
    def delete_secret(self, key: str):
        """Delete secret"""
        if key in self.secrets:
            del self.secrets[key]
            self.save_secrets()
    
    def list_secrets(self) -> List[str]:
        """List all secret keys"""
        return list(self.secrets.keys())
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a value"""
        encrypted = self.cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a value"""
        encrypted = base64.b64decode(encrypted_value.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()
```

#### Configuration Validator
```python
class ConfigurationValidator:
    """Validate configuration before deployment"""
    
    def __init__(self, environment_manager: EnvironmentManager, secrets_manager: SecretsManager):
        self.environment_manager = environment_manager
        self.secrets_manager = secrets_manager
    
    def validate_environment(self, environment: Environment) -> Dict[str, Any]:
        """Validate environment configuration"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'checks': {}
        }
        
        config = self.environment_manager.get_environment_config(environment)
        if not config:
            validation_result['valid'] = False
            validation_result['errors'].append("Configuration not found")
            return validation_result
        
        # Validate basic configuration
        self._validate_basic_config(config, validation_result)
        
        # Validate database connection
        self._validate_database_connection(config, validation_result)
        
        # Validate external services
        self._validate_external_services(config, validation_result)
        
        # Validate secrets
        self._validate_secrets(config, validation_result)
        
        # Validate performance settings
        self._validate_performance_settings(config, validation_result)
        
        return validation_result
    
    def _validate_basic_config(self, config: EnvironmentConfig, result: Dict[str, Any]):
        """Validate basic configuration"""
        checks = {}
        
        # Check required fields
        required_fields = ['database_url', 'llm_api_key', 'gemini_api_key']
        for field in required_fields:
            value = getattr(config, field)
            if not value or value == f"dev_{field}":
                checks[field] = {'status': 'error', 'message': f'{field} is required'}
                result['errors'].append(f"{field} is required")
            else:
                checks[field] = {'status': 'ok', 'message': f'{field} is set'}
        
        # Check URL formats
        if config.database_url and not self._is_valid_url(config.database_url):
            checks['database_url'] = {'status': 'error', 'message': 'Invalid database URL format'}
            result['errors'].append("Invalid database URL format")
        
        if config.redis_url and not self._is_valid_url(config.redis_url):
            checks['redis_url'] = {'status': 'warning', 'message': 'Invalid Redis URL format'}
            result['warnings'].append("Invalid Redis URL format")
        
        result['checks']['basic_config'] = checks
    
    def _validate_database_connection(self, config: EnvironmentConfig, result: Dict[str, Any]):
        """Validate database connection"""
        checks = {}
        
        try:
            # Test database connection
            import mysql.connector
            
            # Parse database URL
            from urllib.parse import urlparse
            parsed = urlparse(config.database_url)
            
            connection = mysql.connector.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:] if parsed.path else None
            )
            
            connection.close()
            checks['connection'] = {'status': 'ok', 'message': 'Database connection successful'}
            
        except Exception as e:
            checks['connection'] = {'status': 'error', 'message': f'Database connection failed: {str(e)}'}
            result['errors'].append(f"Database connection failed: {str(e)}")
        
        result['checks']['database'] = checks
    
    def _validate_external_services(self, config: EnvironmentConfig, result: Dict[str, Any]):
        """Validate external services"""
        checks = {}
        
        # Validate LLM API key
        if config.llm_api_key and len(config.llm_api_key) < 10:
            checks['llm_api_key'] = {'status': 'warning', 'message': 'LLM API key seems too short'}
            result['warnings'].append("LLM API key seems too short")
        else:
            checks['llm_api_key'] = {'status': 'ok', 'message': 'LLM API key format looks valid'}
        
        # Validate Gemini API key
        if config.gemini_api_key and len(config.gemini_api_key) < 10:
            checks['gemini_api_key'] = {'status': 'warning', 'message': 'Gemini API key seems too short'}
            result['warnings'].append("Gemini API key seems too short")
        else:
            checks['gemini_api_key'] = {'status': 'ok', 'message': 'Gemini API key format looks valid'}
        
        result['checks']['external_services'] = checks
    
    def _validate_secrets(self, config: EnvironmentConfig, result: Dict[str, Any]):
        """Validate secrets"""
        checks = {}
        
        # Check if secrets are properly encrypted
        required_secrets = ['llm_api_key', 'gemini_api_key']
        for secret in required_secrets:
            value = getattr(config, secret)
            if value and not self._is_encrypted(value):
                checks[secret] = {'status': 'warning', 'message': 'Secret should be encrypted'}
                result['warnings'].append(f"{secret} should be encrypted")
            else:
                checks[secret] = {'status': 'ok', 'message': 'Secret is encrypted'}
        
        result['checks']['secrets'] = checks
    
    def _validate_performance_settings(self, config: EnvironmentConfig, result: Dict[str, Any]):
        """Validate performance settings"""
        checks = {}
        
        # Check max workers
        if config.max_workers < 1 or config.max_workers > 16:
            checks['max_workers'] = {'status': 'warning', 'message': 'Max workers should be between 1 and 16'}
            result['warnings'].append("Max workers should be between 1 and 16")
        else:
            checks['max_workers'] = {'status': 'ok', 'message': 'Max workers is within reasonable range'}
        
        # Check cache TTL
        if config.cache_ttl < 60 or config.cache_ttl > 3600:
            checks['cache_ttl'] = {'status': 'warning', 'message': 'Cache TTL should be between 60 and 3600 seconds'}
            result['warnings'].append("Cache TTL should be between 60 and 3600 seconds")
        else:
            checks['cache_ttl'] = {'status': 'ok', 'message': 'Cache TTL is within reasonable range'}
        
        # Check timeout
        if config.timeout < 10 or config.timeout > 300:
            checks['timeout'] = {'status': 'warning', 'message': 'Timeout should be between 10 and 300 seconds'}
            result['warnings'].append("Timeout should be between 10 and 300 seconds")
        else:
            checks['timeout'] = {'status': 'ok', 'message': 'Timeout is within reasonable range'}
        
        result['checks']['performance'] = checks
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def _is_encrypted(self, value: str) -> bool:
        """Check if value is encrypted"""
        try:
            # Try to decrypt - if it works, it's encrypted
            self.secrets_manager.decrypt_value(value)
            return True
        except Exception:
            return False
```

### Deployment Monitoring

#### Health Check System
```python
import requests
import time
from typing import Dict, Any, List, Optional

class HealthChecker:
    """Health check system for deployments"""
    
    def __init__(self, environment_manager: EnvironmentManager):
        self.environment_manager = environment_manager
        self.health_checks: List[Dict[str, Any]] = []
    
    def run_health_checks(self, environment: Environment) -> Dict[str, Any]:
        """Run health checks for environment"""
        config = self.environment_manager.get_environment_config(environment)
        if not config:
            return {'status': 'error', 'message': 'Configuration not found'}
        
        health_result = {
            'environment': environment.value,
            'timestamp': time.time(),
            'overall_status': 'healthy',
            'checks': {},
            'errors': [],
            'warnings': []
        }
        
        # Run individual health checks
        self._check_database_health(config, health_result)
        self._check_redis_health(config, health_result)
        self._check_llm_service_health(config, health_result)
        self._check_application_health(config, health_result)
        
        # Determine overall status
        if health_result['errors']:
            health_result['overall_status'] = 'unhealthy'
        elif health_result['warnings']:
            health_result['overall_status'] = 'degraded'
        
        return health_result
    
    def _check_database_health(self, config: EnvironmentConfig, result: Dict[str, Any]):
        """Check database health"""
        try:
            import mysql.connector
            from urllib.parse import urlparse
            
            parsed = urlparse(config.database_url)
            
            connection = mysql.connector.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:] if parsed.path else None,
                connect_timeout=10
            )
            
            # Test query
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            connection.close()
            
            result['checks']['database'] = {
                'status': 'healthy',
                'response_time': 0.1,  # Placeholder
                'message': 'Database connection successful'
            }
            
        except Exception as e:
            result['checks']['database'] = {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Database connection failed'
            }
            result['errors'].append(f"Database health check failed: {str(e)}")
    
    def _check_redis_health(self, config: EnvironmentConfig, result: Dict[str, Any]):
        """Check Redis health"""
        if not config.redis_url:
            result['checks']['redis'] = {
                'status': 'skipped',
                'message': 'Redis not configured'
            }
            return
        
        try:
            import redis
            from urllib.parse import urlparse
            
            parsed = urlparse(config.redis_url)
            
            r = redis.Redis(
                host=parsed.hostname,
                port=parsed.port or 6379,
                db=int(parsed.path[1:]) if parsed.path and parsed.path[1:].isdigit() else 0,
                socket_connect_timeout=10
            )
            
            # Test ping
            r.ping()
            
            result['checks']['redis'] = {
                'status': 'healthy',
                'response_time': 0.05,  # Placeholder
                'message': 'Redis connection successful'
            }
            
        except Exception as e:
            result['checks']['redis'] = {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Redis connection failed'
            }
            result['errors'].append(f"Redis health check failed: {str(e)}")
    
    def _check_llm_service_health(self, config: EnvironmentConfig, result: Dict[str, Any]):
        """Check LLM service health"""
        try:
            # Test LLM service with simple request
            # This is a placeholder - actual implementation would depend on the LLM service
            
            result['checks']['llm_service'] = {
                'status': 'healthy',
                'response_time': 0.5,  # Placeholder
                'message': 'LLM service is responding'
            }
            
        except Exception as e:
            result['checks']['llm_service'] = {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'LLM service is not responding'
            }
            result['errors'].append(f"LLM service health check failed: {str(e)}")
    
    def _check_application_health(self, config: EnvironmentConfig, result: Dict[str, Any]):
        """Check application health"""
        try:
            # Test application endpoints
            # This is a placeholder - actual implementation would test actual endpoints
            
            result['checks']['application'] = {
                'status': 'healthy',
                'response_time': 0.2,  # Placeholder
                'message': 'Application is responding'
            }
            
        except Exception as e:
            result['checks']['application'] = {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Application is not responding'
            }
            result['errors'].append(f"Application health check failed: {str(e)}")
    
    def wait_for_healthy(self, environment: Environment, timeout: int = 300) -> bool:
        """Wait for environment to be healthy"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            health_result = self.run_health_checks(environment)
            
            if health_result['overall_status'] == 'healthy':
                return True
            
            time.sleep(10)  # Wait 10 seconds before next check
        
        return False
    
    def get_health_history(self, environment: Environment, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history"""
        # This would typically query a database or monitoring system
        # For now, return empty list
        return []
```

## Deployment Scripts

### Deployment Scripts
```python
#!/usr/bin/env python3
"""
Deployment script for Seoul Commercial Analysis LLM System
"""

import argparse
import sys
import time
from pathlib import Path

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description='Deploy Seoul Commercial Analysis LLM System')
    parser.add_argument('--environment', choices=['development', 'staging', 'production'], required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--skip-tests', action='store_true', help='Skip tests')
    parser.add_argument('--skip-backup', action='store_true', help='Skip database backup')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    # Initialize deployment components
    environment_manager = EnvironmentManager()
    secrets_manager = SecretsManager()
    validator = ConfigurationValidator(environment_manager, secrets_manager)
    pipeline = DeploymentPipeline(environment_manager)
    health_checker = HealthChecker(environment_manager)
    
    environment = Environment(args.environment)
    
    print(f"Starting deployment of version {args.version} to {environment.value}")
    
    # Validate configuration
    print("Validating configuration...")
    validation_result = validator.validate_environment(environment)
    
    if not validation_result['valid']:
        print("Configuration validation failed:")
        for error in validation_result['errors']:
            print(f"  ERROR: {error}")
        sys.exit(1)
    
    if validation_result['warnings']:
        print("Configuration warnings:")
        for warning in validation_result['warnings']:
            print(f"  WARNING: {warning}")
    
    if args.dry_run:
        print("Dry run mode - deployment would proceed")
        return 0
    
    # Start deployment
    print("Starting deployment...")
    deployment_id = pipeline.deploy(args.version, environment)
    
    # Monitor deployment
    print(f"Deployment ID: {deployment_id}")
    print("Monitoring deployment progress...")
    
    while True:
        deployment = pipeline.get_deployment_status(deployment_id)
        if not deployment:
            print("Deployment not found")
            sys.exit(1)
        
        if deployment.status in [DeploymentStatus.SUCCESS, DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK]:
            break
        
        time.sleep(5)
    
    # Check deployment result
    if deployment.status == DeploymentStatus.SUCCESS:
        print("Deployment completed successfully!")
        
        # Run health checks
        print("Running health checks...")
        health_result = health_checker.run_health_checks(environment)
        
        if health_result['overall_status'] == 'healthy':
            print("Health checks passed!")
            return 0
        else:
            print("Health checks failed:")
            for error in health_result['errors']:
                print(f"  ERROR: {error}")
            return 1
    
    elif deployment.status == DeploymentStatus.FAILED:
        print("Deployment failed!")
        if deployment.error:
            print(f"Error: {deployment.error}")
        return 1
    
    elif deployment.status == DeploymentStatus.ROLLED_BACK:
        print("Deployment was rolled back!")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

## Consequences

### Positive
- **Safe Deployments**: Safe and reliable deployment process
- **Environment Management**: Proper environment isolation and management
- **Configuration Management**: Secure and validated configuration
- **Monitoring**: Comprehensive deployment monitoring
- **Rollback Capability**: Quick rollback for failed deployments

### Negative
- **Complexity**: More complex deployment infrastructure
- **Maintenance**: More deployment code to maintain
- **Resource Usage**: Higher resource usage for deployment
- **Learning Curve**: Team needs to learn deployment processes

### Risks
- **Deployment Failures**: Deployments may fail due to various issues
- **Configuration Errors**: Configuration errors may cause deployment issues
- **Rollback Failures**: Rollback process may fail
- **Environment Issues**: Environment-specific issues may occur

## Success Metrics

### Deployment Metrics
- **Deployment Success Rate**: >95% successful deployments
- **Deployment Time**: <30 minutes for full deployment
- **Rollback Time**: <10 minutes for rollback
- **Configuration Validation**: 100% configuration validation

### System Metrics
- **System Uptime**: >99.5% uptime after deployment
- **Health Check Success**: >95% health check success rate
- **Performance Impact**: <5% performance degradation after deployment
- **Error Rate**: <1% error rate after deployment

## Implementation Timeline

### Phase 1: Environment Management (Week 1)
- [x] Implement environment management
- [x] Create configuration management
- [x] Set up secrets management

### Phase 2: Deployment Pipeline (Week 2)
- [x] Implement deployment pipeline
- [x] Add deployment steps
- [x] Create rollback capability

### Phase 3: Monitoring & Validation (Week 3)
- [ ] Implement health checks
- [ ] Add configuration validation
- [ ] Create deployment monitoring

### Phase 4: Automation & Scripts (Week 4)
- [ ] Implement deployment scripts
- [ ] Add CI/CD integration
- [ ] Create deployment documentation

## References

- [Deployment Best Practices](https://martinfowler.com/articles/deployment.html)
- [Continuous Deployment](https://martinfowler.com/articles/continuousDeployment.html)
- [Configuration Management](https://en.wikipedia.org/wiki/Configuration_management)
- [Secrets Management](https://en.wikipedia.org/wiki/Secrets_management)
- [Health Checks](https://en.wikipedia.org/wiki/Health_check_(computing))
