"""MCP Registry Repository Interface - Domain Layer."""

from abc import ABC, abstractmethod
from typing import List, Optional

from services.mcp_gateway.domain.entities.mcp_instance import MCPInstance
from services.mcp_gateway.domain.value_objects.mcp_instance_status import MCPInstanceStatus


class MCPRegistryRepository(ABC):
    """
    Abstract repository interface for MCP instance registry.
    
    Defines the contract for MCP instance persistence without specifying
    implementation details.
    """
    
    @abstractmethod
    async def register(self, instance: MCPInstance) -> None:
        """
        Register a new MCP instance.
        
        Args:
            instance: MCP instance to register
        
        Raises:
            RepositoryError: If registration fails
        """
        pass
    
    @abstractmethod
    async def deregister(self, instance_id: str) -> bool:
        """
        Deregister an MCP instance.
        
        Args:
            instance_id: Instance ID to deregister
        
        Returns:
            True if deregistered, False if not found
        
        Raises:
            RepositoryError: If deregistration fails
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, instance_id: str) -> Optional[MCPInstance]:
        """
        Find an instance by its ID.
        
        Args:
            instance_id: Instance ID to find
        
        Returns:
            MCP instance if found, None otherwise
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_mcp_id(self, mcp_id: str) -> List[MCPInstance]:
        """
        Find all instances for a specific MCP type.
        
        Args:
            mcp_id: MCP identifier (e.g., "client-acme")
        
        Returns:
            List of matching instances
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_available(
        self,
        mcp_id: Optional[str] = None,
        tier: Optional[int] = None
    ) -> List[MCPInstance]:
        """
        Find all available (routable) instances.
        
        Args:
            mcp_id: Optional filter by MCP ID
            tier: Optional filter by tier
        
        Returns:
            List of available instances
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: MCPInstanceStatus) -> List[MCPInstance]:
        """
        Find instances by status.
        
        Args:
            status: Status to filter by
        
        Returns:
            List of matching instances
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def update(self, instance: MCPInstance) -> None:
        """
        Update an existing instance.
        
        Args:
            instance: Instance with updated data
        
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def find_all(self) -> List[MCPInstance]:
        """
        Get all registered instances.
        
        Returns:
            List of all instances
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def count_by_mcp_id(self, mcp_id: str) -> int:
        """
        Count instances for a specific MCP.
        
        Args:
            mcp_id: MCP identifier
        
        Returns:
            Count of instances
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def cleanup_stale_instances(self, max_age_seconds: int) -> int:
        """
        Remove instances that haven't been seen recently.
        
        Args:
            max_age_seconds: Maximum age before considering stale
        
        Returns:
            Number of instances removed
        
        Raises:
            RepositoryError: If cleanup fails
        """
        pass

