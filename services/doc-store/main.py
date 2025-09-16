"""Service: Doc Store

Endpoints:
- POST /documents: Store documents with metadata and content hashing
- GET /documents/{doc_id}: Retrieve documents by ID with full metadata
- GET /documents/_list: List recent documents with pagination for reporting
- PATCH /documents/{doc_id}/metadata: Update document metadata without changing content
- POST /analyses: Store analysis results linked to documents
- GET /analyses: List analyses with optional document filtering
- GET /search: Full-text search over document content (FTS)
- GET /documents/quality: Analyze document quality metrics and stale content
- GET /style/examples: List style examples by programming language

Responsibilities:
- Provide persistent storage for documents with deduplication via content hashing
- Maintain document metadata for correlation and reporting purposes
- Store analysis results from various analyzers with scoring and model tracking
- Support full-text search across document collections
- Enable document quality assessment and staleness detection
- Provide style examples for code documentation patterns

Dependencies: SQLite database with FTS support, shared utilities for document handling.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
import sqlite3

try:
    import redis.asyncio as aioredis  # type: ignore
except Exception:
    aioredis = None

# ============================================================================
# SHARED MODULES - Optimized import consolidation for consistency
# ============================================================================
from services.shared.config import load_yaml_config, get_config_value
from services.shared.utilities import setup_common_middleware, attach_self_register
from services.shared.health import register_health_endpoints
from services.shared.error_handling import install_error_handlers
from services.shared.constants_new import ServiceNames

# ============================================================================
# HANDLER MODULES - Extracted business logic
# ============================================================================
from .modules.models import (
    PutDocumentRequest, GetDocumentResponse, PutAnalysisRequest,
    ListAnalysesResponse, StyleExamplesResponse, ListDocumentsResponse,
    QualityResponse, SearchResponse, MetadataPatch, AnalyticsResponse, AnalyticsSummaryResponse,
    AdvancedSearchRequest, AdvancedSearchResponse, DocumentVersionsResponse, DocumentVersionDetail,
    VersionComparison, VersionRollbackRequest, VersionCleanupRequest, CacheStatsResponse, CacheInvalidationRequest,
    AddRelationshipRequest, RelationshipsResponse, PathsResponse, GraphStatisticsResponse,
    TagDocumentRequest, TagSearchRequest, TaxonomyNodeRequest, DocumentTagsResponse,
    TagSearchResponse, TagStatisticsResponse, TaxonomyTreeResponse
)
from .modules.database_init import init_database
from .modules.document_handlers import document_handlers
from .modules.analysis_handlers import analysis_handlers
from .modules.search_handlers import search_handlers
from .modules.analytics_handlers import analytics_handlers
from .modules.versioning_handlers import versioning_handlers
from .modules.cache_handlers import cache_handlers
from .modules.relationship_handlers import relationship_handlers
from .modules.tagging_handlers import tagging_handlers
from .modules.caching import docstore_cache

# ============================================================================
# ROUTES - Include existing router
# ============================================================================
from .routes.documents import router as documents_router

_cfg = load_yaml_config("services/doc-store/config.yaml")
DB_PATH = get_config_value("DOCSTORE_DB", _cfg.get("db_path", "services/doc-store/db.sqlite3"), section="doc_store", env_key="DOCSTORE_DB")


# ============================================================================
# APP INITIALIZATION - Using shared patterns for consistency
# ============================================================================

# Initialize database
def _init_db() -> None:
    """Initialize database tables and indexes."""
    conn = get_doc_store_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
              id TEXT PRIMARY KEY,
              content TEXT,
              content_hash TEXT,
              metadata TEXT,
              created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
              id TEXT PRIMARY KEY,
              document_id TEXT,
              analyzer TEXT,
              model TEXT,
              prompt_hash TEXT,
              result TEXT,
              score REAL,
              metadata TEXT,
              created_at TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ensembles (
              id TEXT PRIMARY KEY,
              document_id TEXT,
              config TEXT,
              results TEXT,
              analysis TEXT,
              created_at TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS style_examples (
              id TEXT PRIMARY KEY,
              document_id TEXT,
              language TEXT,
              title TEXT,
              tags TEXT,
              created_at TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        """)

        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash)",
            "CREATE INDEX IF NOT EXISTS idx_analyses_document_id ON analyses(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_analyses_prompt_hash ON analyses(prompt_hash)",
            "CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_style_examples_language ON style_examples(language)"
        ]

        for index in indexes:
            conn.execute(index)

        # Optional FTS for search (best-effort)
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                  id UNINDEXED,
                  title,
                  content,
                  tags
                )
            """)
        except Exception:
            pass

        conn.commit()
    finally:
        conn.close()

# Service configuration constants
SERVICE_NAME = "doc-store"
SERVICE_TITLE = "Doc Store"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5087

# Initialize FastAPI app with shared middleware
app = FastAPI(
    title=SERVICE_TITLE,
    description="Document storage and analysis service for the LLM Documentation Ecosystem",
    version=SERVICE_VERSION
)

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.DOC_STORE)
install_error_handlers(app)
register_health_endpoints(app, ServiceNames.DOC_STORE, SERVICE_VERSION)
attach_self_register(app, ServiceNames.DOC_STORE)

# Initialize database
init_database()

# Initialize cache
@app.on_event("startup")
async def startup_event():
    """Initialize cache on startup."""
    redis_host = get_config_value("REDIS_HOST", None, section="redis", env_key="REDIS_HOST")
    if redis_host:
        redis_url = f"redis://{redis_host}"
    else:
        redis_url = None

    cache_initialized = await docstore_cache.initialize()
    if cache_initialized:
        print(f"✅ Doc-store cache initialized with Redis")
    else:
        print(f"⚠️  Doc-store cache initialized without Redis (local only)")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up cache on shutdown."""
    await docstore_cache.close()


# ============================================================================
# CLEANED UP RESPONSE FORMATTING - Using Standardized Response Models
# ============================================================================

@app.get("/info")
async def info():
    """Service information endpoint."""
    from .modules.shared_utils import create_doc_store_success_response, build_doc_store_context, handle_doc_store_error
    try:
        context = build_doc_store_context("info_retrieval")
        return create_doc_store_success_response("info retrieved", {
            "service": ServiceNames.DOC_STORE,
            "version": app.version
        }, **context)
    except Exception as e:
        context = build_doc_store_context("info_retrieval")
        return handle_doc_store_error("retrieve info", e, **context)

@app.get("/config/effective")
async def config_effective():
    """Effective configuration endpoint."""
    from .modules.shared_utils import create_doc_store_success_response, build_doc_store_context, handle_doc_store_error
    try:
        config_data = {
            "db_path": DB_PATH,
            "middleware_enabled": True,
            "redis_enabled": aioredis is not None
        }
        context = build_doc_store_context("config_retrieval")
        return create_doc_store_success_response("configuration retrieved", config_data, **context)
    except Exception as e:
        context = build_doc_store_context("config_retrieval")
        return handle_doc_store_error("retrieve config", e, **context)

@app.get("/metrics")
async def metrics():
    """Service metrics endpoint."""
    from .modules.shared_utils import create_doc_store_success_response, build_doc_store_context, handle_doc_store_error
    try:
        metrics_data = {
            "service": ServiceNames.DOC_STORE,
            "routes": len(app.routes),
            "active_connections": 0,
            "database_path": DB_PATH
        }
        context = build_doc_store_context("metrics_retrieval", route_count=len(app.routes))
        return create_doc_store_success_response("metrics retrieved", metrics_data, **context)
    except Exception as e:
        context = build_doc_store_context("metrics_retrieval")
        return handle_doc_store_error("retrieve metrics", e, **context)



@app.post("/documents")
async def put_document(req: PutDocumentRequest):
    """Store a document with automatic content hashing and deduplication.

    Creates or updates a document with content hashing for deduplication,
    stores comprehensive metadata, and enables correlation tracking via
    correlation IDs for distributed operations.
    """
    return await document_handlers.handle_put_document(req)


app.include_router(documents_router)


class GetDocumentResponse(BaseModel):
    id: str
    content: str
    content_hash: str
    metadata: Dict[str, Any]
    created_at: str


@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document by ID with full content and metadata.

    Retrieves a complete document including content, metadata, and
    creation timestamp for analysis and processing workflows.
    """
    return await document_handlers.handle_get_document(doc_id)


class PutAnalysisRequest(BaseModel):
    document_id: Optional[str] = None
    content: Optional[str] = None
    analyzer: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    result: Dict[str, Any]
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@app.post("/analyses")
async def put_analysis(req: PutAnalysisRequest):
    """Store analysis results linked to documents with scoring.

    Stores analysis results with model tracking, prompt hash verification,
    and scoring for quality assessment and performance monitoring.
    """
    return await analysis_handlers.handle_put_analysis(req)


class ListAnalysesResponse(BaseModel):
    items: List[Dict[str, Any]]


@app.get("/analyses")
async def list_analyses(document_id: Optional[str] = None):
    """List analyses with optional document filtering and pagination.

    Retrieves analysis results filtered by document ID if specified,
    with support for pagination and chronological ordering.
    """
    return await analysis_handlers.handle_list_analyses(document_id)


class StyleExamplesResponse(BaseModel):
    items: List[Dict[str, Any]]


@app.get("/style/examples")
async def list_style_examples(language: Optional[str] = None):
    """List style examples with optional language filtering."""
    return await search_handlers.handle_list_style_examples(language)


class ListDocumentsResponse(BaseModel):
    items: List[Dict[str, Any]]


@app.get("/documents/_list")
async def list_documents(limit: int = 500):
    """List recent documents with metadata for reporting correlation."""
    return await search_handlers.handle_list_documents(limit)


def _fts_upsert(doc_id: str, title: Optional[str], content: str, tags: Optional[str]) -> None:
    """Best-effort upsert into FTS index."""
    try:
        from services.shared.utilities import ensure_directory
        ensure_directory(os.path.dirname(DB_PATH))
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        try:
            conn.execute("DELETE FROM documents_fts WHERE id=?", (doc_id,))
            conn.execute(
                "INSERT INTO documents_fts (id, title, content, tags) VALUES (?,?,?,?)",
                (doc_id, title or "", content or "", tags or ""),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        return


class SearchResponse(BaseModel):
    items: List[Dict[str, Any]]


@app.get("/search")
async def search(q: str, limit: int = 20):
    """Full-text search over documents with FTS ranking.

    Performs full-text search across document content, titles, and tags
    using SQLite FTS5 for efficient and relevant result ranking.
    """
    return await search_handlers.handle_search(q, limit)


@app.post("/search/advanced", response_model=AdvancedSearchResponse)
async def advanced_search(req: AdvancedSearchRequest):
    """Advanced search with filtering, faceting, and sorting capabilities.

    Provides powerful search functionality with metadata filters, date ranges,
    content type filtering, and faceted results for enhanced discovery.
    """
    return await search_handlers.handle_advanced_search(
        q=req.q,
        content_type=req.content_type,
        source_type=req.source_type,
        language=req.language,
        tags=req.tags,
        date_from=req.date_from,
        date_to=req.date_to,
        has_analysis=req.has_analysis,
        min_score=req.min_score,
        sort_by=req.sort_by,
        sort_order=req.sort_order,
        limit=req.limit,
        offset=req.offset
    )

@app.get("/documents/quality", response_model=QualityResponse)
async def documents_quality(stale_threshold_days: int = 180, min_views: int = 3):
    """Analyze document quality and flag issues.

    Identifies potentially stale documents based on age thresholds,
    detects low-signal content based on view metrics, and provides
    quality assessment recommendations.
    """
    return await search_handlers.handle_documents_quality(stale_threshold_days, min_views)

@app.patch("/documents/{doc_id}/metadata")
async def patch_document_metadata(doc_id: str, req: MetadataPatch):
    """Patch document metadata."""
    return await document_handlers.handle_patch_document_metadata(doc_id, req)


@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(days_back: int = 30):
    """Get comprehensive analytics and insights for the document store.

    Provides detailed analytics on storage patterns, quality trends, usage statistics,
    and insights into content relationships and evolution over the specified time period.
    """
    return await analytics_handlers.handle_analytics(days_back)


@app.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary():
    """Get analytics summary with key insights and recommendations.

    Provides a high-level overview of document store health, key metrics,
    and actionable recommendations for optimization and maintenance.
    """
    return await analytics_handlers.handle_analytics_summary()


@app.get("/documents/{document_id}/versions", response_model=DocumentVersionsResponse)
async def get_document_versions(document_id: str, limit: int = 50, offset: int = 0):
    """Get version history for a document.

    Retrieves the complete version history for a document, including version numbers,
    change summaries, timestamps, and metadata for each version.
    """
    return await versioning_handlers.handle_get_document_versions(document_id, limit, offset)


@app.get("/documents/{document_id}/versions/{version_number}", response_model=DocumentVersionDetail)
async def get_document_version(document_id: str, version_number: int):
    """Get a specific version of a document.

    Retrieves the full content and metadata for a specific version of a document,
    allowing for detailed inspection and comparison.
    """
    return await versioning_handlers.handle_get_document_version(document_id, version_number)


@app.get("/documents/{document_id}/versions/{version_a}/compare/{version_b}", response_model=VersionComparison)
async def compare_document_versions(document_id: str, version_a: int, version_b: int):
    """Compare two versions of a document.

    Provides detailed comparison between two document versions, highlighting
    content changes, metadata differences, and change summaries.
    """
    return await versioning_handlers.handle_compare_versions(document_id, version_a, version_b)


@app.post("/documents/{document_id}/rollback")
async def rollback_document_version(document_id: str, req: VersionRollbackRequest):
    """Rollback a document to a previous version.

    Reverts a document to a specified previous version, creating a new version
    record to maintain the complete change history.
    """
    return await versioning_handlers.handle_rollback_version(document_id, req)


@app.post("/documents/{document_id}/versions/cleanup")
async def cleanup_document_versions(document_id: str, req: VersionCleanupRequest):
    """Clean up old versions of a document.

    Removes old versions beyond the specified retention limit, keeping only
    the most recent versions to manage storage efficiently.
    """
    return await versioning_handlers.handle_cleanup_versions(document_id, req)


@app.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Get comprehensive cache performance statistics.

    Provides detailed metrics on cache performance, hit rates, memory usage,
    and Redis connection status for performance monitoring and optimization.
    """
    return await cache_handlers.handle_get_cache_stats()


@app.post("/cache/invalidate")
async def invalidate_cache(req: CacheInvalidationRequest):
    """Invalidate cache entries by tags or operation.

    Allows selective cache invalidation to ensure data freshness while
    maintaining performance for unchanged data.
    """
    return await cache_handlers.handle_invalidate_cache(tags=req.tags, operation=req.operation)


@app.post("/cache/warmup")
async def warmup_cache():
    """Warm up the cache with frequently accessed data.

    Preloads commonly accessed documents, analytics, and search results
    to improve initial response times after service restart.
    """
    return await cache_handlers.handle_warmup_cache()


@app.post("/cache/optimize")
async def optimize_cache():
    """Optimize cache performance and memory usage.

    Performs cache cleanup, memory optimization, and performance tuning
    to maintain optimal caching efficiency.
    """
    return await cache_handlers.handle_optimize_cache()


@app.post("/relationships", response_model=Dict[str, Any])
async def add_relationship(req: AddRelationshipRequest):
    """Add a relationship between documents.

    Creates a directed relationship between two documents with configurable
    strength and metadata for building knowledge graphs and dependency maps.
    """
    return await relationship_handlers.handle_add_relationship(
        req.source_id, req.target_id, req.relationship_type, req.strength, req.metadata
    )


@app.get("/documents/{document_id}/relationships", response_model=RelationshipsResponse)
async def get_document_relationships(document_id: str, relationship_type: Optional[str] = None,
                                   direction: str = "both", limit: int = 50):
    """Get relationships for a document.

    Retrieves all relationships connected to a document, with optional filtering
    by relationship type and direction (incoming, outgoing, or both).
    """
    return await relationship_handlers.handle_get_relationships(
        document_id, relationship_type, direction, limit
    )


@app.get("/graph/paths/{start_id}/{end_id}", response_model=PathsResponse)
async def find_relationship_paths(start_id: str, end_id: str, max_depth: int = 3):
    """Find relationship paths between documents.

    Discovers connection paths between two documents through the relationship
    graph, useful for understanding indirect dependencies and relationships.
    """
    return await relationship_handlers.handle_find_paths(start_id, end_id, max_depth)


@app.get("/graph/statistics", response_model=GraphStatisticsResponse)
async def get_graph_statistics():
    """Get comprehensive relationship graph statistics.

    Provides insights into the document relationship network including
    connectivity, relationship types distribution, and graph metrics.
    """
    return await relationship_handlers.handle_graph_statistics()


@app.post("/documents/{document_id}/relationships/extract")
async def extract_document_relationships(document_id: str):
    """Extract relationships for an existing document.

    Analyzes document content and metadata to automatically discover and
    store relationships with other documents in the system.
    """
    return await relationship_handlers.handle_extract_relationships(document_id)


@app.post("/documents/{document_id}/tags", response_model=Dict[str, Any])
async def tag_document(document_id: str, req: TagDocumentRequest):
    """Automatically tag a document with semantic information.

    Analyzes document content and metadata to extract semantic entities
    and generate intelligent tags for improved discoverability.
    """
    return await tagging_handlers.handle_tag_document(document_id)


@app.get("/documents/{document_id}/tags", response_model=DocumentTagsResponse)
async def get_document_tags(document_id: str, category: Optional[str] = None):
    """Get semantic tags for a document.

    Retrieves automatically generated tags and their confidence scores,
    optionally filtered by category (programming_language, framework, etc.).
    """
    return await tagging_handlers.handle_get_document_tags(document_id, category)


@app.post("/search/tags", response_model=TagSearchResponse)
async def search_by_tags(req: TagSearchRequest):
    """Search documents by semantic tags.

    Finds documents that match specified tags with configurable confidence
    thresholds and category filtering for precise content discovery.
    """
    return await tagging_handlers.handle_search_by_tags(
        req.tags, req.categories, req.min_confidence, req.limit
    )


@app.get("/tags/statistics", response_model=TagStatisticsResponse)
async def get_tag_statistics():
    """Get comprehensive tag statistics and analytics.

    Provides insights into tag distribution, coverage, and usage patterns
    across the document collection for content strategy optimization.
    """
    return await tagging_handlers.handle_get_tag_statistics()


@app.post("/taxonomy/nodes", response_model=Dict[str, Any])
async def create_taxonomy_node(req: TaxonomyNodeRequest):
    """Create a taxonomy node for tag organization.

    Defines hierarchical relationships between tags with descriptions
    and synonyms for improved semantic understanding and search.
    """
    return await tagging_handlers.handle_create_taxonomy_node(
        req.tag, req.category, req.description, req.parent_tag, req.synonyms
    )


@app.get("/taxonomy/tree", response_model=TaxonomyTreeResponse)
async def get_taxonomy_tree(root_category: Optional[str] = None):
    """Get hierarchical taxonomy tree structure.

    Retrieves the complete tag taxonomy with parent-child relationships,
    descriptions, and synonyms for semantic navigation and understanding.
    """
    return await tagging_handlers.handle_get_taxonomy_tree(root_category)


if __name__ == "__main__":
    """Run the Doc Store service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )


