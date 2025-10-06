"""Stop MCP Use Case - Application Layer."""

import logging
from typing import Protocol

from services.mcp_provisioner.domain.entities.mcp_instance import MCPInstance
from services.mcp_provisioner.domain.value_objects.mcp_state import MCPState
from services.mcp_provisioner.domain.repositories.mcp_repository import MCPRepository
from services.mcp_provisioner.application.dto.operation_result_dto import OperationResultDTO
from services.mcp_provisioner.application.dto.mcp_status_dto import MCPStatusDTO


logger = logging.getLogger(__name__)


class DockerService(Protocol):
    """Protocol for Docker service (infrastructure layer)."""
    async def stop_container(self, container_id: str) -> None:
        """Stop a Docker container."""
        ...


class StopMCPUseCase:
    """Use case for stopping an MCP instance."""
    
    def __init__(self, repository: MCPRepository, docker_service: DockerService):
        self.repository = repository
        self.docker_service = docker_service
    
    async def execute(self, mcp_id: str) -> OperationResultDTO:
        """Stop an MCP instance."""
        try:
            logger.info(f"Stopping MCP instance: {mcp_id}")
            
            instance = await self.repository.find_by_id(mcp_id)
            if not instance:
                return OperationResultDTO.failure(
                    message=f"MCP instance not found: {mcp_id}",
                    errors=["Instance does not exist"],
                )
            
            if instance.state == MCPState.COLD:
                logger.info(f"MCP instance already stopped: {mcp_id}")
                status_dto = MCPStatusDTO.from_entity(instance)
                return OperationResultDTO.success(
                    message=f"MCP instance already stopped: {mcp_id}",
                    data=status_dto,
                )
            
            # Update to COOLING state
            instance.update_state(MCPState.COOLING)
            await self.repository.save(instance)
            
            # Stop container if it exists
            if instance.container_id:
                await self.docker_service.stop_container(instance.container_id)
            
            # Update to COLD state
            instance.update_state(MCPState.COLD)
            instance.container_id = None
            instance.ip_address = None
            await self.repository.save(instance)
            
            logger.info(f"Successfully stopped MCP instance: {mcp_id}")
            
            status_dto = MCPStatusDTO.from_entity(instance)
            return OperationResultDTO.success(
                message=f"MCP instance stopped successfully: {mcp_id}",
                data=status_dto,
            )
            
        except Exception as e:
            logger.error(f"Error stopping MCP: {e}", exc_info=True)
            return OperationResultDTO.failure(
                message="Failed to stop MCP instance",
                errors=[str(e)],
            )

