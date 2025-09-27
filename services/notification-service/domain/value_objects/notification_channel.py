"""Notification channel value object."""

from enum import Enum
from typing import Optional


class NotificationChannel(Enum):
    """Enumeration of supported notification channels."""

    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    SMS = "sms"
    TEAMS = "teams"
    DISCORD = "discord"

    @classmethod
    def from_string(cls, value: str) -> Optional['NotificationChannel']:
        """Create channel from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def get_display_name(self) -> str:
        """Get human-readable display name."""
        display_names = {
            "email": "Email",
            "webhook": "Webhook",
            "slack": "Slack",
            "sms": "SMS",
            "teams": "Microsoft Teams",
            "discord": "Discord",
        }
        return display_names.get(self.value, self.value.title())

    def requires_target_validation(self) -> bool:
        """Check if this channel requires target validation."""
        return self in [self.EMAIL, self.WEBHOOK, self.SLACK, self.SMS, self.TEAMS]

    def supports_attachments(self) -> bool:
        """Check if this channel supports attachments."""
        return self in [self.EMAIL, self.SLACK, self.TEAMS, self.DISCORD]
