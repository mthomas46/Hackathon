"""SQLite implementation of Document Relationship Repository.

This module provides a SQLite-based repository implementation for persistent
document relationship data storage and retrieval operations.
"""

import sqlite3
import json
from typing import Dict, List, Optional

from domain.entities.document_relationship import (
    DocumentRelationship,
    RelationshipType,
    AccessLevel
)
from domain.repositories.document_relationship_repository import DocumentRelationshipRepository


class SQLiteDocumentRelationshipRepository(DocumentRelationshipRepository):
    """SQLite implementation of DocumentRelationshipRepository."""

    def __init__(self, db_path: str = "user_store.db"):
        """Initialize the repository with database connection."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_relationships (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    access_level TEXT NOT NULL,
                    tags TEXT NOT NULL,              -- JSON array of document tags
                    services TEXT NOT NULL,          -- JSON array of related services
                    first_accessed_at TEXT NOT NULL,
                    last_accessed_at TEXT NOT NULL,
                    access_count INTEGER NOT NULL,
                    notify_on_updates BOOLEAN NOT NULL,
                    notify_on_comments BOOLEAN NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, document_id)
                )
            """)

            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_doc ON document_relationships(user_id, document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doc_user ON document_relationships(document_id, user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relationship_type ON document_relationships(relationship_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_access_level ON document_relationships(access_level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON document_relationships(tags)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_services ON document_relationships(services)")

            conn.commit()

    def _relationship_from_row(self, row) -> DocumentRelationship:
        """Convert database row to DocumentRelationship entity."""
        return DocumentRelationship(
            id=row[0],
            user_id=row[1],
            document_id=row[2],
            relationship_type=RelationshipType(row[3]),
            access_level=AccessLevel(row[4]),
            tags=json.loads(row[5]) if row[5] else [],
            services=json.loads(row[6]) if row[6] else [],
            first_accessed_at=row[7],
            last_accessed_at=row[8],
            access_count=row[9],
            notify_on_updates=bool(row[10]),
            notify_on_comments=bool(row[11]),
            created_at=row[12],
            updated_at=row[13]
        )

    async def save(self, relationship: DocumentRelationship) -> None:
        """Save a document relationship to the database."""
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT INTO document_relationships (
                        id, user_id, document_id, relationship_type, access_level,
                        tags, services, first_accessed_at, last_accessed_at,
                        access_count, notify_on_updates, notify_on_comments,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    relationship.id,
                    relationship.user_id,
                    relationship.document_id,
                    relationship.relationship_type.value,
                    relationship.access_level.value,
                    json.dumps(relationship.tags),
                    json.dumps(relationship.services),
                    relationship.first_accessed_at.isoformat(),
                    relationship.last_accessed_at.isoformat(),
                    relationship.access_count,
                    relationship.notify_on_updates,
                    relationship.notify_on_comments,
                    relationship.created_at.isoformat(),
                    relationship.updated_at.isoformat()
                ))
                conn.commit()
            except sqlite3.IntegrityError:
                # Relationship already exists, update it
                await self.update(relationship)

    async def find_by_id(self, relationship_id: str) -> Optional[DocumentRelationship]:
        """Find a relationship by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM document_relationships WHERE id = ?", (relationship_id,))
            row = cursor.fetchone()
            return self._relationship_from_row(row) if row else None

    async def find_by_user_and_document(self, user_id: str, document_id: str) -> Optional[DocumentRelationship]:
        """Find relationship between user and document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM document_relationships
                WHERE user_id = ? AND document_id = ?
            """, (user_id, document_id))
            row = cursor.fetchone()
            return self._relationship_from_row(row) if row else None

    async def find_relationships_by_user(self, user_id: str) -> List[DocumentRelationship]:
        """Find all relationships for a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM document_relationships WHERE user_id = ?", (user_id,))
            return [self._relationship_from_row(row) for row in cursor.fetchall()]

    async def find_relationships_by_document(self, document_id: str) -> List[DocumentRelationship]:
        """Find all relationships for a document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM document_relationships WHERE document_id = ?", (document_id,))
            return [self._relationship_from_row(row) for row in cursor.fetchall()]

    async def find_by_relationship_type(self, relationship_type: RelationshipType) -> List[DocumentRelationship]:
        """Find relationships by type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM document_relationships WHERE relationship_type = ?", (relationship_type.value,))
            return [self._relationship_from_row(row) for row in cursor.fetchall()]

    async def find_by_access_level(self, access_level: AccessLevel) -> List[DocumentRelationship]:
        """Find relationships by access level."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM document_relationships WHERE access_level = ?", (access_level.value,))
            return [self._relationship_from_row(row) for row in cursor.fetchall()]

    async def find_users_by_document_and_topic(self, document_id: str, topic: str) -> List[str]:
        """Find user IDs related to document with topic tags."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT user_id FROM document_relationships
                WHERE document_id = ? AND tags LIKE ?
            """, (document_id, f'%{topic}%'))
            return [row[0] for row in cursor.fetchall()]

    async def find_users_by_service_and_topic(self, service_name: str, topic: str) -> List[str]:
        """Find user IDs subscribed to service with topic expertise."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT user_id FROM document_relationships
                WHERE services LIKE ? AND tags LIKE ?
            """, (f'%{service_name}%', f'%{topic}%'))
            return [row[0] for row in cursor.fetchall()]

    async def find_documents_by_user_and_service(self, user_id: str, service_name: str) -> List[str]:
        """Find document IDs related to user through service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT document_id FROM document_relationships
                WHERE user_id = ? AND services LIKE ?
            """, (user_id, f'%{service_name}%'))
            return [row[0] for row in cursor.fetchall()]

    async def update(self, relationship: DocumentRelationship) -> None:
        """Update an existing relationship."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE document_relationships SET
                    relationship_type = ?, access_level = ?, tags = ?, services = ?,
                    last_accessed_at = ?, access_count = ?, notify_on_updates = ?,
                    notify_on_comments = ?, updated_at = ?
                WHERE id = ?
            """, (
                relationship.relationship_type.value,
                relationship.access_level.value,
                json.dumps(relationship.tags),
                json.dumps(relationship.services),
                relationship.last_accessed_at.isoformat(),
                relationship.access_count,
                relationship.notify_on_updates,
                relationship.notify_on_comments,
                relationship.updated_at.isoformat(),
                relationship.id
            ))
            conn.commit()

    async def delete(self, relationship_id: str) -> bool:
        """Delete a relationship."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM document_relationships WHERE id = ?", (relationship_id,))
            conn.commit()
            return cursor.rowcount > 0

    async def delete_by_user_and_document(self, user_id: str, document_id: str) -> bool:
        """Delete relationship between user and document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM document_relationships
                WHERE user_id = ? AND document_id = ?
            """, (user_id, document_id))
            conn.commit()
            return cursor.rowcount > 0

    async def exists(self, user_id: str, document_id: str) -> bool:
        """Check if relationship exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM document_relationships
                WHERE user_id = ? AND document_id = ? LIMIT 1
            """, (user_id, document_id))
            return cursor.fetchone() is not None

    async def count_relationships_by_user(self, user_id: str) -> int:
        """Count relationships for a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM document_relationships WHERE user_id = ?", (user_id,))
            return cursor.fetchone()[0]

    async def count_relationships_by_document(self, document_id: str) -> int:
        """Count relationships for a document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM document_relationships WHERE document_id = ?", (document_id,))
            return cursor.fetchone()[0]
