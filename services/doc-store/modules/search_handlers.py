"""Search handlers for Doc Store service.

Handles the complex logic for search and quality endpoints.
"""
from typing import Optional, List, Dict, Any

from .logic import compute_quality_flags
from .shared_utils import (
    execute_db_query,
    get_document_by_id,
    build_doc_store_context,
    create_doc_store_success_response,
    handle_doc_store_error
)
from .models import QualityResponse, QualityItemWithBadges, SearchResponse


class SearchHandlers:
    """Handles search and quality operations."""

    @staticmethod
    async def handle_search(q: str, limit: int = 20) -> Dict[str, Any]:
        """Full-text search over documents (best-effort FTS)."""
        items: List[Dict[str, Any]] = []
        use_semantic = False
        try:
            # Use the same database query function
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

    @staticmethod
    async def handle_documents_quality(stale_threshold_days: int = 180, min_views: int = 3) -> QualityResponse:
        """Flag potentially stale, redundant, or low-signal documents."""
        from services.shared.utilities import ensure_directory
        import os
        db_path = os.environ.get("DOCSTORE_DB", "services/doc-store/db.sqlite3")
        ensure_directory(os.path.dirname(db_path))
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        try:
            cur = conn.execute("SELECT id, content_hash, metadata, created_at FROM documents ORDER BY created_at DESC LIMIT 1000")
            rows = cur.fetchall()
        finally:
            conn.close()
        import json
        from datetime import datetime
        import time
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

    @staticmethod
    async def handle_list_style_examples(language: Optional[str] = None) -> Dict[str, Any]:
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
                    from .shared_utils import safe_json_loads
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

    @staticmethod
    async def handle_list_documents(limit: int = 500) -> Dict[str, Any]:
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
                from .shared_utils import safe_json_loads
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


# Create singleton instance
search_handlers = SearchHandlers()
