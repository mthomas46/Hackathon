"""Action Result Value Object"""

from typing import Any, Optional
from datetime import datetime
from enum import Enum


class ActionStatus(Enum):
    """Status of an action execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ActionResult:
    """Value object representing the result of an action execution."""

    def __init__(
        self,
        action_id: str,
        status: ActionStatus,
        output: Optional[Any] = None,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ):
        self._action_id = action_id
        self._status = status
        self._output = output
        self._error_message = error_message
        self._execution_time_ms = execution_time_ms
        self._started_at = started_at or datetime.utcnow()
        self._completed_at = completed_at

        if status in [ActionStatus.COMPLETED, ActionStatus.FAILED, ActionStatus.CANCELLED]:
            self._completed_at = completed_at or datetime.utcnow()

    @property
    def action_id(self) -> str:
        """Get the action ID."""
        return self._action_id

    @property
    def status(self) -> ActionStatus:
        """Get the action status."""
        return self._status

    @property
    def output(self) -> Optional[Any]:
        """Get the action output."""
        return self._output

    @property
    def error_message(self) -> Optional[str]:
        """Get the error message if any."""
        return self._error_message

    @property
    def execution_time_ms(self) -> Optional[int]:
        """Get the execution time in milliseconds."""
        return self._execution_time_ms

    @property
    def started_at(self) -> datetime:
        """Get the start time."""
        return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get the completion time."""
        return self._completed_at

    @property
    def is_successful(self) -> bool:
        """Check if the action was successful."""
        return self._status == ActionStatus.COMPLETED

    @property
    def has_error(self) -> bool:
        """Check if the action has an error."""
        return self._status == ActionStatus.FAILED and self._error_message is not None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "action_id": self._action_id,
            "status": self._status.value,
            "output": self._output,
            "error_message": self._error_message,
            "execution_time_ms": self._execution_time_ms,
            "started_at": self._started_at.isoformat(),
            "completed_at": self._completed_at.isoformat() if self._completed_at else None
        }

    @classmethod
    def success(cls, action_id: str, output: Any, execution_time_ms: int) -> 'ActionResult':
        """Create a successful action result."""
        return cls(
            action_id=action_id,
            status=ActionStatus.COMPLETED,
            output=output,
            execution_time_ms=execution_time_ms
        )

    @classmethod
    def failure(cls, action_id: str, error_message: str, execution_time_ms: int) -> 'ActionResult':
        """Create a failed action result."""
        return cls(
            action_id=action_id,
            status=ActionStatus.FAILED,
            error_message=error_message,
            execution_time_ms=execution_time_ms
        )

    @classmethod
    def skipped(cls, action_id: str) -> 'ActionResult':
        """Create a skipped action result."""
        return cls(action_id=action_id, status=ActionStatus.SKIPPED)
