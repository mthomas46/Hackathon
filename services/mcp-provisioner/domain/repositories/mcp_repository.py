"""MCP Repository Interface - Domain Layer.

This is an abstract interface that defines the contract for
MCP persistence without specifying implementation details.

Implementations will be in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from services.mcp_provisioner.domain.entities.mcp_instance import MCPInstance
from services.mcp_provisioner.domain.value_objects.mcp_state import MCPState


class MCPRepository(ABC):
    """
    Abstract repository interface for MCP instances.
    
    This interface belongs to the domain layer and defines
    what operations are needed without specifying how they
    are implemented (that's infrastructure layer concern).
    """
    
    @abstractmethod
    async def save(self, instance: MCPInstance) -> None:
        """
        Persist an MCP instance.
        
        For new instances, this creates a new record.
        For existing instances, this updates the existing record.
        
        Args:
            instance: MCPInstance to save
        
        Raises:
            RepositoryError: If save operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, mcp_id: str) -> Optional[MCPInstance]:
        """
        Find an MCP instance by ID.
        
        Args:
            mcp_id: Unique MCP identifier
        
        Returns:
            MCPInstance if found, None otherwise
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_all(self) -> List[MCPInstance]:
        """
        Find all MCP instances.
        
        Returns:
            List of all MCPInstances (may be empty)
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_state(self, state: MCPState) -> List[MCPInstance]:
        """
        Find all MCP instances in a specific state.
        
        Args:
            state: State to filter by
        
        Returns:
            List of MCPInstances in the specified state (may be empty)
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_tier(self, tier: int) -> List[MCPInstance]:
        """
        Find all MCP instances for a specific tier.
        
        Args:
            tier: Tier to filter by (0-4)
        
        Returns:
            List of MCPInstances for the tier (may be empty)
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def delete(self, mcp_id: str) -> bool:
        """
        Delete an MCP instance.
        
        Args:
            mcp_id: ID of instance to delete
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            RepositoryError: If delete operation fails
        """
        pass
    
    @abstractmethod
    async def exists(self, mcp_id: str) -> bool:
        """
        Check if an MCP instance exists.
        
        Args:
            mcp_id: ID to check
        
        Returns:
            True if exists, False otherwise
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        Count total number of MCP instances.
        
        Returns:
            Total count of instances
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def count_by_state(self, state: MCPState) -> int:
        """
        Count MCP instances in a specific state.
        
        Args:
            state: State to count
        
        Returns:
            Count of instances in the state
        
        Raises:
            RepositoryError: If query fails
        """
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

