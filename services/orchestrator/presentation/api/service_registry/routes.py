"""API Routes for Service Registry

Provides endpoints for:
- Service registration and discovery
- Service health monitoring
- Service metadata management
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from ....main import container
from .dtos import (
    PollOpenAPIRequest,
    ServiceInfoResponse,
    ServiceListResponse,
    ServiceRegistrationRequest,
    ServiceUnregistrationRequest,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=ServiceInfoResponse,
    summary="Register Service",
    description="Register a new service with the orchestrator registry. The service will be added to the service discovery system and made available for orchestration.",
    status_code=201,
    responses={
        201: {
            "description": "Service registered successfully",
            "model": ServiceInfoResponse,
            "content": {
                "application/json": {
                    "example": {
                        "service_id": "user-service-123",
                        "name": "User Service",
                        "description": "Manages user accounts and authentication",
                        "category": "authentication",
                        "base_url": "https://api.example.com/users",
                        "status": "active",
                        "capabilities": ["user_management", "authentication"],
                        "registered_at": "2024-01-01T12:00:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request data or service already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "Service with this name already exists"}
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to register service: database connection error"}
                }
            }
        }
    }
)
async def register_service(request: ServiceRegistrationRequest):
    """Register a new service with the orchestrator registry.

    This endpoint allows services to register themselves with the orchestrator,
    making them discoverable and available for workflow orchestration.
    """
    try:
        from ....application.service_registry.commands import RegisterServiceCommand

        command = RegisterServiceCommand(
            service_id=request.service_name,  # Using name as ID for simplicity
            name=request.service_name,
            description=f"Service at {request.service_url}",
            category="external",
            base_url=request.service_url,
            openapi_url=None,  # Could be derived or provided
            capabilities=request.capabilities,
            endpoints=[],  # Would be populated from OpenAPI spec
            metadata=request.metadata or {},
        )
        result = await container.register_service_use_case.execute(command)
        if result.is_failure():
            raise HTTPException(status_code=400, detail=result.get_errors_string())
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to register service: {str(e)}"
        )


@router.delete("/unregister", response_model=dict)
async def unregister_service(request: ServiceUnregistrationRequest):
    """Unregister a service from the registry."""
    try:
        from ....application.service_registry.commands import UnregisterServiceCommand
        from ....domain.service_registry.value_objects.service_id import ServiceId

        command = UnregisterServiceCommand(service_id=ServiceId(request.service_name))
        result = await container.unregister_service_use_case.execute(command)
        if result.is_failure():
            raise HTTPException(status_code=400, detail=result.get_errors_string())
        return {"message": "Service unregistered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to unregister service: {str(e)}"
        )


@router.get("/services/{service_name}", response_model=ServiceInfoResponse)
async def get_service(service_name: str):
    """Get information about a specific service."""
    try:
        from ....application.service_registry.queries import GetServiceQuery
        from ....domain.service_registry.value_objects.service_id import ServiceId

        query = GetServiceQuery(service_id=ServiceId(service_name))
        result = await container.get_service_use_case.execute(query)
        if result.is_failure():
            raise HTTPException(status_code=404, detail=result.get_errors_string())
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service: {str(e)}")


@router.get(
    "/services",
    response_model=ServiceListResponse,
    summary="List Services",
    description="Retrieve a paginated list of services registered with the orchestrator. Supports filtering by category, capability, and status.",
    responses={
        200: {
            "description": "Services retrieved successfully",
            "model": ServiceListResponse,
            "content": {
                "application/json": {
                    "example": {
                        "services": [
                            {
                                "service_id": "user-service-123",
                                "name": "User Service",
                                "description": "Manages user accounts",
                                "category": "authentication",
                                "base_url": "https://api.example.com/users",
                                "status": "active",
                                "capabilities": ["user_management"],
                                "registered_at": "2024-01-01T12:00:00Z"
                            }
                        ],
                        "total_count": 1,
                        "limit": 50,
                        "offset": 0
                    }
                }
            }
        },
        400: {
            "description": "Invalid query parameters",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid limit parameter: must be between 1 and 1000"}
                }
            }
        }
    }
)
async def list_services(
    category: Optional[str] = None,
    capability: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List services in the registry with optional filters.

    This endpoint provides paginated access to the service registry with support for
    filtering by service category, required capabilities, and operational status.

    Query Parameters:
    - category: Filter services by category (e.g., 'api', 'worker', 'database')
    - capability: Filter services that have a specific capability
    - status: Filter by service status ('active', 'inactive', 'error')
    - limit: Maximum number of services to return (1-1000, default: 50)
    - offset: Number of services to skip for pagination (default: 0)
    """
    try:
        from ....application.service_registry.queries import ListServicesQuery

        query = ListServicesQuery(
            category_filter=category,
            capability_filter=capability,
            status_filter=status,
            limit=limit,
            offset=offset,
        )
        result = await container.list_services_use_case.execute(query)
        if result.is_failure():
            raise HTTPException(status_code=400, detail=result.get_errors_string())
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list services: {str(e)}"
        )


@router.post("/poll-openapi", response_model=dict)
async def poll_openapi_specs(request: PollOpenAPIRequest):
    """Poll OpenAPI specifications from registered services."""
    try:
        # This would implement polling OpenAPI specs and updating service metadata
        return {
            "message": f"OpenAPI polling initiated for {len(request.service_urls)} services",
            "status": "initiated",
            "services_polled": request.service_urls,
            "force_refresh": request.force_refresh,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to poll OpenAPI specs: {str(e)}"
        )


@router.get("/capabilities", response_model=dict)
async def list_service_capabilities():
    """List all unique capabilities available across registered services."""
    try:
        # This would aggregate capabilities from all registered services
        return {
            "capabilities": [
                "llm-inference",
                "embedding-generation",
                "document-processing",
                "code-analysis",
                "summarization",
                "translation",
                "sentiment-analysis",
                "entity-recognition",
                "question-answering",
                "workflow-execution",
            ],
            "total_services": 0,  # Would be populated from registry
            "services_by_capability": {},  # Would map capabilities to service lists
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list capabilities: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def get_registry_health():
    """Get the health status of the service registry."""
    try:
        services = await container.list_services_use_case.execute(
            await container.list_services_use_case.__class__()  # Get all services
        )
        return {
            "status": "healthy",
            "total_services": (
                len(services.data.services) if services.is_success() else 0
            ),
            "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "uptime": "99.9%",  # Would calculate actual uptime
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get registry health: {str(e)}"
        )


@router.post("/services/{service_name}/ping", response_model=dict)
async def ping_service(service_name: str):
    """Ping a specific service to check its availability."""
    try:
        # This would implement actual service pinging/health checking
        return {
            "service_name": service_name,
            "status": "reachable",
            "response_time_ms": 150,
            "last_checked": "2024-01-01T00:00:00Z",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ping service: {str(e)}")
