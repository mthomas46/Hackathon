"""Gateway API routes."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from services.mcp_gateway.application.dto.register_instance_request import RegisterInstanceRequest
from services.mcp_gateway.application.dto.route_request import RouteRequest
from services.mcp_gateway.application.use_cases.register_instance_use_case import RegisterInstanceUseCase
from services.mcp_gateway.application.use_cases.deregister_instance_use_case import DeregisterInstanceUseCase
from services.mcp_gateway.application.use_cases.route_request_use_case import RouteRequestUseCase
from services.mcp_gateway.application.use_cases.update_health_use_case import UpdateHealthUseCase
from services.mcp_gateway.application.use_cases.get_available_instances_use_case import GetAvailableInstancesUseCase
from services.mcp_gateway.presentation.api.models.requests import (
    RegisterInstanceRequestModel,
    RouteRequestModel,
    UpdateHealthRequestModel
)
from services.mcp_gateway.presentation.api.models.responses import (
    InstanceResponseModel,
    RoutingResponseModel
)
from services.mcp_gateway.presentation.dependencies import (
    get_register_instance_use_case,
    get_deregister_instance_use_case,
    get_route_request_use_case,
    get_update_health_use_case,
    get_available_instances_use_case
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gateway", tags=["Gateway"])


@router.post(
    "/register",
    response_model=InstanceResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Register MCP Instance",
    description="Register a new MCP instance with the Gateway for routing"
)
async def register_instance(
    request: RegisterInstanceRequestModel,
    use_case: RegisterInstanceUseCase = Depends(get_register_instance_use_case)
) -> InstanceResponseModel:
    """Register a new MCP instance."""
    try:
        # Convert API model to DTO
        dto = RegisterInstanceRequest(
            mcp_id=request.mcp_id,
            host=request.host,
            port=request.port,
            name=request.name,
            tier=request.tier,
            priority=request.priority,
            weight=request.weight,
            max_concurrent_requests=request.max_concurrent_requests,
            health_check_url=request.health_check_url,
            tags=request.tags,
            metadata=request.metadata
        )
        
        # Execute use case
        response = await use_case.execute(dto)
        
        # Convert DTO to API model
        return InstanceResponseModel(**response.to_dict())
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering instance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register instance"
        )


@router.delete(
    "/instances/{instance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deregister MCP Instance",
    description="Remove an MCP instance from routing"
)
async def deregister_instance(
    instance_id: str,
    use_case: DeregisterInstanceUseCase = Depends(get_deregister_instance_use_case)
) -> None:
    """Deregister an MCP instance."""
    try:
        result = await use_case.execute(instance_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instance {instance_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deregistering instance {instance_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deregister instance"
        )


@router.post(
    "/route",
    response_model=RoutingResponseModel,
    summary="Route Request to MCP",
    description="Route a request to an appropriate MCP instance with load balancing"
)
async def route_request(
    request: RouteRequestModel,
    use_case: RouteRequestUseCase = Depends(get_route_request_use_case)
) -> RoutingResponseModel:
    """Route a request to an MCP instance."""
    try:
        # Convert API model to DTO
        dto = RouteRequest(
            mcp_id=request.mcp_id,
            method=request.method,
            path=request.path,
            headers=request.headers,
            body=request.body,
            query_params=request.query_params,
            tier=request.tier,
            session_id=request.session_id,
            timeout_seconds=request.timeout_seconds,
            request_id=request.request_id,
            metadata=request.metadata
        )
        
        # Execute use case
        response = await use_case.execute(dto)
        
        # Convert DTO to API model
        return RoutingResponseModel(**response.to_dict())
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error routing request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to route request"
        )


@router.get(
    "/instances",
    response_model=List[InstanceResponseModel],
    summary="List Available Instances",
    description="Get all available MCP instances, optionally filtered by MCP ID or tier"
)
async def list_instances(
    mcp_id: str = None,
    tier: int = None,
    use_case: GetAvailableInstancesUseCase = Depends(get_available_instances_use_case)
) -> List[InstanceResponseModel]:
    """List available MCP instances."""
    try:
        # Execute use case
        responses = await use_case.execute(mcp_id=mcp_id, tier=tier)
        
        # Convert DTOs to API models
        return [InstanceResponseModel(**r.to_dict()) for r in responses]
        
    except Exception as e:
        logger.error(f"Error listing instances: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list instances"
        )


@router.post(
    "/instances/{instance_id}/health",
    response_model=InstanceResponseModel,
    summary="Update Instance Health",
    description="Manually update the health status of an MCP instance"
)
async def update_instance_health(
    instance_id: str,
    request: UpdateHealthRequestModel,
    use_case: UpdateHealthUseCase = Depends(get_update_health_use_case)
) -> InstanceResponseModel:
    """Update instance health status."""
    try:
        # Execute use case
        response = await use_case.execute(instance_id, request.is_healthy)
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instance {instance_id} not found"
            )
        
        # Convert DTO to API model
        return InstanceResponseModel(**response.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating health for {instance_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update instance health"
        )


@router.post(
    "/instances/{instance_id}/drain",
    response_model=InstanceResponseModel,
    summary="Drain Instance",
    description="Set an instance to draining mode (no new requests, finish existing)"
)
async def drain_instance(
    instance_id: str,
    # For now, drain is just setting health to false
    # A more complete implementation would set status to DRAINING
    use_case: UpdateHealthUseCase = Depends(get_update_health_use_case)
) -> InstanceResponseModel:
    """Drain an instance (graceful shutdown)."""
    try:
        # For simplicity, we just mark as unhealthy
        # A full implementation would set status to DRAINING
        response = await use_case.execute(instance_id, is_healthy=False)
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instance {instance_id} not found"
            )
        
        return InstanceResponseModel(**response.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error draining instance {instance_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to drain instance"
        )

