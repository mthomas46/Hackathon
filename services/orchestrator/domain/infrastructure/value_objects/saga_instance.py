"""Saga Instance Value Object"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

from .saga_status import SagaStatus


class SagaStep:
    """Represents a single step in a saga."""

    def __init__(
        self,
        step_id: str,
        service_name: str,
        operation: str,
        compensation_operation: Optional[str] = None,
        status: str = "pending"
    ):
        self.step_id = step_id
        self.service_name = service_name
        self.operation = operation
        self.compensation_operation = compensation_operation
        self.status = status
        self.executed_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None


class SagaInstance:
    """Value object representing a saga orchestration instance."""

    def __init__(
        self,
        saga_type: str,
        correlation_id: str,
        steps: List[SagaStep],
        saga_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._saga_id = saga_id or str(uuid4())
        self._saga_type = saga_type.strip()
        self._correlation_id = correlation_id.strip()
        self._steps = steps.copy()
        self._metadata = metadata or {}
        self._status = SagaStatus.PENDING
        self._created_at = datetime.utcnow()
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._error_message: Optional[str] = None
        self._current_step_index = 0

        self._validate()

    def _validate(self):
        """Validate saga instance data."""
        if not self._saga_type:
            raise ValueError("Saga type cannot be empty")

        if not self._correlation_id:
            raise ValueError("Correlation ID cannot be empty")

        if not self._steps:
            raise ValueError("Saga must have at least one step")

    @property
    def saga_id(self) -> str:
        """Get the saga ID."""
        return self._saga_id

    @property
    def saga_type(self) -> str:
        """Get the saga type."""
        return self._saga_type

    @property
    def correlation_id(self) -> str:
        """Get the correlation ID."""
        return self._correlation_id

    @property
    def status(self) -> SagaStatus:
        """Get the saga status."""
        return self._status

    @property
    def steps(self) -> List[SagaStep]:
        """Get the saga steps."""
        return self._steps.copy()

    @property
    def current_step(self) -> Optional[SagaStep]:
        """Get the current step."""
        if self._status == SagaStatus.STARTED and 0 <= self._current_step_index < len(self._steps):
            return self._steps[self._current_step_index]
        return None

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the saga metadata."""
        return self._metadata.copy()

    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp."""
        return self._created_at

    @property
    def started_at(self) -> Optional[datetime]:
        """Get the start timestamp."""
        return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get the completion timestamp."""
        return self._completed_at

    @property
    def error_message(self) -> Optional[str]:
        """Get the error message."""
        return self._error_message

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get the saga duration in seconds."""
        if self._started_at and self._completed_at:
            return (self._completed_at - self._started_at).total_seconds()
        elif self._started_at:
            return (datetime.utcnow() - self._started_at).total_seconds()
        return None

    def start(self):
        """Start the saga."""
        if self._status != SagaStatus.PENDING:
            raise ValueError(f"Cannot start saga in status: {self._status}")

        self._status = SagaStatus.STARTED
        self._started_at = datetime.utcnow()

    def complete_step(self, step_id: str):
        """Complete a specific step."""
        for step in self._steps:
            if step.step_id == step_id:
                step.status = "completed"
                step.completed_at = datetime.utcnow()
                break

    def fail_step(self, step_id: str, error_message: str):
        """Fail a specific step."""
        for step in self._steps:
            if step.step_id == step_id:
                step.status = "failed"
                step.error_message = error_message
                step.completed_at = datetime.utcnow()
                break

    def complete(self):
        """Complete the saga successfully."""
        self._status = SagaStatus.COMPLETED
        self._completed_at = datetime.utcnow()

    def fail(self, error_message: str):
        """Fail the saga."""
        self._status = SagaStatus.FAILED
        self._completed_at = datetime.utcnow()
        self._error_message = error_message

    def compensate(self):
        """Start compensation phase."""
        self._status = SagaStatus.COMPENSATING

    def abort(self):
        """Abort the saga."""
        self._status = SagaStatus.ABORTED
        self._completed_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "saga_id": self._saga_id,
            "saga_type": self._saga_type,
            "correlation_id": self._correlation_id,
            "status": self._status.value,
            "steps": [
                {
                    "step_id": step.step_id,
                    "service_name": step.service_name,
                    "operation": step.operation,
                    "compensation_operation": step.compensation_operation,
                    "status": step.status,
                    "executed_at": step.executed_at.isoformat() if step.executed_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "error_message": step.error_message
                }
                for step in self._steps
            ],
            "metadata": self._metadata,
            "created_at": self._created_at.isoformat(),
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "error_message": self._error_message,
            "duration_seconds": self.duration_seconds
        }

    def __repr__(self) -> str:
        return f"SagaInstance(saga_id='{self._saga_id}', type='{self._saga_type}', status={self._status})"
