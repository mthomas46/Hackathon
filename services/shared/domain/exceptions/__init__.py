"""Domain Exceptions - Business Rule Violations.

This module contains domain-specific exception classes and helper functions
following Domain-Driven Design principles.
"""

from .exceptions import (
    # Base exceptions
    DomainError,

    # Repository layer
    RepositoryError, EntityNotFoundError, DuplicateEntityError, DataIntegrityError,

    # Service layer
    ServiceError, ValidationError, BusinessRuleViolationError, OperationNotAllowedError,

    # Application layer
    ApplicationError, CommandError, QueryError,

    # Infrastructure layer
    InfrastructureError, ExternalServiceError, ConfigurationError, ConnectionError,

    # Specialized exceptions
    AuthenticationError, AuthorizationError, RateLimitError,
    ResourceExhaustedError, TimeoutError,

    # Helper functions
    create_validation_error, create_business_rule_error,
    create_not_found_error, create_duplicate_error
)

__all__ = [
    "DomainError",
    "RepositoryError", "EntityNotFoundError", "DuplicateEntityError", "DataIntegrityError",
    "ServiceError", "ValidationError", "BusinessRuleViolationError", "OperationNotAllowedError",
    "ApplicationError", "CommandError", "QueryError",
    "InfrastructureError", "ExternalServiceError", "ConfigurationError", "ConnectionError",
    "AuthenticationError", "AuthorizationError", "RateLimitError",
    "ResourceExhaustedError", "TimeoutError",
    "create_validation_error", "create_business_rule_error",
    "create_not_found_error", "create_duplicate_error"
]
