"""Package Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.package import MCPPackage


class PackageRepository(ABC):
    """Abstract repository for MCPPackage entities."""
    
    @abstractmethod
    async def add(self, package: MCPPackage) -> None:
        """Add package."""
        pass
    
    @abstractmethod
    async def get_by_id(self, package_id: str) -> Optional[MCPPackage]:
        """Get package by ID."""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[MCPPackage]:
        """Get package by name."""
        pass
    
    @abstractmethod
    async def get_by_name_and_version(self, name: str, version: str) -> Optional[MCPPackage]:
        """Get package by name and version."""
        pass
    
    @abstractmethod
    async def update(self, package: MCPPackage) -> None:
        """Update package."""
        pass
    
    @abstractmethod
    async def delete(self, package_id: str) -> None:
        """Delete package."""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[MCPPackage]:
        """List all packages."""
        pass
    
    @abstractmethod
    async def find_by_tags(self, tags: List[str]) -> List[MCPPackage]:
        """Find packages by tags."""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: str) -> List[MCPPackage]:
        """Find packages by status."""
        pass
    
    @abstractmethod
    async def search(self, query: str) -> List[MCPPackage]:
        """Search packages."""
        pass

