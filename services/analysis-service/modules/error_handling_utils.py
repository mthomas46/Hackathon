"""Error Handling Utilities for Analysis Service.

This module provides centralized error handling patterns and standardized
error response formats to reduce code duplication across the analysis service.
"""

import logging
from typing import Any, Dict, Optional
from functools import wraps

logger = logging.getLogger(__name__)


def create_error_response(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    status: str = "error",
    **additional_fields
) -> Dict[str, Any]:
    """Create a standardized error response dictionary.

    Args:
        error: The exception that occurred
        context: Additional context information
        status: Status string (default: "error")
        **additional_fields: Additional fields to include in response

    Returns:
        Standardized error response dictionary
    """
    response = {
        "status": status,
        "error": str(error),
        "error_type": type(error).__name__,
    }

    if context:
        response.update(context)

    response.update(additional_fields)

    return response


def create_success_response(
    data: Any = None,
    message: Optional[str] = None,
    **additional_fields
) -> Dict[str, Any]:
    """Create a standardized success response dictionary.

    Args:
        data: Response data
        message: Success message
        **additional_fields: Additional fields to include

    Returns:
        Standardized success response dictionary
    """
    response = {"status": "success"}

    if data is not None:
        response["data"] = data

    if message:
        response["message"] = message

    response.update(additional_fields)

    return response


def handle_analysis_error(
    operation: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    log_level: int = logging.ERROR
) -> Dict[str, Any]:
    """Handle analysis errors with standardized logging and response.

    Args:
        operation: Name of the operation that failed
        error: The exception that occurred
        context: Additional context for logging
        log_level: Logging level to use

    Returns:
        Standardized error response
    """
    context = context or {}
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())

    logger.log(
        log_level,
        f"Analysis operation '{operation}' failed: {error}. Context: {context_str}",
        exc_info=True
    )

    return create_error_response(
        error,
        context=context,
        operation=operation
    )


def safe_analysis_operation(
    operation_name: str,
    default_result: Any = None,
    log_errors: bool = True
):
    """Decorator for safe analysis operations with standardized error handling.

    Args:
        operation_name: Name of the operation for logging
        default_result: Default result to return on error
        log_errors: Whether to log errors

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    handle_analysis_error(operation_name, e, kwargs)
                return default_result

        return wrapper
    return decorator


def safe_sync_operation(
    operation_name: str,
    default_result: Any = None,
    log_errors: bool = True
):
    """Decorator for safe synchronous operations with standardized error handling.

    Args:
        operation_name: Name of the operation for logging
        default_result: Default result to return on error
        log_errors: Whether to log errors

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    handle_analysis_error(operation_name, e, kwargs)
                return default_result

        return wrapper
    return decorator


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> Optional[str]:
    """Validate that required fields are present in data.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Returns:
        Error message if validation fails, None if successful
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"

    return None


def validate_data_types(data: Dict[str, Any], type_requirements: Dict[str, type]) -> Optional[str]:
    """Validate data types for specified fields.

    Args:
        data: Data dictionary to validate
        type_requirements: Dict mapping field names to expected types

    Returns:
        Error message if validation fails, None if successful
    """
    for field, expected_type in type_requirements.items():
        if field in data:
            value = data[field]
            if not isinstance(value, expected_type):
                return f"Field '{field}' must be of type {expected_type.__name__}, got {type(value).__name__}"

    return None


def create_analysis_context(
    operation: str,
    **context_data
) -> Dict[str, Any]:
    """Create standardized analysis context for logging and monitoring.

    Args:
        operation: Operation name
        **context_data: Additional context data

    Returns:
        Context dictionary with operation and additional data
    """
    context = {"operation": operation, "service": "analysis-service"}
    context.update(context_data)
    return context


# Legacy compatibility functions for gradual migration
def standard_error_response(error: Exception, **context) -> Dict[str, Any]:
    """Legacy compatibility function for error responses."""
    return create_error_response(error, context)


def standard_success_response(data: Any = None, **additional_fields) -> Dict[str, Any]:
    """Legacy compatibility function for success responses."""
    return create_success_response(data, **additional_fields)
