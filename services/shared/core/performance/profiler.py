"""Performance Profiler - Advanced profiling and performance monitoring tools."""

import time
import asyncio
import threading
import psutil
import tracemalloc
from typing import Dict, Any, Optional, List, Callable, TypeVar, Union
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
import gc
import sys
import os

from ..logging.logger import get_logger
from ..di.services import ILoggerService

T = TypeVar('T')


@dataclass
class PerformanceMetrics:
    """Performance metrics collected during profiling."""

    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    duration_ms: float = 0.0

    # CPU and Memory metrics
    cpu_percent_start: float = 0.0
    cpu_percent_end: float = 0.0
    memory_mb_start: float = 0.0
    memory_mb_end: float = 0.0
    memory_delta_mb: float = 0.0

    # System metrics
    thread_count: int = 0
    active_threads: int = 0

    # Custom metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    # Performance indicators
    is_slow: bool = False
    memory_leak_detected: bool = False
    high_cpu_usage: bool = False

    def complete(self) -> None:
        """Complete the performance measurement."""
        self.end_time = datetime.now(timezone.utc)
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            self.duration_seconds = duration.total_seconds()
            self.duration_ms = self.duration_seconds * 1000

        # Calculate deltas
        if self.memory_mb_end > 0:
            self.memory_delta_mb = self.memory_mb_end - self.memory_mb_start

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        return {
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "duration_ms": self.duration_ms,
            "cpu_percent_start": self.cpu_percent_start,
            "cpu_percent_end": self.cpu_percent_end,
            "memory_mb_start": self.memory_mb_start,
            "memory_mb_end": self.memory_mb_end,
            "memory_delta_mb": self.memory_delta_mb,
            "thread_count": self.thread_count,
            "active_threads": self.active_threads,
            "custom_metrics": self.custom_metrics,
            "performance_flags": {
                "is_slow": self.is_slow,
                "memory_leak_detected": self.memory_leak_detected,
                "high_cpu_usage": self.high_cpu_usage
            }
        }


class PerformanceProfiler:
    """Advanced performance profiler for synchronous operations."""

    def __init__(self,
                 logger: Optional[ILoggerService] = None,
                 slow_threshold_ms: float = 1000.0,
                 memory_threshold_mb: float = 50.0,
                 enable_memory_tracking: bool = True,
                 enable_cpu_tracking: bool = True) -> None:
        """Initialize performance profiler.

        Args:
            logger: Logger service for performance logging
            slow_threshold_ms: Threshold for slow operation detection (ms)
            memory_threshold_mb: Threshold for memory usage detection (MB)
            enable_memory_tracking: Enable memory usage tracking
            enable_cpu_tracking: Enable CPU usage tracking
        """
        self._logger = logger or get_logger()
        self._slow_threshold_ms = slow_threshold_ms
        self._memory_threshold_mb = memory_threshold_mb
        self._enable_memory_tracking = enable_memory_tracking
        self._enable_cpu_tracking = enable_cpu_tracking

        # Performance tracking
        self._current_metrics: Optional[PerformanceMetrics] = None
        self._performance_history: List[PerformanceMetrics] = []
        self._max_history_size = 1000

        # Memory tracking
        self._memory_tracking_enabled = False
        if enable_memory_tracking:
            try:
                tracemalloc.start()
                self._memory_tracking_enabled = True
            except Exception:
                pass  # Memory tracking not available

    def start_operation(self, operation_name: str, **context) -> PerformanceMetrics:
        """Start profiling an operation.

        Args:
            operation_name: Name of the operation being profiled
            **context: Additional context for the operation

        Returns:
            PerformanceMetrics object for tracking
        """
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=datetime.now(timezone.utc),
            custom_metrics=context
        )

        # Collect initial system metrics
        try:
            if self._enable_cpu_tracking:
                metrics.cpu_percent_start = psutil.cpu_percent(interval=None)
            if self._enable_memory_tracking:
                process = psutil.Process()
                metrics.memory_mb_start = process.memory_info().rss / (1024 * 1024)
        except Exception:
            pass  # System metrics not available

        # Thread information
        metrics.thread_count = threading.active_count()
        metrics.active_threads = len(threading.enumerate())

        self._current_metrics = metrics
        return metrics

    def end_operation(self, metrics: Optional[PerformanceMetrics] = None) -> PerformanceMetrics:
        """End profiling an operation.

        Args:
            metrics: PerformanceMetrics object to complete (uses current if None)

        Returns:
            Completed PerformanceMetrics object
        """
        if metrics is None:
            metrics = self._current_metrics

        if metrics is None:
            return PerformanceMetrics(operation_name="unknown")

        # Collect final system metrics
        try:
            if self._enable_cpu_tracking:
                metrics.cpu_percent_end = psutil.cpu_percent(interval=None)
            if self._enable_memory_tracking:
                process = psutil.Process()
                metrics.memory_mb_end = process.memory_info().rss / (1024 * 1024)
        except Exception:
            pass  # System metrics not available

        # Complete metrics
        metrics.complete()

        # Analyze performance
        self._analyze_performance(metrics)

        # Log performance data
        self._log_performance(metrics)

        # Store in history
        self._add_to_history(metrics)

        return metrics

    def _analyze_performance(self, metrics: PerformanceMetrics) -> None:
        """Analyze performance metrics and set flags.

        Args:
            metrics: Performance metrics to analyze
        """
        # Check for slow operations
        if metrics.duration_ms > self._slow_threshold_ms:
            metrics.is_slow = True

        # Check for memory issues
        if abs(metrics.memory_delta_mb) > self._memory_threshold_mb:
            metrics.memory_leak_detected = True

        # Check for high CPU usage
        if metrics.cpu_percent_end > 80.0:
            metrics.high_cpu_usage = True

    def _log_performance(self, metrics: PerformanceMetrics) -> None:
        """Log performance metrics.

        Args:
            metrics: Performance metrics to log
        """
        log_data = metrics.to_dict()

        if metrics.is_slow or metrics.memory_leak_detected or metrics.high_cpu_usage:
            self._logger.warning(
                f"Performance issue detected: {metrics.operation_name}",
                operation=metrics.operation_name,
                duration_ms=metrics.duration_ms,
                memory_delta_mb=metrics.memory_delta_mb,
                cpu_percent=metrics.cpu_percent_end,
                **log_data
            )
        else:
            self._logger.info(
                f"Performance: {metrics.operation_name}",
                operation=metrics.operation_name,
                duration_ms=metrics.duration_ms,
                **log_data
            )

    def _add_to_history(self, metrics: PerformanceMetrics) -> None:
        """Add metrics to performance history.

        Args:
            metrics: Performance metrics to store
        """
        self._performance_history.append(metrics)

        # Maintain history size limit
        if len(self._performance_history) > self._max_history_size:
            self._performance_history.pop(0)

    @contextmanager
    def profile_operation(self, operation_name: str, **context):
        """Context manager for profiling operations.

        Args:
            operation_name: Name of the operation
            **context: Additional context

        Yields:
            PerformanceMetrics object
        """
        metrics = self.start_operation(operation_name, **context)
        try:
            yield metrics
        finally:
            self.end_operation(metrics)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from history.

        Returns:
            Dictionary with performance statistics
        """
        if not self._performance_history:
            return {"total_operations": 0, "stats": {}}

        durations = [m.duration_ms for m in self._performance_history]
        memory_deltas = [m.memory_delta_mb for m in self._performance_history]

        return {
            "total_operations": len(self._performance_history),
            "duration_stats": {
                "min": min(durations) if durations else 0,
                "max": max(durations) if durations else 0,
                "avg": sum(durations) / len(durations) if durations else 0,
                "slow_operations": len([d for d in durations if d > self._slow_threshold_ms])
            },
            "memory_stats": {
                "min_delta": min(memory_deltas) if memory_deltas else 0,
                "max_delta": max(memory_deltas) if memory_deltas else 0,
                "avg_delta": sum(memory_deltas) / len(memory_deltas) if memory_deltas else 0,
                "memory_issues": len([d for d in memory_deltas if abs(d) > self._memory_threshold_mb])
            }
        }

    def clear_history(self) -> None:
        """Clear performance history."""
        self._performance_history.clear()


class AsyncProfiler(PerformanceProfiler):
    """Performance profiler for asynchronous operations."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize async performance profiler."""
        super().__init__(*args, **kwargs)

    @asynccontextmanager
    async def profile_async_operation(self, operation_name: str, **context):
        """Async context manager for profiling operations.

        Args:
            operation_name: Name of the operation
            **context: Additional context

        Yields:
            PerformanceMetrics object
        """
        metrics = self.start_operation(operation_name, **context)
        try:
            yield metrics
        finally:
            self.end_operation(metrics)

    async def profile_async_function(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Profile an async function execution.

        Args:
            func: Async function to profile
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Function result
        """
        operation_name = f"{func.__module__}.{func.__qualname__}"

        async with self.profile_async_operation(operation_name):
            return await func(*args, **kwargs)


# Global profiler instances
_sync_profiler: Optional[PerformanceProfiler] = None
_async_profiler: Optional[AsyncProfiler] = None


def get_sync_profiler() -> PerformanceProfiler:
    """Get global synchronous profiler instance."""
    global _sync_profiler
    if _sync_profiler is None:
        _sync_profiler = PerformanceProfiler()
    return _sync_profiler


def get_async_profiler() -> AsyncProfiler:
    """Get global asynchronous profiler instance."""
    global _async_profiler
    if _async_profiler is None:
        _async_profiler = AsyncProfiler()
    return _async_profiler


# Convenience functions
def profile_operation(operation_name: str, **context):
    """Profile a synchronous operation.

    Args:
        operation_name: Name of the operation
        **context: Additional context

    Returns:
        Context manager for profiling
    """
    return get_sync_profiler().profile_operation(operation_name, **context)


def profile_async_operation(operation_name: str, **context):
    """Profile an asynchronous operation.

    Args:
        operation_name: Name of the operation
        **context: Additional context

    Returns:
        Async context manager for profiling
    """
    return get_async_profiler().profile_async_operation(operation_name, **context)
