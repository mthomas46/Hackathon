"""Notifications handlers for Doc Store service."""

from typing import Any, Dict


class NotificationsHandlers:
    """Stub implementation for notifications handlers."""
    
    async def send_notification(self, *args, **kwargs) -> Dict[str, Any]:
        """Send notification."""
        return {
            "status": "not_implemented",
            "message": "Notifications feature coming soon"
        }
    
    async def get_notification_settings(self, *args, **kwargs) -> Dict[str, Any]:
        """Get notification settings."""
        return {
            "status": "not_implemented",
            "message": "Notifications feature coming soon"
        }

