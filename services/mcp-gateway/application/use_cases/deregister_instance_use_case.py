"""Deregister Instance Use Case."""

import logging

from services.mcp_gateway.domain.repositories.mcp_registry_repository import MCPRegistryRepository

logger = logging.getLogger(__name__)


class DeregisterInstanceUseCase:
    """
    Use case for deregistering an MCP instance.
    
    This removes the instance from routing.
    """
    
    def __init__(self, registry: MCPRegistryRepository):
        """
        Initialize the use case.
        
        Args:
            registry: Repository for MCP instance storage
        """
        self.registry = registry
    
    async def execute(self, instance_id: str) -> bool:
        """
        Deregister an MCP instance.
        
        Args:
            instance_id: ID of instance to deregister
        
        Returns:
            True if deregistered, False if not found
        
        Raises:
            RepositoryError: If deregistration fails
        """
        try:
            result = await self.registry.deregister(instance_id)
            
            if result:
                logger.info(f"Deregistered MCP instance: {instance_id}")
            else:
                logger.warning(f"Instance not found for deregistration: {instance_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error deregistering instance {instance_id}: {e}", exc_info=True)
            raise

