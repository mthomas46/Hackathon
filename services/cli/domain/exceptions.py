"""Domain-specific exceptions for CLI service.

This module defines exceptions specific to the CLI domain,
following the shared exception hierarchy for consistent error handling.
"""

from services.shared.domain.exceptions import (
    DomainError,
    ValidationError,
    ServiceError,
    ExternalServiceError
)


class CliError(DomainError):
    """Base exception for CLI-related errors."""
    pass


class CliValidationError(ValidationError):
    """CLI validation error."""
    pass


class CliServiceError(ServiceError):
    """Error in CLI service operations."""
    pass


class CliCommandError(CliError):
    """Error executing CLI command."""
    pass


class CliConfigurationError(CliError):
    """CLI configuration error."""
    pass


class CliNetworkError(ExternalServiceError):
    """Network communication error in CLI."""
    pass


class CliTimeoutError(CliNetworkError):
    """Timeout error in CLI operations."""
    pass


class CliAuthenticationError(CliError):
    """Authentication error in CLI."""
    pass


class CliAuthorizationError(CliError):
    """Authorization error in CLI."""
    pass


class CliInputError(CliValidationError):
    """Invalid input provided to CLI."""
    pass


class CliOutputError(CliError):
    """Error in CLI output generation."""
    pass


class CliCacheError(CliError):
    """Error in CLI caching operations."""
    pass
