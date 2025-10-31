"""
Automatic Cleanup API Routes

Endpoints for controlling and monitoring the automatic cleanup service.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services.maintenance.automatic_cleanup_service import (
    get_cleanup_service,
    start_cleanup_service,
    stop_cleanup_service
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/maintenance/cleanup", tags=["Maintenance"])


class CleanupConfig(BaseModel):
    """Configuration for cleanup service."""
    cleanup_interval_minutes: int = Field(60, ge=5, le=1440, description="Cleanup interval in minutes")
    job_retention_days: int = Field(7, ge=1, le=365, description="Keep jobs for N days")
    log_retention_days: int = Field(30, ge=1, le=365, description="Keep logs for N days")


@router.get(
    "/status",
    response_model=Dict[str, Any],
    summary="Get cleanup service status",
    description="Get current status and statistics of the automatic cleanup service"
)
async def get_cleanup_status():
    """
    Get cleanup service status.
    
    Returns:
        Service status, stats, and configuration
    """
    try:
        service = get_cleanup_service()
        stats = service.get_stats()
        
        return {
            "status": "running" if service.running else "stopped",
            "stats": stats,
            "message": "Cleanup service is operational" if service.running else "Cleanup service is not running"
        }
    
    except Exception as e:
        logger.error(f"Failed to get cleanup status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/start",
    response_model=Dict[str, Any],
    summary="Start cleanup service",
    description="Start the automatic cleanup service"
)
async def start_cleanup():
    """
    Start the automatic cleanup service.
    
    The service will run periodically to clean up:
    - Old completed/failed jobs
    - Orphaned Redis messages
    - Stuck jobs
    - Old log files
    
    Returns:
        Success message and service status
    """
    try:
        service = get_cleanup_service()
        
        if service.running:
            return {
                "success": False,
                "message": "Cleanup service is already running",
                "status": "running"
            }
        
        service.start()
        
        return {
            "success": True,
            "message": "Cleanup service started successfully",
            "status": "running",
            "cleanup_interval_minutes": service.cleanup_interval.total_seconds() / 60,
            "job_retention_days": service.job_retention.days
        }
    
    except Exception as e:
        logger.error(f"Failed to start cleanup service: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/stop",
    response_model=Dict[str, Any],
    summary="Stop cleanup service",
    description="Stop the automatic cleanup service"
)
async def stop_cleanup():
    """
    Stop the automatic cleanup service.
    
    Returns:
        Success message and service status
    """
    try:
        service = get_cleanup_service()
        
        if not service.running:
            return {
                "success": False,
                "message": "Cleanup service is not running",
                "status": "stopped"
            }
        
        await service.stop()
        
        return {
            "success": True,
            "message": "Cleanup service stopped successfully",
            "status": "stopped"
        }
    
    except Exception as e:
        logger.error(f"Failed to stop cleanup service: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/run-now",
    response_model=Dict[str, Any],
    summary="Run cleanup now",
    description="Trigger an immediate cleanup run (does not affect scheduled runs)"
)
async def run_cleanup_now():
    """
    Run cleanup immediately.
    
    This triggers a one-time cleanup run without affecting the scheduled runs.
    Useful for testing or manual maintenance.
    
    Returns:
        Cleanup results
    """
    try:
        service = get_cleanup_service()
        results = await service.run_manual_cleanup()
        
        return {
            "success": True,
            "message": "Manual cleanup completed",
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Failed to run manual cleanup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Get cleanup statistics",
    description="Get detailed statistics about cleanup operations"
)
async def get_cleanup_stats():
    """
    Get cleanup statistics.
    
    Returns:
        Detailed statistics including:
        - Total cleanups performed
        - Jobs deleted
        - Redis messages removed
        - Orphaned jobs detected
        - Errors encountered
    """
    try:
        service = get_cleanup_service()
        return service.get_stats()
    
    except Exception as e:
        logger.error(f"Failed to get cleanup stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Check cleanup service health",
    description="Health check for the cleanup service"
)
async def check_cleanup_health():
    """
    Check if cleanup service is healthy.
    
    Returns:
        Health status
    """
    try:
        service = get_cleanup_service()
        
        # Check if service is running
        if not service.running:
            return {
                "healthy": False,
                "status": "stopped",
                "message": "Cleanup service is not running",
                "recommendation": "Start the service with POST /maintenance/cleanup/start"
            }
        
        # Check last cleanup time
        if service.last_cleanup is None:
            return {
                "healthy": True,
                "status": "running",
                "message": "Cleanup service is running but hasn't completed first cleanup yet"
            }
        
        from datetime import datetime, timedelta
        time_since_last = datetime.now() - service.last_cleanup
        expected_interval = service.cleanup_interval
        
        # If last cleanup was more than 2x the interval ago, something is wrong
        if time_since_last > expected_interval * 2:
            return {
                "healthy": False,
                "status": "running_but_stale",
                "message": f"Last cleanup was {time_since_last.total_seconds()/60:.1f} minutes ago (expected every {expected_interval.total_seconds()/60:.0f} minutes)",
                "recommendation": "Check logs for errors or restart the service"
            }
        
        return {
            "healthy": True,
            "status": "running",
            "message": "Cleanup service is healthy",
            "last_cleanup_minutes_ago": time_since_last.total_seconds() / 60,
            "next_cleanup_in_minutes": (expected_interval - time_since_last).total_seconds() / 60
        }
    
    except Exception as e:
        logger.error(f"Failed to check cleanup health: {e}", exc_info=True)
        return {
            "healthy": False,
            "status": "error",
            "message": f"Health check failed: {str(e)}"
        }

