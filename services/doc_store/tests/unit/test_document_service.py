"""Unit tests for DocumentService."""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

# Add project root and parent directories to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.entities import Document
from domain.documents.service import DocumentService
from core.repository import DocumentRepository


class TestDocumentService:
    """Test cases for DocumentService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        return AsyncMock(spec=DocumentRepository)

    @pytest.fixture
    def document_service(self, mock_repository):
        """Create a document service with mock repository."""
        return DocumentService(mock_repository)

    @pytest.mark.asyncio
    async def test_create_document_success(self, document_service, mock_repository):
        """Test successful document creation."""
        # Arrange
        content = "Test document content"
        metadata = {"author": "test_user"}

        mock_repository.find_by_content_hash.return_value = None
        mock_repository.save.return_value = None

        # Act
        result = await document_service.create_document(content, metadata)

        # Assert
        assert isinstance(result, Document)
        assert result.content == content
        assert result.metadata == metadata
        assert result.id is not None
        assert result.content_hash is not None
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_duplicate_content(self, document_service, mock_repository):
        """Test creating document with duplicate content returns existing."""
        # Arrange
        content = "Duplicate content"
        existing_doc = Document(
            id="existing-id",
            content=content,
            content_hash="duplicate-hash",
            metadata={"existing": True}
        )

        mock_repository.find_by_content_hash.return_value = existing_doc

        # Act
        result = await document_service.create_document(content)

        # Assert
        assert result == existing_doc
        mock_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_document_empty_content(self, document_service):
        """Test creating document with empty content raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            await document_service.create_document("")

    @pytest.mark.asyncio
    async def test_create_document_whitespace_content(self, document_service):
        """Test creating document with whitespace-only content raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            await document_service.create_document("   \n\t   ")

    @pytest.mark.asyncio
    async def test_get_document_by_id_success(self, document_service, mock_repository, sample_document):
        """Test successfully getting document by ID."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_document

        # Act
        result = await document_service.get_document_by_id(sample_document.id)

        # Assert
        assert result == sample_document
        mock_repository.find_by_id.assert_called_once_with(sample_document.id)

    @pytest.mark.asyncio
    async def test_get_document_by_id_not_found(self, document_service, mock_repository):
        """Test getting non-existent document by ID."""
        # Arrange
        mock_repository.find_by_id.return_value = None

        # Act
        result = await document_service.get_document_by_id("nonexistent-id")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_documents(self, document_service, mock_repository, sample_documents_data):
        """Test getting all documents."""
        # Arrange
        documents = [Document(**data) for data in sample_documents_data]
        mock_repository.find_all.return_value = documents

        # Act
        result = await document_service.get_all_documents()

        # Assert
        assert result == documents
        mock_repository.find_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_documents_with_pagination(self, document_service, mock_repository):
        """Test getting all documents with pagination."""
        # Arrange
        mock_repository.find_all.return_value = []

        # Act
        result = await document_service.get_all_documents(limit=10, offset=5)

        # Assert
        mock_repository.find_all.assert_called_once_with(limit=10, offset=5)

    @pytest.mark.asyncio
    async def test_update_document_success(self, document_service, mock_repository, sample_document):
        """Test successful document update."""
        # Arrange
        new_content = "Updated content"
        mock_repository.find_by_id.return_value = sample_document
        mock_repository.update.return_value = True

        # Act
        result = await document_service.update_document(sample_document.id, new_content)

        # Assert
        assert result is True
        mock_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_not_found(self, document_service, mock_repository):
        """Test updating non-existent document."""
        # Arrange
        mock_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Document with ID nonexistent not found"):
            await document_service.update_document("nonexistent", "new content")

    @pytest.mark.asyncio
    async def test_delete_document_success(self, document_service, mock_repository, sample_document):
        """Test successful document deletion."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_document
        mock_repository.delete.return_value = True

        # Act
        result = await document_service.delete_document(sample_document.id)

        # Assert
        assert result is True
        mock_repository.delete.assert_called_once_with(sample_document.id)

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, document_service, mock_repository):
        """Test deleting non-existent document."""
        # Arrange
        mock_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Document with ID nonexistent not found"):
            await document_service.delete_document("nonexistent")

    @pytest.mark.asyncio
    async def test_search_documents(self, document_service, mock_repository):
        """Test document search functionality."""
        # Arrange
        search_results = [Document(id="doc1", content="Python tutorial", content_hash="hash1")]
        mock_repository.search_by_content.return_value = search_results

        # Act
        result = await document_service.search_documents("Python")

        # Assert
        assert result == search_results
        mock_repository.search_by_content.assert_called_once_with("Python", 50)

    @pytest.mark.asyncio
    async def test_search_documents_with_limit(self, document_service, mock_repository):
        """Test document search with custom limit."""
        # Arrange
        mock_repository.search_by_content.return_value = []

        # Act
        result = await document_service.search_documents("test", limit=20)

        # Assert
        mock_repository.search_by_content.assert_called_once_with("test", 20)

    @pytest.mark.asyncio
    async def test_get_document_statistics(self, document_service, mock_repository):
        """Test getting document statistics."""
        # Arrange
        mock_repository.find_all.return_value = [
            Document(id="doc1", content="content1", content_hash="hash1"),
            Document(id="doc2", content="content2", content_hash="hash2"),
        ]

        # Act
        stats = await document_service.get_document_statistics()

        # Assert
        assert "total_documents" in stats
        assert stats["total_documents"] == 2

    @pytest.mark.asyncio
    async def test_bulk_create_documents(self, document_service, mock_repository):
        """Test bulk document creation."""
        # Arrange
        documents_data = [
            {"content": "Doc 1", "metadata": {"index": 1}},
            {"content": "Doc 2", "metadata": {"index": 2}},
        ]
        mock_repository.find_by_content_hash.return_value = None
        mock_repository.save.return_value = None

        # Act
        results = await document_service.bulk_create_documents(documents_data)

        # Assert
        assert len(results) == 2
        assert all(isinstance(doc, Document) for doc in results)
        assert mock_repository.save.call_count == 2

    @pytest.mark.asyncio
    async def test_bulk_create_with_duplicates(self, document_service, mock_repository):
        """Test bulk creation handles duplicates correctly."""
        # Arrange
        existing_doc = Document(id="existing", content="Existing content", content_hash="existing-hash")
        documents_data = [
            {"content": "Existing content"},  # Duplicate
            {"content": "New content"}        # New
        ]

        def mock_find_by_hash(content_hash):
            if content_hash == "existing-hash":
                return existing_doc
            return None

        mock_repository.find_by_content_hash.side_effect = mock_find_by_hash

        # Act
        results = await document_service.bulk_create_documents(documents_data)

        # Assert
        assert len(results) == 2
        assert results[0] == existing_doc  # Duplicate returns existing
        assert isinstance(results[1], Document)  # New creates new document

    @pytest.mark.asyncio
    async def test_validate_document_content(self, document_service):
        """Test document content validation."""
        # Valid content should not raise
        await document_service._validate_document_content("Valid content")

        # Empty content should raise
        with pytest.raises(ValueError):
            await document_service._validate_document_content("")

        # Whitespace-only content should raise
        with pytest.raises(ValueError):
            await document_service._validate_document_content("   \n\t  ")

    @pytest.mark.asyncio
    async def test_validate_metadata(self, document_service):
        """Test metadata validation."""
        # Valid metadata should not raise
        await document_service._validate_metadata({"author": "user", "tags": ["tag1"]})

        # None metadata should be handled
        await document_service._validate_metadata(None)

        # Non-dict metadata should raise
        with pytest.raises(ValueError):
            await document_service._validate_metadata("invalid")

    @pytest.mark.asyncio
    async def test_service_handles_repository_errors(self, document_service, mock_repository):
        """Test that service handles repository errors gracefully."""
        # Arrange
        mock_repository.find_by_id.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception):  # Should propagate repository errors
            await document_service.get_document_by_id("test-id")

    @pytest.mark.asyncio
    async def test_service_repository_injection(self):
        """Test that service properly injects repository dependency."""
        # Arrange
        mock_repo = AsyncMock()

        # Act
        service = DocumentService(mock_repo)

        # Assert
        assert service.repository == mock_repo
