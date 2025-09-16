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
