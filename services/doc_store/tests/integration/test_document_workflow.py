"""Integration tests for document workflow functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from doc_store.domain.services.document_service import DocumentService
from doc_store.infrastructure.repositories.document_repository import DocumentRepository
from doc_store.infrastructure.adapters.database_adapter import DatabaseAdapter
from doc_store.infrastructure.services.cache_service import CacheService


class TestDocumentWorkflowIntegration:
    """Integration tests for complete document workflow."""

    @pytest.fixture
    def mock_db_adapter(self):
        """Create mock database adapter."""
        return MagicMock(spec=DatabaseAdapter)

    @pytest.fixture
    def mock_cache_service(self, mock_db_adapter):
        """Create mock cache service."""
        return CacheMock()  # Use a simple mock cache

    @pytest.fixture
    def document_repo(self, mock_db_adapter):
        """Create document repository."""
        return DocumentRepository(mock_db_adapter)

    @pytest.fixture
    def document_service(self, document_repo, mock_cache_service):
        """Create document service with dependencies."""
        return DocumentService(document_repo, mock_cache_service)

    @pytest.mark.asyncio
    async def test_create_and_retrieve_document_workflow(self, document_service, document_repo):
        """Test complete workflow of creating and retrieving a document."""
        # Setup test data
        doc_id = "test-workflow-doc"
        content = "This is a test document for workflow integration."
        metadata = {"author": "test_user", "version": "1.0"}
        tags = ["integration", "test"]

        # Mock repository save
        saved_doc = {
            "id": doc_id,
            "content": content,
            "metadata": metadata,
            "tags": tags
        }
        document_repo.save = MagicMock(return_value=saved_doc)
        document_repo.find_by_id = MagicMock(return_value=saved_doc)

        # Execute workflow
        created_doc = await document_service.create_document(
            doc_id, content, metadata, tags
        )

        # Verify creation
        assert created_doc["id"] == doc_id
        assert created_doc["content"] == content
        assert created_doc["metadata"] == metadata
        assert created_doc["tags"] == tags

        # Verify retrieval
        retrieved_doc = await document_service.get_document(doc_id)
        assert retrieved_doc == created_doc

        # Verify repository interactions
        document_repo.save.assert_called_once()
        document_repo.find_by_id.assert_called()

    @pytest.mark.asyncio
    async def test_search_and_filter_workflow(self, document_service, document_repo):
        """Test document search and filtering workflow."""
        # Setup test data with multiple documents
        documents = [
            {
                "id": "doc-1",
                "content": "Python programming tutorial",
                "metadata": {"category": "tutorial"},
                "tags": ["python", "programming"]
            },
            {
                "id": "doc-2",
                "content": "JavaScript basics guide",
                "metadata": {"category": "guide"},
                "tags": ["javascript", "basics"]
            },
            {
                "id": "doc-3",
                "content": "Advanced Python patterns",
                "metadata": {"category": "advanced"},
                "tags": ["python", "advanced"]
            }
        ]

        # Mock repository methods
        document_repo.search = MagicMock(return_value=[
            doc for doc in documents if "python" in doc["content"].lower()
        ])
        document_repo.count = MagicMock(return_value=len(documents))

        # Execute search workflow
        search_results = await document_service.search_documents("python")
        total_count = await document_service.get_document_statistics()

        # Verify search results
        assert len(search_results) == 2
        assert all("python" in doc["content"].lower() for doc in search_results)

        # Verify statistics
        assert total_count["total_documents"] == 3

    @pytest.mark.asyncio
    async def test_update_and_tag_workflow(self, document_service, document_repo):
        """Test document update and tagging workflow."""
        # Setup initial document
        doc_id = "update-test-doc"
        initial_doc = {
            "id": doc_id,
            "content": "Initial content",
            "metadata": {"version": "1.0"},
            "tags": ["initial"]
        }

        updated_doc = {
            "id": doc_id,
            "content": "Updated content with new information",
            "metadata": {"version": "2.0", "last_modified": "2024-01-01"},
            "tags": ["initial", "updated", "featured"]
        }

        # Mock repository methods
        document_repo.find_by_id = MagicMock(return_value=initial_doc)
        document_repo.save = MagicMock(return_value=updated_doc)

        # Execute update workflow
        updated_result = await document_service.update_document(
            doc_id, "Updated content with new information",
            {"version": "2.0", "last_modified": "2024-01-01"}
        )

        # Verify update
        assert updated_result["content"] == "Updated content with new information"
        assert updated_result["metadata"]["version"] == "2.0"

        # Execute tagging workflow
        tagged_result = await document_service.tag_document(doc_id, ["featured"])

        # Verify tagging
        assert "featured" in tagged_result["tags"]
        assert "initial" in tagged_result["tags"]
        assert "updated" in tagged_result["tags"]

    @pytest.mark.asyncio
    async def test_delete_workflow(self, document_service, document_repo):
        """Test document deletion workflow."""
        doc_id = "delete-test-doc"

        # Mock repository methods
        document_repo.exists = MagicMock(return_value=True)
        document_repo.delete = MagicMock(return_value=True)
        document_repo.find_by_id = MagicMock(return_value=None)  # After deletion

        # Verify document exists before deletion
        exists_before = await document_service.document_exists(doc_id)
        assert exists_before is True

        # Execute deletion
        delete_result = await document_service.delete_document(doc_id)
        assert delete_result is True

        # Verify document no longer exists
        exists_after = await document_service.document_exists(doc_id)
        assert exists_after is False

        # Verify repository interactions
        document_repo.delete.assert_called_once_with(doc_id)

    @pytest.mark.asyncio
    async def test_bulk_operations_workflow(self, document_service, document_repo):
        """Test bulk document operations workflow."""
        # Setup bulk document data
        bulk_docs = [
            {
                "id": f"bulk-doc-{i}",
                "content": f"Content for document {i}",
                "metadata": {"batch": "test-batch"},
                "tags": ["bulk", f"doc-{i}"]
            }
            for i in range(1, 4)
        ]

        # Mock repository methods
        document_repo.find_all = MagicMock(return_value=bulk_docs[:2])  # Limited results
        document_repo.count = MagicMock(return_value=len(bulk_docs))

        # Execute bulk retrieval workflow
        bulk_results = await document_service.get_documents(limit=2, offset=0)
        stats = await document_service.get_document_statistics()

        # Verify bulk operations
        assert len(bulk_results) == 2
        assert stats["total_documents"] == 3
        assert all(doc["metadata"]["batch"] == "test-batch" for doc in bulk_results)

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, document_service, document_repo):
        """Test error handling in document workflows."""
        # Test document not found scenario
        document_repo.find_by_id = MagicMock(return_value=None)

        with pytest.raises(ValueError, match="Document .* not found"):
            await document_service.get_document("nonexistent-doc")

        # Test invalid document creation
        with pytest.raises(ValueError, match="Document ID cannot be empty"):
            await document_service.create_document("", "content")

        # Test invalid metadata
        with pytest.raises(ValueError, match="Invalid metadata format"):
            await document_service.update_document("test-doc", "content", "invalid-metadata")

    @pytest.mark.asyncio
    async def test_caching_integration_workflow(self, document_service, mock_cache_service):
        """Test caching integration in document workflow."""
        doc_id = "cache-test-doc"
        doc_data = {
            "id": doc_id,
            "content": "Cached document content",
            "metadata": {},
            "tags": ["cached"]
        }

        # Mock cache behavior
        mock_cache_service.get = MagicMock(return_value=None)  # Cache miss
        mock_cache_service.set = MagicMock(return_value=True)

        # Mock repository
        document_service._repository.find_by_id = AsyncMock(return_value=doc_data)

        # First call - should cache the result
        result1 = await document_service.get_document(doc_id)
        assert result1 == doc_data

        # Verify cache was checked and set
        mock_cache_service.get.assert_called_with(f"document:{doc_id}")
        mock_cache_service.set.assert_called_with(f"document:{doc_id}", doc_data)

        # Second call - should use cache
        mock_cache_service.get = MagicMock(return_value=doc_data)
        result2 = await document_service.get_document(doc_id)

        assert result2 == doc_data
        # Should not have called repository again
        assert document_service._repository.find_by_id.call_count == 1


class CacheMock:
    """Simple mock cache for testing."""

    def __init__(self):
        self.store = {}

    def get(self, key):
        """Get value from cache."""
        return self.store.get(key)

    def set(self, key, value, ttl=None):
        """Set value in cache."""
        self.store[key] = value
        return True

    def delete(self, key):
        """Delete from cache."""
        return self.store.pop(key, None) is not None

    def clear(self):
        """Clear all cache."""
        self.store.clear()
        return True

    def cleanup_expired(self):
        """Cleanup expired entries."""
        return 0

    def health_check(self):
        """Health check."""
        return {"status": "healthy"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
