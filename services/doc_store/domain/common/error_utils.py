"""Common error handling utilities for Doc Store service.

Reduces code duplication by providing standardized error handling patterns
across all domain services and API endpoints.

NOTE: This module only contains domain-level utilities and does NOT depend on infrastructure.
Infrastructure-specific error handling should be done at the application/presentation layer.
"""

from typing import Any, Dict, Optional

# Domain-level exceptions - no infrastructure dependencies
class DomainException(Exception):
    """Base exception for domain errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DomainValidationException(DomainException):
    """Exception raised when domain validation fails."""
    pass

class DomainNotFoundException(DomainException):
    """Exception raised when a domain entity is not found."""
    pass

class DomainConflictException(DomainException):
    """Exception raised when domain conflicts occur."""
    pass

class DomainExternalServiceException(DomainException):
    """Exception raised when external service calls fail."""
    pass

class DomainDatabaseException(DomainException):
    """Exception raised when database operations fail."""
    pass


def handle_document_not_found(document_id: str, operation: str = "find") -> None:
    """Raise standardized exception for document not found.

    Args:
        document_id: ID of the document that was not found
        operation: Operation being performed

    Raises:
        DomainNotFoundException: Always raised
    """
    raise DomainNotFoundException(f"Document not found during {operation}: {document_id}")


def handle_validation_error(field: str, message: str) -> None:
    """Raise standardized validation exception.

    Args:
        field: Field name that failed validation
        message: Validation error message

    Raises:
        DomainValidationException: Always raised
    """
    raise DomainValidationException(f"Validation failed for {field}: {message}")


def handle_conflict_error(resource_type: str, resource_id: str, message: Optional[str] = None) -> None:
    """Raise standardized conflict exception.

    Args:
        resource_type: Type of resource causing conflict
        resource_id: ID of the conflicting resource
        message: Optional custom message

    Raises:
        DomainConflictException: Always raised
    """
    default_message = f"{resource_type} with ID {resource_id} already exists"
    raise DomainConflictException(message or default_message)


def handle_database_error(operation: str, original_error: Optional[str] = None) -> None:
    """Raise standardized database exception.

    Args:
        operation: Database operation that failed
        original_error: Optional original error message

    Raises:
        DomainDatabaseException: Always raised
    """
    raise DomainDatabaseException(f"Database operation '{operation}' failed: {original_error or 'Unknown database error'}")


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
        DomainExternalServiceException: Always raised
    """
    raise DomainExternalServiceException(f"External service '{service_name}' operation '{operation}' failed: {original_error or 'Unknown error'}")


def create_domain_error_details(
    exception: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized domain error details from exception.

    Args:
        exception: Exception to convert to error details
        operation: Operation that failed
        context: Optional additional context

    Returns:
        Standardized error details dictionary
    """
    details = {
        "operation": operation,
        "exception_type": type(exception).__name__,
        "exception_message": str(exception)
    }

    if context:
        details.update(context)

    # Add specific details based on exception type
    if isinstance(exception, DomainValidationException):
        details["error_type"] = "validation"
    elif isinstance(exception, DomainNotFoundException):
        details["error_type"] = "not_found"
    elif isinstance(exception, DomainConflictException):
        details["error_type"] = "conflict"
    elif isinstance(exception, DomainDatabaseException):
        details["error_type"] = "database"
    elif isinstance(exception, DomainExternalServiceException):
        details["error_type"] = "external_service"
    else:
        details["error_type"] = "general"

    return details


def handle_domain_error(
    exception: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> DomainException:
    """Handle domain exception by wrapping in appropriate domain exception type.

    Args:
        exception: Exception to handle
        operation: Operation that failed
        context: Optional additional context

    Returns:
        Appropriate domain exception
    """
    error_details = create_domain_error_details(exception, operation, context)

    # If it's already a domain exception, return it with enhanced details
    if isinstance(exception, DomainException):
        if not exception.details:
            exception.details = error_details
        return exception

    # Wrap standard exceptions in domain exceptions
    if isinstance(exception, ValueError):
        return DomainValidationException(str(exception), error_details)
    elif isinstance(exception, KeyError):
        return DomainValidationException(f"Required field missing: {exception}", error_details)
    elif isinstance(exception, TypeError):
        return DomainValidationException(f"Invalid data type: {exception}", error_details)
    else:
        return DomainException(f"Domain operation '{operation}' failed: {exception}", error_details)


def validate_domain_operation(func):
    """Decorator to add standardized error handling to domain methods.

    Catches common exceptions and converts them to domain exceptions.
    Should be used on domain service methods.
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DomainException:
            # Re-raise domain exceptions as-is
            raise
        except (ValueError, KeyError, TypeError) as e:
            # Wrap validation errors in domain exceptions
            raise handle_domain_error(e, func.__name__, {
                "function": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            })
        except Exception as e:
            # Wrap unexpected errors in domain exceptions
            raise DomainException(f"Unexpected error in {func.__name__}: {e}", {
                "function": func.__name__,
                "error_type": "unexpected",
                "original_error": str(e)
            })

    return wrapper


class DomainErrorHandler:
    """Domain-level error handling for Doc Store operations.

    This class provides domain-focused error handling without infrastructure dependencies.
    Infrastructure-specific error handling should be done at the application layer.
    """

    def handle_document_operation_error(
        self,
        exception: Exception,
        operation: str,
        document_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> DomainException:
        """Handle errors from document operations.

        Args:
            exception: Exception that occurred
            operation: Operation being performed
            document_id: Optional document ID for context
            context: Optional additional context

        Returns:
            Domain exception with standardized details
        """
        error_context = {"operation": operation}
        if document_id:
            error_context["document_id"] = document_id
        if context:
            error_context.update(context)

        return handle_domain_error(exception, operation, error_context)

    def handle_bulk_operation_error(
        self,
        exception: Exception,
        operation_id: str,
        processed_count: int,
        context: Optional[Dict[str, Any]] = None
    ) -> DomainException:
        """Handle errors from bulk operations.

        Args:
            exception: Exception that occurred
            operation_id: Bulk operation identifier
            processed_count: Number of items processed before error
            context: Optional additional context

        Returns:
            Domain exception with standardized details
        """
        error_context = {
            "operation_id": operation_id,
            "processed_count": processed_count,
            "operation_type": "bulk"
        }
        if context:
            error_context.update(context)

        return handle_domain_error(exception, "bulk_operation", error_context)

    def handle_search_operation_error(
        self,
        exception: Exception,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DomainException:
        """Handle errors from search operations.

        Args:
            exception: Exception that occurred
            query: Search query that caused the error
            context: Optional additional context

        Returns:
            Domain exception with standardized details
        """
        error_context = {"query": query, "operation_type": "search"}
        if context:
            error_context.update(context)

        return handle_domain_error(exception, "search", error_context)

    def handle_analytics_operation_error(
        self,
        exception: Exception,
        time_range: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> DomainException:
        """Handle errors from analytics operations.

        Args:
            exception: Exception that occurred
            time_range: Optional time range for the analytics query
            context: Optional additional context

        Returns:
            Domain exception with standardized details
        """
        error_context = {"operation_type": "analytics"}
        if time_range:
            error_context["time_range"] = time_range
        if context:
            error_context.update(context)

        return handle_domain_error(exception, "analytics", error_context)
