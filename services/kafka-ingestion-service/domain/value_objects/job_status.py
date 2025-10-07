"""Job Status Value Object."""

from enum import Enum


class JobStatus(str, Enum):
    """
    Ingestion job status.
    
    Represents the lifecycle state of a batch ingestion job.
    """
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"  # Some events failed
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal (job finished)."""
        return self in (
            self.COMPLETED,
            self.PARTIALLY_COMPLETED,
            self.FAILED,
            self.CANCELLED
        )
    
    @property
    def is_active(self) -> bool:
        """Check if status represents active processing."""
        return self == self.RUNNING
    
    @property
    def is_success(self) -> bool:
        """Check if status represents successful completion."""
        return self in (self.COMPLETED, self.PARTIALLY_COMPLETED)
    
    def can_transition_to(self, new_status: "JobStatus") -> bool:
        """
        Check if transition to new status is valid.
        
        Args:
            new_status: Target status
            
        Returns:
            True if transition is valid
        """
        # Terminal states cannot transition
        if self.is_terminal:
            return False
        
        # Valid transitions
        valid_transitions = {
            self.PENDING: {self.RUNNING, self.CANCELLED},
            self.RUNNING: {
                self.COMPLETED,
                self.PARTIALLY_COMPLETED,
                self.FAILED,
                self.CANCELLED
            },
        }
        
        return new_status in valid_transitions.get(self, set())

