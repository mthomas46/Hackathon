"""Update Health Use Case."""

import logging
from typing import Optional

from services.mcp_gateway.application.dto.instance_response import InstanceResponse
from services.mcp_gateway.domain.repositories.mcp_registry_repository import MCPRegistryRepository

logger = logging.getLogger(__name__)


class UpdateHealthUseCase:
    """
    Use case for updating an MCP instance's health status.
    
    This is called after health checks to update instance availability.
    """
    
    def __init__(self, registry: MCPRegistryRepository):
        """
        Initialize the use case.
        
        Args:
            registry: Repository for MCP instance storage
        """
        self.registry = registry
    
    async def execute(
        self,
        instance_id: str,
        is_healthy: bool
    ) -> Optional[InstanceResponse]:
        """
        Update instance health status.
        
        Args:
            instance_id: ID of instance to update
            is_healthy: Whether the instance is healthy
        
        Returns:
            Updated instance response, or None if not found
        
        Raises:
            RepositoryError: If update fails
        """
        try:
            # Find the instance
            instance = await self.registry.find_by_id(instance_id)
            
            if not instance:
                logger.warning(f"Instance not found for health update: {instance_id}")
                return None
            
            # Update health status
            instance.update_health(is_healthy)
            
            # Save updated instance
            await self.registry.update(instance)
            
            logger.debug(
                f"Updated health for instance {instance_id}: "
                f"healthy={is_healthy}, status={instance.status}, "
                f"failures={instance.consecutive_failures}"
            )
            
            return InstanceResponse.from_entity(instance)
            
        except Exception as e:
            logger.error(
                f"Error updating health for instance {instance_id}: {e}",
                exc_info=True
            )
            raise

