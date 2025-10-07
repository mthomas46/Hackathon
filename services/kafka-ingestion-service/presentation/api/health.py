"""Health Check Endpoints."""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "kafka-ingestion-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Returns:
        Readiness status
    """
    # TODO: Check Kafka, Redis connectivity
    return {
        "status": "ready",
        "checks": {
            "kafka": "unknown",
            "redis": "unknown"
        }
    }

