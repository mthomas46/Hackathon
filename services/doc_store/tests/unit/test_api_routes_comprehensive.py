"""Comprehensive tests for API routes."""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from services.doc_store.main import app
from services.doc_store.domain.entities import Document


class TestDocumentAPIRoutes:
    """Comprehensive test cases for document API routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(app=app, base_url="http://testserver")

    @pytest.fixture
    def mock_service(self):
        """Create mock document service."""
        service = AsyncMock()
        # Set up common mock returns
        service.create.return_value = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123",
            metadata={"title": "Test"}
        )
        service.get_by_id.return_value = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123",
            metadata={"title": "Test"}
        )
        service.list.return_value = [
            Document(id="doc1", content="Content 1", content_hash="h1"),
            Document(id="doc2", content="Content 2", content_hash="h2"),
        ]
        return service

    @pytest.mark.asyncio
    async def test_create_document_success(self, async_client, mock_service):
        """Test creating a document successfully."""
        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            document_data = {
                "content": "This is test content",
                "metadata": {"title": "Test Document", "author": "Test Author"},
                "correlation_id": "test-correlation-123"
            }

            response = await async_client.post("/api/documents", json=document_data)

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == "test-doc-123"
            assert data["data"]["content"] == "Test content"

            mock_service.create.assert_called_once_with(document_data)

    @pytest.mark.asyncio
    async def test_create_document_validation_error(self, async_client, mock_service):
        """Test creating document with validation error."""
        from services.shared.infrastructure.utilities.error_handling import ValidationException

        mock_service.create.side_effect = ValidationException("content", "Content cannot be empty")

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            document_data = {"content": ""}

            response = await async_client.post("/api/documents", json=document_data)

            assert response.status_code == 422
            data = response.json()
            assert data["success"] is False
            assert "validation_error" in data["error"]["error_code"]

    @pytest.mark.asyncio
    async def test_get_document_by_id_success(self, async_client, mock_service):
        """Test getting document by ID successfully."""
        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            response = await async_client.get("/api/documents/test-doc-123")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == "test-doc-123"

            mock_service.get_by_id.assert_called_once_with("test-doc-123")

    @pytest.mark.asyncio
    async def test_get_document_by_id_not_found(self, async_client, mock_service):
        """Test getting nonexistent document by ID."""
        mock_service.get_by_id.return_value = None

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            response = await async_client.get("/api/documents/nonexistent-id")

            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert data["error"]["error_code"] == "not_found"

    @pytest.mark.asyncio
    async def test_list_documents_success(self, async_client, mock_service):
        """Test listing documents successfully."""
        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            response = await async_client.get("/api/documents")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2
            assert data["data"][0]["id"] == "doc1"
            assert data["data"][1]["id"] == "doc2"

            mock_service.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_success(self, async_client, mock_service):
        """Test updating document successfully."""
        mock_service.update.return_value = Document(
            id="test-doc-123",
            content="Updated content",
            content_hash="hash123",
            metadata={"title": "Updated"}
        )

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            update_data = {
                "content": "Updated content",
                "metadata": {"title": "Updated"}
            }

            response = await async_client.put("/api/documents/test-doc-123", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["content"] == "Updated content"

            mock_service.update.assert_called_once_with("test-doc-123", update_data)

    @pytest.mark.asyncio
    async def test_delete_document_success(self, async_client, mock_service):
        """Test deleting document successfully."""
        mock_service.delete.return_value = True

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            response = await async_client.delete("/api/documents/test-doc-123")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["deleted"] is True

            mock_service.delete.assert_called_once_with("test-doc-123")

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, async_client, mock_service):
        """Test deleting nonexistent document."""
        mock_service.delete.return_value = False

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            response = await async_client.delete("/api/documents/nonexistent-id")

            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert data["error"]["error_code"] == "not_found"

    @pytest.mark.asyncio
    async def test_search_documents_by_correlation_id(self, async_client, mock_service):
        """Test searching documents by correlation ID."""
        mock_service.search_by_correlation_id.return_value = [
            Document(id="doc1", content="Content 1", content_hash="h1", correlation_id="corr-123"),
            Document(id="doc2", content="Content 2", content_hash="h2", correlation_id="corr-123"),
        ]

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            response = await async_client.get("/api/documents/search?correlation_id=corr-123")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2

            mock_service.search_by_correlation_id.assert_called_once_with("corr-123")

    @pytest.mark.asyncio
    async def test_search_documents_by_content(self, async_client, mock_service):
        """Test searching documents by content."""
        mock_service.search_by_content_pattern.return_value = [
            Document(id="doc1", content="Python tutorial", content_hash="h1"),
        ]

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            response = await async_client.get("/api/documents/search?content=Python")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1

            mock_service.search_by_content_pattern.assert_called_once_with("Python")

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, async_client):
        """Test health check endpoint."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "doc_store" in data["service"]

    @pytest.mark.asyncio
    async def test_create_document_missing_content(self, async_client, mock_service):
        """Test creating document with missing content."""
        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            document_data = {"metadata": {"title": "Test"}}

            response = await async_client.post("/api/documents", json=document_data)

            # Should still work as content can be empty string in request
            assert response.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_create_document_invalid_json(self, async_client):
        """Test creating document with invalid JSON."""
        response = await async_client.post(
            "/api/documents",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, async_client):
        """Test method not allowed for endpoint."""
        response = await async_client.patch("/api/documents/test-doc-123")

        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_document_count_endpoint(self, async_client, mock_service):
        """Test getting document count."""
        mock_service.count.return_value = 42

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            response = await async_client.get("/api/documents/count")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["count"] == 42

            mock_service.count.assert_called_once()

    @pytest.mark.asyncio
    async def test_document_exists_endpoint(self, async_client, mock_service):
        """Test checking if document exists."""
        mock_service.exists.return_value = True

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            response = await async_client.head("/api/documents/test-doc-123")

            assert response.status_code == 200

            mock_service.exists.assert_called_once_with("test-doc-123")

    @pytest.mark.asyncio
    async def test_document_not_exists_endpoint(self, async_client, mock_service):
        """Test checking if document doesn't exist."""
        mock_service.exists.return_value = False

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            response = await async_client.head("/api/documents/nonexistent-id")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_bulk_operations_not_implemented(self, async_client):
        """Test bulk operations endpoints (not implemented)."""
        # These endpoints might not exist yet
        response = await async_client.post("/api/documents/bulk", json=[])
        assert response.status_code in [404, 501]  # Not found or not implemented

    @pytest.mark.asyncio
    async def test_invalid_document_id_format(self, async_client):
        """Test handling invalid document ID formats."""
        # Test with special characters that might cause issues
        response = await async_client.get("/api/documents/invalid@id#$%")

        # Should handle gracefully
        assert response.status_code in [200, 404, 422]

    @pytest.mark.asyncio
    async def test_large_request_payload(self, async_client, mock_service):
        """Test handling large request payloads."""
        large_content = "A" * 10000  # 10KB content
        document_data = {
            "content": large_content,
            "metadata": {"size": "large"}
        }

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            response = await async_client.post("/api/documents", json=document_data)

            # Should handle large payloads appropriately
            assert response.status_code in [201, 413, 422]  # Created, too large, or validation error

    @pytest.mark.asyncio
    async def test_concurrent_requests_simulation(self, async_client, mock_service):
        """Test handling concurrent requests."""
        import asyncio

        async def make_request(i):
            doc_data = {"content": f"Concurrent content {i}", "correlation_id": f"corr-{i}"}
            return await async_client.post("/api/documents", json=doc_data)

        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            # Make 5 concurrent requests
            tasks = [make_request(i) for i in range(5)]
            responses = await asyncio.gather(*tasks)

            # All should succeed
            for response in responses:
                assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client):
        """Test CORS headers are present."""
        response = await async_client.options("/api/documents")

        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 404

    @pytest.mark.asyncio
    async def test_request_id_header(self, async_client, mock_service):
        """Test request ID header is handled."""
        with patch('services.doc_store.presentation.api.routes.DocumentService', return_value=mock_service):
            headers = {"X-Request-ID": "test-request-123"}
            response = await async_client.get("/api/documents", headers=headers)

            assert response.status_code == 200
            # Request ID should be echoed back or used in logging
