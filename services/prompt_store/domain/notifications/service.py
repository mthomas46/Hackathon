"""Notifications service.

Contains business logic for webhook management, event notification delivery, and monitoring.
"""

import asyncio
import aiohttp
import hmac
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from services.prompt_store.domain.notifications.repository import (
    NotificationsRepository, WebhookEntity, NotificationEntity
)
from services.prompt_store.infrastructure.cache import prompt_store_cache
from services.shared.utilities import generate_id, utc_now
from services.shared.clients import ServiceClients


class NotificationsService:
    """Service for managing notifications and webhooks."""

    def __init__(self):
        self.repo = NotificationsRepository()
        self.clients = ServiceClients()

    # Webhook management
    async def register_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new webhook."""

        # Validate webhook data
        self._validate_webhook_data(webhook_data)

        # Create webhook
        webhook = self.repo.create_webhook(webhook_data)

        # Invalidate cache
        await prompt_store_cache.delete("webhooks:all")
        await prompt_store_cache.delete("webhooks:active")

        return {
            "webhook_id": webhook.id,
            "name": webhook.name,
            "url": webhook.url,
            "events": webhook.events,
            "is_active": webhook.is_active,
            "created_at": webhook.created_at.isoformat()
        }

    def get_webhook(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook details."""
        webhook = self.repo.get_webhook(webhook_id)
        if not webhook:
            return None

        return webhook.to_dict()

    def list_webhooks(self, active_only: bool = False) -> Dict[str, Any]:
        """List all webhooks."""
        webhooks = self.repo.get_all_webhooks(active_only)

        return {
            "webhooks": [webhook.to_dict() for webhook in webhooks],
            "count": len(webhooks),
            "active_only": active_only
        }

    async def update_webhook(self, webhook_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update webhook configuration."""

        # Validate updates
        if "events" in updates:
            self._validate_event_types(updates["events"])

        # Update webhook
        success = self.repo.update_webhook(webhook_id, updates)
        if not success:
            raise ValueError(f"Webhook {webhook_id} not found")

        # Invalidate cache
        await prompt_store_cache.delete("webhooks:all")
        await prompt_store_cache.delete("webhooks:active")

        return {
            "webhook_id": webhook_id,
            "updated": True,
            "updated_at": utc_now().isoformat()
        }

    async def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook."""
        success = self.repo.delete_webhook(webhook_id)
        if not success:
            raise ValueError(f"Webhook {webhook_id} not found or already deleted")

        # Invalidate cache
        await prompt_store_cache.delete("webhooks:all")
        await prompt_store_cache.delete("webhooks:active")

        return {
            "webhook_id": webhook_id,
            "deleted": True,
            "deleted_at": utc_now().isoformat()
        }

    # Event notification
    async def notify_event(self, event_type: str, event_data: Dict[str, Any],
                          owners: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send notifications for an event using both webhooks and notification service.

        Args:
            event_type: Type of event (e.g., 'prompt.created', 'ab_test.completed')
            event_data: Event data payload
            owners: Optional list of owners to notify via notification service

        Returns:
            Dict with notification results
        """

        results = {
            "event_type": event_type,
            "webhook_notifications": {"sent": 0, "failed": 0, "total": 0},
            "service_notifications": {"sent": 0, "failed": 0},
            "total_sent": 0,
            "total_failed": 0
        }

        # 1. Send via webhooks (existing functionality)
        webhooks = self.repo.get_active_webhooks_for_event(event_type)
        results["webhook_notifications"]["total"] = len(webhooks)

        webhook_sent = 0
        webhook_failed = 0

        for webhook in webhooks:
            try:
                # Create notification record
                notification = self.repo.create_notification(
                    event_type, event_data, "webhook", webhook.id
                )

                # Send webhook asynchronously
                asyncio.create_task(self._send_webhook_notification(webhook, notification))

                webhook_sent += 1

            except Exception as e:
                print(f"Failed to send notification to webhook {webhook.id}: {str(e)}")
                webhook_failed += 1

        results["webhook_notifications"]["sent"] = webhook_sent
        results["webhook_notifications"]["failed"] = webhook_failed

        # 2. Send via notification service if owners are specified
        if owners:
            try:
                # Create human-readable message based on event type
                message = self._create_notification_message(event_type, event_data)

                service_result = await self.send_notification_via_service(
                    event_type=event_type,
                    message=message,
                    owners=owners,
                    metadata={
                        "event_data": event_data,
                        "source": "prompt_store",
                        "timestamp": utc_now().isoformat()
                    }
                )

                if service_result["status"] == "sent":
                    results["service_notifications"]["sent"] = 1
                else:
                    results["service_notifications"]["failed"] = 1

            except Exception as e:
                print(f"Failed to send notification via service: {str(e)}")
                results["service_notifications"]["failed"] = 1

        # Calculate totals
        results["total_sent"] = results["webhook_notifications"]["sent"] + results["service_notifications"]["sent"]
        results["total_failed"] = results["webhook_notifications"]["failed"] + results["service_notifications"]["failed"]

        return results

    def _create_notification_message(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """Create a human-readable notification message based on event type."""
        if event_type == "prompt.created":
            prompt_id = event_data.get("id", "unknown")
            prompt_name = event_data.get("name", "unknown")
            return f"New prompt '{prompt_name}' created (ID: {prompt_id})"

        elif event_type == "prompt.updated":
            prompt_id = event_data.get("id", "unknown")
            prompt_name = event_data.get("name", "unknown")
            version = event_data.get("version", "unknown")
            return f"Prompt '{prompt_name}' updated to version {version} (ID: {prompt_id})"

        elif event_type == "prompt.lifecycle_changed":
            prompt_id = event_data.get("id", "unknown")
            prompt_name = event_data.get("name", "unknown")
            new_status = event_data.get("status", "unknown")
            return f"Prompt '{prompt_name}' status changed to '{new_status}' (ID: {prompt_id})"

        elif event_type == "ab_test.started":
            test_id = event_data.get("id", "unknown")
            test_name = event_data.get("name", "unknown")
            return f"A/B test '{test_name}' started (ID: {test_id})"

        elif event_type == "ab_test.completed":
            test_id = event_data.get("id", "unknown")
            test_name = event_data.get("name", "unknown")
            winner = event_data.get("winner", "unknown")
            return f"A/B test '{test_name}' completed. Winner: {winner} (ID: {test_id})"

        elif event_type == "bulk_operation.completed":
            operation_id = event_data.get("id", "unknown")
            operation_type = event_data.get("operation_type", "unknown")
            success_count = event_data.get("successful_items", 0)
            total_count = event_data.get("total_items", 0)
            return f"Bulk operation '{operation_type}' completed: {success_count}/{total_count} items processed (ID: {operation_id})"

        else:
            return f"Prompt Store event: {event_type}"

    async def send_notification_via_service(self, event_type: str, message: str,
                                          owners: List[str], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send notification via the centralized notification service.

        Args:
            event_type: Type of event for categorization
            message: Human-readable message
            owners: List of owner names to resolve and notify
            metadata: Additional context data

        Returns:
            Dict with notification results
        """
        try:
            # Prepare notification payload
            notification_payload = {
                "channel": "prompt_store",
                "event_type": event_type,
                "message": message,
                "owners": owners,
                "metadata": metadata or {},
                "source": "prompt_store"
            }

            # Send via notification service
            response = await self.clients.send_notification(notification_payload)

            if response.get("success"):
                return {
                    "status": "sent",
                    "notification_id": response.get("notification_id"),
                    "message": "Notification sent successfully",
                    "owners_notified": len(owners)
                }
            else:
                return {
                    "status": "failed",
                    "error": response.get("error", "Unknown error"),
                    "message": "Failed to send notification via service"
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Exception occurred while sending notification"
            }

    async def send_bulk_notifications(self, notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send multiple notifications in batch via notification service.

        Args:
            notifications: List of notification payloads

        Returns:
            Dict with batch results
        """
        results = []
        sent_count = 0
        failed_count = 0

        for notification in notifications:
            result = await self.send_notification_via_service(
                event_type=notification.get("event_type", "bulk_notification"),
                message=notification.get("message", ""),
                owners=notification.get("owners", []),
                metadata=notification.get("metadata", {})
            )

            results.append(result)
            if result["status"] == "sent":
                sent_count += 1
            else:
                failed_count += 1

        return {
            "total_notifications": len(notifications),
            "sent": sent_count,
            "failed": failed_count,
            "results": results
        }

    async def process_pending_notifications(self) -> Dict[str, Any]:
        """Process pending notifications (retry failed ones, send new ones)."""

        pending_notifications = self.repo.get_pending_notifications(limit=100)
        processed = 0
        delivered = 0
        failed = 0

        for notification in pending_notifications:
            try:
                if notification.recipient_type == "webhook":
                    webhook = self.repo.get_webhook(notification.recipient_id)
                    if webhook and webhook.is_active:
                        await self._send_webhook_notification(webhook, notification)
                        delivered += 1
                    else:
                        # Mark as failed if webhook doesn't exist or is inactive
                        self.repo.update_notification_status(
                            notification.id, "failed", "Webhook not found or inactive"
                        )
                        failed += 1
                else:
                    # Handle other recipient types (email, etc.)
                    # For now, mark as delivered
                    self.repo.update_notification_status(notification.id, "delivered")
                    delivered += 1

                processed += 1

            except Exception as e:
                self.repo.update_notification_status(
                    notification.id, "failed", str(e)
                )
                failed += 1

        return {
            "processed": processed,
            "delivered": delivered,
            "failed": failed,
            "remaining_pending": len(pending_notifications) - processed
        }

    def get_notification_stats(self) -> Dict[str, Any]:
        """Get comprehensive notification statistics."""
        return self.repo.get_notification_stats()

    def cleanup_old_notifications(self, days_old: int = 30) -> Dict[str, Any]:
        """Clean up old notification records."""
        deleted_count = self.repo.cleanup_old_notifications(days_old)

        return {
            "cleanup_days": days_old,
            "records_deleted": deleted_count,
            "cleanup_at": utc_now().isoformat()
        }

    # Internal helper methods
    def _validate_webhook_data(self, data: Dict[str, Any]) -> None:
        """Validate webhook registration data."""
        required_fields = ["name", "url", "events"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        if not isinstance(data["events"], list) or not data["events"]:
            raise ValueError("Events must be a non-empty list")

        self._validate_event_types(data["events"])

        # Validate URL format (basic check)
        if not data["url"].startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

    def _validate_event_types(self, events: List[str]) -> None:
        """Validate that event types are supported."""
        invalid_events = [event for event in events if event not in self.repo.VALID_EVENT_TYPES]
        if invalid_events:
            raise ValueError(f"Invalid event types: {', '.join(invalid_events)}")

    async def _send_webhook_notification(self, webhook: WebhookEntity,
                                       notification: NotificationEntity) -> None:
        """Send a notification to a webhook endpoint."""

        payload = {
            "id": notification.id,
            "event_type": notification.event_type,
            "event_data": notification.event_data,
            "timestamp": notification.created_at.isoformat(),
            "webhook_id": webhook.id
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "PromptStore-Webhook/1.0",
            "X-Webhook-ID": webhook.id,
            "X-Event-Type": notification.event_type
        }

        # Add signature if secret is configured
        if webhook.secret:
            signature = self._generate_webhook_signature(
                webhook.secret, payload, notification.created_at.isoformat()
            )
            headers["X-Signature"] = signature

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=webhook.timeout_seconds)) as session:
                async with session.post(webhook.url, json=payload, headers=headers) as response:
                    if response.status >= 200 and response.status < 300:
                        # Success
                        self.repo.update_notification_status(notification.id, "delivered")
                    else:
                        # HTTP error
                        error_text = await response.text()
                        self.repo.update_notification_status(
                            notification.id, "failed",
                            f"HTTP {response.status}: {error_text}"
                        )

        except asyncio.TimeoutError:
            self.repo.update_notification_status(
                notification.id, "failed", "Request timeout"
            )
        except Exception as e:
            self.repo.update_notification_status(
                notification.id, "failed", f"Request failed: {str(e)}"
            )

    def _generate_webhook_signature(self, secret: str, payload: Dict[str, Any],
                                  timestamp: str) -> str:
        """Generate HMAC signature for webhook payload."""
        payload_str = f"{timestamp}.{str(payload)}"
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    # Convenience methods for triggering notifications from other domains
    async def notify_prompt_created(self, prompt_id: str, prompt_data: Dict[str, Any]) -> None:
        """Notify about prompt creation."""
        await self.notify_event("prompt.created", {
            "prompt_id": prompt_id,
            "prompt_data": prompt_data
        })

    async def notify_prompt_updated(self, prompt_id: str, changes: Dict[str, Any]) -> None:
        """Notify about prompt updates."""
        await self.notify_event("prompt.updated", {
            "prompt_id": prompt_id,
            "changes": changes
        })

    async def notify_lifecycle_changed(self, prompt_id: str, old_status: str,
                                     new_status: str, reason: str = "") -> None:
        """Notify about lifecycle status changes."""
        await self.notify_event("prompt.lifecycle_changed", {
            "prompt_id": prompt_id,
            "old_status": old_status,
            "new_status": new_status,
            "reason": reason
        })

    async def notify_ab_test_completed(self, test_id: str, results: Dict[str, Any]) -> None:
        """Notify about A/B test completion."""
        await self.notify_event("ab_test.completed", {
            "test_id": test_id,
            "results": results
        })

    async def notify_bulk_operation_completed(self, operation_id: str,
                                            operation_type: str, results: Dict[str, Any]) -> None:
        """Notify about bulk operation completion."""
        await self.notify_event(f"bulk_operation.{operation_type}", {
            "operation_id": operation_id,
            "results": results
        })
