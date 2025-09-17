"""Application Logging Service - Structured logging with correlation tracking."""

import logging
import json
import sys
from typing import Any, Dict, Optional, List
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from .application_service import ApplicationService, ServiceContext


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def __init__(self, include_extra: bool = True):
        """Initialize formatter."""
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Create base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields if requested
        if self.include_extra and hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                    'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                    'thread', 'threadName', 'processName', 'process', 'message'
                }:
                    # Convert non-serializable objects to strings
                    try:
                        json.dumps(value)
                        log_entry[key] = value
                    except (TypeError, ValueError):
                        log_entry[key] = str(value)

        return json.dumps(log_entry, default=str)


class ApplicationLogger(logging.LoggerAdapter):
    """Application logger with context and correlation tracking."""

    def __init__(self, logger: logging.Logger, context: Optional[Dict[str, Any]] = None):
        """Initialize application logger."""
        super().__init__(logger, context or {})

    def with_context(self, **context) -> 'ApplicationLogger':
        """Create new logger with additional context."""
        new_context = {**self.extra, **context}
        return ApplicationLogger(self.logger, new_context)

    def with_correlation(self, correlation_id: str) -> 'ApplicationLogger':
        """Create logger with correlation ID."""
        return self.with_context(correlation_id=correlation_id)

    def with_user(self, user_id: str) -> 'ApplicationLogger':
        """Create logger with user context."""
        return self.with_context(user_id=user_id)

    def with_service(self, service_name: str) -> 'ApplicationLogger':
        """Create logger with service context."""
        return self.with_context(service=service_name)

    def log_operation_start(self, operation: str, **kwargs) -> None:
        """Log operation start."""
        self.info(f"Starting operation: {operation}", extra={
            'operation': operation,
            'event': 'operation_start',
            **kwargs
        })

    def log_operation_end(self, operation: str, duration: float, **kwargs) -> None:
        """Log operation end."""
        self.info(f"Completed operation: {operation}", extra={
            'operation': operation,
            'duration': duration,
            'event': 'operation_end',
            **kwargs
        })

    def log_operation_error(self, operation: str, error: str, **kwargs) -> None:
        """Log operation error."""
        self.error(f"Operation failed: {operation}", extra={
            'operation': operation,
            'error': error,
            'event': 'operation_error',
            **kwargs
        })

    def log_business_event(self, event: str, **kwargs) -> None:
        """Log business event."""
        self.info(f"Business event: {event}", extra={
            'event_type': 'business',
            'business_event': event,
            **kwargs
        })

    def log_performance_metric(self, metric: str, value: Any, **kwargs) -> None:
        """Log performance metric."""
        self.info(f"Performance metric: {metric} = {value}", extra={
            'event_type': 'performance',
            'metric': metric,
            'value': value,
            **kwargs
        })


class LoggingService(ApplicationService):
    """Application logging service with structured logging support."""

    def __init__(
        self,
        log_level: str = "INFO",
        log_directory: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        enable_console: bool = True,
        enable_file: bool = True,
        structured: bool = True
    ):
        """Initialize logging service."""
        super().__init__("logging_service")

        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_directory = Path(log_directory) if log_directory else Path("logs")
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.structured = structured

        # Create log directory
        if self.enable_file:
            self.log_directory.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        self._configure_logging()

        # Create application logger
        self.app_logger = ApplicationLogger(logging.getLogger("analysis_service"))

    def _configure_logging(self) -> None:
        """Configure logging with appropriate handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create formatter
        if self.structured:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # File handler
        if self.enable_file:
            # Application log file
            app_log_file = self.log_directory / "analysis_service.log"
            file_handler = RotatingFileHandler(
                app_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            # Error log file (only errors and above)
            error_log_file = self.log_directory / "analysis_service_error.log"
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)

    def get_logger(self, name: str = "analysis_service") -> ApplicationLogger:
        """Get a logger instance."""
        logger = logging.getLogger(name)
        return ApplicationLogger(logger, self.app_logger.extra)

    def create_operation_logger(self, operation: str, context: ServiceContext) -> ApplicationLogger:
        """Create logger for operation with context."""
        return self.app_logger.with_context(
            operation=operation,
            correlation_id=context.correlation_id,
            user_id=context.user_id,
            session_id=context.session_id,
            request_id=context.request_id
        )

    async def log_service_metrics(self) -> None:
        """Log service metrics."""
        try:
            # Log current logging statistics
            root_logger = logging.getLogger()
            handler_count = len(root_logger.handlers)

            self.app_logger.log_performance_metric(
                "logging_handlers",
                handler_count,
                service="logging_service"
            )

            # Log log directory size if file logging is enabled
            if self.enable_file and self.log_directory.exists():
                total_size = sum(
                    f.stat().st_size for f in self.log_directory.glob("*.log")
                    if f.is_file()
                )
                self.app_logger.log_performance_metric(
                    "log_directory_size_bytes",
                    total_size,
                    service="logging_service"
                )

        except Exception as e:
            # Don't let metrics logging break the service
            print(f"Error logging service metrics: {e}")

    async def rotate_logs(self) -> None:
        """Manually rotate log files."""
        try:
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                if hasattr(handler, 'doRollover'):
                    handler.doRollover()

            self.app_logger.info("Log files rotated manually")

        except Exception as e:
            self.app_logger.error(f"Error rotating logs: {e}")

    async def cleanup_old_logs(self, days_to_keep: int = 30) -> None:
        """Clean up old log files."""
        try:
            if not self.enable_file:
                return

            import time
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)

            deleted_count = 0
            for log_file in self.log_directory.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    deleted_count += 1

            if deleted_count > 0:
                self.app_logger.info(f"Cleaned up {deleted_count} old log files")

        except Exception as e:
            self.app_logger.error(f"Error cleaning up old logs: {e}")

    def set_log_level(self, level: str) -> None:
        """Set logging level."""
        new_level = getattr(logging, level.upper(), self.log_level)
        logging.getLogger().setLevel(new_level)
        self.log_level = new_level
        self.app_logger.info(f"Log level changed to: {level}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = await super().health_check()

        # Add logging-specific health info
        try:
            root_logger = logging.getLogger()
            health['logging'] = {
                'level': logging.getLevelName(root_logger.level),
                'handlers': len(root_logger.handlers),
                'file_logging_enabled': self.enable_file,
                'console_logging_enabled': self.enable_console,
                'structured_logging': self.structured
            }

            if self.enable_file:
                health['logging']['log_directory'] = str(self.log_directory)
                health['logging']['directory_exists'] = self.log_directory.exists()

        except Exception as e:
            health['logging'] = {'error': str(e)}

        return health


class LogAggregator:
    """Service for aggregating and analyzing logs."""

    def __init__(self, logging_service: LoggingService):
        """Initialize log aggregator."""
        self.logging_service = logging_service
        self.log_entries: List[Dict[str, Any]] = []
        self.max_entries = 10000

    def add_log_entry(self, entry: Dict[str, Any]) -> None:
        """Add log entry to aggregator."""
        self.log_entries.append(entry)

        # Maintain max entries limit
        if len(self.log_entries) > self.max_entries:
            self.log_entries.pop(0)

    def get_logs_by_level(self, level: str) -> List[Dict[str, Any]]:
        """Get logs by level."""
        return [entry for entry in self.log_entries if entry.get('level') == level]

    def get_logs_by_correlation_id(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get logs by correlation ID."""
        return [entry for entry in self.log_entries if entry.get('correlation_id') == correlation_id]

    def get_error_rate(self, time_window_minutes: int = 60) -> float:
        """Calculate error rate in the last time window."""
        # This would need timestamp filtering in a real implementation
        error_count = len(self.get_logs_by_level('ERROR'))
        total_count = len(self.log_entries)

        return error_count / max(1, total_count)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from logs."""
        stats = {
            'total_logs': len(self.log_entries),
            'error_count': len(self.get_logs_by_level('ERROR')),
            'warning_count': len(self.get_logs_by_level('WARNING')),
            'info_count': len(self.get_logs_by_level('INFO')),
            'debug_count': len(self.get_logs_by_level('DEBUG'))
        }

        # Calculate rates
        stats['error_rate'] = stats['error_count'] / max(1, stats['total_logs'])

        return stats


# Global logging service instance
logging_service = LoggingService()

# Create application logger instance
app_logger = logging_service.get_logger()

# Create log aggregator
log_aggregator = LogAggregator(logging_service)
