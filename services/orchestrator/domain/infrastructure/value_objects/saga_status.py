"""Saga Status Value Object"""

from enum import Enum


class SagaStatus(Enum):
    """Enumeration of possible saga orchestration statuses."""

    PENDING = "pending"
    STARTED = "started"
    COMPENSATING = "compensating"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"

    @property
    def is_active(self) -> bool:
        """Check if saga is in active state."""
        return self in (SagaStatus.STARTED, SagaStatus.COMPENSATING)

    @property
    def is_final(self) -> bool:
        """Check if saga is in final state."""
        return self in (SagaStatus.COMPLETED, SagaStatus.FAILED, SagaStatus.ABORTED)

    @property
    def is_successful(self) -> bool:
        """Check if saga completed successfully."""
        return self == SagaStatus.COMPLETED

    @property
    def can_compensate(self) -> bool:
        """Check if saga can enter compensation phase."""
        return self == SagaStatus.STARTED

    def __str__(self) -> str:
        return self.value
