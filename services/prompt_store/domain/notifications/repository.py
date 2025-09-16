"""Notifications repository.

Handles data access operations for webhooks, event notifications, and delivery tracking.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from services.prompt_store.db.queries import execute_query
from services.prompt_store.core.entities import BaseEntity
from services.shared.utilities import generate_id, utc_now


class WebhookEntity(BaseEntity):
    """Webhook entity for external integrations."""

    def __init__(self):
        super().__init__()
        self.name: str = ""
        self.url: str = ""
        self.events: List[str] = []
        self.secret: Optional[str] = None
        self.is_active: bool = True
        self.retry_count: int = 3
        self.timeout_seconds: int = 30
        self.created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert webhook to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "events": self.events,
            "secret": self.secret,
            "is_active": self.is_active,
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookEntity':
        """Create webhook from dictionary."""
        webhook = cls()
        webhook.id = data.get("id")
        webhook.name = data["name"]
        webhook.url = data["url"]
        webhook.events = data.get("events", [])
        webhook.secret = data.get("secret")
        webhook.is_active = data.get("is_active", True)
        webhook.retry_count = data.get("retry_count", 3)
        webhook.timeout_seconds = data.get("timeout_seconds", 30)
        webhook.created_by = data.get("created_by", "")
        if "created_at" in data:
            webhook.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "updated_at" in data:
            webhook.updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        return webhook


class NotificationEntity(BaseEntity):
    """Notification event entity."""

    def __init__(self):
        super().__init__()
        self.event_type: str = ""
        self.event_data: Dict[str, Any] = {}
        self.recipient_type: str = "webhook"  # webhook, email, etc.
        self.recipient_id: str = ""
        self.status: str = "pending"  # pending, delivered, failed
        self.delivered_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "recipient_type": self.recipient_type,
            "recipient_id": self.recipient_id,
            "status": self.status,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationEntity':
        """Create notification from dictionary."""
        notification = cls()
        notification.id = data.get("id")
        notification.event_type = data["event_type"]
        notification.event_data = data.get("event_data", {})
        notification.recipient_type = data.get("recipient_type", "webhook")
        notification.recipient_id = data["recipient_id"]
        notification.status = data.get("status", "pending")
        if "delivered_at" in data and data["delivered_at"]:
            notification.delivered_at = datetime.fromisoformat(data["delivered_at"].replace('Z', '+00:00'))
        notification.error_message = data.get("error_message")
        notification.retry_count = data.get("retry_count", 0)
        if "created_at" in data:
            notification.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "updated_at" in data:
            notification.updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        return notification


class NotificationsRepository:
    """Repository for notification operations."""

    VALID_EVENT_TYPES = {
        "prompt.created", "prompt.updated", "prompt.deleted",
        "prompt.lifecycle_changed", "prompt.version_created",
        "ab_test.created", "ab_test.completed", "ab_test.updated",
        "bulk_operation.started", "bulk_operation.completed", "bulk_operation.failed",
        "relationship.created", "relationship.updated", "relationship.deleted",
        "refinement.started", "refinement.completed", "refinement.failed"
    }

    def __init__(self):
        self.webhooks_table = "webhooks"
        self.notifications_table = "notifications"
        self.deliveries_table = "webhook_deliveries"

    # Webhook CRUD operations
    def create_webhook(self, webhook_data: Dict[str, Any]) -> WebhookEntity:
        """Create a new webhook."""

        webhook = WebhookEntity()
        webhook.id = generate_id()
        webhook.name = webhook_data["name"]
        webhook.url = webhook_data["url"]
        webhook.events = webhook_data["events"]
        webhook.secret = webhook_data.get("secret")
        webhook.is_active = webhook_data.get("is_active", True)
        webhook.retry_count = webhook_data.get("retry_count", 3)
        webhook.timeout_seconds = webhook_data.get("timeout_seconds", 30)
        webhook.created_by = webhook_data.get("created_by", "system")

        query = f"""
            INSERT INTO {self.webhooks_table}
            (id, name, url, events, secret, is_active, retry_count, timeout_seconds, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        execute_query(query, (
            webhook.id, webhook.name, webhook.url, json.dumps(webhook.events),
            webhook.secret, webhook.is_active, webhook.retry_count,
            webhook.timeout_seconds, webhook.created_by,
            webhook.created_at.isoformat(), webhook.updated_at.isoformat()
        ), fetch_all=False)

        return webhook

    def get_webhook(self, webhook_id: str) -> Optional[WebhookEntity]:
        """Get webhook by ID."""
        query = f"""
            SELECT id, name, url, events, secret, is_active, retry_count, timeout_seconds,
                   created_by, created_at, updated_at
            FROM {self.webhooks_table}
            WHERE id = ?
        """

        row = execute_query(query, (webhook_id,), fetch_one=True)
        if not row:
            return None

        # Parse JSON fields
        row["events"] = json.loads(row["events"]) if row["events"] else []
        return WebhookEntity.from_dict(row)

    def get_active_webhooks_for_event(self, event_type: str) -> List[WebhookEntity]:
        """Get all active webhooks that should receive a specific event type."""
        query = f"""
            SELECT id, name, url, events, secret, is_active, retry_count, timeout_seconds,
                   created_by, created_at, updated_at
            FROM {self.webhooks_table}
            WHERE is_active = 1 AND events LIKE ?
        """

        rows = execute_query(query, (f"%{event_type}%",), fetch_all=True)

        webhooks = []
        for row in rows:
            row["events"] = json.loads(row["events"]) if row["events"] else []
            # Double-check that this webhook should receive this event
            if event_type in row["events"]:
                webhooks.append(WebhookEntity.from_dict(row))

        return webhooks

    def get_all_webhooks(self, active_only: bool = False) -> List[WebhookEntity]:
        """Get all webhooks."""
        query = f"""
            SELECT id, name, url, events, secret, is_active, retry_count, timeout_seconds,
                   created_by, created_at, updated_at
            FROM {self.webhooks_table}
        """
        if active_only:
            query += " WHERE is_active = 1"

        query += " ORDER BY created_at DESC"

        rows = execute_query(query, fetch_all=True)

        webhooks = []
        for row in rows:
            row["events"] = json.loads(row["events"]) if row["events"] else []
            webhooks.append(WebhookEntity.from_dict(row))

        return webhooks

    def update_webhook(self, webhook_id: str, updates: Dict[str, Any]) -> bool:
        """Update webhook properties."""
        update_fields = []
        params = []

        for field in ["name", "url", "secret", "is_active", "retry_count", "timeout_seconds"]:
            if field in updates:
                if field == "events":
                    update_fields.append("events = ?")
                    params.append(json.dumps(updates[field]))
                else:
                    update_fields.append(f"{field} = ?")
                    params.append(updates[field])

        if not update_fields:
            return False

        update_fields.append("updated_at = ?")
        params.append(utc_now().isoformat())
        params.append(webhook_id)

        query = f"""
            UPDATE {self.webhooks_table}
            SET {', '.join(update_fields)}
            WHERE id = ?
        """

        execute_query(query, tuple(params), fetch_all=False)
        return True

    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        query = f"DELETE FROM {self.webhooks_table} WHERE id = ?"
        execute_query(query, (webhook_id,), fetch_all=False)
        return True

    # Notification operations
    def create_notification(self, event_type: str, event_data: Dict[str, Any],
                          recipient_type: str, recipient_id: str) -> NotificationEntity:
        """Create a notification event."""

        if event_type not in self.VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event type: {event_type}")

        notification = NotificationEntity()
        notification.id = generate_id()
        notification.event_type = event_type
        notification.event_data = event_data
        notification.recipient_type = recipient_type
        notification.recipient_id = recipient_id
        notification.status = "pending"

        query = f"""
            INSERT INTO {self.notifications_table}
            (id, event_type, event_data, recipient_type, recipient_id, status, retry_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        execute_query(query, (
            notification.id, notification.event_type, json.dumps(notification.event_data),
            notification.recipient_type, notification.recipient_id, notification.status,
            notification.retry_count, notification.created_at.isoformat(),
            notification.updated_at.isoformat()
        ), fetch_all=False)

        return notification

    def get_pending_notifications(self, limit: int = 50) -> List[NotificationEntity]:
        """Get pending notifications for delivery."""
        query = f"""
            SELECT id, event_type, event_data, recipient_type, recipient_id, status,
                   delivered_at, error_message, retry_count, created_at, updated_at
            FROM {self.notifications_table}
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT ?
        """

        rows = execute_query(query, (limit,), fetch_all=True)

        notifications = []
        for row in rows:
            row["event_data"] = json.loads(row["event_data"]) if row["event_data"] else {}
            notifications.append(NotificationEntity.from_dict(row))

        return notifications

    def update_notification_status(self, notification_id: str, status: str,
                                 error_message: Optional[str] = None) -> bool:
        """Update notification delivery status."""
        query = f"""
            UPDATE {self.notifications_table}
            SET status = ?, error_message = ?, retry_count = retry_count + 1,
                delivered_at = ?, updated_at = ?
            WHERE id = ?
        """

        delivered_at = utc_now().isoformat() if status in ["delivered", "failed"] else None

        execute_query(query, (
            status, error_message, delivered_at, utc_now().isoformat(), notification_id
        ), fetch_all=False)

        return True

    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification delivery statistics."""
        # Total counts by status
        status_query = f"""
            SELECT status, COUNT(*) as count
            FROM {self.notifications_table}
            GROUP BY status
        """
        status_rows = execute_query(status_query, fetch_all=True)
        status_counts = {row["status"]: row["count"] for row in status_rows}

        # Event type counts
        event_query = f"""
            SELECT event_type, COUNT(*) as count
            FROM {self.notifications_table}
            GROUP BY event_type
        """
        event_rows = execute_query(event_query, fetch_all=True)
        event_counts = {row["event_type"]: row["count"] for row in event_rows}

        # Recent events
        recent_query = f"""
            SELECT id, event_type, status, created_at
            FROM {self.notifications_table}
            ORDER BY created_at DESC
            LIMIT 10
        """
        recent_rows = execute_query(recent_query, fetch_all=True)
        recent_events = [{"id": row["id"], "event_type": row["event_type"],
                         "status": row["status"], "created_at": row["created_at"]}
                        for row in recent_rows]

        # Webhook stats
        webhook_query = f"""
            SELECT COUNT(*) as total_webhooks,
                   SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_webhooks
            FROM {self.webhooks_table}
        """
        webhook_row = execute_query(webhook_query, fetch_one=True)
        webhook_stats = {
            "total_webhooks": webhook_row["total_webhooks"] if webhook_row else 0,
            "active_webhooks": webhook_row["active_webhooks"] if webhook_row else 0
        }

        return {
            "status_counts": status_counts,
            "event_counts": event_counts,
            "recent_events": recent_events,
            "webhook_stats": webhook_stats,
            "total_notifications": sum(status_counts.values())
        }

    def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Clean up old delivered/failed notifications."""
        query = f"""
            DELETE FROM {self.notifications_table}
            WHERE status IN ('delivered', 'failed')
            AND created_at < datetime('now', '-{days_old} days')
        """
        execute_query(query, fetch_all=False)
        # Note: In a real implementation, you'd track the number of deleted rows
        return 0
