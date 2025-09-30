#!/usr/bin/env python3
"""
Standardized Logging and Monitoring System
==========================================

Comprehensive logging and monitoring framework for the ecosystem.
Provides consistent logging, metrics collection, and monitoring capabilities.

Features:
- Standardized log formatting across all services
- Structured logging with JSON output
- Performance metrics collection
- Health monitoring integration
- Distributed tracing support
- Log aggregation and analysis
- Alerting integration

Author: Ecosystem Hardening Framework
"""

import atexit
import json
import logging
import logging.handlers
import os
import sys
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class LogContext:
    """Context information for logging"""

    service_name: str
    service_version: str = "1.0.0"
    environment: str = "development"
    instance_id: str = field(
        default_factory=lambda: os.environ.get("HOSTNAME", "unknown")
    )
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring"""

    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    disk_usage_percent: float = 0.0
    network_connections: int = 0
    active_threads: int = 0
    open_files: int = 0
    response_time_ms: Optional[float] = None
    request_count: int = 0
    error_count: int = 0


class StandardizedLogger:
    """
    Standardized logging system for the ecosystem.

    Provides consistent logging across all services with structured output,
    performance monitoring, and health tracking.
    """

    def __init__(self, service_name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the standardized logger"""
        self.service_name = service_name
        self.config = config or self._get_default_config()
        self.context = LogContext(service_name=service_name)

        # Initialize logging
        self.logger = logging.getLogger(service_name)
        self._setup_logging()

        # Performance monitoring
        self.metrics = PerformanceMetrics()
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 metrics
        self._monitoring_thread = None
        self._monitoring_active = False

        # Request tracking
        self.request_metrics = defaultdict(int)
        self.error_metrics = defaultdict(int)

        # Health status
        self.health_status = "healthy"
        self.last_health_check = datetime.now()

        # Log collector integration
        self.log_buffer = deque(maxlen=self.config.get("log_collector_batch_size", 10))
        self._log_collector_thread = None
        self._log_collector_active = False
        if self.config.get("log_collector_enabled", False) and HTTPX_AVAILABLE:
            self._start_log_collector()

        # Register cleanup
        atexit.register(self._cleanup)

        self.logger.info(
            "🔧 Standardized Logger initialized",
            extra={
                "service": self.service_name,
                "environment": self.context.environment,
                "instance": self.context.instance_id,
            },
        )

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default logging configuration"""
        return {
            "log_level": os.environ.get("LOG_LEVEL", "INFO"),
            "log_format": os.environ.get("LOG_FORMAT", "json"),
            "log_file": os.environ.get("LOG_FILE", f"/var/log/{self.service_name}.log"),
            "console_logging": os.environ.get("CONSOLE_LOGGING", "true").lower()
            == "true",
            "structured_logging": os.environ.get("STRUCTURED_LOGGING", "true").lower()
            == "true",
            "monitoring_enabled": os.environ.get("MONITORING_ENABLED", "true").lower()
            == "true",
            "metrics_interval": int(os.environ.get("METRICS_INTERVAL", "30")),
            "max_log_size": int(os.environ.get("MAX_LOG_SIZE", "10485760")),  # 10MB
            "backup_count": int(os.environ.get("LOG_BACKUP_COUNT", "5")),
            # Log collector integration
            "log_collector_enabled": os.environ.get("LOG_COLLECTOR_ENABLED", "true").lower()
            == "true",
            "log_collector_url": os.environ.get("LOG_COLLECTOR_URL", "http://localhost:5080"),
            "log_collector_batch_size": int(os.environ.get("LOG_COLLECTOR_BATCH_SIZE", "10")),
            "log_collector_flush_interval": int(os.environ.get("LOG_COLLECTOR_FLUSH_INTERVAL", "30")),
        }

    def _setup_logging(self):
        """Setup logging configuration"""
        # Clear existing handlers
        self.logger.handlers.clear()

        # Set log level
        level = getattr(logging, self.config["log_level"].upper(), logging.INFO)
        self.logger.setLevel(level)

        # Create formatters
        if self.config["structured_logging"]:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
            )

        # Console handler
        if self.config["console_logging"]:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler with rotation
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                self.config["log_file"],
                maxBytes=self.config["max_log_size"],
                backupCount=self.config["backup_count"],
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # Fallback to console only if file logging fails
            self.logger.warning(f"Failed to setup file logging: {e}")

        # Log collector handler
        if self.config.get("log_collector_enabled", False):
            collector_handler = LogCollectorHandler(self)
            collector_handler.setLevel(level)
            self.logger.addHandler(collector_handler)

        # Prevent duplicate logs
        self.logger.propagate = False

    def update_context(self, **kwargs):
        """Update logging context"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        user_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """Log HTTP request with performance metrics"""
        log_level = logging.INFO if status_code < 400 else logging.WARNING

        # Update metrics
        self.request_metrics[f"{method}_{path}"] += 1
        if status_code >= 400:
            self.error_metrics[f"{method}_{path}"] += 1

        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time_ms": round(response_time * 1000, 2),
            "user_id": user_id,
            "service": self.service_name,
        }

        if extra:
            log_data.update(extra)

        self.logger.log(
            log_level, f"HTTP {method} {path} -> {status_code}", extra=log_data
        )

    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        """Log error with context"""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_code": error_code,
            "service": self.service_name,
            "traceback": self._get_traceback(error),
        }

        if context:
            error_data.update(context)

        self.logger.error(f"Error: {error}", extra=error_data, exc_info=True)

    def log_performance(
        self, operation: str, duration: float, metadata: Optional[Dict[str, Any]] = None
    ):
        """Log performance metrics"""
        perf_data = {
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "service": self.service_name,
        }

        if metadata:
            perf_data.update(metadata)

        self.logger.info(f"Performance: {operation}", extra=perf_data)

    def log_business_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log business events for analytics"""
        event_data.update(
            {
                "event_type": event_type,
                "service": self.service_name,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self.logger.info(f"Business Event: {event_type}", extra=event_data)

    def _get_traceback(self, error: Exception) -> str:
        """Get formatted traceback"""
        import traceback

        return "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.config["monitoring_enabled"]:
            return

        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return

        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name=f"{self.service_name}-monitoring",
        )
        self._monitoring_thread.start()
        self.logger.info("📊 Performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring and log collector"""
        if self._monitoring_active:
            self._monitoring_active = False
            if self._monitoring_thread and self._monitoring_thread.is_alive():
                self._monitoring_thread.join(timeout=5.0)

        self._stop_log_collector()
        self.logger.info("🛑 Standardized Logger monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._monitoring_active:
            try:
                self._collect_metrics()
                time.sleep(self.config["metrics_interval"])
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(5)  # Wait before retrying

    def _collect_metrics(self):
        """Collect system and application metrics"""
        try:
            # System metrics
            self.metrics.cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            self.metrics.memory_percent = memory.percent
            self.metrics.memory_mb = memory.used / 1024 / 1024

            disk = psutil.disk_usage("/")
            self.metrics.disk_usage_percent = disk.percent

            network = psutil.net_connections()
            self.metrics.network_connections = len(network)

            # Process metrics
            process = psutil.Process()
            self.metrics.active_threads = process.num_threads()

            try:
                self.metrics.open_files = len(process.open_files())
            except (OSError, IOError):
                self.metrics.open_files = 0

            # Application metrics
            self.metrics.request_count = sum(self.request_metrics.values())
            self.metrics.error_count = sum(self.error_metrics.values())

            # Store metrics history
            self.metrics_history.append(self.metrics)

            # Log metrics periodically
            if len(self.metrics_history) % 10 == 0:  # Every 10 collections
                self._log_metrics_summary()

        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")

    def _log_metrics_summary(self):
        """Log metrics summary"""
        if not self.metrics_history:
            return

        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 metrics

        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        total_requests = sum(m.request_count for m in recent_metrics)
        total_errors = sum(m.error_count for m in recent_metrics)

        metrics_data = {
            "avg_cpu_percent": round(avg_cpu, 2),
            "avg_memory_percent": round(avg_memory, 2),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(total_errors / max(total_requests, 1) * 100, 2),
            "service": self.service_name,
            "period_seconds": len(recent_metrics) * self.config["metrics_interval"],
        }

        self.logger.info("📊 Metrics Summary", extra=metrics_data)

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        self.last_health_check = datetime.now()

        # Determine health based on metrics
        if self.metrics.memory_percent > 90:
            self.health_status = "critical"
        elif self.metrics.memory_percent > 75:
            self.health_status = "warning"
        elif self.metrics.cpu_percent > 90:
            self.health_status = "warning"
        else:
            self.health_status = "healthy"

        # Calculate error rate
        total_requests = sum(self.request_metrics.values())
        total_errors = sum(self.error_metrics.values())
        error_rate = total_errors / max(total_requests, 1)

        if error_rate > 0.1:  # 10% error rate
            self.health_status = "critical"
        elif error_rate > 0.05:  # 5% error rate
            self.health_status = "warning"

        return {
            "status": self.health_status,
            "service": self.service_name,
            "timestamp": self.last_health_check.isoformat(),
            "metrics": {
                "cpu_percent": self.metrics.cpu_percent,
                "memory_percent": self.metrics.memory_percent,
                "disk_usage_percent": self.metrics.disk_usage_percent,
                "active_threads": self.metrics.active_threads,
                "request_count": total_requests,
                "error_count": total_errors,
                "error_rate": round(error_rate * 100, 2),
            },
            "uptime_seconds": (
                datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            ).total_seconds(),
        }

    def _cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
        self.logger.info("🧹 Standardized Logger cleanup completed")

    # Convenience methods for different log levels
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=self._prepare_extra(kwargs))

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=self._prepare_extra(kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=self._prepare_extra(kwargs))

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=self._prepare_extra(kwargs))

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=self._prepare_extra(kwargs))

    def _prepare_extra(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare extra data for logging"""
        extra = {
            "service": self.service_name,
            "instance": self.context.instance_id,
            "environment": self.context.environment,
        }

        # Add context fields if they exist
        for field in ["request_id", "user_id", "correlation_id", "session_id"]:
            value = getattr(self.context, field, None)
            if value:
                extra[field] = value

        extra.update(kwargs)
        return extra

    # Log Collector Integration Methods
    def _start_log_collector(self):
        """Start the log collector forwarding thread"""
        if not HTTPX_AVAILABLE:
            self.logger.warning("httpx not available, log collector disabled")
            return

        self._log_collector_active = True
        self._log_collector_thread = threading.Thread(
            target=self._log_collector_loop,
            daemon=True,
            name=f"{self.service_name}-log-collector"
        )
        self._log_collector_thread.start()
        self.logger.info("📤 Log collector forwarding started")

    def _stop_log_collector(self):
        """Stop the log collector forwarding thread"""
        if self._log_collector_active:
            self._log_collector_active = False
            if self._log_collector_thread and self._log_collector_thread.is_alive():
                self._log_collector_thread.join(timeout=5.0)
            self.logger.info("📤 Log collector forwarding stopped")

    def _log_collector_loop(self):
        """Main log collector forwarding loop"""
        flush_interval = self.config.get("log_collector_flush_interval", 30)

        while self._log_collector_active:
            try:
                time.sleep(flush_interval)
                self._flush_log_buffer()
            except Exception as e:
                self.logger.error(f"Log collector error: {e}")

    def _flush_log_buffer(self):
        """Flush accumulated logs to the log collector service"""
        if not self.log_buffer:
            return

        logs_to_send = list(self.log_buffer)
        self.log_buffer.clear()

        try:
            log_collector_url = self.config.get("log_collector_url")
            if not log_collector_url:
                return

            # Convert logs to log-collector format
            log_items = []
            for log_entry in logs_to_send:
                log_item = {
                    "service": self.service_name,
                    "level": log_entry.get("level", "info"),
                    "message": log_entry.get("message", ""),
                    "timestamp": log_entry.get("timestamp"),
                    "context": log_entry.get("context", {})
                }
                log_items.append(log_item)

            # Send batch to log collector
            async def send_logs():
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{log_collector_url}/logs/batch",
                        json={"items": log_items},
                        headers={"Content-Type": "application/json"}
                    )
                    if response.status_code not in [200, 201]:
                        raise Exception(f"HTTP {response.status_code}: {response.text}")

            # Run async function in thread
            import asyncio
            asyncio.run(send_logs())

        except Exception as e:
            # If log collector fails, put logs back in buffer (up to limit)
            self.logger.warning(f"Failed to send logs to collector: {e}")
            # Re-queue failed logs (but don't overflow buffer)
            for log_entry in logs_to_send[:len(self.log_buffer)]:
                if len(self.log_buffer) < self.log_buffer.maxlen:
                    self.log_buffer.append(log_entry)

    def _buffer_log_for_collection(self, level: str, message: str, extra: Dict[str, Any]):
        """Buffer a log entry for sending to log collector"""
        if not self.config.get("log_collector_enabled", False):
            return

        log_entry = {
            "level": level,
            "message": message,
            "timestamp": extra.get("timestamp"),
            "context": {k: v for k, v in extra.items() if k not in ["service", "timestamp", "environment", "instance"]}
        }

        self.log_buffer.append(log_entry)


class LogCollectorHandler(logging.Handler):
    """Custom logging handler that buffers logs for the log collector"""

    def __init__(self, logger_instance: 'StandardizedLogger'):
        super().__init__()
        self.logger_instance = logger_instance

    def emit(self, record):
        """Buffer log record for sending to log collector"""
        try:
            # Convert log record to dictionary format
            log_entry = {
                "level": record.levelname.lower(),
                "message": record.getMessage(),
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "context": getattr(record, '__dict__', {}).get('extra', {})
            }

            # Add to buffer
            self.logger_instance.log_buffer.append(log_entry)
        except Exception:
            # Don't let logging handler errors break the application
            pass


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs"""

    def format(self, record):
        # Create base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, "service", "unknown"),
            "instance": getattr(record, "instance", "unknown"),
            "environment": getattr(record, "environment", "unknown"),
        }

        # Add any extra fields from the record
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in [
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "message",
                ]:
                    # Convert non-serializable objects to strings
                    if isinstance(value, (datetime, Path)):
                        log_entry[key] = str(value)
                    elif hasattr(value, "__dict__"):
                        log_entry[key] = str(value)
                    else:
                        try:
                            json.dumps(value)  # Test if serializable
                            log_entry[key] = value
                        except (TypeError, ValueError):
                            log_entry[key] = str(value)

        return json.dumps(log_entry, default=str)


def performance_monitor(operation_name: str = None):
    """
    Decorator for performance monitoring of functions
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or f"{func.__module__}.{func.__name__}"

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Get logger from first argument if it's a class instance
                logger = None
                if args and hasattr(args[0], "logger"):
                    logger = args[0].logger
                elif hasattr(func, "__self__") and hasattr(func.__self__, "logger"):
                    logger = func.__self__.logger

                if logger:
                    logger.log_performance(
                        operation,
                        duration,
                        {
                            "success": True,
                            "args_count": len(args),
                            "kwargs_count": len(kwargs),
                        },
                    )

                return result

            except Exception as e:
                duration = time.time() - start_time

                if logger:
                    logger.log_performance(
                        operation,
                        duration,
                        {
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )

                raise

        return wrapper

    return decorator


# Global logger registry for service discovery
_logger_registry = {}


def get_logger(
    service_name: str, config: Optional[Dict[str, Any]] = None
) -> StandardizedLogger:
    """
    Get or create a standardized logger for a service

    Args:
        service_name: Name of the service
        config: Optional configuration dictionary

    Returns:
        StandardizedLogger instance
    """
    if service_name not in _logger_registry:
        _logger_registry[service_name] = StandardizedLogger(service_name, config)

    return _logger_registry[service_name]


def get_all_loggers() -> Dict[str, StandardizedLogger]:
    """Get all registered loggers"""
    return _logger_registry.copy()


def configure_service_logging(service_name: str, config: Dict[str, Any]):
    """
    Configure logging for a service

    Args:
        service_name: Name of the service
        config: Logging configuration
    """
    logger = get_logger(service_name, config)
    logger.start_monitoring()
    return logger


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    logger = get_logger(
        "example-service",
        {"log_level": "INFO", "structured_logging": True, "monitoring_enabled": True},
    )

    logger.start_monitoring()

    # Example logging
    logger.info("Service started", version="1.0.0")
    logger.log_request("GET", "/api/health", 200, 0.045)
    logger.log_business_event("user_login", {"user_id": "12345"})
    logger.log_performance("database_query", 0.123)

    # Get health status
    health = logger.get_health_status()
    logger.info("Health check", **health)

    time.sleep(5)  # Let monitoring run

    logger.stop_monitoring()
    logger.info("Service shutdown")
