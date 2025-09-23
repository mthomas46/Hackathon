"""Tests for Notification Service logging integration with
LogCollectorClient."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

from services.shared.utilities.logging_client import LogCollectorClient


class TestNotificationServiceLoggingIntegration:
    """Test Notification Service logging integration with
    LogCollectorClient."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_logger_client(self):
        """Mock LogCollectorClient."""
        mock_client = AsyncMock(spec=LogCollectorClient)
        return mock_client

    @pytest.fixture(autouse=True)
    async def setup_logger_client(self, mock_logger_client):
        """Setup mock logger client for all tests."""
        global logger_client
        logger_client = mock_logger_client
        yield
        logger_client = None

    @pytest.mark.asyncio
    async def test_notification_delivery_successful_logging(self, client, mock_logger_client):
        """Test successful notification delivery logging."""
        # Mock the notification sender
        with patch("main.notification_sender") as mock_sender:
            mock_sender.send_notification.return_value = {
                "status": "delivered",
                "channel": "slack",
                "target": "#general",
                "deduplicated": False,
                "message_id": "msg_123",
            }

            # Make request
            request_data = {
                "channel": "slack",
                "target": "#general",
                "title": "Test Alert",
                "message": "This is a test notification",
                "metadata": {"priority": "high"},
                "labels": ["alert", "test"],
            }

            response = client.post("/notify", json=request_data)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and delivery
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] in ["notification_send_started", "notification_delivered"]
            ]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == "notification_send_started")
            start_data = start_call[0][1]
            assert start_data["channel"] == "slack"
            assert start_data["target"] == "#general"
            assert start_data["title"] == "Test Alert"
            assert start_data["has_metadata"] is True
            assert start_data["has_labels"] is True
            assert "request_id" in start_data

            # Check delivery event
            delivery_call = next(call for call in business_calls if call[0][0] == "notification_delivered")
            delivery_data = delivery_call[0][1]
            assert delivery_data["channel"] == "slack"
            assert delivery_data["target"] == "#general"
            assert delivery_data["delivery_status"] == "delivered"
            assert delivery_data["was_deduplicated"] is False
            assert delivery_data["success"] is True
            assert "processing_time_seconds" in delivery_data

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            assert perf_call[0][0] == "notification_delivery"
            assert "delivery_success" in perf_call[0][2]
            assert perf_call[0][2]["delivery_success"] is True

    @pytest.mark.asyncio
    async def test_notification_delivery_with_deduplication_logging(self, client, mock_logger_client):
        """Test notification delivery with deduplication logging."""
        # Mock the notification sender to indicate deduplication
        with patch("main.notification_sender") as mock_sender:
            mock_sender.send_notification.return_value = {
                "status": "deduplicated",
                "channel": "email",
                "target": "user@example.com",
                "deduplicated": True,
                "reason": "duplicate_within_time_window",
            }

            # Make request
            request_data = {
                "channel": "email",
                "target": "user@example.com",
                "title": "Duplicate Alert",
                "message": "This is a duplicate notification",
                "metadata": {},
                "labels": [],
            }

            response = client.post("/notify", json=request_data)
            assert response.status_code == 200

            # Check delivery event shows deduplication
            delivery_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "notification_delivered"
            ]
            assert len(delivery_events) >= 1

            delivery_data = delivery_events[0][0][1]
            assert delivery_data["delivery_status"] == "deduplicated"
            assert delivery_data["was_deduplicated"] is True

    @pytest.mark.asyncio
    async def test_notification_delivery_failure_logging(self, client, mock_logger_client):
        """Test failed notification delivery logging."""
        # Mock the notification sender to raise an exception
        with patch("main.notification_sender") as mock_sender, patch("main.dlq_manager") as mock_dlq:

            mock_sender.send_notification.side_effect = Exception("Webhook timeout")
            mock_dlq.add_failed_notification = MagicMock()

            # Make request
            request_data = {
                "channel": "webhook",
                "target": "https://example.com/webhook",
                "title": "Failed Alert",
                "message": "This notification will fail",
                "metadata": {},
                "labels": [],
            }

            response = client.post("/notify", json=request_data)
            assert response.status_code >= 400  # Should fail

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "Notification delivery failed: Webhook timeout" in error_call[0][0]
            assert error_call[0][1]["channel"] == "webhook"
            assert error_call[0][1]["dlq_queued"] is True
            assert error_call[0][1]["error_type"] == "Exception"

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "notification_delivery_failed"
            ]
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data["channel"] == "webhook"
            assert failure_data["error_type"] == "Exception"
            assert "Webhook timeout" in failure_data["error_message"]
            assert failure_data["dlq_queued"] is True

    @pytest.mark.asyncio
    async def test_owner_resolution_successful_logging(self, client, mock_logger_client):
        """Test successful owner resolution logging."""
        # Mock the owner resolver
        with patch("main.owner_resolver") as mock_resolver:
            mock_resolver.resolve_owners.return_value = {
                "alice": "alice@example.com",
                "bob": "bob@example.com",
                "charlie": None,  # Unresolved
            }

            # Make request
            request_data = {"owners": ["alice", "bob", "charlie"]}

            response = client.post("/owners/resolve", json=request_data)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] in ["owner_resolution_started", "owner_resolution_completed"]
            ]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == "owner_resolution_started")
            start_data = start_call[0][1]
            assert start_data["owner_count"] == 3
            assert start_data["owners"] == ["alice", "bob", "charlie"]

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == "owner_resolution_completed")
            completion_data = completion_call[0][1]
            assert completion_data["total_owners"] == 3
            assert completion_data["resolved_count"] == 2  # alice and bob resolved
            assert completion_data["unresolved_count"] == 1  # charlie unresolved
            assert completion_data["success"] is True

    @pytest.mark.asyncio
    async def test_dlq_query_successful_logging(self, client, mock_logger_client):
        """Test successful DLQ query logging."""
        # Mock the DLQ manager
        with patch("main.dlq_manager") as mock_dlq:
            mock_dlq.get_dlq_entries.return_value = [
                {"id": "fail_1", "error": "timeout", "timestamp": "2024-01-01T00:00:00Z"},
                {"id": "fail_2", "error": "network", "timestamp": "2024-01-01T00:01:00Z"},
            ]

            # Make request
            response = client.get("/dlq?limit=10")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] in ["dlq_query_started", "dlq_query_completed"]
            ]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == "dlq_query_started")
            start_data = start_call[0][1]
            assert start_data["requested_limit"] == 10
            assert start_data["applied_limit"] == 10  # Within limits
            assert start_data["limit_was_capped"] is False

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == "dlq_query_completed")
            completion_data = completion_call[0][1]
            assert completion_data["entries_returned"] == 2
            assert completion_data["applied_limit"] == 10
            assert completion_data["success"] is True

    @pytest.mark.asyncio
    async def test_dlq_query_limit_capping_logging(self, client, mock_logger_client):
        """Test DLQ query with limit capping logging."""
        # Mock the DLQ manager
        with patch("main.dlq_manager") as mock_dlq:
            mock_dlq.get_dlq_entries.return_value = []  # Empty for this test

            # Make request with limit exceeding max
            response = client.get("/dlq?limit=1000")  # Exceeds MAX_DLQ_LIMIT
            assert response.status_code == 200

            # Check that limit was capped
            start_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "dlq_query_started"
            ]
            assert len(start_events) >= 1

            start_data = start_events[0][0][1]
            assert start_data["requested_limit"] == 1000
            assert start_data["applied_limit"] == 500  # MAX_DLQ_LIMIT
            assert start_data["limit_was_capped"] is True

    @pytest.mark.asyncio
    async def test_startup_logging(self, mock_logger_client):
        """Test service startup logging."""
        from main import startup_event

        await startup_event()

        # Verify startup logging
        assert mock_logger_client.log_business_event.call_count >= 1
        assert mock_logger_client.log_info.call_count >= 1

        # Check startup business event
        business_call = mock_logger_client.log_business_event.call_args
        assert business_call[0][0] == "notification_service_startup"
        startup_data = business_call[0][1]
        assert "capabilities" in startup_data
        assert "channels" in startup_data
        assert "features" in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert "Notification service started" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_shutdown_logging(self, mock_logger_client):
        """Test service shutdown logging."""
        from main import shutdown_event

        # Set logger client
        global logger_client
        logger_client = mock_logger_client

        await shutdown_event()

        # Verify shutdown logging
        assert mock_logger_client.log_info.call_count >= 1

        info_call = mock_logger_client.log_info.call_args
        assert "Notification service shutting down" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        # Mock the notification sender
        with patch("main.notification_sender") as mock_sender:
            mock_sender.send_notification.return_value = {"status": "delivered"}

            # Make request - should still work without logging
            request_data = {"channel": "slack", "target": "#general", "title": "Test", "message": "Test message"}

            response = client.post("/notify", json=request_data)
            assert response.status_code == 200

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        # Mock the notification sender
        with patch("main.notification_sender") as mock_sender:
            mock_sender.send_notification.return_value = {"status": "delivered"}

            request_data = {
                "channel": "email",
                "target": "test@example.com",
                "title": "Test",
                "message": "Test message",
            }

            client.post("/notify", json=request_data)

            # Check that request IDs are generated and used consistently
            business_calls = mock_logger_client.log_business_event.call_args_list
            perf_calls = mock_logger_client.log_performance_metric.call_args_list

            # Extract request IDs from all calls
            request_ids = set()
            for call in business_calls + perf_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get("request_id")
                    if request_id:
                        request_ids.add(request_id)

            # All calls should use the same request ID
            assert len(request_ids) == 1
            request_id = list(request_ids)[0]
            assert request_id.startswith("notify_")

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        # Mock the notification sender
        with patch("main.notification_sender") as mock_sender:
            mock_sender.send_notification.return_value = {"status": "delivered"}

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            request_data = {
                "channel": "webhook",
                "target": "https://example.com/hook",
                "title": "Test",
                "message": "Test message",
            }

            response = client.post("/notify", json=request_data)
            assert response.status_code == 200

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            processing_time = perf_call[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
