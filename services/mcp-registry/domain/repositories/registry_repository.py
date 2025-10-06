"""Registry Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from services.mcp_registry.domain.entities.registry_entry import RegistryEntry
from services.mcp_registry.domain.value_objects.registry_status import RegistryStatus
from services.mcp_registry.domain.value_objects.mcp_version import MCPVersion


class RegistryRepository(ABC):
    """
    Repository for registry entry persistence.
    
    Manages storage and retrieval of MCP registry entries.
    """
    
    @abstractmethod
    async def save(self, entry: RegistryEntry) -> None:
        """
        Save registry entry.
        
        Args:
            entry: Entry to save
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entry_id: str) -> Optional[RegistryEntry]:
        """
        Get entry by ID.
        
        Args:
            entry_id: Entry ID
        
        Returns:
            RegistryEntry if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_mcp_id(self, mcp_id: str, version: Optional[MCPVersion] = None) -> Optional[RegistryEntry]:
        """
        Get entry by MCP ID and optionally version.
        
        Args:
            mcp_id: MCP ID
            version: Optional version (returns latest if not specified)
        
        Returns:
            RegistryEntry if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_latest_version(self, mcp_id: str) -> Optional[RegistryEntry]:
        """
        Get latest version of an MCP.
        
        Args:
            mcp_id: MCP ID
        
        Returns:
            Latest RegistryEntry if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_versions(self, mcp_id: str) -> List[RegistryEntry]:
        """
        List all versions of an MCP.
        
        Args:
            mcp_id: MCP ID
        
        Returns:
            List of RegistryEntries, sorted by version
        """
        pass
    
    @abstractmethod
    async def list_by_status(self, status: RegistryStatus, limit: Optional[int] = None) -> List[RegistryEntry]:
        """
        List entries by status.
        
        Args:
            status: Status to filter by
            limit: Optional limit
        
        Returns:
            List of RegistryEntries
        """
        pass
    
    @abstractmethod
    async def list_by_owner(self, owner_id: str, limit: Optional[int] = None) -> List[RegistryEntry]:
        """
        List entries by owner.
        
        Args:
            owner_id: Owner ID
            limit: Optional limit
        
        Returns:
            List of RegistryEntries
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        tier: Optional[int] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[RegistryEntry]:
        """
        Search registry entries.
        
        Args:
            query: Search query (searches name, description)
            tier: Optional tier filter
            tags: Optional tag filters
            limit: Optional limit
        
        Returns:
            List of matching RegistryEntries
        """
        pass
    
    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """
        Delete entry.
        
        Args:
            entry_id: Entry ID
        
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def list_public(self, limit: Optional[int] = None) -> List[RegistryEntry]:
        """
        List public MCPs.
        
        Args:
            limit: Optional limit
        
        Returns:
            List of public RegistryEntries
        """
        pass
    
    @abstractmethod
    async def count_by_status(self, status: RegistryStatus) -> int:
        """
        Count entries by status.
        
        Args:
            status: Status to count
        
        Returns:
            Number of entries with status
        """
        pass

