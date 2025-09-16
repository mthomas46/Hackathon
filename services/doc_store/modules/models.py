"""Request and response models for Doc Store service.

Contains all Pydantic models used for API requests and responses.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class PutDocumentRequest(BaseModel):
    """Request model for storing documents."""
    id: Optional[str] = None
    content: str
    content_hash: Optional[str] = None
    # Accept any metadata input and coerce to dict inside handler
    metadata: Optional[Any] = None
    correlation_id: Optional[str] = None


class GetDocumentResponse(BaseModel):
    """Response model for document retrieval."""
    id: str
    content: str
    content_hash: str
    metadata: Dict[str, Any]
    created_at: str


class PutAnalysisRequest(BaseModel):
    """Request model for storing analysis results."""
    document_id: Optional[str] = None
    content: Optional[str] = None
    analyzer: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    result: Dict[str, Any]
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ListAnalysesResponse(BaseModel):
    """Response model for analysis listing."""
    items: List[Dict[str, Any]]


class StyleExamplesResponse(BaseModel):
    """Response model for style examples listing."""
    items: List[Dict[str, Any]]


class ListDocumentsResponse(BaseModel):
    """Response model for document listing."""
    items: List[Dict[str, Any]]


class QualityItem(BaseModel):
    """Quality assessment item."""
    id: str
    created_at: str
    content_hash: str
    stale_days: int
    flags: List[str]
    metadata: Dict[str, Any]
    importance_score: Optional[float] = None


class QualityItemWithBadges(QualityItem):
    """Quality item with badges."""
    badges: List[str] = []


class QualityResponse(BaseModel):
    """Response model for quality assessment."""
    items: List[QualityItemWithBadges]


class SearchResponse(BaseModel):
    """Response model for search operations."""
    items: List[Dict[str, Any]]


class MetadataPatch(BaseModel):
    """Request model for metadata updates."""
    updates: Dict[str, Any]


class AnalyticsResponse(BaseModel):
    """Response model for analytics endpoint."""
    total_documents: int
    total_analyses: int
    total_ensembles: int
    total_style_examples: int
    storage_stats: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    temporal_trends: Dict[str, Any]
    content_insights: Dict[str, Any]
    relationship_insights: Dict[str, Any]


class AnalyticsSummaryResponse(BaseModel):
    """Response model for analytics summary endpoint."""
    summary: Dict[str, Any]
    key_insights: List[str]
    recommendations: List[str]


class AdvancedSearchRequest(BaseModel):
    """Request model for advanced search endpoint."""
    q: Optional[str] = None
    content_type: Optional[str] = None
    source_type: Optional[str] = None
    language: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    has_analysis: Optional[bool] = None
    min_score: Optional[float] = None
    sort_by: str = "relevance"
    sort_order: str = "desc"
    limit: int = 20
    offset: int = 0


class FacetItem(BaseModel):
    """Facet item model."""
    value: str
    count: int


class DateRangeFacet(BaseModel):
    """Date range facet model."""
    range: str
    count: int


class AnalysisStatusFacet(BaseModel):
    """Analysis status facet model."""
    status: str
    count: int


class SearchFacets(BaseModel):
    """Search facets model."""
    content_type: List[FacetItem]
    source_type: List[FacetItem]
    language: List[FacetItem]
    date_ranges: List[DateRangeFacet]
    analysis_status: List[AnalysisStatusFacet]


class AdvancedSearchItem(BaseModel):
    """Advanced search result item."""
    id: str
    content: str
    metadata: Dict[str, Any]
    created_at: str
    content_length: int
    analysis_count: int
    average_analysis_score: float


class AdvancedSearchResponse(BaseModel):
    """Response model for advanced search endpoint."""
    items: List[AdvancedSearchItem]
    total: int
    limit: int
    offset: int
    facets: SearchFacets
    query: Dict[str, Any]


class DocumentVersion(BaseModel):
    """Document version model."""
    id: str
    version_number: int
    content_hash: str
    change_summary: str
    changed_by: str
    created_at: str
    content_size: int


class DocumentVersionsResponse(BaseModel):
    """Response model for document versions listing."""
    document_id: str
    total_versions: int
    versions: List[DocumentVersion]
    limit: int
    offset: int


class DocumentVersionDetail(BaseModel):
    """Detailed document version model."""
    id: str
    document_id: str
    version_number: int
    content: str
    content_hash: str
    metadata: Dict[str, Any]
    change_summary: str
    changed_by: str
    created_at: str


class VersionComparison(BaseModel):
    """Version comparison model."""
    document_id: str
    version_a: Dict[str, Any]
    version_b: Dict[str, Any]
    differences: Dict[str, Any]


class VersionRollbackRequest(BaseModel):
    """Request model for version rollback."""
    version_number: int
    changed_by: Optional[str] = None


class VersionCleanupRequest(BaseModel):
    """Request model for version cleanup."""
    keep_versions: int = 10


class AddRelationshipRequest(BaseModel):
    """Request model for adding relationships."""
    source_id: str
    target_id: str
    relationship_type: str
    strength: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class RelationshipInfo(BaseModel):
    """Relationship information model."""
    id: str
    source_id: str
    target_id: str
    relationship_type: str
    strength: float
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    related_document_title: Optional[str] = None
    related_document_metadata: Dict[str, Any] = {}


class RelationshipsResponse(BaseModel):
    """Response model for relationship queries."""
    document_id: str
    relationships: List[RelationshipInfo]
    total_count: int
    direction: str
    relationship_type_filter: Optional[str] = None


class GraphPath(BaseModel):
    """Graph path model."""
    source: str
    target: str
    type: str
    strength: float
    metadata: Dict[str, Any]


class PathsResponse(BaseModel):
    """Response model for path finding."""
    start_document: str
    end_document: str
    max_depth: int
    paths_found: int
    paths: List[List[GraphPath]]


class GraphStatisticsResponse(BaseModel):
    """Response model for graph statistics."""
    total_relationships: int
    relationship_types: List[Dict[str, Any]]
    top_nodes_by_degree: List[Dict[str, Any]]
    connected_components: Dict[str, Any]
    average_relationship_strength: float
    graph_density: float


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""
    cache_enabled: bool
    local_cache_entries: int
    total_hits: int
    total_misses: int
    hit_rate_percent: float
    total_size_bytes: int
    evictions: int
    avg_response_time_ms: float
    redis_stats: Dict[str, Any]
    uptime_seconds: float


class CacheInvalidationRequest(BaseModel):
    """Request model for cache invalidation."""
    tags: Optional[List[str]] = None
    operation: Optional[str] = None


class TagDocumentRequest(BaseModel):
    """Request model for tagging a document."""
    force_retag: bool = False


class TagSearchRequest(BaseModel):
    """Request model for tag-based search."""
    tags: List[str]
    categories: Optional[List[str]] = None
    min_confidence: float = 0.0
    limit: int = 50


class TaxonomyNodeRequest(BaseModel):
    """Request model for creating taxonomy nodes."""
    tag: str
    category: str
    description: str = ""
    parent_tag: Optional[str] = None
    synonyms: Optional[List[str]] = None


class TagInfo(BaseModel):
    """Tag information model."""
    id: str
    tag: str
    category: str
    confidence: float
    metadata: Dict[str, Any]
    created_at: str


class DocumentTagsResponse(BaseModel):
    """Response model for document tags."""
    document_id: str
    tags: List[TagInfo]
    total_tags: int
    category_filter: Optional[str] = None


class TagSearchResult(BaseModel):
    """Tag search result model."""
    document_id: str
    content: str
    metadata: Dict[str, Any]
    created_at: str
    tag_matches: int
    avg_tag_confidence: float


class TagSearchResponse(BaseModel):
    """Response model for tag search."""
    query: Dict[str, Any]
    results: List[TagSearchResult]
    total_results: int


class TagStatisticsResponse(BaseModel):
    """Response model for tag statistics."""
    total_tags: int
    total_tagged_documents: int
    total_documents: int
    tag_coverage_percentage: float
    category_distribution: List[Dict[str, Any]]
    popular_tags: List[Dict[str, Any]]


class TaxonomyNode(BaseModel):
    """Taxonomy node model."""
    tag: str
    category: str
    description: str
    parent_tag: Optional[str]
    synonyms: List[str]
    created_at: str
    children: List[Dict[str, Any]] = []


class TaxonomyTreeResponse(BaseModel):
    """Response model for taxonomy tree."""
    root_category: Optional[str]
    taxonomy_tree: Dict[str, List[TaxonomyNode]]


class LifecyclePolicyRequest(BaseModel):
    """Request model for creating lifecycle policies."""
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int = 0


class LifecycleTransitionRequest(BaseModel):
    """Request model for phase transitions."""
    new_phase: str
    reason: Optional[str] = None


class LifecyclePolicyInfo(BaseModel):
    """Lifecycle policy information."""
    id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int
    enabled: bool
    created_at: str
    updated_at: str


class LifecycleInfo(BaseModel):
    """Document lifecycle information."""
    id: str
    document_id: str
    current_phase: str
    retention_period_days: Optional[int]
    archival_date: Optional[str]
    deletion_date: Optional[str]
    last_reviewed: Optional[str]
    compliance_status: str
    applied_policies: List[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class LifecycleReportResponse(BaseModel):
    """Response model for lifecycle reports."""
    phase_distribution: List[Dict[str, Any]]
    upcoming_transitions: Dict[str, Any]
    recent_events: List[Dict[str, Any]]
    policy_effectiveness: List[Dict[str, Any]]
    report_period_days: int


class LifecycleStatusResponse(BaseModel):
    """Response model for lifecycle status."""
    lifecycle: LifecycleInfo
    next_transition: Optional[Dict[str, Any]] = None
    compliance_issues: List[str] = []


class PoliciesListResponse(BaseModel):
    """Response model for listing policies."""
    policies: List[LifecyclePolicyInfo]
    total: int


class WebhookRequest(BaseModel):
    """Request model for registering webhooks."""
    name: str
    url: str
    events: List[str]
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    retry_count: int = 3
    timeout_seconds: int = 30


class WebhookInfo(BaseModel):
    """Webhook information."""
    id: str
    name: str
    url: str
    events: List[str]
    headers: Dict[str, str]
    is_active: bool
    retry_count: int
    timeout_seconds: int
    created_at: str
    updated_at: str


class NotificationEventInfo(BaseModel):
    """Notification event information."""
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    user_id: Optional[str]
    metadata: Dict[str, Any]
    created_at: str


class WebhookDeliveryInfo(BaseModel):
    """Webhook delivery information."""
    id: str
    webhook_id: str
    webhook_name: str
    event_type: str
    event_id: str
    status: str
    response_code: Optional[int]
    error_message: Optional[str]
    attempt_count: int
    delivered_at: Optional[str]
    created_at: str


class NotificationStatsResponse(BaseModel):
    """Response model for notification statistics."""
    period_days: int
    event_distribution: List[Dict[str, Any]]
    webhook_delivery_stats: Dict[str, Any]
    recent_failures: List[Dict[str, Any]]


class WebhookDeliveryResponse(BaseModel):
    """Response model for webhook deliveries."""
    deliveries: List[WebhookDeliveryInfo]
    total: int
    filters: Dict[str, Any]


class WebhooksListResponse(BaseModel):
    """Response model for listing webhooks."""
    webhooks: List[WebhookInfo]
    total: int


class EventsListResponse(BaseModel):
    """Response model for listing events."""
    events: List[NotificationEventInfo]
    total: int
    filters: Dict[str, Any]


class BulkDocumentItem(BaseModel):
    """Bulk document creation item."""
    id: Optional[str] = None
    content: str
    metadata: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None


class BulkDocumentCreateRequest(BaseModel):
    """Request model for bulk document creation."""
    documents: List[BulkDocumentItem]


class BulkSearchQuery(BaseModel):
    """Bulk search query item."""
    q: Optional[str] = None
    content_type: Optional[str] = None
    source_type: Optional[str] = None
    language: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    has_analysis: Optional[bool] = None
    limit: int = 20
    offset: int = 0


class BulkSearchRequest(BaseModel):
    """Request model for bulk search."""
    queries: List[BulkSearchQuery]


class BulkTagRequest(BaseModel):
    """Request model for bulk tagging."""
    document_ids: List[str]


class BulkOperationStatus(BaseModel):
    """Response model for bulk operation status."""
    operation_id: str
    operation_type: str
    status: str
    progress: Dict[str, Any]
    created_at: str
    completed_at: Optional[str]
    errors: List[Dict[str, Any]]


class BulkOperationSummary(BaseModel):
    """Summary of bulk operation results."""
    operation_id: str
    operation_type: str
    status: str
    total_items: int
    successful_items: int
    failed_items: int
    created_at: str


class BulkOperationsListResponse(BaseModel):
    """Response model for listing bulk operations."""
    operations: List[BulkOperationSummary]
    total: int
    status_filter: Optional[str]
