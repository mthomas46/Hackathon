"""Versioning service for business logic operations.

Handles document versioning and history management.
"""
from typing import Dict, Any, List, Optional
from ...core.service import BaseService
from ...core.entities import DocumentVersion
from .repository import VersioningRepository


class VersioningService(BaseService[DocumentVersion]):
    """Service for versioning business logic."""

    def __init__(self):
        super().__init__(VersioningRepository())

    def _validate_entity(self, entity: DocumentVersion) -> None:
        """Validate document version."""
        if not entity.document_id:
            raise ValueError("Document ID is required")

        if entity.version_number <= 0:
            raise ValueError("Version number must be positive")

        if not entity.content:
            raise ValueError("Version content is required")

        if not entity.content_hash:
            raise ValueError("Content hash is required")

    def _create_entity_from_data(self, entity_id: str, data: Dict[str, Any]) -> DocumentVersion:
        """Create document version from data."""
        return DocumentVersion(
            id=entity_id,
            document_id=data['document_id'],
            version_number=data['version_number'],
            content=data['content'],
            content_hash=data['content_hash'],
            metadata=data.get('metadata', {}),
            change_summary=data.get('change_summary', ''),
            changed_by=data.get('changed_by')
        )

    def create_version(self, document_id: str, content: str, content_hash: str,
                      metadata: Optional[Dict[str, Any]] = None,
                      change_summary: Optional[str] = None,
                      changed_by: Optional[str] = None) -> DocumentVersion:
        """Create a new version of a document."""
        # Validate inputs
        if not content:
            raise ValueError("Content cannot be empty")

        if not content_hash:
            raise ValueError("Content hash is required")

        return self.repository.create_version(
            document_id, content, content_hash, metadata, change_summary, changed_by
        )

    def get_document_versions(self, document_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get version history for a document."""
        versions = self.repository.get_versions_for_document(document_id, limit, offset)

        return {
            "document_id": document_id,
            "versions": [v.to_dict() for v in versions],
            "total": len(versions),
            "limit": limit,
            "offset": offset,
            "latest_version": max((v.version_number for v in versions), default=0)
        }

    def get_document_version(self, document_id: str, version_number: int) -> Optional[DocumentVersion]:
        """Get a specific version of a document."""
        return self.repository.get_version_by_number(document_id, version_number)

    def compare_versions(self, document_id: str, version_a: int, version_b: int) -> Dict[str, Any]:
        """Compare two versions of a document."""
        if version_a == version_b:
            raise ValueError("Cannot compare a version with itself")

        return self.repository.compare_versions(document_id, version_a, version_b)

    def rollback_to_version(self, document_id: str, version_number: int,
                           changed_by: Optional[str] = None) -> DocumentVersion:
        """Rollback a document to a previous version."""
        # Get the target version
        target_version = self.repository.get_version_by_number(document_id, version_number)
        if not target_version:
            raise ValueError(f"Version {version_number} not found for document {document_id}")

        # Update the current document (this would be handled by document service)
        # For now, just create a new version that represents the rollback
        rollback_version = self.create_version(
            document_id=document_id,
            content=target_version.content,
            content_hash=target_version.content_hash,
            metadata=target_version.metadata,
            change_summary=f"Rolled back to version {version_number}",
            changed_by=changed_by
        )

        return rollback_version

    def cleanup_versions(self, document_id: str, keep_versions: int = 10) -> Dict[str, Any]:
        """Clean up old versions for a document."""
        if keep_versions < 1:
            raise ValueError("Must keep at least 1 version")

        # Check how many versions exist
        versions = self.repository.get_versions_for_document(document_id, limit=1000)
        total_versions = len(versions)

        if total_versions <= keep_versions:
            return {
                "document_id": document_id,
                "message": f"Document has {total_versions} versions, no cleanup needed",
                "versions_deleted": 0
            }

        # Perform cleanup
        deleted_count = self.repository.cleanup_old_versions(document_id, keep_versions)

        return {
            "document_id": document_id,
            "versions_before": total_versions,
            "versions_after": total_versions - deleted_count,
            "versions_deleted": deleted_count,
            "versions_kept": keep_versions
        }

    def get_version_statistics(self) -> Dict[str, Any]:
        """Get comprehensive versioning statistics."""
        return self.repository.get_version_stats()

    def get_version_changes(self, document_id: str, since_version: int = 1) -> List[Dict[str, Any]]:
        """Get changes between versions."""
        versions = self.repository.get_versions_for_document(document_id, limit=100)
        versions_dict = {v.version_number: v for v in versions}

        changes = []
        for version_num in sorted(versions_dict.keys()):
            if version_num >= since_version:
                version = versions_dict[version_num]
                changes.append({
                    "version": version_num,
                    "change_summary": version.change_summary,
                    "changed_by": version.changed_by,
                    "created_at": version.created_at.isoformat(),
                    "content_length": len(version.content),
                    "metadata_keys": list(version.metadata.keys())
                })

        return changes
