"""Store Context Use Case - Application Layer."""

import logging
from typing import Optional

from services.mcp_infrastructure.domain.entities.mcp_context import MCPContext
from services.mcp_infrastructure.domain.value_objects.mcp_context_type import MCPContextType
from services.mcp_infrastructure.domain.repositories.mcp_context_repository import MCPContextRepository
from services.mcp_infrastructure.application.dto.store_context_request import StoreContextRequest
from services.mcp_infrastructure.application.dto.mcp_context_response import MCPContextResponse
from services.mcp_infrastructure.application.dto.operation_result import OperationResult


logger = logging.getLogger(__name__)


class StoreContextUseCase:
    """
    Use case for storing MCP context.
    
    This use case:
    1. Validates the store request
    2. Creates or updates MCPContext entity
    3. Persists via repository
    4. Returns response DTO
    """
    
    def __init__(self, repository: MCPContextRepository):
        """
        Initialize the use case.
        
        Args:
            repository: MCP context repository
        """
        self.repository = repository
    
    async def execute(self, request: StoreContextRequest) -> OperationResult:
        """
        Execute the store context use case.
        
        Args:
            request: Store context request DTO
        
        Returns:
            OperationResult with MCPContextResponse data on success
        """
        try:
            logger.info(f"Storing context for MCP: {request.mcp_id}, type: {request.context_type}")
            
            # Convert context_type string to enum
            try:
                context_type = MCPContextType(request.context_type)
            except ValueError:
                return OperationResult.failure(
                    message=f"Invalid context type: {request.context_type}",
                    errors=[f"Valid types: {[t.value for t in MCPContextType]}"],
                )
            
            # Determine TTL (use request TTL or default from context type)
            ttl = request.ttl if request.ttl is not None else context_type.default_ttl
            
            # Create MCPContext entity
            context = MCPContext(
                mcp_id=request.mcp_id,
                context_type=context_type,
                data=request.data,
                metadata=request.metadata,
                ttl=ttl,
                tags=request.tags,
            )
            
            # Persist the context
            await self.repository.save(context)
            
            logger.info(f"Successfully stored context: {context.id}")
            
            # Convert to response DTO
            response = MCPContextResponse.from_entity(context)
            
            return OperationResult.success(
                message=f"Context stored successfully: {context.id}",
                data=response,
                context_id=context.id,
            )
            
        except ValueError as e:
            logger.error(f"Validation error storing context: {e}")
            return OperationResult.failure(
                message="Validation error",
                errors=[str(e)],
            )
        
        except Exception as e:
            logger.error(f"Unexpected error storing context: {e}", exc_info=True)
            return OperationResult.failure(
                message="Failed to store context",
                errors=[str(e)],
            )

