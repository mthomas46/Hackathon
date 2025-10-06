"""Retrieve Context Use Case - Application Layer."""

import logging

from services.mcp_infrastructure.domain.repositories.mcp_context_repository import MCPContextRepository
from services.mcp_infrastructure.application.dto.mcp_context_response import MCPContextResponse
from services.mcp_infrastructure.application.dto.operation_result import OperationResult


logger = logging.getLogger(__name__)


class RetrieveContextUseCase:
    """Use case for retrieving a single MCP context by ID."""
    
    def __init__(self, repository: MCPContextRepository):
        """Initialize the use case."""
        self.repository = repository
    
    async def execute(self, context_id: str) -> OperationResult:
        """
        Retrieve an MCP context by ID.
        
        Args:
            context_id: Context ID to retrieve
        
        Returns:
            OperationResult with MCPContextResponse data
        """
        try:
            logger.info(f"Retrieving context: {context_id}")
            
            context = await self.repository.find_by_id(context_id)
            
            if not context:
                return OperationResult.failure(
                    message=f"Context not found: {context_id}",
                    errors=["Context does not exist"],
                )
            
            # Check if expired
            if context.is_expired():
                logger.warning(f"Context {context_id} has expired")
                # Still return it but mark as expired
            
            response = MCPContextResponse.from_entity(context)
            
            return OperationResult.success(
                message=f"Context retrieved: {context_id}",
                data=response,
            )
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}", exc_info=True)
            return OperationResult.failure(
                message="Failed to retrieve context",
                errors=[str(e)],
            )

