"""Ingestion Job Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4

from ..value_objects.job_status import JobStatus


@dataclass
class IngestionJob:
    """
    Ingestion job entity.
    
    Tracks a batch ingestion job with multiple document events.
    Provides coordination and monitoring for bulk operations.
    """
    
    # Identity
    job_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    
    # Status
    status: JobStatus = JobStatus.PENDING
    status_message: Optional[str] = None
    
    # Source configuration
    source_type: str = ""  # "docs_directory", "api", "webhook", etc.
    source_config: Dict[str, Any] = field(default_factory=dict)
    
    # Event tracking
    event_ids: List[str] = field(default_factory=list)
    total_events: int = 0
    events_processed: int = 0
    events_succeeded: int = 0
    events_failed: int = 0
    
    # Progress
    progress_percentage: float = 0.0
    
    # Performance metrics
    events_per_second: float = 0.0
    avg_processing_time: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Ownership
    created_by: str = "system"
    
    # Error tracking
    error_summary: Dict[str, int] = field(default_factory=dict)  # error_type -> count
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate job."""
        if not self.job_id:
            self.job_id = str(uuid4())
        if not self.name:
            raise ValueError("Job name is required")
        if not self.source_type:
            raise ValueError("Source type is required")
    
    def update_status(self, new_status: JobStatus, message: Optional[str] = None) -> None:
        """
        Update job status.
        
        Args:
            new_status: New status
            message: Optional status message
            
        Raises:
            ValueError: If transition is invalid
        """
        if not self.status.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        
        self.status = new_status
        self.status_message = message
        
        # Update timestamps
        now = datetime.now(timezone.utc)
        if new_status.is_active and not self.started_at:
            self.started_at = now
        
        if new_status.is_terminal:
            self.completed_at = now
            if new_status == JobStatus.COMPLETED:
                self.progress_percentage = 100.0
    
    def add_event(self, event_id: str) -> None:
        """
        Add event to job.
        
        Args:
            event_id: Event ID to track
        """
        if event_id not in self.event_ids:
            self.event_ids.append(event_id)
            self.total_events = len(self.event_ids)
    
    def record_event_processed(self, succeeded: bool, error_type: Optional[str] = None) -> None:
        """
        Record event processing result.
        
        Args:
            succeeded: Whether event processing succeeded
            error_type: Optional error type if failed
        """
        self.events_processed += 1
        
        if succeeded:
            self.events_succeeded += 1
        else:
            self.events_failed += 1
            if error_type:
                self.error_summary[error_type] = self.error_summary.get(error_type, 0) + 1
        
        # Update progress
        if self.total_events > 0:
            self.progress_percentage = (self.events_processed / self.total_events) * 100
        
        # Check if job is complete
        if self.events_processed >= self.total_events and self.total_events > 0:
            if self.events_failed == 0:
                self.update_status(JobStatus.COMPLETED)
            elif self.events_succeeded > 0:
                self.update_status(JobStatus.PARTIALLY_COMPLETED)
            else:
                self.update_status(JobStatus.FAILED, "All events failed")
    
    def update_metrics(self, processing_time: float) -> None:
        """
        Update performance metrics.
        
        Args:
            processing_time: Processing time for latest event (seconds)
        """
        # Update average processing time
        if self.events_processed > 0:
            current_total = self.avg_processing_time * (self.events_processed - 1)
            self.avg_processing_time = (current_total + processing_time) / self.events_processed
        else:
            self.avg_processing_time = processing_time
        
        # Update events per second
        duration = self.get_duration_seconds()
        if duration and duration > 0:
            self.events_per_second = self.events_processed / duration
    
    def get_duration_seconds(self) -> Optional[float]:
        """Get job duration in seconds."""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.events_processed == 0:
            return 0.0
        return (self.events_succeeded / self.events_processed) * 100
    
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status.is_terminal
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "status_message": self.status_message,
            "source_type": self.source_type,
            "source_config": self.source_config,
            "event_ids": self.event_ids,
            "total_events": self.total_events,
            "events_processed": self.events_processed,
            "events_succeeded": self.events_succeeded,
            "events_failed": self.events_failed,
            "progress_percentage": self.progress_percentage,
            "events_per_second": self.events_per_second,
            "avg_processing_time": self.avg_processing_time,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_by": self.created_by,
            "error_summary": self.error_summary,
            "metadata": self.metadata,
        }

