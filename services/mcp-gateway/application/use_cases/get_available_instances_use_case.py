"""Get Available Instances Use Case."""

import logging
from typing import List, Optional

from services.mcp_gateway.application.dto.instance_response import InstanceResponse
from services.mcp_gateway.domain.repositories.mcp_registry_repository import MCPRegistryRepository

logger = logging.getLogger(__name__)


class GetAvailableInstancesUseCase:
    """
    Use case for getting all available MCP instances.
    
    This is used for health monitoring and routing decisions.
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
        mcp_id: Optional[str] = None,
        tier: Optional[int] = None
    ) -> List[InstanceResponse]:
        """
        Get available instances, optionally filtered.
        
        Args:
            mcp_id: Optional filter by MCP ID
            tier: Optional filter by tier
        
        Returns:
            List of available instance responses
        
        Raises:
            RepositoryError: If query fails
        """
        try:
            # Query available instances
            instances = await self.registry.find_available(
                mcp_id=mcp_id,
                tier=tier
            )
            
            # Convert to responses
            responses = [
                InstanceResponse.from_entity(instance)
                for instance in instances
            ]
            
            logger.debug(
                f"Found {len(responses)} available instances "
                f"(mcp_id={mcp_id}, tier={tier})"
            )
            
            return responses
            
        except Exception as e:
            logger.error(f"Error getting available instances: {e}", exc_info=True)
            raise

