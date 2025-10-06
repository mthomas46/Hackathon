"""Interpreter API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from services.mcp_interpreter.application.dto.parse_query_request import ParseQueryRequest
from services.mcp_interpreter.application.use_cases.parse_query_use_case import ParseQueryUseCase
from services.mcp_interpreter.presentation.api.models.requests import ParseQueryRequestModel
from services.mcp_interpreter.presentation.api.models.responses import ParsedQueryResponseModel
from services.mcp_interpreter.presentation.dependencies import get_parse_query_use_case

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interpreter", tags=["Interpreter"])


@router.post(
    "/parse",
    response_model=ParsedQueryResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Parse Natural Language Query",
    description="Parse and interpret a natural language query to extract intent, entities, and MCP requirements"
)
async def parse_query(
    request: ParseQueryRequestModel,
    use_case: ParseQueryUseCase = Depends(get_parse_query_use_case)
) -> ParsedQueryResponseModel:
    """
    Parse a natural language query.
    
    This endpoint:
    1. Analyzes the query text
    2. Extracts entities (teams, projects, clients, etc.)
    3. Classifies the intent (search, analyze, compare, etc.)
    4. Determines which MCP tiers are needed
    5. Calculates confidence scores
    6. Caches the result for future queries
    
    Returns a structured interpretation that can be used by the
    MCP Orchestrator to execute the query.
    """
    try:
        # Convert API model to DTO
        dto = ParseQueryRequest(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            context=request.context,
            use_cache=request.use_cache,
            force_reparse=request.force_reparse,
            include_alternatives=request.include_alternatives,
        )
        
        # Execute use case
        response = await use_case.execute(dto)
        
        # Convert DTO to API model
        return ParsedQueryResponseModel(**response.to_dict())
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error parsing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse query"
        )

