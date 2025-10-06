"""Delete Context Use Case - Application Layer."""

import logging

from services.mcp_infrastructure.domain.repositories.mcp_context_repository import MCPContextRepository
from services.mcp_infrastructure.application.dto.operation_result import OperationResult


logger = logging.getLogger(__name__)


class DeleteContextUseCase:
    """Use case for deleting MCP context."""
    
    def __init__(self, repository: MCPContextRepository):
        """Initialize the use case."""
        self.repository = repository
    
    async def execute(
        self,
        context_id: Optional[str] = None,
        mcp_id: Optional[str] = None,
        delete_expired: bool = False,
    ) -> OperationResult:
        """
        Delete MCP context(s).
        
        Args:
            context_id: Delete specific context by ID
            mcp_id: Delete all contexts for an MCP
            delete_expired: Delete all expired contexts
        
        Returns:
            OperationResult
        """
        try:
            if context_id:
                # Delete single context
                logger.info(f"Deleting context: {context_id}")
                deleted = await self.repository.delete(context_id)
                
                if deleted:
                    return OperationResult.success(
                        message=f"Context deleted: {context_id}",
                    )
                else:
                    return OperationResult.failure(
                        message=f"Context not found: {context_id}",
                        errors=["Context does not exist"],
                    )
            
            elif mcp_id:
                # Delete all contexts for MCP
                logger.info(f"Deleting all contexts for MCP: {mcp_id}")
                count = await self.repository.delete_by_mcp_id(mcp_id)
                
                return OperationResult.success(
                    message=f"Deleted {count} context(s) for MCP: {mcp_id}",
                    count=count,
                )
            
            elif delete_expired:
                # Delete all expired contexts
                logger.info("Deleting all expired contexts")
                count = await self.repository.delete_expired()
                
                return OperationResult.success(
                    message=f"Deleted {count} expired context(s)",
                    count=count,
                )
            
            else:
                return OperationResult.failure(
                    message="Please provide context_id, mcp_id, or set delete_expired=True",
                    errors=["No deletion criteria specified"],
                )
            
        except Exception as e:
            logger.error(f"Error deleting context: {e}", exc_info=True)
            return OperationResult.failure(
                message="Failed to delete context",
                errors=[str(e)],
            )


from typing import Optional  # Add to imports at top

