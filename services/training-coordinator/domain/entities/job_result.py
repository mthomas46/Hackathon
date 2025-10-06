"""Job Result Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


@dataclass
class JobResult:
    """
    Result of a training job execution.
    
    Contains detailed results from each pipeline stage.
    """
    
    # Identity
    result_id: str
    job_id: str
    
    # Overall result
    success: bool
    message: str
    
    # Stage results
    extraction_results: Dict[str, Any] = field(default_factory=dict)
    normalization_results: Dict[str, Any] = field(default_factory=dict)
    embedding_results: Dict[str, Any] = field(default_factory=dict)
    storage_results: Dict[str, Any] = field(default_factory=dict)
    
    # Metrics
    total_documents: int = 0
    documents_processed: int = 0
    documents_failed: int = 0
    documents_skipped: int = 0
    
    # Embeddings generated
    total_embeddings: int = 0
    vector_db_insertions: int = 0
    graph_db_insertions: int = 0
    
    # Timing
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Errors
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Cost (if applicable)
    estimated_cost: float = 0.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate result."""
        if not self.result_id:
            raise ValueError("Result ID is required")
        if not self.job_id:
            raise ValueError("Job ID is required")
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def complete(self, success: bool = True) -> None:
        """Mark result as complete."""
        self.completed_at = datetime.now(timezone.utc)
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.success = success and len(self.errors) == 0
    
    def get_success_rate(self) -> float:
        """Get document processing success rate."""
        if self.total_documents == 0:
            return 0.0
        return self.documents_processed / self.total_documents
    
    def get_failure_rate(self) -> float:
        """Get document processing failure rate."""
        if self.total_documents == 0:
            return 0.0
        return self.documents_failed / self.total_documents
    
    def has_errors(self) -> bool:
        """Check if result has errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if result has warnings."""
        return len(self.warnings) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result_id": self.result_id,
            "job_id": self.job_id,
            "success": self.success,
            "message": self.message,
            "extraction_results": self.extraction_results,
            "normalization_results": self.normalization_results,
            "embedding_results": self.embedding_results,
            "storage_results": self.storage_results,
            "total_documents": self.total_documents,
            "documents_processed": self.documents_processed,
            "documents_failed": self.documents_failed,
            "documents_skipped": self.documents_skipped,
            "success_rate": self.get_success_rate(),
            "failure_rate": self.get_failure_rate(),
            "total_embeddings": self.total_embeddings,
            "vector_db_insertions": self.vector_db_insertions,
            "graph_db_insertions": self.graph_db_insertions,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "errors": self.errors,
            "warnings": self.warnings,
            "has_errors": self.has_errors(),
            "has_warnings": self.has_warnings(),
            "estimated_cost": self.estimated_cost,
            "metadata": self.metadata,
        }

