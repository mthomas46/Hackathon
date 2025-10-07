"""Create Job Command."""

from dataclasses import dataclass
from typing import Dict, Any

from ...domain.entities.ingestion_job import IngestionJob
from ...domain.repositories.job_repository import JobRepository


@dataclass
class CreateJobCommand:
    """
    Command to create an ingestion job.
    
    Represents the intent to create a batch ingestion job.
    """
    
    name: str
    description: str
    source_type: str
    source_config: Dict[str, Any]
    created_by: str = "system"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class CreateJobHandler:
    """
    Handler for create job command.
    
    Creates ingestion job and persists it.
    """
    
    def __init__(self, job_repository: JobRepository):
        """
        Initialize handler.
        
        Args:
            job_repository: Job repository
        """
        self.job_repository = job_repository
    
    async def handle(self, command: CreateJobCommand) -> IngestionJob:
        """
        Handle create job command.
        
        Args:
            command: Create job command
            
        Returns:
            Created ingestion job
            
        Raises:
            ValueError: If command is invalid
        """
        # Validate command
        if not command.name:
            raise ValueError("Job name is required")
        if not command.source_type:
            raise ValueError("Source type is required")
        
        # Create job
        job = IngestionJob(
            name=command.name,
            description=command.description,
            source_type=command.source_type,
            source_config=command.source_config,
            created_by=command.created_by,
            metadata=command.metadata,
        )
        
        # Save job
        await self.job_repository.save(job)
        
        return job

