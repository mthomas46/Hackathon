"""Tests for Doc Store notification and webhook functionality.

Tests event emission, webhook delivery, notification statistics,
and integration with the notification service.
"""

import sys
import os
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch, AsyncMock, ANY
import pytest

# Import modules normally now that directory uses underscores
from services.doc_store.modules.notifications import (
    NotificationManager, NotificationEvent, Webhook, notification_manager
)


class TestNotificationEvent:
    """Test NotificationEvent class."""

    def test_event_initialization(self):
        """Test notification event initialization."""
        event = NotificationEvent(
            id="event-123",
            event_type="document.created",
            entity_type="document",
            entity_id="doc1",
            user_id="user123",
            metadata={"content_length": 1000},
            created_at="2024-01-01T00:00:00Z"
        )

        assert event.id == "event-123"
        assert event.event_type == "document.created"
        assert event.entity_type == "document"
        assert event.entity_id == "doc1"
        assert event.user_id == "user123"
        assert event.metadata == {"content_length": 1000}


class TestWebhook:
    """Test Webhook class."""

    def test_webhook_initialization(self):
        """Test webhook initialization."""
        webhook = Webhook(
            id="webhook-123",
            name="Test Webhook",
            url="https://example.com/webhook",
            secret="secret123",
            events=["document.created", "document.updated"],
            headers={"Authorization": "Bearer token"},
            is_active=True,
            retry_count=3,
            timeout_seconds=30
        )

        assert webhook.id == "webhook-123"
        assert webhook.name == "Test Webhook"
        assert webhook.url == "https://example.com/webhook"
        assert webhook.secret == "secret123"
        assert webhook.events == ["document.created", "document.updated"]
        assert webhook.is_active is True
        assert webhook.retry_count == 3
        assert webhook.timeout_seconds == 30


class TestNotificationManager:
    """Test NotificationManager class functionality."""

    @pytest.fixture
    def manager(self):
        """Create a test notification manager instance."""
        return NotificationManager()

    def test_manager_initialization(self, manager):
        """Test notification manager initialization."""
        assert isinstance(manager.event_listeners, dict)
        assert isinstance(manager.webhooks, dict)

    @pytest.mark.asyncio
    async def test_emit_event_basic(self, manager):
        """Test basic event emission."""
        with patch('services.doc_store.modules.notifications.execute_db_query') as mock_execute:
            with patch.object(manager, '_deliver_webhooks', new_callable=AsyncMock) as mock_deliver:
                with patch('services.doc_store.modules.notifications.asyncio.create_task') as mock_create_task:
                    mock_execute.return_value = []
                    mock_create_task.return_value = None

                event_id = manager.emit_event(
                    event_type="document.created",
                    entity_type="document",
                    entity_id="doc1",
                    metadata={"size": 1000}
                )

                assert "document.created" in event_id
                assert "doc1" in event_id

                # Verify database storage
                mock_execute.assert_called()

                # Verify webhook delivery was triggered
                mock_deliver.assert_called_once()

    @patch('services.doc_store.modules.notifications.execute_db_query')
    def test_register_webhook(self, mock_execute, manager):
        """Test webhook registration."""
        mock_execute.return_value = []

        webhook_id = manager.register_webhook(
            name="Test Webhook",
            url="https://example.com/hook",
            events=["document.created"],
            secret="secret123",
            retry_count=5
        )

        assert "webhook_test_webhook" == webhook_id
        assert webhook_id in manager.webhooks

        webhook = manager.webhooks[webhook_id]
        assert webhook.name == "Test Webhook"
        assert webhook.url == "https://example.com/hook"
        assert webhook.events == ["document.created"]
        assert webhook.secret == "secret123"
        assert webhook.retry_count == 5

    @pytest.mark.asyncio
    async def test_deliver_webhooks_no_matching(self, manager):
        """Test webhook delivery with no matching webhooks."""
        manager.webhooks = {}  # No webhooks

        event = NotificationEvent(
            id="test-event",
            event_type="document.created",
            entity_type="document",
            entity_id="doc1"
        )

        # Should not raise any errors
        await manager._deliver_webhooks(event)

    @pytest.mark.asyncio
    async def test_deliver_webhooks_with_matching(self, manager):
        """Test webhook delivery with matching webhooks."""
        # Create a test webhook
        webhook = Webhook(
            id="test-webhook",
            name="Test",
            url="https://example.com/hook",
            events=["document.created"],
            is_active=True
        )
        manager.webhooks = {"test-webhook": webhook}

        event = NotificationEvent(
            id="test-event",
            event_type="document.created",
            entity_type="document",
            entity_id="doc1"
        )

        with patch.object(manager, '_deliver_via_notification_service', new_callable=AsyncMock) as mock_deliver:
            await manager._deliver_webhooks(event)

            # Verify delivery was attempted
            mock_deliver.assert_called_once_with(webhook, event, ANY, ANY)

    @pytest.mark.asyncio
    async def test_deliver_via_notification_service_success(self, manager):
        """Test successful delivery via notification service."""
        webhook = Webhook(
            id="test-webhook",
            name="Test",
            url="https://example.com/hook",
            events=["document.created"],
            secret="secret123"
        )

        event = NotificationEvent(
            id="test-event",
            event_type="document.created",
            entity_type="document",
            entity_id="doc1"
        )

        payload = {"test": "payload"}

        # Mock notification service client
        mock_client = Mock()
        mock_client.notify_via_service = AsyncMock(return_value={"status": "sent"})

        with patch('services.doc_store.modules.notifications.execute_db_query') as mock_execute:
            mock_execute.return_value = []

            await manager._deliver_via_notification_service(webhook, event, payload, mock_client)

            # Verify notification service was called
            mock_client.notify_via_service.assert_called_once()

            # Verify delivery was recorded
            assert mock_execute.call_count >= 2  # Initial record + success update

    @pytest.mark.asyncio
    async def test_deliver_via_notification_service_failure(self, manager):
        """Test failed delivery via notification service."""
        webhook = Webhook(
            id="test-webhook",
            name="Test",
            url="https://example.com/hook",
            events=["document.created"]
        )

        event = NotificationEvent(
            id="test-event",
            event_type="document.created",
            entity_type="document",
            entity_id="doc1"
        )

        payload = {"test": "payload"}

        # Mock notification service client with failure
        mock_client = Mock()
        mock_client.notify_via_service = AsyncMock(return_value={"status": "failed", "detail": "Connection error"})

        with patch('services.doc_store.modules.notifications.execute_db_query') as mock_execute:
            mock_execute.return_value = []

            await manager._deliver_via_notification_service(webhook, event, payload, mock_client)

            # Verify delivery failure was recorded
            failure_calls = [call for call in mock_execute.call_args_list if 'failed' in str(call[0][0])]
            assert len(failure_calls) > 0

    def test_generate_signature(self, manager):
        """Test webhook signature generation."""
        payload = '{"test": "data"}'
        secret = "mysecret"

        signature = manager._generate_signature(payload, secret)

        # Should be a valid HMAC-SHA256 hex string
        assert len(signature) == 64  # SHA256 produces 64 character hex string
        assert signature.isalnum()

    @patch('services.doc_store.modules.notifications.execute_db_query')
    def test_get_event_history(self, mock_execute, manager):
        """Test event history retrieval."""
        mock_events = [
            {
                'id': 'event1',
                'event_type': 'document.created',
                'entity_type': 'document',
                'entity_id': 'doc1',
                'user_id': 'user1',
                'metadata': '{"size": 1000}',
                'created_at': '2024-01-01T00:00:00Z'
            },
            {
                'id': 'event2',
                'event_type': 'document.updated',
                'entity_type': 'document',
                'entity_id': 'doc2',
                'user_id': None,
                'metadata': '{}',
                'created_at': '2024-01-01T01:00:00Z'
            }
        ]
        mock_execute.return_value = mock_events

        events = manager.get_event_history(limit=10)

        assert len(events) == 2
        assert events[0]['event_type'] == 'document.created'
        assert events[1]['event_type'] == 'document.updated'

    @patch('services.doc_store.modules.notifications.execute_db_query')
    def test_get_event_history_filtered(self, mock_execute, manager):
        """Test filtered event history retrieval."""
        mock_events = [
            {
                'id': 'event1',
                'event_type': 'document.created',
                'entity_type': 'document',
                'entity_id': 'doc1',
                'user_id': 'user1',
                'metadata': '{}',
                'created_at': '2024-01-01T00:00:00Z'
            }
        ]
        mock_execute.return_value = mock_events

        events = manager.get_event_history(event_type="document.created", entity_id="doc1")

        assert len(events) == 1
        assert events[0]['event_type'] == 'document.created'

    @patch('services.doc_store.modules.notifications.execute_db_query')
    def test_get_webhook_deliveries(self, mock_execute, manager):
        """Test webhook delivery history retrieval."""
        mock_deliveries = [
            {
                'id': 'delivery1',
                'webhook_id': 'webhook1',
                'webhook_name': 'Test Webhook',
                'event_type': 'document.created',
                'event_id': 'event1',
                'status': 'delivered',
                'response_code': 200,
                'error_message': None,
                'attempt_count': 1,
                'delivered_at': '2024-01-01T00:00:00Z',
                'created_at': '2024-01-01T00:00:00Z'
            }
        ]
        mock_execute.return_value = mock_deliveries

        deliveries = manager.get_webhook_deliveries(limit=10)

        assert len(deliveries) == 1
        assert deliveries[0]['status'] == 'delivered'
        assert deliveries[0]['webhook_name'] == 'Test Webhook'

    @patch('services.doc_store.modules.notifications.execute_db_query')
    def test_get_notification_stats(self, mock_execute, manager):
        """Test notification statistics generation."""
        # Mock event distribution
        event_dist = [
            {'event_type': 'document.created', 'count': 50},
            {'event_type': 'document.updated', 'count': 30}
        ]

        # Mock delivery stats
        delivery_stats = [100, 95, 5, 1.2]  # total, successful, failed, avg attempts

        # Mock recent failures
        recent_failures = [
            {
                'id': 'failure1',
                'webhook_name': 'Test Webhook',
                'event_type': 'document.created',
                'error_message': 'Timeout',
                'created_at': '2024-01-01T00:00:00Z'
            }
        ]

        mock_execute.side_effect = [event_dist, delivery_stats, recent_failures]

        stats = manager.get_notification_stats(days_back=7)

        assert stats['period_days'] == 7
        assert len(stats['event_distribution']) == 2
        assert stats['webhook_delivery_stats']['total_deliveries'] == 100
        assert stats['webhook_delivery_stats']['successful_deliveries'] == 95
        assert stats['webhook_delivery_stats']['success_rate'] == 95.0
        assert len(stats['recent_failures']) == 1


class TestNotificationIntegration:
    """Test notification system integration with doc store."""

    @pytest.mark.asyncio
    async def test_webhook_registration_api(self):
        """Test webhook registration API endpoint."""
        from services.doc_store.modules.notification_handlers import NotificationHandlers
        from services.doc_store.core.models import WebhookRequest

        request = WebhookRequest(
            name="API Webhook",
            url="https://api.example.com/webhook",
            events=["document.created", "document.updated"],
            secret="webhook-secret",
            retry_count=5,
            timeout_seconds=60
        )

        with patch('services.doc_store.modules.notification_handlers.notification_manager') as mock_manager:
            mock_manager.register_webhook.return_value = "webhook_api_webhook"

            handler = NotificationHandlers()
            result = await handler.handle_register_webhook(request)

            assert result["data"]["webhook_id"] == "webhook_api_webhook"
            assert result["data"]["name"] == "API Webhook"

    @pytest.mark.asyncio
    async def test_event_emission_api(self):
        """Test manual event emission API."""
        from services.doc_store.modules.notification_handlers import NotificationHandlers

        with patch('services.doc_store.modules.notification_handlers.notification_manager') as mock_manager:
            mock_manager.emit_event.return_value = "event_manual_123"

            handler = NotificationHandlers()
            result = await handler.handle_emit_event(
                event_type="document.test",
                entity_type="document",
                entity_id="test-doc",
                metadata={"test": True}
            )

            assert result["data"]["event_id"] == "event_manual_123"
            assert result["data"]["event_type"] == "document.test"

    @pytest.mark.asyncio
    async def test_event_history_api(self):
        """Test event history API."""
        from services.doc_store.modules.notification_handlers import NotificationHandlers

        mock_events = [
            {
                "id": "event1",
                "event_type": "document.created",
                "entity_type": "document",
                "entity_id": "doc1",
                "metadata": {"size": 1000}
            }
        ]

        with patch('services.doc_store.modules.notification_handlers.notification_manager') as mock_manager:
            mock_manager.get_event_history.return_value = mock_events

            handler = NotificationHandlers()
            result = await handler.handle_get_event_history(limit=10)

            assert len(result["data"]["events"]) == 1
            assert result["data"]["events"][0]["event_type"] == "document.created"

    @pytest.mark.asyncio
    async def test_notification_stats_api(self):
        """Test notification statistics API."""
        from services.doc_store.modules.notification_handlers import NotificationHandlers

        mock_stats = {
            "period_days": 7,
            "event_distribution": [{"event_type": "document.created", "count": 50}],
            "webhook_delivery_stats": {
                "total_deliveries": 100,
                "successful_deliveries": 95,
                "success_rate": 95.0
            },
            "recent_failures": []
        }

        with patch('services.doc_store.modules.notification_handlers.notification_manager') as mock_manager:
            mock_manager.get_notification_stats.return_value = mock_stats

            handler = NotificationHandlers()
            result = await handler.handle_get_notification_stats(days_back=7)

            assert result["data"]["period_days"] == 7
            assert result["data"]["webhook_delivery_stats"]["success_rate"] == 95.0

    @pytest.mark.asyncio
    async def test_webhook_test_api(self):
        """Test webhook testing API."""
        from services.doc_store.modules.notification_handlers import NotificationHandlers

        with patch('services.doc_store.modules.notification_handlers.notification_manager') as mock_manager:
            mock_manager.emit_event.return_value = "event_test_123"

            handler = NotificationHandlers()
            result = await handler.handle_test_webhook("webhook-123")

            assert result["data"]["test_event_id"] == "event_test_123"
            assert result["data"]["webhook_id"] == "webhook-123"


class TestNotificationSecurity:
    """Test notification system security features."""

    def test_signature_generation_consistency(self):
        """Test that signature generation is consistent."""
        manager = NotificationManager()

        payload = '{"test": "data", "timestamp": 1234567890}'
        secret = "test-secret"

        sig1 = manager._generate_signature(payload, secret)
        sig2 = manager._generate_signature(payload, secret)

        # Same input should produce same signature
        assert sig1 == sig2

    def test_signature_generation_different_secrets(self):
        """Test that different secrets produce different signatures."""
        manager = NotificationManager()

        payload = '{"test": "data"}'
        secret1 = "secret1"
        secret2 = "secret2"

        sig1 = manager._generate_signature(payload, secret1)
        sig2 = manager._generate_signature(payload, secret2)

        # Different secrets should produce different signatures
        assert sig1 != sig2

    def test_signature_generation_different_payloads(self):
        """Test that different payloads produce different signatures."""
        manager = NotificationManager()

        payload1 = '{"test": "data1"}'
        payload2 = '{"test": "data2"}'
        secret = "test-secret"

        sig1 = manager._generate_signature(payload1, secret)
        sig2 = manager._generate_signature(payload2, secret)

        # Different payloads should produce different signatures
        assert sig1 != sig2
