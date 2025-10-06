"""Package Storage Repository Interface."""

from abc import ABC, abstractmethod
from typing import Optional

from services.mcp_registry.domain.entities.mcp_package import MCPPackage
from services.mcp_registry.domain.value_objects.storage_backend import StorageBackend


class PackageStorageRepository(ABC):
    """
    Repository for MCP package storage.
    
    Handles physical storage and retrieval of MCP packages.
    """
    
    @abstractmethod
    async def store(self, package: MCPPackage, data: bytes) -> str:
        """
        Store package data.
        
        Args:
            package: Package metadata
            data: Package binary data
        
        Returns:
            Storage location (path or URL)
        """
        pass
    
    @abstractmethod
    async def retrieve(self, storage_location: str) -> bytes:
        """
        Retrieve package data.
        
        Args:
            storage_location: Storage location
        
        Returns:
            Package binary data
        
        Raises:
            FileNotFoundError: If package not found
        """
        pass
    
    @abstractmethod
    async def exists(self, storage_location: str) -> bool:
        """
        Check if package exists.
        
        Args:
            storage_location: Storage location
        
        Returns:
            True if package exists
        """
        pass
    
    @abstractmethod
    async def delete(self, storage_location: str) -> bool:
        """
        Delete package.
        
        Args:
            storage_location: Storage location
        
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def get_size(self, storage_location: str) -> Optional[int]:
        """
        Get package size.
        
        Args:
            storage_location: Storage location
        
        Returns:
            Size in bytes, None if not found
        """
        pass
    
    @abstractmethod
    async def verify_checksum(self, storage_location: str, expected_checksum: str) -> bool:
        """
        Verify package checksum.
        
        Args:
            storage_location: Storage location
            expected_checksum: Expected SHA256 checksum
        
        Returns:
            True if checksum matches
        """
        pass
    
    @abstractmethod
    def get_backend(self) -> StorageBackend:
        """
        Get storage backend type.
        
        Returns:
            StorageBackend enum value
        """
        pass

