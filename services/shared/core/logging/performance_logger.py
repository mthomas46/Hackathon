"""Performance Logger - Specialized logging for performance metrics and monitoring."""

import time
import asyncio
from typing import Dict, Any, Optional, Callable, TypeVar, Awaitable
from contextlib import asynccontextmanager
from functools import wraps

from .logger import get_logger
from ..di.services import ILoggerService

T = TypeVar('T')


class PerformanceLogger:
    """Performance logging utility for tracking operation metrics.

    This class provides:
    - Automatic timing of operations
    - Performance threshold monitoring
    - Memory usage tracking
    - Custom performance metrics
    - Async operation support
    - Structured performance data logging
    """

    def __init__(self, logger: Optional[ILoggerService] = None) -> None:
        """Initialize performance logger.

        Args:
            logger: Logger service instance (uses global logger if None)
        """
        self._logger = logger or get_logger()

    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """Log performance metric.

        Args:
            operation: Name of the operation
            duration: Duration in seconds
            **kwargs: Additional performance context
        """
        self._logger.log_performance(operation, duration, **kwargs)

    def time_operation(self, operation: str, **context) -> 'PerformanceTimer':
        """Create a performance timer for an operation.

        Args:
            operation: Name of the operation to time
            **context: Additional context for the performance log

        Returns:
            PerformanceTimer instance for timing the operation

        Example:
            with perf_logger.time_operation("database_query", query_type="select") as timer:
                result = db.execute_query("SELECT * FROM users")
                timer.add_context(rows_returned=len(result))
        """
        return PerformanceTimer(self, operation, **context)

    def time_async_operation(self, operation: str, **context) -> 'AsyncPerformanceTimer':
        """Create an async performance timer for an operation.

        Args:
            operation: Name of the operation to time
            **context: Additional context for the performance log

        Returns:
            AsyncPerformanceTimer instance for timing async operations

        Example:
            async with perf_logger.time_async_operation("api_call", endpoint="/users") as timer:
                result = await api_client.get_users()
                timer.add_context(user_count=len(result))
        """
        return AsyncPerformanceTimer(self, operation, **context)

    def time_function(self, operation: Optional[str] = None, **context):
        """Decorator to time function execution.

        Args:
            operation: Custom operation name (uses function name if None)
            **context: Additional context for performance logs

        Returns:
            Decorator function

        Example:
            @perf_logger.time_function(operation="user_validation")
            def validate_user(user_data):
                # validation logic here
                return True

            @perf_logger.time_function()  # Uses function name
            def process_data(data):
                # processing logic here
                return result
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            op_name = operation or f"{func.__module__}.{func.__qualname__}"

            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    with self.time_operation(op_name, **context) as timer:
                        result = await func(*args, **kwargs)
                        return result
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    with self.time_operation(op_name, **context) as timer:
                        result = func(*args, **kwargs)
                        return result
                return sync_wrapper

        return decorator

    def monitor_threshold(self, operation: str, threshold_seconds: float, **context) -> 'ThresholdTimer':
        """Monitor operation against performance threshold.

        Args:
            operation: Name of the operation
            threshold_seconds: Performance threshold in seconds
            **context: Additional context

        Returns:
            ThresholdTimer that logs warnings if threshold exceeded

        Example:
            with perf_logger.monitor_threshold("heavy_calculation", 5.0) as timer:
                result = perform_heavy_calculation()
        """
        return ThresholdTimer(self, operation, threshold_seconds, **context)


class PerformanceTimer:
    """Timer for synchronous operations with performance logging."""

    def __init__(self, perf_logger: PerformanceLogger, operation: str, **context) -> None:
        """Initialize performance timer.

        Args:
            perf_logger: Performance logger instance
            operation: Operation name
            **context: Additional context data
        """
        self._perf_logger = perf_logger
        self._operation = operation
        self._context = dict(context)
        self._start_time: Optional[float] = None
        self._additional_context: Dict[str, Any] = {}

    def __enter__(self):
        """Start timing operation."""
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log performance."""
        if self._start_time is not None:
            duration = time.perf_counter() - self._start_time
            self._log_performance(duration, exc_type is not None)

    def add_context(self, **kwargs) -> None:
        """Add additional context to the performance log.

        Args:
            **kwargs: Additional context data
        """
        self._additional_context.update(kwargs)

    def _log_performance(self, duration: float, had_error: bool) -> None:
        """Log performance data.

        Args:
            duration: Operation duration in seconds
            had_error: Whether operation had an error
        """
        context = {
            **self._context,
            **self._additional_context,
            "success": not had_error,
            "error_occurred": had_error
        }

        self._perf_logger.log_performance(self._operation, duration, **context)


class AsyncPerformanceTimer:
    """Timer for asynchronous operations with performance logging."""

    def __init__(self, perf_logger: PerformanceLogger, operation: str, **context) -> None:
        """Initialize async performance timer.

        Args:
            perf_logger: Performance logger instance
            operation: Operation name
            **context: Additional context data
        """
        self._perf_logger = perf_logger
        self._operation = operation
        self._context = dict(context)
        self._start_time: Optional[float] = None
        self._additional_context: Dict[str, Any] = {}

    async def __aenter__(self):
        """Start timing async operation."""
        self._start_time = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log async performance."""
        if self._start_time is not None:
            duration = time.perf_counter() - self._start_time
            had_error = exc_type is not None
            self._log_performance(duration, had_error)

    def add_context(self, **kwargs) -> None:
        """Add additional context to the performance log.

        Args:
            **kwargs: Additional context data
        """
        self._additional_context.update(kwargs)

    def _log_performance(self, duration: float, had_error: bool) -> None:
        """Log async performance data.

        Args:
            duration: Operation duration in seconds
            had_error: Whether operation had an error
        """
        context = {
            **self._context,
            **self._additional_context,
            "success": not had_error,
            "error_occurred": had_error,
            "async_operation": True
        }

        self._perf_logger.log_performance(self._operation, duration, **context)


class ThresholdTimer(PerformanceTimer):
    """Performance timer that monitors against thresholds."""

    def __init__(self, perf_logger: PerformanceLogger, operation: str,
                 threshold_seconds: float, **context) -> None:
        """Initialize threshold timer.

        Args:
            perf_logger: Performance logger instance
            operation: Operation name
            threshold_seconds: Performance threshold in seconds
            **context: Additional context data
        """
        super().__init__(perf_logger, operation, **context)
        self._threshold = threshold_seconds

    def _log_performance(self, duration: float, had_error: bool) -> None:
        """Log performance with threshold monitoring.

        Args:
            duration: Operation duration in seconds
            had_error: Whether operation had an error
        """
        # Add threshold information
        context = {
            **self._context,
            **self._additional_context,
            "success": not had_error,
            "error_occurred": had_error,
            "threshold_seconds": self._threshold,
            "threshold_exceeded": duration > self._threshold,
            "performance_ratio": duration / self._threshold if self._threshold > 0 else 0
        }

        # Log with appropriate level based on threshold
        if duration > self._threshold:
            # Log as warning if threshold exceeded
            self._perf_logger._logger.warning(
                f"Performance threshold exceeded: {self._operation}",
                operation=self._operation,
                duration_seconds=duration,
                threshold_seconds=self._threshold,
                excess_time=duration - self._threshold,
                **context
            )
        else:
            # Log as info if within threshold
            self._perf_logger.log_performance(self._operation, duration, **context)


# Global performance logger instance
_performance_logger: Optional[PerformanceLogger] = None


def get_performance_logger() -> PerformanceLogger:
    """Get global performance logger instance.

    Returns:
        Global performance logger instance
    """
    global _performance_logger
    if _performance_logger is None:
        _performance_logger = PerformanceLogger()
    return _performance_logger


# Convenience functions
def time_operation(operation: str, **context):
    """Convenience function to time an operation.

    Args:
        operation: Operation name
        **context: Additional context

    Returns:
        PerformanceTimer context manager

    Example:
        with time_operation("database_query", table="users"):
            result = db.query("SELECT * FROM users")
    """
    return get_performance_logger().time_operation(operation, **context)


def time_async_operation(operation: str, **context):
    """Convenience function to time an async operation.

    Args:
        operation: Operation name
        **context: Additional context

    Returns:
        AsyncPerformanceTimer context manager

    Example:
        async with time_async_operation("api_call", endpoint="/users"):
            result = await api.get_users()
    """
    return get_performance_logger().time_async_operation(operation, **context)


def monitor_performance(operation: str, threshold_seconds: float, **context):
    """Convenience function to monitor operation against threshold.

    Args:
        operation: Operation name
        threshold_seconds: Performance threshold in seconds
        **context: Additional context

    Returns:
        ThresholdTimer context manager

    Example:
        with monitor_performance("heavy_calculation", 5.0):
            result = perform_heavy_calculation()
    """
    return get_performance_logger().monitor_threshold(operation, threshold_seconds, **context)
