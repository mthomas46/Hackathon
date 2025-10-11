"""
Health check endpoints.

Provides service health status and dependency checks.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from ...storage import get_database
from ...storage.chromadb_client import get_chroma_client
from ...utils.redis_client import get_redis_client
from ...services.models.ollama_client import get_ollama_client

logger = logging.getLogger(__name__)

router = APIRouter()

# Service startup time
_startup_time = datetime.utcnow()


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"           # All systems operational
    DEGRADED = "degraded"         # Some non-critical systems down
    UNHEALTHY = "unhealthy"       # Critical systems down
    UNAVAILABLE = "unavailable"   # Service can't respond


# Define critical services (must be healthy for service to function)
CRITICAL_SERVICES = ["database", "redis"]


class ComponentHealth(BaseModel):
    """Health status for a single component."""
    status: str = Field(..., description="Component status (healthy/degraded/unhealthy)")
    message: Optional[str] = Field(None, description="Status message or error")
    response_time_ms: Optional[float] = Field(None, description="Health check response time")


class HealthResponse(BaseModel):
    """Complete health check response."""
    status: str = Field(..., description="Overall service status")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Health check timestamp (ISO 8601)")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    components: Dict[str, ComponentHealth] = Field(..., description="Individual component health")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "timestamp": "2025-10-11T16:20:00.000Z",
                "uptime_seconds": 3600.5,
                "components": {
                    "database": {
                        "status": "healthy",
                        "message": "Connected",
                        "response_time_ms": 2.5
                    },
                    "redis": {
                        "status": "healthy",
                        "message": "Connected",
                        "response_time_ms": 1.2
                    }
                }
            }
        }


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check service health and dependencies",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def health_check():
    """
    Comprehensive health check with component details.
    
    Checks:
    - Service status
    - Database connectivity (CRITICAL)
    - Redis connectivity (CRITICAL)
    - ChromaDB connectivity (optional)
    - Ollama connectivity (optional)
    
    Returns:
        - HEALTHY: All systems operational
        - DEGRADED: Non-critical systems down (ChromaDB, Ollama)
        - UNHEALTHY: Critical systems down (database, redis)
    """
    import time
    components = {}
    
    # Check database
    start = time.time()
    try:
        db = get_database()
        db_healthy = await db.health_check()
        response_time = (time.time() - start) * 1000
        components["database"] = ComponentHealth(
            status="healthy" if db_healthy else "unhealthy",
            message="Connected" if db_healthy else "Connection failed",
            response_time_ms=round(response_time, 2)
        )
    except Exception as e:
        response_time = (time.time() - start) * 1000
        components["database"] = ComponentHealth(
            status="unhealthy",
            message=str(e),
            response_time_ms=round(response_time, 2)
        )
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis
    start = time.time()
    try:
        redis = get_redis_client()
        redis_healthy = await redis.health_check()
        response_time = (time.time() - start) * 1000
        components["redis"] = ComponentHealth(
            status="healthy" if redis_healthy else "unhealthy",
            message="Connected" if redis_healthy else "Connection failed",
            response_time_ms=round(response_time, 2)
        )
    except Exception as e:
        response_time = (time.time() - start) * 1000
        components["redis"] = ComponentHealth(
            status="unhealthy",
            message=str(e),
            response_time_ms=round(response_time, 2)
        )
        logger.error(f"Redis health check failed: {e}")
    
    # Check ChromaDB (non-critical)
    start = time.time()
    try:
        chroma = get_chroma_client()
        chroma_healthy = await chroma.health_check()
        response_time = (time.time() - start) * 1000
        components["chromadb"] = ComponentHealth(
            status="healthy" if chroma_healthy else "degraded",
            message="Connected" if chroma_healthy else "Connection failed",
            response_time_ms=round(response_time, 2)
        )
    except Exception as e:
        response_time = (time.time() - start) * 1000
        components["chromadb"] = ComponentHealth(
            status="degraded",
            message=str(e),
            response_time_ms=round(response_time, 2)
        )
        logger.warning(f"ChromaDB health check failed: {e}")
    
    # Check Ollama (non-critical)
    start = time.time()
    try:
        ollama = get_ollama_client()
        ollama_healthy = await ollama.is_available()
        response_time = (time.time() - start) * 1000
        components["ollama"] = ComponentHealth(
            status="healthy" if ollama_healthy else "degraded",
            message="Connected" if ollama_healthy else "Not available",
            response_time_ms=round(response_time, 2)
        )
    except Exception as e:
        response_time = (time.time() - start) * 1000
        components["ollama"] = ComponentHealth(
            status="degraded",
            message=str(e),
            response_time_ms=round(response_time, 2)
        )
        logger.warning(f"Ollama health check failed: {e}")
    
    # Determine overall status
    critical_unhealthy = (
        components["database"].status == "unhealthy" or 
        components["redis"].status == "unhealthy"
    )
    non_critical_down = (
        components.get("chromadb", ComponentHealth(status="healthy", message="")).status == "degraded" or
        components.get("ollama", ComponentHealth(status="healthy", message="")).status == "degraded"
    )
    
    if critical_unhealthy:
        overall_status = "unhealthy"
    elif non_critical_down:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    # Calculate uptime
    uptime = (datetime.utcnow() - _startup_time).total_seconds()
    
    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=round(uptime, 2),
        components=components
    )


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

