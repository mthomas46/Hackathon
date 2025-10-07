"""Logging Configuration for MCP Services."""

import logging
import sys
from typing import Optional


def configure_logging(
    service_name: str,
    log_level: str = "INFO",
    structured: bool = True,
    include_timestamp: bool = True,
) -> logging.Logger:
    """
    Configure structured logging for MCP service.
    
    Args:
        service_name: Name of the service
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Use structured (JSON) logging
        include_timestamp: Include timestamp in logs
    
    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(f"mcp.{service_name}")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    if structured:
        formatter = StructuredFormatter(
            service_name=service_name,
            include_timestamp=include_timestamp
        )
    else:
        format_str = (
            f'[{service_name}] %(asctime)s - %(name)s - '
            f'%(levelname)s - %(message)s'
        )
        formatter = logging.Formatter(format_str)
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info(f"Logging configured for {service_name} at {log_level} level")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class StructuredFormatter(logging.Formatter):
    """
    Formatter that outputs structured (JSON-like) log entries.
    
    Format:
    {
        "timestamp": "2025-10-07T12:00:00Z",
        "service": "kafka-ingestion",
        "level": "INFO",
        "source": "module.function",
        "message": "Log message",
        "fields": {...}
    }
    """
    
    def __init__(
        self,
        service_name: str,
        include_timestamp: bool = True
    ):
        """
        Initialize formatter.
        
        Args:
            service_name: Name of the service
            include_timestamp: Include timestamp in output
        """
        super().__init__()
        self.service_name = service_name
        self.include_timestamp = include_timestamp
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured output.
        
        Args:
            record: Log record to format
        
        Returns:
            Formatted log string
        """
        # Build structured log entry
        parts = []
        
        if self.include_timestamp:
            timestamp = self.formatTime(record, "%Y-%m-%dT%H:%M:%S")
            parts.append(f'timestamp="{timestamp}Z"')
        
        parts.append(f'service="{self.service_name}"')
        parts.append(f'level="{record.levelname}"')
        parts.append(f'source="{record.name}"')
        parts.append(f'message="{record.getMessage()}"')
        
        # Add custom fields if present
        if hasattr(record, "fields") and record.fields:
            fields_str = ", ".join(
                f'{k}={v}' for k, v in record.fields.items()
            )
            parts.append(f'fields={{" {fields_str} "}}')
        
        # Add exception info if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            parts.append(f'exception="{exc_text}"')
        
        return " | ".join(parts)


class FieldAdapter(logging.LoggerAdapter):
    """
    Logger adapter that allows passing custom fields to logs.
    
    Usage:
        logger = logging.getLogger(__name__)
        adapter = FieldAdapter(logger, {"service_id": "123"})
        adapter.info("Message", fields={"user_id": "456"})
    """
    
    def process(self, msg, kwargs):
        """
        Process log message and kwargs.
        
        Args:
            msg: Log message
            kwargs: Log keyword arguments
        
        Returns:
            Tuple of (msg, kwargs)
        """
        # Extract fields from kwargs
        fields = kwargs.pop("fields", {})
        
        # Merge with adapter fields
        if self.extra:
            fields.update(self.extra)
        
        # Add fields to kwargs
        kwargs["extra"] = {"fields": fields}
        
        return msg, kwargs

