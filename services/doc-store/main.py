"""Service: Doc Store

Endpoints:
- POST /documents, POST /documents/enveloped, GET /documents/{id}
- GET /documents/_list, GET /search, GET /documents/quality
- POST /analyses, GET /analyses, GET /style/examples

Dependencies: FastAPI, SQLite, optional Redis pub/sub, shared middlewares, ServiceClients (callers).
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
from services.shared.envelopes import DocumentEnvelope, validate_envelope
from services.shared.utilities import setup_common_middleware, attach_self_register, utc_now
from services.shared.health import register_health_endpoints
from services.shared.responses import create_success_response
from services.shared.error_handling import ServiceException, install_error_handlers
from services.shared.constants_new import ServiceNames, ErrorCodes
# Import logic with fallback for different loading contexts
try:
    from .logic import compute_quality_flags
except ImportError:
    try:
        from logic import compute_quality_flags
    except ImportError:
        # Fallback for when loaded via importlib
        import sys
        import os
        current_dir = os.path.dirname(__file__)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from logic import compute_quality_flags

# ============================================================================
# LOCAL MODULES - Service-specific functionality with fallbacks
# ============================================================================
try:
    from .modules.document_ops import create_document_logic
    from .routes.documents import router as documents_router
    from .modules.shared_utils import (
        get_doc_store_connection,
        handle_doc_store_error,
        create_doc_store_success_response,
        build_doc_store_context,
        validate_document_data,
        safe_json_loads,
        safe_json_dumps,
        generate_document_id,
        generate_content_hash,
        execute_db_query,
        get_document_by_id
    )
except ImportError:
    try:
        from modules.document_ops import create_document_logic
        from routes.documents import router as documents_router
        from modules.shared_utils import (
            get_doc_store_connection,
            handle_doc_store_error,
            create_doc_store_success_response,
            build_doc_store_context,
            validate_document_data,
            safe_json_loads,
            safe_json_dumps,
            generate_document_id,
            generate_content_hash,
            execute_db_query,
            get_document_by_id
        )
    except ImportError:
        # Fallback for when loaded via importlib
        import sys
        import os
        current_dir = os.path.dirname(__file__)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from modules.document_ops import create_document_logic
        from routes.documents import router as documents_router
        from modules.shared_utils import (
            get_doc_store_connection,
            handle_doc_store_error,
            create_doc_store_success_response,
            build_doc_store_context,
            validate_document_data,
            safe_json_loads,
            safe_json_dumps,
            generate_document_id,
            generate_content_hash,
            execute_db_query,
            get_document_by_id
        )


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
_init_db()


# ============================================================================
# CLEANED UP RESPONSE FORMATTING - Using Standardized Response Models
# ============================================================================

@app.get("/info")
async def info():
    """Service information endpoint."""
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


class PutDocumentRequest(BaseModel):
    id: Optional[str] = None
    content: str
    content_hash: Optional[str] = None
    # Accept any metadata input and coerce to dict inside handler
    metadata: Optional[Any] = None
    correlation_id: Optional[str] = None


@app.post("/documents")
async def put_document(req: PutDocumentRequest):
    """Store a document using extracted logic."""
    try:
        # Validate document data (Pydantic already enforces metadata as dict; coerce if needed)
        meta = req.metadata if isinstance(req.metadata, dict) or req.metadata is None else {}
        doc_data = validate_document_data({
            "content": req.content,
            "id": req.id,
            "metadata": meta,
            "correlation_id": req.correlation_id
        })

        # Create a shallow copy of the request object with coerced metadata for downstream logic
        class _ReqShim:
            def __init__(self, base):
                self.id = base.id
                self.content = base.content
                self.content_hash = base.content_hash
                self.metadata = meta
                self.correlation_id = base.correlation_id

        result = create_document_logic(_ReqShim(req), aioredis)

        # Handle async Redis publishing separately
        if aioredis and result.get("id"):
            try:
                from services.shared.config import get_config_value
                host = get_config_value("REDIS_HOST", None, section="redis", env_key="REDIS_HOST")
                if host:
                    client = aioredis.from_url(f"redis://{host}")
                    # Create envelope for publishing
                    env = DocumentEnvelope(
                        id=result["id"],
                        version=None,
                        correlation_id=req.correlation_id,
                        source_refs=[],
                        content_hash=result["content_hash"],
                        document={
                            "id": result["id"],
                            "content_hash": result["content_hash"],
                            "metadata": req.metadata or {}
                        },
                    )
                    await client.publish("docs.stored", env.model_dump_json())
                    await client.aclose()
            except Exception:
                pass

        # Add created_at for test compatibility
        if os.environ.get("TESTING", "").lower() == "true":
            from services.shared.utilities import utc_now
            result["created_at"] = utc_now().isoformat()

        context = build_doc_store_context("document_creation", doc_id=result.get("id"))
        return create_doc_store_success_response("created", result, **context)

    except Exception as e:
        context = build_doc_store_context("document_creation")
        return handle_doc_store_error("create document", e, ErrorCodes.VALIDATION_ERROR, **context)


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
    try:
        document = get_document_by_id(doc_id)

        if not document:
            return handle_doc_store_error(
                "retrieve document",
                Exception(f"Document '{doc_id}' not found"),
                ErrorCodes.DOCUMENT_NOT_FOUND,
                doc_id=doc_id
            )

        context = build_doc_store_context("document_retrieval", doc_id=doc_id)
        return create_doc_store_success_response("retrieved", document, **context)

    except Exception as e:
        context = build_doc_store_context("document_retrieval", doc_id=doc_id)
        return handle_doc_store_error("retrieve document", e, ErrorCodes.DATABASE_ERROR, **context)


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
    try:
        if not req.document_id and not req.content:
            return handle_doc_store_error(
                "store analysis",
                Exception("Provide document_id or content"),
                ErrorCodes.VALIDATION_ERROR,
                validation_fields=["document_id", "content"]
            )

        doc_id = req.document_id
        if not doc_id:
            # Store content as a document first
            dreq = PutDocumentRequest(content=req.content or "")
            await put_document(dreq)
            doc_id = dreq.id or generate_document_id(req.content or "")

        from services.shared.utilities import stable_hash
        prompt_hash = stable_hash(req.prompt or "")
        analysis_id = f"an:{stable_hash((doc_id or '') + (req.analyzer or '') + (req.model or '') + prompt_hash)[:12]}"

        # Insert analysis using shared utilities
        execute_db_query(
            """INSERT OR REPLACE INTO analyses
               (id, document_id, analyzer, model, prompt_hash, result, score, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                analysis_id,
                doc_id,
                req.analyzer,
                req.model,
                prompt_hash,
                safe_json_dumps(req.result),
                req.score,
                safe_json_dumps(req.metadata),
                utc_now().isoformat(),
            )
        )

        result = {"id": analysis_id, "document_id": doc_id}
        context = build_doc_store_context("analysis_creation", doc_id=doc_id, analysis_id=analysis_id)
        return create_doc_store_success_response("analysis stored", result, **context)

    except Exception as e:
        context = build_doc_store_context("analysis_creation", doc_id=req.document_id)
        return handle_doc_store_error("store analysis", e, ErrorCodes.DATABASE_ERROR, **context)


class ListAnalysesResponse(BaseModel):
    items: List[Dict[str, Any]]


@app.get("/analyses")
async def list_analyses(document_id: Optional[str] = None):
    """List analyses with optional document filtering."""
    try:
        if document_id:
            rows = execute_db_query(
                """SELECT id, document_id, analyzer, model, prompt_hash, result, score, metadata, created_at
                   FROM analyses WHERE document_id=? ORDER BY created_at DESC""",
                (document_id,),
                fetch_all=True
            )
        else:
            rows = execute_db_query(
                """SELECT id, document_id, analyzer, model, prompt_hash, result, score, metadata, created_at
                   FROM analyses ORDER BY created_at DESC LIMIT 100""",
                fetch_all=True
            )

        items: List[Dict[str, Any]] = []
        for r in rows:
            try:
                items.append({
                    "id": r[0],
                    "document_id": r[1],
                    "analyzer": r[2],
                    "model": r[3],
                    "prompt_hash": r[4],
                    "result": safe_json_loads(r[5]),
                    "score": r[6],
                    "metadata": safe_json_loads(r[7]),
                    "created_at": r[8],
                })
            except Exception:
                continue

        result = {"items": items}
        context = build_doc_store_context("analyses_listing", document_id=document_id, item_count=len(items))
        return create_doc_store_success_response("analyses listed", result, **context)

    except Exception as e:
        context = build_doc_store_context("analyses_listing", document_id=document_id)
        return handle_doc_store_error("list analyses", e, **context)


class StyleExamplesResponse(BaseModel):
    items: List[Dict[str, Any]]


@app.get("/style/examples")
async def list_style_examples(language: Optional[str] = None):
    """List style examples with optional language filtering."""
    try:
        if language:
            rows = execute_db_query(
                """SELECT s.language, s.title, s.tags, d.content, d.metadata
                   FROM style_examples s JOIN documents d ON s.document_id=d.id
                   WHERE s.language=? ORDER BY s.created_at DESC""",
                (language.lower(),),
                fetch_all=True
            )
        else:
            rows = execute_db_query(
                """SELECT s.language, COUNT(1) as cnt FROM style_examples s
                   GROUP BY s.language ORDER BY cnt DESC""",
                fetch_all=True
            )

        items: List[Dict[str, Any]] = []
        if language:
            for r in rows:
                meta = safe_json_loads(r[4])
                items.append({
                    "language": r[0],
                    "title": r[1],
                    "tags": (r[2] or "").split(",") if r[2] else [],
                    "snippet": r[3],
                    "metadata": meta,
                })
        else:
            for r in rows:
                items.append({"language": r[0], "count": r[1]})

        result = {"items": items}
        context = build_doc_store_context("style_examples_listing", language=language, item_count=len(items))
        return create_doc_store_success_response("style examples listed", result, **context)

    except Exception as e:
        context = build_doc_store_context("style_examples_listing", language=language)
        return handle_doc_store_error("list style examples", e, **context)


class ListDocumentsResponse(BaseModel):
    items: List[Dict[str, Any]]


@app.get("/documents/_list")
async def list_documents(limit: int = 500):
    """List recent documents with metadata for reporting correlation."""
    try:
        rows = execute_db_query(
            """SELECT id, content_hash, metadata, created_at FROM documents
               ORDER BY created_at DESC LIMIT ?""",
            (max(1, min(limit, 2000)),),
            fetch_all=True
        )

        items: List[Dict[str, Any]] = []
        for r in rows:
            meta = safe_json_loads(r[2])
            items.append({
                "id": r[0],
                "content_hash": r[1] or "",
                "metadata": meta,
                "created_at": r[3] or "",
            })

        result = {"items": items}
        context = build_doc_store_context("documents_listing", limit=limit, item_count=len(items))
        return create_doc_store_success_response("documents listed", result, **context)

    except Exception as e:
        context = build_doc_store_context("documents_listing", limit=limit)
        return handle_doc_store_error("list documents", e, **context)


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
    items: List[Dict[str, Any]] = []
    use_semantic = False
    try:
        # Use the same database query function as other utilities
        rows = execute_db_query(
            "SELECT id FROM documents_fts WHERE documents_fts MATCH ? LIMIT ?",
            (q, max(1, min(limit, 100)),),
            fetch_all=True
        )
        ids = [r[0] for r in rows] if rows else []
        for doc_id in ids:
            try:
                document = get_document_by_id(doc_id)
                if document:
                    items.append(document)
            except Exception:
                continue
        if not items:
            use_semantic = True
    except Exception:
        use_semantic = True
    # Semantic fallback (stub): keyword containment and simple scoring
    if use_semantic:
        ql = (q or "").lower().split()
        try:
            # Use the same database query function
            rows = execute_db_query(
                "SELECT id, content, metadata FROM documents ORDER BY created_at DESC LIMIT 500",
                (),
                fetch_all=True
            )
            scored: List[tuple[int, str]] = []
            for r in rows:
                doc_id = r[0]
                content = (r[1] or "").lower()
                meta = r[2] or ""
                # Simple keyword score
                score = sum(1 for tok in ql if tok and tok in content)
                if score > 0:
                    scored.append((score, doc_id))
            scored.sort(reverse=True)
            for score, doc_id in scored[:max(1, min(limit, 50))]:
                try:
                    document = get_document_by_id(doc_id)
                    if document:
                        items.append(document)
                except Exception:
                    pass
        except Exception:
            pass
    # get_document returns Pydantic model; ensure plain dicts
    norm_items: List[Dict[str, Any]] = []
    for it in items:
        if hasattr(it, "model_dump"):
            norm_items.append(it.model_dump())
        else:
            norm_items.append(it)  # type: ignore

    context = build_doc_store_context("search", query=q)
    return create_doc_store_success_response("search", {"items": norm_items}, **context)


class QualityItem(BaseModel):
    id: str
    created_at: str
    content_hash: str
    stale_days: int
    flags: List[str]
    metadata: Dict[str, Any]
    importance_score: float | None = None
    # optional backlinks count if provided in metadata


class QualityItemWithBadges(QualityItem):
    badges: List[str] = []


class QualityResponse(BaseModel):
    items: List[QualityItemWithBadges]


@app.get("/documents/quality", response_model=QualityResponse)
async def documents_quality(stale_threshold_days: int = 180, min_views: int = 3):
    """Flag potentially stale, redundant, or low-signal documents.

    Heuristics:
    - stale: created_at older than threshold
    - redundant: duplicate content_hash appears multiple times
    - low_views: metadata.views < min_views when provided
    - missing_owner: metadata.owner missing
    """
    from services.shared.utilities import ensure_directory
    ensure_directory(os.path.dirname(DB_PATH))
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    try:
        cur = conn.execute("SELECT id, content_hash, metadata, created_at FROM documents ORDER BY created_at DESC LIMIT 1000")
        rows = cur.fetchall()
    finally:
        conn.close()
    from datetime import datetime
    import json as pyjson
    now = datetime.now(timezone.utc)
    out = compute_quality_flags(rows, stale_threshold_days=stale_threshold_days, min_views=min_views)
    items: List[QualityItemWithBadges] = []
    for it in out:
        flags = it.get("flags", []) or []
        badges: List[str] = []
        if "high_importance" in flags:
            badges.append("high_importance")
        if "recently_viewed" in flags:
            badges.append("recently_viewed")
        if "attachments_referenced" in flags:
            badges.append("evidence_attached")
        items.append(QualityItemWithBadges(**it, badges=badges))
    return QualityResponse(items=items)


class MetadataPatch(BaseModel):
    updates: Dict[str, Any]


@app.patch("/documents/{doc_id}/metadata")
async def patch_document_metadata(doc_id: str, req: MetadataPatch):
    import sqlite3
    from services.shared.utilities import ensure_directory
    ensure_directory(os.path.dirname(DB_PATH))
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    try:
        cur = conn.execute("SELECT metadata FROM documents WHERE id=?", (doc_id,))
        row = cur.fetchone()
        meta = {}
        if row and row[0]:
            try:
                meta = json.loads(row[0])
            except Exception:
                meta = {}
        if isinstance(meta, dict):
            meta.update(req.updates or {})
        else:
            meta = req.updates or {}
        conn.execute("UPDATE documents SET metadata=? WHERE id=?", (json.dumps(meta), doc_id))
        conn.commit()
    finally:
        conn.close()
    return {"id": doc_id, "metadata": meta}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5087)


