"""Unified Response Handler System.

This module provides standardized HTTP response patterns for all services
in the LLM Documentation Ecosystem. Consolidates 11+ duplicate response
creation functions into a single, consistent API.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    """Standardized API response format for all services."""

    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Any] = Field(None, description="Response data payload")
    message: Optional[str] = Field(None, description="Human-readable message")
    errors: Optional[List[Dict[str, Any]]] = Field(
        None, description="Error details if applicable"
    )
    request_id: Optional[str] = Field(None, description="Request correlation ID")
    timestamp: str = Field(..., description="Response timestamp in ISO format")

    class Config:
        """Pydantic configuration."""

        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


def create_success_response(
    data: Any = None, message: str = "", request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create standardized success response.

    Args:
        data: Response payload data
        message: Success message (defaults to generic message)
        request_id: Request correlation ID

    Returns:
        Standardized success response dictionary
    """
    return APIResponse(
        success=True,
        data=data,
        message=message or "Operation completed successfully",
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat(),
    ).dict()


def create_error_response(
    message: str,
    error_code: Optional[str] = None,
    status_code: int = 500,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create standardized error response.

    Args:
        message: Error message
        error_code: Machine-readable error code
        status_code: HTTP status code (for reference)
        request_id: Request correlation ID
        details: Additional error context

    Returns:
        Standardized error response dictionary
    """
    return APIResponse(
        success=False,
        message=message,
        errors=(
            [
                {
                    "code": error_code,
                    "message": message,
                    "details": details,
                    "status_code": status_code,
                }
            ]
            if error_code
            else None
        ),
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat(),
    ).dict()


def create_validation_error_response(
    errors: Dict[str, List[str]], request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create validation error response.

    Args:
        errors: Dictionary mapping field names to error messages
        request_id: Request correlation ID

    Returns:
        Standardized validation error response
    """
    error_details = []
    for field, messages in errors.items():
        error_details.append({"field": field, "messages": messages})

    return APIResponse(
        success=False,
        message="Validation failed",
        errors=error_details,
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat(),
    ).dict()


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create paginated response.

    Args:
        items: List of items for current page
        total: Total number of items across all pages
        page: Current page number (1-based)
        page_size: Number of items per page
        request_id: Request correlation ID

    Returns:
        Standardized paginated response
    """
    return create_success_response(
        data={
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "has_next": page * page_size < total,
                "has_prev": page > 1,
            },
        },
        request_id=request_id,
    )


def create_list_response(
    items: List[Any], count: Optional[int] = None, request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create list response for simple collections.

    Args:
        items: List of items
        count: Total count (if different from items length)
        request_id: Request correlation ID

    Returns:
        Standardized list response
    """
    return create_success_response(
        data={"items": items, "count": count if count is not None else len(items)},
        request_id=request_id,
    )


def create_crud_response(
    operation: str,
    resource_id: Optional[str] = None,
    message: str = "",
    data: Any = None,
    request_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Create CRUD operation response.

    Args:
        operation: CRUD operation type (create, read, update, delete)
        resource_id: ID of the affected resource
        message: Custom success message
        data: Response data
        request_id: Request correlation ID
        **kwargs: Additional response data

    Returns:
        Standardized CRUD response
    """
    response_data = {"operation": operation, "resource_id": resource_id, **kwargs}

    if data is not None:
        response_data["data"] = data

    default_messages = {
        "create": f"Resource created successfully{' with ID ' + resource_id if resource_id else ''}",
        "read": "Resource retrieved successfully",
        "update": (
            f"Resource {resource_id} updated successfully"
            if resource_id
            else "Resource updated successfully"
        ),
        "delete": (
            f"Resource {resource_id} deleted successfully"
            if resource_id
            else "Resource deleted successfully"
        ),
    }

    return create_success_response(
        data=response_data,
        message=message
        or default_messages.get(operation, "Operation completed successfully"),
        request_id=request_id,
    )


# Service-specific response helpers
def create_service_success_response(
    service_name: str, operation: str, data: Any = None, **context
) -> Dict[str, Any]:
    """Create service-specific success response.

    Args:
        service_name: Name of the service
        operation: Operation being performed
        data: Response data
        **context: Additional context for the response

    Returns:
        Service-specific success response
    """
    return create_success_response(
        data={"service": service_name, "operation": operation, "data": data, **context},
        message=f"{service_name} operation '{operation}' completed successfully",
    )


def create_memory_agent_success_response(
    operation: str, data: Any = None, **context
) -> Dict[str, Any]:
    """Create memory agent specific success response.

    Args:
        operation: Memory operation type
        data: Response data
        **context: Additional context

    Returns:
        Memory agent response
    """
    return create_service_success_response(
        service_name="memory-agent", operation=operation, data=data, **context
    )


# Legacy compatibility aliases
# These maintain backward compatibility while encouraging migration to unified functions


def success_response(*args, **kwargs) -> Dict[str, Any]:
    """Legacy alias for create_success_response."""
    return create_success_response(*args, **kwargs)


def error_response(*args, **kwargs) -> Dict[str, Any]:
    """Legacy alias for create_error_response."""
    return create_error_response(*args, **kwargs)


def validation_error_response(*args, **kwargs) -> Dict[str, Any]:
    """Legacy alias for create_validation_error_response."""
    return create_validation_error_response(*args, **kwargs)


def paginated_response(*args, **kwargs) -> Dict[str, Any]:
    """Legacy alias for create_paginated_response."""
    return create_paginated_response(*args, **kwargs)


def list_response(*args, **kwargs) -> Dict[str, Any]:
    """Legacy alias for create_list_response."""
    return create_list_response(*args, **kwargs)


def crud_response(*args, **kwargs) -> Dict[str, Any]:
    """Legacy alias for create_crud_response."""
    return create_crud_response(*args, **kwargs)
