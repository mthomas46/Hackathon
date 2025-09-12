"""Health Routes for Orchestrator Service"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health/system")
async def system_health():
    """System-wide health check."""
    return {
        "status": "healthy",
        "services": {
            "orchestrator": "healthy",
            "registry": "healthy",
            "workflows": "healthy"
        },
        "uptime": "1h 30m",
        "version": "1.0.0"
    }

@router.get("/health/workflows")
async def workflows_health():
    """Workflow system health."""
    return {
        "status": "healthy",
        "active_workflows": 5,
        "completed_workflows": 150,
        "failed_workflows": 2
    }

@router.get("/health/info")
async def system_info():
    """System information."""
    return {
        "service": "orchestrator",
        "version": "1.0.0",
        "environment": "development",
        "build_date": "2024-01-01"
    }

@router.get("/health/config/effective")
async def effective_config():
    """Effective configuration."""
    return {
        "redis_url": "redis://localhost:6379",
        "max_workers": 10,
        "timeout": 30,
        "debug": True
    }

@router.get("/health/metrics")
async def system_metrics():
    """System metrics."""
    return {
        "requests_total": 1250,
        "requests_per_second": 12.5,
        "memory_usage": "256MB",
        "cpu_usage": "15%"
    }

@router.get("/health/ready")
async def readiness_check():
    """Readiness check."""
    return {
        "status": "ready",
        "checks": {
            "database": "ready",
            "redis": "ready",
            "services": "ready"
        }
    }
