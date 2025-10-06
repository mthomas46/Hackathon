"""Execute Job Request DTO."""

from dataclasses import dataclass


@dataclass
class ExecuteJobRequest:
    """Request to execute a training job."""
    
    job_id: str
    async_execution: bool = True
    
    def __post_init__(self):
        """Validate request."""
        if not self.job_id:
            raise ValueError("Job ID is required")

