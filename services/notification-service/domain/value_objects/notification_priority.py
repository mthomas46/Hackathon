"""Notification priority value object."""

from enum import Enum


class NotificationPriority(Enum):
    """Enumeration of notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

    @classmethod
    def from_string(cls, value: str) -> 'NotificationPriority':
        """Create priority from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.NORMAL  # Default to normal

    def get_retry_attempts(self) -> int:
        """Get number of retry attempts based on priority."""
        retry_map = {
            "low": 1,
            "normal": 2,
            "high": 3,
            "urgent": 4,
            "critical": 5,
        }
        return retry_map.get(self.value, 2)

    def get_timeout_seconds(self) -> int:
        """Get timeout in seconds based on priority."""
        timeout_map = {
            "low": 30,
            "normal": 20,
            "high": 15,
            "urgent": 10,
            "critical": 5,
        }
        return timeout_map.get(self.value, 20)
