"""Dead Letter Queue domain entity."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class DeadLetterQueue:
    """Domain entity representing a dead letter queue entry.

    Stores notifications that failed delivery after all retries.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    notification_id: str = ""
    owner_name: str = ""
    channel: str = ""
    target: str = ""
    title: str = ""
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    failure_reason: str = ""
    failure_count: int = 0
    first_failure_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_failure_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    retry_eligible: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def record_failure(self, reason: str) -> None:
        """Record a delivery failure."""
        self.failure_count += 1
        self.failure_reason = reason
        self.last_failure_at = datetime.now(timezone.utc)

    def mark_retry_eligible(self) -> None:
        """Mark this entry as eligible for retry."""
        self.retry_eligible = True

    def mark_resolved(self) -> None:
        """Mark this entry as resolved."""
        self.resolved = True
        self.resolved_at = datetime.now(timezone.utc)

    @property
    def is_expired(self) -> bool:
        """Check if DLQ entry is expired (older than 30 days)."""
        if self.resolved:
            return False
        days_since_first_failure = (datetime.now(timezone.utc) - self.first_failure_at).days
        return days_since_first_failure > 30

    @property
    def time_since_last_failure(self) -> float:
        """Get time in seconds since last failure."""
        return (datetime.now(timezone.utc) - self.last_failure_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "notification_id": self.notification_id,
            "owner_name": self.owner_name,
            "channel": self.channel,
            "target": self.target,
            "title": self.title,
            "message": self.message,
            "metadata": self.metadata,
            "failure_reason": self.failure_reason,
            "failure_count": self.failure_count,
            "first_failure_at": self.first_failure_at.isoformat(),
            "last_failure_at": self.last_failure_at.isoformat(),
            "retry_eligible": self.retry_eligible,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
