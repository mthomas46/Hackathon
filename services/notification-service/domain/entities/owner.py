"""Owner domain entity."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Owner:
    """Domain entity representing a notification owner/target.

    Encapsulates owner information and notification preferences.
    """

    name: str = ""
    email: Optional[str] = None
    webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    phone_number: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

    @property
    def primary_channel(self) -> Optional[str]:
        """Get the primary notification channel for this owner."""
        if self.email and self.preferences.get("email_enabled", True):
            return "email"
        elif self.webhook_url and self.preferences.get("webhook_enabled", True):
            return "webhook"
        elif self.slack_channel and self.preferences.get("slack_enabled", True):
            return "slack"
        elif self.phone_number and self.preferences.get("sms_enabled", True):
            return "sms"
        return None

    def get_target_for_channel(self, channel: str) -> Optional[str]:
        """Get the target address for a specific channel."""
        channel_map = {
            "email": self.email,
            "webhook": self.webhook_url,
            "slack": self.slack_channel,
            "sms": self.phone_number,
        }
        return channel_map.get(channel)

    def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """Update notification preferences."""
        self.preferences.update(new_preferences)
        self.last_updated = datetime.now(timezone.utc)

    def is_channel_enabled(self, channel: str) -> bool:
        """Check if a notification channel is enabled for this owner."""
        return self.preferences.get(f"{channel}_enabled", True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "email": self.email,
            "webhook_url": self.webhook_url,
            "slack_channel": self.slack_channel,
            "phone_number": self.phone_number,
            "preferences": self.preferences,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "is_active": self.is_active,
        }
