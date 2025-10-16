"""
Stuck Worker Monitor

Monitors worker heartbeats to detect truly stuck workers.
Can be run as a background task or called via API.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ...storage import get_database
from ...storage.repositories import IngestionJobRepository

logger = logging.getLogger(__name__)


async def check_stuck_workers() -> Dict[str, Any]:
    """
    Check for stuck workers (no heartbeat for >10 minutes).
    
    Returns:
        Dict with stuck worker detection results
    """
    result = {
        "total_processing": 0,
        "stuck_workers": 0,
        "stuck_jobs": [],
        "warnings": []
    }
    
    try:
        db = get_database()
        
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            
            # Get all processing jobs
            processing_jobs = await repo.get_running_jobs()
            result["total_processing"] = len(processing_jobs)
            
            if not processing_jobs:
                return result
            
            logger.debug(f"Checking {len(processing_jobs)} processing jobs for stuck workers...")
            
            for job in processing_jobs:
                try:
                    # Check for heartbeat in metadata
                    if not job.job_metadata or "worker_heartbeat" not in job.job_metadata:
                        # No heartbeat yet - might be newly started
                        if job.started_at:
                            age = datetime.utcnow() - job.started_at
                            if age > timedelta(minutes=5):
                                # Job running >5min with no heartbeat - likely stuck
                                warning = f"Job {job.id} has no heartbeat (age: {age})"
                                result["warnings"].append(warning)
                                result["stuck_workers"] += 1
                                result["stuck_jobs"].append({
                                    "job_id": str(job.id),
                                    "started_at": job.started_at.isoformat() if job.started_at else None,
                                    "reason": "no_heartbeat",
                                    "age_minutes": age.total_seconds() / 60
                                })
                                logger.warning(f"⚠️  {warning}")
                        continue
                    
                    # Check last heartbeat time
                    last_heartbeat_str = job.job_metadata.get("worker_heartbeat")
                    if not last_heartbeat_str:
                        continue
                    
                    try:
                        last_heartbeat = datetime.fromisoformat(last_heartbeat_str)
                    except:
                        logger.debug(f"Could not parse heartbeat timestamp for job {job.id}")
                        continue
                    
                    # Calculate heartbeat age
                    heartbeat_age = datetime.utcnow() - last_heartbeat
                    
                    # If no heartbeat for >10 minutes, worker is likely stuck
                    if heartbeat_age > timedelta(minutes=10):
                        worker_id = job.job_metadata.get("worker_id", "unknown")
                        warning = (
                            f"Job {job.id} worker stuck: "
                            f"no heartbeat for {heartbeat_age} "
                            f"(worker: {worker_id})"
                        )
                        result["warnings"].append(warning)
                        result["stuck_workers"] += 1
                        result["stuck_jobs"].append({
                            "job_id": str(job.id),
                            "worker_id": worker_id,
                            "last_heartbeat": last_heartbeat.isoformat(),
                            "heartbeat_age_minutes": heartbeat_age.total_seconds() / 60,
                            "reason": "heartbeat_stale"
                        })
                        logger.warning(f"⚠️  {warning}")
                
                except Exception as e:
                    error_msg = f"Error checking job {job.id} for stuck worker: {e}"
                    logger.error(error_msg)
                    result["warnings"].append(error_msg)
            
            # Log summary
            if result["stuck_workers"] > 0:
                logger.error(
                    f"🚨 Stuck workers detected: {result['stuck_workers']} of {result['total_processing']} jobs"
                )
            else:
                logger.debug(f"✅ No stuck workers ({result['total_processing']} jobs active)")
    
    except Exception as e:
        error_msg = f"Failed to check stuck workers: {e}"
        logger.error(error_msg, exc_info=True)
        result["warnings"].append(error_msg)
    
    return result


async def get_worker_health_summary() -> Dict[str, Any]:
    """
    Get summary of worker health across all jobs.
    
    Returns:
        Dict with health summary
    """
    try:
        db = get_database()
        
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            processing_jobs = await repo.get_running_jobs()
            
            summary = {
                "total_jobs": len(processing_jobs),
                "with_heartbeat": 0,
                "without_heartbeat": 0,
                "recent_heartbeat": 0,  # <1 min
                "stale_heartbeat": 0,   # >10 min
                "workers": set()
            }
            
            for job in processing_jobs:
                if not job.job_metadata or "worker_heartbeat" not in job.job_metadata:
                    summary["without_heartbeat"] += 1
                    continue
                
                summary["with_heartbeat"] += 1
                
                # Track worker IDs
                worker_id = job.job_metadata.get("worker_id")
                if worker_id:
                    summary["workers"].add(worker_id)
                
                # Check heartbeat age
                try:
                    last_heartbeat = datetime.fromisoformat(job.job_metadata["worker_heartbeat"])
                    age = datetime.utcnow() - last_heartbeat
                    
                    if age < timedelta(minutes=1):
                        summary["recent_heartbeat"] += 1
                    elif age > timedelta(minutes=10):
                        summary["stale_heartbeat"] += 1
                except:
                    pass
            
            # Convert set to list for JSON serialization
            summary["workers"] = list(summary["workers"])
            
            return summary
    
    except Exception as e:
        logger.error(f"Failed to get worker health summary: {e}", exc_info=True)
        return {
            "error": str(e),
            "total_jobs": 0
        }

