"""Health check routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
import redis.asyncio as redis

from services.mcp_orchestrator import __version__
from services.mcp_orchestrator.presentation.api.models.responses import HealthResponseModel
from services.mcp_orchestrator.presentation.dependencies import get_redis_client, get_settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponseModel,
    summary="Health Check",
    description="Check the health status of the MCP Orchestrator service"
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
    
    # Check MCP Gateway (if enabled)
    if settings.mcp_gateway_enabled:
        checks["mcp_gateway"] = "configured"
    else:
        checks["mcp_gateway"] = "disabled"
    
    # Check LLM Gateway (if enabled)
    if settings.llm_gateway_enabled:
        checks["llm_gateway"] = "configured"
    else:
        checks["llm_gateway"] = "disabled"
    
    return HealthResponseModel(
        status=overall_status,
        service="mcp-orchestrator",
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

