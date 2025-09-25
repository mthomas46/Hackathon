"""Enterprise Error Handling Framework

Modular error handling, recovery, and resilience framework for enterprise applications.
Provides comprehensive error management across all services with intelligent recovery.
"""

from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from .decorators import (
    enterprise_error_handler_decorator,
    circuit_breaker,
    retry_on_failure,
)
from .error_context import ErrorContext, RecoveryAction
from .error_handler import EnterpriseErrorHandler
from .error_types import ErrorSeverity, ErrorCategory, RecoveryStrategy
from .utils import create_error_context, handle_service_error

__all__ = [
    # Error types
    "ErrorSeverity",
    "ErrorCategory",
    "RecoveryStrategy",

    # Error context
    "ErrorContext",
    "RecoveryAction",

    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerOpenException",

    # Error handler
    "EnterpriseErrorHandler",

    # Decorators
    "enterprise_error_handler_decorator",
    "circuit_breaker",
    "retry_on_failure",

    # Utilities
    "create_error_context",
    "handle_service_error",
]