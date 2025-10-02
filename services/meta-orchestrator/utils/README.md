# Meta-Orchestrator Utilities

Utility functions and helpers for the Meta-Orchestration Service, providing common functionality used across different components.

## 📋 Overview

The utils package contains reusable utility functions, exception classes, and helper modules that support the core functionality of the Meta-Orchestrator service.

## 📁 Structure

```
utils/
├── __init__.py          # Utils package initialization
└── exceptions.py        # Custom exception classes
```

## 🚨 Exception Classes (`exceptions.py`)

Custom exception hierarchy for the Meta-Orchestrator service:

```python
from typing import Dict, Any, Optional

class MetaOrchestratorError(Exception):
    """Base exception for all Meta-Orchestrator errors"""

    def __init__(self, message: str, error_code: str = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "exception_type": self.__class__.__name__
        }

class ServiceError(MetaOrchestratorError):
    """Base class for service-related errors"""
    pass

class ServiceNotFoundError(ServiceError):
    """Raised when a requested service is not found"""

    def __init__(self, service_name: str):
        super().__init__(
            f"Service '{service_name}' not found",
            error_code="SERVICE_NOT_FOUND",
            details={"service_name": service_name}
        )

class ServiceOperationError(ServiceError):
    """Raised when a service operation fails"""

    def __init__(self, service_name: str, operation: str, reason: str = None):
        message = f"Operation '{operation}' failed for service '{service_name}'"
        if reason:
            message += f": {reason}"

        super().__init__(
            message,
            error_code="SERVICE_OPERATION_FAILED",
            details={
                "service_name": service_name,
                "operation": operation,
                "reason": reason
            }
        )

class DependencyError(ServiceError):
    """Raised when service dependency issues occur"""

    def __init__(self, service_name: str, dependency: str, issue: str):
        super().__init__(
            f"Dependency issue for service '{service_name}': {issue}",
            error_code="DEPENDENCY_ERROR",
            details={
                "service_name": service_name,
                "dependency": dependency,
                "issue": issue
            }
        )

class CircularDependencyError(DependencyError):
    """Raised when circular dependencies are detected"""

    def __init__(self, service_name: str, cycle: list):
        cycle_str = " -> ".join(cycle + [cycle[0]])
        super().__init__(
            service_name,
            "",
            f"Circular dependency detected: {cycle_str}"
        )
        self.cycle = cycle

class ConfigurationError(MetaOrchestratorError):
    """Base class for configuration-related errors"""
    pass

class ConfigurationValidationError(ConfigurationError):
    """Raised when configuration validation fails"""

    def __init__(self, service_name: str, validation_errors: list):
        super().__init__(
            f"Configuration validation failed for service '{service_name}'",
            error_code="CONFIG_VALIDATION_FAILED",
            details={
                "service_name": service_name,
                "validation_errors": validation_errors
            }
        )

class ConfigurationNotFoundError(ConfigurationError):
    """Raised when configuration is not found"""

    def __init__(self, service_name: str, config_type: str = None):
        message = f"Configuration not found for service '{service_name}'"
        if config_type:
            message += f" ({config_type})"

        super().__init__(
            message,
            error_code="CONFIG_NOT_FOUND",
            details={
                "service_name": service_name,
                "config_type": config_type
            }
        )

class DockerError(MetaOrchestratorError):
    """Base class for Docker-related errors"""
    pass

class DockerOperationError(DockerError):
    """Raised when Docker operations fail"""

    def __init__(self, operation: str, container_name: str = None, reason: str = None):
        message = f"Docker operation '{operation}' failed"
        if container_name:
            message += f" for container '{container_name}'"
        if reason:
            message += f": {reason}"

        details = {"operation": operation}
        if container_name:
            details["container_name"] = container_name
        if reason:
            details["reason"] = reason

        super().__init__(message, error_code="DOCKER_OPERATION_FAILED", details=details)

class DockerConnectionError(DockerError):
    """Raised when Docker daemon connection fails"""

    def __init__(self, reason: str = None):
        message = "Failed to connect to Docker daemon"
        if reason:
            message += f": {reason}"

        super().__init__(
            message,
            error_code="DOCKER_CONNECTION_FAILED",
            details={"reason": reason}
        )

class MonitoringError(MetaOrchestratorError):
    """Base class for monitoring-related errors"""
    pass

class HealthCheckError(MonitoringError):
    """Raised when health checks fail"""

    def __init__(self, service_name: str, endpoint: str, reason: str):
        super().__init__(
            f"Health check failed for service '{service_name}'",
            error_code="HEALTH_CHECK_FAILED",
            details={
                "service_name": service_name,
                "endpoint": endpoint,
                "reason": reason
            }
        )

class DriftDetectionError(MonitoringError):
    """Raised when configuration drift detection fails"""

    def __init__(self, reason: str, service_name: str = None):
        message = "Configuration drift detection failed"
        if service_name:
            message += f" for service '{service_name}'"
        if reason:
            message += f": {reason}"

        details = {"reason": reason}
        if service_name:
            details["service_name"] = service_name

        super().__init__(message, error_code="DRIFT_DETECTION_FAILED", details=details)

class AuditError(MetaOrchestratorError):
    """Base class for audit-related errors"""
    pass

class ValidationError(MetaOrchestratorError):
    """Base class for validation errors"""
    pass

class SecurityError(MetaOrchestratorError):
    """Base class for security-related errors"""
    pass

class AuthenticationError(SecurityError):
    """Raised when authentication fails"""

    def __init__(self, reason: str = None):
        message = "Authentication failed"
        if reason:
            message += f": {reason}"

        super().__init__(message, error_code="AUTHENTICATION_FAILED", details={"reason": reason})

class AuthorizationError(SecurityError):
    """Raised when authorization fails"""

    def __init__(self, user: str, operation: str, resource: str = None):
        message = f"Authorization failed for user '{user}' attempting operation '{operation}'"
        if resource:
            message += f" on resource '{resource}'"

        details = {"user": user, "operation": operation}
        if resource:
            details["resource"] = resource

        super().__init__(message, error_code="AUTHORIZATION_FAILED", details=details)

class RateLimitError(SecurityError):
    """Raised when rate limits are exceeded"""

    def __init__(self, limit: int, window_seconds: int, retry_after: int = None):
        message = f"Rate limit exceeded: {limit} requests per {window_seconds} seconds"
        details = {
            "limit": limit,
            "window_seconds": window_seconds,
            "retry_after": retry_after
        }

        super().__init__(message, error_code="RATE_LIMIT_EXCEEDED", details=details)
```

## 🔧 Utility Functions

### Common Utility Functions

While the current utils package primarily contains exceptions, here are examples of utility functions that would typically be included:

```python
# utils/helpers.py
import re
import time
from typing import Dict, Any, Optional
from pathlib import Path

def validate_service_name(name: str) -> bool:
    """Validate service name format"""
    # Service names must be alphanumeric with dashes and underscores
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-_]*$'
    return bool(re.match(pattern, name)) and len(name) <= 63

def normalize_port_mapping(port_str: str) -> tuple[int, int]:
    """Normalize port mapping string to (host_port, container_port)"""
    if ':' in port_str:
        host_port, container_port = port_str.split(':', 1)
        return int(host_port), int(container_port)
    else:
        port = int(port_str)
        return port, port

def calculate_uptime(start_time: float) -> str:
    """Calculate uptime from start timestamp"""
    elapsed = time.time() - start_time
    days, remainder = divmod(int(elapsed), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)

def deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result

def find_files_by_pattern(directory: Path, pattern: str) -> list[Path]:
    """Find files matching a pattern in directory"""
    import glob
    return [Path(f) for f in glob.glob(str(directory / pattern), recursive=True)]

def safe_get_nested_value(data: Dict[str, Any], keys: list, default=None):
    """Safely get nested dictionary value"""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def generate_operation_id(prefix: str = "op") -> str:
    """Generate unique operation ID"""
    import uuid
    return f"{prefix}_{int(time.time())}_{str(uuid.uuid4())[:8]}"

def format_bytes(size: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return ".1f"
        size /= 1024.0
    return ".1f"

def parse_duration(duration_str: str) -> int:
    """Parse duration string to seconds (e.g., '5m', '1h30m', '300s')"""
    import re

    total_seconds = 0
    pattern = r'(\d+)([smhd])'
    matches = re.findall(pattern, duration_str.lower())

    multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}

    for value, unit in matches:
        total_seconds += int(value) * multipliers.get(unit, 1)

    return total_seconds
```

### Docker Utilities

```python
# utils/docker.py
import docker
from typing import Dict, List, Optional, Any

class DockerUtils:
    """Docker-related utility functions"""

    def __init__(self):
        self.client = docker.from_env()

    def get_container_stats(self, container_name: str) -> Optional[Dict[str, Any]]:
        """Get container resource statistics"""
        try:
            container = self.client.containers.get(container_name)
            stats = container.stats(stream=False)

            cpu_stats = stats['cpu_stats']
            precpu_stats = stats['precpu_stats']

            # Calculate CPU usage percentage
            cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
            system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0

            # Calculate memory usage
            memory_stats = stats['memory_stats']
            memory_usage = memory_stats['usage']
            memory_limit = memory_stats['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0

            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage': memory_usage,
                'memory_limit': memory_limit,
                'memory_percent': round(memory_percent, 2),
                'network_rx': stats.get('networks', {}).get('eth0', {}).get('rx_bytes', 0),
                'network_tx': stats.get('networks', {}).get('eth0', {}).get('tx_bytes', 0)
            }
        except Exception:
            return None

    def get_container_logs(self, container_name: str, lines: int = 100,
                          since: Optional[str] = None) -> List[str]:
        """Get container logs"""
        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=lines, since=since, timestamps=True)
            return logs.decode('utf-8').strip().split('\n')
        except Exception:
            return []

    def inspect_container(self, container_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed container information"""
        try:
            container = self.client.containers.get(container_name)
            return container.attrs
        except Exception:
            return None

    def list_containers(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List containers with optional filters"""
        try:
            containers = self.client.containers.list(filters=filters or {})
            return [{
                'id': c.id,
                'name': c.name,
                'image': c.image.tags[0] if c.image.tags else c.image.id,
                'status': c.status,
                'ports': c.ports
            } for c in containers]
        except Exception:
            return []

    def check_docker_connectivity(self) -> bool:
        """Check if Docker daemon is accessible"""
        try:
            self.client.ping()
            return True
        except Exception:
            return False
```

### Configuration Utilities

```python
# utils/config.py
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigUtils:
    """Configuration file utilities"""

    @staticmethod
    def load_yaml_config(file_path: Path) -> Dict[str, Any]:
        """Load YAML configuration file"""
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def save_yaml_config(file_path: Path, config: Dict[str, Any]) -> None:
        """Save configuration to YAML file"""
        with open(file_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    @staticmethod
    def load_json_config(file_path: Path) -> Dict[str, Any]:
        """Load JSON configuration file"""
        with open(file_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def save_json_config(file_path: Path, config: Dict[str, Any]) -> None:
        """Save configuration to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2, sort_keys=False)

    @staticmethod
    def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries"""
        result = {}
        for config in configs:
            result = deep_merge_dicts(result, config)
        return result

    @staticmethod
    def validate_config_schema(config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate configuration against schema"""
        errors = []

        def validate_value(path: str, value: Any, schema_def: Dict[str, Any]):
            if 'type' in schema_def:
                expected_type = schema_def['type']
                if expected_type == 'string' and not isinstance(value, str):
                    errors.append(f"{path}: expected string, got {type(value).__name__}")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"{path}: expected number, got {type(value).__name__}")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"{path}: expected boolean, got {type(value).__name__}")
                elif expected_type == 'array' and not isinstance(value, list):
                    errors.append(f"{path}: expected array, got {type(value).__name__}")
                elif expected_type == 'object' and not isinstance(value, dict):
                    errors.append(f"{path}: expected object, got {type(value).__name__}")

            if 'required' in schema_def and schema_def['required'] and value is None:
                errors.append(f"{path}: required field is missing")

            if 'pattern' in schema_def and isinstance(value, str):
                import re
                if not re.match(schema_def['pattern'], value):
                    errors.append(f"{path}: value does not match pattern {schema_def['pattern']}")

        def validate_object(path: str, obj: Dict[str, Any], schema_def: Dict[str, Any]):
            if 'properties' in schema_def:
                properties = schema_def['properties']
                for key, value in obj.items():
                    if key in properties:
                        validate_value(f"{path}.{key}", value, properties[key])
                    else:
                        errors.append(f"{path}.{key}: unexpected property")

                # Check required properties
                required = schema_def.get('required', [])
                for req in required:
                    if req not in obj:
                        errors.append(f"{path}.{req}: required property missing")

        if isinstance(config, dict):
            validate_object('', config, schema)

        return errors
```

### Logging Utilities

```python
# utils/logging.py
import logging
import sys
from typing import Optional
from pathlib import Path

class LoggerUtils:
    """Logging configuration utilities"""

    @staticmethod
    def setup_structured_logging(
        level: str = "INFO",
        log_file: Optional[Path] = None,
        json_format: bool = True
    ) -> logging.Logger:
        """Set up structured logging"""

        # Create logger
        logger = logging.getLogger('meta-orchestrator')
        logger.setLevel(getattr(logging, level.upper()))

        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create formatter
        if json_format:
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s", '
                '"module": "%(module)s", "function": "%(funcName)s", '
                '"line": %(lineno)d, "extra": %(extra)s}'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    @staticmethod
    def create_correlation_logger(base_logger: logging.Logger, correlation_id: str):
        """Create logger with correlation ID"""
        return CorrelationLogger(base_logger, correlation_id)

class CorrelationLogger:
    """Logger that includes correlation ID in all log entries"""

    def __init__(self, base_logger: logging.Logger, correlation_id: str):
        self.base_logger = base_logger
        self.correlation_id = correlation_id

    def _log(self, level: str, message: str, extra: Optional[dict] = None):
        """Log message with correlation ID"""
        extra = extra or {}
        extra['correlation_id'] = self.correlation_id
        getattr(self.base_logger, level.lower())(message, extra=extra)

    def debug(self, message: str, extra: Optional[dict] = None):
        self._log('DEBUG', message, extra)

    def info(self, message: str, extra: Optional[dict] = None):
        self._log('INFO', message, extra)

    def warning(self, message: str, extra: Optional[dict] = None):
        self._log('WARNING', message, extra)

    def error(self, message: str, extra: Optional[dict] = None):
        self._log('ERROR', message, extra)

    def critical(self, message: str, extra: Optional[dict] = None):
        self._log('CRITICAL', message, extra)
```

## 🔄 Async Utilities

```python
# utils/async_utils.py
import asyncio
from typing import List, Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import functools

class AsyncUtils:
    """Async utility functions"""

    @staticmethod
    async def run_in_executor(func: Callable, *args, **kwargs) -> Any:
        """Run blocking function in thread pool executor"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

    @staticmethod
    async def gather_with_concurrency(n: int, *tasks: List[Callable]) -> List[Any]:
        """Run tasks with limited concurrency"""
        semaphore = asyncio.Semaphore(n)

        async def run_with_semaphore(task):
            async with semaphore:
                return await task

        return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])

    @staticmethod
    async def timeout_wrapper(coro: Callable, timeout: float, default=None):
        """Wrap coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            return default

    @staticmethod
    def create_task_with_callback(coro: Callable, callback: Callable) -> asyncio.Task:
        """Create task with completion callback"""
        task = asyncio.create_task(coro)

        def done_callback(task):
            try:
                result = task.result()
                callback(result, None)
            except Exception as e:
                callback(None, e)

        task.add_done_callback(done_callback)
        return task

    @staticmethod
    async def retry_async(coro: Callable, max_attempts: int = 3,
                         delay: float = 1.0, backoff: float = 2.0) -> Any:
        """Retry async operation with exponential backoff"""
        attempt = 0
        current_delay = delay

        while attempt < max_attempts:
            try:
                return await coro()
            except Exception as e:
                attempt += 1
                if attempt >= max_attempts:
                    raise e

                await asyncio.sleep(current_delay)
                current_delay *= backoff
```

## 📊 Performance Utilities

```python
# utils/performance.py
import time
import psutil
from typing import Dict, Any, Callable
from functools import wraps
import tracemalloc

class PerformanceUtils:
    """Performance monitoring utilities"""

    @staticmethod
    def time_execution(func: Callable) -> Callable:
        """Decorator to time function execution"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                print(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return wrapper

    @staticmethod
    def memory_usage(func: Callable) -> Callable:
        """Decorator to monitor memory usage"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            process = psutil.Process()
            initial_memory = process.memory_info().rss

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                final_memory = process.memory_info().rss
                memory_used = final_memory - initial_memory
                print(f"{func.__name__} used {memory_used / 1024 / 1024:.2f} MB of memory")
        return wrapper

    @staticmethod
    def profile_memory(func: Callable) -> Callable:
        """Decorator to profile memory usage with tracemalloc"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracemalloc.start()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                current, peak = tracemalloc.get_traced_memory()
                print(f"{func.__name__} - Current memory: {current / 1024 / 1024:.2f} MB, "
                      f"Peak memory: {peak / 1024 / 1024:.2f} MB")
                tracemalloc.stop()
        return wrapper

    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """Get current system statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
```

This utils package provides essential exception classes and utility functions that support the robust operation of the Meta-Orchestrator service, promoting code reuse and maintainability across all components.
