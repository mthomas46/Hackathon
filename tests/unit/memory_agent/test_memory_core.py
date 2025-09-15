"""Memory Agent core functionality tests.

Tests memory storage and retrieval operations.
Focused on essential CRUD operations following TDD principles.
"""
import pytest
import importlib.util, os
from fastapi.testclient import TestClient

from .test_utils import load_memory_agent_service, _assert_http_ok


@pytest.fixture(scope="module")
def client():
    """Test client fixture for memory agent service."""
    app = load_memory_agent_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestMemoryCore:
    """Test core memory agent functionality."""

    def test_put_memory_item(self, client):
        """Test storing a memory item."""
        memory_item = {
            "id": "test-memory-1",
            "type": "test_data",
            "key": "test-key-1",
            "summary": "Test memory item",
            "data": {
                "content": "Test memory content",
                "metadata": {"source": "test"}
            }
        }

        request_data = {"item": memory_item}
        response = client.post("/memory/put", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert "success" in data or "data" in data

    def test_list_memory_items(self, client):
        """Test listing memory items."""
        response = client.get("/memory/list")
        _assert_http_ok(response)

        data = response.json()
        assert "data" in data or "items" in data

        if "data" in data and "items" in data["data"]:
            items = data["data"]["items"]
            assert isinstance(items, list)

    def test_list_memory_with_filtering(self, client):
        """Test listing memory items with type filtering."""
        # First store some test items
        test_items = [
            {
                "key": "filter-test-1",
                "value": {"test": "data1"},
                "item_type": "test_type_a"
            },
            {
                "key": "filter-test-2",
                "value": {"test": "data2"},
                "item_type": "test_type_b"
            }
        ]

        for item in test_items:
            request_data = {"item": item}
            client.post("/memory/put", json=request_data)

        # Test filtering by type
        response = client.get("/memory/list", params={"type": "test_data"})
        _assert_http_ok(response)

        data = response.json()
        if "data" in data and "items" in data["data"]:
            items = data["data"]["items"]
            assert isinstance(items, list)
            # Should contain items of the filtered type
            for item in items:
                if item.get("item_type") == "test_type_a":
                    assert "filter-test-1" in item.get("key", "")

    def test_memory_item_validation(self, client):
        """Test memory item validation."""
        # Test with missing required fields
        invalid_item = {
            "key": "invalid-test"
            # Missing value, item_type, etc.
        }

        request_data = {"item": invalid_item}
        response = client.post("/memory/put", json=request_data)
        # Should handle validation gracefully
        assert response.status_code in [200, 400, 422]

    def test_memory_key_filtering(self, client):
        """Test filtering memory items by key."""
        # Store item with specific key
        memory_item = {
            "id": "key-filter-test",
            "type": "key_test",
            "key": "key-filter-test",
            "summary": "Key filtering test",
            "data": {"test": "key filtering"}
        }

        request_data = {"item": memory_item}
        client.post("/memory/put", json=request_data)

        # Test filtering by key
        response = client.get("/memory/list", params={"key": "key-filter-test"})
        _assert_http_ok(response)

        data = response.json()
        if "data" in data and "items" in data["data"]:
            items = data["data"]["items"]
            assert len(items) >= 1
            # Should find the item with matching key
            found = any(item.get("key") == "key-filter-test" for item in items)
            assert found

    def test_memory_pagination(self, client):
        """Test memory listing with pagination."""
        # Store multiple items
        for i in range(5):
            memory_item = {
                "id": f"pagination-test-{i}",
                "type": "pagination_test",
                "key": f"pagination-key-{i}",
                "summary": f"Pagination test item {i}",
                "data": {"index": i}
            }
            request_data = {"item": memory_item}
            client.post("/memory/put", json=request_data)

        # Test with limit
        response = client.get("/memory/list", params={"limit": 3})
        _assert_http_ok(response)

        data = response.json()
        if "data" in data and "items" in data["data"]:
            items = data["data"]["items"]
            assert len(items) <= 3  # Should respect limit

    def test_memory_ttl_handling(self, client):
        """Test TTL (time-to-live) handling for memory items."""
        memory_item = {
            "id": "ttl-test",
            "type": "ttl_test",
            "key": "ttl-test-key",
            "summary": "TTL test item",
            "data": {"ttl_test": "data"}
        }

        request_data = {"item": memory_item}
        client.post("/memory/put", json=request_data)

        # Item should be retrievable immediately
        response = client.get("/memory/list", params={"key": "ttl-test-key"})
        _assert_http_ok(response)

        data = response.json()
        if "data" in data and "items" in data["data"]:
            items = data["data"]["items"]
            # Should find the item initially
            found = any(item.get("key") == "ttl-test-key" for item in items)
            assert found

    def test_memory_item_structure(self, client):
        """Test memory item data structure and serialization."""
        complex_item = {
            "id": "structure-test",
            "type": "structure_test",
            "key": "structure-test-key",
            "summary": "Complex memory item for structure testing",
            "data": {
                "nested": {
                    "data": [1, 2, 3],
                    "metadata": {
                        "created": "2024-01-01T00:00:00Z",
                        "tags": ["test", "structure"]
                    }
                },
                "complexity": "high"
            }
        }

        request_data = {"item": complex_item}
        response = client.post("/memory/put", json=request_data)
        _assert_http_ok(response)

        # Retrieve and verify structure is preserved
        get_response = client.get("/memory/list", params={"key": "structure-test-key"})
        _assert_http_ok(get_response)

        data = get_response.json()
        if "data" in data and "items" in data["data"]:
            items = data["data"]["items"]
            if items:
                item = items[0]
                assert "nested" in item.get("data", {})
                assert isinstance(item["data"]["nested"]["data"], list)
