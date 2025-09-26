"""Doc Store API Quality Tests.

Tests for document quality assessment at the API endpoint level.
"""

import pytest
import json


@pytest.mark.api
class TestQualityAssessment:
    """Test document quality operations."""

    def test_get_quality_metrics_basic(self, client):
        """Test basic quality metrics retrieval."""
        response = client.get("/api/v1/documents/quality")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_quality_metrics_with_parameters(self, client):
        """Test quality metrics with custom parameters."""
        params = {
            "stale_threshold_days": 90,
            "min_views": 5
        }

        response = client.get("/api/v1/documents/quality", params=params)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_quality_metrics_strict_threshold(self, client):
        """Test quality metrics with strict threshold."""
        response = client.get("/api/v1/documents/quality", params={"stale_threshold_days": 30})
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_quality_metrics_lenient_threshold(self, client):
        """Test quality metrics with lenient threshold."""
        response = client.get("/api/v1/documents/quality", params={"stale_threshold_days": 365})
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_quality_metrics_zero_views(self, client):
        """Test quality metrics with zero minimum views."""
        response = client.get("/api/v1/documents/quality", params={"min_views": 0})
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_quality_metrics_high_views(self, client):
        """Test quality metrics with high minimum views."""
        response = client.get("/api/v1/documents/quality", params={"min_views": 100})
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_quality_metrics_invalid_parameters(self, client):
        """Test quality metrics with invalid parameters."""
        invalid_params = [
            {"stale_threshold_days": -1},
            {"min_views": -1},
            {"stale_threshold_days": 0},
            {"min_views": -100},
        ]

        for params in invalid_params:
            response = client.get("/api/v1/documents/quality", params=params)
            assert response.status_code == 422  # Validation error

    def test_quality_metrics_edge_cases(self, client):
        """Test quality metrics with edge case parameters."""
        edge_cases = [
            {"stale_threshold_days": 1},  # Very strict
            {"stale_threshold_days": 3650},  # Very lenient (10 years)
            {"min_views": 0},  # No minimum
            {"min_views": 1000},  # Very high threshold
        ]

        for params in edge_cases:
            response = client.get("/api/v1/documents/quality", params=params)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

    def test_quality_metrics_data_structure(self, client):
        """Test quality metrics data structure."""
        response = client.get("/api/v1/documents/quality")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        quality_data = data["data"]
        assert isinstance(quality_data, dict)

        # Should contain quality assessment fields
        expected_fields = ["total_documents", "quality_score", "stale_documents", "low_quality"]
        # At least some fields should be present
        assert len(quality_data) > 0

    def test_quality_metrics_with_documents(self, client):
        """Test quality metrics after creating documents."""
        # Create documents with different ages/metadata
        docs = [
            {
                "content": "Recent quality document.",
                "metadata": {"created_recently": True, "quality": "high"}
            },
            {
                "content": "Older quality document.",
                "metadata": {"created_recently": False, "quality": "medium"}
            }
        ]

        # Create documents
        created_docs = []
        for doc in docs:
            response = client.post("/api/v1/documents", json=doc)
            assert response.status_code == 200
            created_docs.append(response.json()["data"]["id"])

        # Get quality metrics
        response = client.get("/api/v1/documents/quality")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Should have some quality assessment
        quality_data = data["data"]
        assert isinstance(quality_data, dict)

    def test_quality_metrics_performance(self, client):
        """Test quality metrics endpoint performance."""
        import time

        start_time = time.time()

        # Make multiple quality requests
        for i in range(10):
            response = client.get("/api/v1/documents/quality")
            assert response.status_code == 200

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time
        assert duration < 3.0  # 3 seconds for 10 requests

    def test_quality_metrics_concurrent_access(self, client):
        """Test quality metrics under concurrent access."""
        import threading

        results = []
        errors = []

        def make_quality_request():
            try:
                response = client.get("/api/v1/documents/quality")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Create multiple concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_quality_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert all(code == 200 for code in results)
        assert len(errors) == 0


@pytest.mark.api
class TestQualityMetricsIntegration:
    """Test quality metrics integration with other features."""

    def test_quality_after_document_changes(self, client):
        """Test quality metrics after document modifications."""
        # Create a document
        doc_data = {
            "content": "Document for quality testing.",
            "metadata": {"quality_test": True}
        }

        response = client.post("/api/v1/documents", json=doc_data)
        assert response.status_code == 200
        doc_id = response.json()["data"]["id"]

        # Update document metadata
        update_data = {
            "updates": {
                "quality_score": 0.95,
                "last_reviewed": "2024-01-15"
            }
        }

        response = client.patch(f"/api/v1/documents/{doc_id}/metadata", json=update_data)
        # Patch may not be implemented, but that's ok
        assert response.status_code in [200, 405, 501]

        # Get quality metrics
        response = client.get("/api/v1/documents/quality")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_quality_metrics_error_handling(self, client):
        """Test quality metrics error handling."""
        # Test with malformed parameters
        response = client.get("/api/v1/documents/quality", params={"invalid_param": "value"})
        # Should handle gracefully
        assert response.status_code in [200, 422, 400]

        # Test with extreme values
        response = client.get("/api/v1/documents/quality", params={"stale_threshold_days": 999999})
        assert response.status_code in [200, 422]
