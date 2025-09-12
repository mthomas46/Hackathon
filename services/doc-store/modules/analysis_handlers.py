"""Analysis handlers for Doc Store service.

Handles the complex logic for analysis endpoints.
"""
from typing import Optional, List, Dict, Any

from services.shared.utilities import stable_hash, utc_now

from .shared_utils import (
    execute_db_query,
    safe_json_dumps,
    safe_json_loads,
    build_doc_store_context,
    create_doc_store_success_response,
    handle_doc_store_error
)
from .models import ListAnalysesResponse


class AnalysisHandlers:
    """Handles analysis operations."""

    @staticmethod
    async def handle_put_analysis(req) -> Dict[str, Any]:
        """Store analysis results."""
        try:
            if not req.document_id and not req.content:
                return handle_doc_store_error(
                    "store analysis",
                    Exception("Provide document_id or content"),
                    error_code="VALIDATION_ERROR",
                    validation_fields=["document_id", "content"]
                )

            doc_id = req.document_id
            if not doc_id:
                # Store content as a document first
                from .document_handlers import document_handlers
                from .models import PutDocumentRequest
                dreq = PutDocumentRequest(content=req.content or "")
                doc_result = await document_handlers.handle_put_document(dreq)
                doc_id = doc_result.get("id") or await AnalysisHandlers._generate_document_id(req.content or "")

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
            return handle_doc_store_error("store analysis", e, error_code="DATABASE_ERROR", **context)

    @staticmethod
    async def handle_list_analyses(document_id: Optional[str] = None) -> Dict[str, Any]:
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

    @staticmethod
    async def _generate_document_id(content: str) -> str:
        """Generate document ID from content."""
        from .shared_utils import generate_document_id
        return generate_document_id(content)


# Create singleton instance
analysis_handlers = AnalysisHandlers()
