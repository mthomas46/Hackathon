"""Logging infrastructure for the Simulation Dashboard Service.

This module provides structured logging capabilities for the dashboard service,
following consistent patterns with the broader ecosystem.
"""

import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

from infrastructure.config.config import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """Setup logging configuration for the dashboard service."""
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set log level
    log_level = getattr(logging, config.level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Create formatter
    if config.format.lower() == "json" and STRUCTLOG_AVAILABLE:
        # Use structured logging
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.JSONRenderer(),
        )
    else:
        # Use standard logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Configure structlog if available
    if STRUCTLOG_AVAILABLE and config.enable_structlog:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)


class DashboardLogger:
    """Enhanced logger for dashboard-specific logging."""

    def __init__(self, name: str):
        """Initialize dashboard logger."""
        self.logger = get_logger(name)
        self.name = name

    def info(self, message: str, **kwargs) -> None:
        """Log info message with additional context."""
        self.logger.info(message, extra=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message with additional context."""
        self.logger.error(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with additional context."""
        self.logger.warning(message, extra=kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with additional context."""
        self.logger.debug(message, extra=kwargs)

    def log_request(self, method: str, url: str, status_code: int, duration: float) -> None:
        """Log HTTP request details."""
        self.logger.info(
            f"HTTP Request: {method} {url}",
            method=method,
            url=url,
            status_code=status_code,
            duration=duration
        )

    def log_websocket_message(self, message_type: str, simulation_id: Optional[str] = None) -> None:
        """Log WebSocket message."""
        self.logger.debug(
            f"WebSocket Message: {message_type}",
            message_type=message_type,
            simulation_id=simulation_id
        )

    def log_simulation_event(self, event_type: str, simulation_id: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log simulation-related events."""
        self.logger.info(
            f"Simulation Event: {event_type}",
            event_type=event_type,
            simulation_id=simulation_id,
            details=details or {}
        )

    def log_performance_metric(self, metric_name: str, value: float, unit: str = "") -> None:
        """Log performance metrics."""
        self.logger.info(
            f"Performance: {metric_name} = {value} {unit}",
            metric_name=metric_name,
            value=value,
            unit=unit
        )


# Global logger instance
_logger: Optional[DashboardLogger] = None


def get_dashboard_logger(name: str = "simulation_dashboard") -> DashboardLogger:
    """Get the global dashboard logger instance."""
    global _logger
    if _logger is None:
        _logger = DashboardLogger(name)
    return _logger
