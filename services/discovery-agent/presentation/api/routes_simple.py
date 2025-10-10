"""API Routes for Discovery Agent

Real implementations using domain services.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from .models import BulkDiscoverRequest, DiscoverRequest
from domain.services.service_discovery import (
    discover_service,
    discover_multiple_services,
)
from domain.services.tool_generation import (
    generate_tools_from_service,
    generate_tool_summary,
)

# Create router
router = APIRouter()


def create_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Create standardized success response."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def create_error_response(error: str, message: str, details: Any = None) -> Dict[str, Any]:
    """Create standardized error response."""
    response = {
        "success": False,
        "error": error,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if details:
        response["details"] = details
    return response


@router.post(
    "/discover",
    response_model=Dict[str, Any],
    summary="Discover Single Service",
    description="Discover and analyze a single service by fetching its OpenAPI specification.",
    tags=["discovery"],
)
async def discover_service_endpoint(request: DiscoverRequest) -> Dict[str, Any]:
    """
    Discover a service from its OpenAPI specification.
    
    Fetches the OpenAPI spec, parses endpoints, and returns discovery results.
    """
    try:
        # Call domain service
        result = await discover_service(
            service_name=request.name,
            base_url=request.base_url,
            openapi_url=request.openapi_url,
            openapi_content=request.spec,  # Model uses 'spec' not 'openapi_content'
        )
        
        if result.success:
            return create_success_response(
                data={
                    "service_name": result.service.name,
                    "base_url": result.service.base_url,
                    "version": result.service.version,
                    "description": result.service.description,
                    "endpoints_discovered": result.endpoint_count,
                    "discovery_duration_ms": result.discovery_duration_ms,
                    "endpoints": [
                        {
                            "path": ep.path,
                            "method": ep.method,
                            "summary": ep.summary,
                        }
                        for ep in result.service.endpoints[:10]  # Limit to first 10 for response
                    ],
                    "status": "discovered",
                },
                message=result.summary()
            )
        else:
            return create_error_response(
                error="DiscoveryFailed",
                message=result.error_message or "Failed to discover service",
                details={
                    "service_name": request.name,
                    "base_url": request.base_url,
                    "duration_ms": result.discovery_duration_ms,
                }
            )
    except Exception as e:
        return create_error_response(
            error="InternalError",
            message=f"Discovery failed with error: {str(e)}",
            details={"service_name": request.name}
        )


@router.post(
    "/discover/tools",
    response_model=Dict[str, Any],
    summary="Discover Service and Generate Tools",
    description="Discover service and generate LangGraph tool definitions.",
    tags=["discovery"],
)
async def discover_and_generate_tools(request: DiscoverRequest) -> Dict[str, Any]:
    """
    Discover service and generate LangGraph tools.
    
    First discovers the service, then generates tool definitions from endpoints.
    """
    try:
        # First, discover the service
        result = await discover_service(
            service_name=request.name,
            base_url=request.base_url,
            openapi_url=request.openapi_url,
            openapi_content=request.spec,
        )
        
        if not result.success:
            return create_error_response(
                error="DiscoveryFailed",
                message=result.error_message or "Failed to discover service",
                details={
                    "service_name": request.name,
                    "base_url": request.base_url,
                }
            )
        
        # Generate tools from discovered service
        tools = generate_tools_from_service(result.service)
        summary = generate_tool_summary(tools)
        
        return create_success_response(
            data={
                "service_name": result.service.name,
                "base_url": result.service.base_url,
                "version": result.service.version,
                "endpoints_discovered": result.endpoint_count,
                "tools_generated": summary["total_tools"],
                "discovery_duration_ms": result.discovery_duration_ms,
                "tools": tools[:10],  # Limit to first 10 in response
                "summary": summary,
                "status": "completed",
            },
            message=f"Generated {summary['total_tools']} tools from {result.endpoint_count} endpoints"
        )
        
    except Exception as e:
        return create_error_response(
            error="InternalError",
            message=f"Tool generation failed: {str(e)}",
            details={"service_name": request.name}
        )


@router.get(
    "/services/{service_name}",
    response_model=Dict[str, Any],
    summary="Get Service Information",
    description="Retrieve information about a discovered service.",
    tags=["discovery"],
)
async def get_service(service_name: str) -> Dict[str, Any]:
    """
    Get information about a discovered service.
    
    NOTE: This is a stub implementation.
    """
    return create_success_response(
        data={
            "service_name": service_name,
            "status": "not_found",
            "message": "Service registry is being refactored"
        },
        message="Stub implementation - service registry being refactored"
    )


@router.post(
    "/discover/bulk",
    response_model=Dict[str, Any],
    summary="Bulk Service Discovery",
    description="Discover multiple services concurrently.",
    tags=["discovery"],
)
async def bulk_discover(request: BulkDiscoverRequest) -> Dict[str, Any]:
    """
    Discover multiple services concurrently.
    """
    try:
        services = request.services if hasattr(request, 'services') else []
        
        if not services:
            return create_error_response(
                error="InvalidRequest",
                message="No services provided for discovery"
            )
        
        # Call domain service
        results = await discover_multiple_services(services)
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        return create_success_response(
            data={
                "services_requested": len(services),
                "services_discovered": len(successful),
                "services_failed": len(failed),
                "total_endpoints": sum(r.endpoint_count for r in successful),
                "results": [
                    {
                        "service_name": r.service.name,
                        "success": r.success,
                        "endpoints_discovered": r.endpoint_count,
                        "error_message": r.error_message,
                    }
                    for r in results
                ]
            },
            message=f"Discovered {len(successful)}/{len(services)} services successfully"
        )
    except Exception as e:
        return create_error_response(
            error="InternalError",
            message=f"Bulk discovery failed: {str(e)}"
        )

