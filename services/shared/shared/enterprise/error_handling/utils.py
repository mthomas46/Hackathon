"""Utility functions for error handling."""

import traceback
from typing import Any, Dict


def create_error_context(
    service_name: str,
    operation: str,
    error: Exception,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized error context dictionary."""
    return {
        "service_name": service_name,
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "stack_trace": traceback.format_exc(),
        "metadata": metadata or {},
    }


def handle_service_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle service errors with standardized response."""
    return {
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "service": context.get("service_name", "unknown"),
            "operation": context.get("operation", "unknown"),
        },
        "recovery": {
            "suggested_action": "log_and_monitor",
            "severity": "medium",
        },
        "context": context,
    }
