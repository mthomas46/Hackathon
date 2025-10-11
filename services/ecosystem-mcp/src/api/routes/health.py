"""
Health check endpoints.

Provides service health status and dependency checks.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum

from fastapi import APIRouter, status

from ...storage import get_database
from ...storage.chromadb_client import get_chroma_client
from ...utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"           # All systems operational
    DEGRADED = "degraded"         # Some non-critical systems down
    UNHEALTHY = "unhealthy"       # Critical systems down
    UNAVAILABLE = "unavailable"   # Service can't respond


# Define critical services (must be healthy for service to function)
CRITICAL_SERVICES = ["database", "redis"]


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
    Comprehensive health check with accurate status reporting.
    
    Checks:
    - Service status
    - Database connectivity (CRITICAL)
    - Redis connectivity (CRITICAL)
    - ChromaDB connectivity (optional)
    
    Returns:
        - HEALTHY: All systems operational
        - DEGRADED: Non-critical systems down (e.g., ChromaDB)
        - UNHEALTHY: Critical systems down (database, redis)
    """
    # Check database
    db_healthy = False
    db_error = None
    try:
        db = get_database()
        db_healthy = await db.health_check()
    except Exception as e:
        db_error = str(e)
        logger.error(f"Database health check failed: {e}")
    
    # Check ChromaDB
    chroma_healthy = False
    chroma_error = None
    try:
        chroma = get_chroma_client()
        chroma_healthy = await chroma.health_check()
    except Exception as e:
        chroma_error = str(e)
        logger.warning(f"ChromaDB health check failed: {e}")
    
    # Check Redis
    redis_healthy = False
    redis_error = None
    try:
        redis = get_redis_client()
        redis_healthy = await redis.health_check()
    except Exception as e:
        redis_error = str(e)
        logger.error(f"Redis health check failed: {e}")
    
    # Collect service statuses
    services_info = {
        "database": {"healthy": db_healthy, "critical": True, "error": db_error},
        "chromadb": {"healthy": chroma_healthy, "critical": False, "error": chroma_error},
        "redis": {"healthy": redis_healthy, "critical": True, "error": redis_error},
    }
    
    # Determine overall status
    critical_down = [name for name, info in services_info.items() if info["critical"] and not info["healthy"]]
    non_critical_down = [name for name, info in services_info.items() if not info["critical"] and not info["healthy"]]
    
    if critical_down:
        health_status = HealthStatus.UNHEALTHY
    elif non_critical_down:
        health_status = HealthStatus.DEGRADED
    else:
        health_status = HealthStatus.HEALTHY
    
    # Build response
    response = {
        "status": health_status.value,
        "timestamp": datetime.utcnow().isoformat(),
        "critical_services": CRITICAL_SERVICES,
        "services": {
            name: info["healthy"] for name, info in services_info.items()
        },
        "details": {
            "all_healthy": not (critical_down or non_critical_down),
            "degraded_services": non_critical_down if health_status == HealthStatus.DEGRADED else [],
            "failed_services": critical_down if health_status == HealthStatus.UNHEALTHY else [],
        }
    }
    
    # Add error details if any
    errors = {name: info["error"] for name, info in services_info.items() if info["error"]}
    if errors:
        response["errors"] = errors
    
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

