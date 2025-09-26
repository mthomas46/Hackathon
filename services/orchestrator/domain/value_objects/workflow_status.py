"""Workflow status value object."""

from enum import Enum


class WorkflowStatus(Enum):
    """Enumeration of possible workflow statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

    def is_terminal(self) -> bool:
        """Check if this status represents a terminal state."""
        return self in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]

    def is_active(self) -> bool:
        """Check if this status represents an active (non-terminal) state."""
        return self in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]

    def can_transition_to(self, new_status: 'WorkflowStatus') -> bool:
        """Check if transition from current status to new status is valid."""
        # Define valid transitions
        transitions = {
            WorkflowStatus.PENDING: [WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED],
            WorkflowStatus.RUNNING: [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED, WorkflowStatus.PAUSED],
            WorkflowStatus.PAUSED: [WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED],
            WorkflowStatus.COMPLETED: [],  # Terminal state
            WorkflowStatus.FAILED: [],     # Terminal state
            WorkflowStatus.CANCELLED: []   # Terminal state
        }

        return new_status in transitions.get(self, [])
