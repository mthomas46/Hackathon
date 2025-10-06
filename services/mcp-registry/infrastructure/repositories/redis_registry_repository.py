"""Redis Registry Repository Implementation."""

import json
import logging
from typing import List, Optional

import redis.asyncio as redis

from services.mcp_registry.domain.entities.registry_entry import RegistryEntry
from services.mcp_registry.domain.repositories.registry_repository import RegistryRepository
from services.mcp_registry.domain.value_objects.registry_status import RegistryStatus
from services.mcp_registry.domain.value_objects.mcp_version import MCPVersion

logger = logging.getLogger(__name__)


class RedisRegistryRepository(RegistryRepository):
    """Redis implementation of RegistryRepository."""
    
    def __init__(self, redis_client: redis.Redis, key_prefix: str = "mcp:registry:"):
        self.redis = redis_client
        self.key_prefix = key_prefix
    
    def _entry_key(self, entry_id: str) -> str:
        """Get Redis key for entry."""
        return f"{self.key_prefix}entry:{entry_id}"
    
    def _mcp_index_key(self, mcp_id: str) -> str:
        """Get Redis key for MCP index."""
        return f"{self.key_prefix}mcp:{mcp_id}:versions"
    
    def _status_index_key(self, status: RegistryStatus) -> str:
        """Get Redis key for status index."""
        return f"{self.key_prefix}status:{status.value}"
    
    def _owner_index_key(self, owner_id: str) -> str:
        """Get Redis key for owner index."""
        return f"{self.key_prefix}owner:{owner_id}"
    
    def _public_index_key(self) -> str:
        """Get Redis key for public MCPs index."""
        return f"{self.key_prefix}public"
    
    async def save(self, entry: RegistryEntry) -> None:
        """Save registry entry."""
        entry_key = self._entry_key(entry.entry_id)
        entry_data = json.dumps(entry.to_dict())
        
        # Save entry
        await self.redis.set(entry_key, entry_data)
        
        # Update MCP version index
        mcp_index = self._mcp_index_key(entry.mcp_id)
        await self.redis.zadd(
            mcp_index,
            {entry.entry_id: float(f"{entry.version.major}.{entry.version.minor:02d}{entry.version.patch:02d}")}
        )
        
        # Update status index
        status_index = self._status_index_key(entry.status)
        await self.redis.sadd(status_index, entry.entry_id)
        
        # Update owner index
        owner_index = self._owner_index_key(entry.owner_id)
        await self.redis.sadd(owner_index, entry.entry_id)
        
        # Update public index
        if entry.is_public:
            await self.redis.sadd(self._public_index_key(), entry.entry_id)
        
        logger.debug(f"Saved entry: {entry.entry_id}")
    
    async def get_by_id(self, entry_id: str) -> Optional[RegistryEntry]:
        """Get entry by ID."""
        entry_key = self._entry_key(entry_id)
        data = await self.redis.get(entry_key)
        
        if not data:
            return None
        
        entry_dict = json.loads(data)
        return self._from_dict(entry_dict)
    
    async def get_by_mcp_id(self, mcp_id: str, version: Optional[MCPVersion] = None) -> Optional[RegistryEntry]:
        """Get entry by MCP ID and version."""
        mcp_index = self._mcp_index_key(mcp_id)
        
        if version:
            # Get specific version
            version_score = float(f"{version.major}.{version.minor:02d}{version.patch:02d}")
            entry_ids = await self.redis.zrangebyscore(mcp_index, version_score, version_score)
            if entry_ids:
                return await self.get_by_id(entry_ids[0].decode())
        else:
            # Get latest version
            entry_ids = await self.redis.zrevrange(mcp_index, 0, 0)
            if entry_ids:
                return await self.get_by_id(entry_ids[0].decode())
        
        return None
    
    async def get_latest_version(self, mcp_id: str) -> Optional[RegistryEntry]:
        """Get latest version of an MCP."""
        return await self.get_by_mcp_id(mcp_id, None)
    
    async def list_versions(self, mcp_id: str) -> List[RegistryEntry]:
        """List all versions of an MCP."""
        mcp_index = self._mcp_index_key(mcp_id)
        entry_ids = await self.redis.zrevrange(mcp_index, 0, -1)
        
        entries = []
        for entry_id in entry_ids:
            entry = await self.get_by_id(entry_id.decode())
            if entry:
                entries.append(entry)
        
        return entries
    
    async def list_by_status(self, status: RegistryStatus, limit: Optional[int] = None) -> List[RegistryEntry]:
        """List entries by status."""
        status_index = self._status_index_key(status)
        entry_ids = await self.redis.smembers(status_index)
        
        entries = []
        for entry_id in entry_ids:
            entry = await self.get_by_id(entry_id.decode())
            if entry:
                entries.append(entry)
                if limit and len(entries) >= limit:
                    break
        
        return entries
    
    async def list_by_owner(self, owner_id: str, limit: Optional[int] = None) -> List[RegistryEntry]:
        """List entries by owner."""
        owner_index = self._owner_index_key(owner_id)
        entry_ids = await self.redis.smembers(owner_index)
        
        entries = []
        for entry_id in entry_ids:
            entry = await self.get_by_id(entry_id.decode())
            if entry:
                entries.append(entry)
                if limit and len(entries) >= limit:
                    break
        
        return entries
    
    async def search(
        self,
        query: str,
        tier: Optional[int] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[RegistryEntry]:
        """Search registry entries (simple implementation)."""
        # Simple search: scan all entries and filter
        # In production, use Redis Search or external search engine
        pattern = f"{self.key_prefix}entry:*"
        entries = []
        
        async for key in self.redis.scan_iter(match=pattern):
            entry = await self.get_by_id(key.decode().split(":")[-1])
            if not entry:
                continue
            
            # Filter by query
            query_lower = query.lower()
            if query_lower not in entry.name.lower() and query_lower not in entry.description.lower():
                continue
            
            # Filter by tier
            if tier is not None and entry.manifest.tier != tier:
                continue
            
            # Filter by tags
            if tags:
                if not any(tag in entry.manifest.tags for tag in tags):
                    continue
            
            entries.append(entry)
            if limit and len(entries) >= limit:
                break
        
        return entries
    
    async def delete(self, entry_id: str) -> bool:
        """Delete entry."""
        entry = await self.get_by_id(entry_id)
        if not entry:
            return False
        
        # Remove from indices
        mcp_index = self._mcp_index_key(entry.mcp_id)
        await self.redis.zrem(mcp_index, entry_id)
        
        status_index = self._status_index_key(entry.status)
        await self.redis.srem(status_index, entry_id)
        
        owner_index = self._owner_index_key(entry.owner_id)
        await self.redis.srem(owner_index, entry_id)
        
        if entry.is_public:
            await self.redis.srem(self._public_index_key(), entry_id)
        
        # Delete entry
        entry_key = self._entry_key(entry_id)
        await self.redis.delete(entry_key)
        
        logger.info(f"Deleted entry: {entry_id}")
        return True
    
    async def list_public(self, limit: Optional[int] = None) -> List[RegistryEntry]:
        """List public MCPs."""
        public_index = self._public_index_key()
        entry_ids = await self.redis.smembers(public_index)
        
        entries = []
        for entry_id in entry_ids:
            entry = await self.get_by_id(entry_id.decode())
            if entry:
                entries.append(entry)
                if limit and len(entries) >= limit:
                    break
        
        return entries
    
    async def count_by_status(self, status: RegistryStatus) -> int:
        """Count entries by status."""
        status_index = self._status_index_key(status)
        return await self.redis.scard(status_index)
    
    def _from_dict(self, data: dict) -> RegistryEntry:
        """Convert dict to RegistryEntry (simplified)."""
        # In production, implement full deserialization
        # For now, raise to indicate incomplete implementation
        from services.mcp_registry.domain.entities.mcp_manifest import MCPManifest
        from services.mcp_registry.domain.value_objects.storage_backend import StorageBackend
        from services.mcp_registry.domain.value_objects.export_format import ExportFormat
        from datetime import datetime
        
        manifest = MCPManifest.from_dict(data["manifest"])
        
        return RegistryEntry(
            entry_id=data["entry_id"],
            mcp_id=data["mcp_id"],
            manifest=manifest,
            status=RegistryStatus(data["status"]),
            status_message=data.get("status_message"),
            storage_backend=StorageBackend(data["storage_backend"]),
            storage_location=data["storage_location"],
            export_format=ExportFormat(data["export_format"]),
            registered_at=datetime.fromisoformat(data["registered_at"]),
            last_accessed_at=datetime.fromisoformat(data["last_accessed_at"]) if data.get("last_accessed_at") else None,
            deprecated_at=datetime.fromisoformat(data["deprecated_at"]) if data.get("deprecated_at") else None,
            archived_at=datetime.fromisoformat(data["archived_at"]) if data.get("archived_at") else None,
            is_latest=data["is_latest"],
            previous_version_id=data.get("previous_version_id"),
            next_version_id=data.get("next_version_id"),
            download_count=data["download_count"],
            import_count=data["import_count"],
            access_count=data["access_count"],
            security_scan_status=data["security_scan_status"],
            security_scan_at=datetime.fromisoformat(data["security_scan_at"]) if data.get("security_scan_at") else None,
            security_issues=data["security_issues"],
            integrity_check_status=data["integrity_check_status"],
            integrity_check_at=datetime.fromisoformat(data["integrity_check_at"]) if data.get("integrity_check_at") else None,
            owner_id=data["owner_id"],
            owner_organization=data.get("owner_organization"),
            maintainers=data["maintainers"],
            is_public=data["is_public"],
            allowed_users=data["allowed_users"],
            allowed_organizations=data["allowed_organizations"],
            metadata=data["metadata"],
        )

