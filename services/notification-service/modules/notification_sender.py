"""Notification sending and deduplication for notification service."""

import time
from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException


class NotificationSender:
    """Handles notification sending with deduplication and error handling."""

    def __init__(self, dedup_window: int = 600):
        """Initialize sender with deduplication window in seconds."""
        self._dedup_cache: Dict[str, float] = {}
        self._dedup_window = dedup_window

    async def send_notification(
        self,
        channel: str,
        target: str,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        labels: Optional[list[str]] = None
    ) -> Dict[str, str]:
        """Send a notification with deduplication."""

        # Check for duplicate notifications
        dedup_key = f"{target}|{title}|{hash(message)}"
        now = time.time()

        if self._dedup_cache.get(dedup_key, 0) > now - self._dedup_window:
            return {"status": "duplicate_suppressed"}

        # Mark as sent for deduplication
        self._dedup_cache[dedup_key] = now

        # Send the notification
        return await self._send_to_channel(
            channel.lower().strip(),
            target,
            title,
            message,
            metadata or {},
            labels or []
        )

    async def _send_to_channel(
        self,
        channel: str,
        target: str,
        title: str,
        message: str,
        metadata: Dict[str, Any],
        labels: list[str]
    ) -> Dict[str, str]:
        """Send notification to specific channel."""

        if channel == "webhook":
            return await self._send_webhook(target, title, message, metadata, labels)
        elif channel in ("slack", "email"):
            # Stub implementations - would integrate with actual providers
            return {"status": "queued", "channel": channel}
        else:
            return {"status": "queued", "channel": channel}

    async def _send_webhook(
        self,
        target: str,
        title: str,
        message: str,
        metadata: Dict[str, Any],
        labels: list[str]
    ) -> Dict[str, str]:
        """Send notification via webhook."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(target, json={
                    "title": title,
                    "message": message,
                    "metadata": metadata,
                    "labels": labels
                })
                response.raise_for_status()
                return {"status": "sent"}
        except Exception as e:
            # This would typically go to DLQ, but we handle it in the main endpoint
            raise HTTPException(status_code=502, detail=f"Webhook failed: {e}")

    def clear_dedup_cache(self) -> None:
        """Clear the deduplication cache."""
        self._dedup_cache.clear()


# Global instance
notification_sender = NotificationSender()
