"""Notification Service owner resolution tests.

Tests owner-to-target mapping and resolution functionality.
Focused on owner management and caching following TDD principles.
"""
import pytest
from fastapi.testclient import TestClient

from .test_utils import load_notification_service


@pytest.fixture(scope="module")
def client():
    """Test client fixture for notification service."""
    app = load_notification_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


def _assert_http_ok(response):
    """Assert HTTP 200 response."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestNotificationOwners:
    """Test owner resolution and management functionality."""

    def test_owners_update_basic(self, client):
        """Test basic owner update functionality."""
        owner_data = {
            "id": "test-resource-1",
            "owner": "alice@example.com",
            "team": "platform-team"
        }

        response = client.post("/owners/update", json=owner_data)
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert "id" in data
        assert data["id"] == "test-resource-1"
        assert "owner" in data
        assert "team" in data

    def test_owners_update_minimal(self, client):
        """Test owner update with minimal fields."""
        owner_data = {
            "id": "test-resource-2"
            # No owner or team specified
        }

        response = client.post("/owners/update", json=owner_data)
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["id"] == "test-resource-2"
        # Owner and team should be None or empty

    def test_owners_resolve_basic(self, client):
        """Test basic owner resolution."""
        resolve_data = {
            "owners": ["alice@example.com", "bob@example.com"]
        }

        response = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(response)

        data = response.json()
        assert "resolved" in data
        resolved = data["resolved"]
        assert isinstance(resolved, dict)

        # Should have entries for both owners
        assert "alice@example.com" in resolved
        assert "bob@example.com" in resolved

    def test_owners_resolve_empty_list(self, client):
        """Test owner resolution with empty owner list."""
        resolve_data = {
            "owners": []
        }

        response = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(response)

        data = response.json()
        assert "resolved" in data
        resolved = data["resolved"]
        assert isinstance(resolved, dict)
        assert len(resolved) == 0

    def test_owners_resolve_heuristics_webhook(self, client):
        """Test owner resolution heuristics for webhook URLs."""
        resolve_data = {
            "owners": ["https://hooks.slack.com/services/ABC/DEF/GHI"]
        }

        response = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(response)

        data = response.json()
        resolved = data["resolved"]
        webhook_owner = resolved["https://hooks.slack.com/services/ABC/DEF/GHI"]
        assert isinstance(webhook_owner, dict)
        assert "webhook" in webhook_owner

    def test_owners_resolve_heuristics_email(self, client):
        """Test owner resolution heuristics for email addresses."""
        resolve_data = {
            "owners": ["support@company.com"]
        }

        response = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(response)

        data = response.json()
        resolved = data["resolved"]
        email_owner = resolved["support@company.com"]
        assert isinstance(email_owner, dict)
        assert "email" in email_owner

    def test_owners_resolve_heuristics_handle(self, client):
        """Test owner resolution heuristics for plain handles."""
        resolve_data = {
            "owners": ["platform-team"]
        }

        response = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(response)

        data = response.json()
        resolved = data["resolved"]
        handle_owner = resolved["platform-team"]
        assert isinstance(handle_owner, dict)
        assert "handle" in handle_owner

    def test_owners_resolve_caching(self, client):
        """Test owner resolution caching functionality."""
        resolve_data = {
            "owners": ["cache-test@example.com"]
        }

        # First resolution should work
        response1 = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(response1)

        # Second resolution should use cache
        response2 = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(response2)

        data2 = response2.json()
        resolved = data2["resolved"]
        assert "cache-test@example.com" in resolved

    def test_owners_resolve_mixed_types(self, client):
        """Test owner resolution with mixed owner types."""
        resolve_data = {
            "owners": [
                "alice@example.com",  # Email
                "https://webhook.example.com/notify",  # Webhook
                "devops-team",  # Handle
                "invalid-owner-format"  # Should still resolve
            ]
        }

        response = client.post("/owners/resolve", json=resolve_data)
        _assert_http_ok(response)

        data = response.json()
        resolved = data["resolved"]
        assert len(resolved) == 4

        # Check that all owners were resolved
        for owner in resolve_data["owners"]:
            assert owner in resolved
            assert isinstance(resolved[owner], dict)

    def test_owners_resolve_validation(self, client):
        """Test owner resolution input validation."""
        # Test with missing owners field
        invalid_data = {}

        response = client.post("/owners/resolve", json=invalid_data)
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            assert "resolved" in data

    def test_owners_update_validation(self, client):
        """Test owner update input validation."""
        # Test with missing required id field
        invalid_data = {
            "owner": "test@example.com"
            # Missing id
        }

        response = client.post("/owners/update", json=invalid_data)
        # Should return validation error
        assert response.status_code in [400, 422]

        if response.status_code in [400, 422]:
            data = response.json()
            assert "detail" in data

    def test_owners_resolve_null_owners(self, client):
        """Test owner resolution with null owners list."""
        resolve_data = {
            "owners": None
        }

        response = client.post("/owners/resolve", json=resolve_data)
        # Should return validation error for null owners
        assert response.status_code == 422

        if response.status_code == 422:
            data = response.json()
            assert "detail" in data
            # Validation should indicate list type required
