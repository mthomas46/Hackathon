"""Health Monitoring API Routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from .dtos import (
    HealthCheckRequest, SystemHealthResponse, ServiceHealthResponse,
    SystemMetricsResponse, SystemInfoResponse, ReadinessResponse
)

router = APIRouter()


def get_health_container():
    """Dependency injection for health monitoring services."""
    from ....main import container
    return container


@router.get("/system", response_model=SystemHealthResponse)
async def get_system_health(container = Depends(get_health_container)):
    """Get comprehensive system health check."""
    try:
        # Create query
        from ....application.health_monitoring.queries import GetSystemHealthQuery

        query = GetSystemHealthQuery()

        # Execute use case
        result = await container.get_system_health_use_case.execute(query)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.message or "Unknown error")

        # Extract data from DomainResult
        system_health = result.data

        # Convert to response
        return SystemHealthResponse(
            overall_status=system_health.overall_status.value,
            timestamp=system_health.timestamp,
            services={
                health.service_name: {
                    "status": health.status.value,
                    "response_time_ms": health.check_result.response_time_ms if health.check_result else None,
                    "last_check": health.last_check.isoformat(),
                    "error_message": health.check_result.error_message if health.check_result else None
                }
                for health in system_health.service_health
            },
            uptime_seconds=None,  # TODO: Add to SystemHealth domain object
            version=None  # TODO: Add to SystemHealth domain object
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/services/{service_name}", response_model=ServiceHealthResponse)
async def get_service_health(
    service_name: str,
    container = Depends(get_health_container)
):
    """Get health status for a specific service."""
    try:
        # Create query
        from ....application.health_monitoring.queries import GetServiceHealthQuery

        query = GetServiceHealthQuery(service_name=service_name)

        # Execute use case
        result = await container.get_service_health_use_case.execute(query)

        if not result.success:
            if "not found" in result.error_message.lower():
                raise HTTPException(status_code=404, detail=result.error_message)
            raise HTTPException(status_code=500, detail=result.error_message)

        # Convert to response
        return ServiceHealthResponse(
            service_name=result.service_health.service_name,
            status=result.service_health.status.value,
            timestamp=result.service_health.timestamp,
            response_time_ms=result.service_health.response_time_ms,
            version=result.service_health.version,
            details=result.service_health.details
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service health: {str(e)}")


@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(container = Depends(get_health_container)):
    """Get system performance metrics."""
    try:
        # Create query
        from ....application.health_monitoring.queries import GetSystemMetricsQuery

        query = GetSystemMetricsQuery()

        # Execute use case
        result = await container.get_system_metrics_use_case.execute(query)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message)

        # Convert to response
        return SystemMetricsResponse(
            timestamp=result.metrics.timestamp,
            cpu_usage=result.metrics.cpu_usage,
            memory_usage=result.metrics.memory_usage,
            disk_usage=result.metrics.disk_usage,
            active_connections=result.metrics.active_connections,
            request_count=result.metrics.request_count,
            error_count=result.metrics.error_count,
            uptime_seconds=result.metrics.uptime_seconds
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info(container = Depends(get_health_container)):
    """Get system information."""
    try:
        # Create query
        from ....application.health_monitoring.queries import GetSystemInfoQuery

        query = GetSystemInfoQuery()

        # Execute use case
        result = await container.get_system_info_use_case.execute(query)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message)

        # Convert to response
        return SystemInfoResponse(
            hostname=result.system_info.hostname,
            platform=result.system_info.platform,
            python_version=result.system_info.python_version,
            service_version=result.system_info.service_version,
            environment=result.system_info.environment,
            startup_time=result.system_info.startup_time,
            config=result.system_info.config
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")


@router.get("/ready", response_model=ReadinessResponse)
async def check_readiness(container = Depends(get_health_container)):
    """Check if the system is ready to serve requests."""
    try:
        # Create query
        from ....application.health_monitoring.queries import CheckSystemReadinessQuery

        query = CheckSystemReadinessQuery()

        # Execute use case
        result = await container.check_system_readiness_use_case.execute(query)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message)

        # Convert to response
        return ReadinessResponse(
            ready=result.readiness.ready,
            timestamp=result.readiness.timestamp,
            checks={
                check_name: {
                    "status": check_result.status.value,
                    "message": check_result.message,
                    "details": check_result.details
                }
                for check_name, check_result in result.readiness.checks.items()
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check readiness: {str(e)}")


@router.post("/check")
async def perform_health_check(
    request: HealthCheckRequest,
    container = Depends(get_health_container)
):
    """Perform a health check (for manual triggering)."""
    try:
        if request.service_name:
            # Service-specific health check
            from ....application.health_monitoring.commands import CheckServiceHealthCommand

            command = CheckServiceHealthCommand(
                service_name=request.service_name,
                include_details=request.include_details
            )

            result = await container.check_service_health_use_case.execute(command)
        else:
            # System-wide health check
            from ....application.health_monitoring.commands import CheckSystemHealthCommand

            command = CheckSystemHealthCommand(include_details=request.include_details)
            result = await container.check_system_health_use_case.execute(command)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message)

        return {"status": "health_check_completed", "message": "Health check completed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
