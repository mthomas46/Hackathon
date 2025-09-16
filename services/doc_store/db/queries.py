"""Common database query operations for Doc Store service.

Provides reusable query functions to reduce code duplication.
"""
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from .connection import doc_store_db_connection


def execute_query(query: str, params: Optional[Tuple] = None,
                  fetch_one: bool = False, fetch_all: bool = False) -> Union[None, Dict, List[Dict]]:
    """Execute a database query with proper connection management."""
    with doc_store_db_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(query, params or ())

            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            elif fetch_all:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return None

        except Exception:
            conn.rollback()
            raise


def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    """Get document by ID."""
    return execute_query(
        "SELECT * FROM documents WHERE id = ?",
        (document_id,),
        fetch_one=True
    )


def get_documents_list(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Get list of documents with pagination."""
    return execute_query(
        "SELECT id, content_hash, metadata, created_at FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
        fetch_all=True
    )


def search_documents(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Full-text search documents."""
    fts_results = execute_query(
        "SELECT rowid FROM documents_fts WHERE content MATCH ? LIMIT ?",
        (query, limit),
        fetch_all=True
    )

    if not fts_results:
        return []

    # Get document IDs from FTS results
    doc_ids = [str(row['rowid']) for row in fts_results]

    # Fetch actual documents
    placeholders = ','.join('?' for _ in doc_ids)
    return execute_query(
        f"SELECT * FROM documents WHERE rowid IN ({placeholders})",
        tuple(doc_ids),
        fetch_all=True
    )


def insert_document(doc_id: str, content: str, content_hash: str,
                   metadata: Dict[str, Any], correlation_id: Optional[str] = None) -> None:
    """Insert a new document."""
    from services.shared.utilities import utc_now

    execute_query("""
        INSERT INTO documents (id, content, content_hash, metadata, correlation_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_id,
        content,
        content_hash,
        json.dumps(metadata),
        correlation_id,
        utc_now().isoformat(),
        utc_now().isoformat()
    ))


def update_document_metadata(doc_id: str, metadata: Dict[str, Any]) -> None:
    """Update document metadata."""
    from services.shared.utilities import utc_now

    execute_query("""
        UPDATE documents SET metadata = ?, updated_at = ? WHERE id = ?
    """, (
        json.dumps(metadata),
        utc_now().isoformat(),
        doc_id
    ))


def insert_analysis(document_id: str, analyzer: str, model: str,
                   prompt_hash: str, result: Dict[str, Any],
                   score: Optional[float], metadata: Optional[Dict[str, Any]]) -> str:
    """Insert analysis result."""
    import uuid
    from services.shared.utilities import utc_now

    analysis_id = str(uuid.uuid4())
    execute_query("""
        INSERT INTO analyses (id, document_id, analyzer, model, prompt_hash, result, score, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        analysis_id,
        document_id,
        analyzer,
        model,
        prompt_hash,
        json.dumps(result),
        score,
        json.dumps(metadata) if metadata else None,
        utc_now().isoformat()
    ))

    return analysis_id


def get_analyses_by_document(document_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get analyses for a document."""
    return execute_query(
        "SELECT * FROM analyses WHERE document_id = ? ORDER BY created_at DESC LIMIT ?",
        (document_id, limit),
        fetch_all=True
    )


def insert_bulk_operation(operation_id: str, operation_type: str,
                         total_items: int, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Insert bulk operation record."""
    from services.shared.utilities import utc_now

    execute_query("""
        INSERT INTO bulk_operations (operation_id, operation_type, total_items, metadata, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        operation_id,
        operation_type,
        total_items,
        json.dumps(metadata) if metadata else None,
        utc_now().isoformat()
    ))


def update_bulk_operation_status(operation_id: str, status: str,
                               processed_items: int, successful_items: int,
                               failed_items: int, errors: Optional[List[str]] = None) -> None:
    """Update bulk operation status."""
    from services.shared.utilities import utc_now

    completed_at = utc_now().isoformat() if status in ['completed', 'failed'] else None

    execute_query("""
        UPDATE bulk_operations
        SET status = ?, processed_items = ?, successful_items = ?, failed_items = ?,
            errors = ?, completed_at = ?
        WHERE operation_id = ?
    """, (
        status,
        processed_items,
        successful_items,
        failed_items,
        json.dumps(errors) if errors else None,
        completed_at,
        operation_id
    ))


def get_bulk_operation_status(operation_id: str) -> Optional[Dict[str, Any]]:
    """Get bulk operation status."""
    return execute_query(
        "SELECT * FROM bulk_operations WHERE operation_id = ?",
        (operation_id,),
        fetch_one=True
    )


def list_bulk_operations(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """List bulk operations with optional status filter."""
    if status:
        return execute_query(
            "SELECT * FROM bulk_operations WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
            fetch_all=True
        )
    else:
        return execute_query(
            "SELECT * FROM bulk_operations ORDER BY created_at DESC LIMIT ?",
            (limit,),
            fetch_all=True
        )
