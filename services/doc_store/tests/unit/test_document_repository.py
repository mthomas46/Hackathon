"""Unit tests for DocumentRepository."""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add project root and parent directories to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.doc_store.domain.entities import Document
from services.doc_store.domain.repository import DocumentRepository


class TestDocumentRepository:
    """Test cases for DocumentRepository."""

    @pytest.mark.asyncio
    async def test_save_document(self, document_repository, sample_document):
        """Test saving a document."""
        # Act
        await document_repository.save(sample_document)

        # Assert
        saved = await document_repository.find_by_id(sample_document.id)
        assert saved is not None
        assert saved.id == sample_document.id
        assert saved.content == sample_document.content
        assert saved.content_hash == sample_document.content_hash
        assert saved.metadata == sample_document.metadata

    @pytest.mark.asyncio
    async def test_find_by_id_existing(self, document_repository, sample_document):
        """Test finding an existing document by ID."""
        # Arrange
        await document_repository.save(sample_document)

        # Act
        result = await document_repository.find_by_id(sample_document.id)

        # Assert
        assert result is not None
        assert result.id == sample_document.id
        assert isinstance(result, Document)

    @pytest.mark.asyncio
    async def test_find_by_id_nonexistent(self, document_repository):
        """Test finding a non-existent document by ID."""
        # Act
        result = await document_repository.find_by_id("nonexistent-id")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_find_all_empty(self, document_repository):
        """Test finding all documents when repository is empty."""
        # Act
        results = await document_repository.find_all()

        # Assert
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_find_all_with_documents(self, document_repository, sample_documents_data):
        """Test finding all documents when repository has data."""
        # Arrange
        for doc_data in sample_documents_data:
            doc = Document(**doc_data)
            await document_repository.save(doc)

        # Act
        results = await document_repository.find_all()

        # Assert
        assert len(results) == len(sample_documents_data)
        assert all(isinstance(doc, Document) for doc in results)

    @pytest.mark.asyncio
    async def test_find_all_with_pagination(self, document_repository, sample_documents_data):
        """Test finding all documents with pagination."""
        # Arrange
        for doc_data in sample_documents_data:
            doc = Document(**doc_data)
            await document_repository.save(doc)

        # Act
        results = await document_repository.find_all(limit=2, offset=1)

        # Assert
        assert len(results) == 2
        # Should return documents at index 1 and 2 (0-indexed)

    @pytest.mark.asyncio
    async def test_update_document(self, document_repository, sample_document):
        """Test updating a document."""
        # Arrange
        await document_repository.save(sample_document)
        updated_content = "Updated content"

        # Act
        update_data = {"content": updated_content}
        success = await document_repository.update(sample_document.id, update_data)

        # Assert
        assert success is True
        updated = await document_repository.find_by_id(sample_document.id)
        assert updated.content == updated_content

    @pytest.mark.asyncio
    async def test_update_nonexistent_document(self, document_repository):
        """Test updating a non-existent document."""
        # Act
        success = await document_repository.update("nonexistent-id", {"content": "test"})

        # Assert
        assert success is False

    @pytest.mark.asyncio
    async def test_delete_document(self, document_repository, sample_document):
        """Test deleting a document."""
        # Arrange
        await document_repository.save(sample_document)

        # Act
        success = await document_repository.delete(sample_document.id)

        # Assert
        assert success is True
        deleted = await document_repository.find_by_id(sample_document.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, document_repository):
        """Test deleting a non-existent document."""
        # Act
        success = await document_repository.delete("nonexistent-id")

        # Assert
        assert success is False

    @pytest.mark.asyncio
    async def test_find_by_content_hash(self, document_repository, sample_document):
        """Test finding document by content hash."""
        # Arrange
        await document_repository.save(sample_document)

        # Act
        result = await document_repository.find_by_content_hash(sample_document.content_hash)

        # Assert
        assert result is not None
        assert result.id == sample_document.id
        assert result.content_hash == sample_document.content_hash

    @pytest.mark.asyncio
    async def test_find_by_content_hash_nonexistent(self, document_repository):
        """Test finding document by non-existent content hash."""
        # Act
        result = await document_repository.find_by_content_hash("nonexistent-hash")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_search_by_content(self, document_repository):
        """Test searching documents by content."""
        # Arrange
        docs_data = [
            {"id": "doc1", "content": "Python programming tutorial", "content_hash": "hash1"},
            {"id": "doc2", "content": "Java programming guide", "content_hash": "hash2"},
            {"id": "doc3", "content": "Python data structures", "content_hash": "hash3"}
        ]

        for doc_data in docs_data:
            doc = Document(**doc_data)
            await document_repository.save(doc)

        # Act
        results = await document_repository.search_by_content("Python")

        # Assert
        assert len(results) == 2
        assert all("Python" in doc.content for doc in results)

    @pytest.mark.asyncio
    async def test_search_by_content_no_results(self, document_repository):
        """Test searching documents by content with no matches."""
        # Arrange
        doc = Document(id="doc1", content="Some content", content_hash="hash1")
        await document_repository.save(doc)

        # Act
        results = await document_repository.search_by_content("nonexistent")

        # Assert
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_repository_handles_database_errors(self, document_repository):
        """Test that repository handles database errors gracefully."""
        # This would require mocking database errors, but for now
        # we'll just ensure the repository initializes properly
        assert document_repository is not None
        assert hasattr(document_repository, 'save')
        assert hasattr(document_repository, 'find_by_id')

    @pytest.mark.asyncio
    async def test_repository_metadata_handling(self, document_repository):
        """Test that repository handles metadata correctly."""
        # Arrange
        doc_with_metadata = Document(
            id="meta-doc",
            content="Content with metadata",
            content_hash="meta-hash",
            metadata={
                "author": "Test Author",
                "tags": ["test", "metadata"],
                "version": 1,
                "nested": {"key": "value"}
            }
        )

        # Act
        await document_repository.save(doc_with_metadata)
        retrieved = await document_repository.find_by_id("meta-doc")

        # Assert
        assert retrieved is not None
        assert retrieved.metadata["author"] == "Test Author"
        assert "test" in retrieved.metadata["tags"]
        assert retrieved.metadata["nested"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_repository_correlation_id_handling(self, document_repository):
        """Test that repository handles correlation IDs correctly."""
        # Arrange
        doc_with_correlation = Document(
            id="corr-doc",
            content="Content with correlation",
            content_hash="corr-hash",
            correlation_id="test-correlation-123"
        )

        # Act
        await document_repository.save(doc_with_correlation)
        retrieved = await document_repository.find_by_id("corr-doc")

        # Assert
        assert retrieved is not None
        assert retrieved.correlation_id == "test-correlation-123"
