"""
Orchestration API Routes

REST API endpoints for sub-job execution orchestration.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from ...services.orchestration import get_job_orchestrator, get_progress_tracker
from ...services.orchestration.job_orchestrator import ExecutionStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orchestration", tags=["Orchestration"])


class ExecuteRequest(BaseModel):
    """Request to execute a processing plan."""
    plan_id: str
    max_concurrent: int = 5


class ExecuteResponse(BaseModel):
    """Response from execution request."""
    success: bool
    message: str
    plan_id: str
    status: str


class StatusResponse(BaseModel):
    """Execution status response."""
    plan_id: str
    status: str
    sub_jobs_completed: int
    sub_jobs_failed: int
    total_files_processed: int
    total_files_failed: int
    total_files_skipped: int
    duration_seconds: float
    error_message: Optional[str] = None


class ProgressResponse(BaseModel):
    """Progress response."""
    plan_id: str
    total_files: int
    files_processed: int
    files_failed: int
    files_skipped: int
    progress_pct: float
    sub_jobs_total: int
    sub_jobs_completed: int
    sub_jobs_failed: int
    sub_jobs_active: int
    eta_seconds: Optional[float]
    elapsed_seconds: Optional[float]


@router.post(
    "/execute/{plan_id}",
    response_model=ExecuteResponse,
    summary="Execute processing plan",
    description="Start parallel execution of a processing plan's sub-jobs"
)
async def execute_plan(
    plan_id: str,
    background_tasks: BackgroundTasks,
    max_concurrent: int = 5
):
    """
    Execute a processing plan with parallel sub-jobs.
    
    This starts the execution in the background and returns immediately.
    Use the status endpoint to monitor progress.
    """
    try:
        logger.info(f"🚀 Received execution request for plan {plan_id}")
        
        orchestrator = get_job_orchestrator(max_concurrent=max_concurrent)
        
        # Check if already executing
        current_status = await orchestrator.get_execution_status(plan_id)
        if current_status:
            return ExecuteResponse(
                success=False,
                message=f"Plan {plan_id} is already executing",
                plan_id=plan_id,
                status=current_status.status.value
            )
        
        # Start execution in background
        background_tasks.add_task(orchestrator.execute_plan, plan_id)
        
        logger.info(f"✅ Started execution of plan {plan_id}")
        
        return ExecuteResponse(
            success=True,
            message=f"Execution started for plan {plan_id}",
            plan_id=plan_id,
            status="running"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start execution: {str(e)}"
        )


@router.get(
    "/status/{plan_id}",
    response_model=StatusResponse,
    summary="Get execution status",
    description="Get current execution status for a processing plan"
)
async def get_execution_status(plan_id: str):
    """Get execution status for a plan."""
    try:
        orchestrator = get_job_orchestrator()
        result = await orchestrator.get_execution_status(plan_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active execution found for plan {plan_id}"
            )
        
        return StatusResponse(
            plan_id=result.plan_id,
            status=result.status.value,
            sub_jobs_completed=result.sub_jobs_completed,
            sub_jobs_failed=result.sub_jobs_failed,
            total_files_processed=result.total_files_processed,
            total_files_failed=result.total_files_failed,
            total_files_skipped=result.total_files_skipped,
            duration_seconds=result.duration_seconds,
            error_message=result.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution status: {str(e)}"
        )


@router.post(
    "/pause/{plan_id}",
    summary="Pause execution",
    description="Pause execution of a processing plan"
)
async def pause_execution(plan_id: str):
    """Pause execution of a plan."""
    try:
        orchestrator = get_job_orchestrator()
        success = await orchestrator.pause_execution(plan_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active execution found for plan {plan_id}"
            )
        
        return {
            "success": True,
            "message": f"Execution paused for plan {plan_id}",
            "plan_id": plan_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause execution: {str(e)}"
        )


@router.post(
    "/resume/{plan_id}",
    summary="Resume execution",
    description="Resume paused execution of a processing plan"
)
async def resume_execution(plan_id: str):
    """Resume execution of a paused plan."""
    try:
        orchestrator = get_job_orchestrator()
        success = await orchestrator.resume_execution(plan_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan {plan_id} is not paused"
            )
        
        return {
            "success": True,
            "message": f"Execution resumed for plan {plan_id}",
            "plan_id": plan_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume execution: {str(e)}"
        )


@router.post(
    "/cancel/{plan_id}",
    summary="Cancel execution",
    description="Cancel execution of a processing plan"
)
async def cancel_execution(plan_id: str):
    """Cancel execution of a plan."""
    try:
        orchestrator = get_job_orchestrator()
        success = await orchestrator.cancel_execution(plan_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active execution found for plan {plan_id}"
            )
        
        return {
            "success": True,
            "message": f"Execution cancelled for plan {plan_id}",
            "plan_id": plan_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel execution: {str(e)}"
        )


@router.get(
    "/progress/{plan_id}",
    response_model=ProgressResponse,
    summary="Get execution progress",
    description="Get real-time progress for a processing plan"
)
async def get_progress(plan_id: str):
    """Get execution progress for a plan."""
    try:
        tracker = get_progress_tracker()
        progress = await tracker.get_progress(plan_id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No progress tracking found for plan {plan_id}"
            )
        
        return ProgressResponse(
            plan_id=progress.plan_id,
            total_files=progress.total_files,
            files_processed=progress.files_processed,
            files_failed=progress.files_failed,
            files_skipped=progress.files_skipped,
            progress_pct=progress.progress_pct,
            sub_jobs_total=progress.sub_jobs_total,
            sub_jobs_completed=progress.sub_jobs_completed,
            sub_jobs_failed=progress.sub_jobs_failed,
            sub_jobs_active=progress.sub_jobs_active,
            eta_seconds=progress.eta_seconds,
            elapsed_seconds=progress.elapsed_seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get progress: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}"
        )


@router.get(
    "/metrics",
    summary="Get orchestration metrics",
    description="Get overall orchestration system metrics"
)
async def get_metrics():
    """Get orchestration system metrics."""
    try:
        from ...services.orchestration import get_resource_allocator
        
        allocator = get_resource_allocator()
        stats = allocator.get_stats()
        
        return {
            "success": True,
            "resource_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )

