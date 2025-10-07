"""Job DTOs."""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class JobDTO:
    """Data transfer object for ingestion job."""
    
    job_id: str
    name: str
    description: str
    status: str
    source_type: str
    total_events: int
    events_processed: int
    events_succeeded: int
    events_failed: int
    progress_percentage: float
    events_per_second: float
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    
    @classmethod
    def from_entity(cls, job: Any) -> "JobDTO":
        """
        Create DTO from entity.
        
        Args:
            job: IngestionJob entity
            
        Returns:
            JobDTO
        """
        return cls(
            job_id=job.job_id,
            name=job.name,
            description=job.description,
            status=job.status.value,
            source_type=job.source_type,
            total_events=job.total_events,
            events_processed=job.events_processed,
            events_succeeded=job.events_succeeded,
            events_failed=job.events_failed,
            progress_percentage=job.progress_percentage,
            events_per_second=job.events_per_second,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )


@dataclass
class JobListDTO:
    """Data transfer object for list of jobs."""
    
    jobs: List[JobDTO]
    total: int
    page: int
    page_size: int

