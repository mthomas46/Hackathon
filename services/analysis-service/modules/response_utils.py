"""Response Utilities for Analysis Service.

This module provides standardized response formatting functions to ensure
consistent API responses across all analysis service endpoints.
"""

import time
from typing import Any, Dict, List, Optional, Union


def create_analysis_response(
    status: str,
    data: Any = None,
    message: Optional[str] = None,
    execution_time: Optional[float] = None,
    **additional_fields
) -> Dict[str, Any]:
    """Create a standardized analysis API response.

    Args:
        status: Response status ("success", "error", "partial")
        data: Response data payload
        message: Human-readable message
        execution_time: Execution time in seconds
        **additional_fields: Additional response fields

    Returns:
        Standardized response dictionary
    """
    response = {
        "status": status,
        "timestamp": time.time(),
    }

    if data is not None:
        response["data"] = data

    if message:
        response["message"] = message

    if execution_time is not None:
        response["execution_time_seconds"] = round(execution_time, 3)

    response.update(additional_fields)

    return response


def create_findings_response(
    findings: List[Dict[str, Any]],
    total_count: Optional[int] = None,
    filtered_count: Optional[int] = None,
    **additional_fields
) -> Dict[str, Any]:
    """Create a standardized findings response.

    Args:
        findings: List of finding dictionaries
        total_count: Total number of findings available
        filtered_count: Number of findings after filtering
        **additional_fields: Additional response fields

    Returns:
        Standardized findings response
    """
    response = create_analysis_response(
        status="success",
        data=findings,
        findings_count=len(findings)
    )

    if total_count is not None:
        response["total_count"] = total_count

    if filtered_count is not None:
        response["filtered_count"] = filtered_count

    response.update(additional_fields)

    return response


def create_paginated_response(
    items: List[Any],
    page: int,
    page_size: int,
    total_count: int,
    **additional_fields
) -> Dict[str, Any]:
    """Create a paginated response.

    Args:
        items: Items for current page
        page: Current page number (1-based)
        page_size: Items per page
        total_count: Total number of items
        **additional_fields: Additional response fields

    Returns:
        Paginated response dictionary
    """
    total_pages = (total_count + page_size - 1) // page_size

    response = create_analysis_response(
        status="success",
        data=items,
        pagination={
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    )

    response.update(additional_fields)

    return response


def create_document_response(
    document: Dict[str, Any],
    include_metadata: bool = True,
    include_content: bool = True,
    **additional_fields
) -> Dict[str, Any]:
    """Create a standardized document response.

    Args:
        document: Document dictionary
        include_metadata: Whether to include metadata
        include_content: Whether to include content
        **additional_fields: Additional response fields

    Returns:
        Standardized document response
    """
    # Create a clean document response
    response_doc = {
        "id": document.get("id"),
        "title": document.get("title"),
        "type": document.get("type"),
    }

    if include_metadata:
        response_doc.update({
            "category": document.get("category"),
            "status": document.get("status"),
            "priority": document.get("priority"),
            "assignee": document.get("assignee"),
            "created_at": document.get("dateCreated"),
            "updated_at": document.get("dateUpdated"),
            "author": document.get("author"),
            "tags": document.get("tags", []),
        })

    if include_content:
        response_doc["content"] = document.get("content")

    return create_analysis_response(
        status="success",
        data=response_doc,
        **additional_fields
    )


def create_health_response(
    status: str,
    services: Dict[str, str],
    metrics: Optional[Dict[str, Any]] = None,
    **additional_fields
) -> Dict[str, Any]:
    """Create a standardized health check response.

    Args:
        status: Overall health status
        services: Dictionary of service statuses
        metrics: Health metrics
        **additional_fields: Additional response fields

    Returns:
        Health check response
    """
    response = create_analysis_response(
        status=status,
        data={
            "overall_status": status,
            "services": services,
        }
    )

    if metrics:
        response["data"]["metrics"] = metrics

    response.update(additional_fields)

    return response


def create_error_response(
    error: Union[str, Exception],
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    **additional_fields
) -> Dict[str, Any]:
    """Create a standardized error response.

    Args:
        error: Error message or exception
        error_code: Error code identifier
        details: Additional error details
        **additional_fields: Additional response fields

    Returns:
        Error response dictionary
    """
    error_message = str(error) if isinstance(error, Exception) else error

    response = create_analysis_response(
        status="error",
        message=error_message,
        error=error_message
    )

    if error_code:
        response["error_code"] = error_code

    if details:
        response["details"] = details

    response.update(additional_fields)

    return response


def create_validation_error_response(
    validation_errors: List[str],
    field_errors: Optional[Dict[str, List[str]]] = None,
    **additional_fields
) -> Dict[str, Any]:
    """Create a validation error response.

    Args:
        validation_errors: List of general validation errors
        field_errors: Field-specific validation errors
        **additional_fields: Additional response fields

    Returns:
        Validation error response
    """
    details = {"validation_errors": validation_errors}

    if field_errors:
        details["field_errors"] = field_errors

    return create_error_response(
        error="Validation failed",
        error_code="VALIDATION_ERROR",
        details=details,
        **additional_fields
    )


def create_async_operation_response(
    operation_id: str,
    status: str = "accepted",
    estimated_completion: Optional[int] = None,
    **additional_fields
) -> Dict[str, Any]:
    """Create response for asynchronous operations.

    Args:
        operation_id: Unique operation identifier
        status: Operation status
        estimated_completion: Estimated completion time in seconds
        **additional_fields: Additional response fields

    Returns:
        Async operation response
    """
    response = create_analysis_response(
        status=status,
        data={"operation_id": operation_id}
    )

    if estimated_completion:
        response["data"]["estimated_completion_seconds"] = estimated_completion

    response.update(additional_fields)

    return response
