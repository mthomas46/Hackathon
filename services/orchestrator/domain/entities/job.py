"""Job domain entity."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from ..value_objects.job_id import JobId
from ..value_objects.job_status import JobStatus


@dataclass
class Job:
    """Domain entity representing a job execution."""

    id: JobId
    workflow_id: str
    name: str
    status: JobStatus
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def validate(self) -> None:
        """Validate the job according to domain rules."""
        if not self.name or not self.name.strip():
            raise ValueError("Job name cannot be empty")

        if not self.workflow_id:
            raise ValueError("Job must have a workflow ID")

    def start(self) -> None:
        """Mark job as started."""
        if self.status != JobStatus.QUEUED:
            raise ValueError(f"Cannot start job in status: {self.status}")

        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark job as completed."""
        if self.status != JobStatus.RUNNING:
            raise ValueError(f"Cannot complete job in status: {self.status}")

        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()

        if result:
            self.metadata.update(result)

    def fail(self, error: str) -> None:
        """Mark job as failed."""
        if self.status not in [JobStatus.RUNNING, JobStatus.QUEUED]:
            raise ValueError(f"Cannot fail job in status: {self.status}")

        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.metadata['error'] = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': str(self.id),
            'workflow_id': self.workflow_id,
            'name': self.name,
            'status': str(self.status),
            'payload': self.payload,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
