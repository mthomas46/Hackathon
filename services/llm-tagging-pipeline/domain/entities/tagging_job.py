"""Tagging Job Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4


@dataclass
class TaggingJob:
    """
    Tagging job entity.
    
    Tracks a batch tagging operation for multiple documents.
    Coordinates LLM-based tagging across documents.
    """
    
    # Identity
    job_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    
    # Configuration
    model_name: str = "llama2"  # Default Ollama model
    batch_size: int = 10
    max_retries: int = 3
    
    # Document tracking
    document_ids: List[str] = field(default_factory=list)
    total_documents: int = 0
    documents_processed: int = 0
    documents_succeeded: int = 0
    documents_failed: int = 0
    
    # Progress
    progress_percentage: float = 0.0
    current_document: Optional[str] = None
    
    # Status
    status: str = "pending"  # pending, running, completed, failed, cancelled
    error_message: Optional[str] = None
    
    # Performance metrics
    avg_processing_time: float = 0.0
    total_tokens_used: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Ownership
    created_by: str = "system"
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate job."""
        if not self.job_id:
            self.job_id = str(uuid4())
        if not self.name:
            raise ValueError("Job name is required")
    
    def start(self) -> None:
        """Start the job."""
        if self.status != "pending":
            raise ValueError(f"Cannot start job in {self.status} status")
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)
    
    def add_document(self, document_id: str) -> None:
        """
        Add document to job.
        
        Args:
            document_id: Document ID to add
        """
        if document_id not in self.document_ids:
            self.document_ids.append(document_id)
            self.total_documents = len(self.document_ids)
    
    def record_document_processed(
        self,
        document_id: str,
        succeeded: bool,
        processing_time: float,
        tokens_used: int = 0,
        error: Optional[str] = None
    ) -> None:
        """
        Record document processing result.
        
        Args:
            document_id: Document ID
            succeeded: Whether processing succeeded
            processing_time: Processing time in seconds
            tokens_used: Number of tokens used
            error: Optional error message
        """
        self.documents_processed += 1
        self.current_document = document_id
        
        if succeeded:
            self.documents_succeeded += 1
        else:
            self.documents_failed += 1
            if error and not self.error_message:
                self.error_message = error
        
        # Update metrics
        if self.documents_processed > 0:
            current_total = self.avg_processing_time * (self.documents_processed - 1)
            self.avg_processing_time = (current_total + processing_time) / self.documents_processed
        
        self.total_tokens_used += tokens_used
        
        # Update progress
        if self.total_documents > 0:
            self.progress_percentage = (self.documents_processed / self.total_documents) * 100
        
        # Check if job is complete
        if self.documents_processed >= self.total_documents and self.total_documents > 0:
            self.complete()
    
    def complete(self) -> None:
        """Mark job as completed."""
        if self.documents_failed == 0:
            self.status = "completed"
        elif self.documents_succeeded > 0:
            self.status = "partially_completed"
        else:
            self.status = "failed"
            if not self.error_message:
                self.error_message = "All documents failed to process"
        
        self.completed_at = datetime.now(timezone.utc)
        self.progress_percentage = 100.0
    
    def cancel(self) -> None:
        """Cancel the job."""
        if self.status in ("completed", "failed", "cancelled"):
            raise ValueError(f"Cannot cancel job in {self.status} status")
        self.status = "cancelled"
        self.completed_at = datetime.now(timezone.utc)
    
    def fail(self, error: str) -> None:
        """
        Mark job as failed.
        
        Args:
            error: Error message
        """
        self.status = "failed"
        self.error_message = error
        self.completed_at = datetime.now(timezone.utc)
    
    def get_duration_seconds(self) -> Optional[float]:
        """Get job duration in seconds."""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.documents_processed == 0:
            return 0.0
        return (self.documents_succeeded / self.documents_processed) * 100
    
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status in ("completed", "partially_completed", "failed", "cancelled")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "description": self.description,
            "model_name": self.model_name,
            "batch_size": self.batch_size,
            "max_retries": self.max_retries,
            "document_ids": self.document_ids,
            "total_documents": self.total_documents,
            "documents_processed": self.documents_processed,
            "documents_succeeded": self.documents_succeeded,
            "documents_failed": self.documents_failed,
            "progress_percentage": self.progress_percentage,
            "current_document": self.current_document,
            "status": self.status,
            "error_message": self.error_message,
            "avg_processing_time": self.avg_processing_time,
            "total_tokens_used": self.total_tokens_used,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_by": self.created_by,
            "metadata": self.metadata,
        }

