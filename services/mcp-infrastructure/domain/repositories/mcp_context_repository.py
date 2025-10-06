"""MCP Context Repository Interface - Domain Layer.

Abstract interface for context persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from services.mcp_infrastructure.domain.entities.mcp_context import MCPContext
from services.mcp_infrastructure.domain.value_objects.mcp_context_type import MCPContextType


class MCPContextRepository(ABC):
    """
    Abstract repository interface for MCP contexts.
    
    Defines operations for storing, retrieving, and managing
    MCP operational context without specifying implementation details.
    """
    
    @abstractmethod
    async def save(self, context: MCPContext) -> None:
        """
        Save an MCP context.
        
        Args:
            context: MCPContext to save
        
        Raises:
            RepositoryError: If save operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, context_id: str) -> Optional[MCPContext]:
        """
        Find a context by its ID.
        
        Args:
            context_id: Context ID
        
        Returns:
            MCPContext if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_mcp_id(
        self,
        mcp_id: str,
        context_type: Optional[MCPContextType] = None
    ) -> List[MCPContext]:
        """
        Find all contexts for an MCP instance.
        
        Args:
            mcp_id: MCP instance ID
            context_type: Optional filter by context type
        
        Returns:
            List of MCPContext objects
        """
        pass
    
    @abstractmethod
    async def find_by_type(self, context_type: MCPContextType) -> List[MCPContext]:
        """
        Find all contexts of a specific type.
        
        Args:
            context_type: Type to filter by
        
        Returns:
            List of MCPContext objects
        """
        pass
    
    @abstractmethod
    async def find_by_tags(self, tags: List[str]) -> List[MCPContext]:
        """
        Find contexts by tags (OR search).
        
        Args:
            tags: List of tags to search for
        
        Returns:
            List of MCPContext objects matching any of the tags
        """
        pass
    
    @abstractmethod
    async def delete(self, context_id: str) -> bool:
        """
        Delete a context.
        
        Args:
            context_id: Context ID to delete
        
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def delete_by_mcp_id(self, mcp_id: str) -> int:
        """
        Delete all contexts for an MCP instance.
        
        Args:
            mcp_id: MCP instance ID
        
        Returns:
            Number of contexts deleted
        """
        pass
    
    @abstractmethod
    async def delete_expired(self) -> int:
        """
        Delete all expired contexts.
        
        Returns:
            Number of contexts deleted
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Get total number of contexts."""
        pass
    
    @abstractmethod
    async def count_by_type(self, context_type: MCPContextType) -> int:
        """Get count of contexts by type."""
        pass


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""
    pass


class DuplicateEntityError(RepositoryError):
    """Raised when attempting to create a duplicate entity."""
    pass

