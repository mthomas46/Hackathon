"""Get Registry Entry Use Case."""

import logging
from typing import Optional, List

from services.mcp_registry.domain.repositories.registry_repository import RegistryRepository
from services.mcp_registry.application.dto.registry_entry_response import RegistryEntryResponse
from services.mcp_registry.domain.value_objects.mcp_version import MCPVersion

logger = logging.getLogger(__name__)


class GetRegistryEntryUseCase:
    """Use case for getting registry entries."""
    
    def __init__(self, registry_repository: RegistryRepository):
        self.registry_repo = registry_repository
    
    async def get_by_id(self, entry_id: str) -> Optional[RegistryEntryResponse]:
        """Get entry by ID."""
        entry = await self.registry_repo.get_by_id(entry_id)
        if not entry:
            return None
        
        entry.record_access()
        await self.registry_repo.save(entry)
        
        return self._to_response(entry)
    
    async def get_by_mcp_id(self, mcp_id: str, version: Optional[str] = None) -> Optional[RegistryEntryResponse]:
        """Get entry by MCP ID and version."""
        version_obj = MCPVersion.from_string(version) if version else None
        entry = await self.registry_repo.get_by_mcp_id(mcp_id, version_obj)
        
        if not entry:
            return None
        
        entry.record_access()
        await self.registry_repo.save(entry)
        
        return self._to_response(entry)
    
    async def list_versions(self, mcp_id: str) -> List[RegistryEntryResponse]:
        """List all versions of an MCP."""
        entries = await self.registry_repo.list_versions(mcp_id)
        return [self._to_response(e) for e in entries]
    
    async def list_by_owner(self, owner_id: str, limit: Optional[int] = None) -> List[RegistryEntryResponse]:
        """List entries by owner."""
        entries = await self.registry_repo.list_by_owner(owner_id, limit)
        return [self._to_response(e) for e in entries]
    
    async def list_public(self, limit: Optional[int] = None) -> List[RegistryEntryResponse]:
        """List public MCPs."""
        entries = await self.registry_repo.list_public(limit)
        return [self._to_response(e) for e in entries]
    
    def _to_response(self, entry) -> RegistryEntryResponse:
        """Convert RegistryEntry to response DTO."""
        return RegistryEntryResponse(
            entry_id=entry.entry_id,
            mcp_id=entry.mcp_id,
            name=entry.name,
            version=str(entry.version),
            description=entry.description,
            status=entry.status.value,
            status_message=entry.status_message,
            storage_backend=entry.storage_backend.value,
            storage_location=entry.storage_location,
            export_format=entry.export_format.value,
            tier=entry.manifest.tier,
            scope=entry.manifest.scope,
            total_size_bytes=entry.manifest.total_size_bytes,
            has_vector_db=entry.manifest.has_vector_db,
            has_graph_db=entry.manifest.has_graph_db,
            registered_at=entry.registered_at.isoformat(),
            last_accessed_at=entry.last_accessed_at.isoformat() if entry.last_accessed_at else None,
            deprecated_at=entry.deprecated_at.isoformat() if entry.deprecated_at else None,
            archived_at=entry.archived_at.isoformat() if entry.archived_at else None,
            is_latest=entry.is_latest,
            previous_version_id=entry.previous_version_id,
            next_version_id=entry.next_version_id,
            download_count=entry.download_count,
            import_count=entry.import_count,
            access_count=entry.access_count,
            security_scan_status=entry.security_scan_status,
            security_scan_at=entry.security_scan_at.isoformat() if entry.security_scan_at else None,
            security_issues=entry.security_issues,
            integrity_check_status=entry.integrity_check_status,
            integrity_check_at=entry.integrity_check_at.isoformat() if entry.integrity_check_at else None,
            owner_id=entry.owner_id,
            owner_organization=entry.owner_organization,
            maintainers=entry.maintainers,
            is_public=entry.is_public,
            tags=entry.manifest.tags,
            metadata=entry.metadata,
        )

