"""Document repository for data access operations.

Handles all database interactions for documents.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional

from ...domain.entities import Document
from services.shared.domain.repositories.base_repository import SqlRepository
from ...db.queries import execute_query, search_documents


class DocumentRepository(SqlRepository[Document]):
    """Repository for document data access."""

    def __init__(self, connection_string: str):
        super().__init__(Document, connection_string)

    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _row_to_entity(self, row: Dict[str, Any]) -> Document:
        """Convert database row to Document entity."""
        from datetime import datetime
        
        # 🔍 DEBUG: Log raw row data
        print(f"🔍 [ROW_TO_ENTITY] raw row tags: {row.get('tags')}", flush=True)
        
        # Parse tags
        tags_raw = row.get("tags") or "[]"
        tags_parsed = json.loads(tags_raw)
        print(f"🔍 [ROW_TO_ENTITY] parsed tags: {tags_parsed}", flush=True)

        doc = Document(
            id=row["id"],
            content=row["content"],
            content_hash=row["content_hash"],
            metadata=json.loads(row["metadata"] or "{}"),
            tags=tags_parsed,  # ✅ Use parsed tags
            correlation_id=row.get("correlation_id"),
            created_at=(
                datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                if isinstance(row["created_at"], str)
                else row["created_at"]
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
                if row.get("updated_at") and isinstance(row["updated_at"], str)
                else row.get("updated_at")
            ),
        )
        
        print(f"🔍 [ROW_TO_ENTITY] Document.tags: {doc.tags}", flush=True)
        return doc

    def _entity_to_row(self, entity: Document) -> Dict[str, Any]:
        """Convert Document entity to database row."""
        # 🔍 DEBUG: Log tags before serialization
        print(f"🔍 [ENTITY_TO_ROW] entity.tags: {entity.tags}", flush=True)
        
        serialized_tags = json.dumps(entity.tags)
        print(f"🔍 [ENTITY_TO_ROW] serialized tags: {serialized_tags}", flush=True)
        
        row = {
            "id": entity.id,
            "content": entity.content,
            "content_hash": entity.content_hash,
            "metadata": json.dumps(entity.metadata),
            "tags": serialized_tags,  # ✅ CRITICAL FIX: Serialize tags to JSON
            "correlation_id": entity.correlation_id,
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
        }
        
        print(f"🔍 [ENTITY_TO_ROW] row dict tags: {row.get('tags')}", flush=True)
        return row

    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """Find document by ID (async version for base service compatibility)."""
        print(f"🔍 [REPOSITORY DEBUG] find_by_id called with: {document_id}", flush=True)
        
        try:
            row = execute_query(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,),
                fetch_one=True,
            )
            print(f"🔍 [REPOSITORY DEBUG] execute_query returned: {type(row)}", flush=True)
            if row:
                print(f"🔍 [REPOSITORY DEBUG] row has tags: {row.get('tags')}", flush=True)
            
            result = self._row_to_entity(row) if row else None
            print(f"🔍 [REPOSITORY DEBUG] returning Document with tags: {result.tags if result else 'None'}", flush=True)
            return result
        except Exception as e:
            print(f"🔍 [REPOSITORY DEBUG] ERROR: {e}", flush=True)
            raise
    
    async def find_by_content_hash(self, content_hash: str) -> Optional[Document]:
        """Find document by content hash (async version)."""
        row = execute_query(
            "SELECT * FROM documents WHERE content_hash = ?",
            (content_hash,),
            fetch_one=True,
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
            fetch_all=True,
        )

        # Calculate quality flags for each document
        import sys

        sys.path.append("services/doc_store")
        from logic import compute_quality_flags

        return compute_quality_flags(rows)

    def get_documents_by_correlation_id(
        self, correlation_id: str
    ) -> List[Dict[str, Any]]:
        """Get documents by correlation ID."""
        return execute_query(
            "SELECT * FROM documents WHERE correlation_id = ? ORDER BY created_at DESC",
            (correlation_id,),
            fetch_all=True,
        )

    def get_by_metadata_field(
        self, field_name: str, field_value: str
    ) -> List[Document]:
        """Get documents by a specific metadata field value."""
        # Use JSON_EXTRACT for SQLite JSON queries
        rows = execute_query(
            "SELECT * FROM documents WHERE json_extract(metadata, ?) = ? ORDER BY created_at DESC",
            (f"$.{field_name}", field_value),
            fetch_all=True,
        )
        return [self._row_to_entity(row) for row in rows]

    def get_by_metadata_field_exists(self, field_name: str) -> List[Document]:
        """Get documents where a specific metadata field exists."""
        # Use JSON_EXTRACT to check if field exists and is not null
        rows = execute_query(
            "SELECT * FROM documents WHERE json_extract(metadata, ?) IS NOT NULL ORDER BY created_at DESC",
            (f"$.{field_name}",),
            fetch_all=True,
        )
        return [self._row_to_entity(row) for row in rows]
