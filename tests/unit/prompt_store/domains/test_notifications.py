"""Tests for notifications domain.

Tests covering repository, service, and handler layers for webhook notifications.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from services.prompt_store.domain.notifications.repository import (
    NotificationsRepository, WebhookEntity, NotificationEntity
)
from services.prompt_store.domain.notifications.service import NotificationsService
from services.prompt_store.domain.notifications.handlers import NotificationsHandlers
from services.prompt_store.core.models import WebhookCreate


@pytest.mark.unit
class TestNotificationsRepository:
    """Test NotificationsRepository operations."""

    def test_create_webhook_success(self, prompt_store_db):
        """Test successful webhook creation."""
        repo = NotificationsRepository()
        webhook_data = {
            "name": "test_webhook",
            "url": "https://example.com/webhook",
            "events": ["prompt.created", "prompt.updated"],
            "secret": "test_secret",
            "is_active": True,
            "created_by": "test_user"
        }

        webhook = repo.create_webhook(webhook_data)
        assert webhook.name == "test_webhook"
        assert webhook.url == "https://example.com/webhook"
        assert webhook.events == ["prompt.created", "prompt.updated"]
        assert webhook.is_active is True

    def test_get_webhook_found(self, prompt_store_db):
        """Test getting existing webhook."""
        repo = NotificationsRepository()
        webhook_data = {
            "name": "get_test_webhook",
            "url": "https://example.com/webhook",
            "events": ["prompt.created"],
            "created_by": "test_user"
        }

        created = repo.create_webhook(webhook_data)
        retrieved = repo.get_webhook(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "get_test_webhook"

    def test_get_active_webhooks_for_event(self, prompt_store_db):
        """Test getting active webhooks for specific event."""
        repo = NotificationsRepository()

        # Create webhook for specific events
        webhook_data = {
            "name": "event_webhook",
            "url": "https://example.com/webhook",
            "events": ["prompt.created", "prompt.updated"],
            "is_active": True,
            "created_by": "test_user"
        }
        repo.create_webhook(webhook_data)

        # Get webhooks for event
        webhooks = repo.get_active_webhooks_for_event("prompt.created")
        assert len(webhooks) >= 1
        assert any(w.name == "event_webhook" for w in webhooks)

    def test_create_notification_success(self, prompt_store_db):
        """Test successful notification creation."""
        repo = NotificationsRepository()
        notification = repo.create_notification(
            "prompt.created",
            {"prompt_id": "test_123", "name": "Test Prompt"},
            "webhook",
            "webhook_123"
        )

        assert notification.event_type == "prompt.created"
        assert notification.event_data["prompt_id"] == "test_123"
        assert notification.recipient_type == "webhook"
        assert notification.recipient_id == "webhook_123"
        assert notification.status == "pending"

    def test_get_pending_notifications(self, prompt_store_db):
        """Test getting pending notifications."""
        repo = NotificationsRepository()

        # Create some notifications
        for i in range(3):
            repo.create_notification(
                "prompt.created",
                {"prompt_id": f"test_{i}"},
                "webhook",
                f"webhook_{i}"
            )

        pending = repo.get_pending_notifications(limit=5)
        assert len(pending) >= 3

        for notification in pending:
            assert notification.status == "pending"


@pytest.mark.unit
class TestNotificationsService:
    """Test NotificationsService business logic."""

    def test_register_webhook_success(self, prompt_store_db):
        """Test successful webhook registration."""
        service = NotificationsService()
        webhook_data = {
            "name": "service_test_webhook",
            "url": "https://example.com/webhook",
            "events": ["prompt.created", "prompt.updated"],
            "secret": "test_secret",
            "is_active": True,
            "created_by": "test_user"
        }

        result = service.register_webhook(webhook_data)
        assert result["name"] == "service_test_webhook"
        assert result["is_active"] is True
        assert "webhook_id" in result

    def test_register_webhook_validation_error(self, prompt_store_db):
        """Test webhook registration with validation error."""
        service = NotificationsService()
        invalid_data = {
            "name": "",  # Invalid: empty name
            "url": "https://example.com/webhook",
            "events": ["invalid.event"],
            "created_by": "test_user"
        }

        with pytest.raises(ValueError):
            service.register_webhook(invalid_data)

    @pytest.mark.asyncio
    async def test_notify_event_success(self, prompt_store_db):
        """Test successful event notification."""
        service = NotificationsService()

        # Create a webhook first
        webhook_data = {
            "name": "notify_test_webhook",
            "url": "https://httpbin.org/post",  # Use httpbin for testing
            "events": ["prompt.created"],
            "is_active": True,
            "created_by": "test_user"
        }
        webhook_result = service.register_webhook(webhook_data)

        # Notify event
        result = await service.notify_event(
            "prompt.created",
            {"prompt_id": "test_123", "name": "Test Prompt"}
        )

        assert result["event_type"] == "prompt.created"
        assert result["total_webhooks"] >= 1
        assert "notifications_sent" in result

    def test_get_notification_stats(self, prompt_store_db):
        """Test getting notification statistics."""
        service = NotificationsService()

        # Create some test data
        service.repo.create_notification("prompt.created", {}, "webhook", "test_webhook")
        service.repo.create_webhook({
            "name": "stats_test_webhook",
            "url": "https://example.com",
            "events": ["prompt.created"],
            "created_by": "test_user"
        })

        stats = service.get_notification_stats()
        assert "status_counts" in stats
        assert "event_counts" in stats
        assert "webhook_stats" in stats
        assert "recent_events" in stats


@pytest.mark.unit
class TestNotificationsHandlers:
    """Test NotificationsHandlers HTTP operations."""

    def test_handle_register_webhook_success(self):
        """Test successful webhook registration handler."""
        handlers = NotificationsHandlers()

        with patch.object(handlers.notifications_service, 'register_webhook') as mock_register:
            mock_register.return_value = {
                "webhook_id": "test_webhook_id",
                "name": "test_webhook",
                "url": "https://example.com",
                "events": ["prompt.created"],
                "is_active": True
            }

            webhook_data = WebhookCreate(
                name="test_webhook",
                url="https://example.com",
                events=["prompt.created"]
            )

            result = handlers.handle_register_webhook(webhook_data)

            assert result["success"] is True
            assert result["data"]["name"] == "test_webhook"
            mock_register.assert_called_once()

    def test_handle_list_webhooks_success(self):
        """Test successful webhooks listing handler."""
        handlers = NotificationsHandlers()

        with patch.object(handlers.notifications_service, 'list_webhooks') as mock_list:
            mock_list.return_value = {
                "webhooks": [{"id": "webhook_1", "name": "test"}],
                "count": 1,
                "active_only": False
            }

            result = handlers.handle_list_webhooks()

            assert result["success"] is True
            assert result["data"]["count"] == 1
            mock_list.assert_called_once_with(False)

    def test_handle_get_notification_stats_success(self):
        """Test successful notification stats handler."""
        handlers = NotificationsHandlers()

        with patch.object(handlers.notifications_service, 'get_notification_stats') as mock_stats:
            mock_stats.return_value = {
                "status_counts": {"pending": 5, "delivered": 10},
                "event_counts": {"prompt.created": 15},
                "webhook_stats": {"total_webhooks": 3, "active_webhooks": 2},
                "recent_events": [],
                "total_notifications": 15
            }

            result = handlers.handle_get_notification_stats()

            assert result["success"] is True
            assert result["data"]["total_notifications"] == 15
            mock_stats.assert_called_once()

    def test_handle_get_valid_events_success(self):
        """Test successful valid events retrieval."""
        handlers = NotificationsHandlers()

        result = handlers.handle_get_valid_events()

        assert result["success"] is True
        assert "valid_event_types" in result["data"]
        assert "event_categories" in result["data"]
        assert len(result["data"]["valid_event_types"]) > 0
