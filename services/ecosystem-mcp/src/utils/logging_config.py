"""
Structured logging configuration.

Provides JSON-based structured logging for better observability.
"""

import logging
import sys
from typing import Dict, Any

import structlog


def configure_structured_logging(
    log_level: str = "INFO",
    json_logs: bool = True,
    include_timestamp: bool = True,
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Output logs in JSON format (recommended for production)
        include_timestamp: Include ISO timestamps in logs
    
    Example:
        >>> configure_structured_logging(log_level="INFO", json_logs=True)
        >>> logger = structlog.get_logger()
        >>> logger.info("user.login", user_id=123, ip="192.168.1.1")
    """
    # Convert log level string to logging constant
    log_level_const = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level_const,
    )
    
    # Build processor chain
    processors = [
        # Merge context vars (includes request_id from middleware)
        structlog.contextvars.merge_contextvars,
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add extra context
        structlog.stdlib.ExtraAdder(),
        # Filter by log level
        structlog.stdlib.filter_by_level,
    ]
    
    # Add timestamp if requested
    if include_timestamp:
        processors.append(
            structlog.processors.TimeStamper(fmt="iso", utc=True)
        )
    
    # Add common processors
    processors.extend([
        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
        # Handle positional arguments
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Decode unicode
        structlog.processors.UnicodeDecoder(),
    ])
    
    # Choose renderer based on json_logs flag
    if json_logs:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Human-readable output for development
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured structured logger
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("operation.started", operation="data_ingestion", count=100)
    """
    return structlog.get_logger(name)


def add_context(**kwargs: Any) -> None:
    """
    Add context to all subsequent log messages in this execution context.
    
    Args:
        **kwargs: Key-value pairs to add to logging context
    
    Example:
        >>> add_context(request_id="abc-123", user_id=456)
        >>> logger.info("processing.started")  # Will include request_id and user_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()


def log_with_context(
    logger: structlog.BoundLogger,
    level: str,
    event: str,
    **context: Any
) -> None:
    """
    Log a message with structured context.
    
    Args:
        logger: Structured logger instance
        level: Log level (info, warning, error, debug)
        event: Event name (use dot notation: "service.action")
        **context: Additional context as key-value pairs
    
    Example:
        >>> log_with_context(
        ...     logger, "info", "user.created",
        ...     user_id=123, email="user@example.com", source="api"
        ... )
    """
    log_func = getattr(logger, level.lower())
    log_func(event, **context)


# Pre-configured logger for common use cases
def create_service_logger(
    service_name: str,
    environment: str,
    version: str = "1.0.0"
) -> structlog.BoundLogger:
    """
    Create a logger with service-level context.
    
    Args:
        service_name: Name of the service
        environment: Environment (development, staging, production)
        version: Service version
    
    Returns:
        Logger with service context bound
    
    Example:
        >>> logger = create_service_logger("ecosystem-mcp", "production", "1.0.0")
        >>> logger.info("service.started", port=8000)
    """
    logger = get_logger(service_name)
    return logger.bind(
        service=service_name,
        environment=environment,
        version=version,
    )
