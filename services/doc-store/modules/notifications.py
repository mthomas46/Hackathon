# ============================================================================
# NOTIFICATIONS MODULE
# ============================================================================
"""
Real-time notifications and webhook system for Doc Store service.

Provides comprehensive event notification capabilities including:
- Real-time event streaming and delivery
- Webhook management and delivery
- Notification subscriptions and filtering
- Event history and analytics
- Delivery tracking and retry mechanisms
"""

import json
import asyncio
import aiohttp
import hmac
import hashlib
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from services.shared.utilities import utc_now
from .shared_utils import execute_db_query


@dataclass
class NotificationEvent:
    """Represents a notification event."""
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class Webhook:
    """Webhook configuration."""
    id: str
    name: str
    url: str
    secret: Optional[str] = None
    events: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    is_active: bool = True
    retry_count: int = 3
    timeout_seconds: int = 30
    created_at: str = ""
    updated_at: str = ""


@dataclass
class WebhookDelivery:
    """Webhook delivery attempt."""
    id: str
    webhook_id: str
    event_type: str
    event_id: str
    payload: Dict[str, Any]
    status: str = "pending"
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    attempt_count: int = 1
    delivered_at: Optional[str] = None
    created_at: str = ""


class NotificationManager:
    """Manages notification events and delivery."""

    def __init__(self):
        self.event_listeners: Dict[str, Set] = {}
        self.webhooks: Dict[str, Webhook] = {}
        self._load_webhooks()

    def _load_webhooks(self):
        """Load webhooks from database."""
        try:
            rows = execute_db_query(
                "SELECT id, name, url, secret, events, headers, is_active, retry_count, timeout_seconds, created_at, updated_at FROM webhooks WHERE is_active = 1",
                fetch_all=True
            )

            for row in rows:
                webhook = Webhook(
                    id=row['id'],
                    name=row['name'],
                    url=row['url'],
                    secret=row['secret'],
                    events=json.loads(row['events'] or '[]'),
                    headers=json.loads(row['headers'] or '{}'),
                    is_active=bool(row['is_active']),
                    retry_count=row['retry_count'],
                    timeout_seconds=row['timeout_seconds'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                self.webhooks[webhook.id] = webhook

        except Exception as e:
            print(f"Error loading webhooks: {e}")

    def emit_event(self, event_type: str, entity_type: str, entity_id: str,
                   user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Emit a notification event."""
        event_id = f"event_{event_type}_{entity_type}_{entity_id}_{int(datetime.now().timestamp())}"

        try:
            # Store event in database
            execute_db_query("""
                INSERT INTO notification_events
                (id, event_type, entity_type, entity_id, user_id, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                event_type,
                entity_type,
                entity_id,
                user_id,
                json.dumps(metadata or {}),
                utc_now().isoformat()
            ))

            event = NotificationEvent(
                id=event_id,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                metadata=metadata or {},
                created_at=utc_now().isoformat()
            )

            # Trigger webhook deliveries asynchronously
            asyncio.create_task(self._deliver_webhooks(event))

            # Notify local listeners
            self._notify_listeners(event)

            return event_id

        except Exception as e:
            print(f"Error emitting event: {e}")
            return ""

    def _notify_listeners(self, event: NotificationEvent):
        """Notify local event listeners."""
        listeners = self.event_listeners.get(event.event_type, set())
        for listener in listeners:
            try:
                # In a real implementation, this would call registered listener functions
                pass
            except Exception as e:
                print(f"Error notifying listener: {e}")

    async def _deliver_webhooks(self, event: NotificationEvent):
        """Deliver event to registered webhooks."""
        matching_webhooks = [
            webhook for webhook in self.webhooks.values()
            if event.event_type in webhook.events and webhook.is_active
        ]

        if not matching_webhooks:
            return

        payload = {
            "event_id": event.id,
            "event_type": event.event_type,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "user_id": event.user_id,
            "metadata": event.metadata,
            "timestamp": event.created_at
        }

        # Deliver to each matching webhook
        tasks = [self._deliver_to_webhook(webhook, event, payload) for webhook in matching_webhooks]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _deliver_to_webhook(self, webhook: Webhook, event: NotificationEvent, payload: Dict[str, Any]):
        """Deliver event to a specific webhook."""
        delivery_id = f"delivery_{webhook.id}_{event.id}"

        try:
            headers = dict(webhook.headers)
            headers.update({
                "Content-Type": "application/json",
                "User-Agent": "DocStore-Webhook/1.0"
            })

            # Add signature if secret is configured
            if webhook.secret:
                signature = self._generate_signature(json.dumps(payload), webhook.secret)
                headers["X-DocStore-Signature"] = signature

            # Create delivery record
            execute_db_query("""
                INSERT INTO webhook_deliveries
                (id, webhook_id, event_type, event_id, payload, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """, (
                delivery_id,
                webhook.id,
                event.event_type,
                event.id,
                json.dumps(payload),
                utc_now().isoformat()
            ))

            # Attempt delivery with retries
            success = False
            last_error = None

            for attempt in range(webhook.retry_count):
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=webhook.timeout_seconds)) as session:
                        async with session.post(webhook.url, json=payload, headers=headers) as response:
                            response_body = await response.text()
                            response_code = response.status

                            # Update delivery record
                            execute_db_query("""
                                UPDATE webhook_deliveries
                                SET status = ?, response_code = ?, response_body = ?,
                                    attempt_count = ?, delivered_at = ?, updated_at = ?
                                WHERE id = ?
                            """, (
                                "delivered" if response_code < 400 else "failed",
                                response_code,
                                response_body[:5000] if response_body else None,  # Limit response body size
                                attempt + 1,
                                utc_now().isoformat() if response_code < 400 else None,
                                utc_now().isoformat(),
                                delivery_id
                            ))

                            if response_code < 400:
                                success = True
                                break
                            else:
                                last_error = f"HTTP {response_code}: {response_body}"

                except Exception as e:
                    last_error = str(e)

                    # Update delivery record with error
                    execute_db_query("""
                        UPDATE webhook_deliveries
                        SET status = 'failed', error_message = ?, attempt_count = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        last_error,
                        attempt + 1,
                        utc_now().isoformat(),
                        delivery_id
                    ))

                    if attempt < webhook.retry_count - 1:
                        # Wait before retry (exponential backoff)
                        await asyncio.sleep(2 ** attempt)

            if not success:
                # Final failure
                execute_db_query("""
                    UPDATE webhook_deliveries
                    SET status = 'failed', error_message = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    last_error or "Unknown error",
                    utc_now().isoformat(),
                    delivery_id
                ))

        except Exception as e:
            print(f"Error delivering webhook {webhook.name}: {e}")

    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate webhook signature for payload verification."""
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def register_webhook(self, name: str, url: str, events: List[str],
                        secret: Optional[str] = None, headers: Optional[Dict[str, str]] = None,
                        retry_count: int = 3, timeout_seconds: int = 30) -> str:
        """Register a new webhook."""
        webhook_id = f"webhook_{name.lower().replace(' ', '_')}"

        try:
            execute_db_query("""
                INSERT OR REPLACE INTO webhooks
                (id, name, url, secret, events, headers, is_active, retry_count, timeout_seconds, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
            """, (
                webhook_id,
                name,
                url,
                secret,
                json.dumps(events),
                json.dumps(headers or {}),
                retry_count,
                timeout_seconds,
                utc_now().isoformat(),
                utc_now().isoformat()
            ))

            webhook = Webhook(
                id=webhook_id,
                name=name,
                url=url,
                secret=secret,
                events=events,
                headers=headers or {},
                is_active=True,
                retry_count=retry_count,
                timeout_seconds=timeout_seconds,
                created_at=utc_now().isoformat(),
                updated_at=utc_now().isoformat()
            )
            self.webhooks[webhook_id] = webhook

            return webhook_id

        except Exception as e:
            raise Exception(f"Failed to register webhook: {str(e)}")

    def get_event_history(self, event_type: Optional[str] = None, entity_type: Optional[str] = None,
                         entity_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history with optional filtering."""
        try:
            query = "SELECT id, event_type, entity_type, entity_id, user_id, metadata, created_at FROM notification_events WHERE 1=1"
            params = []

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)

            if entity_id:
                query += " AND entity_id = ?"
                params.append(entity_id)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = execute_db_query(query, tuple(params), fetch_all=True)

            events = []
            for row in rows:
                events.append({
                    "id": row['id'],
                    "event_type": row['event_type'],
                    "entity_type": row['entity_type'],
                    "entity_id": row['entity_id'],
                    "user_id": row['user_id'],
                    "metadata": json.loads(row['metadata'] or '{}'),
                    "created_at": row['created_at']
                })

            return events

        except Exception:
            return []

    def get_webhook_deliveries(self, webhook_id: Optional[str] = None, status: Optional[str] = None,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get webhook delivery history."""
        try:
            query = """
                SELECT wd.id, wd.webhook_id, w.name as webhook_name, wd.event_type, wd.event_id,
                       wd.status, wd.response_code, wd.error_message, wd.attempt_count,
                       wd.delivered_at, wd.created_at
                FROM webhook_deliveries wd
                LEFT JOIN webhooks w ON wd.webhook_id = w.id
                WHERE 1=1
            """
            params = []

            if webhook_id:
                query += " AND wd.webhook_id = ?"
                params.append(webhook_id)

            if status:
                query += " AND wd.status = ?"
                params.append(status)

            query += " ORDER BY wd.created_at DESC LIMIT ?"
            params.append(limit)

            rows = execute_db_query(query, tuple(params), fetch_all=True)

            deliveries = []
            for row in rows:
                deliveries.append({
                    "id": row['id'],
                    "webhook_id": row['webhook_id'],
                    "webhook_name": row['webhook_name'],
                    "event_type": row['event_type'],
                    "event_id": row['event_id'],
                    "status": row['status'],
                    "response_code": row['response_code'],
                    "error_message": row['error_message'],
                    "attempt_count": row['attempt_count'],
                    "delivered_at": row['delivered_at'],
                    "created_at": row['created_at']
                })

            return deliveries

        except Exception:
            return []

    def get_notification_stats(self, days_back: int = 7) -> Dict[str, Any]:
        """Get comprehensive notification statistics."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

            # Event type distribution
            event_types = execute_db_query("""
                SELECT event_type, COUNT(*) as count
                FROM notification_events
                WHERE created_at > ?
                GROUP BY event_type
                ORDER BY count DESC
            """, (cutoff_date,), fetch_all=True)

            # Webhook delivery success rates
            delivery_stats = execute_db_query("""
                SELECT
                    COUNT(*) as total_deliveries,
                    SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as successful_deliveries,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_deliveries,
                    AVG(attempt_count) as avg_attempts
                FROM webhook_deliveries
                WHERE created_at > ?
            """, (cutoff_date,), fetch_one=True)

            # Recent webhook failures
            recent_failures = execute_db_query("""
                SELECT wd.id, w.name as webhook_name, wd.event_type, wd.error_message, wd.created_at
                FROM webhook_deliveries wd
                LEFT JOIN webhooks w ON wd.webhook_id = w.id
                WHERE wd.status = 'failed' AND wd.created_at > ?
                ORDER BY wd.created_at DESC
                LIMIT 10
            """, (cutoff_date,), fetch_all=True)

            return {
                "period_days": days_back,
                "event_distribution": [
                    {"event_type": row['event_type'], "count": row['count']}
                    for row in event_types
                ],
                "webhook_delivery_stats": {
                    "total_deliveries": delivery_stats[0],
                    "successful_deliveries": delivery_stats[1],
                    "failed_deliveries": delivery_stats[2],
                    "success_rate": (delivery_stats[1] / delivery_stats[0] * 100) if delivery_stats[0] > 0 else 0,
                    "average_attempts": round(delivery_stats[3] or 0, 2)
                },
                "recent_failures": [
                    {
                        "delivery_id": row['id'],
                        "webhook_name": row['webhook_name'],
                        "event_type": row['event_type'],
                        "error_message": row['error_message'],
                        "timestamp": row['created_at']
                    } for row in recent_failures
                ]
            }

        except Exception as e:
            return {"error": str(e)}


# Global notification manager instance
notification_manager = NotificationManager()
