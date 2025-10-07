"""Ingestion API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...application.commands.ingest_document import IngestDocumentCommand, IngestDocumentHandler
from ...application.commands.create_job import CreateJobCommand, CreateJobHandler
from ...application.dtos.event_dto import EventDTO
from ...application.dtos.job_dto import JobDTO
from ...domain.repositories.event_repository import EventRepository
from ...domain.repositories.job_repository import JobRepository
from .schemas import IngestDocumentRequest, CreateJobRequest

router = APIRouter(prefix="/api/v1", tags=["ingestion"])


# Dependency injection placeholders
async def get_event_repository() -> EventRepository:
    """Get event repository."""
    # TODO: Implement actual dependency injection
    raise NotImplementedError()


async def get_job_repository() -> JobRepository:
    """Get job repository."""
    # TODO: Implement actual dependency injection
    raise NotImplementedError()


@router.post("/events", response_model=EventDTO)
async def ingest_document(
    request: IngestDocumentRequest,
    event_repository: EventRepository = Depends(get_event_repository)
):
    """
    Ingest a document event.
    
    Args:
        request: Ingest document request
        event_repository: Event repository
        
    Returns:
        Created event
    """
    try:
        # Create command
        command = IngestDocumentCommand(
            document_id=request.document_id,
            title=request.title,
            content=request.content,
            event_type=request.event_type,
            source_metadata=request.source_metadata,
            content_type=request.content_type or "text/markdown",
            source_url=request.source_url,
            tags=request.tags or [],
            categories=request.categories or [],
            metadata=request.metadata or {},
            correlation_id=request.correlation_id,
        )
        
        # Handle command
        handler = IngestDocumentHandler(event_repository)
        event = await handler.handle(command)
        
        # Return DTO
        return EventDTO.from_entity(event)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs", response_model=JobDTO)
async def create_job(
    request: CreateJobRequest,
    job_repository: JobRepository = Depends(get_job_repository)
):
    """
    Create an ingestion job.
    
    Args:
        request: Create job request
        job_repository: Job repository
        
    Returns:
        Created job
    """
    try:
        # Create command
        command = CreateJobCommand(
            name=request.name,
            description=request.description,
            source_type=request.source_type,
            source_config=request.source_config,
            created_by=request.created_by or "system",
            metadata=request.metadata or {},
        )
        
        # Handle command
        handler = CreateJobHandler(job_repository)
        job = await handler.handle(command)
        
        # Return DTO
        return JobDTO.from_entity(job)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}", response_model=EventDTO)
async def get_event(
    event_id: str,
    event_repository: EventRepository = Depends(get_event_repository)
):
    """
    Get event by ID.
    
    Args:
        event_id: Event ID
        event_repository: Event repository
        
    Returns:
        Event
    """
    event = await event_repository.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return EventDTO.from_entity(event)


@router.get("/jobs/{job_id}", response_model=JobDTO)
async def get_job(
    job_id: str,
    job_repository: JobRepository = Depends(get_job_repository)
):
    """
    Get job by ID.
    
    Args:
        job_id: Job ID
        job_repository: Job repository
        
    Returns:
        Job
    """
    job = await job_repository.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobDTO.from_entity(job)


@router.get("/jobs", response_model=List[JobDTO])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    job_repository: JobRepository = Depends(get_job_repository)
):
    """
    List jobs.
    
    Args:
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return
        job_repository: Job repository
        
    Returns:
        List of jobs
    """
    jobs = await job_repository.list_all(skip=skip, limit=limit)
    return [JobDTO.from_entity(job) for job in jobs]

