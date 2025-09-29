"""SQLite implementation of document repository."""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.entities import Document, DocumentId, Content, Metadata
from .document_repository import DocumentRepository


class SQLiteDocumentRepository(DocumentRepository):
    """SQLite implementation of document repository."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize SQLite repository."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content_text TEXT NOT NULL,
                    content_format TEXT NOT NULL,
                    author TEXT,
                    tags TEXT,  -- JSON array
                    repository_id TEXT,
                    version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT  -- JSON object
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_author ON documents(author)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_repository ON documents(repository_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_updated ON documents(updated_at)")

    async def save(self, document: Document) -> None:
        """Save a document to SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO documents
                (id, title, content_text, content_format, author, tags,
                 repository_id, version, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document.id.value,
                document.title,
                document.content.text,
                document.content.format,
                document.metadata.author,
                json.dumps(document.metadata.tags),
                document.repository_id,
                document.version,
                document.metadata.created_at.isoformat(),
                document.metadata.updated_at.isoformat(),
                json.dumps(document.metadata.properties)
            ))

    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, title, content_text, content_format, author, tags,
                       repository_id, version, created_at, updated_at, metadata
                FROM documents WHERE id = ?
            """, (document_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_document(row)

    async def get_all(self) -> List[Document]:
        """Get all documents from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, title, content_text, content_format, author, tags,
                       repository_id, version, created_at, updated_at, metadata
                FROM documents ORDER BY updated_at DESC
            """)

            return [self._row_to_document(row) for row in cursor.fetchall()]

    async def get_by_author(self, author: str) -> List[Document]:
        """Get documents by author from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, title, content_text, content_format, author, tags,
                       repository_id, version, created_at, updated_at, metadata
                FROM documents WHERE author = ? ORDER BY updated_at DESC
            """, (author,))

            return [self._row_to_document(row) for row in cursor.fetchall()]

    async def delete(self, document_id: str) -> bool:
        """Delete a document from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            return cursor.rowcount > 0

    def _row_to_document(self, row) -> Document:
        """Convert database row to Document entity."""
        id, title, content_text, content_format, author, tags_json, \
        repository_id, version, created_at_str, updated_at_str, metadata_json = row

        # Parse dates
        created_at = datetime.fromisoformat(created_at_str)
        updated_at = datetime.fromisoformat(updated_at_str)

        # Parse JSON fields
        tags = json.loads(tags_json) if tags_json else []
        properties = json.loads(metadata_json) if metadata_json else {}

        # Create value objects
        document_id = DocumentId(id)
        content = Content(text=content_text, format=content_format)
        metadata = Metadata(
            created_at=created_at,
            updated_at=updated_at,
            author=author,
            tags=tags,
            properties=properties
        )

        return Document(
            id=document_id,
            title=title,
            content=content,
            metadata=metadata,
            repository_id=repository_id,
            version=version
        )
