"""Common Logging Utilities

Reduces code duplication by providing standardized logging patterns
used throughout the shared service and ecosystem.

This module provides:
- Structured logging helpers
- Performance logging patterns
- Error logging utilities
- Request/response logging
- Audit logging patterns
"""

import time
import logging
from typing import Any, Dict, Optional, Callable
from contextlib import contextmanager
from functools import wraps

from .error_handling import ServiceException


# ============================================================================
# STRUCTURED LOGGING HELPERS (REDUCING DUPLICATION)
# ============================================================================

def log_operation_start(operation_name: str, **context) -> str:
    """Log the start of an operation with structured data.

    Common pattern for operation logging across services.

    Args:
        operation_name: Name of the operation
        **context: Additional context data for structured logging

    Returns:
        Operation ID for tracking
    """
    import uuid
    operation_id = str(uuid.uuid4())[:8]

    logger = logging.getLogger(__name__)
    logger.info(
        f"Starting operation: {operation_name}",
        extra={
            "operation": operation_name,
            "operation_id": operation_id,
            "event_type": "operation_start",
            **context
        }
    )
    return operation_id

def log_operation_end(operation_id: str, operation_name: str,
                     success: bool = True, duration_ms: float = None,
                     **context) -> None:
    """Log the end of an operation with structured data.

    Common pattern for operation completion logging.

    Args:
        operation_id: Operation ID from log_operation_start
        operation_name: Name of the operation
        success: Whether the operation succeeded
        duration_ms: Operation duration in milliseconds
        **context: Additional context data
    """
    logger = logging.getLogger(__name__)

    log_data = {
        "operation": operation_name,
        "operation_id": operation_id,
        "event_type": "operation_end",
        "success": success,
        **context
    }

    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms

    if success:
        logger.info(
            f"Completed operation: {operation_name}",
            extra=log_data
        )
    else:
        logger.error(
            f"Failed operation: {operation_name}",
            extra=log_data
        )

@contextmanager
def log_operation(operation_name: str, **context):
    """Context manager for logging operation start/end.

    Common pattern for operation lifecycle logging.

    Args:
        operation_name: Name of the operation
        **context: Additional context data

    Example:
        with log_operation("process_data", user_id=123):
            # do work
            pass
    """
    operation_id = log_operation_start(operation_name, **context)
    start_time = time.time()

    try:
        yield operation_id
        duration_ms = (time.time() - start_time) * 1000
        log_operation_end(operation_id, operation_name, success=True,
                         duration_ms=duration_ms, **context)
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_operation_end(operation_id, operation_name, success=False,
                         duration_ms=duration_ms, error=str(e), **context)
        raise


# ============================================================================
# PERFORMANCE LOGGING PATTERNS (REDUCING DUPLICATION)
# ============================================================================

def log_performance_metric(metric_name: str, value: float,
                          unit: str = "ms", **context) -> None:
    """Log performance metrics with structured data.

    Common pattern for performance monitoring across services.

    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        **context: Additional context data
    """
    logger = logging.getLogger(__name__)
    logger.info(
        f"Performance metric: {metric_name} = {value}{unit}",
        extra={
            "metric_name": metric_name,
            "metric_value": value,
            "metric_unit": unit,
            "event_type": "performance_metric",
            **context
        }
    )

def log_request_metrics(method: str, path: str, status_code: int,
                       duration_ms: float, **context) -> None:
    """Log HTTP request metrics.

    Common pattern for request logging across services.

    Args:
        method: HTTP method
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration
        **context: Additional context data
    """
    logger = logging.getLogger(__name__)

    # Determine log level based on status code
    if status_code >= 500:
        log_method = logger.error
    elif status_code >= 400:
        log_method = logger.warning
    else:
        log_method = logger.info

    log_method(
        f"HTTP {method} {path} - {status_code} ({duration_ms:.2f}ms)",
        extra={
            "http_method": method,
            "http_path": path,
            "http_status": status_code,
            "duration_ms": duration_ms,
            "event_type": "http_request",
            **context
        }
    )


# ============================================================================
# ERROR LOGGING UTILITIES (REDUCING DUPLICATION)
# ============================================================================

def log_service_error(error: Exception, operation: str = None,
                     error_code: str = None, **context) -> None:
    """Log service errors with structured data.

    Common pattern for error logging across services.

    Args:
        error: Exception that occurred
        operation: Operation being performed when error occurred
        error_code: Error code for categorization
        **context: Additional context data
    """
    logger = logging.getLogger(__name__)

    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "event_type": "service_error",
        **context
    }

    if operation:
        log_data["operation"] = operation

    if error_code:
        log_data["error_code"] = error_code

    # Add stack trace for debugging in development
    if logger.isEnabledFor(logging.DEBUG):
        import traceback
        log_data["stack_trace"] = traceback.format_exc()

    logger.error(
        f"Service error in {operation or 'unknown operation'}: {error}",
        extra=log_data,
        exc_info=True
    )

def log_validation_error(field: str, value: Any, reason: str, **context) -> None:
    """Log validation errors with structured data.

    Common pattern for validation error logging.

    Args:
        field: Field that failed validation
        value: Invalid value provided
        reason: Reason for validation failure
        **context: Additional context data
    """
    logger = logging.getLogger(__name__)
    logger.warning(
        f"Validation error for field '{field}': {reason}",
        extra={
            "field": field,
            "invalid_value": str(value)[:100],  # Truncate for security
            "validation_reason": reason,
            "event_type": "validation_error",
            **context
        }
    )


# ============================================================================
# AUDIT LOGGING PATTERNS (REDUCING DUPLICATION)
# ============================================================================

def log_audit_event(event_type: str, user_id: str = None,
                   resource_type: str = None, resource_id: str = None,
                   action: str = None, **context) -> None:
    """Log audit events for security and compliance.

    Common pattern for audit logging across services.

    Args:
        event_type: Type of audit event
        user_id: User performing the action
        resource_type: Type of resource being acted upon
        resource_id: ID of the resource
        action: Action being performed
        **context: Additional context data
    """
    logger = logging.getLogger("audit")

    log_data = {
        "event_type": event_type,
        "audit_event": True,
        **context
    }

    if user_id:
        log_data["user_id"] = user_id
    if resource_type:
        log_data["resource_type"] = resource_type
    if resource_id:
        log_data["resource_id"] = resource_id
    if action:
        log_data["action"] = action

    logger.info(
        f"Audit event: {event_type}",
        extra=log_data
    )

def log_security_event(event_type: str, severity: str = "medium",
                      source_ip: str = None, user_agent: str = None,
                      **context) -> None:
    """Log security events.

    Common pattern for security event logging.

    Args:
        event_type: Type of security event
        severity: Severity level (low, medium, high, critical)
        source_ip: IP address of the source
        user_agent: User agent string
        **context: Additional context data
    """
    logger = logging.getLogger("security")

    log_data = {
        "event_type": event_type,
        "severity": severity,
        "security_event": True,
        **context
    }

    if source_ip:
        log_data["source_ip"] = source_ip
    if user_agent:
        log_data["user_agent"] = user_agent

    # Choose log level based on severity
    if severity == "critical":
        log_method = logger.critical
    elif severity == "high":
        log_method = logger.error
    elif severity == "medium":
        log_method = logger.warning
    else:
        log_method = logger.info

    log_method(
        f"Security event: {event_type} (severity: {severity})",
        extra=log_data
    )


# ============================================================================
# DECORATOR-BASED LOGGING (REDUCING DUPLICATION)
# ============================================================================

def log_method_calls(logger_name: str = None):
    """Decorator to log method calls with structured data.

    Common pattern for method-level logging.

    Args:
        logger_name: Name of logger to use (defaults to module logger)

    Returns:
        Decorator function

    Example:
        @log_method_calls()
        def my_method(self, arg1, arg2):
            return arg1 + arg2
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name or func.__module__)

            # Get method name and class if available
            if args and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
                method_name = f"{class_name}.{func.__qualname__}"
            else:
                method_name = func.__qualname__

            start_time = time.time()

            logger.debug(
                f"Calling method: {method_name}",
                extra={
                    "method": method_name,
                    "event_type": "method_call_start",
                    "args_count": len(args),
                    "kwargs_count": len(kwargs)
                }
            )

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                logger.debug(
                    f"Method completed: {method_name}",
                    extra={
                        "method": method_name,
                        "event_type": "method_call_end",
                        "duration_ms": duration_ms,
                        "success": True
                    }
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                logger.error(
                    f"Method failed: {method_name} - {e}",
                    extra={
                        "method": method_name,
                        "event_type": "method_call_end",
                        "duration_ms": duration_ms,
                        "success": False,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise

        return wrapper
    return decorator

def log_async_method_calls(logger_name: str = None):
    """Decorator to log async method calls with structured data.

    Common pattern for async method-level logging.

    Args:
        logger_name: Name of logger to use (defaults to module logger)

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name or func.__module__)

            # Get method name and class if available
            if args and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
                method_name = f"{class_name}.{func.__qualname__}"
            else:
                method_name = func.__qualname__

            start_time = time.time()

            logger.debug(
                f"Calling async method: {method_name}",
                extra={
                    "method": method_name,
                    "event_type": "async_method_call_start",
                    "args_count": len(args),
                    "kwargs_count": len(kwargs)
                }
            )

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                logger.debug(
                    f"Async method completed: {method_name}",
                    extra={
                        "method": method_name,
                        "event_type": "async_method_call_end",
                        "duration_ms": duration_ms,
                        "success": True
                    }
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                logger.error(
                    f"Async method failed: {method_name} - {e}",
                    extra={
                        "method": method_name,
                        "event_type": "async_method_call_end",
                        "duration_ms": duration_ms,
                        "success": False,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


# ============================================================================
# LOGGING CONFIGURATION HELPERS (REDUCING DUPLICATION)
# ============================================================================

def configure_structured_logging(service_name: str, log_level: str = "INFO",
                               enable_json: bool = False) -> None:
    """Configure structured logging for a service.

    Common pattern for service logging configuration.

    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Whether to use JSON formatting
    """
    import logging
    import sys

    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(level)

    # Remove existing handlers
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)

    # Create formatter
    if enable_json:
        try:
            import json
            class JSONFormatter(logging.Formatter):
                def format(self, record):
                    log_data = {
                        "timestamp": record.created,
                        "level": record.levelname,
                        "service": service_name,
                        "message": record.getMessage(),
                        "module": record.module,
                        "function": record.funcName,
                        "line": record.lineno
                    }

                    # Add extra fields
                    if hasattr(record, '__dict__'):
                        for key, value in record.__dict__.items():
                            if key not in ['name', 'msg', 'args', 'levelname', 'levelno',
                                         'pathname', 'filename', 'module', 'exc_info',
                                         'exc_text', 'stack_info', 'lineno', 'funcName',
                                         'created', 'msecs', 'relativeCreated', 'thread',
                                         'threadName', 'processName', 'process', 'message']:
                                log_data[key] = value

                    return json.dumps(log_data)
            formatter = JSONFormatter()
        except ImportError:
            formatter = logging.Formatter(
                f'%(asctime)s - {service_name} - %(levelname)s - %(name)s - %(message)s'
            )
    else:
        formatter = logging.Formatter(
            f'%(asctime)s - {service_name} - %(levelname)s - %(name)s - %(message)s'
        )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    # Configure specific loggers
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
