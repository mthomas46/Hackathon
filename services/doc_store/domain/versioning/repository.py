"""Versioning repository for data access operations.

Handles document version data and history operations.
"""
import json
from typing import List, Optional, Dict, Any
from ...core.repository import BaseRepository
from ...db.queries import execute_query
from ...core.entities import DocumentVersion


class VersioningRepository(BaseRepository[DocumentVersion]):
    """Repository for versioning data access."""

    def __init__(self):
        super().__init__("document_versions")

    def _row_to_entity(self, row: Dict[str, Any]) -> DocumentVersion:
        """Convert database row to DocumentVersion entity."""
        return DocumentVersion(
            id=row['id'],
            document_id=row['document_id'],
            version_number=row['version_number'],
            content=row['content'],
            content_hash=row['content_hash'],
            metadata=json.loads(row.get('metadata', '{}')),
            change_summary=row.get('change_summary', ''),
            changed_by=row.get('changed_by'),
            created_at=row['created_at'],
            updated_at=row.get('updated_at')
        )

    def _entity_to_row(self, entity: DocumentVersion) -> Dict[str, Any]:
        """Convert DocumentVersion entity to database row."""
        return {
            'id': entity.id,
            'document_id': entity.document_id,
            'version_number': entity.version_number,
            'content': entity.content,
            'content_hash': entity.content_hash,
            'metadata': json.dumps(entity.metadata),
            'change_summary': entity.change_summary,
            'changed_by': entity.changed_by,
            'created_at': entity.created_at.isoformat(),
            'updated_at': entity.updated_at.isoformat() if entity.updated_at else None
        }

    def get_versions_for_document(self, document_id: str, limit: int = 50, offset: int = 0) -> List[DocumentVersion]:
        """Get all versions for a document."""
        rows = execute_query(
            f"SELECT * FROM {self.table_name} WHERE document_id = ? ORDER BY version_number DESC LIMIT ? OFFSET ?",
            (document_id, limit, offset),
            fetch_all=True
        )
        return [self._row_to_entity(row) for row in rows]

    def get_version_by_number(self, document_id: str, version_number: int) -> Optional[DocumentVersion]:
        """Get a specific version of a document."""
        row = execute_query(
            f"SELECT * FROM {self.table_name} WHERE document_id = ? AND version_number = ?",
            (document_id, version_number),
            fetch_one=True
        )
        return self._row_to_entity(row) if row else None

    def get_latest_version_number(self, document_id: str) -> int:
        """Get the latest version number for a document."""
        row = execute_query(
            f"SELECT MAX(version_number) as max_version FROM {self.table_name} WHERE document_id = ?",
            (document_id,),
            fetch_one=True
        )
        return row['max_version'] if row and row['max_version'] else 0

    def create_version(self, document_id: str, content: str, content_hash: str,
                      metadata: Optional[Dict[str, Any]] = None,
                      change_summary: Optional[str] = None,
                      changed_by: Optional[str] = None) -> DocumentVersion:
        """Create a new version of a document."""
        # Get next version number
        next_version = self.get_latest_version_number(document_id) + 1

        # Create version ID
        version_id = f"{document_id}:v{next_version}"

        version = DocumentVersion(
            id=version_id,
            document_id=document_id,
            version_number=next_version,
            content=content,
            content_hash=content_hash,
            metadata=metadata or {},
            change_summary=change_summary or "Document update",
            changed_by=changed_by
        )

        self.save(version)
        return version

    def compare_versions(self, document_id: str, version_a: int, version_b: int) -> Dict[str, Any]:
        """Compare two versions of a document."""
        version_a_obj = self.get_version_by_number(document_id, version_a)
        version_b_obj = self.get_version_by_number(document_id, version_b)

        if not version_a_obj or not version_b_obj:
            raise ValueError("One or both versions not found")

        # Simple content comparison
        content_diff = {
            "version_a_length": len(version_a_obj.content),
            "version_b_length": len(version_b_obj.content),
            "content_changed": version_a_obj.content != version_b_obj.content,
            "hash_changed": version_a_obj.content_hash != version_b_obj.content_hash
        }

        # Metadata comparison
        metadata_diff = {}
        all_keys = set(version_a_obj.metadata.keys()) | set(version_b_obj.metadata.keys())
        for key in all_keys:
            val_a = version_a_obj.metadata.get(key)
            val_b = version_b_obj.metadata.get(key)
            if val_a != val_b:
                metadata_diff[key] = {"from": val_a, "to": val_b}

        return {
            "document_id": document_id,
            "comparison": {
                "version_a": version_a_obj.version_number,
                "version_b": version_b_obj.version_number,
                "created_a": version_a_obj.created_at.isoformat(),
                "created_b": version_b_obj.created_at.isoformat(),
                "changed_by_a": version_a_obj.changed_by,
                "changed_by_b": version_b_obj.changed_by
            },
            "content_diff": content_diff,
            "metadata_diff": metadata_diff,
            "summary_a": version_a_obj.change_summary,
            "summary_b": version_b_obj.change_summary
        }

    def cleanup_old_versions(self, document_id: str, keep_versions: int = 10) -> int:
        """Clean up old versions, keeping only the most recent ones."""
        # Get versions to delete (older than the keep_versions most recent)
        rows = execute_query(
            f"SELECT id FROM {self.table_name} WHERE document_id = ? ORDER BY version_number DESC LIMIT -1 OFFSET ?",
            (document_id, keep_versions),
            fetch_all=True
        )

        deleted_count = 0
        for row in rows:
            self.delete_by_id(row['id'])
            deleted_count += 1

        return deleted_count

    def get_version_stats(self) -> Dict[str, Any]:
        """Get versioning statistics."""
        # Total versions
        total_row = execute_query(f"SELECT COUNT(*) as count FROM {self.table_name}", fetch_one=True)
        total_versions = total_row['count'] if total_row else 0

        # Documents with versions
        docs_row = execute_query(f"SELECT COUNT(DISTINCT document_id) as count FROM {self.table_name}", fetch_one=True)
        documents_versioned = docs_row['count'] if docs_row else 0

        # Average versions per document
        avg_versions = total_versions / documents_versioned if documents_versioned > 0 else 0

        # Version distribution
        dist_rows = execute_query(f"""
            SELECT document_id, COUNT(*) as version_count
            FROM {self.table_name}
            GROUP BY document_id
            ORDER BY version_count DESC
            LIMIT 10
        """, fetch_all=True)

        version_distribution = {row['document_id']: row['version_count'] for row in dist_rows}

        return {
            "total_versions": total_versions,
            "documents_versioned": documents_versioned,
            "average_versions_per_document": avg_versions,
            "most_versioned_documents": version_distribution
        }
