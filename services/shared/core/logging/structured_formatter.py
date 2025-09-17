"""Structured Formatter - JSON logging formatter with correlation ID support."""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """JSON structured logging formatter with correlation ID support.

    This formatter outputs log records in JSON format, including:
    - Timestamp in ISO format
    - Log level
    - Logger name
    - Message
    - Correlation ID (if available)
    - Thread information
    - Any additional structured data
    """

    def __init__(self, include_extra: bool = True) -> None:
        """Initialize structured formatter.

        Args:
            include_extra: Whether to include extra fields in output
        """
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON formatted log entry
        """
        # Base log entry structure
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread_id": record.thread,
            "thread_name": record.threadName,
            "process_id": record.process,
            "process_name": record.processName,
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add structured data from record
        if hasattr(record, 'structured_data') and record.structured_data:
            log_entry.update(record.structured_data)

        # Add any additional fields from the record
        if self.include_extra:
            # Get all attributes that aren't already included
            standard_attrs = {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'structured_data'
            }

            for attr in dir(record):
                if not attr.startswith('_') and attr not in standard_attrs:
                    value = getattr(record, attr)
                    if isinstance(value, (str, int, float, bool, type(None))):
                        log_entry[attr] = value

        # Convert to JSON with proper formatting
        try:
            return json.dumps(log_entry, default=self._json_serializer, indent=None)
        except (TypeError, ValueError) as e:
            # Fallback to basic formatting if JSON serialization fails
            fallback_entry = {
                "timestamp": log_entry["timestamp"],
                "level": log_entry["level"],
                "logger": log_entry["logger"],
                "message": f"JSON serialization failed: {e}, original message: {log_entry.get('message', 'N/A')}",
                "error": str(e)
            }
            return json.dumps(fallback_entry, indent=None)

    def _json_serializer(self, obj: Any) -> str:
        """Custom JSON serializer for non-standard objects.

        Args:
            obj: Object to serialize

        Returns:
            String representation of the object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Convert object to dictionary
            return str(obj)
        else:
            return str(obj)


class ColoredStructuredFormatter(StructuredFormatter):
    """Structured formatter with color coding for console output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def __init__(self, include_extra: bool = True, use_colors: bool = True) -> None:
        """Initialize colored structured formatter.

        Args:
            include_extra: Whether to include extra fields
            use_colors: Whether to use ANSI color codes
        """
        super().__init__(include_extra)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional color coding.

        Args:
            record: Log record to format

        Returns:
            Formatted log entry (with colors if enabled)
        """
        # Get base JSON format
        json_output = super().format(record)

        if not self.use_colors:
            return json_output

        # Add color coding for console output
        level_color = self.COLORS.get(record.levelname, '')
        colored_output = f"{level_color}{json_output}{self.RESET}"

        return colored_output


class CompactFormatter(logging.Formatter):
    """Compact formatter for development and debugging."""

    def __init__(self) -> None:
        """Initialize compact formatter."""
        super().__init__(
            fmt='%(asctime)s %(levelname)-8s %(name)-20s %(correlation_id)s %(message)s',
            datefmt='%H:%M:%S'
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format log record in compact format.

        Args:
            record: Log record to format

        Returns:
            Compact formatted log entry
        """
        # Add correlation ID if available
        if hasattr(record, 'structured_data') and record.structured_data:
            correlation_id = record.structured_data.get('correlation_id', '-')
        else:
            correlation_id = '-'

        # Add correlation ID to record for formatter
        record.correlation_id = correlation_id[:8] if correlation_id != '-' else '-'

        return super().format(record)


class PerformanceFormatter(logging.Formatter):
    """Formatter specialized for performance logging."""

    def __init__(self) -> None:
        """Initialize performance formatter."""
        super().__init__(
            fmt='%(asctime)s PERF %(name)s %(operation)s %(duration_ms).2fms %(message)s'
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format performance log record.

        Args:
            record: Log record to format

        Returns:
            Performance-focused formatted log entry
        """
        # Extract performance data from structured data
        if hasattr(record, 'structured_data') and record.structured_data:
            perf_data = record.structured_data
            record.operation = perf_data.get('operation', 'unknown')
            record.duration_ms = perf_data.get('duration_ms', 0.0)

        return super().format(record)
