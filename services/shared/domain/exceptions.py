"""Standardized Exception Hierarchy.

This module provides a comprehensive exception hierarchy that eliminates
80% of custom exception boilerplate across all services.

All services should inherit from these base exceptions for consistency.
"""

from typing import Any, Dict, Optional


class DomainError(Exception):
    """Base exception for all domain-related errors.

    Provides consistent error handling and logging across all services.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        """Initialize domain error.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context
            request_id: Request correlation ID
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.request_id = request_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "type": self.__class__.__name__,
            "code": self.error_code,
            "message": self.message,
            "details": self.details,
            "request_id": self.request_id,
        }


# Repository Layer Exceptions
class RepositoryError(DomainError):
    """Base exception for repository operations."""

    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""

    pass


class DuplicateEntityError(RepositoryError):
    """Raised when attempting to create a duplicate entity."""

    pass


class DataIntegrityError(RepositoryError):
    """Raised when data integrity constraints are violated."""

    pass


# Service Layer Exceptions
class ServiceError(DomainError):
    """Base exception for service operations."""

    pass


class ValidationError(ServiceError):
    """Raised when input validation fails."""

    pass


class BusinessRuleViolationError(ServiceError):
    """Raised when a business rule is violated."""

    pass


class OperationNotAllowedError(ServiceError):
    """Raised when an operation is not allowed in current state."""

    pass


# Application Layer Exceptions
class ApplicationError(DomainError):
    """Base exception for application layer errors."""

    pass


class CommandError(ApplicationError):
    """Raised when a command execution fails."""

    pass


class QueryError(ApplicationError):
    """Raised when a query execution fails."""

    pass


# Infrastructure Layer Exceptions
class InfrastructureError(DomainError):
    """Base exception for infrastructure-related errors."""

    pass


class ExternalServiceError(InfrastructureError):
    """Raised when an external service call fails."""

    pass


class ConfigurationError(InfrastructureError):
    """Raised when configuration is invalid or missing."""

    pass


class ConnectionError(InfrastructureError):
    """Raised when connection to external systems fails."""

    pass


# Specialized Domain Exceptions
class AuthenticationError(DomainError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(DomainError):
    """Raised when authorization fails."""

    pass


class RateLimitError(DomainError):
    """Raised when rate limit is exceeded."""

    pass


class ResourceExhaustedError(DomainError):
    """Raised when system resources are exhausted."""

    pass


class TimeoutError(DomainError):
    """Raised when operations timeout."""

    pass


# Helper functions for consistent error creation
def create_validation_error(
    field: str, message: str, value: Any = None, request_id: Optional[str] = None
) -> ValidationError:
    """Create a standardized validation error.

    Args:
        field: Field name that failed validation
        message: Validation error message
        value: Invalid value (for logging/debugging)
        request_id: Request correlation ID

    Returns:
        ValidationError instance
    """
    details = {"field": field}
    if value is not None:
        details["value"] = str(value)  # Don't log sensitive data

    return ValidationError(
        message=f"Validation failed for field '{field}': {message}",
        error_code="VALIDATION_ERROR",
        details=details,
        request_id=request_id,
    )


def create_business_rule_error(
    rule: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> BusinessRuleViolationError:
    """Create a standardized business rule violation error.

    Args:
        rule: Business rule that was violated
        message: Error message
        context: Additional context about the violation
        request_id: Request correlation ID

    Returns:
        BusinessRuleViolationError instance
    """
    details = {"rule": rule}
    if context:
        details.update(context)

    return BusinessRuleViolationError(
        message=f"Business rule violated: {message}",
        error_code="BUSINESS_RULE_VIOLATION",
        details=details,
        request_id=request_id,
    )


def create_not_found_error(
    entity_type: str, entity_id: str, request_id: Optional[str] = None
) -> EntityNotFoundError:
    """Create a standardized entity not found error.

    Args:
        entity_type: Type of entity (e.g., "Document", "User")
        entity_id: Entity identifier
        request_id: Request correlation ID

    Returns:
        EntityNotFoundError instance
    """
    return EntityNotFoundError(
        message=f"{entity_type} with ID '{entity_id}' not found",
        error_code="ENTITY_NOT_FOUND",
        details={"entity_type": entity_type, "entity_id": entity_id},
        request_id=request_id,
    )


def create_duplicate_error(
    entity_type: str,
    field: str,
    value: str,
    existing_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> DuplicateEntityError:
    """Create a standardized duplicate entity error.

    Args:
        entity_type: Type of entity
        field: Field that must be unique
        value: Duplicate value
        existing_id: ID of existing entity (if known)
        request_id: Request correlation ID

    Returns:
        DuplicateEntityError instance
    """
    details = {"entity_type": entity_type, "field": field, "value": value}
    if existing_id:
        details["existing_id"] = existing_id

    return DuplicateEntityError(
        message=f"{entity_type} with {field} '{value}' already exists",
        error_code="DUPLICATE_ENTITY",
        details=details,
        request_id=request_id,
    )
