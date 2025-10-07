"""Synchronization API Routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ...application.services.sync_service import SyncService
from ...domain.entities.sync_job import SyncJob

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


async def get_sync_service() -> SyncService:
    """Get sync service instance."""
    raise NotImplementedError("Service dependency injection not configured")


@router.post("/jobs", response_model=dict)
async def create_sync_job(
    name: str,
    source_type: str,
    source_config: dict,
    target_path: str,
    file_patterns: List[str] = None,
    service: SyncService = Depends(get_sync_service),
):
    """Create new sync job."""
    job = await service.create_sync_job(
        name=name,
        source_type=source_type,
        source_config=source_config,
        target_path=target_path,
        file_patterns=file_patterns,
    )
    return job.to_dict()


@router.post("/jobs/{job_id}/execute", response_model=dict)
async def execute_sync_job(
    job_id: str,
    service: SyncService = Depends(get_sync_service),
):
    """Execute synchronization job."""
    try:
        job = await service.execute_sync_job(job_id)
        return job.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=dict)
async def get_sync_job(
    job_id: str,
    service: SyncService = Depends(get_sync_service),
):
    """Get sync job by ID."""
    job = await service.get_sync_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Sync job not found")
    return job.to_dict()


@router.get("/jobs", response_model=List[dict])
async def list_sync_jobs(
    service: SyncService = Depends(get_sync_service),
):
    """List all sync jobs."""
    jobs = await service.list_sync_jobs()
    return [job.to_dict() for job in jobs]

