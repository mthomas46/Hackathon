"""Delete MCP Use Case - Application Layer."""

import logging
from typing import Protocol

from services.mcp_provisioner.domain.value_objects.mcp_state import MCPState
from services.mcp_provisioner.domain.repositories.mcp_repository import MCPRepository
from services.mcp_provisioner.application.dto.operation_result_dto import OperationResultDTO


logger = logging.getLogger(__name__)


class DockerService(Protocol):
    """Protocol for Docker service (infrastructure layer)."""
    async def stop_container(self, container_id: str) -> None:
        """Stop a Docker container."""
        ...
    
    async def remove_container(self, container_id: str) -> None:
        """Remove a Docker container."""
        ...


class DeleteMCPUseCase:
    """Use case for deleting an MCP instance."""
    
    def __init__(self, repository: MCPRepository, docker_service: DockerService):
        self.repository = repository
        self.docker_service = docker_service
    
    async def execute(self, mcp_id: str, force: bool = False) -> OperationResultDTO:
        """
        Delete an MCP instance.
        
        Args:
            mcp_id: ID of MCP to delete
            force: If True, forcefully stop and remove container
        
        Returns:
            OperationResultDTO
        """
        try:
            logger.info(f"Deleting MCP instance: {mcp_id} (force={force})")
            
            instance = await self.repository.find_by_id(mcp_id)
            if not instance:
                return OperationResultDTO.failure(
                    message=f"MCP instance not found: {mcp_id}",
                    errors=["Instance does not exist"],
                )
            
            # Stop and remove container if running
            if instance.container_id and instance.state != MCPState.COLD:
                if force or instance.state in [MCPState.HOT, MCPState.WARMING]:
                    logger.info(f"Stopping container: {instance.container_id}")
                    await self.docker_service.stop_container(instance.container_id)
                
                logger.info(f"Removing container: {instance.container_id}")
                await self.docker_service.remove_container(instance.container_id)
            
            # Delete from repository
            deleted = await self.repository.delete(mcp_id)
            
            if deleted:
                logger.info(f"Successfully deleted MCP instance: {mcp_id}")
                return OperationResultDTO.success(
                    message=f"MCP instance deleted: {mcp_id}",
                )
            else:
                return OperationResultDTO.failure(
                    message=f"Failed to delete MCP instance: {mcp_id}",
                    errors=["Delete operation returned false"],
                )
            
        except Exception as e:
            logger.error(f"Error deleting MCP: {e}", exc_info=True)
            return OperationResultDTO.failure(
                message="Failed to delete MCP instance",
                errors=[str(e)],
            )

