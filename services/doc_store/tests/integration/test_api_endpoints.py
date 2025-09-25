"""Integration tests for doc_store API endpoints."""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from services.doc_store.main import app
from services.doc_store.core.entities import Document


class TestDocumentAPI:
    """Integration tests for document API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client for the FastAPI app."""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            yield client

    def test_health_endpoint(self, client):
        """Test health endpoint returns success."""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "database_status" in data["data"]
        assert "features" in data["data"]

    def test_create_document_success(self, client):
        """Test successful document creation via API."""
        # Arrange
        document_data = {
            "content": "Test document content for API testing",
            "title": "API Test Document",
            "metadata": {
                "author": "test_user",
                "tags": ["api", "test"],
                "source": "integration_test"
            }
        }

        # Act
        response = client.post("/documents", json=document_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        document = data["data"]
        assert "id" in document
        assert document["content"] == document_data["content"]
        assert document["metadata"]["author"] == "test_user"

    def test_create_document_validation_error(self, client):
        """Test document creation with validation error."""
        # Arrange
        invalid_data = {
            "content": "",  # Empty content should fail
            "metadata": {"invalid": "data"}
        }

        # Act
        response = client.post("/documents", json=invalid_data)

        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert data["success"] is False
        assert "errors" in data

    def test_get_document_by_id_success(self, client):
        """Test getting document by ID via API."""
        # Arrange - Create document first
        create_data = {
            "content": "Document for retrieval test",
            "metadata": {"test": "get_by_id"}
        }
        create_response = client.post("/documents", json=create_data)
        assert create_response.status_code == 201
        doc_id = create_response.json()["data"]["id"]

        # Act
        response = client.get(f"/documents/{doc_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == doc_id
        assert data["data"]["content"] == create_data["content"]

    def test_get_document_by_id_not_found(self, client):
        """Test getting non-existent document by ID."""
        # Act
        response = client.get("/documents/nonexistent-id")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()

    def test_list_documents(self, client):
        """Test listing documents via API."""
        # Arrange - Create a few test documents
        for i in range(3):
            doc_data = {
                "content": f"List test document {i}",
                "metadata": {"index": i, "test": "list"}
            }
            response = client.post("/documents", json=doc_data)
            assert response.status_code == 201

        # Act
        response = client.get("/documents")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data["data"]
        assert len(data["data"]["items"]) >= 3

    def test_list_documents_with_pagination(self, client):
        """Test listing documents with pagination."""
        # Act
        response = client.get("/documents?limit=2&offset=1")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) <= 2
        assert data["data"]["pagination"]["page"] == 2
        assert data["data"]["pagination"]["page_size"] == 2

    def test_update_document_success(self, client):
        """Test successful document update via API."""
        # Arrange - Create document first
        create_data = {
            "content": "Original content for update test",
            "metadata": {"test": "update"}
        }
        create_response = client.post("/documents", json=create_data)
        assert create_response.status_code == 201
        doc_id = create_response.json()["data"]["id"]

        # Act
        update_data = {
            "content": "Updated content via API",
            "metadata": {"test": "update", "updated": True}
        }
        response = client.put(f"/documents/{doc_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify update
        get_response = client.get(f"/documents/{doc_id}")
        assert get_response.status_code == 200
        updated_doc = get_response.json()["data"]
        assert updated_doc["content"] == update_data["content"]
        assert updated_doc["metadata"]["updated"] is True

    def test_update_document_not_found(self, client):
        """Test updating non-existent document."""
        # Act
        update_data = {"content": "This should not work"}
        response = client.put("/documents/nonexistent-id", json=update_data)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_delete_document_success(self, client):
        """Test successful document deletion via API."""
        # Arrange - Create document first
        create_data = {
            "content": "Document for deletion test",
            "metadata": {"test": "delete"}
        }
        create_response = client.post("/documents", json=create_data)
        assert create_response.status_code == 201
        doc_id = create_response.json()["data"]["id"]

        # Act
        response = client.delete(f"/documents/{doc_id}")

        # Assert
        assert response.status_code == 204  # No content for successful deletion

        # Verify deletion
        get_response = client.get(f"/documents/{doc_id}")
        assert get_response.status_code == 404

    def test_delete_document_not_found(self, client):
        """Test deleting non-existent document."""
        # Act
        response = client.delete("/documents/nonexistent-id")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_search_documents(self, client):
        """Test document search via API."""
        # Arrange - Create documents with searchable content
        search_docs = [
            {"content": "Python programming tutorial", "metadata": {"topic": "python"}},
            {"content": "Java programming guide", "metadata": {"topic": "java"}},
            {"content": "Python data structures explained", "metadata": {"topic": "python"}}
        ]

        for doc_data in search_docs:
            response = client.post("/documents", json=doc_data)
            assert response.status_code == 201

        # Act
        response = client.get("/documents/search?q=Python")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) >= 2  # Should find both Python documents

    def test_document_statistics(self, client):
        """Test document statistics endpoint."""
        # Act
        response = client.get("/documents/statistics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_documents" in data["data"]
        assert "last_updated" in data["data"]

    def test_bulk_operations(self, client):
        """Test bulk document operations."""
        # Arrange
        bulk_data = {
            "documents": [
                {
                    "content": "Bulk document 1",
                    "metadata": {"batch": "test1", "index": 1}
                },
                {
                    "content": "Bulk document 2",
                    "metadata": {"batch": "test1", "index": 2}
                }
            ]
        }

        # Act
        response = client.post("/documents/bulk", json=bulk_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["documents"]) == 2
        assert all("id" in doc for doc in data["data"]["documents"])

    def test_error_response_format(self, client):
        """Test that all error responses follow consistent format."""
        # Act - Trigger validation error
        response = client.post("/documents", json={"content": ""})

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "message" in data
        assert "errors" in data
        assert "request_id" in data
        assert "timestamp" in data

    def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        # Act
        response = client.options("/documents", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        })

        # Assert
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client):
        """Test handling of concurrent requests."""
        # This test would require more complex setup for true concurrency testing
        # For now, just test basic concurrent-like behavior

        # Act - Make multiple requests
        tasks = []
        for i in range(5):
            doc_data = {
                "content": f"Concurrent test document {i}",
                "metadata": {"test": "concurrent", "index": i}
            }
            tasks.append(async_client.post("/documents", json=doc_data))

        responses = await asyncio.gather(*tasks)

        # Assert - All requests should succeed
        assert all(resp.status_code == 201 for resp in responses)
        assert all(resp.json()["success"] is True for resp in responses)

    def test_api_response_consistency(self, client):
        """Test that all API responses follow consistent format."""
        endpoints_to_test = [
            ("/health", "get", None),
            ("/documents/statistics", "get", None),
        ]

        for endpoint, method, data in endpoints_to_test:
            # Act
            if method == "get":
                response = client.get(endpoint)
            elif method == "post":
                response = client.post(endpoint, json=data)

            # Assert
            assert response.status_code in [200, 201]
            data = response.json()

            # Check consistent response structure
            assert "success" in data
            assert "data" in data
            assert "message" in data
            assert "request_id" in data
            assert "timestamp" in data

            # Success responses should have success=True
            if response.status_code in [200, 201]:
                assert data["success"] is True
                assert data["message"] is not None
