"""Unit tests for Document application handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from application.handlers.document_handler import DocumentHandler


class TestDocumentHandler:
    """Test cases for DocumentHandler application service."""

    @pytest.fixture
    def handler(self):
        """Create handler instance for testing."""
        return DocumentHandler()

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_service(self):
        """Create mock domain service."""
        return AsyncMock()

    def test_handler_initialization(self, handler):
        """Test handler initialization."""
        assert handler.simulations == {}  # In-memory storage
        assert hasattr(handler, 'create_document')
        assert hasattr(handler, 'get_document')
        assert hasattr(handler, 'list_documents')

    @pytest.mark.asyncio
    async def test_create_document_success(self, handler):
        """Test successful document creation."""
        result = await handler.create_document(
            content="This is a test document with enough content for processing.",
            title="Test Document",
            source="web",
            author="Test Author"
        )

        assert "document_id" in result
        assert result["title"] == "Test Document"
        assert "created_at" in result
        assert "word_count" in result
        assert result["word_count"] == 11  # Count of words in content

        # Check document was stored
        assert len(handler.simulations) == 1
        doc_id = result["document_id"]
        assert doc_id in handler.simulations

    @pytest.mark.asyncio
    async def test_create_document_minimal_fields(self, handler):
        """Test document creation with minimal required fields."""
        result = await handler.create_document(
            content="This is a test document with enough content for processing."
        )

        assert result["title"] is None
        assert "document_id" in result
        assert "word_count" in result

    @pytest.mark.asyncio
    async def test_get_document_success(self, handler):
        """Test successful document retrieval."""
        # First create a document
        create_result = await handler.create_document(
            content="This is a test document with enough content for processing.",
            title="Test Document"
        )
        doc_id = create_result["document_id"]

        # Now retrieve it
        result = await handler.get_document(doc_id)

        assert result["id"] == doc_id
        assert result["title"] == "Test Document"
        assert result["content"] == "This is a test document with enough content for processing."
        assert "metadata" in result
        assert "created_at" in result
        assert "updated_at" in result

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, handler):
        """Test document retrieval for non-existent document."""
        with pytest.raises(ValueError, match="Document nonexistent not found"):
            await handler.get_document("nonexistent")

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, handler):
        """Test listing documents when none exist."""
        result = await handler.list_documents()

        assert result["documents"] == []
        assert result["total_count"] == 0
        assert result["limit"] == 50
        assert result["offset"] == 0

    @pytest.mark.asyncio
    async def test_list_documents_with_data(self, handler):
        """Test listing documents with existing data."""
        # Create multiple documents
        await handler.create_document(
            content="First document with enough content for processing.",
            title="First Doc"
        )
        await handler.create_document(
            content="Second document with enough content for processing.",
            title="Second Doc"
        )

        result = await handler.list_documents(limit=10, offset=0)

        assert len(result["documents"]) == 2
        assert result["total_count"] == 2
        assert result["documents"][0]["title"] == "First Doc"
        assert result["documents"][1]["title"] == "Second Doc"

    @pytest.mark.asyncio
    async def test_list_documents_with_pagination(self, handler):
        """Test document listing with pagination."""
        # Create 5 documents
        for i in range(5):
            await handler.create_document(
                content=f"Document {i} with enough content for processing.",
                title=f"Doc {i}"
            )

        # Test pagination
        result = await handler.list_documents(limit=2, offset=1)

        assert len(result["documents"]) == 2
        assert result["total_count"] == 5
        assert result["limit"] == 2
        assert result["offset"] == 1
        assert result["documents"][0]["title"] == "Doc 1"
        assert result["documents"][1]["title"] == "Doc 2"

    @pytest.mark.asyncio
    async def test_update_document_success(self, handler):
        """Test successful document update."""
        # Create document
        create_result = await handler.create_document(
            content="Original content for testing.",
            title="Original Title"
        )
        doc_id = create_result["document_id"]

        # Update document
        update_result = await handler.update_document(
            document_id=doc_id,
            content="Updated content for testing.",
            title="Updated Title"
        )

        assert update_result["document_id"] == doc_id
        assert "updated_at" in update_result

        # Verify update
        doc = handler.simulations[doc_id]
        assert doc["content"] == "Updated content for testing."
        assert doc["title"] == "Updated Title"
        assert doc["version"] == 2  # Should be incremented

    @pytest.mark.asyncio
    async def test_update_document_not_found(self, handler):
        """Test updating non-existent document."""
        with pytest.raises(ValueError, match="Document nonexistent not found"):
            await handler.update_document("nonexistent", content="New content")

    @pytest.mark.asyncio
    async def test_delete_document_success(self, handler):
        """Test successful document deletion."""
        # Create document
        create_result = await handler.create_document(
            content="Document to be deleted."
        )
        doc_id = create_result["document_id"]

        # Delete document
        delete_result = await handler.delete_document(doc_id)

        assert delete_result["document_id"] == doc_id
        assert delete_result["deleted"] is True
        assert doc_id not in handler.simulations

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, handler):
        """Test deleting non-existent document."""
        with pytest.raises(ValueError, match="Document nonexistent not found"):
            await handler.delete_document("nonexistent")

    @pytest.mark.asyncio
    async def test_document_validation(self, handler):
        """Test document content validation."""
        # Test empty content
        with pytest.raises(Exception):  # Should raise validation error
            await handler.create_document(content="")

        # Test content too short
        with pytest.raises(Exception):  # Should raise validation error
            await handler.create_document(content="Short")
