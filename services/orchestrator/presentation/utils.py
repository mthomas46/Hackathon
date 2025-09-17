"""Presentation Layer Utilities

Utility functions for the presentation layer (API routes and DTOs).
These functions handle common presentation concerns like response formatting and request processing.
"""

from typing import Dict, Any, Optional

from services.shared.constants_new import ErrorCodes
from services.shared.responses import create_success_response, create_error_response
from services.shared.logging import fire_and_forget
from services.shared.constants_new import ServiceNames


def handle_service_error(operation: str, error: Exception, **context) -> Dict[str, Any]:
    """Standardized error handling for service operations."""
    fire_and_forget("error", f"Service {operation} error: {error}", ServiceNames.ORCHESTRATOR, context)
    return create_error_response(
        f"Failed to {operation}",
        error_code=ErrorCodes.SERVICE_COMMUNICATION_FAILED,
        details={"error": str(error), **context}
    )


def create_service_success_response(operation: str, data: Any, **context) -> Dict[str, Any]:
    """Standardized success response creation for service operations."""
    fire_and_forget("info", f"Service {operation} completed successfully", ServiceNames.ORCHESTRATOR, context)
    return create_success_response(
        f"Service {operation} completed successfully",
        data,
        **context
    )


def build_operation_context(operation: str, **kwargs) -> Dict[str, Any]:
    """Build standardized operation context for logging and responses."""
    context = {"operation": operation}
    context.update(kwargs)
    return context


def extract_pagination_params(
    page: int = 1,
    limit: int = 50,
    max_limit: int = 1000
) -> tuple[int, int]:
    """Extract and validate pagination parameters."""
    page = max(1, page)
    limit = max(1, min(limit, max_limit))
    offset = (page - 1) * limit
    return offset, limit


def format_paginated_response(
    items: list,
    total: int,
    offset: int,
    limit: int,
    **metadata
) -> Dict[str, Any]:
    """Format a paginated response."""
    return {
        "items": items,
        "total": total,
        "page": (offset // limit) + 1,
        "limit": limit,
        "has_more": (offset + len(items)) < total,
        **metadata
    }


__all__ = [
    'handle_service_error',
    'create_service_success_response',
    'build_operation_context',
    'extract_pagination_params',
    'format_paginated_response'
]
