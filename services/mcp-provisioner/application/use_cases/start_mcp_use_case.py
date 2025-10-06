"""Start MCP Use Case - Application Layer.

This use case handles starting a provisioned MCP instance.
"""

import logging
from typing import Protocol

from services.mcp_provisioner.domain.entities.mcp_instance import MCPInstance
from services.mcp_provisioner.domain.value_objects.mcp_state import MCPState
from services.mcp_provisioner.domain.repositories.mcp_repository import MCPRepository, EntityNotFoundError
from services.mcp_provisioner.application.dto.operation_result_dto import OperationResultDTO
from services.mcp_provisioner.application.dto.mcp_status_dto import MCPStatusDTO


logger = logging.getLogger(__name__)


class DockerService(Protocol):
    """Protocol for Docker service (infrastructure layer)."""
    
    async def start_container(self, instance: MCPInstance) -> dict:
        """Start a Docker container for the MCP instance."""
        ...


class StartMCPUseCase:
    """
    Use case for starting an MCP instance.
    
    This use case:
    1. Retrieves the MCP instance from repository
    2. Validates the instance can be started
    3. Delegates to Docker service to start container
    4. Updates instance state to WARMING -> HOT
    5. Persists the updated instance
    """
    
    def __init__(self, repository: MCPRepository, docker_service: DockerService):
        """
        Initialize the use case.
        
        Args:
            repository: MCP repository for persistence
            docker_service: Docker service for container operations
        """
        self.repository = repository
        self.docker_service = docker_service
    
    async def execute(self, mcp_id: str) -> OperationResultDTO:
        """
        Execute the start use case.
        
        Args:
            mcp_id: ID of MCP instance to start
        
        Returns:
            OperationResultDTO with MCPStatusDTO data on success
        """
        try:
            logger.info(f"Starting MCP instance: {mcp_id}")
            
            # Retrieve instance
            instance = await self.repository.find_by_id(mcp_id)
            if not instance:
                logger.warning(f"MCP instance not found: {mcp_id}")
                return OperationResultDTO.failure(
                    message=f"MCP instance not found: {mcp_id}",
                    errors=["Instance does not exist"],
                )
            
            # Validate state
            if instance.state == MCPState.HOT:
                logger.info(f"MCP instance already running: {mcp_id}")
                status_dto = MCPStatusDTO.from_entity(instance)
                return OperationResultDTO.success(
                    message=f"MCP instance already running: {mcp_id}",
                    data=status_dto,
                )
            
            if instance.state not in [MCPState.COLD, MCPState.ERROR]:
                logger.warning(f"MCP instance in invalid state for starting: {instance.state}")
                return OperationResultDTO.failure(
                    message=f"Cannot start MCP in state: {instance.state.value}",
                    errors=[f"Current state: {instance.state.value}"],
                )
            
            # Update to WARMING state
            instance.update_state(MCPState.WARMING)
            await self.repository.save(instance)
            
            # Start container (delegates to infrastructure)
            container_info = await self.docker_service.start_container(instance)
            
            # Update instance with container info
            instance.container_id = container_info.get("container_id")
            instance.ip_address = container_info.get("ip_address")
            instance.external_port = container_info.get("external_port")
            instance.update_state(MCPState.HOT)
            instance.mark_accessed()
            
            # Persist updates
            await self.repository.save(instance)
            
            logger.info(f"Successfully started MCP instance: {mcp_id}")
            
            # Convert to status DTO
            status_dto = MCPStatusDTO.from_entity(instance)
            status_dto.health_status = "healthy"
            
            return OperationResultDTO.success(
                message=f"MCP instance started successfully: {mcp_id}",
                data=status_dto,
            )
            
        except EntityNotFoundError as e:
            logger.error(f"Entity not found: {e}")
            return OperationResultDTO.failure(
                message="MCP instance not found",
                errors=[str(e)],
            )
        
        except Exception as e:
            logger.error(f"Unexpected error starting MCP: {e}", exc_info=True)
            
            # Try to update state to ERROR
            try:
                if instance:
                    instance.update_state(MCPState.ERROR)
                    instance.metadata["error"] = str(e)
                    await self.repository.save(instance)
            except Exception as save_error:
                logger.error(f"Failed to save error state: {save_error}")
            
            return OperationResultDTO.failure(
                message="Failed to start MCP instance",
                errors=[str(e)],
            )

