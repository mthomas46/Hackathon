"""
Health check endpoints.

Provides service health status and dependency checks.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, status

from ...storage import get_database
from ...storage.chromadb_client import get_chroma_client
from ...utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Health check",
    description="Check service health and dependencies",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def health_check():
    """
    Comprehensive health check.
    
    Checks:
    - Service status
    - Database connectivity
    - Redis connectivity
    - ChromaDB connectivity
    
    Returns:
        Health status with timestamp and dependency status
    """
    db = get_database()
    chroma = get_chroma_client()
    redis = get_redis_client()
    
    # Check dependencies
    db_healthy = await db.health_check()
    chroma_healthy = await chroma.health_check()
    redis_healthy = await redis.health_check()
    
    # Overall status
    is_healthy = all([db_healthy, chroma_healthy, redis_healthy])
    
    response = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_healthy,
            "chromadb": chroma_healthy,
            "redis": redis_healthy
        }
    }
    
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return response


@router.get(
    "/health/live",
    summary="Liveness probe",
    description="Simple liveness check (service is running)",
    responses={
        200: {"description": "Service is alive"}
    }
)
async def liveness():
    """
    Liveness probe for Kubernetes/Docker.
    
    Returns 200 if service is running.
    """
    return {"status": "alive"}


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Readiness check (service can handle requests)",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"}
    }
)
async def readiness():
    """
    Readiness probe for Kubernetes/Docker.
    
    Returns 200 if service can handle requests.
    """
    # Check critical dependencies
    db = get_database()
    redis = get_redis_client()
    
    db_ready = await db.health_check()
    redis_ready = await redis.health_check()
    
    is_ready = db_ready and redis_ready
    
    if is_ready:
        return {"status": "ready"}
    else:
        return {"status": "not ready", "dependencies": {
            "database": db_ready,
            "redis": redis_ready
        }}

