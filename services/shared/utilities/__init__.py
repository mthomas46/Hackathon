"""Shared Utilities Package.

This package contains utility functions and helpers used across all services
in the LLM Documentation Ecosystem.

Modules:
- utilities: Core utility functions
- middleware: HTTP middleware components
- error_handling: Standardized error handling
- helpers: Additional helper functions
- validation: Input validation utilities
- observability: Monitoring and observability helpers
- resilience: Circuit breaker and retry logic
"""

# Import and expose key functions for easy access
from .utilities import (
    utc_now,
    attach_self_register,
    setup_common_middleware,
    iso_datetime,
    generate_id,
    safe_filename,
    clean_string,
    get_service_client
)

from .middleware import ServiceMiddleware
from .error_handling import ServiceException, ValidationException
# from .observability import setup_logging, fire_and_forget  # Not implemented yet
from .resilience import CircuitBreaker

__all__ = [
    # Core utilities
    'utc_now',
    'attach_self_register',
    'setup_common_middleware',
    'iso_datetime',
    'generate_id',
    'safe_filename',
    'clean_string',
    'get_service_client',

    # Middleware
    'ServiceMiddleware',

    # Error handling
    'ServiceException',
    'ValidationException',

    # Observability
    # 'setup_logging',  # Not implemented yet
    # 'fire_and_forget',  # Not implemented yet

    # Resilience
    'CircuitBreaker'
]