"""List Contexts Use Case - Application Layer."""

import logging
from typing import Optional, List

from services.mcp_infrastructure.domain.repositories.mcp_context_repository import MCPContextRepository
from services.mcp_infrastructure.domain.value_objects.mcp_context_type import MCPContextType
from services.mcp_infrastructure.application.dto.mcp_context_response import MCPContextResponse
from services.mcp_infrastructure.application.dto.operation_result import OperationResult


logger = logging.getLogger(__name__)


class ListContextsUseCase:
    """Use case for listing MCP contexts with filters."""
    
    def __init__(self, repository: MCPContextRepository):
        """Initialize the use case."""
        self.repository = repository
    
    async def execute(
        self,
        mcp_id: Optional[str] = None,
        context_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> OperationResult:
        """
        List MCP contexts with optional filters.
        
        Args:
            mcp_id: Filter by MCP ID (optional)
            context_type: Filter by context type (optional)
            tags: Filter by tags (optional, OR search)
        
        Returns:
            OperationResult with list of MCPContextResponse
        """
        try:
            logger.info(f"Listing contexts (mcp_id={mcp_id}, type={context_type}, tags={tags})")
            
            contexts = []
            
            # Apply filters in priority order
            if mcp_id:
                # Filter by MCP ID (with optional context type)
                type_enum = None
                if context_type:
                    try:
                        type_enum = MCPContextType(context_type)
                    except ValueError:
                        return OperationResult.failure(
                            message=f"Invalid context type: {context_type}",
                            errors=[f"Valid types: {[t.value for t in MCPContextType]}"],
                        )
                
                contexts = await self.repository.find_by_mcp_id(mcp_id, type_enum)
            
            elif context_type:
                # Filter by context type only
                try:
                    type_enum = MCPContextType(context_type)
                    contexts = await self.repository.find_by_type(type_enum)
                except ValueError:
                    return OperationResult.failure(
                        message=f"Invalid context type: {context_type}",
                        errors=[f"Valid types: {[t.value for t in MCPContextType]}"],
                    )
            
            elif tags:
                # Filter by tags
                contexts = await self.repository.find_by_tags(tags)
            
            else:
                # No filters - this could be expensive, consider pagination
                logger.warning("Listing all contexts without filters")
                contexts = []  # Don't return all by default
                return OperationResult.failure(
                    message="Please provide at least one filter (mcp_id, context_type, or tags)",
                    errors=["Unfiltered queries not supported"],
                )
            
            # Convert to response DTOs
            responses = [MCPContextResponse.from_entity(ctx) for ctx in contexts]
            
            return OperationResult.success(
                message=f"Found {len(responses)} context(s)",
                data=responses,
                count=len(responses),
            )
            
        except Exception as e:
            logger.error(f"Error listing contexts: {e}", exc_info=True)
            return OperationResult.failure(
                message="Failed to list contexts",
                errors=[str(e)],
            )

