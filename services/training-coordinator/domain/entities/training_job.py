"""Training Job Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from services.training_coordinator.domain.value_objects.job_status import JobStatus
from services.training_coordinator.domain.value_objects.job_priority import JobPriority
from services.training_coordinator.domain.value_objects.data_source import DataSource


@dataclass
class TrainingJob:
    """
    Training job for MCP knowledge base.
    
    Aggregate root for training pipeline operations.
    Tracks a complete training job through all pipeline stages.
    """
    
    # Identity
    job_id: str
    mcp_id: str
    name: str
    description: str
    
    # Status & Priority
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    
    # Data source configuration
    data_sources: List[DataSource] = field(default_factory=list)
    source_config: Dict[str, Any] = field(default_factory=dict)
    
    # Pipeline configuration
    enable_extraction: bool = True
    enable_normalization: bool = True
    enable_embedding: bool = True
    enable_storage: bool = True
    
    # Resource limits
    max_documents: Optional[int] = None
    max_duration_seconds: Optional[int] = None
    max_cost: Optional[float] = None
    
    # Progress tracking
    progress_percentage: float = 0.0
    current_stage: Optional[str] = None
    documents_processed: int = 0
    documents_total: int = 0
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    result_summary: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    # Ownership
    created_by: str = "system"
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate job."""
        if not self.job_id:
            raise ValueError("Job ID is required")
        if not self.mcp_id:
            raise ValueError("MCP ID is required")
        if not self.data_sources:
            raise ValueError("At least one data source required")
    
    def update_status(self, new_status: JobStatus, message: Optional[str] = None) -> None:
        """
        Update job status.
        
        Args:
            new_status: New status
            message: Optional message
        
        Raises:
            ValueError: If transition invalid
        """
        if not self.status.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        
        self.status = new_status
        
        if message:
            self.error_message = message
        
        # Update timestamps
        now = datetime.now(timezone.utc)
        if new_status.is_active and not self.started_at:
            self.started_at = now
        
        if new_status.is_terminal:
            self.completed_at = now
            if new_status == JobStatus.COMPLETED:
                self.progress_percentage = 100.0
    
    def update_progress(self, percentage: float, stage: str, docs_processed: int = None) -> None:
        """
        Update job progress.
        
        Args:
            percentage: Progress percentage (0-100)
            stage: Current stage
            docs_processed: Documents processed (optional)
        """
        self.progress_percentage = min(max(percentage, 0.0), 100.0)
        self.current_stage = stage
        
        if docs_processed is not None:
            self.documents_processed = docs_processed
    
    def get_duration_seconds(self) -> Optional[float]:
        """Get job duration in seconds."""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    def is_timed_out(self) -> bool:
        """Check if job has exceeded max duration."""
        if not self.max_duration_seconds:
            return False
        
        duration = self.get_duration_seconds()
        return duration is not None and duration > self.max_duration_seconds
    
    def can_pause(self) -> bool:
        """Check if job can be paused."""
        return self.status.is_active
    
    def can_resume(self) -> bool:
        """Check if job can be resumed."""
        return self.status == JobStatus.PAUSED
    
    def can_cancel(self) -> bool:
        """Check if job can be cancelled."""
        return not self.status.is_terminal
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "mcp_id": self.mcp_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "data_sources": [ds.value for ds in self.data_sources],
            "source_config": self.source_config,
            "enable_extraction": self.enable_extraction,
            "enable_normalization": self.enable_normalization,
            "enable_embedding": self.enable_embedding,
            "enable_storage": self.enable_storage,
            "max_documents": self.max_documents,
            "max_duration_seconds": self.max_duration_seconds,
            "max_cost": self.max_cost,
            "progress_percentage": self.progress_percentage,
            "current_stage": self.current_stage,
            "documents_processed": self.documents_processed,
            "documents_total": self.documents_total,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result_summary": self.result_summary,
            "error_message": self.error_message,
            "created_by": self.created_by,
            "metadata": self.metadata,
        }

