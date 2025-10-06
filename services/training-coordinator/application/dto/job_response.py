"""Job Response DTO."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class JobResponse:
    """Response with job details."""
    
    job_id: str
    mcp_id: str
    name: str
    description: str
    status: str
    priority: str
    progress_percentage: float
    current_stage: Optional[str]
    documents_processed: int
    documents_total: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[float]
    created_by: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "mcp_id": self.mcp_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "progress_percentage": self.progress_percentage,
            "current_stage": self.current_stage,
            "documents_processed": self.documents_processed,
            "documents_total": self.documents_total,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "created_by": self.created_by,
            "metadata": self.metadata,
        }

