"""Register Instance Use Case."""

import logging
from typing import Optional

from services.mcp_gateway.application.dto.register_instance_request import RegisterInstanceRequest
from services.mcp_gateway.application.dto.instance_response import InstanceResponse
from services.mcp_gateway.domain.entities.mcp_instance import MCPInstance
from services.mcp_gateway.domain.repositories.mcp_registry_repository import MCPRegistryRepository
from services.mcp_gateway.domain.value_objects.mcp_instance_status import MCPInstanceStatus

logger = logging.getLogger(__name__)


class RegisterInstanceUseCase:
    """
    Use case for registering a new MCP instance with the Gateway.
    
    This makes the instance available for routing.
    """
    
    def __init__(self, registry: MCPRegistryRepository):
        """
        Initialize the use case.
        
        Args:
            registry: Repository for MCP instance storage
        """
        self.registry = registry
    
    async def execute(self, request: RegisterInstanceRequest) -> InstanceResponse:
        """
        Register a new MCP instance.
        
        Args:
            request: Registration request with instance details
        
        Returns:
            Response with registered instance details
        
        Raises:
            ValueError: If validation fails
            RepositoryError: If registration fails
        """
        try:
            # Create MCPInstance entity from request
            instance = MCPInstance(
                mcp_id=request.mcp_id,
                name=request.name or request.mcp_id,
                host=request.host,
                port=request.port,
                tier=request.tier,
                priority=request.priority,
                weight=request.weight,
                max_concurrent_requests=request.max_concurrent_requests,
                health_check_url=request.health_check_url,
                tags=request.tags,
                metadata=request.metadata,
                status=MCPInstanceStatus.UNKNOWN,  # Will be updated by health check
            )
            
            # Register in repository
            await self.registry.register(instance)
            
            logger.info(
                f"Registered MCP instance: {instance.id} "
                f"(mcp_id={instance.mcp_id}, host={instance.host}:{instance.port})"
            )
            
            # Return response
            return InstanceResponse.from_entity(instance)
            
        except ValueError as e:
            logger.warning(f"Validation error registering instance: {e}")
            raise
        except Exception as e:
            logger.error(f"Error registering instance: {e}", exc_info=True)
            raise

