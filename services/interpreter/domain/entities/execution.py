"""Execution Domain Entities.

Core domain entities for execution tracking and results.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from uuid import uuid4


class ExecutionStatus(Enum):
    """Enumeration of execution statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class ExecutionResult:
    """Domain entity representing the result of an execution."""

    execution_id: str
    status: ExecutionStatus
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    output_format: Optional[str] = None
    output_size_bytes: Optional[int] = None
    workflow_name: Optional[str] = None
    query_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate execution result entity."""
        if not self.execution_id:
            raise ValueError("Execution ID is required")

    def mark_completed(self, result_data: Optional[Dict[str, Any]] = None, execution_time_ms: Optional[float] = None):
        """Mark execution as completed."""
        self.status = ExecutionStatus.COMPLETED
        self.result_data = result_data or {}
        self.execution_time_ms = execution_time_ms
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error_message: str, execution_time_ms: Optional[float] = None):
        """Mark execution as failed."""
        self.status = ExecutionStatus.FAILED
        self.error_message = error_message
        self.execution_time_ms = execution_time_ms
        self.completed_at = datetime.now(timezone.utc)

    def mark_cancelled(self, execution_time_ms: Optional[float] = None):
        """Mark execution as cancelled."""
        self.status = ExecutionStatus.CANCELLED
        self.execution_time_ms = execution_time_ms
        self.completed_at = datetime.now(timezone.utc)

    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.COMPLETED

    def has_error(self) -> bool:
        """Check if execution has an error."""
        return self.status == ExecutionStatus.FAILED and self.error_message is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "status": self.status.value,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "output_format": self.output_format,
            "output_size_bytes": self.output_size_bytes,
            "workflow_name": self.workflow_name,
            "query_id": self.query_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
