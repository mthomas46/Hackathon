"""Notification domain entity."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Notification:
    """Domain entity representing a notification.

    Encapsulates all notification data and business rules.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    channel: str = ""
    target: str = ""
    title: str = ""
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    labels: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed
    retry_count: int = 0
    max_retries: int = 3
    deduplication_key: Optional[str] = None

    def mark_as_sent(self) -> None:
        """Mark notification as successfully sent."""
        self.status = "sent"
        self.sent_at = datetime.now(timezone.utc)

    def mark_as_failed(self, error_message: str = "") -> None:
        """Mark notification as failed."""
        self.status = "failed"
        self.retry_count += 1
        if error_message:
            self.metadata["last_error"] = error_message

    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        return self.retry_count < self.max_retries and self.status != "sent"

    def generate_deduplication_key(self) -> str:
        """Generate deduplication key for this notification."""
        if not self.deduplication_key:
            self.deduplication_key = f"{self.target}|{self.title}|{hash(self.message)}"
        return self.deduplication_key

    @property
    def is_expired(self) -> bool:
        """Check if notification is expired (for deduplication)."""
        if not self.sent_at:
            return False
        # Consider expired after 10 minutes
        return (datetime.now(timezone.utc) - self.sent_at).total_seconds() > 600

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "channel": self.channel,
            "target": self.target,
            "title": self.title,
            "message": self.message,
            "metadata": self.metadata,
            "labels": self.labels,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
            "retry_count": self.retry_count,
            "deduplication_key": self.deduplication_key,
        }
