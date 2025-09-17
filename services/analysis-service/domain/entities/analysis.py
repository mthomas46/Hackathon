"""Analysis domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from .document import DocumentId


class AnalysisStatus(Enum):
    """Analysis execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class AnalysisId:
    """Value object for analysis identifier."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Analysis ID must be a non-empty string")


@dataclass
class Analysis:
    """Analysis domain entity."""
    id: AnalysisId
    document_id: DocumentId
    analysis_type: str
    status: AnalysisStatus = AnalysisStatus.PENDING
    configuration: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.analysis_type or not isinstance(self.analysis_type, str):
            raise ValueError("Analysis type must be a non-empty string")

    def start(self) -> None:
        """Mark analysis as started."""
        if self.status != AnalysisStatus.PENDING:
            raise ValueError(f"Cannot start analysis in {self.status.value} status")

        self.status = AnalysisStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, result: Dict[str, Any]) -> None:
        """Mark analysis as completed with result."""
        if self.status != AnalysisStatus.RUNNING:
            raise ValueError(f"Cannot complete analysis in {self.status.value} status")

        self.status = AnalysisStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def fail(self, error_message: str) -> None:
        """Mark analysis as failed with error message."""
        if self.status not in [AnalysisStatus.PENDING, AnalysisStatus.RUNNING]:
            raise ValueError(f"Cannot fail analysis in {self.status.value} status")

        self.status = AnalysisStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message

    def cancel(self) -> None:
        """Mark analysis as cancelled."""
        if self.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
            raise ValueError(f"Cannot cancel analysis in {self.status.value} status")

        self.status = AnalysisStatus.CANCELLED
        self.completed_at = datetime.now()

    @property
    def duration(self) -> Optional[float]:
        """Get analysis duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_completed(self) -> bool:
        """Check if analysis is completed (success or failure)."""
        return self.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]

    @property
    def is_successful(self) -> bool:
        """Check if analysis completed successfully."""
        return self.status == AnalysisStatus.COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary representation."""
        return {
            'id': self.id.value,
            'document_id': self.document_id.value,
            'analysis_type': self.analysis_type,
            'status': self.status.value,
            'configuration': self.configuration,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'duration': self.duration
        }
