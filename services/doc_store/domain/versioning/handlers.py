"""Versioning handlers for API endpoints.

Handles versioning and history-related HTTP requests.
"""
from typing import Dict, Any, Optional
from ...core.handler import BaseHandler
from .service import VersioningService


class VersioningHandlers(BaseHandler):
    """Handlers for versioning API endpoints."""

    def __init__(self):
        super().__init__(VersioningService())

    async def handle_get_document_versions(self, document_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Handle document version history retrieval."""
        result = self.service.get_document_versions(document_id, limit, offset)

        return await self._handle_request(
            lambda: result,
            operation="get_document_versions",
            document_id=document_id,
            versions_returned=result["total"]
        )

    async def handle_get_document_version(self, document_id: str, version_number: int) -> Dict[str, Any]:
        """Handle specific version retrieval."""
        version = self.service.get_document_version(document_id, version_number)

        if not version:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("Version not found")))

        return await self._handle_request(
            lambda: version.to_dict(),
            operation="get_document_version",
            document_id=document_id,
            version_number=version_number
        )

    async def handle_compare_versions(self, document_id: str, version_a: int, version_b: int) -> Dict[str, Any]:
        """Handle version comparison."""
        comparison = self.service.compare_versions(document_id, version_a, version_b)

        return await self._handle_request(
            lambda: comparison,
            operation="compare_versions",
            document_id=document_id,
            version_a=version_a,
            version_b=version_b
        )

    async def handle_rollback_version(self, document_id: str, version_number: int,
                                     changed_by: Optional[str] = None) -> Dict[str, Any]:
        """Handle version rollback."""
        rolled_back_version = self.service.rollback_to_version(document_id, version_number, changed_by)

        return await self._handle_request(
            lambda: rolled_back_version.to_dict(),
            operation="rollback_version",
            document_id=document_id,
            rolled_back_to=version_number,
            new_version=rolled_back_version.version_number
        )

    async def handle_cleanup_versions(self, document_id: str, keep_versions: int = 10) -> Dict[str, Any]:
        """Handle version cleanup."""
        result = self.service.cleanup_versions(document_id, keep_versions)

        return await self._handle_request(
            lambda: result,
            operation="cleanup_versions",
            document_id=document_id,
            versions_deleted=result["versions_deleted"]
        )

    async def handle_get_version_statistics(self) -> Dict[str, Any]:
        """Handle versioning statistics request."""
        stats = self.service.get_version_statistics()

        return await self._handle_request(
            lambda: stats,
            operation="get_version_statistics"
        )

    async def handle_get_version_changes(self, document_id: str, since_version: int = 1) -> Dict[str, Any]:
        """Handle version changes retrieval."""
        changes = self.service.get_version_changes(document_id, since_version)

        return await self._handle_request(
            lambda: {"changes": changes, "count": len(changes)},
            operation="get_version_changes",
            document_id=document_id,
            since_version=since_version,
            changes_count=len(changes)
        )
