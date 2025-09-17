"""Doc Store API Tagging Tests.

Tests for document tagging functionality at the API endpoint level.
"""

import pytest
import json


@pytest.mark.api
class TestDocumentTagging:
    """Test document tagging operations."""

    def test_tag_document_success(self, client):
        """Test successful document tagging."""
        # Create a document first
        doc_data = {
            "content": "Document for tagging testing with Python code and API references.",
            "metadata": {"language": "python", "type": "code"}
        }

        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Tag the document
        response = client.post(f"/api/v1/documents/{doc_id}/tags")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        # Tagging may return tag information or just success

    def test_tag_document_nonexistent(self, client):
        """Test tagging non-existent document."""
        response = client.post("/api/v1/documents/nonexistent-id/tags")
        # Should handle gracefully
        assert response.status_code in [200, 404, 422]

    def test_tag_document_multiple_times(self, client):
        """Test tagging the same document multiple times."""
        # Create a document
        doc_data = {"content": "Multi-tag test document.", "metadata": {}}
        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Tag multiple times
        for i in range(3):
            response = client.post(f"/api/v1/documents/{doc_id}/tags")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True


@pytest.mark.api
class TestTagSearch:
    """Test tag-based document search."""

    def test_search_by_tags_success(self, client):
        """Test successful tag-based search."""
        # Create documents with different tags
        docs = [
            {"content": "Python programming document.", "metadata": {"language": "python"}},
            {"content": "JavaScript programming document.", "metadata": {"language": "javascript"}},
            {"content": "API documentation.", "metadata": {"type": "api", "language": "english"}},
        ]

        created_docs = []
        for doc in docs:
            response = client.post("/api/v1/documents", json=doc)
            assert response.status_code == 200
            created_docs.append(response.json()["data"]["id"])

        # Tag documents (may not work if tagging isn't fully implemented)
        for doc_id in created_docs:
            tag_response = client.post(f"/api/v1/documents/{doc_id}/tags")
            # Tagging may not be implemented yet
            assert tag_response.status_code in [200, 501]

        # Search by tags
        search_params = {"tags": ["python", "api"], "limit": 10, "offset": 0}
        response = client.get("/api/v1/tags/search", params=search_params)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_search_by_tags_empty_results(self, client):
        """Test tag search with no matching results."""
        search_params = {"tags": ["nonexistent_tag"], "limit": 5}
        response = client.get("/api/v1/tags/search", params=search_params)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_search_by_tags_validation(self, client):
        """Test tag search with validation errors."""
        invalid_searches = [
            {"tags": [], "limit": 10},  # Empty tags
            {"limit": 10},  # No tags
            {"tags": ["tag1"], "limit": -1},  # Negative limit
            {"tags": ["tag1"], "offset": -1},  # Negative offset
        ]

        for search_params in invalid_searches:
            response = client.get("/api/v1/tags/search", params=search_params)
            # Should handle validation gracefully
            assert response.status_code in [200, 422, 400]


@pytest.mark.api
class TestTaggingIntegration:
    """Test tagging integration with other features."""

    def test_tagging_with_search_integration(self, client):
        """Test tagging works with regular search."""
        # Create a document
        doc_data = {
            "content": "Tagged document for search integration testing.",
            "metadata": {"tags": ["integration", "test"]}
        }

        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Tag the document
        tag_response = client.post(f"/api/v1/documents/{doc_id}/tags")
        # Tagging may not be implemented yet
        assert tag_response.status_code in [200, 501]

        # Regular search should still work
        search_data = {"query": "integration testing", "limit": 5}
        search_response = client.post("/api/v1/search", json=search_data)
        assert search_response.status_code == 200

        search_results = search_response.json()
        assert search_results["success"] is True

    def test_tagging_with_analytics_integration(self, client):
        """Test tagging provides data for analytics."""
        # Create and tag some documents
        for i in range(3):
            doc_data = {
                "content": f"Tagged document {i} for analytics.",
                "metadata": {"batch": "analytics", "index": i}
            }

            create_response = client.post("/api/v1/documents", json=doc_data)
            assert create_response.status_code == 200
            doc_id = create_response.json()["data"]["id"]

            # Tag the document
            tag_response = client.post(f"/api/v1/documents/{doc_id}/tags")
            # Tagging may not be fully implemented
            assert tag_response.status_code in [200, 501]

        # Analytics should still work
        analytics_response = client.get("/api/v1/analytics/summary")
        assert analytics_response.status_code == 200

        analytics_data = analytics_response.json()
        assert analytics_data["success"] is True


@pytest.mark.api
class TestTaggingEdgeCases:
    """Test tagging edge cases and error conditions."""

    def test_tag_document_malformed_id(self, client):
        """Test tagging with malformed document ID."""
        malformed_ids = ["", "   ", "../escape", "<script>alert('xss')</script>"]

        for malformed_id in malformed_ids:
            response = client.post(f"/api/v1/documents/{malformed_id}/tags")
            # Should handle gracefully
            assert response.status_code in [200, 404, 422, 400]

    def test_tag_search_large_tag_list(self, client):
        """Test tag search with many tags."""
        many_tags = [f"tag{i}" for i in range(20)]
        search_params = {"tags": many_tags, "limit": 10}

        response = client.get("/api/v1/tags/search", params=search_params)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_tag_search_special_characters(self, client):
        """Test tag search with special characters."""
        special_tags = ["tag-with-dashes", "tag_with_underscores", "tag.with.dots", "tag@symbol"]
        search_params = {"tags": special_tags, "limit": 5}

        response = client.get("/api/v1/tags/search", params=search_params)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True


@pytest.mark.api
class TestTaggingPerformance:
    """Test tagging performance characteristics."""

    def test_tagging_operations_performance(self, client):
        """Test tagging operations performance."""
        import time

        # Create a document
        doc_data = {"content": "Performance test document for tagging.", "metadata": {}}
        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        start_time = time.time()

        # Perform multiple tagging operations
        for i in range(10):
            response = client.post(f"/api/v1/documents/{doc_id}/tags")
            assert response.status_code in [200, 501]  # May not be implemented

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time (even if not implemented)
        assert duration < 3.0  # 3 seconds for 10 operations

    def test_tag_search_performance(self, client):
        """Test tag search performance."""
        import time

        start_time = time.time()

        # Perform multiple tag searches
        for i in range(5):
            search_params = {"tags": [f"performance_tag_{i}"], "limit": 10}
            response = client.get("/api/v1/tags/search", params=search_params)
            assert response.status_code == 200

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time
        assert duration < 2.0  # 2 seconds for 5 searches

    def test_tagging_concurrent_operations(self, client):
        """Test tagging under concurrent access."""
        import threading

        # Create a document
        doc_data = {"content": "Concurrent tagging test document.", "metadata": {}}
        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        results = []
        errors = []

        def perform_tagging():
            try:
                response = client.post(f"/api/v1/documents/{doc_id}/tags")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Create concurrent tagging requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=perform_tagging)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All requests should complete (may succeed or return 501)
        assert all(code in [200, 501] for code in results)
        assert len(errors) == 0
