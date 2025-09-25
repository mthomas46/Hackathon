"""API routes for Doc Store service.

Consolidated route definitions for all endpoints.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

# Using standardized response system
from services.shared.presentation.responses import (
    create_success_response,
    create_error_response,
    create_paginated_response,
    create_list_response,
    APIResponse,
)

from ..core.models import (
    BulkDocumentRequest,
    CacheInvalidationRequest,
    CacheStatsResponse,
    DocumentListResponse,
    DocumentRequest,
    DocumentResponse,
    LifecyclePolicyRequest,
    LifecycleStatusResponse,
    LifecycleTransitionRequest,
    MetadataUpdateRequest,
    QualityResponse,
    SearchRequest,
    SearchResponse,
    SuccessResponse,
    TagRequest,
    TagSearchRequest,
    VersionRollbackRequest,
    WebhookRequest,
)
from ..domain.analytics.handlers import AnalyticsHandlers
from ..domain.bulk.handlers import BulkOperationsHandlers

# Import handlers from domains
from ..domain.documents.handlers import document_handlers
from ..domain.lifecycle.handlers import LifecycleHandlers
from ..domain.notifications.handlers import NotificationsHandlers
from ..domain.relationships.handlers import RelationshipsHandlers
from ..domain.tagging.handlers import TaggingHandlers
from ..domain.versioning.handlers import VersioningHandlers

# Create router
router = APIRouter(prefix="/api/v1", tags=["docstore"])

# Initialize handlers
bulk_handlers = BulkOperationsHandlers()
analytics_handlers = AnalyticsHandlers()
lifecycle_handlers = LifecycleHandlers()
versioning_handlers = VersioningHandlers()
relationships_handlers = RelationshipsHandlers()
tagging_handlers = TaggingHandlers()
notifications_handlers = NotificationsHandlers()


# Document endpoints
@router.post(
    "/documents",
    summary="Create Document",
    description="Create a new document in the document store with content, metadata, and optional custom ID.",
    response_description="Successfully created document with ID, content hash, and metadata",
    responses={
        201: {
            "description": "Document created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Document created successfully",
                        "data": {
                            "id": "doc-123",
                            "content_hash": "abc123...",
                            "created_at": "2024-01-01T00:00:00"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid document data or validation error"},
        413: {"description": "Document content too large"},
        500: {"description": "Internal server error during document creation"}
    }
)
async def create_document(request: DocumentRequest):
    """Create a new document."""
    result = await document_handlers.handle_create_document(request)
    return create_success_response(data=result, message="Document created successfully")


@router.get(
    "/documents/{document_id}",
    summary="Get Document",
    description="Retrieve a document by its unique ID including content, metadata, and version information.",
    response_description="Document data with content, metadata, and timestamps",
    responses={
        200: {
            "description": "Document retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Document retrieved successfully",
                        "data": {
                            "id": "doc-123",
                            "content": "# Document content...",
                            "content_hash": "abc123...",
                            "metadata": {"author": "user", "tags": []},
                            "created_at": "2024-01-01T00:00:00"
                        }
                    }
                }
            }
        },
        404: {"description": "Document not found"},
        500: {"description": "Internal server error during document retrieval"}
    }
)
async def get_document(document_id: str):
    """Get document by ID."""
    result = await document_handlers.handle_get_document(document_id)
    return create_success_response(
        data=result, message="Document retrieved successfully"
    )


@router.get(
    "/documents",
    summary="List Documents",
    description="Retrieve a paginated list of documents with optional filtering and sorting capabilities.",
    response_description="Paginated list of documents with metadata",
    responses={
        200: {
            "description": "Documents retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Documents retrieved successfully",
                        "data": {
                            "items": [
                                {
                                    "id": "doc-123",
                                    "title": "Document 1",
                                    "content_hash": "abc123...",
                                    "created_at": "2024-01-01T00:00:00"
                                }
                            ],
                            "total": 100,
                            "page": 1,
                            "page_size": 50,
                            "total_pages": 2
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid pagination parameters"},
        500: {"description": "Internal server error during document listing"}
    }
)
async def list_documents(
    limit: int = Query(50, ge=1, le=1000, description="Number of documents per page"),
    offset: int = Query(0, ge=0, description="Number of documents to skip")
):
    """List documents with pagination."""
    result = await document_handlers.handle_list_documents(limit, offset)
    return create_paginated_response(
        items=result.get("items", []),
        total=result.get("total", 0),
        page=(offset // limit) + 1,
        page_size=limit,
        message="Documents retrieved successfully",
    )


@router.patch("/documents/{document_id}/metadata")
async def update_document_metadata(document_id: str, request: MetadataUpdateRequest):
    """Update document metadata."""
    return await document_handlers.handle_update_metadata(document_id, request)


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete document by ID."""
    return await document_handlers.handle_delete_document(document_id)


# Search endpoints
@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search documents by content."""
    return await document_handlers.handle_search_documents(request)


# Quality endpoints
@router.get("/documents/quality", response_model=QualityResponse)
async def get_quality_metrics(limit: int = Query(1000, ge=1, le=10000)):
    """Get document quality metrics."""
    return await document_handlers.handle_get_quality_metrics(limit)


# Analytics endpoints
@router.get("/analytics/summary")
async def get_analytics_summary(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    """Get analytics summary."""
    result = await analytics_handlers.handle_get_analytics_summary()
    return create_success_response(data=result, message="Analytics summary retrieved")


# Versioning endpoints
@router.get("/documents/{document_id}/versions")
async def get_document_versions(
    document_id: str, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)
):
    """Get document version history."""
    result = await versioning_handlers.handle_get_document_versions(
        document_id, limit, offset
    )
    return create_paginated_response(
        result["items"],
        result["total"],
        1,
        limit,
        message="Document versions retrieved",
    )


@router.post("/documents/{document_id}/versions/rollback")
async def rollback_document_version(document_id: str, request: VersionRollbackRequest):
    """Rollback document to previous version."""
    result = await versioning_handlers.handle_rollback_to_version(
        document_id, request.version_number, request.reason
    )
    return create_success_response(
        data=result, message="Document rolled back successfully"
    )


# Relationship endpoints
@router.post("/relationships")
async def add_relationship(request: Dict[str, Any]):  # Using dict for now
    """Add relationship between documents."""
    return await relationships_handlers.handle_add_relationship(
        request["source_document_id"],
        request["target_document_id"],
        request["relationship_type"],
        request.get("strength", 1.0),
        request.get("metadata", {}),
    )


@router.get("/documents/{document_id}/relationships", response_model=SuccessResponse)
async def get_document_relationships(
    document_id: str, direction: str = Query("both", regex="^(both|outgoing|incoming)$")
):
    """Get relationships for a document."""
    return await relationships_handlers.handle_get_relationships(document_id, direction)


@router.get("/relationships/paths", response_model=SuccessResponse)
async def find_relationship_paths(
    start_id: str = Query(..., description="Starting document ID"),
    end_id: str = Query(..., description="Ending document ID"),
    max_depth: int = Query(3, ge=1, le=10),
):
    """Find paths between documents."""
    return await relationships_handlers.handle_find_paths(start_id, end_id, max_depth)


@router.get("/relationships/stats", response_model=SuccessResponse)
async def get_relationship_statistics():
    """Get relationship graph statistics."""
    return await relationships_handlers.handle_get_graph_statistics()


# Tagging endpoints
@router.post("/documents/{document_id}/tags", response_model=SuccessResponse)
async def tag_document(document_id: str, request: TagRequest):
    """Automatically tag a document."""
    return await tagging_handlers.handle_tag_document(document_id)


@router.get("/tags/search", response_model=SuccessResponse)
async def search_by_tags(request: TagSearchRequest):
    """Search documents by tags."""
    return await tagging_handlers.handle_search_by_tags(
        request.tags, request.limit, request.offset
    )


# Lifecycle endpoints
@router.post("/lifecycle/policies")
async def create_lifecycle_policy(request: LifecyclePolicyRequest):
    """Create lifecycle policy."""
    return await lifecycle_handlers.handle_create_policy(
        request.name,
        request.description,
        request.conditions,
        request.actions,
        request.priority,
    )


@router.post("/documents/{document_id}/lifecycle/transition")
async def transition_document_phase(
    document_id: str, request: LifecycleTransitionRequest
):
    """Transition document to new lifecycle phase."""
    return await lifecycle_handlers.handle_apply_lifecycle_policies(
        {"id": document_id, "new_phase": request.new_phase, "reason": request.reason}
    )


@router.get(
    "/documents/{document_id}/lifecycle", response_model=LifecycleStatusResponse
)
async def get_document_lifecycle(document_id: str):
    """Get document lifecycle status."""
    return await lifecycle_handlers.handle_get_document_lifecycle(document_id)


# Notification endpoints
@router.post("/webhooks", response_model=SuccessResponse)
async def register_webhook(request: WebhookRequest):
    """Register webhook for notifications."""
    return await notifications_handlers.handle_register_webhook(
        request.name,
        request.url,
        request.events,
        request.secret,
        request.is_active,
        request.retry_count,
        request.timeout_seconds,
    )


@router.get("/webhooks", response_model=SuccessResponse)
async def list_webhooks():
    """List registered webhooks."""
    return await notifications_handlers.handle_list_webhooks()


@router.get("/notifications/stats", response_model=SuccessResponse)
async def get_notification_stats():
    """Get notification statistics."""
    return await notifications_handlers.handle_get_notification_stats()


# Bulk operations endpoints
@router.post("/bulk/documents", response_model=SuccessResponse)
async def create_documents_bulk(request: BulkDocumentRequest):
    """Create multiple documents in bulk."""
    return await bulk_handlers.handle_bulk_create_documents(request.documents)


@router.get("/bulk/operations", response_model=SuccessResponse)
async def list_bulk_operations(
    status: Optional[str] = None, limit: int = Query(50, ge=1, le=100)
):
    """List bulk operations."""
    return await bulk_handlers.handle_list_bulk_operations(status, limit)


@router.get("/bulk/operations/{operation_id}", response_model=SuccessResponse)
async def get_bulk_operation_status(operation_id: str):
    """Get bulk operation status."""
    return await bulk_handlers.handle_get_bulk_operation_status(operation_id)


@router.delete("/bulk/operations/{operation_id}", response_model=SuccessResponse)
async def cancel_bulk_operation(operation_id: str):
    """Cancel bulk operation."""
    return await bulk_handlers.handle_cancel_bulk_operation(operation_id)


# Cache management endpoints
@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Get cache statistics."""
    # TODO: Implement cache handlers
    raise HTTPException(status_code=501, detail="Cache management not yet implemented")


@router.post("/cache/invalidate")
async def invalidate_cache(request: CacheInvalidationRequest):
    """Invalidate cache entries."""
    # TODO: Implement cache handlers
    raise HTTPException(status_code=501, detail="Cache management not yet implemented")


@router.post("/cache/warmup")
async def warmup_cache(operations: List[Dict[str, Any]]):
    """Warm up cache with common operations."""
    # TODO: Implement cache handlers
    raise HTTPException(status_code=501, detail="Cache management not yet implemented")


@router.post("/cache/optimize")
async def optimize_cache():
    """Optimize cache performance."""
    # TODO: Implement cache handlers
    raise HTTPException(status_code=501, detail="Cache management not yet implemented")
