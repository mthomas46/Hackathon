"""Context Management Routes - REST API endpoints for MCP context operations."""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from services.mcp_infrastructure.presentation.api.models.requests import (
    StoreContextRequest,
)
from services.mcp_infrastructure.presentation.api.models.responses import (
    ContextResponse,
    ContextListResponse,
    OperationResponse,
)
from services.mcp_infrastructure.presentation.api.dependencies import (
    get_store_context_use_case,
    get_retrieve_context_use_case,
    get_list_contexts_use_case,
    get_delete_context_use_case,
)
from services.mcp_infrastructure.application.use_cases.store_context_use_case import StoreContextUseCase
from services.mcp_infrastructure.application.use_cases.retrieve_context_use_case import RetrieveContextUseCase
from services.mcp_infrastructure.application.use_cases.list_contexts_use_case import ListContextsUseCase
from services.mcp_infrastructure.application.use_cases.delete_context_use_case import DeleteContextUseCase
from services.mcp_infrastructure.application.dto.store_context_request import (
    StoreContextRequest as StoreContextDTO,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/context", tags=["Context Management"])


@router.post(
    "",
    response_model=OperationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store MCP Context",
    description="Store or update context for an MCP instance",
    responses={
        201: {"description": "Context stored successfully"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"},
    },
)
async def store_context(
    request: StoreContextRequest,
    use_case: StoreContextUseCase = Depends(get_store_context_use_case),
) -> OperationResponse:
    """
    Store context for an MCP instance.
    
    **Parameters:**
    - **mcp_id**: MCP instance ID (required)
    - **context_type**: Type of context (required)
    - **data**: Context data payload (required)
    - **metadata**: Additional metadata (optional)
    - **ttl**: Time-to-live in seconds (optional)
    - **tags**: Tags for categorization (optional)
    
    **Returns:**
    - Operation result with stored context ID
    """
    logger.info(f"Storing context for MCP: {request.mcp_id}, type: {request.context_type}")
    
    # Convert API model to DTO
    dto = StoreContextDTO(
        mcp_id=request.mcp_id,
        context_type=request.context_type,
        data=request.data,
        metadata=request.metadata,
        ttl=request.ttl,
        tags=request.tags,
    )
    
    # Execute use case
    result = await use_case.execute(dto)
    
    if not result.is_success():
        logger.error(f"Failed to store context: {result.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )
    
    return OperationResponse(
        status=result.status.value,
        message=result.message,
        data=result.data.to_dict() if result.data else None,
        metadata=result.metadata,
    )


@router.get(
    "/{context_id}",
    response_model=ContextResponse,
    summary="Retrieve Context",
    description="Retrieve a specific MCP context by ID",
    responses={
        200: {"description": "Context found"},
        404: {"description": "Context not found"},
        500: {"description": "Internal server error"},
    },
)
async def retrieve_context(
    context_id: str,
    use_case: RetrieveContextUseCase = Depends(get_retrieve_context_use_case),
) -> ContextResponse:
    """
    Retrieve a specific context by its ID.
    
    **Parameters:**
    - **context_id**: Context ID to retrieve
    
    **Returns:**
    - Full context data
    """
    logger.info(f"Retrieving context: {context_id}")
    
    result = await use_case.execute(context_id)
    
    if not result.is_success():
        logger.warning(f"Context not found: {context_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.message,
        )
    
    # Convert DTO to API response
    context_data = result.data.to_dict()
    return ContextResponse(**context_data)


@router.get(
    "",
    response_model=ContextListResponse,
    summary="List Contexts",
    description="List MCP contexts with optional filters",
    responses={
        200: {"description": "Contexts retrieved"},
        400: {"description": "Invalid query parameters"},
        500: {"description": "Internal server error"},
    },
)
async def list_contexts(
    mcp_id: Optional[str] = Query(None, description="Filter by MCP ID"),
    context_type: Optional[str] = Query(None, description="Filter by context type"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    use_case: ListContextsUseCase = Depends(get_list_contexts_use_case),
) -> ContextListResponse:
    """
    List MCP contexts with optional filters.
    
    **Query Parameters:**
    - **mcp_id**: Filter by MCP instance ID
    - **context_type**: Filter by context type
    - **tags**: Filter by tags (comma-separated, OR logic)
    
    At least one filter must be provided.
    
    **Returns:**
    - List of matching contexts
    """
    # Parse tags if provided
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    logger.info(f"Listing contexts (mcp_id={mcp_id}, type={context_type}, tags={tag_list})")
    
    # Validate at least one filter is provided
    if not mcp_id and not context_type and not tag_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one filter (mcp_id, context_type, or tags) must be provided",
        )
    
    result = await use_case.execute(
        mcp_id=mcp_id,
        context_type=context_type,
        tags=tag_list,
    )
    
    if not result.is_success():
        logger.error(f"Failed to list contexts: {result.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )
    
    # Convert DTOs to API responses
    context_responses = [
        ContextResponse(**ctx.to_dict()) for ctx in result.data
    ]
    
    return ContextListResponse(
        contexts=context_responses,
        count=len(context_responses),
        filters_applied={
            "mcp_id": mcp_id,
            "context_type": context_type,
            "tags": tag_list,
        },
    )


@router.delete(
    "/{context_id}",
    response_model=OperationResponse,
    summary="Delete Context",
    description="Delete a specific MCP context by ID",
    responses={
        200: {"description": "Context deleted"},
        404: {"description": "Context not found"},
        500: {"description": "Internal server error"},
    },
)
async def delete_context(
    context_id: str,
    use_case: DeleteContextUseCase = Depends(get_delete_context_use_case),
) -> OperationResponse:
    """
    Delete a specific context by its ID.
    
    **Parameters:**
    - **context_id**: Context ID to delete
    
    **Returns:**
    - Operation result
    """
    logger.info(f"Deleting context: {context_id}")
    
    result = await use_case.execute(context_id=context_id)
    
    if not result.is_success():
        logger.warning(f"Failed to delete context: {result.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.message,
        )
    
    return OperationResponse(
        status=result.status.value,
        message=result.message,
        metadata=result.metadata,
    )


@router.delete(
    "/mcp/{mcp_id}",
    response_model=OperationResponse,
    summary="Delete All Contexts for MCP",
    description="Delete all contexts associated with an MCP instance",
    responses={
        200: {"description": "Contexts deleted"},
        500: {"description": "Internal server error"},
    },
)
async def delete_mcp_contexts(
    mcp_id: str,
    use_case: DeleteContextUseCase = Depends(get_delete_context_use_case),
) -> OperationResponse:
    """
    Delete all contexts for an MCP instance.
    
    **Parameters:**
    - **mcp_id**: MCP instance ID
    
    **Returns:**
    - Operation result with count of deleted contexts
    """
    logger.info(f"Deleting all contexts for MCP: {mcp_id}")
    
    result = await use_case.execute(mcp_id=mcp_id)
    
    if not result.is_success():
        logger.error(f"Failed to delete contexts for MCP: {result.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.message,
        )
    
    return OperationResponse(
        status=result.status.value,
        message=result.message,
        metadata=result.metadata,
    )


@router.post(
    "/cleanup/expired",
    response_model=OperationResponse,
    summary="Delete Expired Contexts",
    description="Delete all expired contexts across all MCPs",
    responses={
        200: {"description": "Expired contexts deleted"},
        500: {"description": "Internal server error"},
    },
)
async def delete_expired_contexts(
    use_case: DeleteContextUseCase = Depends(get_delete_context_use_case),
) -> OperationResponse:
    """
    Delete all expired contexts.
    
    This endpoint performs cleanup of contexts that have passed their TTL.
    
    **Returns:**
    - Operation result with count of deleted contexts
    """
    logger.info("Deleting all expired contexts")
    
    result = await use_case.execute(delete_expired=True)
    
    if not result.is_success():
        logger.error(f"Failed to delete expired contexts: {result.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.message,
        )
    
    return OperationResponse(
        status=result.status.value,
        message=result.message,
        metadata=result.metadata,
    )

