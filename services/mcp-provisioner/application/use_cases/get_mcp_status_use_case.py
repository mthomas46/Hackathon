"""Get MCP Status Use Case - Application Layer."""

import logging

from services.mcp_provisioner.domain.repositories.mcp_repository import MCPRepository
from services.mcp_provisioner.application.dto.operation_result_dto import OperationResultDTO
from services.mcp_provisioner.application.dto.mcp_status_dto import MCPStatusDTO


logger = logging.getLogger(__name__)


class GetMCPStatusUseCase:
    """Use case for retrieving MCP instance status."""
    
    def __init__(self, repository: MCPRepository):
        self.repository = repository
    
    async def execute(self, mcp_id: str) -> OperationResultDTO:
        """Get status of an MCP instance."""
        try:
            logger.info(f"Getting status for MCP: {mcp_id}")
            
            instance = await self.repository.find_by_id(mcp_id)
            if not instance:
                return OperationResultDTO.failure(
                    message=f"MCP instance not found: {mcp_id}",
                    errors=["Instance does not exist"],
                )
            
            status_dto = MCPStatusDTO.from_entity(instance)
            
            return OperationResultDTO.success(
                message=f"MCP status retrieved: {mcp_id}",
                data=status_dto,
            )
            
        except Exception as e:
            logger.error(f"Error getting MCP status: {e}", exc_info=True)
            return OperationResultDTO.failure(
                message="Failed to get MCP status",
                errors=[str(e)],
            )

