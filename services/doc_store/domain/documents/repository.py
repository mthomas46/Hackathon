"""Document repository for data access operations.

Handles all database interactions for documents.
"""
import hashlib
import json
from typing import List, Optional, Dict, Any
from services.shared.utilities import utc_now
from ...db.queries import execute_query, get_document_by_id, insert_document, update_document_metadata
from ...core.entities import Document


class DocumentRepository:
    """Repository for document data access."""

    @staticmethod
    def calculate_content_hash(content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def get_by_id(document_id: str) -> Optional[Document]:
        """Get document by ID."""
        row = get_document_by_id(document_id)
        if not row:
            return None

        return Document(
            id=row['id'],
            content=row['content'],
            content_hash=row['content_hash'],
            metadata=json.loads(row['metadata'] or '{}'),
            correlation_id=row.get('correlation_id'),
            created_at=row['created_at'],
            updated_at=row.get('updated_at')
        )

    @staticmethod
    def get_by_content_hash(content_hash: str) -> Optional[Document]:
        """Get document by content hash."""
        row = execute_query(
            "SELECT * FROM documents WHERE content_hash = ?",
            (content_hash,),
            fetch_one=True
        )
        if not row:
            return None

        return Document(
            id=row['id'],
            content=row['content'],
            content_hash=row['content_hash'],
            metadata=json.loads(row['metadata'] or '{}'),
            correlation_id=row.get('correlation_id'),
            created_at=row['created_at'],
            updated_at=row.get('updated_at')
        )

    @staticmethod
    def save(document: Document) -> None:
        """Save document to database."""
        insert_document(
            doc_id=document.id,
            content=document.content,
            content_hash=document.content_hash,
            metadata=document.metadata,
            correlation_id=document.correlation_id
        )

    @staticmethod
    def update_metadata(document_id: str, metadata: Dict[str, Any]) -> None:
        """Update document metadata."""
        update_document_metadata(document_id, metadata)

    @staticmethod
    def list_documents(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List documents with pagination."""
        return execute_query(
            """
            SELECT id, content_hash, metadata, correlation_id, created_at
            FROM documents
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
            fetch_all=True
        )

    @staticmethod
    def search_documents(query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Full-text search documents."""
        from ...db.queries import search_documents
        return search_documents(query, limit)

    @staticmethod
    def get_quality_metrics(limit: int = 1000) -> List[Dict[str, Any]]:
        """Get document quality metrics."""
        # Get recent documents for quality analysis
        rows = execute_query(
            """
            SELECT id, content_hash, metadata, created_at
            FROM documents
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
            fetch_all=True
        )

        # Calculate quality flags for each document
        import sys
        sys.path.append('services/doc_store')
        from logic import compute_quality_flags

        return compute_quality_flags(rows)

    @staticmethod
    def get_documents_by_correlation_id(correlation_id: str) -> List[Dict[str, Any]]:
        """Get documents by correlation ID."""
        return execute_query(
            "SELECT * FROM documents WHERE correlation_id = ? ORDER BY created_at DESC",
            (correlation_id,),
            fetch_all=True
        )

    @staticmethod
    def delete_document(document_id: str) -> None:
        """Delete document by ID."""
        execute_query("DELETE FROM documents WHERE id = ?", (document_id,))
