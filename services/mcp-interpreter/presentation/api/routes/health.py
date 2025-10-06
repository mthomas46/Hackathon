"""Health check routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
import redis.asyncio as redis

from services.mcp_interpreter import __version__
from services.mcp_interpreter.presentation.api.models.responses import HealthResponseModel
from services.mcp_interpreter.presentation.dependencies import get_redis_client, get_settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponseModel,
    summary="Health Check",
    description="Check the health status of the MCP Interpreter service"
)
async def health_check(
    redis_client: redis.Redis = Depends(get_redis_client),
    settings = Depends(get_settings)
) -> HealthResponseModel:
    """Health check endpoint."""
    checks = {}
    overall_status = "healthy"
    
    # Check Redis connectivity
    try:
        await redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"
    
    # Check cache status
    checks["cache"] = "enabled" if settings.cache_enabled else "disabled"
    
    # Check NLP status
    checks["nlp"] = "enabled" if settings.nlp_enabled else "disabled"
    
    return HealthResponseModel(
        status=overall_status,
        service="mcp-interpreter",
        version=__version__,
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks=checks
    )


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Check if the service is ready to accept requests"
)
async def readiness_check(
    redis_client: redis.Redis = Depends(get_redis_client)
) -> dict:
    """Readiness check for Kubernetes."""
    try:
        # Check critical dependencies
        await redis_client.ping()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not ready", "reason": str(e)}


@router.get(
    "/live",
    summary="Liveness Check",
    description="Check if the service is alive"
)
async def liveness_check() -> dict:
    """Liveness check for Kubernetes."""
    return {"status": "alive"}

