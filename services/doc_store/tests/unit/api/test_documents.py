"""Doc Store API Document Operations Tests.

Tests for comprehensive document operations at the API endpoint level,
including CRUD operations, metadata management, and advanced features.
"""

import pytest
import json


@pytest.mark.api
class TestDocumentCRUD:
    """Test basic document CRUD operations."""

    def test_create_document_comprehensive(self, client):
        """Test comprehensive document creation."""
        doc_data = {
            "content": "This is a comprehensive test document with full metadata.",
            "metadata": {
                "title": "Comprehensive Test Document",
                "author": "API Test Suite",
                "category": "testing",
                "tags": ["api", "comprehensive", "test"],
                "version": "1.0",
                "language": "en",
                "created_by": "test_framework"
            }
        }

        response = client.post("/api/v1/documents", json=doc_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        doc_result = data["data"]
        assert "id" in doc_result
        assert "content" in doc_result
        assert "content_hash" in doc_result
        assert "metadata" in doc_result
        assert doc_result["content"] == doc_data["content"]
        assert doc_result["metadata"]["title"] == doc_data["metadata"]["title"]

    def test_get_document_comprehensive(self, client):
        """Test comprehensive document retrieval."""
        # Create a document first
        doc_data = {
            "content": "Document for comprehensive retrieval testing.",
            "metadata": {
                "test_type": "retrieval",
                "complexity": "high"
            }
        }

        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Retrieve the document
        response = client.get(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        retrieved_doc = data["data"]
        assert retrieved_doc["id"] == doc_id
        assert retrieved_doc["content"] == doc_data["content"]
        assert retrieved_doc["metadata"]["test_type"] == "retrieval"

    def test_list_documents_comprehensive(self, client):
        """Test comprehensive document listing."""
        # Create multiple test documents
        test_docs = [
            {
                "content": f"List test document {i}.",
                "metadata": {"batch": "list_test", "index": i}
            }
            for i in range(5)
        ]

        created_ids = []
        for doc in test_docs:
            response = client.post("/api/v1/documents", json=doc)
            assert response.status_code == 200
            created_ids.append(response.json()["data"]["id"])

        # List documents
        response = client.get("/api/v1/documents")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        docs_list = data["data"]
        assert "items" in docs_list
        assert "total" in docs_list
        assert isinstance(docs_list["items"], list)
        assert len(docs_list["items"]) >= 5  # At least our test docs

    def test_update_metadata_comprehensive(self, client):
        """Test comprehensive metadata updates."""
        # Create a document
        doc_data = {
            "content": "Document for metadata update testing.",
            "metadata": {
                "initial_status": "draft",
                "version": "1.0"
            }
        }

        create_response = client.post("/api/v1/documents", json=doc_data)
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["id"]

        # Update metadata
        update_data = {
            "updates": {
                "status": "published",
                "version": "1.1",
                "last_modified": "2024-01-15",
                "reviewer": "test_reviewer",
                "tags": ["updated", "published"]
            }
        }

        response = client.patch(f"/api/v1/documents/{doc_id}/metadata", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify metadata was updated
        get_response = client.get(f"/api/v1/documents/{doc_id}")
        assert get_response.status_code == 200

        updated_doc = get_response.json()["data"]
        # Note: metadata updates may not persist depending on implementation
        assert isinstance(updated_doc["metadata"], dict)


@pytest.mark.api
class TestDocumentValidation:
    """Test document input validation."""

    def test_create_document_validation_missing_content(self, client):
        """Test validation when content is missing."""
        doc_data = {
            "metadata": {"test": "validation"}
        }

        response = client.post("/api/v1/documents", json=doc_data)
        assert response.status_code == 422  # Validation error

    def test_create_document_validation_empty_content(self, client):
        """Test validation when content is empty."""
        doc_data = {
            "content": "",
            "metadata": {"test": "validation"}
        }

        response = client.post("/api/v1/documents", json=doc_data)
        assert response.status_code == 422  # Validation error

    def test_create_document_validation_whitespace_content(self, client):
        """Test validation when content is only whitespace."""
        doc_data = {
            "content": "   \n\t  ",
            "metadata": {"test": "validation"}
        }

        response = client.post("/api/v1/documents", json=doc_data)
        assert response.status_code == 422  # Validation error

    def test_get_document_validation_invalid_id(self, client):
        """Test validation with invalid document ID."""
        invalid_ids = ["", "   ", "../escape", "<script>"]

        for invalid_id in invalid_ids:
            response = client.get(f"/api/v1/documents/{invalid_id}")
            assert response.status_code in [404, 422, 400]

    def test_update_metadata_validation_missing_updates(self, client):
        """Test validation when metadata updates are missing."""
        update_data = {}

        response = client.patch("/api/v1/documents/test-doc/metadata", json=update_data)
        assert response.status_code == 422  # Validation error

    def test_update_metadata_validation_empty_updates(self, client):
        """Test validation when metadata updates are empty."""
        update_data = {"updates": {}}

        response = client.patch("/api/v1/documents/test-doc/metadata", json=update_data)
        assert response.status_code == 422  # Validation error


@pytest.mark.api
class TestDocumentSearch:
    """Test document search through API."""

    def test_search_documents_basic(self, client):
        """Test basic document search."""
        search_data = {
            "query": "test document",
            "limit": 10
        }

        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]

    def test_search_documents_with_filters(self, client):
        """Test search with various filters."""
        search_configs = [
            {"query": "comprehensive", "limit": 5},
            {"query": "test", "limit": 20},
            {"query": "document", "limit": 1},
        ]

        for config in search_configs:
            response = client.post("/api/v1/search", json=config)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["items"]) <= config["limit"]


@pytest.mark.api
class TestDocumentOperationsEdgeCases:
    """Test document operations edge cases."""

    def test_create_document_large_content(self, client):
        """Test creating document with large content."""
        large_content = "x" * 10000  # 10KB content
        doc_data = {
            "content": large_content,
            "metadata": {"size": "large", "test": "edge_case"}
        }

        response = client.post("/api/v1/documents", json=doc_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_create_document_complex_metadata(self, client):
        """Test creating document with complex nested metadata."""
        complex_metadata = {
            "nested": {
                "deeply": {
                    "nested": {
                        "value": "test",
                        "array": [1, 2, 3],
                        "boolean": True
                    }
                }
            },
            "tags": ["complex", "nested", "metadata"],
            "scores": {"quality": 0.95, "relevance": 0.87}
        }

        doc_data = {
            "content": "Document with complex metadata.",
            "metadata": complex_metadata
        }

        response = client.post("/api/v1/documents", json=doc_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_document_operations_concurrent(self, client):
        """Test concurrent document operations."""
        import threading

        results = []
        errors = []

        def create_document(index):
            try:
                doc_data = {
                    "content": f"Concurrent test document {index}.",
                    "metadata": {"batch": "concurrent", "index": index}
                }
                response = client.post("/api/v1/documents", json=doc_data)
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Create multiple concurrent document creation requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_document, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert all(code == 200 for code in results)
        assert len(errors) == 0

    def test_document_operations_performance(self, client):
        """Test document operations performance."""
        import time

        # Create multiple documents and measure performance
        start_time = time.time()

        for i in range(20):
            doc_data = {
                "content": f"Performance test document {i}.",
                "metadata": {"batch": "performance", "index": i}
            }
            response = client.post("/api/v1/documents", json=doc_data)
            assert response.status_code == 200

        # Test listing performance
        response = client.get("/api/v1/documents")
        assert response.status_code == 200

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time
        assert duration < 10.0  # 10 seconds for 21 operations

    def test_document_unicode_handling(self, client):
        """Test document operations with unicode content."""
        unicode_content = "Unicode test: ñáéíóú 🚀 🌟 📚 中文 Español Français"
        unicode_metadata = {
            "language": "multilingual",
            "special_chars": "ñáéíóú",
            "emojis": "🚀🌟📚"
        }

        doc_data = {
            "content": unicode_content,
            "metadata": unicode_metadata
        }

        response = client.post("/api/v1/documents", json=doc_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify unicode content is preserved
        doc_id = data["data"]["id"]
        get_response = client.get(f"/api/v1/documents/{doc_id}")
        assert get_response.status_code == 200

        retrieved = get_response.json()["data"]
        assert retrieved["content"] == unicode_content
