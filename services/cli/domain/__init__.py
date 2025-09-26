"""Domain layer for CLI service.

This layer contains the core business logic, domain entities, value objects,
and domain services that represent the CLI service's domain model.
"""

from .exceptions import CliError, CliCommandError, CliValidationError

__all__ = [
    "CliError",
    "CliCommandError",
    "CliValidationError",
]
