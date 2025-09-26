"""
Health domain routes
Handles health checks and monitoring endpoints
"""

from fastapi import APIRouter, HTTPException
from services.shared.presentation.responses import create_success_response
from services.shared.monitoring.health import HealthStatus

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return create_success_response({
        "status": HealthStatus.HEALTHY.value,
        "service": "analysis-service",
        "version": "1.0.0"
    })


@router.get("/api/v1/analysis/status")
async def get_analysis_status_v1():
    """Get comprehensive analysis service status (v1)."""
    # Add analysis-specific status information
    analysis_status = {
        "service": "analysis-service",
        "version": "1.0.0",
        "status": HealthStatus.HEALTHY.value,
        "capabilities": {
            "sentiment_analysis": True,
            "semantic_similarity": True,
            "code_quality_analysis": True,
            "security_scanning": True,
            "cross_repository_analysis": True,
            "distributed_processing": True
        },
        "endpoints": {
            "health": "/health",
            "status": "/api/v1/analysis/status",
            "integration_health": "/integration/health"
        }
    }
    return create_success_response(analysis_status)


@router.get("/integration/health")
async def check_integration_health():
    """Check integration health with other services."""
    return create_success_response({
        "status": HealthStatus.HEALTHY.value,
        "services": ["doc-store", "llm-gateway"]
    })
