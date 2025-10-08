"""API routes for Doc Store service.

Consolidated route definitions for all endpoints.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

# Using standardized response system
from services.shared.core.responses.responses import (
    create_success_response,
    create_error_response,
    create_paginated_response,
    create_list_response,
)
from services.shared.presentation.api.responses import APIResponse

from ...presentation.dto.models import (
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
from ...application.handlers.analytics_handlers import AnalyticsHandlers
from ...application.handlers.bulk_handlers import BulkOperationsHandlers

# Import handlers from application layer
from ...application.handlers.document_handlers import AbstractDocumentHandlers
from ...application.handlers.lifecycle_handlers import LifecycleHandlers
from ...application.handlers.notifications_handlers import NotificationsHandlers
from ...application.handlers.relationships_handlers import RelationshipsHandlers
from ...application.handlers.tagging_handlers import TaggingHandlers
from ...application.handlers.versioning_handlers import VersioningHandlers

# Dependency injection container
from ...infrastructure.di.container import container


# Dependency functions for injection
def get_document_handlers() -> AbstractDocumentHandlers:
    """Get document handlers from dependency container."""
    return container.document_handlers

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
    tags=["documents"],
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
async def create_document(
    request: DocumentRequest,
    document_handlers: AbstractDocumentHandlers = Depends(get_document_handlers)
):
    """Create a new document."""
    result = await document_handlers.handle_create_document(request)
    return create_success_response(data=result, message="Document created successfully")


@router.get(
    "/documents/{document_id}",
    tags=["documents"],
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
async def get_document(
    document_id: str,
    document_handlers: AbstractDocumentHandlers = Depends(get_document_handlers)
):
    """Get document by ID."""
    print(f"🔍 [ROUTE DEBUG] get_document called with: {document_id}", flush=True)
    result = await document_handlers.handle_get_document(document_id)
    print(f"🔍 [ROUTE DEBUG] handle_get_document returned: {type(result)}, hasattr id: {hasattr(result, 'id')}, hasattr tags: {hasattr(result, 'tags')}", flush=True)
    if result:
        print(f"🔍 [ROUTE DEBUG] result.id = {getattr(result, 'id', 'NO ATTR')}, result.tags = {getattr(result, 'tags', 'NO ATTR')}", flush=True)
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
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    document_handlers: AbstractDocumentHandlers = Depends(get_document_handlers)
):
    """List documents with pagination."""
    result = await document_handlers.handle_list_documents(limit, offset)
    # result is already a DocumentListResponse, return it directly
    return create_success_response(
        data={
            "items": result.items,
            "total": result.total,
            "has_more": result.has_more,
            "page": (offset // limit) + 1,
            "page_size": limit
        },
        message="Documents retrieved successfully"
    )


@router.patch(
    "/documents/{document_id}/metadata",
    tags=["documents"],
    summary="Update Document Metadata",
    description="Update specific metadata fields for an existing document without modifying the content.",
    response_description="Successfully updated document metadata",
    responses={
        200: {
            "description": "Metadata updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Document metadata updated successfully",
                        "data": {
                            "id": "doc-123",
                            "updated_fields": ["tags", "author"],
                            "updated_at": "2024-01-01T12:00:00"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid metadata or validation error"},
        404: {"description": "Document not found"},
        500: {"description": "Internal server error during metadata update"}
    }
)
async def update_document_metadata(
    document_id: str,
    request: MetadataUpdateRequest,
    document_handlers: AbstractDocumentHandlers = Depends(get_document_handlers)
):
    """Update document metadata."""
    return await document_handlers.handle_update_metadata(document_id, request)


@router.delete(
    "/documents/{document_id}",
    tags=["documents"],
    summary="Delete Document",
    description="Permanently delete a document and all its versions from the document store.",
    response_description="Successfully deleted document",
    responses={
        200: {
            "description": "Document deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Document deleted successfully",
                        "data": {
                            "id": "doc-123",
                            "deleted_at": "2024-01-01T12:00:00",
                            "versions_removed": 3
                        }
                    }
                }
            }
        },
        404: {"description": "Document not found"},
        409: {"description": "Document cannot be deleted due to existing relationships"},
        500: {"description": "Internal server error during document deletion"}
    }
)
async def delete_document(
    document_id: str,
    document_handlers: AbstractDocumentHandlers = Depends(get_document_handlers)
):
    """Delete document by ID."""
    return await document_handlers.handle_delete_document(document_id)


# Search endpoints
@router.post(
    "/search",
    tags=["search"],
    summary="Search Documents",
    description="Perform advanced search across documents using full-text search, filters, and semantic similarity.",
    response_description="Search results with relevance scoring and metadata",
    response_model=SearchResponse,
    responses={
        200: {
            "description": "Search completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Search completed successfully",
                        "data": {
                            "query": "machine learning",
                            "total_results": 25,
                            "results": [
                                {
                                    "document_id": "doc-123",
                                    "score": 0.95,
                                    "title": "ML Algorithms Guide",
                                    "snippet": "...machine learning algorithms...",
                                    "metadata": {"tags": ["ml", "algorithms"]}
                                }
                            ],
                            "facets": {"tags": ["ml", "ai", "data"]},
                            "took_ms": 150
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid search query or parameters"},
        500: {"description": "Internal server error during search"}
    }
)
async def search_documents(
    request: SearchRequest,
    document_handlers: AbstractDocumentHandlers = Depends(get_document_handlers)
):
    """Search documents by content."""
    return await document_handlers.handle_search_documents(request)


# Quality endpoints
@router.get(
    "/documents/quality",
    tags=["analytics"],
    summary="Get Document Quality Metrics",
    description="Retrieve quality metrics and analysis for documents in the store, including readability, completeness, and technical accuracy scores.",
    response_description="Document quality metrics and analysis results",
    response_model=QualityResponse,
    responses={
        200: {
            "description": "Quality metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Quality metrics retrieved successfully",
                        "data": {
                            "total_documents": 150,
                            "average_quality_score": 0.78,
                            "quality_distribution": {
                                "excellent": 45,
                                "good": 60,
                                "fair": 30,
                                "poor": 15
                            },
                            "top_issues": ["missing_metadata", "inconsistent_formatting"],
                            "recommendations": ["Add document templates", "Implement quality gates"]
                        }
                    }
                }
            }
        },
        500: {"description": "Internal server error during quality analysis"}
    }
)
async def get_quality_metrics(
    limit: int = Query(1000, ge=1, le=10000),
    document_handlers: AbstractDocumentHandlers = Depends(get_document_handlers)
):
    """Get document quality metrics."""
    return await document_handlers.handle_get_quality_metrics(limit)


# Analytics endpoints
@router.get(
    "/analytics/summary",
    tags=["analytics"],
    summary="Get Analytics Summary",
    description="Retrieve comprehensive analytics summary including document counts, usage patterns, quality trends, and system performance metrics.",
    response_description="Complete analytics summary with trends and insights",
    responses={
        200: {
            "description": "Analytics summary retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Analytics summary retrieved successfully",
                        "data": {
                            "document_stats": {
                                "total_documents": 1250,
                                "active_documents": 1180,
                                "archived_documents": 70
                            },
                            "usage_patterns": {
                                "daily_creates": 25,
                                "weekly_searches": 450,
                                "top_tags": ["api", "tutorial", "reference"]
                            },
                            "quality_trends": {
                                "average_score": 0.82,
                                "improvement_rate": 0.05,
                                "quality_distribution": {"excellent": 40, "good": 35, "fair": 20, "poor": 5}
                            },
                            "system_performance": {
                                "average_response_time": 150,
                                "uptime_percentage": 99.9,
                                "error_rate": 0.01
                            }
                        }
                    }
                }
            }
        },
        500: {"description": "Internal server error during analytics retrieval"}
    }
)
async def get_analytics_summary(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    """Get analytics summary."""
    result = await analytics_handlers.handle_get_analytics_summary()
    return create_success_response(data=result, message="Analytics summary retrieved")


# Versioning endpoints
@router.get(
    "/documents/{document_id}/versions",
    tags=["versioning"],
    summary="Get Document Versions",
    description="Retrieve the complete version history for a document, including changes, authors, and timestamps.",
    response_description="Paginated list of document versions with change details",
    responses={
        200: {
            "description": "Document versions retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Document versions retrieved",
                        "data": {
                            "items": [
                                {
                                    "version_number": 3,
                                    "created_at": "2024-01-01T12:00:00",
                                    "author": "user@example.com",
                                    "change_type": "content_update",
                                    "change_summary": "Updated API documentation",
                                    "content_hash": "def456..."
                                }
                            ],
                            "total": 3,
                            "page": 1,
                            "page_size": 50,
                            "total_pages": 1
                        }
                    }
                }
            }
        },
        404: {"description": "Document not found"},
        500: {"description": "Internal server error during version retrieval"}
    }
)
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


@router.post(
    "/documents/{document_id}/versions/rollback",
    tags=["versioning"],
    summary="Rollback Document Version",
    description="Rollback a document to a previous version, creating a new version with the rolled-back content.",
    response_description="Successfully rolled back document with new version details",
    responses={
        200: {
            "description": "Document rolled back successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Document rolled back successfully",
                        "data": {
                            "document_id": "doc-123",
                            "rolled_back_to_version": 2,
                            "new_version_number": 4,
                            "rollback_reason": "Incorrect API documentation",
                            "rolled_back_at": "2024-01-01T12:00:00"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid rollback request or version not found"},
        404: {"description": "Document not found"},
        500: {"description": "Internal server error during rollback"}
    }
)
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
@router.post(
    "/documents/{document_id}/tags",
    tags=["tagging"],
    summary="Tag Document",
    description="Add tags to a document for better organization and searchability.",
    response_description="Successfully tagged document with applied tags",
    response_model=SuccessResponse,
    responses={
        200: {
            "description": "Document tagged successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Document tagged successfully",
                        "data": {
                            "document_id": "doc-123",
                            "applied_tags": ["api", "reference", "v2"],
                            "tagged_at": "2024-01-01T12:00:00"
                        }
                    }
                }
            }
        },
        404: {"description": "Document not found"},
        500: {"description": "Internal server error during tagging"}
    }
)
async def tag_document(document_id: str, request: TagRequest):
    """Automatically tag a document."""
    return await tagging_handlers.handle_tag_document(document_id)


@router.get(
    "/tags/search",
    tags=["tagging"],
    summary="Search by Tags",
    description="Find documents that match specific tag combinations using advanced tag-based search.",
    response_description="Documents matching the tag search criteria",
    response_model=SuccessResponse,
    responses={
        200: {
            "description": "Tag search completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Tag search completed successfully",
                        "data": {
                            "query": {"tags": ["api", "v2"], "operator": "AND"},
                            "total_results": 15,
                            "results": [
                                {
                                    "document_id": "doc-123",
                                    "title": "API Reference v2",
                                    "tags": ["api", "reference", "v2"],
                                    "score": 1.0
                                }
                            ]
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid tag search parameters"},
        500: {"description": "Internal server error during tag search"}
    }
)
async def search_by_tags(request: TagSearchRequest):
    """Search documents by tags."""
    return await tagging_handlers.handle_search_by_tags(
        request.tags, request.limit, request.offset
    )


# Lifecycle endpoints
@router.post(
    "/lifecycle/policies",
    tags=["lifecycle"],
    summary="Create Lifecycle Policy",
    description="Create a new lifecycle policy to automate document transitions and cleanup.",
    response_description="Successfully created lifecycle policy",
    responses={
        201: {
            "description": "Lifecycle policy created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Lifecycle policy created successfully",
                        "data": {
                            "policy_id": "policy-123",
                            "name": "Standard Document Lifecycle",
                            "rules": [
                                {"phase": "active", "retention_days": 365},
                                {"phase": "archive", "retention_days": 1825}
                            ]
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid policy configuration"},
        500: {"description": "Internal server error during policy creation"}
    }
)
async def create_lifecycle_policy(request: LifecyclePolicyRequest):
    """Create lifecycle policy."""
    return await lifecycle_handlers.handle_create_policy(
        request.name,
        request.description,
        request.conditions,
        request.actions,
        request.priority,
    )


@router.post(
    "/documents/{document_id}/lifecycle/transition",
    tags=["lifecycle"],
    summary="Transition Document Phase",
    description="Manually transition a document to a different lifecycle phase (active, archive, delete).",
    response_description="Successfully transitioned document to new phase",
    responses={
        200: {
            "description": "Document transitioned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Document transitioned successfully",
                        "data": {
                            "document_id": "doc-123",
                            "from_phase": "active",
                            "to_phase": "archive",
                            "transitioned_at": "2024-01-01T12:00:00",
                            "reason": "Manual archive request"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid transition or phase not allowed"},
        404: {"description": "Document not found"},
        500: {"description": "Internal server error during transition"}
    }
)
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
@router.post(
    "/bulk/documents",
    tags=["bulk"],
    summary="Bulk Create Documents",
    description="Create multiple documents in a single batch operation for improved performance.",
    response_description="Bulk operation initiated with operation ID and status",
    response_model=SuccessResponse,
    responses={
        202: {
            "description": "Bulk operation accepted and queued",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Bulk document creation initiated",
                        "data": {
                            "operation_id": "bulk-123",
                            "status": "queued",
                            "total_documents": 50,
                            "estimated_completion": "2024-01-01T12:05:00"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid bulk request or document data"},
        429: {"description": "Too many concurrent bulk operations"},
        500: {"description": "Internal server error during bulk operation initiation"}
    }
)
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


# =============================================================================
# DEBUG ROUTES - Tags Testing (Added for systematic debugging)
# =============================================================================

@router.post("/debug/documents/direct-sql", tags=["debug"])
async def create_document_direct_sql(body: dict):
    """Create document with DIRECT SQL - bypasses ALL layers."""
    import sqlite3
    import json
    from datetime import datetime
    
    try:
        db_path = "/app/services/doc_store/data/doc_store.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tags = body.get('tags', [])
        tags_json = json.dumps(tags)
        
        cursor.execute(
            """
            INSERT INTO documents (id, content, content_hash, metadata, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                body['id'],
                body['content'],
                "direct-sql-hash",
                "{}",
                tags_json,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            )
        )
        conn.commit()
        
        cursor.execute("SELECT id, tags FROM documents WHERE id = ?", (body['id'],))
        result = cursor.fetchone()
        conn.close()
        
        return {
            "success": True,
            "method": "direct-sql",
            "tags_sent": tags,
            "tags_json": tags_json,
            "tags_stored": result[1] if result else None,
            "message": "✅ Direct SQL insert successful"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/debug/documents/via-service", tags=["debug"])
async def create_document_via_service_debug(body: dict):
    """Create document using Service layer."""
    try:
        from services.doc_store.domain.documents.service import DocumentService
        
        tags = body.get('tags', [])
        
        service = DocumentService()
        doc = await service.create({
            "id": body['id'],
            "content": body['content'],
            "metadata": {},
            "tags": tags,
            "correlation_id": None
        })
        
        return {
            "success": True,
            "method": "via-service",
            "tags_sent": tags,
            "tags_in_doc": doc.tags,
            "message": "✅ Insert via service successful"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/debug/documents/{doc_id}/tags-debug", tags=["debug"])
async def get_document_tags_debug(doc_id: str):
    """Get document with detailed tags debugging info."""
    import sqlite3
    import json
    
    try:
        db_path = "/app/services/doc_store/data/doc_store.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, content, tags, metadata FROM documents WHERE id = ?",
            (doc_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {"success": False, "message": "Document not found"}
        
        tags_raw = result[2]
        
        return {
            "success": True,
            "id": result[0],
            "tags_raw": tags_raw,
            "tags_type": str(type(tags_raw)),
            "tags_length": len(tags_raw) if tags_raw else 0,
            "tags_parsed": json.loads(tags_raw) if tags_raw else None,
            "is_empty_array": tags_raw == "[]"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# VECTORIZATION & RAG ENDPOINTS
# ============================================================================

# Import embedding and synthesis services
from ...domain.embeddings.service import get_embedding_service
from ...domain.synthesis.service import get_synthesis_service

@router.get(
    "/embeddings/stats",
    tags=["embeddings", "vectorization"],
    summary="Get Embedding Statistics"
)
async def get_embedding_stats():
    """Get statistics about document vectorization coverage."""
    import logging
    logger = logging.getLogger("doc_store.embeddings")
    
    try:
        from ...db.queries import get_document_count, get_documents_without_vectors
        
        logger.info("📊 Fetching embedding statistics...")
        total_docs = get_document_count()  # Not async
        docs_without_vectors = get_documents_without_vectors(limit=99999)  # Not async
        vectorized = total_docs - len(docs_without_vectors)
        coverage = (vectorized / total_docs * 100) if total_docs > 0 else 0
        
        logger.info(f"✅ Stats: {total_docs} total, {vectorized} vectorized ({coverage:.1f}%)")
        
        return create_success_response(
            data={
                "total_documents": total_docs,
                "vectorized_documents": vectorized,
                "coverage_percentage": round(coverage, 2)
            },
            message="Embedding statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"❌ Error getting embedding stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.post(
    "/embeddings/generate",
    tags=["embeddings", "vectorization"],
    summary="Generate Document Embedding"
)
async def generate_document_embedding(document_id: str = Query(...)):
    """Generate vector embedding for a specific document."""
    import logging
    logger = logging.getLogger("doc_store.embeddings")
    
    try:
        logger.info(f"🔄 Generating embedding for document: {document_id}")
        embedding_service = get_embedding_service()
        result = await embedding_service.embed_document(document_id)
        logger.info(f"✅ Embedding generated successfully for {document_id}")
        
        return create_success_response(
            data=result,
            message=f"Embedding generated for document {document_id}"
        )
    except Exception as e:
        logger.error(f"❌ Failed to generate embedding for {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

@router.post(
    "/embeddings/generate-batch",
    tags=["embeddings", "vectorization"],
    summary="Generate Embeddings in Batch"
)
async def generate_embeddings_batch(limit: int = Query(100, ge=1, le=1000)):
    """Generate embeddings for documents without vectors."""
    import logging
    import sys
    logger = logging.getLogger("doc_store.embeddings")
    
    # Enhanced logging for systematic debugging
    logger.info("=" * 70)
    logger.info("🔬 EMBEDDING BATCH GENERATION - DETAILED LOGGING")
    logger.info("=" * 70)
    logger.info(f"📥 Request: limit={limit}")
    
    try:
        # Step 1: Check documents
        logger.info(f"\n📊 Step 1: Checking documents without vectors...")
        from ...db.queries import get_documents_without_vectors
        
        logger.info(f"   🔍 Querying database...")
        documents = get_documents_without_vectors(limit=limit)
        logger.info(f"   ✅ Query complete: Found {len(documents)} documents")
        
        if not documents:
            logger.info("   ℹ️  All documents already have embeddings")
            return create_success_response(
                data={"successful": 0, "failed": 0, "already_vectorized": True},
                message="All documents already have embeddings"
            )
        
        logger.info(f"   📄 Sample document IDs: {[d.get('id', 'unknown')[:20] for d in documents[:3]]}")
        
        # Step 2: Initialize embedding service
        logger.info(f"\n🤖 Step 2: Initializing embedding service...")
        logger.info(f"   🔍 Checking for sentence-transformers...")
        
        try:
            import sentence_transformers
            logger.info(f"   ✅ sentence-transformers found: {sentence_transformers.__version__}")
        except ImportError as ie:
            logger.error(f"   ❌ sentence-transformers NOT FOUND")
            logger.error(f"   📦 This package is required for embeddings")
            logger.error(f"   💡 Install: pip install sentence-transformers")
            logger.error(f"   💡 Or add to Dockerfile: RUN pip install sentence-transformers")
            raise Exception("Embedding generation requires sentence-transformers. Install with: pip install sentence-transformers") from ie
        
        logger.info(f"   🔧 Getting embedding service instance...")
        embedding_service = get_embedding_service()
        logger.info(f"   ✅ Embedding service initialized: {type(embedding_service).__name__}")
        
        # Step 3: Generate embeddings
        logger.info(f"\n⚙️  Step 3: Generating embeddings...")
        logger.info(f"   📊 Batch size: 32")
        logger.info(f"   📄 Documents to process: {len(documents)}")
        logger.info(f"   🚀 Starting batch generation...")
        
        result = await embedding_service.embed_documents_batch(documents=documents, batch_size=32)
        
        logger.info(f"   ✅ Generation complete!")
        logger.info(f"   📊 Results: {len(result)} embeddings generated")
        
        # Step 4: Success
        logger.info(f"\n✅ BATCH EMBEDDING COMPLETE")
        logger.info(f"   • Documents processed: {len(documents)}")
        logger.info(f"   • Embeddings generated: {len(result)}")
        logger.info(f"   • Success rate: 100%")
        logger.info("=" * 70)
        
        return create_success_response(
            data={"successful": len(result), "failed": 0, "documents_processed": len(documents)},
            message=f"Batch embedding completed: {len(result)} successful"
        )
        
    except Exception as e:
        # Enhanced error logging
        logger.error("=" * 70)
        logger.error("❌ BATCH EMBEDDING FAILED")
        logger.error("=" * 70)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Python version: {sys.version}")
        
        # Check if it's the expected import error
        if "sentence-transformers" in str(e):
            logger.error("\n🔍 ROOT CAUSE: Missing dependency")
            logger.error("   Package: sentence-transformers")
            logger.error("   Status: NOT INSTALLED")
            logger.error("\n💡 SOLUTION:")
            logger.error("   1. Temporary: docker exec doc_store pip install sentence-transformers")
            logger.error("   2. Permanent: Add to Dockerfile + rebuild")
        
        logger.error("=" * 70)
        
        raise HTTPException(status_code=500, detail=f"Batch embedding failed: {str(e)}")

@router.post(
    "/search/semantic",
    tags=["search", "vectorization"],
    summary="Semantic Similarity Search"
)
async def semantic_search(
    query: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
    min_similarity: float = Query(0.3, ge=0.0, le=1.0)
):
    """Search documents by semantic similarity."""
    import logging
    logger = logging.getLogger("doc_store.semantic_search")
    
    try:
        logger.info(f"🔍 Semantic search: '{query[:50]}...' (limit={limit}, min_sim={min_similarity})")
        embedding_service = get_embedding_service()
        results = await embedding_service.semantic_search(
            query=query,
            limit=limit,
            min_similarity=min_similarity
        )
        logger.info(f"✅ Found {len(results)} semantically similar documents")
        
        return create_success_response(
            data={
                "query": query,
                "results": results,
                "count": len(results)
            },
            message=f"Found {len(results)} semantically similar documents"
        )
    except Exception as e:
        logger.error(f"❌ Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")

@router.post(
    "/synthesis/generate",
    tags=["synthesis", "rag"],
    summary="Generate Answer with RAG"
)
async def synthesize_answer(
    query: str = Query(...),
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0),
    temperature: float = Query(0.3, ge=0.0, le=1.0),
    max_tokens: int = Query(500, ge=50, le=2000),
    llm_model: str = Query("llama3.2:3b")
):
    """Generate intelligent answer using RAG (Retrieval-Augmented Generation)."""
    import logging
    logger = logging.getLogger("doc_store.rag")
    
    try:
        logger.info(f"🤖 RAG synthesis: '{query[:50]}...' (model={llm_model}, temp={temperature})")
        synthesis_service = get_synthesis_service(llm_model=llm_model)
        
        result = await synthesis_service.synthesize_with_search(
            query=query,
            semantic_weight=semantic_weight,
            min_similarity=0.3,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        docs_used = result.get("context_documents_used", 0)
        method = result.get("synthesis_method", "unknown")
        logger.info(f"✅ RAG complete: {docs_used} docs, method={method}")
        
        return create_success_response(
            data=result,
            message="Answer synthesized successfully"
        )
    except Exception as e:
        logger.error(f"❌ RAG synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG synthesis failed: {str(e)}")

