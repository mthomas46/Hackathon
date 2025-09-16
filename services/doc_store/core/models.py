"""Core request and response models for Doc Store service.

Consolidated and simplified from the original 595-line file.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


# Document Models
class DocumentRequest(BaseModel):
    """Base document request model."""
    id: Optional[str] = None
    content: str
    content_hash: Optional[str] = None
    metadata: Optional[Any] = None
    correlation_id: Optional[str] = None


class DocumentResponse(BaseModel):
    """Base document response model."""
    id: str
    content: str
    content_hash: str
    metadata: Dict[str, Any]
    created_at: str


class DocumentListResponse(BaseModel):
    """Response for document listing."""
    items: List[Dict[str, Any]]
    total: int
    has_more: bool


class MetadataUpdateRequest(BaseModel):
    """Request for updating document metadata."""
    metadata: Dict[str, Any]


# Analysis Models
class AnalysisRequest(BaseModel):
    """Request for storing analysis results."""
    document_id: Optional[str] = None
    content: Optional[str] = None
    analyzer: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    result: Dict[str, Any]
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    """Response for analysis operations."""
    id: str
    document_id: str
    analyzer: str
    model: str
    result: Dict[str, Any]
    score: Optional[float] = None
    created_at: str


class AnalysisListResponse(BaseModel):
    """Response for analysis listing."""
    items: List[Dict[str, Any]]
    total: int


# Search Models
class SearchRequest(BaseModel):
    """Request for document search."""
    query: str
    limit: Optional[int] = 50
    filters: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Response for search operations."""
    items: List[Dict[str, Any]]
    total: int
    query: str


# Quality Models
class QualityResponse(BaseModel):
    """Response for quality analysis."""
    items: List[Dict[str, Any]]
    total: int
    stale_count: int
    redundant_count: int


# Style Examples Models
class StyleExamplesResponse(BaseModel):
    """Response for style examples."""
    items: List[Dict[str, Any]]
    languages: List[str]


# Analytics Models
class AnalyticsRequest(BaseModel):
    """Request for analytics operations."""
    document_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    group_by: Optional[str] = None


class AnalyticsResponse(BaseModel):
    """Response for analytics operations."""
    summary: Dict[str, Any]
    trends: List[Dict[str, Any]]
    insights: List[str]


class AnalyticsSummaryResponse(BaseModel):
    """Summary analytics response."""
    total_documents: int
    total_analyses: int
    average_quality_score: float
    top_analyzers: List[Dict[str, Any]]


# Versioning Models
class DocumentVersionResponse(BaseModel):
    """Response for document versions."""
    versions: List[Dict[str, Any]]
    current_version: int
    total_versions: int


class VersionComparison(BaseModel):
    """Version comparison response."""
    version1: Dict[str, Any]
    version2: Dict[str, Any]
    differences: List[Dict[str, Any]]


class VersionRollbackRequest(BaseModel):
    """Request for version rollback."""
    version_number: int
    reason: Optional[str] = None


# Relationship Models
class RelationshipRequest(BaseModel):
    """Request for relationship operations."""
    source_id: str
    target_id: str
    relationship_type: str
    strength: Optional[float] = 1.0
    metadata: Optional[Dict[str, Any]] = None


class RelationshipsResponse(BaseModel):
    """Response for relationship queries."""
    document_id: str
    relationships: List[Dict[str, Any]]
    total_count: int
    direction: str


class PathsResponse(BaseModel):
    """Response for path finding."""
    start_id: str
    end_id: str
    paths: List[List[Dict[str, Any]]]
    found: bool


class GraphStatisticsResponse(BaseModel):
    """Response for graph statistics."""
    total_nodes: int
    total_relationships: int
    relationship_types: Dict[str, int]
    average_degree: float
    connected_components: int


# Tagging Models
class TagRequest(BaseModel):
    """Request for tagging operations."""
    document_id: str
    content: Optional[str] = None


class TagResponse(BaseModel):
    """Response for tagging operations."""
    document_id: str
    entities: List[Dict[str, Any]]
    tags: List[Dict[str, Any]]
    confidence: float


class TagSearchRequest(BaseModel):
    """Request for tag-based search."""
    tags: List[str]
    operator: Optional[str] = "AND"  # AND, OR
    limit: Optional[int] = 50


class TagSearchResponse(BaseModel):
    """Response for tag search."""
    items: List[Dict[str, Any]]
    total: int
    tags_matched: List[str]


class TaxonomyResponse(BaseModel):
    """Response for tag taxonomy."""
    tags: List[Dict[str, Any]]
    hierarchy: Dict[str, List[str]]


# Lifecycle Models
class LifecyclePolicyRequest(BaseModel):
    """Request for lifecycle policy operations."""
    name: str
    description: Optional[str] = None
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: Optional[int] = 0


class LifecycleTransitionRequest(BaseModel):
    """Request for lifecycle transitions."""
    new_phase: str
    reason: Optional[str] = None


class LifecycleStatusResponse(BaseModel):
    """Response for lifecycle status."""
    document_id: str
    current_phase: str
    retention_period_days: Optional[int] = None
    archival_date: Optional[str] = None
    deletion_date: Optional[str] = None
    applied_policies: List[str]


# Notification Models
class WebhookRequest(BaseModel):
    """Request for webhook operations."""
    name: str
    url: str
    events: List[str]
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    retry_count: Optional[int] = None
    timeout_seconds: Optional[int] = None


class WebhooksListResponse(BaseModel):
    """Response for webhooks listing."""
    webhooks: List[Dict[str, Any]]
    total: int


class NotificationStatsResponse(BaseModel):
    """Response for notification statistics."""
    total_events: int
    delivered_webhooks: int
    failed_deliveries: int
    active_webhooks: int


# Bulk Operations Models
class BulkDocumentRequest(BaseModel):
    """Request for bulk document operations."""
    documents: List[DocumentRequest]


class BulkOperationStatus(BaseModel):
    """Response for bulk operation status."""
    operation_id: str
    operation_type: str
    status: str
    progress: Dict[str, Any]
    created_at: str
    completed_at: Optional[str] = None


class BulkOperationsListResponse(BaseModel):
    """Response for bulk operations listing."""
    operations: List[Dict[str, Any]]
    total: int


# Cache Models
class CacheStatsResponse(BaseModel):
    """Response for cache statistics."""
    cache_enabled: bool
    local_cache_entries: int
    total_hits: int
    total_misses: int
    hit_rate_percent: float
    total_size_bytes: int
    redis_stats: Optional[Dict[str, Any]] = None


class CacheInvalidationRequest(BaseModel):
    """Request for cache invalidation."""
    tags: Optional[List[str]] = None
    patterns: Optional[List[str]] = None


# Generic Response Models
class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
