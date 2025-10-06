"""List MCPs Use Case - Application Layer."""

import logging
from typing import Optional

from services.mcp_provisioner.domain.value_objects.mcp_state import MCPState
from services.mcp_provisioner.domain.repositories.mcp_repository import MCPRepository
from services.mcp_provisioner.application.dto.operation_result_dto import OperationResultDTO
from services.mcp_provisioner.application.dto.mcp_status_dto import MCPStatusDTO


logger = logging.getLogger(__name__)


class ListMCPsUseCase:
    """Use case for listing MCP instances."""
    
    def __init__(self, repository: MCPRepository):
        self.repository = repository
    
    async def execute(self, state_filter: Optional[MCPState] = None) -> OperationResultDTO:
        """
        List all MCP instances, optionally filtered by state.
        
        Args:
            state_filter: Optional state to filter by
        
        Returns:
            OperationResultDTO with list of MCPStatusDTOs
        """
        try:
            logger.info(f"Listing MCPs (filter: {state_filter})")
            
            if state_filter:
                instances = await self.repository.find_by_state(state_filter)
            else:
                instances = await self.repository.find_all()
            
            status_dtos = [MCPStatusDTO.from_entity(instance) for instance in instances]
            
            return OperationResultDTO.success(
                message=f"Found {len(status_dtos)} MCP instances",
                data=status_dtos,
                count=len(status_dtos),
            )
            
        except Exception as e:
            logger.error(f"Error listing MCPs: {e}", exc_info=True)
            return OperationResultDTO.failure(
                message="Failed to list MCP instances",
                errors=[str(e)],
            )

