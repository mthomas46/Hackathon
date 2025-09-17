"""Doc Store API Core Tests.

Tests for basic CRUD operations, health endpoints, and core functionality
at the API endpoint level.
"""

import pytest
import json


@pytest.mark.api
class TestHealthEndpoints:
    """Test health and service information endpoints."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_info_endpoint(self, client):
        """Test service info endpoint."""
        response = client.get("/info")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data

        service_data = data["data"]
        assert "service" in service_data
        assert service_data["service"] == "doc_store"

    def test_config_effective_endpoint(self, client):
        """Test effective configuration endpoint."""
        response = client.get("/config/effective")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True


@pytest.mark.api
class TestDocumentOperations:
    """Test basic document CRUD operations."""

    def test_put_document_basic(self, client):
        """Test basic document creation."""
        doc_data = {
            "content": "This is a test document for API testing.",
            "metadata": {
                "type": "documentation",
                "language": "english",
                "author": "test-author"
            }
        }

        response = client.post("/api/v1/documents", json=doc_data)
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

    def test_put_document_with_custom_id(self, client):
        """Test document creation with custom ID."""
        doc_data = {
            "content": "Document with custom ID.",
            "metadata": {"type": "test"}
        }

        response = client.put("/documents/custom-doc-id", json=doc_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_put_document_minimal(self, client):
        """Test document creation with minimal data."""
        doc_data = {"content": "Minimal document content."}

        response = client.put("/documents/minimal-doc", json=doc_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_get_document_existing(self, client):
        """Test retrieving an existing document."""
        # First create a document
        doc_data = {"content": "Document to retrieve."}
        client.put("/documents/retrieve-test", json=doc_data)

        # Then retrieve it
        response = client.get("/documents/retrieve-test")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["content"] == "Document to retrieve."

    def test_get_document_not_found(self, client):
        """Test retrieving a non-existent document."""
        response = client.get("/documents/non-existent-doc")
        assert response.status_code == 404

        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_put_analysis_basic(self, client):
        """Test basic analysis creation."""
        analysis_data = {
            "analyzer": "quality-analyzer",
            "model": "gpt-4",
            "result": {"score": 0.85, "issues": ["minor formatting"]},
            "score": 0.85
        }

        response = client.put("/documents/test-doc-123/analysis", json=analysis_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_list_documents_basic(self, client):
        """Test basic document listing."""
        response = client.get("/documents")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_documents_with_pagination(self, client):
        """Test document listing with pagination."""
        response = client.get("/documents?limit=10&offset=0")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_search_documents_basic(self, client):
        """Test basic document search."""
        response = client.get("/documents/search?q=test")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_patch_metadata_basic(self, client):
        """Test basic metadata update."""
        # First create a document
        doc_data = {"content": "Document for metadata update."}
        client.put("/documents/metadata-test", json=doc_data)

        # Update metadata
        update_data = {
            "updates": {
                "tags": ["updated"],
                "status": "reviewed"
            }
        }

        response = client.patch("/documents/metadata-test/metadata", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_list_analyses_basic(self, client):
        """Test basic analyses listing."""
        response = client.get("/documents/test-doc-123/analyses")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_get_quality_metrics(self, client):
        """Test quality metrics retrieval."""
        response = client.get("/documents/quality")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_list_style_examples(self, client):
        """Test style examples listing."""
        response = client.get("/documents/style-examples")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data


@pytest.mark.api
class TestAnalyticsOperations:
    """Test analytics-related operations."""

    def test_get_analytics_summary(self, client):
        """Test analytics summary retrieval."""
        response = client.get("/analytics/summary")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_get_analytics_detailed(self, client):
        """Test detailed analytics retrieval."""
        response = client.get("/analytics/detailed")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True


@pytest.mark.api
class TestTaggingOperations:
    """Test tagging-related operations."""

    def test_tag_document(self, client):
        """Test document tagging."""
        tag_data = {
            "tags": ["python", "api"],
            "confidence_threshold": 0.5
        }

        response = client.post("/documents/test-doc-123/tags", json=tag_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_get_document_tags(self, client):
        """Test retrieving document tags."""
        response = client.get("/documents/test-doc-123/tags")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True


@pytest.mark.api
class TestVersioningOperations:
    """Test versioning-related operations."""

    def test_create_version(self, client):
        """Test version creation."""
        version_data = {
            "content": "Updated content for new version.",
            "change_summary": "Updated documentation"
        }

        response = client.post("/documents/test-doc-123/versions", json=version_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_list_versions(self, client):
        """Test version listing."""
        response = client.get("/documents/test-doc-123/versions")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_get_version(self, client):
        """Test specific version retrieval."""
        response = client.get("/documents/test-doc-123/versions/1")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
