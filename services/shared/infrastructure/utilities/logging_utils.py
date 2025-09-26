"""Common logging utilities for Doc Store infrastructure.

Reduces code duplication by providing standardized logging patterns
across infrastructure components.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def log_operation_start(operation: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log the start of an operation.

    Args:
        operation: Name of the operation
        context: Optional additional context for logging
    """
    log_context = {"operation": operation}
    if context:
        log_context.update(context)

    logger.info(f"Starting {operation}", extra=log_context)


def log_operation_success(operation: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log successful completion of an operation.

    Args:
        operation: Name of the operation
        context: Optional additional context for logging
    """
    log_context = {"operation": operation, "status": "success"}
    if context:
        log_context.update(context)

    logger.info(f"Completed {operation} successfully", extra=log_context)


def log_operation_error(operation: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an error that occurred during an operation.

    Args:
        operation: Name of the operation
        error: Exception that occurred
        context: Optional additional context for logging
    """
    log_context = {
        "operation": operation,
        "status": "error",
        "error_type": type(error).__name__,
        "error_message": str(error)
    }
    if context:
        log_context.update(context)

    logger.error(f"Failed to {operation}: {error}", extra=log_context, exc_info=True)


def log_resource_status(resource_type: str, status: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log resource status changes.

    Args:
        resource_type: Type of resource (e.g., "monitoring", "cache")
        status: Status change (e.g., "started", "stopped")
        context: Optional additional context for logging
    """
    log_context = {"resource_type": resource_type, "status": status}
    if context:
        log_context.update(context)

    logger.info(f"Doc Store {resource_type} {status}", extra=log_context)


def log_api_request_error(endpoint: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log API request errors.

    Args:
        endpoint: API endpoint that failed
        error: Exception that occurred
        context: Optional additional context for logging
    """
    log_context = {
        "endpoint": endpoint,
        "error_type": type(error).__name__,
        "error_message": str(error)
    }
    if context:
        log_context.update(context)

    logger.error(f"Unhandled exception in {endpoint}: {error}", exc_info=True, extra=log_context)


class OperationLogger:
    """Helper class for logging operations with consistent patterns.

    Provides context managers and decorators for operation logging.
    """

    def __init__(self, operation_name: str, context: Optional[Dict[str, Any]] = None):
        """Initialize operation logger.

        Args:
            operation_name: Name of the operation to log
            context: Optional additional context for all logs
        """
        self.operation_name = operation_name
        self.base_context = context or {}

    def log_start(self, additional_context: Optional[Dict[str, Any]] = None) -> None:
        """Log operation start."""
        context = {**self.base_context}
        if additional_context:
            context.update(additional_context)
        log_operation_start(self.operation_name, context)

    def log_success(self, additional_context: Optional[Dict[str, Any]] = None) -> None:
        """Log operation success."""
        context = {**self.base_context}
        if additional_context:
            context.update(additional_context)
        log_operation_success(self.operation_name, context)

    def log_error(self, error: Exception, additional_context: Optional[Dict[str, Any]] = None) -> None:
        """Log operation error."""
        context = {**self.base_context}
        if additional_context:
            context.update(additional_context)
        log_operation_error(self.operation_name, error, context)


def log_with_context(operation: str, context: Optional[Dict[str, Any]] = None):
    """Decorator to add operation logging to functions.

    Args:
        operation: Operation name for logging
        context: Optional additional context for logging

    Returns:
        Decorated function with logging
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = OperationLogger(operation, context)

            try:
                logger.log_start({
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                })

                result = func(*args, **kwargs)

                logger.log_success({"function": func.__name__})
                return result

            except Exception as e:
                logger.log_error(e, {"function": func.__name__})
                raise

        return wrapper
    return decorator


class APILogger:
    """Helper class for API-specific logging patterns."""

    @staticmethod
    def log_endpoint_error(endpoint: str, error: Exception, request_context: Optional[Dict[str, Any]] = None) -> None:
        """Log API endpoint errors with request context.

        Args:
            endpoint: API endpoint path
            error: Exception that occurred
            request_context: Optional request context (method, user, etc.)
        """
        context = {"endpoint": endpoint}
        if request_context:
            context.update(request_context)
        log_api_request_error(endpoint, error, context)

    @staticmethod
    def log_resource_operation(resource: str, operation: str, status: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log resource management operations.

        Args:
            resource: Resource name (e.g., "cache", "monitoring")
            operation: Operation performed (e.g., "invalidate", "reset")
            status: Operation status ("started", "completed", "failed")
            context: Optional additional context
        """
        context = context or {}
        context.update({"resource": resource, "operation": operation})
        log_resource_status(f"{resource} {operation}", status, context)
