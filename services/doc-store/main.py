"""Doc Store Service

Document storage and analysis service for the LLM Documentation Ecosystem.
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
    QualityResponse, SearchResponse, MetadataPatch
)
from .modules.database_init import init_database
from .modules.document_handlers import document_handlers
from .modules.analysis_handlers import analysis_handlers
from .modules.search_handlers import search_handlers

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

# Initialize FastAPI app with shared middleware
app = FastAPI(title="Doc Store", version="1.0.0")

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.DOC_STORE)
install_error_handlers(app)
register_health_endpoints(app, ServiceNames.DOC_STORE, "1.0.0")
attach_self_register(app, ServiceNames.DOC_STORE)

# Initialize database
init_database()


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
    """Store a document."""
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
    """Get document by ID."""
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
    """Store analysis results."""
    return await analysis_handlers.handle_put_analysis(req)


class ListAnalysesResponse(BaseModel):
    items: List[Dict[str, Any]]


@app.get("/analyses")
async def list_analyses(document_id: Optional[str] = None):
    """List analyses with optional document filtering."""
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
    """Full-text search over documents (best-effort FTS)."""
    return await search_handlers.handle_search(q, limit)

@app.get("/documents/quality", response_model=QualityResponse)
async def documents_quality(stale_threshold_days: int = 180, min_views: int = 3):
    """Flag potentially stale, redundant, or low-signal documents."""
    return await search_handlers.handle_documents_quality(stale_threshold_days, min_views)

@app.patch("/documents/{doc_id}/metadata")
async def patch_document_metadata(doc_id: str, req: MetadataPatch):
    """Patch document metadata."""
    return await document_handlers.handle_patch_document_metadata(doc_id, req)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5087)


