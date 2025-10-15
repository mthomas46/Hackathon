"""
Job Recovery API Routes

Provides endpoints for managing job checkpoints and recovery.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ...storage import get_database
from ...utils.job_recovery import get_recovery_manager, JobType

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class JobRecoveryStatus(BaseModel):
    """Job recovery status response."""
    job_id: str
    job_type: str
    can_resume: bool
    last_checkpoint: Optional[Dict[str, Any]] = None
    resume_from_sequence: Optional[int] = None
    incomplete_count: int = 0
    progress: Optional[Dict[str, Any]] = None


class ResumeJobRequest(BaseModel):
    """Request to resume a job."""
    job_id: str = Field(..., description="Job ID to resume")
    job_type: str = Field(..., description="Type of job (ingestion, embedding, documentation)")


class CheckpointListResponse(BaseModel):
    """List of checkpoints for a job."""
    job_id: str
    total_checkpoints: int
    completed_checkpoints: int
    pending_checkpoints: int
    failed_checkpoints: int
    checkpoints: list[Dict[str, Any]]


# Endpoints
@router.get("/recovery/status/{job_id}", response_model=JobRecoveryStatus)
async def get_recovery_status(job_id: str):
    """
    Get recovery status for a job.
    
    Returns checkpoint information and whether job can be resumed.
    """
    try:
        db = get_database()
        recovery_manager = get_recovery_manager(db)
        
        # Load checkpoints
        await recovery_manager.load_checkpoints(job_id)
        
        # Check if can resume
        can_resume = await recovery_manager.can_resume(job_id)
        
        if not can_resume:
            return JobRecoveryStatus(
                job_id=job_id,
                job_type="unknown",
                can_resume=False,
                incomplete_count=0
            )
        
        # Get resume state
        resume_state = await recovery_manager.get_resume_state(job_id)
        
        return JobRecoveryStatus(
            job_id=job_id,
            job_type=resume_state["last_checkpoint"]["job_type"],
            can_resume=True,
            last_checkpoint=resume_state["last_checkpoint"],
            resume_from_sequence=resume_state["resume_from_sequence"],
            incomplete_count=resume_state["incomplete_count"],
            progress=resume_state["progress"]
        )
    
    except Exception as e:
        logger.error(f"Error getting recovery status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recovery/checkpoints/{job_id}", response_model=CheckpointListResponse)
async def get_checkpoints(job_id: str):
    """
    Get all checkpoints for a job.
    
    Returns detailed checkpoint information.
    """
    try:
        db = get_database()
        recovery_manager = get_recovery_manager(db)
        
        # Load checkpoints
        await recovery_manager.load_checkpoints(job_id)
        
        # Get all checkpoints
        checkpoints = recovery_manager.checkpoints.get(job_id, [])
        
        # Count by status
        completed = sum(1 for cp in checkpoints if cp.status.value == "completed")
        pending = sum(1 for cp in checkpoints if cp.status.value == "pending")
        failed = sum(1 for cp in checkpoints if cp.status.value == "failed")
        
        return CheckpointListResponse(
            job_id=job_id,
            total_checkpoints=len(checkpoints),
            completed_checkpoints=completed,
            pending_checkpoints=pending,
            failed_checkpoints=failed,
            checkpoints=[cp.to_dict() for cp in checkpoints]
        )
    
    except Exception as e:
        logger.error(f"Error getting checkpoints: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recovery/resume")
async def resume_job(request: ResumeJobRequest):
    """
    Resume an interrupted job from last checkpoint.
    
    Triggers job processing with resume enabled.
    """
    try:
        db = get_database()
        recovery_manager = get_recovery_manager(db)
        
        # Validate job type
        try:
            job_type = JobType(request.job_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid job type: {request.job_type}"
            )
        
        # Load checkpoints
        await recovery_manager.load_checkpoints(request.job_id)
        
        # Check if can resume
        can_resume = await recovery_manager.can_resume(request.job_id)
        
        if not can_resume:
            raise HTTPException(
                status_code=400,
                detail=f"Job {request.job_id} cannot be resumed (no completed checkpoints)"
            )
        
        # Get resume state
        resume_state = await recovery_manager.get_resume_state(request.job_id)
        
        # Dispatch resume based on job type
        if job_type == JobType.INGESTION:
            result = await _resume_ingestion(request.job_id, resume_state)
        elif job_type == JobType.EMBEDDING:
            result = await _resume_embedding(request.job_id, resume_state)
        elif job_type == JobType.DOCUMENTATION:
            result = await _resume_documentation(request.job_id, resume_state)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported job type: {job_type}")
        
        return {
            "success": True,
            "job_id": request.job_id,
            "job_type": request.job_type,
            "message": "Job resumed successfully",
            "resume_state": resume_state,
            "result": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/recovery/checkpoints/{job_id}")
async def cleanup_checkpoints(
    job_id: str,
    keep_last: int = 3
):
    """
    Clean up old checkpoints for a job.
    
    Keeps only the most recent N checkpoints.
    """
    try:
        db = get_database()
        recovery_manager = get_recovery_manager(db)
        
        # Load checkpoints
        await recovery_manager.load_checkpoints(job_id)
        
        # Get count before cleanup
        before_count = len(recovery_manager.checkpoints.get(job_id, []))
        
        # Cleanup
        await recovery_manager.cleanup_checkpoints(
            job_id=job_id,
            keep_last=keep_last
        )
        
        # Get count after cleanup
        after_count = len(recovery_manager.checkpoints.get(job_id, []))
        
        return {
            "success": True,
            "job_id": job_id,
            "checkpoints_before": before_count,
            "checkpoints_after": after_count,
            "removed": before_count - after_count
        }
    
    except Exception as e:
        logger.error(f"Error cleaning up checkpoints: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions for resuming different job types
async def _resume_ingestion(job_id: str, resume_state: Dict[str, Any]) -> Dict[str, Any]:
    """Resume an ingestion job."""
    from ...storage.repositories import IngestionJobRepository
    from ...services.ingestion.recoverable_job_processor import RecoverableJobProcessor
    
    db = get_database()
    async with db.session() as session:
        job_repo = IngestionJobRepository(session)
        job = await job_repo.get_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # Create recoverable processor
        recovery_manager = get_recovery_manager(db)
        processor = RecoverableJobProcessor(job_id, recovery_manager)
        
        # Process with resume enabled
        result = await processor.process(job, resume=True)
        
        return result


async def _resume_embedding(job_id: str, resume_state: Dict[str, Any]) -> Dict[str, Any]:
    """Resume an embedding generation job."""
    from ...services.embeddings.recoverable_embedding_generator import RecoverableEmbeddingGenerator
    
    # Create recoverable generator
    generator = RecoverableEmbeddingGenerator(job_id=job_id)
    
    # Resume generation
    result = await generator.generate_all_missing(resume=True)
    
    return result


async def _resume_documentation(job_id: str, resume_state: Dict[str, Any]) -> Dict[str, Any]:
    """Resume a documentation generation job."""
    from ...services.documentation.recoverable_doc_generator import RecoverableDocGenerator
    
    # Get config from resume state
    last_checkpoint = resume_state["last_checkpoint"]["data"]
    
    # Reconstruct config (you may want to store this in checkpoint data)
    config = {
        "num_passes": last_checkpoint.get("total_passes", 3),
        "questions_per_pass": 5,
        "output_dir": "/app/generated_docs",
        "topic": "system documentation",
        "llm_tier": "auto",
        "max_retries": 3
    }
    
    # Create recoverable generator
    generator = RecoverableDocGenerator(job_id=job_id)
    
    # Resume generation
    result = await generator.generate_multipass(config=config, resume=True)
    
    return result

