"""Logger Service - Enterprise-grade structured logging with correlation IDs."""

import logging
import json
import threading
import sys
from typing import Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime, timezone
from contextvars import ContextVar

from ..di.services import ILoggerService


# Global correlation ID context variable
_correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
_correlation_lock = threading.RLock()


class LoggerService(ILoggerService):
    """Enterprise-grade structured logging service with correlation IDs.

    This logger service provides:
    - Structured logging with JSON output
    - Correlation ID tracking across requests
    - Multiple log levels with appropriate filtering
    - Performance logging capabilities
    - Configurable output destinations
    - Thread-safe operations
    - Contextual information enrichment
    """

    def __init__(self,
                 name: str = "analysis-service",
                 level: str = "INFO",
                 log_file: Optional[str] = None,
                 enable_json: bool = True,
                 enable_console: bool = True) -> None:
        """Initialize logger service.

        Args:
            name: Logger name/identifier
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for log output
            enable_json: Enable JSON structured logging
            enable_console: Enable console output
        """
        self.name = name
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.enable_json = enable_json
        self.enable_console = enable_console

        # Create logger
        self._logger = logging.getLogger(f"{name}.structured")
        self._logger.setLevel(self.level)

        # Remove existing handlers to avoid duplicates
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        # Add console handler if enabled
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.level)
            if enable_json:
                from .structured_formatter import StructuredFormatter
                console_handler.setFormatter(StructuredFormatter())
            else:
                console_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            self._logger.addHandler(console_handler)

        # Add file handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(self.level)
            if enable_json:
                from .structured_formatter import StructuredFormatter
                file_handler.setFormatter(StructuredFormatter())
            else:
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(correlation_id)s - %(message)s'
                ))
            self._logger.addHandler(file_handler)

        # Prevent duplicate messages from parent loggers
        self._logger.propagate = False

    def _enrich_log_data(self, **kwargs) -> Dict[str, Any]:
        """Enrich log data with contextual information."""
        enriched = dict(kwargs)

        # Add correlation ID if available
        correlation_id = _correlation_id.get()
        if correlation_id:
            enriched['correlation_id'] = correlation_id

        # Add timestamp if not provided
        if 'timestamp' not in enriched:
            enriched['timestamp'] = datetime.now(timezone.utc).isoformat()

        # Add service information
        enriched['service'] = self.name

        # Add thread information for debugging
        enriched['thread_id'] = threading.get_ident()
        enriched['thread_name'] = threading.current_thread().name

        return enriched

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with structured data.

        Debug messages are typically used for detailed troubleshooting
        information useful during development and debugging.

        Args:
            message: Log message
            **kwargs: Additional structured data to include
        """
        if self._logger.isEnabledFor(logging.DEBUG):
            enriched_data = self._enrich_log_data(**kwargs)
            self._logger.debug(message, extra={'structured_data': enriched_data})

    def info(self, message: str, **kwargs) -> None:
        """Log info message with structured data.

        Info messages provide general information about application
        operation, such as startup events and successful operations.

        Args:
            message: Log message
            **kwargs: Additional structured data to include
        """
        if self._logger.isEnabledFor(logging.INFO):
            enriched_data = self._enrich_log_data(**kwargs)
            self._logger.info(message, extra={'structured_data': enriched_data})

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with structured data.

        Warning messages indicate potential issues that don't prevent
        operation but should be investigated.

        Args:
            message: Log message
            **kwargs: Additional structured data to include
        """
        if self._logger.isEnabledFor(logging.WARNING):
            enriched_data = self._enrich_log_data(**kwargs)
            self._logger.warning(message, extra={'structured_data': enriched_data})

    def error(self, message: str, **kwargs) -> None:
        """Log error message with structured data.

        Error messages indicate failures that affect operation but
        don't necessarily cause application shutdown.

        Args:
            message: Log message
            **kwargs: Additional structured data to include
        """
        if self._logger.isEnabledFor(logging.ERROR):
            enriched_data = self._enrich_log_data(**kwargs)
            self._logger.error(message, extra={'structured_data': enriched_data})

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with structured data.

        Critical messages indicate severe failures that may require
        immediate attention and could cause application instability.

        Args:
            message: Log message
            **kwargs: Additional structured data to include
        """
        if self._logger.isEnabledFor(logging.CRITICAL):
            enriched_data = self._enrich_log_data(**kwargs)
            self._logger.critical(message, extra={'structured_data': enriched_data})

    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """Log performance metrics.

        Args:
            operation: Name of the operation being measured
            duration: Duration in seconds
            **kwargs: Additional performance context
        """
        self.info(
            f"Performance: {operation}",
            operation=operation,
            duration_seconds=duration,
            duration_ms=duration * 1000,
            performance_category="measurement",
            **kwargs
        )

    def log_request(self, method: str, endpoint: str, status_code: int,
                   duration: float, **kwargs) -> None:
        """Log HTTP request information.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            status_code: HTTP status code
            duration: Request duration in seconds
            **kwargs: Additional request context
        """
        log_level = logging.INFO if status_code < 400 else logging.WARNING if status_code < 500 else logging.ERROR

        self._logger.log(
            log_level,
            f"HTTP {method} {endpoint} -> {status_code}",
            extra={
                'structured_data': self._enrich_log_data(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                    duration_seconds=duration,
                    duration_ms=duration * 1000,
                    request_category="http",
                    **kwargs
                )
            }
        )

    def log_business_event(self, event_type: str, **kwargs) -> None:
        """Log business domain events.

        Args:
            event_type: Type of business event
            **kwargs: Event-specific data
        """
        self.info(
            f"Business Event: {event_type}",
            event_type=event_type,
            event_category="business",
            **kwargs
        )

    def create_child_logger(self, child_name: str) -> 'LoggerService':
        """Create a child logger with the same configuration.

        Args:
            child_name: Name for the child logger

        Returns:
            New logger instance with child name
        """
        return LoggerService(
            name=f"{self.name}.{child_name}",
            level=logging.getLevelName(self.level),
            enable_json=self.enable_json,
            enable_console=self.enable_console
        )


# Global logger instance
_global_logger: Optional[LoggerService] = None


def get_logger(name: Optional[str] = None) -> LoggerService:
    """Get logger instance.

    Args:
        name: Optional logger name (defaults to 'analysis-service')

    Returns:
        Logger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = LoggerService(name or "analysis-service")
    return _global_logger


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID.

    Returns:
        Current correlation ID or None if not set
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Set correlation ID for current context.

    Args:
        correlation_id: Correlation ID to set, or None to clear
    """
    with _correlation_lock:
        _correlation_id.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate a new correlation ID.

    Returns:
        New unique correlation ID
    """
    import uuid
    return str(uuid.uuid4())


def with_correlation_id(correlation_id: Optional[str] = None):
    """Context manager/decorator to set correlation ID.

    Args:
        correlation_id: Correlation ID to use (generates new one if None)

    Yields:
        Correlation ID that was set

    Example:
        with with_correlation_id() as correlation_id:
            logger.info("Starting operation", operation_id="123")
    """
    from contextlib import contextmanager

    @contextmanager
    def _correlation_context(corr_id: Optional[str]):
        previous_id = get_correlation_id()
        new_id = corr_id or generate_correlation_id()
        set_correlation_id(new_id)

        try:
            yield new_id
        finally:
            set_correlation_id(previous_id)

    return _correlation_context(correlation_id)
