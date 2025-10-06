"""MCP instance management routes."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path

from services.mcp_provisioner.presentation.api.models.request_models import (
    ProvisionRequest,
    DeleteRequest,
)
from services.mcp_provisioner.presentation.api.models.response_models import (
    MCPStatusResponse,
    OperationResponse,
    ListMCPsResponse,
)
from services.mcp_provisioner.application.use_cases.provision_mcp_use_case import ProvisionMCPUseCase
from services.mcp_provisioner.application.use_cases.start_mcp_use_case import StartMCPUseCase
from services.mcp_provisioner.application.use_cases.stop_mcp_use_case import StopMCPUseCase
from services.mcp_provisioner.application.use_cases.get_mcp_status_use_case import GetMCPStatusUseCase
from services.mcp_provisioner.application.use_cases.list_mcps_use_case import ListMCPsUseCase
from services.mcp_provisioner.application.use_cases.delete_mcp_use_case import DeleteMCPUseCase
from services.mcp_provisioner.application.dto.provision_request_dto import ProvisionRequestDTO
from services.mcp_provisioner.domain.value_objects.mcp_state import MCPState
from services.mcp_provisioner.presentation.api.dependencies import (
    get_provision_use_case,
    get_start_use_case,
    get_stop_use_case,
    get_get_status_use_case,
    get_list_use_case,
    get_delete_use_case,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcps", tags=["MCP Management"])


@router.post(
    "",
    response_model=OperationResponse,
    status_code=201,
    summary="Provision MCP Instance",
    description="Create and provision a new MCP instance (in COLD state)",
    responses={
        201: {"description": "MCP instance provisioned successfully"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"},
    }
)
async def provision_mcp(
    request: ProvisionRequest,
    use_case: ProvisionMCPUseCase = Depends(get_provision_use_case)
) -> OperationResponse:
    """
    Provision a new MCP instance.
    
    This creates the MCP record but does not start the container.
    Use the start endpoint to actually run the container.
    """
    logger.info(f"Provision request for client: {request.client_id}, tier: {request.tier}")
    
    # Convert to DTO
    provision_dto = ProvisionRequestDTO(
        client_id=request.client_id,
        tier=request.tier,
        image_name=request.image_name,
        memory_limit=request.memory_limit,
        cpu_shares=request.cpu_shares,
        environment_vars=request.environment_vars,
        metadata=request.metadata,
    )
    
    # Execute use case
    result = await use_case.execute(provision_dto)
    
    if not result.is_success():
        logger.warning(f"Provision failed: {result.message}")
        raise HTTPException(status_code=400, detail=result.message)
    
    # Convert status DTO to response model
    status_dto = result.data
    mcp_status = MCPStatusResponse(**status_dto.to_dict())
    
    return OperationResponse(
        status=result.status.value,
        message=result.message,
        data=mcp_status,
        metadata=result.metadata,
    )


@router.post(
    "/{mcp_id}/start",
    response_model=OperationResponse,
    summary="Start MCP Instance",
    description="Start a provisioned MCP instance (COLD → WARMING → HOT)",
    responses={
        200: {"description": "MCP instance started successfully"},
        404: {"description": "MCP instance not found"},
        400: {"description": "Invalid state transition"},
        500: {"description": "Internal server error"},
    }
)
async def start_mcp(
    mcp_id: str = Path(..., description="MCP instance ID"),
    use_case: StartMCPUseCase = Depends(get_start_use_case)
) -> OperationResponse:
    """
    Start an MCP instance.
    
    This starts the Docker container and updates the state to HOT.
    """
    logger.info(f"Start request for MCP: {mcp_id}")
    
    result = await use_case.execute(mcp_id)
    
    if not result.is_success():
        if "not found" in result.message.lower():
            raise HTTPException(status_code=404, detail=result.message)
        raise HTTPException(status_code=400, detail=result.message)
    
    # Convert status DTO to response model
    status_dto = result.data
    mcp_status = MCPStatusResponse(**status_dto.to_dict())
    
    return OperationResponse(
        status=result.status.value,
        message=result.message,
        data=mcp_status,
    )


@router.post(
    "/{mcp_id}/stop",
    response_model=OperationResponse,
    summary="Stop MCP Instance",
    description="Stop a running MCP instance (HOT → COOLING → COLD)",
    responses={
        200: {"description": "MCP instance stopped successfully"},
        404: {"description": "MCP instance not found"},
        500: {"description": "Internal server error"},
    }
)
async def stop_mcp(
    mcp_id: str = Path(..., description="MCP instance ID"),
    use_case: StopMCPUseCase = Depends(get_stop_use_case)
) -> OperationResponse:
    """
    Stop an MCP instance.
    
    This stops the Docker container and updates the state to COLD.
    """
    logger.info(f"Stop request for MCP: {mcp_id}")
    
    result = await use_case.execute(mcp_id)
    
    if not result.is_success():
        if "not found" in result.message.lower():
            raise HTTPException(status_code=404, detail=result.message)
        raise HTTPException(status_code=500, detail=result.message)
    
    # Convert status DTO to response model
    status_dto = result.data
    mcp_status = MCPStatusResponse(**status_dto.to_dict())
    
    return OperationResponse(
        status=result.status.value,
        message=result.message,
        data=mcp_status,
    )


@router.get(
    "/{mcp_id}",
    response_model=MCPStatusResponse,
    summary="Get MCP Status",
    description="Get the current status of an MCP instance",
    responses={
        200: {"description": "MCP status retrieved"},
        404: {"description": "MCP instance not found"},
        500: {"description": "Internal server error"},
    }
)
async def get_mcp_status(
    mcp_id: str = Path(..., description="MCP instance ID"),
    use_case: GetMCPStatusUseCase = Depends(get_get_status_use_case)
) -> MCPStatusResponse:
    """Get the status of an MCP instance."""
    logger.info(f"Status request for MCP: {mcp_id}")
    
    result = await use_case.execute(mcp_id)
    
    if not result.is_success():
        if "not found" in result.message.lower():
            raise HTTPException(status_code=404, detail=result.message)
        raise HTTPException(status_code=500, detail=result.message)
    
    # Convert status DTO to response model
    status_dto = result.data
    return MCPStatusResponse(**status_dto.to_dict())


@router.get(
    "",
    response_model=ListMCPsResponse,
    summary="List MCP Instances",
    description="List all MCP instances, optionally filtered by state",
    responses={
        200: {"description": "MCP instances retrieved"},
        500: {"description": "Internal server error"},
    }
)
async def list_mcps(
    state: Optional[str] = Query(
        None,
        description="Filter by state (cold/warming/hot/cooling/error)"
    ),
    use_case: ListMCPsUseCase = Depends(get_list_use_case)
) -> ListMCPsResponse:
    """List all MCP instances, optionally filtered by state."""
    logger.info(f"List request (state filter: {state})")
    
    # Parse state filter
    state_filter = None
    if state:
        try:
            state_filter = MCPState(state.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid state: {state}. Valid states: cold, warming, hot, cooling, error"
            )
    
    result = await use_case.execute(state_filter)
    
    if not result.is_success():
        raise HTTPException(status_code=500, detail=result.message)
    
    # Convert status DTOs to response models
    status_dtos = result.data
    mcp_statuses = [MCPStatusResponse(**dto.to_dict()) for dto in status_dtos]
    
    return ListMCPsResponse(
        status=result.status.value,
        message=result.message,
        data=mcp_statuses,
        count=len(mcp_statuses),
    )


@router.delete(
    "/{mcp_id}",
    response_model=OperationResponse,
    summary="Delete MCP Instance",
    description="Delete an MCP instance and cleanup resources",
    responses={
        200: {"description": "MCP instance deleted successfully"},
        404: {"description": "MCP instance not found"},
        500: {"description": "Internal server error"},
    }
)
async def delete_mcp(
    mcp_id: str = Path(..., description="MCP instance ID"),
    force: bool = Query(False, description="Force deletion even if running"),
    use_case: DeleteMCPUseCase = Depends(get_delete_use_case)
) -> OperationResponse:
    """
    Delete an MCP instance.
    
    This stops the container (if running), removes it, and deletes the MCP record.
    """
    logger.info(f"Delete request for MCP: {mcp_id} (force={force})")
    
    result = await use_case.execute(mcp_id, force=force)
    
    if not result.is_success():
        if "not found" in result.message.lower():
            raise HTTPException(status_code=404, detail=result.message)
        raise HTTPException(status_code=500, detail=result.message)
    
    return OperationResponse(
        status=result.status.value,
        message=result.message,
    )

