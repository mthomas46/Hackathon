"""Notification Service monitoring infrastructure for Frontend service.

Provides visualization and monitoring capabilities for notification service
owner resolution, notification delivery, and dead letter queue management.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.shared.utilities import utc_now
from .shared_utils import get_notification_service_url, get_frontend_clients


class NotificationServiceMonitor:
    """Monitor for notification service owner resolution and notification delivery."""

    def __init__(self):
        self._notifications = []
        self._owner_resolutions = []
        self._cache_ttl = 30  # Cache for 30 seconds

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = getattr(self, f"_{cache_key}_updated", None)
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_notification_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive notification service status."""
        if not force_refresh and self.is_cache_fresh("status"):
            return getattr(self, "_status_cache", {})

        try:
            clients = get_frontend_clients()
            notification_url = get_notification_service_url()

            # Get health status and DLQ
            health_response = await clients.get_json(f"{notification_url}/health")
            dlq_response = await clients.get_json(f"{notification_url}/dlq")

            status_data = {
                "health": health_response,
                "dlq": dlq_response,
                "notification_stats": self._calculate_notification_stats(),
                "recent_notifications": self._notifications[-10:] if self._notifications else [],  # Last 10 notifications
                "recent_owner_resolutions": self._owner_resolutions[-10:] if self._owner_resolutions else [],  # Last 10 resolutions
                "last_updated": utc_now().isoformat()
            }

            self._status_cache = status_data
            self._status_updated = utc_now()

            return status_data

        except Exception as e:
            return {
                "error": str(e),
                "health": {},
                "dlq": {},
                "notification_stats": {},
                "recent_notifications": [],
                "recent_owner_resolutions": [],
                "last_updated": utc_now().isoformat()
            }

    async def resolve_owners(self, owners: List[str]) -> Dict[str, Any]:
        """Resolve owners to their notification targets."""
        try:
            clients = get_frontend_clients()
            notification_url = get_notification_service_url()

            payload = {"owners": owners}
            response = await clients.post_json(f"{notification_url}/owners/resolve", payload)

            if response.get("resolved"):
                # Cache the resolution
                resolution_result = {
                    "id": f"resolution_{utc_now().isoformat()}",
                    "timestamp": utc_now().isoformat(),
                    "owners_requested": owners,
                    "resolved_targets": response["resolved"],
                    "resolution_count": len(response["resolved"]),
                    "response": response
                }

                self._owner_resolutions.insert(0, resolution_result)  # Add to front
                # Keep only last 50 resolutions
                if len(self._owner_resolutions) > 50:
                    self._owner_resolutions = self._owner_resolutions[:50]

                return {
                    "success": True,
                    "resolution_id": resolution_result["id"],
                    "resolved_targets": resolution_result["resolved_targets"],
                    "resolution_count": resolution_result["resolution_count"],
                    "response": response
                }

            return {
                "success": False,
                "error": "Owner resolution failed",
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }

    async def send_notification(self, channel: str, target: str, title: str, message: str, metadata: Optional[Dict[str, Any]] = None, labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send a notification through the service."""
        try:
            clients = get_frontend_clients()
            notification_url = get_notification_service_url()

            payload = {
                "channel": channel,
                "target": target,
                "title": title,
                "message": message,
                "metadata": metadata or {},
                "labels": labels or []
            }

            response = await clients.post_json(f"{notification_url}/notify", payload)

            # Cache the notification
            notification_result = {
                "id": f"notification_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "channel": channel,
                "target": target,
                "title": title,
                "message": message[:200] + "..." if len(message) > 200 else message,
                "metadata": metadata,
                "labels": labels,
                "success": response.get("success", False),
                "response": response
            }

            self._notifications.insert(0, notification_result)  # Add to front
            # Keep only last 50 notifications
            if len(self._notifications) > 50:
                self._notifications = self._notifications[:50]

            return {
                "success": True,
                "notification_id": notification_result["id"],
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }

    async def get_dlq_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get dead letter queue entries."""
        try:
            clients = get_frontend_clients()
            notification_url = get_notification_service_url()

            dlq_response = await clients.get_json(f"{notification_url}/dlq?limit={limit}")
            return dlq_response.get("items", [])

        except Exception as e:
            return []

    def _calculate_notification_stats(self) -> Dict[str, Any]:
        """Calculate statistics from cached notifications and resolutions."""
        if not self._notifications:
            return {
                "total_notifications": 0,
                "successful_notifications": 0,
                "failed_notifications": 0,
                "channels_used": [],
                "total_owner_resolutions": 0
            }

        total_notifications = len(self._notifications)
        successful_notifications = sum(1 for n in self._notifications if n.get("success"))
        failed_notifications = total_notifications - successful_notifications

        # Channel usage
        channels = set()
        for notification in self._notifications:
            if notification.get("channel"):
                channels.add(notification["channel"])

        total_resolutions = len(self._owner_resolutions)

        return {
            "total_notifications": total_notifications,
            "successful_notifications": successful_notifications,
            "failed_notifications": failed_notifications,
            "success_rate": round((successful_notifications / total_notifications) * 100, 1) if total_notifications > 0 else 0,
            "channels_used": list(channels),
            "total_owner_resolutions": total_resolutions
        }

    def get_notification_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent notification history."""
        return self._notifications[:limit]

    def get_owner_resolution_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent owner resolution history."""
        return self._owner_resolutions[:limit]


# Global instance
notification_service_monitor = NotificationServiceMonitor()
