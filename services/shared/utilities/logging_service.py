"""Advanced Logging Service with correlation IDs, structured logging, and error tracking.

Provides comprehensive logging infrastructure for the ecosystem with:
- Correlation ID tracking across service calls
- Structured logging with context
- Error aggregation and alerting
- Performance monitoring
- Centralized log management
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
import traceback
import uuid
from collections import defaultdict, deque
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

# Correlation ID context variable
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


@dataclass
class LogEntry:
    """Structured log entry."""

    timestamp: float
    level: str
    message: str
    correlation_id: Optional[str]
    service_name: str
    operation: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    performance_data: Optional[Dict[str, Any]] = None


@dataclass
class ErrorAggregation:
    """Aggregated error information."""

    error_type: str
    message_pattern: str
    count: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    affected_services: set = field(default_factory=set)
    severity: str = "low"  # low, medium, high, critical


class StructuredLogger(logging.Logger):
    """Enhanced logger with structured logging and correlation ID support."""

    def __init__(self, name: str, service_name: str = "unknown"):
        super().__init__(name)
        self.service_name = service_name

    def _log_with_context(
        self,
        level: int,
        msg: str,
        args,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
        correlation_id=None,
        operation=None,
        user_id=None,
        session_id=None,
        request_id=None,
        performance_data=None,
        **kwargs,
    ):
        """Log with additional context."""
        # Get correlation ID from context or parameter
        corr_id = correlation_id or correlation_id_var.get()

        # Create structured extra data
        structured_extra = {
            "correlation_id": corr_id,
            "service_name": self.service_name,
            "operation": operation,
            "user_id": user_id,
            "session_id": session_id,
            "request_id": request_id,
            "performance_data": performance_data,
            "timestamp": time.time(),
            **(extra or {}),
            **kwargs,
        }

        # Add stack trace for errors
        if level >= logging.ERROR and exc_info:
            structured_extra["stack_trace"] = "".join(traceback.format_exception(*exc_info))

        super()._log(level, msg, args, exc_info, structured_extra, stack_info, stacklevel)

    def info_with_context(self, msg: str, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, msg, (), **kwargs)

    def error_with_context(self, msg: str, **kwargs):
        """Log error message with context."""
        self._log_with_context(logging.ERROR, msg, (), **kwargs)

    def warning_with_context(self, msg: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, msg, (), **kwargs)

    def debug_with_context(self, msg: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, msg, (), **kwargs)


class CorrelationContextManager:
    """Context manager for correlation ID management."""

    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self._token = None

    def __enter__(self):
        self._token = correlation_id_var.set(self.correlation_id)
        return self.correlation_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token is not None:
            correlation_id_var.reset(self._token)


class LoggingService:
    """Centralized logging service with monitoring and alerting."""

    def __init__(self):
        self._loggers: Dict[str, StructuredLogger] = {}
        self._error_aggregator = defaultdict(ErrorAggregation)
        self._performance_monitor = defaultdict(list)  # operation -> list of durations
        self._alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self._log_queue: deque = deque(maxlen=10000)  # Circular buffer for recent logs
        self._lock = threading.Lock()
        self._error_thresholds = {
            "high_frequency": 10,  # errors per minute
            "critical_errors": ["ConnectionError", "TimeoutError", "DatabaseError"],
        }

        # Integration with centralized logging
        self._centralized_logging = None
        self._forward_to_centralized = True

        # Try to initialize centralized logging integration
        try:
            from .centralized_logging_service import get_centralized_logging_service

            self._centralized_logging = get_centralized_logging_service()
        except ImportError:
            logger.warning("Centralized logging service not available")

    def get_logger(self, name: str, service_name: str = "unknown") -> StructuredLogger:
        """Get or create a structured logger."""
        if name not in self._loggers:
            logger = StructuredLogger(name, service_name)
            logger.setLevel(logging.INFO)

            # Add console handler with structured formatting
            handler = logging.StreamHandler(sys.stdout)
            formatter = StructuredFormatter()
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            self._loggers[name] = logger

        return self._loggers[name]

    def log_performance(self, operation: str, duration: float, metadata: Optional[Dict[str, Any]] = None):
        """Log performance metrics."""
        with self._lock:
            self._performance_monitor[operation].append((time.time(), duration))

            # Keep only last 1000 measurements per operation
            if len(self._performance_monitor[operation]) > 1000:
                self._performance_monitor[operation].pop(0)

            # Check for performance degradation
            recent_measurements = [d for _, d in self._performance_monitor[operation][-50:]]
            if len(recent_measurements) >= 10:
                avg_duration = sum(recent_measurements) / len(recent_measurements)
                if avg_duration > 5.0:  # 5 second threshold
                    self._trigger_alert(
                        "performance_degradation",
                        {
                            "operation": operation,
                            "average_duration": avg_duration,
                            "sample_size": len(recent_measurements),
                            "metadata": metadata,
                        },
                    )

    async def log_error(self, error_type: str, message: str, service_name: str, correlation_id: Optional[str] = None):
        """Log and aggregate errors."""
        with self._lock:
            key = f"{error_type}:{message[:100]}"  # Truncate long messages

            if key not in self._error_aggregator:
                self._error_aggregator[key] = ErrorAggregation(error_type=error_type, message_pattern=message[:200])

            aggregation = self._error_aggregator[key]
            aggregation.count += 1
            aggregation.last_seen = time.time()
            aggregation.affected_services.add(service_name)

            # Determine severity
            if error_type in self._error_thresholds["critical_errors"]:
                aggregation.severity = "critical"
            elif aggregation.count > 100:
                aggregation.severity = "high"
            elif aggregation.count > 20:
                aggregation.severity = "medium"

            # Check for high-frequency errors
            time_window = 60  # 1 minute
            recent_errors = [
                agg for agg in self._error_aggregator.values() if time.time() - agg.last_seen < time_window
            ]

            if len(recent_errors) > self._error_thresholds["high_frequency"]:
                self._trigger_alert(
                    "high_error_frequency",
                    {
                        "error_count": len(recent_errors),
                        "time_window_seconds": time_window,
                        "recent_errors": [agg.error_type for agg in recent_errors[:5]],
                    },
                )

            # Forward error to centralized logging
            await self._forward_log_to_centralized(
                {
                    "timestamp": time.time(),
                    "level": "ERROR",
                    "service_name": service_name,
                    "message": message,
                    "correlation_id": correlation_id,
                    "operation": "error_logging",
                    "extra_data": {
                        "error_type": error_type,
                        "severity": aggregation.severity,
                        "error_count": aggregation.count,
                    },
                    "tags": ["error", error_type.lower()],
                }
            )

    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Add callback for alerts."""
        self._alert_callbacks.append(callback)

    def _trigger_alert(self, alert_type: str, data: Dict[str, Any]):
        """Trigger alerts to all registered callbacks."""
        for callback in self._alert_callbacks:
            try:
                callback(alert_type, data)
            except Exception as e:
                print(f"Alert callback failed: {e}")

    async def _forward_log_to_centralized(self, log_data: Dict[str, Any]):
        """Forward log entry to centralized logging service."""
        if self._forward_to_centralized and self._centralized_logging:
            try:
                await self._centralized_logging.store_log_entry(log_data)
            except Exception as e:
                logger.debug(f"Failed to forward log to centralized logging: {e}")

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error aggregations."""
        with self._lock:
            return {
                "total_unique_errors": len(self._error_aggregator),
                "errors_by_severity": {
                    "critical": len([e for e in self._error_aggregator.values() if e.severity == "critical"]),
                    "high": len([e for e in self._error_aggregator.values() if e.severity == "high"]),
                    "medium": len([e for e in self._error_aggregator.values() if e.severity == "medium"]),
                    "low": len([e for e in self._error_aggregator.values() if e.severity == "low"]),
                },
                "most_frequent_errors": sorted(
                    [(k, v.count) for k, v in self._error_aggregator.items()], key=lambda x: x[1], reverse=True
                )[:10],
            }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        with self._lock:
            summary = {}
            for operation, measurements in self._performance_monitor.items():
                if measurements:
                    durations = [d for _, d in measurements]
                    summary[operation] = {
                        "count": len(durations),
                        "avg_duration": sum(durations) / len(durations),
                        "min_duration": min(durations),
                        "max_duration": max(durations),
                        "p95_duration": sorted(durations)[int(len(durations) * 0.95)],
                    }
            return summary

    def export_logs(self, format: str = "json") -> str:
        """Export recent logs in specified format."""
        with self._lock:
            logs = list(self._log_queue)

        if format == "json":
            return json.dumps([log.__dict__ if hasattr(log, "__dict__") else str(log) for log in logs], indent=2)
        else:
            return "\n".join(str(log) for log in logs)


class StructuredFormatter(logging.Formatter):
    """Structured log formatter for JSON output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Extract structured fields
        structured_data = {
            "timestamp": record.created,
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "correlation_id": getattr(record, "correlation_id", None),
            "service_name": getattr(record, "service_name", None),
            "operation": getattr(record, "operation", None),
            "user_id": getattr(record, "user_id", None),
            "session_id": getattr(record, "session_id", None),
            "request_id": getattr(record, "request_id", None),
        }

        # Add performance data if present
        if hasattr(record, "performance_data") and record.performance_data:
            structured_data["performance"] = record.performance_data

        # Add stack trace if present
        if hasattr(record, "stack_trace") and record.stack_trace:
            structured_data["stack_trace"] = record.stack_trace

        # Add any extra fields
        if hasattr(record, "extra_data") and record.extra_data:
            structured_data.update(record.extra_data)

        # In development, return pretty JSON. In production, return compact JSON
        if os.getenv("ENVIRONMENT", "development") == "development":
            return json.dumps(structured_data, indent=2, default=str)
        else:
            return json.dumps(structured_data, default=str)


# Global instance
_logging_service: Optional[LoggingService] = None


def get_logging_service() -> LoggingService:
    """Get the global logging service instance."""
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService()
    return _logging_service


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in context."""
    correlation_id_var.set(correlation_id)


def with_correlation_id(correlation_id: Optional[str] = None):
    """Context manager for correlation ID."""
    return CorrelationContextManager(correlation_id)


def log_performance(operation: str, duration: float, **metadata):
    """Convenience function to log performance metrics."""
    service = get_logging_service()
    service.log_performance(operation, duration, metadata)


async def log_error(error_type: str, message: str, service_name: str, correlation_id: Optional[str] = None):
    """Convenience function to log errors."""
    service = get_logging_service()
    await service.log_error(error_type, message, service_name, correlation_id)
