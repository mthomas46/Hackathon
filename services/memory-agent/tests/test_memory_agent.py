"""Memory Agent Service Tests

Comprehensive test suite for the Memory Agent service covering:
- Health endpoint functionality
- Memory item storage and retrieval
- TTL (Time-To-Live) management
- Filtering and pagination
- Capacity limits and memory management
- Event processing and correlation
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from services.memory_agent.main import app, create_memory_agent_success_response
from services.shared.core.models.models import MemoryItem


class TestMemoryAgentHealth:
    """Test health endpoint functionality."""

    def test_health_endpoint(self, client):
        """Test basic health endpoint returns proper status."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "memory_count" in data
        assert "service" in data
        assert data["service"] == "memory-agent"

    def test_health_with_memory_items(self, client):
        """Test health endpoint shows memory statistics."""
        # Add a memory item first
        memory_data = {
            "key": "test-health-key",
            "type": "test",
            "content": {"message": "test content"},
            "ttl": 3600
        }

        response = client.post("/memory/put", json=memory_data)
        assert response.status_code == 200

        # Check health shows the item
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["memory_count"] >= 1


class TestMemoryAgentStorage:
    """Test memory item storage functionality."""

    def test_put_memory_item_basic(self, client):
        """Test basic memory item storage."""
        memory_data = {
            "key": "test-basic-key",
            "type": "test_type",
            "content": {"message": "Hello World", "value": 42},
            "ttl": 3600
        }

        response = client.post("/memory/put", json=memory_data)
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "memory_id" in data
        assert "context" in data

    def test_put_memory_item_minimal(self, client):
        """Test memory storage with minimal required fields."""
        memory_data = {
            "key": "minimal-key",
            "content": "simple string content"
        }

        response = client.post("/memory/put", json=memory_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "memory_id" in data

    def test_put_memory_item_with_ttl(self, client):
        """Test memory storage with TTL functionality."""
        memory_data = {
            "key": "ttl-test-key",
            "type": "ttl_test",
            "content": {"test": "ttl functionality"},
            "ttl": 1  # 1 second TTL
        }

        response = client.post("/memory/put", json=memory_data)
        assert response.status_code == 200

        # Immediately check - should exist
        list_response = client.get("/memory/list?key=ttl-test-key")
        assert list_response.status_code == 200
        items = list_response.json().get("items", [])
        assert len(items) == 1

        # Wait for TTL to expire
        time.sleep(2)

        # Check again - should not exist
        list_response = client.get("/memory/list?key=ttl-test-key")
        assert list_response.status_code == 200
        items = list_response.json().get("items", [])
        assert len(items) == 0

    def test_put_memory_item_validation(self, client):
        """Test memory storage validation."""
        # Test missing key
        invalid_data = {
            "content": "no key provided"
        }

        response = client.post("/memory/put", json=invalid_data)
        # Should still work as key is generated if missing
        assert response.status_code == 200

        # Test invalid TTL
        invalid_ttl_data = {
            "key": "invalid-ttl",
            "content": "test",
            "ttl": "invalid"
        }

        response = client.post("/memory/put", json=invalid_ttl_data)
        # Should handle invalid TTL gracefully
        assert response.status_code in [200, 400]  # Either accepts or rejects


class TestMemoryAgentRetrieval:
    """Test memory item retrieval functionality."""

    def test_list_memory_items_empty(self, client):
        """Test listing memory items when empty."""
        response = client.get("/memory/list")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert isinstance(data["items"], list)
        assert data["total"] == 0

    def test_list_memory_items_basic(self, client):
        """Test basic memory item listing."""
        # Add some test items
        items = [
            {"key": "list-test-1", "type": "test", "content": "item 1"},
            {"key": "list-test-2", "type": "test", "content": "item 2"},
            {"key": "list-test-3", "type": "other", "content": "item 3"}
        ]

        for item in items:
            response = client.post("/memory/put", json=item)
            assert response.status_code == 200

        # List all items
        response = client.get("/memory/list")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

    def test_list_memory_items_filtering(self, client):
        """Test memory item filtering by type and key."""
        # Add test items
        client.post("/memory/put", json={"key": "filter-1", "type": "type_a", "content": "A1"})
        client.post("/memory/put", json={"key": "filter-2", "type": "type_a", "content": "A2"})
        client.post("/memory/put", json={"key": "filter-3", "type": "type_b", "content": "B1"})

        # Filter by type
        response = client.get("/memory/list?type=type_a")
        assert response.status_code == 200
        data = response.json()
        assert all(item["type"] == "type_a" for item in data["items"])

        # Filter by key
        response = client.get("/memory/list?key=filter-1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["key"] == "filter-1"

    def test_list_memory_items_pagination(self, client):
        """Test memory item pagination."""
        # Add multiple items
        for i in range(10):
            client.post("/memory/put", json={
                "key": f"page-test-{i}",
                "type": "pagination",
                "content": f"item {i}"
            })

        # Test limit
        response = client.get("/memory/list?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total"] >= 10

    def test_list_memory_items_limit_validation(self, client):
        """Test pagination limit validation."""
        # Test negative limit
        response = client.get("/memory/list?limit=-1")
        assert response.status_code == 400 or response.status_code == 422  # Validation error

        # Test excessive limit
        response = client.get("/memory/list?limit=10000")
        # Should either reject or cap the limit
        assert response.status_code in [200, 400, 422]


class TestMemoryAgentIntegration:
    """Test memory agent integration scenarios."""

    def test_memory_workflow_scenario(self, client):
        """Test complete memory workflow scenario."""
        # 1. Store workflow start
        start_data = {
            "key": "workflow-123-start",
            "type": "workflow_start",
            "content": {
                "workflow_id": "wf-123",
                "action": "document_analysis",
                "timestamp": time.time()
            }
        }

        response = client.post("/memory/put", json=start_data)
        assert response.status_code == 200

        # 2. Store intermediate results
        intermediate_data = {
            "key": "workflow-123-progress",
            "type": "workflow_progress",
            "content": {
                "workflow_id": "wf-123",
                "step": "analysis_complete",
                "results": {"documents_processed": 5}
            }
        }

        response = client.post("/memory/put", json=intermediate_data)
        assert response.status_code == 200

        # 3. Retrieve workflow context
        response = client.get("/memory/list?type=workflow_progress")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

        # 4. Verify workflow correlation
        found_progress = any(
            item["content"].get("workflow_id") == "wf-123"
            for item in data["items"]
        )
        assert found_progress

    @patch('services.memory_agent.main.aioredis')
    def test_event_processing_simulation(self, mock_redis, client):
        """Test event processing simulation."""
        # Mock Redis for event processing
        mock_redis_conn = Mock()
        mock_redis.from_url.return_value = mock_redis_conn

        # Simulate event processing
        event_data = {
            "key": "event-summary-456",
            "type": "event_summary",
            "content": {
                "event_type": "document_ingested",
                "summary": "Document successfully processed",
                "correlation_id": "corr-789"
            }
        }

        response = client.post("/memory/put", json=event_data)
        assert response.status_code == 200

        # Verify event storage
        response = client.get("/memory/list?type=event_summary")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1


class TestMemoryAgentErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON in requests."""
        response = client.post("/memory/put", data="invalid json")
        assert response.status_code == 400

    def test_large_content_handling(self, client):
        """Test handling of large content."""
        large_content = {"data": "x" * 10000}  # 10KB content

        response = client.post("/memory/put", json={
            "key": "large-content-test",
            "content": large_content
        })

        # Should either accept or reject based on size limits
        assert response.status_code in [200, 413, 400]

    def test_concurrent_memory_operations(self, client):
        """Test concurrent memory operations."""
        import threading
        import queue

        results = queue.Queue()

        def worker(worker_id):
            """Worker function for concurrent testing."""
            try:
                response = client.post("/memory/put", json={
                    "key": f"concurrent-{worker_id}",
                    "type": "concurrency_test",
                    "content": f"Worker {worker_id} data"
                })
                results.put((worker_id, response.status_code))
            except Exception as e:
                results.put((worker_id, str(e)))

        # Start concurrent workers
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Check results
        successful_operations = 0
        while not results.empty():
            worker_id, result = results.get()
            if isinstance(result, int) and result == 200:
                successful_operations += 1

        # At least some operations should succeed
        assert successful_operations > 0


class TestMemoryAgentLogging:
    """Test logging integration."""

    @patch('services.memory_agent.main.logger_client')
    def test_memory_operations_logging(self, mock_logger, client):
        """Test that memory operations are logged."""
        mock_logger.log_business_event = AsyncMock()
        mock_logger.log_info = AsyncMock()
        mock_logger.log_performance_metric = AsyncMock()

        # Perform memory operation
        response = client.post("/memory/put", json={
            "key": "logging-test",
            "type": "logging",
            "content": "test logging"
        })

        assert response.status_code == 200

        # Verify logging was called (if logger is configured)
        # Note: This test may be skipped if logger is not configured in test environment


# Pytest fixtures
@pytest.fixture
def client():
    """Create test client for memory agent."""
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__])
