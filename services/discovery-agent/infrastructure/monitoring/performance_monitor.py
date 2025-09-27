"""Performance monitoring utilities for discovery agent."""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    operation_name: str
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Resource usage
    cpu_percent_start: float = 0.0
    cpu_percent_end: float = 0.0
    memory_mb_start: float = 0.0
    memory_mb_end: float = 0.0

    # Operation metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None

    def complete(self, success: bool = True, error_message: str = None) -> None:
        """Mark the operation as completed."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.cpu_percent_end = psutil.cpu_percent(interval=None)
        self.memory_mb_end = psutil.virtual_memory().used / 1024 / 1024
        self.success = success
        if error_message:
            self.error_message = error_message

    @property
    def cpu_usage_delta(self) -> float:
        """Get CPU usage change during operation."""
        return self.cpu_percent_end - self.cpu_percent_start

    @property
    def memory_delta_mb(self) -> float:
        """Get memory usage change during operation."""
        return self.memory_mb_end - self.memory_mb_start

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "cpu_percent_start": self.cpu_percent_start,
            "cpu_percent_end": self.cpu_percent_end,
            "memory_mb_start": self.memory_mb_start,
            "memory_mb_end": self.memory_mb_end,
            "cpu_usage_delta": self.cpu_usage_delta,
            "memory_delta_mb": self.memory_delta_mb,
            "metadata": self.metadata,
            "success": self.success,
            "error_message": self.error_message,
        }


class PerformanceMonitor:
    """Performance monitoring utility for discovery operations."""

    def __init__(self):
        """Initialize performance monitor."""
        self._metrics_history: List[PerformanceMetrics] = []
        self._lock = threading.Lock()
        self._system_baseline = self._capture_system_metrics()

    def _capture_system_metrics(self) -> Dict[str, float]:
        """Capture current system metrics as baseline."""
        memory = psutil.virtual_memory()
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_used_mb": memory.used / 1024 / 1024,
            "memory_available_mb": memory.available / 1024 / 1024,
            "memory_percent": memory.percent,
        }

    @contextmanager
    def monitor_operation(self, operation_name: str, metadata: Dict[str, Any] = None):
        """Context manager to monitor an operation's performance."""
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            cpu_percent_start=self._system_baseline["cpu_percent"],
            memory_mb_start=self._system_baseline["memory_used_mb"],
            metadata=metadata or {}
        )

        start_time = time.time()
        try:
            yield metrics
            metrics.complete(success=True)
        except Exception as e:
            duration = time.time() - start_time
            metrics.complete(success=False, error_message=str(e))
            logger.warning(f"Operation '{operation_name}' failed after {duration:.2f}s: {e}")
            raise
        finally:
            with self._lock:
                self._metrics_history.append(metrics)

    def get_recent_metrics(self, limit: int = 10) -> List[PerformanceMetrics]:
        """Get recent performance metrics."""
        with self._lock:
            return self._metrics_history[-limit:] if limit > 0 else self._metrics_history

    def get_operation_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get statistics for a specific operation type."""
        with self._lock:
            relevant_metrics = [m for m in self._metrics_history if m.operation_name == operation_name]

        if not relevant_metrics:
            return {"operation": operation_name, "count": 0}

        successful_metrics = [m for m in relevant_metrics if m.success]

        return {
            "operation": operation_name,
            "count": len(relevant_metrics),
            "success_count": len(successful_metrics),
            "success_rate": len(successful_metrics) / len(relevant_metrics) if relevant_metrics else 0,
            "avg_duration": sum(m.duration_seconds for m in successful_metrics) / len(successful_metrics) if successful_metrics else 0,
            "max_duration": max((m.duration_seconds for m in successful_metrics), default=0),
            "min_duration": min((m.duration_seconds for m in successful_metrics), default=0),
            "avg_cpu_delta": sum(m.cpu_usage_delta for m in successful_metrics) / len(successful_metrics) if successful_metrics else 0,
            "avg_memory_delta_mb": sum(m.memory_delta_mb for m in successful_metrics) / len(successful_metrics) if successful_metrics else 0,
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health metrics."""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_used_mb": memory.used / 1024 / 1024,
            "memory_available_mb": memory.available / 1024 / 1024,
            "memory_percent": memory.percent,
            "disk_used_gb": disk.used / 1024 / 1024 / 1024,
            "disk_free_gb": disk.free / 1024 / 1024 / 1024,
            "disk_percent": disk.percent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def clear_history(self, older_than_hours: int = 24) -> int:
        """Clear old metrics history."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)

        with self._lock:
            old_count = len(self._metrics_history)
            self._metrics_history = [
                m for m in self._metrics_history
                if m.start_time > cutoff_time
            ]
            return old_count - len(self._metrics_history)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        with self._lock:
            total_operations = len(self._metrics_history)
            successful_operations = len([m for m in self._metrics_history if m.success])

        system_health = self.get_system_health()

        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "system_health": system_health,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_async_operation(operation_name: str):
    """Decorator to monitor async operation performance."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with performance_monitor.monitor_operation(operation_name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def monitor_sync_operation(operation_name: str):
    """Decorator to monitor sync operation performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with performance_monitor.monitor_operation(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
