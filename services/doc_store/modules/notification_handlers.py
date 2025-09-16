# ============================================================================
# NOTIFICATION HANDLERS MODULE
# ============================================================================
"""
Notification and webhook handlers for Doc Store service.

Provides endpoints for webhook management, event monitoring, and delivery tracking.
"""

from typing import Dict, Any, Optional, List
from .notifications import notification_manager
from .shared_utils import (
    build_doc_store_context,
    create_doc_store_success_response,
    handle_doc_store_error
)
from .models import (
    WebhookRequest,
    NotificationStatsResponse,
    WebhookDeliveryResponse
)


class NotificationHandlers:
    """Handles notification and webhook operations."""

    @staticmethod
    async def handle_register_webhook(req: WebhookRequest) -> Dict[str, Any]:
        """Register a new webhook."""
        try:
            webhook_id = notification_manager.register_webhook(
                name=req.name,
                url=req.url,
                events=req.events,
                secret=req.secret,
                headers=req.headers,
                retry_count=req.retry_count,
                timeout_seconds=req.timeout_seconds
            )

            context = build_doc_store_context("webhook_registration", webhook_name=req.name)
            return create_doc_store_success_response("webhook registered", {
                "webhook_id": webhook_id,
                "name": req.name,
                "url": req.url,
                "events": req.events
            }, **context)

        except Exception as e:
            context = build_doc_store_context("webhook_registration", webhook_name=req.name)
            return handle_doc_store_error("register webhook", e, **context)

    @staticmethod
    async def handle_get_webhooks() -> Dict[str, Any]:
        """Get all registered webhooks."""
        try:
            webhooks = []
            for webhook_id, webhook in notification_manager.webhooks.items():
                webhooks.append({
                    "id": webhook.id,
                    "name": webhook.name,
                    "url": webhook.url,
                    "events": webhook.events,
                    "headers": webhook.headers,
                    "is_active": webhook.is_active,
                    "retry_count": webhook.retry_count,
                    "timeout_seconds": webhook.timeout_seconds,
                    "created_at": webhook.created_at,
                    "updated_at": webhook.updated_at
                })

            context = build_doc_store_context("webhooks_retrieval", count=len(webhooks))
            return create_doc_store_success_response("webhooks retrieved", {
                "webhooks": webhooks,
                "total": len(webhooks)
            }, **context)

        except Exception as e:
            context = build_doc_store_context("webhooks_retrieval")
            return handle_doc_store_error("get webhooks", e, **context)

    @staticmethod
    async def handle_emit_event(event_type: str, entity_type: str, entity_id: str,
                               user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manually emit a notification event."""
        try:
            event_id = notification_manager.emit_event(
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                metadata=metadata
            )

            if event_id:
                context = build_doc_store_context("event_emission", event_type=event_type, entity_id=entity_id)
                return create_doc_store_success_response("event emitted", {
                    "event_id": event_id,
                    "event_type": event_type,
                    "entity_type": entity_type,
                    "entity_id": entity_id
                }, **context)
            else:
                return handle_doc_store_error("emit event", "Failed to emit event")

        except Exception as e:
            context = build_doc_store_context("event_emission", event_type=event_type)
            return handle_doc_store_error("emit event", e, **context)

    @staticmethod
    async def handle_get_event_history(event_type: Optional[str] = None, entity_type: Optional[str] = None,
                                     entity_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Get notification event history."""
        try:
            events = notification_manager.get_event_history(event_type, entity_type, entity_id, limit)

            context = build_doc_store_context("event_history_retrieval", count=len(events))
            return create_doc_store_success_response("event history retrieved", {
                "events": events,
                "total": len(events),
                "filters": {
                    "event_type": event_type,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "limit": limit
                }
            }, **context)

        except Exception as e:
            context = build_doc_store_context("event_history_retrieval")
            return handle_doc_store_error("get event history", e, **context)

    @staticmethod
    async def handle_get_webhook_deliveries(webhook_id: Optional[str] = None, status: Optional[str] = None,
                                          limit: int = 100) -> Dict[str, Any]:
        """Get webhook delivery history."""
        try:
            deliveries = notification_manager.get_webhook_deliveries(webhook_id, status, limit)

            context = build_doc_store_context("webhook_deliveries_retrieval", count=len(deliveries))
            return create_doc_store_success_response("webhook deliveries retrieved", {
                "deliveries": deliveries,
                "total": len(deliveries),
                "filters": {
                    "webhook_id": webhook_id,
                    "status": status,
                    "limit": limit
                }
            }, **context)

        except Exception as e:
            context = build_doc_store_context("webhook_deliveries_retrieval")
            return handle_doc_store_error("get webhook deliveries", e, **context)

    @staticmethod
    async def handle_get_notification_stats(days_back: int = 7) -> Dict[str, Any]:
        """Get comprehensive notification statistics."""
        try:
            stats = notification_manager.get_notification_stats(days_back)

            context = build_doc_store_context("notification_stats_retrieval", days_back=days_back)
            return create_doc_store_success_response("notification statistics retrieved", stats, **context)

        except Exception as e:
            context = build_doc_store_context("notification_stats_retrieval", days_back=days_back)
            return handle_doc_store_error("get notification stats", e, **context)

    @staticmethod
    async def handle_test_webhook(webhook_id: str) -> Dict[str, Any]:
        """Test a webhook by sending a test event."""
        try:
            # Emit a test event
            test_event_id = notification_manager.emit_event(
                event_type="webhook.test",
                entity_type="webhook",
                entity_id=webhook_id,
                metadata={"test": True, "timestamp": notification_manager.utc_now().isoformat()}
            )

            if test_event_id:
                context = build_doc_store_context("webhook_test", webhook_id=webhook_id)
                return create_doc_store_success_response("webhook test initiated", {
                    "webhook_id": webhook_id,
                    "test_event_id": test_event_id
                }, **context)
            else:
                return handle_doc_store_error("test webhook", "Failed to emit test event")

        except Exception as e:
            context = build_doc_store_context("webhook_test", webhook_id=webhook_id)
            return handle_doc_store_error("test webhook", e, **context)
