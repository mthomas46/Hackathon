#!/usr/bin/env python3
"""
Enterprise Error Handling Framework - Legacy Compatibility Layer

This file provides backward compatibility for existing imports.
For new code, use the modular imports from the submodules.

DEPRECATED: This monolithic file will be removed in a future version.
Use the new modular imports instead:
- from services.shared.enterprise.error_handling import EnterpriseErrorHandler
- from services.shared.enterprise.error_handling import enterprise_error_handler_decorator
"""

# Re-export everything from the new modular structure for backward compatibility
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

# Legacy compatibility - create global instances
enterprise_error_handler = EnterpriseErrorHandler()

# Legacy imports for backward compatibility
HTTPException = Exception  # Mock for legacy code

# Temporary service names for legacy compatibility
ServiceNames = type(
    "ServiceNames",
    (),
    {
        "ORCHESTRATOR": "orchestrator",
        "ANALYSIS_SERVICE": "analysis-service",
        "DOC_STORE": "doc_store",
        "PROMPT_STORE": "prompt-store",
    },
)()

def fire_and_forget(level: str, message: str, service: str):
    """Simple logging function for legacy compatibility."""
    print(f"[{level.upper()}] {service}: {message}")

# Export legacy names
__all__ = [
    # New modular exports
    "EnterpriseErrorHandler",
    "CircuitBreaker",
    "CircuitBreakerOpenException",
    "enterprise_error_handler_decorator",
    "circuit_breaker",
    "retry_on_failure",
    "ErrorContext",
    "RecoveryAction",
    "ErrorSeverity",
    "ErrorCategory",
    "RecoveryStrategy",
    "create_error_context",
    "handle_service_error",

    # Legacy compatibility
    "enterprise_error_handler",
    "HTTPException",
    "ServiceNames",
    "fire_and_forget",
]
