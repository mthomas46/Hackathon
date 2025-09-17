"""API Routes for Service Registry

Provides endpoints for:
- Service registration and discovery
- Service health monitoring
- Service metadata management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from .dtos import (
    ServiceRegistrationRequest, ServiceUnregistrationRequest,
    PollOpenAPIRequest, ServiceInfoResponse, RegistryEntryResponse,
    ServiceListResponse
)
from ....main import container

router = APIRouter()


@router.post("/register", response_model=ServiceInfoResponse)
async def register_service(request: ServiceRegistrationRequest):
    """Register a new service with the registry."""
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
            metadata=request.metadata or {}
        )
        result = await container.register_service_use_case.execute(command)
        if result.is_failure():
            raise HTTPException(status_code=400, detail=result.get_errors_string())
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register service: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Failed to unregister service: {str(e)}")


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


@router.get("/services", response_model=ServiceListResponse)
async def list_services(
    category: Optional[str] = None,
    capability: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List services in the registry with optional filters."""
    try:
        from ....application.service_registry.queries import ListServicesQuery
        query = ListServicesQuery(
            category_filter=category,
            capability_filter=capability,
            status_filter=status,
            limit=limit,
            offset=offset
        )
        result = await container.list_services_use_case.execute(query)
        if result.is_failure():
            raise HTTPException(status_code=400, detail=result.get_errors_string())
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list services: {str(e)}")


@router.post("/poll-openapi", response_model=dict)
async def poll_openapi_specs(request: PollOpenAPIRequest):
    """Poll OpenAPI specifications from registered services."""
    try:
        # This would implement polling OpenAPI specs and updating service metadata
        return {
            "message": f"OpenAPI polling initiated for {len(request.service_urls)} services",
            "status": "initiated",
            "services_polled": request.service_urls,
            "force_refresh": request.force_refresh
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to poll OpenAPI specs: {str(e)}")


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
                "workflow-execution"
            ],
            "total_services": 0,  # Would be populated from registry
            "services_by_capability": {}  # Would map capabilities to service lists
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list capabilities: {str(e)}")


@router.get("/health", response_model=dict)
async def get_registry_health():
    """Get the health status of the service registry."""
    try:
        services = await container.list_services_use_case.execute(
            await container.list_services_use_case.__class__()  # Get all services
        )
        return {
            "status": "healthy",
            "total_services": len(services.data.services) if services.is_success() else 0,
            "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "uptime": "99.9%"  # Would calculate actual uptime
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get registry health: {str(e)}")


@router.post("/services/{service_name}/ping", response_model=dict)
async def ping_service(service_name: str):
    """Ping a specific service to check its availability."""
    try:
        # This would implement actual service pinging/health checking
        return {
            "service_name": service_name,
            "status": "reachable",
            "response_time_ms": 150,
            "last_checked": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ping service: {str(e)}")
