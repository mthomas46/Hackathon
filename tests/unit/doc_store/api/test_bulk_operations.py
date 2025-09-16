"""Doc Store API Bulk Operations Tests.

Tests for bulk operations functionality at the API endpoint level.
"""

import pytest
import json
import uuid


@pytest.mark.api
class TestBulkDocumentCreation:
    """Test bulk document creation operations."""

    def test_bulk_create_documents_success(self, client):
        """Test successful bulk document creation."""
        documents = [
            {
                "content": "Bulk document one for testing.",
                "metadata": {"batch": "test", "index": 1}
            },
            {
                "content": "Bulk document two for testing.",
                "metadata": {"batch": "test", "index": 2}
            }
        ]

        response = client.post("/api/v1/bulk/documents", json={"documents": documents})
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        bulk_result = data["data"]
        assert "operation_id" in bulk_result
        assert "operation_type" in bulk_result
        assert bulk_result["operation_type"] == "create_documents"

    def test_bulk_create_documents_empty_list(self, client):
        """Test bulk creation with empty document list."""
        response = client.post("/api/v1/bulk/documents", json={"documents": []})
        # Should handle validation gracefully
        assert response.status_code in [200, 422, 400]

    def test_bulk_create_documents_large_batch(self, client):
        """Test bulk creation with large number of documents."""
        documents = [
            {
                "content": f"Large batch document {i}.",
                "metadata": {"batch": "large", "index": i}
            }
            for i in range(10)
        ]

        response = client.post("/api/v1/bulk/documents", json={"documents": documents})
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_bulk_create_documents_validation_error(self, client):
        """Test bulk creation with invalid documents."""
        invalid_documents = [
            {"metadata": {"test": "missing content"}},  # Missing content
            {"content": "", "metadata": {}},  # Empty content
        ]

        response = client.post("/api/v1/bulk/documents", json={"documents": invalid_documents})
        # Should handle validation errors gracefully
        assert response.status_code in [200, 422, 400]


@pytest.mark.api
class TestBulkOperationsListing:
    """Test bulk operations listing and status."""

    def test_list_bulk_operations(self, client):
        """Test listing bulk operations."""
        response = client.get("/api/v1/bulk/operations")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        result = data["data"]
        assert "operations" in result
        assert "total" in result
        assert isinstance(result["operations"], list)

    def test_list_bulk_operations_with_filters(self, client):
        """Test listing bulk operations with status filter."""
        # Test different status filters
        for status in ["pending", "processing", "completed", "failed"]:
            response = client.get(f"/api/v1/bulk/operations?status={status}")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

    def test_list_bulk_operations_with_limit(self, client):
        """Test listing bulk operations with custom limit."""
        for limit in [1, 5, 10, 50]:
            response = client.get(f"/api/v1/bulk/operations?limit={limit}")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

            result = data["data"]
            assert len(result["operations"]) <= limit

    def test_list_bulk_operations_invalid_limit(self, client):
        """Test listing with invalid limit."""
        response = client.get("/api/v1/bulk/operations?limit=-1")
        assert response.status_code == 422  # Validation error

        response = client.get("/api/v1/bulk/operations?limit=10000")
        assert response.status_code == 422  # Too large


@pytest.mark.api
class TestBulkOperationStatus:
    """Test individual bulk operation status retrieval."""

    def test_get_bulk_operation_status_valid_id(self, client):
        """Test getting status of a valid operation."""
        # First create a bulk operation
        documents = [{"content": "Status test document.", "metadata": {}}]
        response = client.post("/api/v1/bulk/documents", json={"documents": documents})
        assert response.status_code == 200

        operation_id = response.json()["data"]["operation_id"]

        # Now get its status
        response = client.get(f"/api/v1/bulk/operations/{operation_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        operation = data["data"]
        assert operation["operation_id"] == operation_id
        assert "status" in operation
        assert "operation_type" in operation

    def test_get_bulk_operation_status_invalid_id(self, client):
        """Test getting status with invalid operation ID."""
        invalid_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/bulk/operations/{invalid_id}")
        # Should handle gracefully
        assert response.status_code in [200, 404, 422]

    def test_get_bulk_operation_status_malformed_id(self, client):
        """Test getting status with malformed operation ID."""
        malformed_ids = ["", "invalid", "../escape", "<script>"]

        for invalid_id in malformed_ids:
            response = client.get(f"/api/v1/bulk/operations/{invalid_id}")
            assert response.status_code in [200, 404, 422, 400]


@pytest.mark.api
class TestBulkOperationCancellation:
    """Test bulk operation cancellation."""

    def test_cancel_bulk_operation_valid(self, client):
        """Test cancelling a valid bulk operation."""
        # Create a bulk operation
        documents = [{"content": "Cancel test document.", "metadata": {}}]
        response = client.post("/api/v1/bulk/documents", json={"documents": documents})
        assert response.status_code == 200

        operation_id = response.json()["data"]["operation_id"]

        # Cancel the operation
        response = client.delete(f"/api/v1/bulk/operations/{operation_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_cancel_bulk_operation_invalid_id(self, client):
        """Test cancelling with invalid operation ID."""
        invalid_id = str(uuid.uuid4())
        response = client.delete(f"/api/v1/bulk/operations/{invalid_id}")
        # Should handle gracefully
        assert response.status_code in [200, 404, 422]


@pytest.mark.api
class TestBulkOperationsIntegration:
    """Test bulk operations integration with other features."""

    def test_bulk_operations_with_analytics(self, client):
        """Test that bulk operations appear in analytics."""
        # Create some bulk operations
        documents = [
            {"content": f"Analytics integration document {i}.", "metadata": {"batch": "analytics_test"}}
            for i in range(3)
        ]

        response = client.post("/api/v1/bulk/documents", json={"documents": documents})
        assert response.status_code == 200

        # Check analytics (may or may not reflect bulk operations)
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_bulk_operations_concurrent_creation(self, client):
        """Test creating multiple bulk operations concurrently."""
        import threading

        results = []
        errors = []

        def create_bulk_operation(index):
            try:
                documents = [{"content": f"Concurrent bulk doc {index}.", "metadata": {"batch": "concurrent"}}]
                response = client.post("/api/v1/bulk/documents", json={"documents": documents})
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Create multiple concurrent bulk operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_bulk_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All should succeed
        assert all(code == 200 for code in results)
        assert len(errors) == 0

        # Check that operations were created
        response = client.get("/api/v1/bulk/operations")
        assert response.status_code == 200

        data = response.json()
        result = data["data"]
        # Should have at least our test operations
        assert len(result["operations"]) >= 5


@pytest.mark.api
class TestBulkOperationsPerformance:
    """Test bulk operations performance characteristics."""

    def test_bulk_operations_response_time(self, client):
        """Test that bulk operations respond within reasonable time."""
        import time

        documents = [{"content": "Performance test document.", "metadata": {}}]

        start_time = time.time()
        response = client.post("/api/v1/bulk/documents", json={"documents": documents})
        end_time = time.time()

        assert response.status_code == 200
        duration = end_time - start_time

        # Should complete within 2 seconds
        assert duration < 2.0

    def test_bulk_operations_listing_performance(self, client):
        """Test bulk operations listing performance."""
        import time

        start_time = time.time()
        response = client.get("/api/v1/bulk/operations")
        end_time = time.time()

        assert response.status_code == 200
        duration = end_time - start_time

        # Should complete within 1 second
        assert duration < 1.0
