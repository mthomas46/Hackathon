"""Metrics utilities for CLI operations."""

from typing import Dict, Any
from services.shared.logging import fire_and_forget
import time


def log_cli_operation(operation: str, success: bool = True, duration: float = 0.0, **context):
    """Log CLI operation metrics."""
    log_data = {
        'operation': operation,
        'success': success,
        'duration_ms': duration * 1000,
        'service': 'cli',
        'timestamp': time.time()
    }
    log_data.update(context)

    fire_and_forget("info", f"CLI operation: {operation}", "cli", log_data)


def log_cli_command(command: str, args: Dict[str, Any] = None, **context):
    """Log CLI command execution."""
    log_data = {
        'command': command,
        'args': args or {},
        'service': 'cli',
        'timestamp': time.time()
    }
    log_data.update(context)

    fire_and_forget("info", f"CLI command: {command}", "cli", log_data)


def create_operation_timer():
    """Create a context manager for timing operations."""
    class OperationTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.end_time = time.time()

        def get_duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

    return OperationTimer()


def track_api_call(endpoint: str, method: str = 'GET', success: bool = True, duration: float = 0.0, **context):
    """Track API call metrics."""
    log_data = {
        'api_endpoint': endpoint,
        'method': method,
        'success': success,
        'duration_ms': duration * 1000,
        'service': 'cli',
        'timestamp': time.time()
    }
    log_data.update(context)

    fire_and_forget("info", f"CLI API call: {method} {endpoint}", "cli", log_data)


def track_cache_operation(operation: str, cache_key: str, hit: bool = True, **context):
    """Track cache operation metrics."""
    log_data = {
        'cache_operation': operation,
        'cache_key': cache_key,
        'hit': hit,
        'service': 'cli',
        'timestamp': time.time()
    }
    log_data.update(context)

    fire_and_forget("info", f"CLI cache {operation}: {cache_key}", "cli", log_data)


def create_metrics_summary() -> Dict[str, Any]:
    """Create a summary of CLI metrics (placeholder for future implementation)."""
    # This would typically aggregate metrics from a metrics store
    return {
        'total_operations': 0,
        'successful_operations': 0,
        'failed_operations': 0,
        'average_duration_ms': 0.0,
        'popular_commands': [],
        'error_rate': 0.0
    }
