"""Document repository for data access operations.

Handles all database interactions for documents.
"""
import hashlib
import json
from typing import List, Optional, Dict, Any
from ...core.repository import BaseRepository
from ...db.queries import execute_query, search_documents
from ...core.entities import Document


class DocumentRepository(BaseRepository[Document]):
    """Repository for document data access."""

    def __init__(self):
        super().__init__("documents")

    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _row_to_entity(self, row: Dict[str, Any]) -> Document:
        """Convert database row to Document entity."""
        from datetime import datetime
        return Document(
            id=row['id'],
            content=row['content'],
            content_hash=row['content_hash'],
            metadata=json.loads(row['metadata'] or '{}'),
            correlation_id=row.get('correlation_id'),
            created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if isinstance(row['created_at'], str) else row['created_at'],
            updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')) if row.get('updated_at') and isinstance(row['updated_at'], str) else row.get('updated_at')
        )

    def _entity_to_row(self, entity: Document) -> Dict[str, Any]:
        """Convert Document entity to database row."""
        return {
            'id': entity.id,
            'content': entity.content,
            'content_hash': entity.content_hash,
            'metadata': json.dumps(entity.metadata),
            'correlation_id': entity.correlation_id,
            'created_at': entity.created_at.isoformat(),
            'updated_at': entity.updated_at.isoformat() if entity.updated_at else None
        }

    def get_by_content_hash(self, content_hash: str) -> Optional[Document]:
        """Get document by content hash."""
        row = execute_query(
            "SELECT * FROM documents WHERE content_hash = ?",
            (content_hash,),
            fetch_one=True
        )
        return self._row_to_entity(row) if row else None

    def search_documents(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Full-text search documents."""
        return search_documents(query, limit)

    def get_quality_metrics(self, limit: int = 1000) -> List[Dict[str, Any]]:
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

    def get_documents_by_correlation_id(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get documents by correlation ID."""
        return execute_query(
            "SELECT * FROM documents WHERE correlation_id = ? ORDER BY created_at DESC",
            (correlation_id,),
            fetch_all=True
        )
