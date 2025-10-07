"""Job Status Value Object."""

from enum import Enum


class JobStatus(str, Enum):
    """
    Status of a training job.
    
    Tracks the lifecycle of MCP training jobs through the pipeline.
    """
    
    PENDING = "pending"
    """Job is queued, waiting to start."""
    
    VALIDATING = "validating"
    """Job is being validated."""
    
    EXTRACTING = "extracting"
    """Data extraction in progress."""
    
    NORMALIZING = "normalizing"
    """Data normalization in progress."""
    
    EMBEDDING = "embedding"
    """Embedding generation in progress."""
    
    STORING = "storing"
    """Storing to data stores (vector/graph DB)."""
    
    COMPLETED = "completed"
    """Job completed successfully."""
    
    FAILED = "failed"
    """Job failed with errors."""
    
    CANCELLED = "cancelled"
    """Job was cancelled."""
    
    PAUSED = "paused"
    """Job is paused."""
    
    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal (no further transitions)."""
        return self in {
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        }
    
    @property
    def is_active(self) -> bool:
        """Check if job is actively processing."""
        return self in {
            JobStatus.VALIDATING,
            JobStatus.EXTRACTING,
            JobStatus.NORMALIZING,
            JobStatus.EMBEDDING,
            JobStatus.STORING,
        }
    
    @property
    def is_waiting(self) -> bool:
        """Check if job is waiting."""
        return self in {
            JobStatus.PENDING,
            JobStatus.PAUSED,
        }
    
    def can_transition_to(self, new_status: "JobStatus") -> bool:
        """
        Check if transition to new status is valid.
        
        Args:
            new_status: Target status
        
        Returns:
            True if transition is allowed
        """
        # Terminal states cannot transition
        if self.is_terminal:
            return False
        
        # Valid transitions
        valid_transitions = {
            JobStatus.PENDING: {
                JobStatus.VALIDATING,
                JobStatus.CANCELLED,
            },
            JobStatus.VALIDATING: {
                JobStatus.EXTRACTING,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
            },
            JobStatus.EXTRACTING: {
                JobStatus.NORMALIZING,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
                JobStatus.PAUSED,
            },
            JobStatus.NORMALIZING: {
                JobStatus.EMBEDDING,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
                JobStatus.PAUSED,
            },
            JobStatus.EMBEDDING: {
                JobStatus.STORING,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
                JobStatus.PAUSED,
            },
            JobStatus.STORING: {
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
            },
            JobStatus.PAUSED: {
                JobStatus.EXTRACTING,
                JobStatus.NORMALIZING,
                JobStatus.EMBEDDING,
                JobStatus.CANCELLED,
            },
        }
        
        allowed = valid_transitions.get(self, set())
        return new_status in allowed

