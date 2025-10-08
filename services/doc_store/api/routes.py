"""API routes for Doc Store service.

Consolidated route definitions for all endpoints.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

# Using standardized response system
from services.shared.presentation.api.responses import (
    create_success_response,
    create_error_response,
    create_paginated_response,
    create_list_response,
    APIResponse,
)

from ..presentation.dto.models import (
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
from ..domain.documents.handlers import AbstractDocumentHandlers
from ..domain.lifecycle.handlers import LifecycleHandlers
from ..domain.notifications.handlers import NotificationsHandlers
from ..domain.relationships.handlers import RelationshipsHandlers
from ..domain.tagging.handlers import TaggingHandlers
from ..domain.versioning.handlers import VersioningHandlers

# Import embedding service
from ..domain.embeddings.service import get_embedding_service

# Import synthesis service
from ..domain.synthesis.service import get_synthesis_service

# Dependency injection container
from ..infrastructure.di.container import container


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
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    document_handlers: AbstractDocumentHandlers = Depends(get_document_handlers)
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
    summary="Search Documents (Hybrid Search)",
    description="""Perform advanced hybrid search across documents combining:
    - Full-text search (FTS5)
    - Semantic similarity search (vector embeddings)
    - Tag-based search
    - Metadata filtering
    
    Results are intelligently merged and ranked by relevance.""",
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
                            "search_mode": "hybrid",
                            "total_results": 25,
                            "results": [
                                {
                                    "document_id": "doc-123",
                                    "score": 0.95,
                                    "semantic_similarity": 0.87,
                                    "keyword_score": 0.92,
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
    use_semantic: bool = Query(True, description="Enable semantic (vector) search"),
    semantic_weight: float = Query(0.5, ge=0.0, le=1.0, description="Weight for semantic vs keyword (0=keyword only, 1=semantic only)"),
    document_handlers: AbstractDocumentHandlers = Depends(get_document_handlers)
):
    """
    Search documents using hybrid approach (keyword + semantic).
    
    The search combines:
    1. Traditional keyword search (tags, metadata, FTS)
    2. Semantic similarity search (if enabled and embeddings available)
    3. Intelligent result merging with configurable weighting
    """
    import time
    from ..db.queries import search_documents as keyword_search
    
    start_time = time.time()
    
    # Get keyword search results
    keyword_results = keyword_search(request.query, limit=request.limit)
    
    # Get semantic search results if enabled
    semantic_results = []
    if use_semantic:
        try:
            embedding_service = get_embedding_service()
            semantic_results = await embedding_service.semantic_search(
                query=request.query,
                limit=request.limit,
                min_similarity=0.3
            )
        except Exception as e:
            # Gracefully degrade to keyword-only search
            logger = __import__('logging').getLogger(__name__)
            logger.warning(f"Semantic search failed, using keyword-only: {e}")
    
    # Merge and rank results
    merged_results = _merge_search_results(
        keyword_results=keyword_results,
        semantic_results=semantic_results,
        semantic_weight=semantic_weight,
        limit=request.limit
    )
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Extract facets
    facets = _extract_facets(merged_results)
    
    search_mode = "hybrid" if use_semantic and semantic_results else "keyword"
    
    return create_success_response(
        data={
            "query": request.query,
            "search_mode": search_mode,
            "total_results": len(merged_results),
            "results": merged_results,
            "facets": facets,
            "took_ms": round(duration_ms, 2)
        },
        message="Search completed successfully"
    )


def _merge_search_results(
    keyword_results: List[Dict[str, Any]],
    semantic_results: List[Dict[str, Any]],
    semantic_weight: float,
    limit: int
) -> List[Dict[str, Any]]:
    """
    Merge keyword and semantic search results with weighted scoring.
    
    Args:
        keyword_results: Results from keyword search
        semantic_results: Results from semantic search
        semantic_weight: Weight for semantic score (0-1)
        limit: Maximum results to return
    
    Returns:
        Merged and ranked results
    """
    keyword_weight = 1.0 - semantic_weight
    
    # Index results by document ID
    results_by_id = {}
    
    # Add keyword results
    for idx, doc in enumerate(keyword_results):
        doc_id = doc.get("id")
        keyword_score = doc.get("relevance_score", 0.0)
        if keyword_score == 0.0:
            # Inverse rank scoring if no explicit score
            keyword_score = 1.0 / (idx + 1)
        
        results_by_id[doc_id] = {
            **doc,
            "keyword_score": keyword_score,
            "semantic_similarity": 0.0
        }
    
    # Add/merge semantic results
    for idx, doc in enumerate(semantic_results):
        doc_id = doc.get("id")
        semantic_score = doc.get("semantic_similarity", 0.0)
        
        if doc_id in results_by_id:
            # Merge scores
            results_by_id[doc_id]["semantic_similarity"] = semantic_score
        else:
            # Add new result
            results_by_id[doc_id] = {
                **doc,
                "keyword_score": 0.0,
                "semantic_similarity": semantic_score
            }
    
    # Calculate combined scores
    for doc in results_by_id.values():
        keyword_score = doc.get("keyword_score", 0.0)
        semantic_score = doc.get("semantic_similarity", 0.0)
        
        # Normalize scores to [0, 1]
        keyword_norm = min(1.0, keyword_score)
        semantic_norm = min(1.0, semantic_score)
        
        # Combined weighted score
        combined_score = (keyword_weight * keyword_norm) + (semantic_weight * semantic_norm)
        doc["score"] = combined_score
    
    # Sort by combined score
    sorted_results = sorted(
        results_by_id.values(),
        key=lambda x: x.get("score", 0.0),
        reverse=True
    )
    
    return sorted_results[:limit]


def _extract_facets(results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract facets (tags) from search results."""
    import json
    
    tag_counts = {}
    
    for doc in results:
        tags_str = doc.get("tags", "[]")
        try:
            tags = json.loads(tags_str) if isinstance(tags_str, str) else tags_str
            if isinstance(tags, list):
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        except:
            pass
    
    # Return top tags
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return {"tags": [tag for tag, _ in sorted_tags[:10]]}



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


# Embedding/Semantic Search endpoints
@router.post(
    "/embeddings/generate",
    tags=["embeddings"],
    summary="Generate Document Embedding",
    description="Generate vector embedding for a single document to enable semantic search.",
    response_description="Successfully generated embedding with metadata",
    responses={
        200: {
            "description": "Embedding generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Embedding generated successfully",
                        "data": {
                            "vector_id": "vec-123",
                            "document_id": "doc-123",
                            "vector_model": "sentence-transformers/all-MiniLM-L6-v2",
                            "embedding_dimension": 384
                        }
                    }
                }
            }
        },
        404: {"description": "Document not found"},
        500: {"description": "Error generating embedding"}
    }
)
async def generate_document_embedding(
    document_id: str = Query(..., description="Document ID to generate embedding for")
):
    """Generate embedding for a specific document."""
    from ..db.queries import get_document_by_id
    
    # Get document
    document = get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Generate embedding
    embedding_service = get_embedding_service()
    result = await embedding_service.embed_document(
        document_id=document_id,
        content=document.get("content", ""),
        metadata={"document_metadata": document.get("metadata")}
    )
    
    return create_success_response(
        data=result,
        message="Embedding generated successfully"
    )


@router.post(
    "/embeddings/generate-batch",
    tags=["embeddings"],
    summary="Generate Embeddings in Batch",
    description="Generate vector embeddings for multiple documents in batch for improved performance.",
    response_description="Batch embedding generation results",
    responses={
        202: {
            "description": "Batch embedding generation completed",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Batch embeddings generated",
                        "data": {
                            "total": 50,
                            "successful": 48,
                            "failed": 2,
                            "results": []
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid batch request"},
        500: {"description": "Error during batch embedding generation"}
    }
)
async def generate_embeddings_batch(
    document_ids: List[str] = Query(None, description="List of document IDs"),
    limit: int = Query(100, ge=1, le=1000, description="Auto-embed documents without vectors")
):
    """Generate embeddings for multiple documents."""
    from ..db.queries import get_document_by_id, get_documents_without_vectors
    
    # Get documents
    if document_ids:
        documents = []
        for doc_id in document_ids:
            doc = get_document_by_id(doc_id)
            if doc:
                documents.append(doc)
    else:
        # Auto-generate for documents without vectors
        documents = get_documents_without_vectors(limit=limit)
    
    if not documents:
        return create_success_response(
            data={"total": 0, "successful": 0, "failed": 0, "results": []},
            message="No documents to process"
        )
    
    # Generate embeddings
    embedding_service = get_embedding_service()
    results = await embedding_service.embed_documents_batch(documents)
    
    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful
    
    return create_success_response(
        data={
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "results": results
        },
        message=f"Batch embeddings generated: {successful} successful, {failed} failed"
    )


@router.post(
    "/search/semantic",
    tags=["search", "embeddings"],
    summary="Semantic Search",
    description="Perform semantic similarity search using vector embeddings to find contextually similar documents.",
    response_description="Semantically similar documents with similarity scores",
    responses={
        200: {
            "description": "Semantic search completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Semantic search completed",
                        "data": {
                            "query": "machine learning algorithms",
                            "total_results": 15,
                            "results": [
                                {
                                    "id": "doc-123",
                                    "content": "Deep learning neural networks...",
                                    "semantic_similarity": 0.87,
                                    "metadata": {}
                                }
                            ]
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid search query"},
        500: {"description": "Error during semantic search"}
    }
)
async def semantic_search(
    query: str = Query(..., description="Search query text"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    min_similarity: float = Query(0.3, ge=0.0, le=1.0, description="Minimum similarity threshold")
):
    """Perform semantic search using vector similarity."""
    embedding_service = get_embedding_service()
    
    results = await embedding_service.semantic_search(
        query=query,
        limit=limit,
        min_similarity=min_similarity
    )
    
    return create_success_response(
        data={
            "query": query,
            "total_results": len(results),
            "results": results
        },
        message="Semantic search completed"
    )


@router.get(
    "/embeddings/model-info",
    tags=["embeddings"],
    summary="Get Embedding Model Info",
    description="Retrieve information about the current embedding model including dimensions and capabilities.",
    response_description="Embedding model metadata",
    responses={
        200: {
            "description": "Model information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Model information retrieved",
                        "data": {
                            "name": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimensions": 384,
                            "max_sequence_length": 256,
                            "model_size_mb": 90.5,
                            "language": "en"
                        }
                    }
                }
            }
        }
    }
)
async def get_embedding_model_info():
    """Get embedding model information."""
    embedding_service = get_embedding_service()
    model_info = embedding_service.get_model_info()
    
    return create_success_response(
        data=model_info,
        message="Model information retrieved"
    )


@router.get(
    "/embeddings/stats",
    tags=["embeddings"],
    summary="Get Embedding Statistics",
    description="Retrieve statistics about vectorized documents and coverage.",
    response_description="Embedding coverage statistics",
    responses={
        200: {
            "description": "Statistics retrieved successfully"
        }
    }
)
async def get_embedding_stats():
    """Get embedding statistics."""
    from ..db.queries import execute_query
    
    # Get total documents
    total_docs = execute_query(
        "SELECT COUNT(*) as count FROM documents",
        fetch_one=True
    )
    
    # Get vectorized documents
    vectorized_docs = execute_query(
        "SELECT COUNT(DISTINCT document_id) as count FROM document_vectors",
        fetch_one=True
    )
    
    # Get vector models
    models = execute_query(
        """
        SELECT vector_model, COUNT(*) as count 
        FROM document_vectors 
        GROUP BY vector_model
        """,
        fetch_all=True
    )
    
    total = total_docs.get("count", 0) if total_docs else 0
    vectorized = vectorized_docs.get("count", 0) if vectorized_docs else 0
    coverage = (vectorized / total * 100) if total > 0 else 0
    
    return create_success_response(
        data={
            "total_documents": total,
            "vectorized_documents": vectorized,
            "coverage_percentage": round(coverage, 2),
            "models": models or []
        },
        message="Embedding statistics retrieved"
    )


# RAG/Synthesis endpoints
@router.post(
    "/synthesis/generate",
    tags=["synthesis", "rag"],
    summary="Generate Answer with RAG",
    description="""Generate an intelligent answer using Retrieval-Augmented Generation (RAG).
    
    This endpoint:
    1. Performs hybrid search (semantic + keyword) to find relevant documents
    2. Retrieves top K most relevant documents as context
    3. Uses LLM to synthesize a comprehensive answer from the context
    4. Returns answer with source citations and confidence
    
    This provides better answers than simple search by:
    - Understanding the question semantically
    - Combining information from multiple documents
    - Generating natural, coherent responses
    - Citing sources for verification""",
    response_description="Synthesized answer with sources and metadata",
    responses={
        200: {
            "description": "Answer generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Answer synthesized successfully",
                        "data": {
                            "answer": "Machine learning algorithms include supervised learning (classification, regression), unsupervised learning (clustering), and reinforcement learning...",
                            "query": "What are machine learning algorithms?",
                            "context_documents_used": 5,
                            "model": "llama3.2:3b",
                            "sources": ["doc-123", "doc-456", "doc-789"],
                            "synthesis_method": "rag",
                            "temperature": 0.3,
                            "search_metadata": {
                                "documents_found": 15,
                                "semantic_weight": 0.7,
                                "search_time_ms": 250
                            }
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid request"},
        500: {"description": "Error during synthesis"}
    }
)
async def synthesize_answer(
    query: str = Query(..., description="User's question"),
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0, description="Weight for semantic vs keyword search"),
    min_similarity: float = Query(0.3, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    temperature: float = Query(0.3, ge=0.0, le=1.0, description="LLM temperature for generation"),
    max_tokens: int = Query(500, ge=50, le=2000, description="Maximum tokens to generate"),
    llm_model: str = Query("llama3.2:3b", description="LLM model to use")
):
    """
    Generate answer using RAG (Retrieval-Augmented Generation).
    
    Combines semantic search with LLM generation for intelligent answers.
    """
    synthesis_service = get_synthesis_service(llm_model=llm_model)
    
    result = await synthesis_service.synthesize_with_search(
        query=query,
        semantic_weight=semantic_weight,
        min_similarity=min_similarity,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return create_success_response(
        data=result,
        message="Answer synthesized successfully"
    )


@router.post(
    "/synthesis/batch",
    tags=["synthesis", "rag"],
    summary="Batch Answer Generation",
    description="Generate answers for multiple questions in batch using RAG.",
    response_description="Batch synthesis results",
    responses={
        202: {
            "description": "Batch synthesis completed",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Batch synthesis completed",
                        "data": {
                            "total": 10,
                            "successful": 9,
                            "failed": 1,
                            "results": []
                        }
                    }
                }
            }
        }
    }
)
async def synthesize_batch(
    queries: List[str] = Query(..., description="List of questions"),
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0),
    temperature: float = Query(0.3, ge=0.0, le=1.0),
    max_tokens: int = Query(500, ge=50, le=2000)
):
    """Generate answers for multiple questions in batch."""
    import asyncio
    
    synthesis_service = get_synthesis_service()
    
    # Process queries concurrently
    tasks = [
        synthesis_service.synthesize_with_search(
            query=q,
            semantic_weight=semantic_weight,
            temperature=temperature,
            max_tokens=max_tokens
        )
        for q in queries
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count successes and failures
    successful = []
    failed = []
    
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            failed.append({
                "query": queries[idx],
                "error": str(result)
            })
        else:
            successful.append(result)
    
    return create_success_response(
        data={
            "total": len(queries),
            "successful": len(successful),
            "failed": len(failed),
            "results": successful,
            "errors": failed
        },
        message=f"Batch synthesis completed: {len(successful)} successful, {len(failed)} failed"
    )
