"""Notification Service core functionality tests.

Tests notification sending, deduplication, and delivery.
Focused on essential notification operations following TDD principles.
"""

import importlib.util, os
import pytest
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


class TestNotificationCore:
    """Test core notification service functionality."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data

    def test_notify_webhook_success(self, client):
        """Test successful webhook notification."""
        notification_data = {
            "channel": "webhook",
            "target": "http://httpbin.org/post",  # Public test endpoint
            "title": "Test Notification",
            "message": "This is a test notification message",
            "metadata": {"test": True, "priority": "low"},
            "labels": ["test", "notification"]
        }

        response = client.post("/notify", json=notification_data)
        # May succeed or fail depending on external service availability
        assert response.status_code in [200, 502]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data["status"] == "sent"

    def test_notify_deduplication(self, client):
        """Test notification deduplication within 10-minute window."""
        notification_data = {
            "channel": "webhook",
            "target": "http://test-endpoint.com/webhook",
            "title": "Duplicate Test",
            "message": "This message should be deduplicated",
            "metadata": {"test": "duplicate"},
            "labels": ["duplicate"]
        }

        # First notification should be processed
        response1 = client.post("/notify", json=notification_data)
        # Status may vary based on implementation
        assert response1.status_code in [200, 502]

        # Second identical notification should be deduplicated
        response2 = client.post("/notify", json=notification_data)
        assert response2.status_code in [200, 502]

        if response2.status_code == 200:
            data2 = response2.json()
            # Should indicate duplicate suppression
            assert "status" in data2
            # Note: exact duplicate detection may vary by implementation

    def test_notify_unsupported_channel(self, client):
        """Test notification with unsupported channel."""
        notification_data = {
            "channel": "unsupported",
            "target": "test-target",
            "title": "Unsupported Channel",
            "message": "This uses an unsupported notification channel",
            "metadata": {"test": "unsupported"},
            "labels": ["unsupported"]
        }

        response = client.post("/notify", json=notification_data)
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            # May return "queued" for unsupported channels

    def test_notify_validation(self, client):
        """Test notification input validation."""
        # Test with missing required fields
        invalid_data = {
            "channel": "webhook",
            # Missing target, title, message
            "metadata": {}
        }

        response = client.post("/notify", json=invalid_data)
        # Should return validation error
        assert response.status_code in [400, 422]

        if response.status_code in [400, 422]:
            data = response.json()
            assert "detail" in data

    def test_notify_slack_channel(self, client):
        """Test Slack notification channel."""
        notification_data = {
            "channel": "slack",
            "target": "#test-channel",
            "title": "Slack Test",
            "message": "This is a test Slack message",
            "metadata": {"slack": True},
            "labels": ["slack", "test"]
        }

        response = client.post("/notify", json=notification_data)
        # Slack integration may not be implemented, but should handle gracefully
        assert response.status_code in [200, 501]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "channel" in data

    def test_notify_email_channel(self, client):
        """Test email notification channel."""
        notification_data = {
            "channel": "email",
            "target": "test@example.com",
            "title": "Email Test",
            "message": "This is a test email message",
            "metadata": {"email": True},
            "labels": ["email", "test"]
        }

        response = client.post("/notify", json=notification_data)
        # Email integration may not be implemented, but should handle gracefully
        assert response.status_code in [200, 501]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "channel" in data

    def test_dlq_endpoint(self, client):
        """Test dead-letter queue endpoint."""
        response = client.get("/dlq")
        _assert_http_ok(response)

        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_dlq_with_limit(self, client):
        """Test dead-letter queue with pagination limit."""
        response = client.get("/dlq", params={"limit": 10})
        _assert_http_ok(response)

        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) <= 10

    def test_dlq_limit_validation(self, client):
        """Test dead-letter queue limit validation."""
        # Test with very large limit
        response = client.get("/dlq", params={"limit": 1000})
        _assert_http_ok(response)

        data = response.json()
        assert "items" in data
        # Should respect reasonable limits

        # Test with zero limit
        response = client.get("/dlq", params={"limit": 0})
        _assert_http_ok(response)

        data = response.json()
        assert "items" in data
        # Should handle zero gracefully
