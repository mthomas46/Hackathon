"""Package Repository Interface - Domain Layer."""

from abc import ABC, abstractmethod
from typing import List, Optional

from services.mcp_store.domain.entities.mcp_package import MCPPackage


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""
    pass


class DuplicateEntityError(RepositoryError):
    """Raised when trying to create a duplicate entity."""
    pass


class PackageRepository(ABC):
    """
    Abstract base class for Package repositories.
    
    Defines the interface for persisting and querying MCP packages.
    """
    
    @abstractmethod
    async def save(self, package: MCPPackage) -> None:
        """
        Save a new package.
        
        Args:
            package: The package to save
            
        Raises:
            DuplicateEntityError: If package already exists
            RepositoryError: If save fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, package_id: str) -> Optional[MCPPackage]:
        """
        Retrieve a package by ID.
        
        Args:
            package_id: The package ID
            
        Returns:
            The package if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[MCPPackage]:
        """
        Retrieve a package by name.
        
        Args:
            name: The package name
            
        Returns:
            The package if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        include_private: bool = False
    ) -> List[MCPPackage]:
        """
        List all packages.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            include_private: Whether to include private packages
            
        Returns:
            List of packages
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[MCPPackage]:
        """
        Search packages by query, tags, and categories.
        
        Args:
            query: Search query string
            tags: Filter by tags
            categories: Filter by categories
            limit: Maximum number of results
            
        Returns:
            List of matching packages
        """
        pass
    
    @abstractmethod
    async def get_by_owner(
        self,
        owner_id: str,
        limit: int = 100
    ) -> List[MCPPackage]:
        """
        Get packages by owner.
        
        Args:
            owner_id: The owner ID
            limit: Maximum number of results
            
        Returns:
            List of packages owned by the user
        """
        pass
    
    @abstractmethod
    async def get_popular(
        self,
        limit: int = 20
    ) -> List[MCPPackage]:
        """
        Get most popular packages.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of popular packages sorted by popularity score
        """
        pass
    
    @abstractmethod
    async def get_recent(
        self,
        limit: int = 20
    ) -> List[MCPPackage]:
        """
        Get recently published packages.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of recent packages sorted by published_at
        """
        pass
    
    @abstractmethod
    async def update(self, package: MCPPackage) -> None:
        """
        Update an existing package.
        
        Args:
            package: The package to update
            
        Raises:
            EntityNotFoundError: If package doesn't exist
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def delete(self, package_id: str) -> None:
        """
        Delete a package.
        
        Args:
            package_id: The package ID
            
        Raises:
            EntityNotFoundError: If package doesn't exist
            RepositoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def exists(self, package_id: str) -> bool:
        """
        Check if a package exists.
        
        Args:
            package_id: The package ID
            
        Returns:
            True if package exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def count(self, include_private: bool = False) -> int:
        """
        Get total number of packages.
        
        Args:
            include_private: Whether to include private packages
            
        Returns:
            The count of packages
        """
        pass
