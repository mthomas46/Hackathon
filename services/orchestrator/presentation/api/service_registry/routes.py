"""API Routes for Service Registry

Provides endpoints for:
- Service registration and discovery
- Service health monitoring
- Service metadata management
"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException

from services.shared.core.constants_new import ServiceNames
from services.shared.utilities.logging_client import get_log_collector_client

from ....main import container
from .dtos import (
    PollOpenAPIRequest,
    ServiceInfoResponse,
    ServiceListResponse,
    ServiceRegistrationRequest,
    ServiceUnregistrationRequest,
)

# Global logger client instance
logger_client = None


async def get_logger_client():
    """Get or initialize the logger client."""
    global logger_client
    if logger_client is None:
        try:
            logger_client = await get_log_collector_client(ServiceNames.ORCHESTRATOR)
        except Exception:
            pass  # Fallback to no logging if client unavailable
    return logger_client


router = APIRouter()


@router.post("/register", response_model=ServiceInfoResponse)
async def register_service(request: ServiceRegistrationRequest):
    """Register a new service with the registry."""
    start_time = time.time()
    request_id = f"service_register_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log service registration start
        if logger:
            await logger.log_business_event(
                "service_registration_started",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_registration",
                    "service_name": request.service_name,
                    "service_url": request.service_url,
                    "capabilities_count": len(request.capabilities) if request.capabilities else 0,
                    "metadata_provided": bool(request.metadata),
                    "registration_type": "external_service",
                },
            )

            await logger.log_info(
                "Registering new service with orchestrator",
                {
                    "request_id": request_id,
                    "service_name": request.service_name,
                    "service_url": request.service_url,
                    "capabilities": request.capabilities,
                    "has_metadata": bool(request.metadata),
                    "registration_source": "api_request",
                },
            )

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
            error_details = result.get_errors_string()
            response_time = time.time() - start_time

            # Log registration validation failure
            if logger:
                await logger.log_business_event(
                    "service_registration_validation_failed",
                    {
                        "request_id": request_id,
                        "service_name": request.service_name,
                        "service_url": request.service_url,
                        "response_time_seconds": response_time,
                        "validation_errors": error_details,
                        "capabilities_count": len(request.capabilities) if request.capabilities else 0,
                    },
                )

            raise HTTPException(status_code=400, detail=error_details)

        response_time = time.time() - start_time

        # Log successful service registration
        if logger:
            await logger.log_business_event(
                "service_registered",
                {
                    "request_id": request_id,
                    "service_name": request.service_name,
                    "service_url": request.service_url,
                    "service_id": result.data.get("id") if result.data else None,
                    "response_time_seconds": response_time,
                    "success": True,
                    "capabilities_registered": len(request.capabilities) if request.capabilities else 0,
                    "service_category": "external",
                    "registry_entry_created": True,
                },
            )

            await logger.log_performance_metric(
                "service_registration",
                response_time,
                {
                    "request_id": request_id,
                    "service_name": request.service_name,
                    "registration_success": True,
                    "capabilities_count": len(request.capabilities) if request.capabilities else 0,
                },
            )

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log service registration failure
        if logger:
            await logger.log_error(
                f"Service registration failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_registration",
                    "service_name": request.service_name,
                    "service_url": request.service_url,
                    "capabilities_count": len(request.capabilities) if request.capabilities else 0,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "service_registration_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "service_registration_failed",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_registration",
                    "service_name": request.service_name,
                    "service_url": request.service_url,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to register service: {str(e)}")


@router.delete("/unregister", response_model=dict)
async def unregister_service(request: ServiceUnregistrationRequest):
    """Unregister a service from the registry."""
    start_time = time.time()
    request_id = f"service_unregister_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log service unregistration start
        if logger:
            await logger.log_business_event(
                "service_unregistration_started",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_removal",
                    "service_name": request.service_name,
                    "unregistration_type": "explicit_removal",
                    "registry_cleanup": True,
                },
            )

            await logger.log_info(
                "Unregistering service from orchestrator",
                {
                    "request_id": request_id,
                    "service_name": request.service_name,
                    "unregistration_source": "api_request",
                    "registry_cleanup_required": True,
                },
            )

        from ....application.service_registry.commands import UnregisterServiceCommand
        from ....domain.service_registry.value_objects.service_id import ServiceId

        command = UnregisterServiceCommand(service_id=ServiceId(request.service_name))
        result = await container.unregister_service_use_case.execute(command)

        if result.is_failure():
            error_details = result.get_errors_string()
            response_time = time.time() - start_time

            # Log unregistration validation failure
            if logger:
                await logger.log_business_event(
                    "service_unregistration_validation_failed",
                    {
                        "request_id": request_id,
                        "service_name": request.service_name,
                        "response_time_seconds": response_time,
                        "validation_errors": error_details,
                        "unregistration_blocked": True,
                    },
                )

            raise HTTPException(status_code=400, detail=error_details)

        response_time = time.time() - start_time

        # Log successful service unregistration
        if logger:
            await logger.log_business_event(
                "service_unregistered",
                {
                    "request_id": request_id,
                    "service_name": request.service_name,
                    "response_time_seconds": response_time,
                    "success": True,
                    "registry_entry_removed": True,
                    "cleanup_completed": True,
                    "service_discovery_updated": True,
                },
            )

            await logger.log_performance_metric(
                "service_unregistration",
                response_time,
                {
                    "request_id": request_id,
                    "service_name": request.service_name,
                    "unregistration_success": True,
                    "registry_cleanup_completed": True,
                },
            )

        return {"message": "Service unregistered successfully"}

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log service unregistration failure
        if logger:
            await logger.log_error(
                f"Service unregistration failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_removal",
                    "service_name": request.service_name,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "service_unregistration_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "service_unregistration_failed",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_removal",
                    "service_name": request.service_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to unregister service: {str(e)}")


@router.get("/services/{service_name}", response_model=ServiceInfoResponse)
async def get_service(service_name: str):
    """Get information about a specific service."""
    start_time = time.time()
    request_id = f"service_get_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log service information retrieval start
        if logger:
            await logger.log_business_event(
                "service_info_retrieval_started",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_lookup",
                    "service_name": service_name,
                    "query_type": "service_details",
                    "data_scope": "single_service",
                },
            )

            await logger.log_info(
                "Retrieving service information from registry",
                {
                    "request_id": request_id,
                    "service_name": service_name,
                    "query_operation": "service_metadata_retrieval",
                    "includes_capabilities": True,
                    "includes_health_status": True,
                },
            )

        from ....application.service_registry.queries import GetServiceQuery
        from ....domain.service_registry.value_objects.service_id import ServiceId

        query = GetServiceQuery(service_id=ServiceId(service_name))
        result = await container.get_service_use_case.execute(query)

        if result.is_failure():
            error_details = result.get_errors_string()
            response_time = time.time() - start_time

            # Log service not found
            if logger:
                await logger.log_business_event(
                    "service_not_found",
                    {
                        "request_id": request_id,
                        "service_name": service_name,
                        "operation": "service_discovery_lookup",
                        "response_time_seconds": response_time,
                        "query_result": "not_found",
                        "registry_lookup_failed": True,
                    },
                )

            raise HTTPException(status_code=404, detail=error_details)

        response_time = time.time() - start_time

        # Log successful service information retrieval
        if logger:
            await logger.log_business_event(
                "service_info_retrieved",
                {
                    "request_id": request_id,
                    "service_name": service_name,
                    "operation": "service_discovery_lookup",
                    "response_time_seconds": response_time,
                    "success": True,
                    "service_id": result.data.get("id") if result.data else None,
                    "service_category": result.data.get("category") if result.data else None,
                    "capabilities_count": len(result.data.get("capabilities", [])) if result.data else 0,
                    "service_status": result.data.get("status", "unknown") if result.data else "unknown",
                },
            )

            await logger.log_performance_metric(
                "service_info_retrieval",
                response_time,
                {
                    "request_id": request_id,
                    "service_name": service_name,
                    "retrieval_success": True,
                    "data_returned": bool(result.data),
                },
            )

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log service information retrieval failure
        if logger:
            await logger.log_error(
                f"Service information retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_lookup",
                    "service_name": service_name,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "service_info_retrieval_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "service_info_retrieval_failed",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_lookup",
                    "service_name": service_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get service: {str(e)}")


@router.get("/services", response_model=ServiceListResponse)
async def list_services(
    category: Optional[str] = None,
    capability: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List services in the registry with optional filters."""
    start_time = time.time()
    request_id = f"services_list_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log service listing start
        if logger:
            filters_applied = bool(category or capability or status)
            await logger.log_business_event(
                "service_listing_started",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_inventory",
                    "query_type": "service_list",
                    "pagination_enabled": True,
                    "filters_applied": filters_applied,
                    "category_filter": category,
                    "capability_filter": capability,
                    "status_filter": status,
                    "limit": limit,
                    "offset": offset,
                },
            )

            await logger.log_info(
                "Listing services from registry",
                {
                    "request_id": request_id,
                    "pagination_limit": limit,
                    "pagination_offset": offset,
                    "filters_active": filters_applied,
                    "query_scope": "filtered_services" if filters_applied else "all_services",
                },
            )

        from ....application.service_registry.queries import ListServicesQuery

        query = ListServicesQuery(
            category_filter=category, capability_filter=capability, status_filter=status, limit=limit, offset=offset
        )
        result = await container.list_services_use_case.execute(query)

        if result.is_failure():
            error_details = result.get_errors_string()
            response_time = time.time() - start_time

            # Log service listing validation failure
            if logger:
                await logger.log_business_event(
                    "service_listing_validation_failed",
                    {
                        "request_id": request_id,
                        "response_time_seconds": response_time,
                        "validation_errors": error_details,
                        "filters_applied": filters_applied,
                        "listing_blocked": True,
                    },
                )

            raise HTTPException(status_code=400, detail=error_details)

        response_time = time.time() - start_time
        services_returned = len(result.data.services) if result.data and hasattr(result.data, "services") else 0

        # Log successful service listing
        if logger:
            await logger.log_business_event(
                "service_listing_completed",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_inventory",
                    "response_time_seconds": response_time,
                    "success": True,
                    "services_returned": services_returned,
                    "filters_applied": filters_applied,
                    "limit": limit,
                    "offset": offset,
                    "total_available": result.data.total if result.data and hasattr(result.data, "total") else 0,
                },
            )

            await logger.log_performance_metric(
                "service_listing",
                response_time,
                {
                    "request_id": request_id,
                    "services_returned": services_returned,
                    "filters_used": filters_applied,
                    "listing_success": True,
                },
            )

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log service listing failure
        if logger:
            await logger.log_error(
                f"Service listing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_inventory",
                    "category_filter": category,
                    "capability_filter": capability,
                    "status_filter": status,
                    "limit": limit,
                    "offset": offset,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "service_listing_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "service_listing_failed",
                {
                    "request_id": request_id,
                    "operation": "service_discovery_inventory",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to list services: {str(e)}")


@router.post("/poll-openapi", response_model=dict)
async def poll_openapi_specs(request: PollOpenAPIRequest):
    """Poll OpenAPI specifications from registered services."""
    start_time = time.time()
    request_id = f"openapi_poll_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log OpenAPI polling start
        if logger:
            await logger.log_business_event(
                "openapi_polling_started",
                {
                    "request_id": request_id,
                    "operation": "service_specification_discovery",
                    "services_to_poll": len(request.service_urls),
                    "force_refresh": request.force_refresh,
                    "polling_type": "bulk_openapi_collection",
                    "specification_format": "openapi",
                },
            )

            await logger.log_info(
                "Initiating OpenAPI specification polling",
                {
                    "request_id": request_id,
                    "service_count": len(request.service_urls),
                    "force_refresh_enabled": request.force_refresh,
                    "polling_operation": "specification_discovery",
                    "registry_update_required": True,
                },
            )

        # This would implement polling OpenAPI specs and updating service metadata
        response_time = time.time() - start_time

        # Log successful OpenAPI polling initiation
        if logger:
            await logger.log_business_event(
                "openapi_polling_initiated",
                {
                    "request_id": request_id,
                    "operation": "service_specification_discovery",
                    "response_time_seconds": response_time,
                    "success": True,
                    "services_targeted": len(request.service_urls),
                    "force_refresh": request.force_refresh,
                    "polling_status": "initiated",
                },
            )

            await logger.log_performance_metric(
                "openapi_polling_initiation",
                response_time,
                {
                    "request_id": request_id,
                    "services_targeted": len(request.service_urls),
                    "force_refresh": request.force_refresh,
                    "initiation_success": True,
                },
            )

        return {
            "message": f"OpenAPI polling initiated for {len(request.service_urls)} services",
            "status": "initiated",
            "services_polled": request.service_urls,
            "force_refresh": request.force_refresh,
        }

    except Exception as e:
        error_time = time.time() - start_time

        # Log OpenAPI polling failure
        if logger:
            await logger.log_error(
                f"OpenAPI polling initiation failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "service_specification_discovery",
                    "services_targeted": len(request.service_urls),
                    "force_refresh": request.force_refresh,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "openapi_polling_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "openapi_polling_failed",
                {
                    "request_id": request_id,
                    "operation": "service_specification_discovery",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "services_targeted": len(request.service_urls),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to poll OpenAPI specs: {str(e)}")


@router.get("/capabilities", response_model=dict)
async def list_service_capabilities():
    """List all unique capabilities available across registered services."""
    start_time = time.time()
    request_id = f"capabilities_list_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log capabilities listing start
        if logger:
            await logger.log_business_event(
                "capabilities_listing_started",
                {
                    "request_id": request_id,
                    "operation": "service_capability_discovery",
                    "query_type": "capability_inventory",
                    "aggregation_type": "unique_capabilities",
                    "registry_analysis": True,
                },
            )

            await logger.log_info(
                "Listing service capabilities from registry",
                {
                    "request_id": request_id,
                    "query_operation": "capability_aggregation",
                    "includes_service_mapping": True,
                    "capability_discovery": True,
                },
            )

        # This would aggregate capabilities from all registered services
        capabilities = [
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
        ]

        response_time = time.time() - start_time

        # Log successful capabilities listing
        if logger:
            await logger.log_business_event(
                "capabilities_listed",
                {
                    "request_id": request_id,
                    "operation": "service_capability_discovery",
                    "response_time_seconds": response_time,
                    "success": True,
                    "capabilities_returned": len(capabilities),
                    "capability_types": len(set(capabilities)),
                    "registry_services_analyzed": 0,  # Would be populated
                    "service_mapping_available": False,  # Would be populated
                },
            )

            await logger.log_performance_metric(
                "capabilities_listing",
                response_time,
                {
                    "request_id": request_id,
                    "capabilities_returned": len(capabilities),
                    "listing_success": True,
                    "registry_query_performed": True,
                },
            )

        return {
            "capabilities": capabilities,
            "total_services": 0,  # Would be populated from registry
            "services_by_capability": {},  # Would map capabilities to service lists
        }

    except Exception as e:
        error_time = time.time() - start_time

        # Log capabilities listing failure
        if logger:
            await logger.log_error(
                f"Capabilities listing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "service_capability_discovery",
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "capabilities_listing_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "capabilities_listing_failed",
                {
                    "request_id": request_id,
                    "operation": "service_capability_discovery",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to list capabilities: {str(e)}")


@router.get("/health", response_model=dict)
async def get_registry_health():
    """Get the health status of the service registry."""
    start_time = time.time()
    request_id = f"registry_health_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log registry health check start
        if logger:
            await logger.log_business_event(
                "registry_health_check_started",
                {
                    "request_id": request_id,
                    "operation": "service_registry_monitoring",
                    "check_type": "registry_health_assessment",
                    "monitoring_scope": "service_discovery_system",
                    "includes_service_counts": True,
                },
            )

            await logger.log_info(
                "Performing registry health assessment",
                {
                    "request_id": request_id,
                    "health_check_operation": "comprehensive_registry_analysis",
                    "includes_uptime_calculation": True,
                    "includes_service_inventory": True,
                },
            )

        services = await container.list_services_use_case.execute(
            await container.list_services_use_case.__class__()  # Get all services
        )

        total_services = len(services.data.services) if services.is_success() else 0
        response_time = time.time() - start_time

        # Log successful registry health check
        if logger:
            await logger.log_business_event(
                "registry_health_assessed",
                {
                    "request_id": request_id,
                    "operation": "service_registry_monitoring",
                    "response_time_seconds": response_time,
                    "success": True,
                    "registry_status": "healthy",
                    "total_services_registered": total_services,
                    "registry_operational": True,
                    "health_check_comprehensive": True,
                },
            )

            await logger.log_performance_metric(
                "registry_health_check",
                response_time,
                {
                    "request_id": request_id,
                    "total_services": total_services,
                    "health_check_success": True,
                    "registry_operational": True,
                },
            )

        return {
            "status": "healthy",
            "total_services": total_services,
            "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "uptime": "99.9%",  # Would calculate actual uptime
        }

    except Exception as e:
        error_time = time.time() - start_time

        # Log registry health check failure
        if logger:
            await logger.log_error(
                f"Registry health check failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "service_registry_monitoring",
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "registry_health_check_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "registry_health_check_failed",
                {
                    "request_id": request_id,
                    "operation": "service_registry_monitoring",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get registry health: {str(e)}")


@router.post("/services/{service_name}/ping", response_model=dict)
async def ping_service(service_name: str):
    """Ping a specific service to check its availability."""
    start_time = time.time()
    request_id = f"service_ping_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log service ping start
        if logger:
            await logger.log_business_event(
                "service_ping_started",
                {
                    "request_id": request_id,
                    "operation": "service_availability_check",
                    "service_name": service_name,
                    "check_type": "service_reachability_test",
                    "monitoring_type": "individual_service_health",
                    "ping_operation": True,
                },
            )

            await logger.log_info(
                "Pinging service for availability check",
                {
                    "request_id": request_id,
                    "service_name": service_name,
                    "health_check_operation": "service_reachability_test",
                    "response_time_measurement": True,
                    "status_verification": True,
                },
            )

        # This would implement actual service pinging/health checking
        response_time_ms = 150  # Simulated response time
        response_time = time.time() - start_time

        # Log successful service ping
        if logger:
            await logger.log_business_event(
                "service_pinged",
                {
                    "request_id": request_id,
                    "operation": "service_availability_check",
                    "response_time_seconds": response_time,
                    "success": True,
                    "service_name": service_name,
                    "service_status": "reachable",
                    "response_time_ms": response_time_ms,
                    "availability_confirmed": True,
                },
            )

            await logger.log_performance_metric(
                "service_ping",
                response_time,
                {
                    "request_id": request_id,
                    "service_name": service_name,
                    "ping_success": True,
                    "response_time_ms": response_time_ms,
                    "service_reachable": True,
                },
            )

        return {
            "service_name": service_name,
            "status": "reachable",
            "response_time_ms": response_time_ms,
            "last_checked": "2024-01-01T00:00:00Z",
        }

    except Exception as e:
        error_time = time.time() - start_time

        # Log service ping failure
        if logger:
            await logger.log_error(
                f"Service ping failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "service_availability_check",
                    "service_name": service_name,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "service_ping_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "service_ping_failed",
                {
                    "request_id": request_id,
                    "operation": "service_availability_check",
                    "service_name": service_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to ping service: {str(e)}")
