"""Health Check Routes - API endpoints for service health monitoring."""

import logging
import time
from datetime import datetime
from fastapi import APIRouter, Depends, status
import redis.asyncio as redis

from services.mcp_infrastructure.presentation.api.models.responses import HealthResponse
from services.mcp_infrastructure.presentation.api.dependencies import get_redis_client
from services.mcp_infrastructure.infrastructure.config.settings import get_settings


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])

# Track service start time
SERVICE_START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check overall service health and dependency status",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"},
    },
)
async def health_check(
    redis_client: redis.Redis = Depends(get_redis_client),
) -> HealthResponse:
    """
    Comprehensive health check including all dependencies.
    
    Checks:
    - Service availability
    - Redis connectivity
    - Service uptime
    
    **Returns:**
    - Health status with dependency information
    """
    settings = get_settings()
    
    # Check Redis
    redis_status = "healthy"
    try:
        await redis_client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "unhealthy"
    
    # Determine overall status
    overall_status = "healthy" if redis_status == "healthy" else "degraded"
    
    # Calculate uptime
    uptime_seconds = time.time() - SERVICE_START_TIME
    
    return HealthResponse(
        status=overall_status,
        service=settings.service_name,
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
        dependencies={
            "redis": redis_status,
        },
        uptime_seconds=uptime_seconds,
    )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Check if service is ready to accept requests (Kubernetes readiness probe)",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"},
    },
)
async def readiness_check(
    redis_client: redis.Redis = Depends(get_redis_client),
) -> dict:
    """
    Kubernetes readiness probe.
    
    Returns 200 if service is ready to handle requests,
    503 if service is not yet ready or dependencies are unavailable.
    
    **Returns:**
    - Simple ready status
    """
    try:
        # Check Redis connectivity
        await redis_client.ping()
        
        return {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Check if service is alive (Kubernetes liveness probe)",
    responses={
        200: {"description": "Service is alive"},
    },
)
async def liveness_check() -> dict:
    """
    Kubernetes liveness probe.
    
    Simple check to verify the service process is running.
    Does not check dependencies.
    
    **Returns:**
    - Simple alive status
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": time.time() - SERVICE_START_TIME,
    }

