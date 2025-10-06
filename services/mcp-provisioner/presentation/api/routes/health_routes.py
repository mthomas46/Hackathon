"""Health check routes."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends
import redis.asyncio as redis

from services.mcp_provisioner.presentation.api.models.response_models import HealthResponse
from services.mcp_provisioner.presentation.api.dependencies import get_redis_client, get_docker_service
from services.mcp_provisioner.infrastructure.config.settings import Settings, get_settings


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check service health and dependencies status",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"},
    }
)
async def health_check(
    settings: Settings = Depends(get_settings),
    redis_client: redis.Redis = Depends(get_redis_client),
) -> HealthResponse:
    """
    Health check endpoint.
    
    Checks:
    - Service is running
    - Redis connection
    - Docker connection
    """
    dependencies = {}
    
    # Check Redis
    try:
        await redis_client.ping()
        dependencies["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        dependencies["redis"] = "unhealthy"
    
    # Check Docker
    try:
        docker_service = await get_docker_service()
        docker_service.client.ping()
        dependencies["docker"] = "healthy"
    except Exception as e:
        logger.error(f"Docker health check failed: {e}")
        dependencies["docker"] = "unhealthy"
    
    # Overall status
    overall_status = "healthy" if all(
        status == "healthy" for status in dependencies.values()
    ) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        service=settings.service_name,
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
        dependencies=dependencies,
    )


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Check if service is ready to accept requests",
)
async def readiness_check() -> dict:
    """Readiness check for Kubernetes."""
    return {"ready": True}


@router.get(
    "/live",
    summary="Liveness Check",
    description="Check if service is alive",
)
async def liveness_check() -> dict:
    """Liveness check for Kubernetes."""
    return {"alive": True}

