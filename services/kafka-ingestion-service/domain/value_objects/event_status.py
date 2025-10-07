"""Event Status Value Object."""

from enum import Enum


class EventStatus(str, Enum):
    """
    Document event processing status.
    
    Represents the lifecycle state of an event through the ingestion pipeline.
    """
    
    PENDING = "pending"
    INGESTED = "ingested"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"  # Max retries exceeded
    
    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal (no further processing)."""
        return self in (self.PROCESSED, self.DEAD_LETTER)
    
    @property
    def is_active(self) -> bool:
        """Check if status represents active processing."""
        return self in (self.PROCESSING, self.RETRYING)
    
    @property
    def is_error(self) -> bool:
        """Check if status represents an error state."""
        return self in (self.FAILED, self.DEAD_LETTER)
    
    def can_transition_to(self, new_status: "EventStatus") -> bool:
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
            self.PENDING: {self.INGESTED, self.FAILED},
            self.INGESTED: {self.PROCESSING, self.FAILED},
            self.PROCESSING: {self.PROCESSED, self.FAILED},
            self.FAILED: {self.RETRYING, self.DEAD_LETTER},
            self.RETRYING: {self.PROCESSING, self.DEAD_LETTER},
        }
        
        return new_status in valid_transitions.get(self, set())

