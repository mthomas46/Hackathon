"""Workflow Domain Entities.

Core domain entities for workflow management and execution.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from uuid import uuid4


class WorkflowStatus(Enum):
    """Enumeration of workflow execution statuses."""

    CREATED = "created"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class Workflow:
    """Domain entity representing a workflow definition."""

    name: str
    description: Optional[str] = None
    workflow_type: str = "standard"
    parameters: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    required_services: List[str] = field(default_factory=list)
    estimated_duration_ms: Optional[int] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate workflow entity."""
        if not self.name or not self.name.strip():
            raise ValueError("Workflow name cannot be empty")
        if not self.steps:
            self.steps = []

    def get_step_count(self) -> int:
        """Get total number of steps."""
        return len(self.steps)

    def requires_service(self, service_name: str) -> bool:
        """Check if workflow requires a specific service."""
        return service_name in self.required_services

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "workflow_type": self.workflow_type,
            "parameters": self.parameters,
            "steps": self.steps,
            "required_services": self.required_services,
            "estimated_duration_ms": self.estimated_duration_ms,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class WorkflowExecution:
    """Domain entity representing a workflow execution instance."""

    workflow_id: str
    workflow_name: str
    parameters: Dict[str, Any]
    status: WorkflowStatus = WorkflowStatus.CREATED
    user_id: Optional[str] = None
    execution_context: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate workflow execution entity."""
        if not self.workflow_id:
            raise ValueError("Workflow ID is required")
        if self.workflow_name and not self.workflow_name.strip():
            raise ValueError("Workflow name cannot be empty")

    def start_execution(self):
        """Mark execution as started."""
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.updated_at = self.started_at

    def complete_execution(self, results: Optional[Dict[str, Any]] = None):
        """Mark execution as completed."""
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.progress = 100.0
        if results:
            self.results.update(results)
        self.updated_at = self.completed_at

    def fail_execution(self, error_message: str):
        """Mark execution as failed."""
        self.status = WorkflowStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at

    def update_progress(self, progress: float, context: Optional[Dict[str, Any]] = None):
        """Update execution progress."""
        self.progress = max(0.0, min(100.0, progress))
        if context:
            self.execution_context.update(context)
        self.updated_at = datetime.now(timezone.utc)

    def get_execution_time_ms(self) -> Optional[float]:
        """Get total execution time in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None

    def is_completed(self) -> bool:
        """Check if execution is completed (success or failure)."""
        return self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "parameters": self.parameters,
            "status": self.status.value,
            "user_id": self.user_id,
            "execution_context": self.execution_context,
            "results": self.results,
            "error_message": self.error_message,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
