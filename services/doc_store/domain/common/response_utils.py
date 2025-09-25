"""Common response utilities for Doc Store API endpoints.

Reduces code duplication by providing standardized response patterns
for all API endpoints.
"""

from typing import Any, Dict, List, Optional

from services.shared.core.responses.responses import (
    create_success_response,
    create_error_response,
    create_paginated_response,
    create_list_response,
)
from services.shared.presentation.api.responses import APIResponse


def document_created_response(document: Any, message: Optional[str] = None) -> APIResponse:
    """Standard response for document creation.

    Args:
        document: Created document entity
        message: Optional custom message

    Returns:
        Standardized API response
    """
    return create_success_response(
        data=document.to_dict() if hasattr(document, 'to_dict') else document,
        message=message or "Document created successfully"
    )


def document_retrieved_response(document: Any, message: Optional[str] = None) -> APIResponse:
    """Standard response for document retrieval.

    Args:
        document: Retrieved document entity
        message: Optional custom message

    Returns:
        Standardized API response
    """
    return create_success_response(
        data=document.to_dict() if hasattr(document, 'to_dict') else document,
        message=message or "Document retrieved successfully"
    )


def document_updated_response(document: Any, message: Optional[str] = None) -> APIResponse:
    """Standard response for document updates.

    Args:
        document: Updated document entity
        message: Optional custom message

    Returns:
        Standardized API response
    """
    return create_success_response(
        data=document.to_dict() if hasattr(document, 'to_dict') else document,
        message=message or "Document updated successfully"
    )


def document_deleted_response(deleted: bool = True, message: Optional[str] = None) -> APIResponse:
    """Standard response for document deletion.

    Args:
        deleted: Whether deletion was successful
        message: Optional custom message

    Returns:
        Standardized API response
    """
    return create_success_response(
        data={"deleted": deleted},
        message=message or "Document deleted successfully"
    )


def documents_list_response(documents: List[Any], message: Optional[str] = None) -> APIResponse:
    """Standard response for document lists.

    Args:
        documents: List of document entities
        message: Optional custom message

    Returns:
        Standardized API response
    """
    data = [
        doc.to_dict() if hasattr(doc, 'to_dict') else doc
        for doc in documents
    ]

    return create_list_response(
        data=data,
        message=message or f"Retrieved {len(documents)} documents"
    )


def documents_paginated_response(
    documents: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: Optional[str] = None
) -> APIResponse:
    """Standard response for paginated document lists.

    Args:
        documents: List of document entities for current page
        total: Total number of documents
        page: Current page number
        page_size: Number of items per page
        message: Optional custom message

    Returns:
        Standardized API response
    """
    data = [
        doc.to_dict() if hasattr(doc, 'to_dict') else doc
        for doc in documents
    ]

    return create_paginated_response(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        message=message or f"Retrieved {len(documents)} documents (page {page})"
    )


def search_results_response(
    results: List[Any],
    query: str,
    total: Optional[int] = None,
    message: Optional[str] = None
) -> APIResponse:
    """Standard response for search results.

    Args:
        results: Search result entities
        query: Search query used
        total: Optional total number of results
        message: Optional custom message

    Returns:
        Standardized API response
    """
    data = [
        result.to_dict() if hasattr(result, 'to_dict') else result
        for result in results
    ]

    response_data = {
        "results": data,
        "query": query,
        "count": len(data)
    }

    if total is not None:
        response_data["total"] = total

    return create_success_response(
        data=response_data,
        message=message or f"Found {len(data)} results for query: {query}"
    )


def analytics_response(
    analytics_data: Dict[str, Any],
    time_range: Optional[str] = None,
    message: Optional[str] = None
) -> APIResponse:
    """Standard response for analytics data.

    Args:
        analytics_data: Analytics data dictionary
        time_range: Optional time range description
        message: Optional custom message

    Returns:
        Standardized API response
    """
    data = {"analytics": analytics_data}
    if time_range:
        data["time_range"] = time_range

    return create_success_response(
        data=data,
        message=message or "Analytics data retrieved successfully"
    )


def bulk_operation_response(
    operation_id: str,
    status: str,
    processed: int,
    total: int,
    message: Optional[str] = None
) -> APIResponse:
    """Standard response for bulk operations.

    Args:
        operation_id: Unique operation identifier
        status: Operation status
        processed: Number of items processed
        total: Total number of items
        message: Optional custom message

    Returns:
        Standardized API response
    """
    return create_success_response(
        data={
            "operation_id": operation_id,
            "status": status,
            "processed": processed,
            "total": total,
            "progress": processed / total if total > 0 else 0
        },
        message=message or f"Bulk operation {status}: {processed}/{total} processed"
    )


def lifecycle_transition_response(
    document_id: str,
    from_status: str,
    to_status: str,
    transition_id: Optional[str] = None,
    message: Optional[str] = None
) -> APIResponse:
    """Standard response for lifecycle transitions.

    Args:
        document_id: Document that was transitioned
        from_status: Previous lifecycle status
        to_status: New lifecycle status
        transition_id: Optional transition identifier
        message: Optional custom message

    Returns:
        Standardized API response
    """
    data = {
        "document_id": document_id,
        "from_status": from_status,
        "to_status": to_status
    }

    if transition_id:
        data["transition_id"] = transition_id

    return create_success_response(
        data=data,
        message=message or f"Document transitioned from {from_status} to {to_status}"
    )


def notification_sent_response(
    notification_id: str,
    recipient_count: int,
    message: Optional[str] = None
) -> APIResponse:
    """Standard response for notification sending.

    Args:
        notification_id: Unique notification identifier
        recipient_count: Number of recipients notified
        message: Optional custom message

    Returns:
        Standardized API response
    """
    return create_success_response(
        data={
            "notification_id": notification_id,
            "recipients_notified": recipient_count
        },
        message=message or f"Notification sent to {recipient_count} recipients"
    )


def cache_operation_response(
    operation: str,
    affected_keys: List[str],
    message: Optional[str] = None
) -> APIResponse:
    """Standard response for cache operations.

    Args:
        operation: Cache operation performed (invalidate, clear, etc.)
        affected_keys: List of affected cache keys
        message: Optional custom message

    Returns:
        Standardized API response
    """
    return create_success_response(
        data={
            "operation": operation,
            "affected_keys": affected_keys,
            "keys_affected": len(affected_keys)
        },
        message=message or f"Cache {operation} completed for {len(affected_keys)} keys"
    )


def service_health_response(
    service_name: str,
    status: str,
    components: Optional[Dict[str, str]] = None,
    message: Optional[str] = None
) -> APIResponse:
    """Standard response for service health checks.

    Args:
        service_name: Name of the service
        status: Health status (healthy, degraded, unhealthy)
        components: Optional component health statuses
        message: Optional custom message

    Returns:
        Standardized API response
    """
    data = {
        "service": service_name,
        "status": status
    }

    if components:
        data["components"] = components

    return create_success_response(
        data=data,
        message=message or f"Service {service_name} is {status}"
    )
