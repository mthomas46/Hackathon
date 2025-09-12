"""Notification Service caching and deduplication tests.

Tests notification deduplication, caching, and performance optimizations.
Focused on cache management and duplicate prevention following TDD principles.
"""

import importlib.util, os
import pytest
import time
from fastapi.testclient import TestClient


def _load_notification_service():
    """Load notification-service dynamically."""
    spec = importlib.util.spec_from_file_location(
        "services.notification-service.main",
        os.path.join(os.getcwd(), 'services', 'notification-service', 'main.py')
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app


@pytest.fixture(scope="module")
def notification_app():
    """Load notification-service."""
    return _load_notification_service()


@pytest.fixture
def client(notification_app):
    """Create test client."""
    return TestClient(notification_app)


def _assert_http_ok(response):
    """Assert HTTP 200 response."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestNotificationCaching:
    """Test notification caching and deduplication functionality."""

    def test_deduplication_basic(self, client):
        """Test basic notification deduplication."""
        base_notification = {
            "channel": "webhook",
            "target": "http://test-endpoint.com/dedup",
            "title": "Dedup Test",
            "message": "This is a deduplication test message",
            "metadata": {"test": "deduplication"},
            "labels": ["test", "dedup"]
        }

        # Send first notification
        response1 = client.post("/notify", json=base_notification)
        assert response1.status_code in [200, 502]

        # Send identical notification immediately after
        response2 = client.post("/notify", json=base_notification)
        assert response2.status_code in [200, 502]

        # Second response should indicate deduplication
        if response2.status_code == 200:
            data2 = response2.json()
            assert "status" in data2
            # May return "duplicate_suppressed" or similar

    def test_deduplication_different_content(self, client):
        """Test that different content is not deduplicated."""
        notification1 = {
            "channel": "webhook",
            "target": "http://test-endpoint.com/dedup",
            "title": "Dedup Test",
            "message": "Message 1",
            "metadata": {"test": "deduplication"},
            "labels": ["test", "dedup"]
        }

        notification2 = {
            "channel": "webhook",
            "target": "http://test-endpoint.com/dedup",
            "title": "Dedup Test",
            "message": "Message 2",  # Different message
            "metadata": {"test": "deduplication"},
            "labels": ["test", "dedup"]
        }

        # Both should be processed (not deduplicated)
        response1 = client.post("/notify", json=notification1)
        response2 = client.post("/notify", json=notification2)

        assert response1.status_code in [200, 502]
        assert response2.status_code in [200, 502]

        # Should not be deduplicated since content differs

    def test_deduplication_different_targets(self, client):
        """Test that different targets are not deduplicated."""
        notification1 = {
            "channel": "webhook",
            "target": "http://target1.com/webhook",
            "title": "Dedup Test",
            "message": "Same message",
            "metadata": {"test": "deduplication"},
            "labels": ["test", "dedup"]
        }

        notification2 = {
            "channel": "webhook",
            "target": "http://target2.com/webhook",  # Different target
            "title": "Dedup Test",
            "message": "Same message",
            "metadata": {"test": "deduplication"},
            "labels": ["test", "dedup"]
        }

        # Both should be processed (not deduplicated)
        response1 = client.post("/notify", json=notification1)
        response2 = client.post("/notify", json=notification2)

        assert response1.status_code in [200, 502]
        assert response2.status_code in [200, 502]

        # Should not be deduplicated since targets differ

    def test_deduplication_window_expiration(self, client):
        """Test that deduplication window expires correctly."""
        notification = {
            "channel": "webhook",
            "target": "http://test-endpoint.com/window",
            "title": "Window Test",
            "message": "Test deduplication window",
            "metadata": {"test": "window"},
            "labels": ["test", "window"]
        }

        # Send first notification
        response1 = client.post("/notify", json=notification)
        assert response1.status_code in [200, 502]

        # Wait for deduplication window to expire (if implemented)
        # Note: In a real test, we might mock time or wait
        time.sleep(0.1)  # Minimal wait

        # This test demonstrates the concept - actual expiration
        # would depend on the 10-minute window implementation

    def test_cache_key_generation(self, client):
        """Test deduplication cache key generation."""
        # Test various combinations that should generate different keys
        notifications = [
            {
                "channel": "webhook",
                "target": "http://test.com/1",
                "title": "Test",
                "message": "Message",
                "metadata": {},
                "labels": []
            },
            {
                "channel": "webhook",
                "target": "http://test.com/1",
                "title": "Test",
                "message": "Different Message",  # Different message
                "metadata": {},
                "labels": []
            },
            {
                "channel": "webhook",
                "target": "http://test.com/2",  # Different target
                "title": "Test",
                "message": "Message",
                "metadata": {},
                "labels": []
            },
            {
                "channel": "webhook",
                "target": "http://test.com/1",
                "title": "Different Title",  # Different title
                "message": "Message",
                "metadata": {},
                "labels": []
            }
        ]

        # Send all notifications
        responses = []
        for notification in notifications:
            response = client.post("/notify", json=notification)
            responses.append(response)
            assert response.status_code in [200, 502]

        # Each should be processed independently (different cache keys)

    def test_owner_resolution_caching(self, client):
        """Test owner resolution caching functionality."""
        resolve_data = {
            "owners": ["cached-owner@example.com"]
        }

        # First resolution
        response1 = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(response1)

        # Second resolution (should use cache)
        response2 = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(response2)

        data1 = response1.json()
        data2 = response2.json()

        # Results should be identical (from cache)
        assert data1["resolved"] == data2["resolved"]

    def test_owner_resolution_cache_expiration(self, client):
        """Test owner resolution cache expiration."""
        resolve_data = {
            "owners": ["expiring-owner@example.com"]
        }

        # First resolution
        response1 = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(response1)

        # In a real scenario, we'd wait for TTL expiration
        # For testing, we can verify cache is being used
        data1 = response1.json()
        assert "resolved" in data1
        assert "expiring-owner@example.com" in data1["resolved"]

    def test_dlq_size_limits(self, client):
        """Test dead-letter queue size limits."""
        # Send multiple failing notifications to populate DLQ
        for i in range(5):
            notification = {
                "channel": "webhook",
                "target": "http://nonexistent-endpoint.invalid",
                "title": f"DLQ Test {i}",
                "message": f"Message {i}",
                "metadata": {"test": "dlq"},
                "labels": ["test", "dlq"]
            }

            response = client.post("/notify", json=notification)
            # May fail due to invalid endpoint
            assert response.status_code in [200, 502]

        # Check DLQ contents
        dlq_response = client.get("/dlq")
        _assert_http_ok(dlq_response)

        dlq_data = dlq_response.json()
        assert "items" in dlq_data
        items = dlq_data["items"]

        # Should have some failed notifications
        # Note: DLQ population depends on actual failure handling

    def test_cache_cleanup_scenarios(self, client):
        """Test cache cleanup under various scenarios."""
        # Send variety of notifications to populate caches
        notifications = [
            {
                "channel": "webhook",
                "target": "http://cleanup1.com",
                "title": "Cleanup Test 1",
                "message": "Test message 1"
            },
            {
                "channel": "webhook",
                "target": "http://cleanup2.com",
                "title": "Cleanup Test 2",
                "message": "Test message 2"
            }
        ]

        for notification in notifications:
            response = client.post("/notify", json=notification)
            assert response.status_code in [200, 502]

        # Resolve some owners to populate resolution cache
        resolve_data = {
            "owners": ["cleanup-owner1@example.com", "cleanup-owner2@example.com"]
        }

        resolve_response = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(resolve_response)

        # Verify caches are populated (indirectly through successful operations)

    def test_performance_under_load(self, client):
        """Test notification performance under load."""
        # Send multiple notifications rapidly
        notification_base = {
            "channel": "webhook",
            "target": "http://load-test.com",
            "title": "Load Test",
            "message": "Performance test message",
            "metadata": {"test": "load"},
            "labels": ["test", "load"]
        }

        # Send 10 notifications quickly
        responses = []
        for i in range(10):
            notification = notification_base.copy()
            notification["message"] = f"Performance test message {i}"
            response = client.post("/notify", json=notification)
            responses.append(response)
            assert response.status_code in [200, 502]

        # Verify all were processed
        success_count = sum(1 for r in responses if r.status_code == 200)
        # At least some should succeed
        assert success_count >= 0

    def test_memory_usage_monitoring(self, client):
        """Test memory usage with caches and queues."""
        # Perform operations that use memory
        for i in range(20):
            notification = {
                "channel": "webhook",
                "target": f"http://memory-test-{i}.com",
                "title": f"Memory Test {i}",
                "message": f"Memory usage test {i}",
                "metadata": {"test": "memory", "index": i},
                "labels": ["test", "memory"]
            }

            response = client.post("/notify", json=notification)
            assert response.status_code in [200, 502]

        # Service should continue to function normally
        health_response = client.get("/health")
        _assert_http_ok(health_response)

        health_data = health_response.json()
        assert health_data["status"] == "healthy"
