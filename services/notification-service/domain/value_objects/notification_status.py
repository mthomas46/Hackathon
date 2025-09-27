"""Notification status value object."""

from enum import Enum
from typing import List


class NotificationStatus(Enum):
    """Enumeration of notification statuses."""

    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

    @classmethod
    def from_string(cls, value: str) -> 'NotificationStatus':
        """Create status from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.PENDING

    def is_terminal(self) -> bool:
        """Check if this is a terminal status (no further processing)."""
        return self in [self.SENT, self.CANCELLED, self.EXPIRED]

    def is_failure(self) -> bool:
        """Check if this status represents a failure."""
        return self in [self.FAILED, self.EXPIRED]

    def allows_retry(self) -> bool:
        """Check if this status allows retry attempts."""
        return self in [self.FAILED, self.RETRYING]

    @classmethod
    def get_active_statuses(cls) -> List['NotificationStatus']:
        """Get all active (non-terminal) statuses."""
        return [cls.PENDING, cls.SENDING, cls.RETRYING]

    @classmethod
    def get_terminal_statuses(cls) -> List['NotificationStatus']:
        """Get all terminal statuses."""
        return [cls.SENT, cls.FAILED, cls.CANCELLED, cls.EXPIRED]
