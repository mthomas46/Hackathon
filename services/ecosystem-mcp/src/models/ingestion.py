"""
Ingestion models for Ecosystem MCP Service.

Represents ingestion jobs, their progress, and results.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IngestionMode(str, Enum):
    """
    Ingestion mode types.
    """
    QUICK = "quick"              # Mode 1: Current .md only
    STANDARD = "standard"        # Mode 2: Current code + .md
    HISTORICAL = "historical"    # Mode 3: Current + .md history
    FULL = "full"               # Mode 4: Complete history


class IngestionStatus(str, Enum):
    """
    Ingestion job status.
    """
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IngestionJob(BaseModel):
    """
    Ingestion job model.
    
    Tracks the progress of document ingestion.
    """
    
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique job identifier"
    )
    
    mode: IngestionMode = Field(
        description="Ingestion mode"
    )
    
    status: IngestionStatus = Field(
        default=IngestionStatus.PENDING,
        description="Current job status"
    )
    
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When job started"
    )
    
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When job completed"
    )
    
    documents_processed: int = Field(
        default=0,
        ge=0,
        description="Number of documents processed"
    )
    
    documents_total: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total documents to process"
    )
    
    documents_failed: int = Field(
        default=0,
        ge=0,
        description="Number of documents that failed"
    )
    
    embeddings_generated: int = Field(
        default=0,
        ge=0,
        description="Number of embeddings generated"
    )
    
    total_cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="Total cost for this job"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional job metadata"
    )
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.documents_total and self.documents_total > 0:
            return (self.documents_processed / self.documents_total) * 100
        return 0.0
    
    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == IngestionStatus.RUNNING
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status in [
            IngestionStatus.COMPLETED,
            IngestionStatus.FAILED,
            IngestionStatus.CANCELLED
        ]
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.is_running:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "mode": "standard",
                "status": "running",
                "documents_processed": 500,
                "documents_total": 1000,
                "embeddings_generated": 450,
                "total_cost_usd": 0.75
            }
        }


class IngestionResult(BaseModel):
    """
    Result of an ingestion job.
    """
    
    job_id: UUID = Field(
        description="Job identifier"
    )
    
    mode: IngestionMode = Field(
        description="Ingestion mode used"
    )
    
    success: bool = Field(
        description="Whether job succeeded"
    )
    
    documents_processed: int = Field(
        ge=0,
        description="Documents processed"
    )
    
    documents_failed: int = Field(
        ge=0,
        description="Documents failed"
    )
    
    embeddings_generated: int = Field(
        ge=0,
        description="Embeddings generated"
    )
    
    total_cost_usd: float = Field(
        ge=0.0,
        description="Total cost"
    )
    
    duration_seconds: float = Field(
        ge=0.0,
        description="Job duration"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error if failed"
    )
    
    summary: str = Field(
        description="Human-readable summary"
    )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.documents_processed + self.documents_failed
        if total > 0:
            return (self.documents_processed / total) * 100
        return 0.0

