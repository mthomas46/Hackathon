"""Common error handling utilities for Doc Store service.

Reduces code duplication by providing standardized error handling patterns
across all domain services and API endpoints.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException

from services.shared.infrastructure.utilities.error_handling import (
    ServiceException,
    ValidationException,
    NotFoundException,
    ConflictException,
    ExternalServiceException,
    DatabaseException,
)
from services.shared.presentation.responses import create_error_response


def handle_document_not_found(document_id: str, operation: str = "find") -> None:
    """Raise standardized exception for document not found.

    Args:
        document_id: ID of the document that was not found
        operation: Operation being performed

    Raises:
        NotFoundException: Always raised
    """
    raise NotFoundException("document", document_id)


def handle_validation_error(field: str, message: str) -> None:
    """Raise standardized validation exception.

    Args:
        field: Field name that failed validation
        message: Validation error message

    Raises:
        ValidationException: Always raised
    """
    raise ValidationException({field: [message]})


def handle_conflict_error(resource_type: str, resource_id: str, message: Optional[str] = None) -> None:
    """Raise standardized conflict exception.

    Args:
        resource_type: Type of resource causing conflict
        resource_id: ID of the conflicting resource
        message: Optional custom message

    Raises:
        ConflictException: Always raised
    """
    default_message = f"{resource_type} with ID {resource_id} already exists"
    raise ConflictException(message or default_message)


def handle_database_error(operation: str, original_error: Optional[str] = None) -> None:
    """Raise standardized database exception.

    Args:
        operation: Database operation that failed
        original_error: Optional original error message

    Raises:
        DatabaseException: Always raised
    """
    raise DatabaseException(operation, original_error or "Unknown database error")


def handle_external_service_error(
    service_name: str,
    operation: str,
    original_error: Optional[str] = None
) -> None:
    """Raise standardized external service exception.

    Args:
        service_name: Name of the external service
        operation: Operation that failed
        original_error: Optional original error message

    Raises:
        ExternalServiceException: Always raised
    """
    raise ExternalServiceException(service_name, operation, original_error)


def create_api_error_response(
    exception: Exception,
    status_code: Optional[int] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Create standardized API error response from exception.

    Args:
        exception: Exception to convert to API response
        status_code: Optional custom status code
        message: Optional custom message

    Returns:
        Standardized error response dictionary
    """
    if isinstance(exception, ServiceException):
        return create_error_response(
            message=message or exception.message,
            error_code=exception.error_code,
            details=exception.details
        )

    # Handle standard exceptions
    if isinstance(exception, ValueError):
        return create_error_response(
            message=message or str(exception),
            error_code="validation_error",
            details={"original_error": str(exception)}
        )

    if isinstance(exception, KeyError):
        return create_error_response(
            message=message or "Required field missing",
            error_code="missing_field",
            details={"field": str(exception), "original_error": str(exception)}
        )

    if isinstance(exception, TypeError):
        return create_error_response(
            message=message or "Invalid data type",
            error_code="type_error",
            details={"original_error": str(exception)}
        )

    # Generic error handling
    return create_error_response(
        message=message or "An unexpected error occurred",
        error_code="internal_error",
        details={"original_error": str(exception)}
    )


def handle_and_log_error(
    exception: Exception,
    operation: str,
    logger: Any,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Handle exception with logging and return standardized error response.

    Args:
        exception: Exception to handle
        operation: Operation that failed
        logger: Logger instance to use
        context: Optional additional context for logging

    Returns:
        Standardized error response dictionary
    """
    error_context = {
        "operation": operation,
        "exception_type": type(exception).__name__,
        "exception_message": str(exception)
    }

    if context:
        error_context.update(context)

    logger.error(
        f"Error during {operation}",
        extra=error_context,
        exc_info=True
    )

    return create_api_error_response(exception)


def validate_and_handle_errors(func):
    """Decorator to add standardized error handling to service methods.

    Catches common exceptions and converts them to standardized responses.
    Should be used on service methods that are called by API endpoints.
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ServiceException:
            # Re-raise service exceptions as-is
            raise
        except ValueError as e:
            raise ValidationException(str(e))
        except KeyError as e:
            raise ValidationException(f"Required field missing: {e}")
        except Exception as e:
            # Log unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Unexpected error in {func.__name__}",
                extra={
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "error": str(e)
                },
                exc_info=True
            )
            raise ServiceException(f"Internal error: {e}")

    return wrapper


class ErrorHandler:
    """Centralized error handling for Doc Store operations."""

    def __init__(self, logger: Any):
        """Initialize error handler with logger.

        Args:
            logger: Logger instance to use for error logging
        """
        self.logger = logger

    def handle_document_operation_error(
        self,
        exception: Exception,
        operation: str,
        document_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle errors from document operations.

        Args:
            exception: Exception that occurred
            operation: Operation being performed
            document_id: Optional document ID for context
            context: Optional additional context

        Returns:
            Standardized error response
        """
        error_context = {"operation": operation}
        if document_id:
            error_context["document_id"] = document_id
        if context:
            error_context.update(context)

        return handle_and_log_error(exception, operation, self.logger, error_context)

    def handle_bulk_operation_error(
        self,
        exception: Exception,
        operation_id: str,
        processed_count: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle errors from bulk operations.

        Args:
            exception: Exception that occurred
            operation_id: Bulk operation identifier
            processed_count: Number of items processed before error
            context: Optional additional context

        Returns:
            Standardized error response
        """
        error_context = {
            "operation_id": operation_id,
            "processed_count": processed_count
        }
        if context:
            error_context.update(context)

        return handle_and_log_error(exception, "bulk_operation", self.logger, error_context)

    def handle_search_error(
        self,
        exception: Exception,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle errors from search operations.

        Args:
            exception: Exception that occurred
            query: Search query that caused the error
            context: Optional additional context

        Returns:
            Standardized error response
        """
        error_context = {"query": query}
        if context:
            error_context.update(context)

        return handle_and_log_error(exception, "search", self.logger, error_context)

    def handle_analytics_error(
        self,
        exception: Exception,
        time_range: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle errors from analytics operations.

        Args:
            exception: Exception that occurred
            time_range: Optional time range for the analytics query
            context: Optional additional context

        Returns:
            Standardized error response
        """
        error_context = {}
        if time_range:
            error_context["time_range"] = time_range
        if context:
            error_context.update(context)

        return handle_and_log_error(exception, "analytics", self.logger, error_context)
