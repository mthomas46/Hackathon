"""Document operations for the Doc Store service.

This module contains all document CRUD operations and related functionality,
extracted from the main doc-store service to improve maintainability.
"""

import json
from typing import Optional, Dict, Any
import sqlite3

# Import shared utilities with fallback for different loading contexts
try:
    from ..modules.shared_utils import (
        get_doc_store_connection,
        return_connection_to_pool,
        handle_doc_store_error,
        execute_db_query,
        safe_json_dumps,
        generate_document_id,
        generate_content_hash,
        build_doc_store_context,
        create_doc_store_success_response
    )
except ImportError:
    try:
        from .shared_utils import (
            get_doc_store_connection,
            return_connection_to_pool,
            handle_doc_store_error,
            execute_db_query,
            safe_json_dumps,
            generate_document_id,
            generate_content_hash,
            build_doc_store_context,
            create_doc_store_success_response
        )
    except ImportError:
        # Fallback for when loaded via importlib
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        try:
            from modules.shared_utils import (
                get_doc_store_connection,
                return_connection_to_pool,
                handle_doc_store_error,
                execute_db_query,
                safe_json_dumps,
                generate_document_id,
                generate_content_hash,
                build_doc_store_context,
                create_doc_store_success_response
            )
        except ImportError:
            # Final fallback - import from current directory
            current_dir = os.path.dirname(__file__)
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from shared_utils import (
                get_doc_store_connection,
                return_connection_to_pool,
                handle_doc_store_error,
                execute_db_query,
                safe_json_dumps,
                generate_document_id,
                generate_content_hash,
                build_doc_store_context,
                create_doc_store_success_response
            )
from services.shared.utilities import utc_now
from services.shared.envelopes import DocumentEnvelope


def create_document_logic(req: Any, aioredis: Optional[Any] = None) -> Dict[str, Any]:
    """Core logic for creating a document with enhanced error handling and transaction safety."""
    context = build_doc_store_context("document_logic_creation")

    try:
        # Generate document identifiers using shared utilities
        doc_id = req.id or generate_document_id(req.content)
        chash = req.content_hash or generate_content_hash(req.content)
        context["doc_id"] = doc_id

        # Prepare metadata with content length
        meta_obj = _prepare_document_metadata(req)
        meta_json = safe_json_dumps(meta_obj)

        # Execute all database operations in a transaction
        conn = get_doc_store_connection()
        try:
            # Insert document
            conn.execute(
                """INSERT OR REPLACE INTO documents
                   (id, content, content_hash, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (doc_id, req.content, chash, meta_json, utc_now().isoformat())
            )

            # Handle style example indexing
            _handle_style_example_indexing_with_connection(conn, doc_id, chash, req.metadata)

            # Update FTS index
            _update_fts_index_with_connection(conn, doc_id, req.metadata, req.content)

            # Commit transaction
            conn.commit()

        except Exception as db_error:
            conn.rollback()
            raise db_error
        finally:
            # Return connection to pool instead of closing
            return_connection_to_pool(conn)

        # Prepare and return result
        result = {"id": doc_id, "content_hash": chash}

        # Handle Redis publishing (best-effort - doesn't affect success)
        _handle_redis_publish(aioredis, doc_id, chash, req, meta_obj)

        return result

    except Exception as e:
        return handle_doc_store_error("create document", e, **context)


def _prepare_document_metadata(req: Any) -> Dict[str, Any]:
    """Prepare document metadata with content length."""
    meta_obj = req.metadata.copy() if req.metadata else {}
    meta_obj.setdefault("content_length", len(req.content or ""))
    return meta_obj


def _handle_style_example_indexing_with_connection(conn: sqlite3.Connection, doc_id: str, chash: str, metadata: Optional[Dict[str, Any]]) -> None:
    """Handle indexing for style examples."""
    try:
        if not metadata or not isinstance(metadata, dict):
            return

        if metadata.get("type") == "style_example":
            language = (metadata.get("language") or "").lower()
            title = metadata.get("title") or None
            tags = ",".join(metadata.get("tags") or []) if isinstance(metadata.get("tags"), list) else None

            conn.execute(
                """INSERT OR REPLACE INTO style_examples
                   (id, document_id, language, title, tags, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (f"style:{language}:{chash[:12]}", doc_id, language, title, tags, utc_now().isoformat())
            )
    except Exception:
        # Best-effort indexing, continue on error
        pass


def _update_fts_index_with_connection(conn: sqlite3.Connection, doc_id: str, metadata: Optional[Dict[str, Any]], content: str) -> None:
    """Update FTS index for the document using provided database connection."""
    try:
        title = None
        tags = []

        if metadata and isinstance(metadata, dict):
            title = metadata.get("title")
            if isinstance(metadata.get("tags"), list):
                tags = metadata.get("tags") or []

        _fts_upsert_logic_with_connection(conn, doc_id, title, content or "", ",".join(tags))
    except Exception:
        # Best-effort FTS update, continue on error
        pass


def _handle_redis_publish(aioredis: Optional[Any], doc_id: str, chash: str, req: Any, meta_obj: Dict[str, Any]) -> None:
    """Handle Redis publishing for document creation."""
    if not aioredis:
        return

    try:
        host = os.environ.get("REDIS_HOST")
        if host:
            # Validate envelope shape for downstream consumers
            env = DocumentEnvelope(
                id=doc_id,
                version=None,
                correlation_id=req.correlation_id,
                source_refs=[],
                content_hash=chash,
                document={"id": doc_id, "content_hash": chash, "metadata": meta_obj or {}},
            )

            # Note: Async publishing should be handled in the calling function
            # For now, we prepare the envelope for the caller
    except Exception:
        # Best-effort Redis publish, continue on error
        pass


def create_document_enveloped_logic(env):
    """Core logic for creating a document from envelope with enhanced error handling."""
    try:
        inner = env.document or {}
        content = inner.get("content") or ""
        provided_id = env.id or inner.get("id")
        doc_id = provided_id or generate_document_id(content)
        chash = env.content_hash or inner.get("content_hash") or generate_content_hash(content)

        # Prepare metadata with content length
        meta_obj = inner.get("metadata") or {}
        meta_obj.setdefault("content_length", len(content))
        meta_json = safe_json_dumps(meta_obj)

        # Insert document using shared database utilities
        execute_db_query(
            """INSERT OR REPLACE INTO documents
               (id, content, content_hash, metadata, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (doc_id, content, chash, meta_json, utc_now().isoformat())
        )

        context = build_doc_store_context("enveloped_document_creation", doc_id=doc_id)
        return {"id": doc_id, "content_hash": chash}

    except Exception as e:
        context = build_doc_store_context("enveloped_document_creation")
        return handle_doc_store_error("create document from envelope", e, **context)


def _fts_upsert_logic_with_connection(conn: sqlite3.Connection, doc_id: str, title: Optional[str], content: str, tags: Optional[str]) -> None:
    """Update FTS index for a document using provided database connection."""
    try:
        conn.execute(
            """INSERT OR REPLACE INTO documents_fts (id, title, content, tags)
               VALUES (?, ?, ?, ?)""",
            (doc_id, title or "", content, tags or "")
        )
    except Exception:
        # Best-effort FTS update, continue on error
        pass
