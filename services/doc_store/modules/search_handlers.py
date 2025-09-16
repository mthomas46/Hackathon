"""Search handlers for Doc Store service.

Handles the complex logic for search and quality endpoints, including
advanced filtering, faceted search, and enhanced query capabilities.
"""
from typing import Optional, List, Dict, Any, Tuple
import json
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from logic import compute_quality_flags
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
    async def handle_advanced_search(
        q: Optional[str] = None,
        content_type: Optional[str] = None,
        source_type: Optional[str] = None,
        language: Optional[str] = None,
        tags: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        has_analysis: Optional[bool] = None,
        min_score: Optional[float] = None,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Advanced search with filtering, faceting, and sorting capabilities."""
        try:
            # Build the base query
            query_parts = []
            params = []

            # Full-text search condition
            if q:
                query_parts.append("d.id IN (SELECT id FROM documents_fts WHERE documents_fts MATCH ?)")
                params.append(q)

            # Content type filter
            if content_type:
                query_parts.append("json_extract(d.metadata, '$.type') = ?")
                params.append(content_type)

            # Source type filter
            if source_type:
                query_parts.append("json_extract(d.metadata, '$.source_type') = ?")
                params.append(source_type)

            # Language filter
            if language:
                query_parts.append("json_extract(d.metadata, '$.language') = ?")
                params.append(language)

            # Tags filter (JSON array contains)
            if tags:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("d.metadata LIKE ?")
                    params.append(f"%{tag}%")
                if tag_conditions:
                    query_parts.append(f"({' OR '.join(tag_conditions)})")

            # Date range filters
            if date_from:
                query_parts.append("d.created_at >= ?")
                params.append(date_from)
            if date_to:
                query_parts.append("d.created_at <= ?")
                params.append(date_to)

            # Analysis filter
            if has_analysis is not None:
                if has_analysis:
                    query_parts.append("d.id IN (SELECT document_id FROM analyses)")
                else:
                    query_parts.append("d.id NOT IN (SELECT document_id FROM analyses)")

            # Build WHERE clause
            where_clause = " AND ".join(query_parts) if query_parts else "1=1"

            # Build ORDER BY clause
            order_mappings = {
                "relevance": "d.created_at",  # Default relevance by recency
                "date": "d.created_at",
                "size": "LENGTH(d.content)",
                "analysis_count": "(SELECT COUNT(*) FROM analyses WHERE document_id = d.id)"
            }
            order_field = order_mappings.get(sort_by, "d.created_at")
            order_direction = "DESC" if sort_order.lower() == "desc" else "ASC"

            # Execute search query
            search_query = f"""
                SELECT d.id, d.content, d.metadata, d.created_at,
                       LENGTH(d.content) as content_length,
                       (SELECT COUNT(*) FROM analyses WHERE document_id = d.id) as analysis_count,
                       (SELECT AVG(score) FROM analyses WHERE document_id = d.id AND score IS NOT NULL) as avg_analysis_score
                FROM documents d
                WHERE {where_clause}
                ORDER BY {order_field} {order_direction}
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            rows = execute_db_query(search_query, tuple(params), fetch_all=True)

            # Process results
            items = []
            for row in rows:
                doc_id, content, metadata, created_at, content_length, analysis_count, avg_score = row

                # Parse metadata
                try:
                    metadata_dict = json.loads(metadata or '{}')
                except:
                    metadata_dict = {}

                items.append({
                    "id": doc_id,
                    "content": content,
                    "metadata": metadata_dict,
                    "created_at": created_at,
                    "content_length": content_length,
                    "analysis_count": analysis_count or 0,
                    "average_analysis_score": avg_score or 0.0
                })

            # Generate facets
            facets = await SearchHandlers._generate_search_facets(q, content_type, source_type, date_from, date_to)

            # Calculate total count for pagination
            count_query = f"SELECT COUNT(*) FROM documents d WHERE {where_clause}"
            count_params = params[:-2]  # Remove limit and offset
            total_count = execute_db_query(count_query, tuple(count_params), fetch_one=True)[0]

            result = {
                "items": items,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "facets": facets,
                "query": {
                    "q": q,
                    "filters": {
                        "content_type": content_type,
                        "source_type": source_type,
                        "language": language,
                        "tags": tags,
                        "date_from": date_from,
                        "date_to": date_to,
                        "has_analysis": has_analysis,
                        "min_score": min_score
                    },
                    "sort": {"by": sort_by, "order": sort_order}
                }
            }

            context = build_doc_store_context("advanced_search", query=str(q), result_count=len(items))
            return create_doc_store_success_response("advanced search completed", result, **context)

        except Exception as e:
            context = build_doc_store_context("advanced_search", query=str(q))
            return handle_doc_store_error("perform advanced search", e, **context)

    @staticmethod
    async def _generate_search_facets(
        q: Optional[str] = None,
        content_type: Optional[str] = None,
        source_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate search facets for filtering options."""
        facets = {}

        # Content type facet
        content_type_rows = execute_db_query("""
            SELECT json_extract(metadata, '$.type') as content_type, COUNT(*) as count
            FROM documents
            WHERE json_extract(metadata, '$.type') IS NOT NULL
            GROUP BY content_type
            ORDER BY count DESC
            LIMIT 20
        """, fetch_all=True)
        facets["content_type"] = [{"value": row[0], "count": row[1]} for row in content_type_rows]

        # Source type facet
        source_type_rows = execute_db_query("""
            SELECT json_extract(metadata, '$.source_type') as source_type, COUNT(*) as count
            FROM documents
            WHERE json_extract(metadata, '$.source_type') IS NOT NULL
            GROUP BY source_type
            ORDER BY count DESC
            LIMIT 20
        """, fetch_all=True)
        facets["source_type"] = [{"value": row[0], "count": row[1]} for row in source_type_rows]

        # Language facet
        language_rows = execute_db_query("""
            SELECT json_extract(metadata, '$.language') as language, COUNT(*) as count
            FROM documents
            WHERE json_extract(metadata, '$.language') IS NOT NULL
            GROUP BY language
            ORDER BY count DESC
            LIMIT 20
        """, fetch_all=True)
        facets["language"] = [{"value": row[0], "count": row[1]} for row in language_rows]

        # Date ranges facet (last 30 days, 90 days, etc.)
        now = datetime.now()
        date_ranges = [
            ("last_7_days", now - timedelta(days=7)),
            ("last_30_days", now - timedelta(days=30)),
            ("last_90_days", now - timedelta(days=90)),
            ("last_year", now - timedelta(days=365))
        ]

        date_facets = []
        for label, cutoff_date in date_ranges:
            count = execute_db_query(
                "SELECT COUNT(*) FROM documents WHERE created_at >= ?",
                (cutoff_date.isoformat(),),
                fetch_one=True
            )[0]
            date_facets.append({"range": label, "count": count})
        facets["date_ranges"] = date_facets

        # Analysis status facet
        analyzed_count = execute_db_query(
            "SELECT COUNT(DISTINCT document_id) FROM analyses",
            fetch_one=True
        )[0]
        total_docs = execute_db_query("SELECT COUNT(*) FROM documents", fetch_one=True)[0]
        unanalyzed_count = total_docs - analyzed_count

        facets["analysis_status"] = [
            {"status": "analyzed", "count": analyzed_count},
            {"status": "unanalyzed", "count": unanalyzed_count}
        ]

        return facets

    @staticmethod
    async def handle_documents_quality(stale_threshold_days: int = 180, min_views: int = 3) -> QualityResponse:
        """Flag potentially stale, redundant, or low-signal documents."""
        from services.shared.utilities import ensure_directory
        import os
        db_path = os.environ.get("DOCSTORE_DB", "services/doc_store/db.sqlite3")
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
