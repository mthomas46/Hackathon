"""Tests for the centralized logging client."""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.shared.utilities.logging_client import (
    LogCollectorClient,
    get_log_collector_client,
    log_service_event,
    log_business_event,
    log_performance_metric
)


class TestLogCollectorClient:
    """Test the LogCollectorClient functionality."""

    @pytest.fixture
    async def client(self):
        """Create a test client."""
        client = LogCollectorClient(
            service_name="test-service",
            batch_size=2,  # Small batch for testing
            flush_interval=0.1  # Fast flush for testing
        )
        await client.start()
        yield client
        await client.stop()

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization."""
        client = LogCollectorClient("test-service")
        assert client.service_name == "test-service"
        assert client.collector_url == "http://localhost:5080"
        assert client.batch_size == 10
        assert not client._running

    @pytest.mark.asyncio
    async def test_client_start_stop(self, client):
        """Test client start/stop lifecycle."""
        assert client._running
        assert client._session is not None
        assert client._flush_task is not None

        await client.stop()
        assert not client._running
        assert client._session is None

    @pytest.mark.asyncio
    async def test_log_info(self, client):
        """Test info level logging."""
        await client.log_info("Test message", {"key": "value"})

        # Check that log was added to batch
        assert len(client._batch) == 1
        log_entry = client._batch[0]
        assert log_entry["service"] == "test-service"
        assert log_entry["level"] == "info"
        assert log_entry["message"] == "Test message"
        assert log_entry["context"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_log_error_with_exception(self, client):
        """Test error logging with exception."""
        test_error = ValueError("test error")
        await client.log_error("Error occurred", {"code": 500}, test_error)

        assert len(client._batch) == 1
        log_entry = client._batch[0]
        assert log_entry["level"] == "error"
        assert "error_type" in log_entry["context"]
        assert "error_message" in log_entry["context"]
        assert log_entry["context"]["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_business_event_logging(self, client):
        """Test business event logging."""
        await client.log_business_event("user_registered", {
            "user_id": 123,
            "plan": "premium"
        })

        assert len(client._batch) == 1
        log_entry = client._batch[0]
        assert log_entry["level"] == "info"
        assert "Business event: user_registered" in log_entry["message"]
        assert log_entry["context"]["event_type"] == "user_registered"
        assert log_entry["context"]["user_id"] == 123

    @pytest.mark.asyncio
    async def test_performance_metric_logging(self, client):
        """Test performance metric logging."""
        await client.log_performance_metric("database_query", 0.145, {"rows": 100})

        assert len(client._batch) == 1
        log_entry = client._batch[0]
        assert "Performance: database_query" in log_entry["message"]
        assert log_entry["context"]["operation"] == "database_query"
        assert log_entry["context"]["duration_seconds"] == 0.145
        assert log_entry["context"]["rows"] == 100
        assert log_entry["context"]["performance_metric"] is True

    @pytest.mark.asyncio
    async def test_batch_flushing(self, client):
        """Test automatic batch flushing."""
        # Mock the session and HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        client._session = AsyncMock()
        client._session.post.return_value = mock_response

        # Add logs to trigger flush
        await client.log_info("Message 1")
        await client.log_info("Message 2")  # This should trigger flush (batch_size=2)

        # Give time for async flush
        await asyncio.sleep(0.05)

        # Check that batch was sent
        assert client._session.post.called
        call_args = client._session.post.call_args
        request_data = call_args[1]["json"]
        assert len(request_data["items"]) == 2

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test client as async context manager."""
        async with LogCollectorClient("test-service") as client:
            assert client._running
            assert client._session is not None

            await client.log_info("Test in context")

        assert not client._running
        assert client._session is None

    @pytest.mark.asyncio
    async def test_get_client_stats(self, client):
        """Test getting client statistics."""
        # Add some logs
        await client.log_info("Test 1")
        await client.log_info("Test 2")

        stats = await client.get_stats()
        assert "batch_queue_size" in stats
        assert "is_running" in stats
        assert stats["is_running"] is True
        assert stats["batch_queue_size"] == 2
        assert stats["logs_sent"] == 0  # Not flushed yet

    @pytest.mark.asyncio
    async def test_error_retry_logic(self, client):
        """Test error handling and retry logic."""
        # Mock session to fail first two times, succeed third
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500

        mock_response_success = Mock()
        mock_response_success.status_code = 200

        client._session = AsyncMock()
        client._session.post.side_effect = [
            mock_response_fail,  # First attempt fails
            mock_response_fail,  # Second attempt fails
            mock_response_success  # Third attempt succeeds
        ]

        await client.log_info("Test message")
        await client.log_info("Test message 2")

        # Manually trigger flush
        await client._flush_batch()

        # Should have been called 3 times (2 retries + 1 success)
        assert client._session.post.call_count == 3
        assert client.stats["retries"] == 2


class TestGlobalClientManagement:
    """Test global client management functions."""

    @pytest.mark.asyncio
    async def test_get_log_collector_client_singleton(self):
        """Test that get_log_collector_client returns singleton instances."""
        client1 = await get_log_collector_client("test-service-1")
        client2 = await get_log_collector_client("test-service-1")
        client3 = await get_log_collector_client("test-service-2")

        # Same service should return same instance
        assert client1 is client2
        # Different service should return different instance
        assert client1 is not client3

        # Clean up
        from services.shared.utilities.logging_client import _clients
        for service_name in ["test-service-1", "test-service-2"]:
            if service_name in _clients:
                await _clients[service_name].stop()

    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test convenience logging functions."""
        # Mock the client to avoid actual HTTP calls
        mock_client = Mock()
        mock_client.log_info = AsyncMock()
        mock_client.log_error = AsyncMock()
        mock_client.log_business_event = AsyncMock()
        mock_client.log_performance_metric = AsyncMock()

        with patch('services.shared.utilities.logging_client.get_log_collector_client',
                  return_value=mock_client):
            # Test service event logging
            await log_service_event("test-service", "info", "Test message", {"key": "value"})
            mock_client.log_info.assert_called_with("Test message", {"key": "value"})

            # Test business event logging
            await log_business_event("test-service", "user_login", {"user_id": 123})
            mock_client.log_business_event.assert_called_with("user_login", {"user_id": 123})

            # Test performance metric logging
            await log_performance_metric("test-service", "api_call", 0.5, {"endpoint": "/api"})
            mock_client.log_performance_metric.assert_called_with("api_call", 0.5, {"endpoint": "/api"})


class TestErrorHandling:
    """Test error handling in logging client."""

    @pytest.mark.asyncio
    async def test_network_failure_fallback(self):
        """Test fallback to local logging when network fails."""
        client = LogCollectorClient("test-service", batch_size=1)

        # Don't start the client (no session) - should fallback to local logging
        await client.log_info("Test message")

        # Should still work without session
        assert len(client._batch) == 1

        # Flush should work with local fallback
        await client._flush_batch()

        # Clean up
        await client.stop()

    @pytest.mark.asyncio
    async def test_malformed_log_handling(self):
        """Test handling of malformed log data."""
        client = LogCollectorClient("test-service")

        # These should not raise exceptions
        await client.log_info(None)  # None message
        await client.log_error("", {})  # Empty message
        await client.log_business_event("test", None)  # None data

        assert len(client._batch) == 3

        await client.stop()

    @pytest.mark.asyncio
    async def test_concurrent_logging(self):
        """Test concurrent logging operations."""
        client = LogCollectorClient("test-service", batch_size=5)

        async def log_worker(worker_id):
            for i in range(10):
                await client.log_info(f"Worker {worker_id} message {i}")

        # Start multiple concurrent workers
        tasks = [asyncio.create_task(log_worker(i)) for i in range(3)]
        await asyncio.gather(*tasks)

        # Should have collected all messages
        assert len(client._batch) == 30

        await client.stop()


class TestIntegrationWithMockCollector:
    """Test integration with mock log collector service."""

    @pytest.mark.asyncio
    async def test_end_to_end_logging_flow(self):
        """Test complete logging flow from client to mock collector."""
        # This would test actual HTTP communication with a mock server
        # For now, just test the client-side batching and stats
        client = LogCollectorClient("test-service", batch_size=3)

        # Add multiple logs
        for i in range(5):
            await client.log_info(f"Message {i}", {"index": i})

        # Check batch accumulation
        assert len(client._batch) == 5

        # Get stats
        stats = await client.get_stats()
        assert stats["batch_queue_size"] == 5
        assert stats["logs_sent"] == 0  # Not flushed yet

        await client.stop()

    @pytest.mark.asyncio
    async def test_service_restart_recovery(self):
        """Test client recovery after service restart."""
        client = LogCollectorClient("test-service")

        # Simulate service being unavailable
        client._session = None

        # Should fallback gracefully
        await client.log_error("Service error", {"code": "CONNECTION_LOST"})

        # Should still have the log in batch
        assert len(client._batch) == 1

        await client.stop()
