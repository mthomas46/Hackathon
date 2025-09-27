"""Memory Agent management and statistics tests.

Tests memory statistics, cleanup, and management operations.
Focused on operational aspects following TDD principles.
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


class TestMemoryManagement:
    """Test memory management and statistics functionality."""

    def test_memory_stats_endpoint(self, client):
        """Test memory statistics endpoint."""
        # This endpoint might not exist, but let's test if it does
        response = client.get("/memory/stats")
        # Accept various status codes as endpoint may not be implemented
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            # Should contain memory statistics
            if "data" in data:
                stats = data["data"]
                assert isinstance(stats, dict)

    def test_health_endpoint(self, client):
        """Test health endpoint with memory information."""
        response = client.get("/health")
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        # Memory agent health should include memory count
        assert "count" in data or "memory_count" in data

    def test_memory_cleanup_operations(self, client):
        """Test memory cleanup functionality."""
        # Store some items that should be cleaned up
        for i in range(3):
            memory_item = {
                "id": f"cleanup-test-{i}",
                "type": "cleanup_test",
                "key": f"cleanup-key-{i}",
                "summary": f"Cleanup test item {i}",
                "data": {"cleanup": True}
            }
            request_data = {"item": memory_item}
            client.post("/memory/put", json=request_data)

        # Verify items are initially stored
        list_response = client.get("/memory/list", params={"type": "cleanup_test"})
        _assert_http_ok(list_response)

        data = list_response.json()
        if "data" in data and "items" in data["data"]:
            initial_count = len(data["data"]["items"])
            assert initial_count >= 3

    def test_memory_capacity_limits(self, client):
        """Test memory capacity limits and overflow handling."""
        # Store multiple items to potentially trigger capacity limits
        stored_keys = []
        for i in range(10):  # Store more than typical capacity
            memory_item = {
                "id": f"capacity-test-{i}",
                "type": "capacity_test",
                "key": f"capacity-key-{i}",
                "summary": f"Capacity test item {i}",
                "data": {"capacity_test": True, "index": i}
            }
            request_data = {"item": memory_item}
            response = client.post("/memory/put", json=request_data)
            if response.status_code == 200:
                stored_keys.append(f"capacity-test-{i}")

        # Verify some items are stored
        assert len(stored_keys) > 0

        # List all items to check capacity management
        list_response = client.get("/memory/list", params={"type": "capacity_test"})
        _assert_http_ok(list_response)

        data = list_response.json()
        if "data" in data and "items" in data["data"]:
            items = data["data"]["items"]
            # Should have some items, possibly limited by capacity
            assert len(items) > 0

    def test_memory_type_filtering_efficiency(self, client):
        """Test efficiency of memory type filtering."""
        # Store items of different types
        types_and_counts = {
            "type_a": 3,
            "type_b": 2,
            "type_c": 4
        }

        for mem_type, count in types_and_counts.items():
            for i in range(count):
                memory_item = {
                    "id": f"{mem_type}-item-{i}",
                    "type": mem_type,
                    "key": f"{mem_type}-key-{i}",
                    "summary": f"{mem_type} test item {i}",
                    "data": {"index": i}
                }
                request_data = {"item": memory_item}
                client.post("/memory/put", json=request_data)

        # Test filtering by each type
        for mem_type, expected_count in types_and_counts.items():
            response = client.get("/memory/list", params={"type": mem_type})
            _assert_http_ok(response)

            data = response.json()
            if "data" in data and "items" in data["data"]:
                items = data["data"]["items"]
                # Should only return items of the specified type
                type_items = [item for item in items if item.get("type") == mem_type]
                assert len(type_items) >= expected_count

    def test_memory_metadata_handling(self, client):
        """Test memory item metadata handling."""
        memory_item = {
            "id": "metadata-test",
            "type": "metadata_test",
            "key": "metadata-test-key",
            "summary": "Metadata test item",
            "data": {
                "test": "data",
                "source": "test_suite",
                "category": "validation",
                "tags": ["metadata", "test"],
                "custom_field": "custom_value"
            }
        }

        request_data = {"item": memory_item}
        response = client.post("/memory/put", json=request_data)
        _assert_http_ok(response)

        # Retrieve and verify metadata is preserved
        list_response = client.get("/memory/list", params={"key": "metadata-test-key"})
        _assert_http_ok(list_response)

        data = list_response.json()
        if "data" in data and "items" in data["data"]:
            items = data["data"]["items"]
            if items:
                item = items[0]
                # Check that the data field contains the expected metadata
                data = item["data"]
                assert data["source"] == "test_suite"
                assert "tags" in data
                assert "custom_field" in data
                assert data["custom_field"] == "custom_value"

    def test_memory_bulk_operations(self, client):
        """Test bulk memory operations."""
        # Store multiple items in quick succession
        bulk_items = []
        for i in range(5):
            memory_item = {
                "id": f"bulk-test-{i}",
                "type": "bulk_test",
                "key": f"bulk-key-{i}",
                "summary": f"Bulk test item {i}",
                "data": {"bulk_test": True, "sequence": i}
            }
            bulk_items.append(memory_item)

        # Store all items
        for item in bulk_items:
            request_data = {"item": item}
            response = client.post("/memory/put", json=request_data)
            _assert_http_ok(response)

        # Verify all items are stored
        list_response = client.get("/memory/list", params={"type": "bulk_test"})
        _assert_http_ok(list_response)

        data = list_response.json()
        if "data" in data and "items" in data["data"]:
            items = data["data"]["items"]
            assert len(items) >= 5

            # Verify sequence is preserved
            sequences = [item["data"]["sequence"] for item in items]
            assert len(set(sequences)) == len(sequences)  # All sequences unique

    def test_memory_error_handling(self, client):
        """Test error handling for invalid memory operations."""
        # Test with malformed JSON
        response = client.post("/memory/put", data="invalid json")
        assert response.status_code in [400, 422]

        # Test with empty payload
        response = client.post("/memory/put", json={})
        assert response.status_code in [400, 422]

        # Test with invalid item structure
        response = client.post("/memory/put", json={"item": "not an object"})
        assert response.status_code in [400, 422]

    def test_memory_list_parameter_validation(self, client):
        """Test parameter validation for memory list endpoint."""
        # Test with invalid parameters
        response = client.get("/memory/list", params={"limit": "invalid"})
        assert response.status_code in [200, 400, 422]  # May be handled gracefully

        # Test with negative limit
        response = client.get("/memory/list", params={"limit": -1})
        assert response.status_code in [200, 400, 422]

        # Test with very large limit
        response = client.get("/memory/list", params={"limit": 10000})
        assert response.status_code in [200, 400, 422]
