"""
Worker Health Monitoring and Auto-Recovery

Provides utilities to check if background workers are running and attempt
to restart them if they've stopped. Uses Docker CLI for container inspection.
"""

import asyncio
import logging
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..services.ingestion import get_ingestion_worker

logger = logging.getLogger(__name__)


class WorkerHealthChecker:
    """
    Health checker for background workers.
    
    Monitors worker status and provides auto-recovery capabilities.
    """
    
    def __init__(self):
        """Initialize the health checker."""
        self.last_check: Optional[datetime] = None
        self.check_interval = timedelta(seconds=30)
        self.restart_attempts: Dict[str, int] = {}
        self.max_restart_attempts = 3
    
    async def check_ingestion_worker_health(self) -> Dict[str, Any]:
        """
        Check if the ingestion worker is running and healthy.
        
        Returns:
            Dict with status, running state, and details
        """
        try:
            worker = get_ingestion_worker()
            
            # Check if worker is running
            is_running = worker.running if hasattr(worker, 'running') else False
            
            # Check if worker loop is actually processing
            # (worker might say it's running but be stuck)
            is_processing = await self._check_worker_is_processing()
            
            status = {
                "worker": "ingestion",
                "running": is_running,
                "processing": is_processing,
                "healthy": is_running and is_processing,
                "last_check": datetime.now().isoformat(),
                "restart_attempts": self.restart_attempts.get("ingestion", 0)
            }
            
            if not status["healthy"]:
                logger.warning(
                    f"⚠️ Ingestion worker unhealthy: running={is_running}, processing={is_processing}"
                )
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to check ingestion worker health: {e}", exc_info=True)
            return {
                "worker": "ingestion",
                "running": False,
                "processing": False,
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def _check_worker_is_processing(self) -> bool:
        """
        Check if worker is actually processing jobs (not stuck).
        
        This checks Redis streams to see if jobs are being consumed.
        
        Returns:
            True if worker appears to be processing, False otherwise
        """
        try:
            from ..utils.redis_client import get_redis_client
            
            redis = get_redis_client()
            
            # Check if consumer group exists and is active
            try:
                info = await redis.client.xinfo_groups(redis.INGESTION_STREAM)
                
                for group in info:
                    if group.get('name') == redis.CONSUMER_GROUP:
                        # Check pending messages
                        pending = group.get('pending', 0)
                        
                        # If there are pending messages but no lag, worker is processing
                        # If pending is 0, worker is idle (which is okay)
                        return True
                
                # Consumer group doesn't exist - worker not initialized
                logger.warning("Consumer group not found - worker may not be initialized")
                return False
                
            except Exception as e:
                logger.warning(f"Could not check consumer group: {e}")
                # If we can't check Redis, assume worker is okay
                return True
                
        except Exception as e:
            logger.error(f"Error checking worker processing state: {e}")
            return False
    
    async def restart_ingestion_worker(self) -> Dict[str, Any]:
        """
        Attempt to restart the ingestion worker.
        
        Returns:
            Dict with restart status and details
        """
        try:
            worker_name = "ingestion"
            attempts = self.restart_attempts.get(worker_name, 0)
            
            if attempts >= self.max_restart_attempts:
                return {
                    "success": False,
                    "message": f"Max restart attempts ({self.max_restart_attempts}) exceeded",
                    "worker": worker_name,
                    "attempts": attempts
                }
            
            logger.info(f"🔄 Attempting to restart ingestion worker (attempt {attempts + 1}/{self.max_restart_attempts})")
            
            # Stop the current worker
            worker = get_ingestion_worker()
            if worker.running:
                await worker.stop()
                logger.info("  ✓ Stopped current worker instance")
            
            # Wait a bit for cleanup
            await asyncio.sleep(2)
            
            # Start fresh worker
            await worker.start()
            logger.info("  ✓ Started new worker instance")
            
            # Verify it started
            await asyncio.sleep(2)
            health = await self.check_ingestion_worker_health()
            
            if health["healthy"]:
                logger.info("✅ Ingestion worker restarted successfully")
                self.restart_attempts[worker_name] = 0  # Reset counter on success
                return {
                    "success": True,
                    "message": "Worker restarted successfully",
                    "worker": worker_name,
                    "health": health
                }
            else:
                self.restart_attempts[worker_name] = attempts + 1
                return {
                    "success": False,
                    "message": "Worker restarted but not healthy",
                    "worker": worker_name,
                    "health": health,
                    "attempts": attempts + 1
                }
                
        except Exception as e:
            logger.error(f"Failed to restart ingestion worker: {e}", exc_info=True)
            self.restart_attempts[worker_name] = attempts + 1
            return {
                "success": False,
                "message": f"Restart failed: {str(e)}",
                "worker": worker_name,
                "error": str(e),
                "attempts": attempts + 1
            }
    
    async def check_container_health(self) -> Dict[str, Any]:
        """
        Check if the ecosystem-mcp container is healthy using Docker CLI.
        
        Returns:
            Dict with container status
        """
        try:
            # Run docker inspect command
            result = subprocess.run(
                ["docker", "inspect", "ecosystem-mcp-service"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {
                    "healthy": False,
                    "message": "Container not found or not accessible",
                    "error": result.stderr
                }
            
            import json
            inspect_data = json.loads(result.stdout)
            
            if not inspect_data:
                return {
                    "healthy": False,
                    "message": "No container data returned"
                }
            
            container = inspect_data[0]
            state = container.get("State", {})
            health = state.get("Health", {})
            
            return {
                "healthy": state.get("Running", False) and state.get("Status") != "unhealthy",
                "running": state.get("Running", False),
                "status": state.get("Status", "unknown"),
                "health_status": health.get("Status", "none"),
                "pid": state.get("Pid", 0),
                "started_at": state.get("StartedAt", "unknown"),
                "message": "Container is healthy" if state.get("Running") else "Container is not running"
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Docker inspect command timed out")
            return {
                "healthy": False,
                "message": "Docker command timed out",
                "error": "timeout"
            }
        except Exception as e:
            logger.error(f"Failed to check container health: {e}", exc_info=True)
            return {
                "healthy": False,
                "message": f"Failed to check container: {str(e)}",
                "error": str(e)
            }
    
    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of all workers and container.
        
        Returns:
            Dict with overall health status
        """
        try:
            # Check container health
            container_health = await self.check_container_health()
            
            # Check ingestion worker
            worker_health = await self.check_ingestion_worker_health()
            
            # Overall health
            overall_healthy = (
                container_health.get("healthy", False) and
                worker_health.get("healthy", False)
            )
            
            return {
                "overall_healthy": overall_healthy,
                "container": container_health,
                "workers": {
                    "ingestion": worker_health
                },
                "timestamp": datetime.now().isoformat(),
                "recommendations": self._get_recommendations(container_health, worker_health)
            }
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive health: {e}", exc_info=True)
            return {
                "overall_healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_recommendations(self, container_health: Dict, worker_health: Dict) -> List[str]:
        """
        Get recommendations based on health status.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if not container_health.get("healthy"):
            if not container_health.get("running"):
                recommendations.append("Container is not running. Start it with: docker start ecosystem-mcp-service")
            else:
                recommendations.append("Container is unhealthy. Check logs with: docker logs ecosystem-mcp-service")
        
        if not worker_health.get("healthy"):
            if not worker_health.get("running"):
                recommendations.append("Ingestion worker is not running. Try restarting via API: POST /api/v1/admin/workers/ingestion/restart")
            elif not worker_health.get("processing"):
                recommendations.append("Ingestion worker is stuck. Check Redis streams or restart the worker.")
        
        if not recommendations:
            recommendations.append("All systems healthy ✅")
        
        return recommendations


# Global health checker instance
_health_checker: Optional[WorkerHealthChecker] = None


def get_worker_health_checker() -> WorkerHealthChecker:
    """
    Get the global worker health checker instance.
    
    Returns:
        WorkerHealthChecker instance
    """
    global _health_checker
    
    if _health_checker is None:
        _health_checker = WorkerHealthChecker()
    
    return _health_checker

