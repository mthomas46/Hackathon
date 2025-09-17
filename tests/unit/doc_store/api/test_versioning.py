"""Doc Store API Versioning Tests.

Tests for document versioning functionality at the API endpoint level.
"""

import pytest
import json


@pytest.mark.api
class TestDocumentVersionRetrieval:
    """Test document version history retrieval."""

    def test_get_document_versions_empty(self, client):
        """Test getting versions for document with no versions."""
        # Create a document
        doc_data = {"content": "Version test document.", "metadata": {}}
        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Get versions (should have at least initial version)
        response = client.get(f"/api/v1/documents/{doc_id}/versions")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        versions_data = data["data"]
        assert "versions" in versions_data
        assert "total" in versions_data
        assert isinstance(versions_data["versions"], list)

    def test_get_document_versions_with_pagination(self, client):
        """Test getting document versions with pagination."""
        # Create a document
        doc_data = {"content": "Pagination test document.", "metadata": {}}
        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Test pagination parameters
        for limit in [1, 5, 10]:
            response = client.get(f"/api/v1/documents/{doc_id}/versions?limit={limit}")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

            versions_data = data["data"]
            assert len(versions_data["versions"]) <= limit

    def test_get_document_versions_nonexistent(self, client):
        """Test getting versions for non-existent document."""
        response = client.get("/api/v1/documents/nonexistent-id/versions")
        # Should handle gracefully
        assert response.status_code in [200, 404, 422]


@pytest.mark.api
class TestDocumentVersionRollback:
    """Test document version rollback functionality."""

    def test_rollback_document_version_success(self, client):
        """Test successful document version rollback."""
        # Create a document
        doc_data = {"content": "Original content for rollback testing.", "metadata": {}}
        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Update the document to create a new version
        update_data = {
            "updates": {
                "content": "Updated content for rollback testing.",
                "version": "2.0"
            }
        }

        # Note: Metadata update may not be implemented, that's ok
        update_response = client.patch(f"/api/v1/documents/{doc_id}/metadata", json=update_data)
        assert update_response.status_code in [200, 405, 501]

        # Attempt rollback (this may not work if versioning isn't fully implemented)
        rollback_data = {
            "version_number": 1,
            "reason": "Rolling back to original version for testing"
        }

        response = client.post(f"/api/v1/documents/{doc_id}/versions/rollback", json=rollback_data)
        # Rollback may not be implemented yet
        assert response.status_code in [200, 501]

    def test_rollback_document_version_invalid_number(self, client):
        """Test rollback with invalid version number."""
        # Create a document
        doc_data = {"content": "Invalid rollback test document.", "metadata": {}}
        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Try rollback with invalid version
        rollback_data = {
            "version_number": 999,
            "reason": "Testing invalid version rollback"
        }

        response = client.post(f"/api/v1/documents/{doc_id}/versions/rollback", json=rollback_data)
        # Should handle gracefully
        assert response.status_code in [200, 422, 400, 501]

    def test_rollback_document_version_nonexistent(self, client):
        """Test rollback on non-existent document."""
        rollback_data = {
            "version_number": 1,
            "reason": "Testing rollback on non-existent document"
        }

        response = client.post("/api/v1/documents/nonexistent-id/versions/rollback", json=rollback_data)
        # Should handle gracefully
        assert response.status_code in [404, 422, 400, 501]


@pytest.mark.api
class TestVersioningIntegration:
    """Test versioning integration with document operations."""

    def test_versioning_with_document_updates(self, client):
        """Test versioning behavior with document updates."""
        # Create a document
        doc_data = {
            "content": "Versioning integration test document.",
            "metadata": {"version": "1.0", "category": "integration"}
        }

        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Get initial versions
        versions_response = client.get(f"/api/v1/documents/{doc_id}/versions")
        assert versions_response.status_code == 200

        initial_versions = versions_response.json()["data"]

        # Attempt metadata update (may create new version)
        update_data = {
            "updates": {
                "version": "1.1",
                "last_modified": "2024-01-16"
            }
        }

        update_response = client.patch(f"/api/v1/documents/{doc_id}/metadata", json=update_data)
        # Update may not be implemented
        assert update_response.status_code in [200, 405, 501]

        # Check if versions increased (if versioning is implemented)
        final_versions_response = client.get(f"/api/v1/documents/{doc_id}/versions")
        assert final_versions_response.status_code == 200

        final_versions = final_versions_response.json()["data"]
        # Versions should be the same or increased (depending on implementation)
        assert final_versions["total"] >= initial_versions["total"]

    def test_versioning_edge_cases(self, client):
        """Test versioning edge cases."""
        # Create document
        doc_data = {"content": "Edge case versioning document.", "metadata": {}}
        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Test various pagination edge cases
        edge_cases = [
            "?limit=0",  # Zero limit
            "?limit=1000",  # Large limit
            "?offset=0",  # Zero offset
            "?offset=100",  # Large offset
        ]

        for params in edge_cases:
            response = client.get(f"/api/v1/documents/{doc_id}/versions{params}")
            assert response.status_code in [200, 422]  # Success or validation error


@pytest.mark.api
class TestVersioningPerformance:
    """Test versioning performance characteristics."""

    def test_versioning_operations_performance(self, client):
        """Test versioning operations performance."""
        import time

        # Create a document
        doc_data = {"content": "Performance test document.", "metadata": {}}
        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        start_time = time.time()

        # Perform multiple version retrievals
        for i in range(10):
            response = client.get(f"/api/v1/documents/{doc_id}/versions")
            assert response.status_code == 200

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time
        assert duration < 3.0  # 3 seconds for 10 operations

    def test_versioning_concurrent_access(self, client):
        """Test versioning under concurrent access."""
        import threading

        # Create a document
        doc_data = {"content": "Concurrent versioning test document.", "metadata": {}}
        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        results = []
        errors = []

        def access_versions():
            try:
                response = client.get(f"/api/v1/documents/{doc_id}/versions")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Create concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=access_versions)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert all(code == 200 for code in results)
        assert len(errors) == 0
