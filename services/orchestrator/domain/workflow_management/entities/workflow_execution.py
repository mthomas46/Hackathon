"""Workflow Execution Entity"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..value_objects.workflow_id import WorkflowId
from ..value_objects.execution_id import ExecutionId
from ..value_objects.action_result import ActionResult


class WorkflowExecutionStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowExecution:
    """Entity representing a workflow execution instance."""

    execution_id: ExecutionId = field(default_factory=ExecutionId.generate)
    workflow_id: WorkflowId = None
    status: WorkflowExecutionStatus = WorkflowExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, ActionResult] = field(default_factory=dict)
    error_message: Optional[str] = None
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None

    def __post_init__(self):
        """Validate execution after initialization."""
        if self.workflow_id is None:
            raise ValueError("Workflow ID is required")

    def start(self, parameters: Dict[str, Any], correlation_id: Optional[str] = None, trace_id: Optional[str] = None):
        """Start the workflow execution."""
        if self.status != WorkflowExecutionStatus.PENDING:
            raise ValueError(f"Cannot start execution in {self.status.value} status")

        self.status = WorkflowExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.parameters = parameters.copy()
        self.correlation_id = correlation_id
        self.trace_id = trace_id

    def complete(self):
        """Mark the execution as completed."""
        if self.status not in [WorkflowExecutionStatus.RUNNING, WorkflowExecutionStatus.PENDING]:
            raise ValueError(f"Cannot complete execution in {self.status.value} status")

        self.status = WorkflowExecutionStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def fail(self, error_message: str):
        """Mark the execution as failed."""
        if self.status not in [WorkflowExecutionStatus.RUNNING, WorkflowExecutionStatus.PENDING]:
            raise ValueError(f"Cannot fail execution in {self.status.value} status")

        self.status = WorkflowExecutionStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def cancel(self):
        """Cancel the execution."""
        if self.status in [WorkflowExecutionStatus.COMPLETED, WorkflowExecutionStatus.FAILED]:
            raise ValueError(f"Cannot cancel execution in {self.status.value} status")

        self.status = WorkflowExecutionStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    def add_action_result(self, result: ActionResult):
        """Add an action result to the execution."""
        self.results[result.action_id] = result

    def get_action_result(self, action_id: str) -> Optional[ActionResult]:
        """Get an action result by action ID."""
        return self.results.get(action_id)

    def get_successful_actions(self) -> List[str]:
        """Get list of action IDs that completed successfully."""
        return [action_id for action_id, result in self.results.items() if result.is_successful]

    def get_failed_actions(self) -> List[str]:
        """Get list of action IDs that failed."""
        return [action_id for action_id, result in self.results.items() if result.has_error]

    def get_pending_actions(self) -> List[str]:
        """Get list of action IDs that are pending (not yet executed)."""
        # This would need to be implemented based on the workflow definition
        # For now, return empty list as this requires workflow context
        return []

    @property
    def duration_ms(self) -> Optional[int]:
        """Get the execution duration in milliseconds."""
        if not self.started_at or not self.completed_at:
            return None
        return int((self.completed_at - self.started_at).total_seconds() * 1000)

    @property
    def is_completed(self) -> bool:
        """Check if the execution is completed."""
        return self.status in [WorkflowExecutionStatus.COMPLETED, WorkflowExecutionStatus.FAILED, WorkflowExecutionStatus.CANCELLED]

    @property
    def is_successful(self) -> bool:
        """Check if the execution was successful."""
        return self.status == WorkflowExecutionStatus.COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "execution_id": self.execution_id.value,
            "workflow_id": self.workflow_id.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parameters": self.parameters,
            "results": {k: v.to_dict() for k, v in self.results.items()},
            "error_message": self.error_message,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "duration_ms": self.duration_ms
        }
