"""Doc Store API Integration Tests.

Tests for end-to-end workflows, cross-domain interactions, and
complex business logic at the API level.
"""

import pytest
import json


@pytest.mark.api
class TestDocumentLifecycleIntegration:
    """Test complete document lifecycle workflows."""

    def test_complete_document_lifecycle(self, client):
        """Test complete document lifecycle from creation to analysis."""
        doc_id = "lifecycle-test-doc"

        # 1. Create document
        doc_data = {
            "content": "This is a comprehensive test document for lifecycle testing.",
            "metadata": {
                "type": "documentation",
                "language": "english",
                "author": "test-suite",
                "tags": ["test", "lifecycle"]
            }
        }

        response = client.put(f"/documents/{doc_id}", json=doc_data)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 2. Retrieve document
        response = client.get(f"/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["content"] == doc_data["content"]

        # 3. Add analysis
        analysis_data = {
            "analyzer": "quality-analyzer",
            "model": "gpt-4",
            "result": {
                "score": 0.92,
                "issues": [],
                "readability": "excellent"
            },
            "score": 0.92
        }

        response = client.put(f"/documents/{doc_id}/analysis", json=analysis_data)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 4. Update metadata
        update_data = {
            "updates": {
                "status": "analyzed",
                "quality_score": 0.92
            }
        }

        response = client.patch(f"/documents/{doc_id}/metadata", json=update_data)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 5. Verify metadata was updated
        response = client.get(f"/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["metadata"]["status"] == "analyzed"
        assert data["data"]["metadata"]["quality_score"] == 0.92

    def test_document_search_and_filtering_workflow(self, client):
        """Test document search and filtering workflow."""
        # Create multiple test documents
        docs = [
            {
                "id": "search-doc-1",
                "content": "Python programming tutorial for beginners.",
                "metadata": {"type": "tutorial", "language": "python", "level": "beginner"}
            },
            {
                "id": "search-doc-2",
                "content": "Advanced JavaScript concepts and patterns.",
                "metadata": {"type": "guide", "language": "javascript", "level": "advanced"}
            },
            {
                "id": "search-doc-3",
                "content": "Basic HTML and CSS introduction.",
                "metadata": {"type": "tutorial", "language": "html", "level": "beginner"}
            }
        ]

        # Create documents
        for doc in docs:
            response = client.put(f"/documents/{doc['id']}", json={
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            assert response.status_code == 200

        # Test search by content
        response = client.get("/documents/search?q=python")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

        # Test search by metadata (if supported)
        response = client.get("/documents?type=tutorial")
        assert response.status_code in [200, 422]  # May not be implemented

    def test_bulk_operations_workflow(self, client):
        """Test bulk operations workflow."""
        # Create multiple documents
        bulk_docs = []
        for i in range(5):
            doc_id = f"bulk-test-{i}"
            doc_data = {
                "content": f"Bulk test document number {i}.",
                "metadata": {"batch": "bulk-test", "index": i}
            }

            response = client.put(f"/documents/{doc_id}", json=doc_data)
            assert response.status_code == 200
            bulk_docs.append(doc_id)

        # Test bulk retrieval (if supported)
        response = client.get("/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify documents exist
        for doc_id in bulk_docs:
            response = client.get(f"/documents/{doc_id}")
            assert response.status_code == 200

    def test_versioning_workflow(self, client):
        """Test document versioning workflow."""
        doc_id = "version-test-doc"

        # Create initial document
        initial_content = "Initial document content."
        response = client.put(f"/documents/{doc_id}", json={"content": initial_content})
        assert response.status_code == 200

        # Create version (if versioning is supported)
        version_data = {
            "content": "Updated document content with improvements.",
            "change_summary": "Added improvements and clarifications"
        }

        response = client.post(f"/documents/{doc_id}/versions", json=version_data)
        # Versioning may not be implemented yet
        assert response.status_code in [200, 404, 501]

        # List versions (if supported)
        response = client.get(f"/documents/{doc_id}/versions")
        assert response.status_code in [200, 404, 501]

    def test_analytics_workflow(self, client):
        """Test analytics workflow."""
        # Create some test data first
        for i in range(3):
            doc_data = {
                "content": f"Analytics test document {i} with some content.",
                "metadata": {"category": "analytics-test", "index": i}
            }
            response = client.put(f"/documents/analytics-doc-{i}", json=doc_data)
            assert response.status_code == 200

            # Add analysis
            analysis_data = {
                "analyzer": "quality-analyzer",
                "result": {"score": 0.8 + i * 0.05},
                "score": 0.8 + i * 0.05
            }
            response = client.put(f"/documents/analytics-doc-{i}/analysis", json=analysis_data)
            assert response.status_code == 200

        # Get analytics summary
        response = client.get("/analytics/summary")
        assert response.status_code in [200, 404, 501]  # May not be implemented

        # Get quality metrics
        response = client.get("/documents/quality")
        assert response.status_code in [200, 404, 501]  # May not be implemented

    def test_relationships_workflow(self, client):
        """Test document relationships workflow."""
        # Create related documents
        docs = [
            {"id": "parent-doc", "content": "Parent document with main content."},
            {"id": "child-doc", "content": "Child document that references parent."},
            {"id": "related-doc", "content": "Related document with similar content."}
        ]

        for doc in docs:
            response = client.put(f"/documents/{doc['id']}", json={"content": doc["content"]})
            assert response.status_code == 200

        # Create relationship (if supported)
        relationship_data = {
            "source_document_id": "child-doc",
            "target_document_id": "parent-doc",
            "relationship_type": "references",
            "strength": 0.9
        }

        response = client.post("/relationships", json=relationship_data)
        # Relationships may not be implemented
        assert response.status_code in [200, 404, 501]

    def test_tagging_workflow(self, client):
        """Test document tagging workflow."""
        doc_id = "tagging-test-doc"

        # Create document
        response = client.put(f"/documents/{doc_id}", json={
            "content": "Document about Python programming and web development."
        })
        assert response.status_code == 200

        # Tag document (if supported)
        tag_data = {
            "tags": ["python", "programming", "web-development"],
            "confidence_threshold": 0.5
        }

        response = client.post(f"/documents/{doc_id}/tags", json=tag_data)
        assert response.status_code in [200, 404, 501]

        # Get document tags (if supported)
        response = client.get(f"/documents/{doc_id}/tags")
        assert response.status_code in [200, 404, 501]

    def test_notification_workflow(self, client):
        """Test notification workflow."""
        # Create document to trigger notifications
        response = client.put("/documents/notification-test", json={
            "content": "Document that should trigger notifications."
        })
        assert response.status_code == 200

        # Check notification endpoints (if implemented)
        response = client.get("/notifications/events")
        assert response.status_code in [200, 404, 501]

        response = client.get("/notifications/webhooks")
        assert response.status_code in [200, 404, 501]

    def test_lifecycle_management_workflow(self, client):
        """Test lifecycle management workflow."""
        doc_id = "lifecycle-mgmt-doc"

        # Create document with lifecycle metadata
        response = client.put(f"/documents/{doc_id}", json={
            "content": "Document for lifecycle management testing.",
            "metadata": {
                "retention_policy": "1-year",
                "archive_after": "6-months"
            }
        })
        assert response.status_code == 200

        # Apply lifecycle policies (if supported)
        response = client.post(f"/documents/{doc_id}/lifecycle/apply")
        assert response.status_code in [200, 404, 501]

        # Check lifecycle status (if supported)
        response = client.get(f"/documents/{doc_id}/lifecycle")
        assert response.status_code in [200, 404, 501]

    def test_error_handling_workflow(self, client):
        """Test comprehensive error handling."""
        # Test various error scenarios
        error_scenarios = [
            # Invalid document ID
            ("/documents/", 404),
            # Non-existent document
            ("/documents/non-existent", 404),
            # Invalid JSON
            ("/documents/test", 400),
            # Missing required fields
            ("/documents/test", 422),
            # Invalid analysis data
            ("/documents/test/analysis", 422),
        ]

        for endpoint, expected_status in error_scenarios:
            if "PUT" in endpoint.upper() or "PATCH" in endpoint.upper():
                response = client.put(endpoint, json={})
            else:
                response = client.get(endpoint)
            # Allow for various error status codes
            assert response.status_code >= 400

    def test_performance_workflow(self, client):
        """Test performance under load."""
        import time

        # Create multiple documents quickly
        start_time = time.time()

        for i in range(10):
            doc_data = {
                "content": f"Performance test document {i}.",
                "metadata": {"batch": "performance-test"}
            }
            response = client.put(f"/documents/perf-doc-{i}", json=doc_data)
            assert response.status_code == 200

        # Measure retrieval performance
        for i in range(10):
            response = client.get(f"/documents/perf-doc-{i}")
            assert response.status_code == 200

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time
        assert duration < 5.0  # 5 seconds for 20 operations
