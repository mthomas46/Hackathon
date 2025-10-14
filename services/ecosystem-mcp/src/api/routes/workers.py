"""
Worker Management Endpoints

Provides API endpoints for monitoring and managing background workers.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from ...utils.worker_health import get_worker_health_checker

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/workers/health",
    response_model=Dict[str, Any],
    summary="Get worker health status",
    description="Check health of all background workers and container"
)
async def get_worker_health():
    """
    Get comprehensive health status of workers and container.
    
    Returns:
        Dict with health status for all workers
    """
    try:
        health_checker = get_worker_health_checker()
        health = await health_checker.get_comprehensive_health()
        return health
    except Exception as e:
        logger.error(f"Failed to get worker health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/workers/ingestion/status",
    response_model=Dict[str, Any],
    summary="Get ingestion worker status",
    description="Check if ingestion worker is running and healthy"
)
async def get_ingestion_worker_status():
    """
    Get status of the ingestion worker.
    
    Returns:
        Dict with ingestion worker status
    """
    try:
        health_checker = get_worker_health_checker()
        status = await health_checker.check_ingestion_worker_health()
        return status
    except Exception as e:
        logger.error(f"Failed to get ingestion worker status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/workers/ingestion/restart",
    response_model=Dict[str, Any],
    summary="Restart ingestion worker",
    description="Attempt to restart the ingestion worker"
)
async def restart_ingestion_worker():
    """
    Restart the ingestion worker.
    
    This will:
    1. Stop the current worker instance
    2. Start a new worker instance
    3. Verify the new worker is healthy
    
    Returns:
        Dict with restart status
    """
    try:
        health_checker = get_worker_health_checker()
        result = await health_checker.restart_ingestion_worker()
        
        if not result.get("success"):
            # Return 200 but with success=false in body
            # (not a 500 error, just unsuccessful restart)
            return result
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to restart ingestion worker: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/workers/ingestion/auto-recover",
    response_model=Dict[str, Any],
    summary="Auto-recover ingestion worker",
    description="Check worker health and restart if unhealthy"
)
async def auto_recover_ingestion_worker():
    """
    Check ingestion worker health and restart if needed.
    
    This endpoint checks if the worker is healthy, and if not,
    attempts to restart it automatically.
    
    Returns:
        Dict with recovery status
    """
    try:
        health_checker = get_worker_health_checker()
        
        # Check current health
        health = await health_checker.check_ingestion_worker_health()
        
        if health.get("healthy"):
            return {
                "recovered": False,
                "message": "Worker is already healthy, no action needed",
                "health": health
            }
        
        # Worker is unhealthy, attempt restart
        logger.info("🔧 Auto-recovering unhealthy ingestion worker...")
        restart_result = await health_checker.restart_ingestion_worker()
        
        return {
            "recovered": restart_result.get("success", False),
            "message": "Recovery attempted" if restart_result.get("success") else "Recovery failed",
            "restart_result": restart_result,
            "previous_health": health
        }
        
    except Exception as e:
        logger.error(f"Failed to auto-recover worker: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/workers/container/health",
    response_model=Dict[str, Any],
    summary="Get container health",
    description="Check ecosystem-mcp container health via Docker CLI"
)
async def get_container_health():
    """
    Get health status of the ecosystem-mcp container.
    
    Uses Docker CLI to inspect container state.
    
    Returns:
        Dict with container health status
    """
    try:
        health_checker = get_worker_health_checker()
        health = await health_checker.check_container_health()
        return health
    except Exception as e:
        logger.error(f"Failed to get container health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

