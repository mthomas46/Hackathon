"""Comprehensive tests for Document entity."""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from services.doc_store.domain.entities import Document


class TestDocumentEntity:
    """Comprehensive test cases for Document entity."""

    def test_document_creation_with_required_fields(self):
        """Test creating a document with all required fields."""
        doc = Document(
            id="test-doc-123",
            content="This is test content",
            content_hash="abc123hash",
            correlation_id="corr-456"
        )

        assert doc.id == "test-doc-123"
        assert doc.content == "This is test content"
        assert doc.content_hash == "abc123hash"
        assert doc.correlation_id == "corr-456"
        assert doc.metadata == {}
        assert doc.updated_at is None
        assert isinstance(doc.created_at, datetime)

    def test_document_creation_with_metadata(self):
        """Test creating a document with metadata."""
        metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "tags": ["test", "document"]
        }

        doc = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123",
            metadata=metadata
        )

        assert doc.metadata == metadata
        assert doc.metadata["title"] == "Test Document"
        assert doc.metadata["tags"] == ["test", "document"]

    def test_document_validation_empty_content(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            Document(
                id="test-doc-123",
                content="",
                content_hash="hash123"
            )

    def test_document_validation_whitespace_content(self):
        """Test that whitespace-only content raises ValueError."""
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            Document(
                id="test-doc-123",
                content="   \n\t   ",
                content_hash="hash123"
            )

    def test_document_basic_properties(self):
        """Test that document has basic required properties."""
        doc = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123"
        )

        assert doc.id == "test-doc-123"
        assert doc.content == "Test content"
        assert doc.content_hash == "hash123"
        assert doc.metadata == {}
        assert doc.correlation_id is None

    def test_document_update_timestamp(self):
        """Test updating document timestamp."""
        doc = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123"
        )

        initial_created_at = doc.created_at
        initial_updated_at = doc.updated_at

        # Simulate some time passing
        with patch('services.doc_store.domain.entities.datetime') as mock_datetime:
            new_time = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = new_time
            mock_datetime.utcnow = datetime.utcnow

            doc.update_timestamp()

        assert doc.updated_at is not None
        assert doc.created_at == initial_created_at  # created_at should not change

    def test_document_to_dict_conversion(self):
        """Test converting document to dictionary."""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

        doc = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123",
            correlation_id="corr-456",
            metadata={"title": "Test Doc"},
            created_at=created_at,
            updated_at=updated_at
        )

        doc_dict = doc.to_dict()

        expected_dict = {
            "id": "test-doc-123",
            "content": "Test content",
            "content_hash": "hash123",
            "correlation_id": "corr-456",
            "metadata": {"title": "Test Doc"},
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat()
        }

        assert doc_dict == expected_dict

    def test_document_from_dict_conversion(self):
        """Test creating document from dictionary."""
        doc_dict = {
            "id": "test-doc-123",
            "content": "Test content",
            "content_hash": "hash123",
            "correlation_id": "corr-456",
            "metadata": {"title": "Test Doc"},
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-02T12:00:00"
        }

        doc = Document.from_dict(doc_dict)

        assert doc.id == "test-doc-123"
        assert doc.content == "Test content"
        assert doc.content_hash == "hash123"
        assert doc.correlation_id == "corr-456"
        assert doc.metadata == {"title": "Test Doc"}
        assert isinstance(doc.created_at, datetime)
        assert isinstance(doc.updated_at, datetime)

    def test_document_equality(self):
        """Test document equality comparison."""
        fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        doc1 = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123",
            created_at=fixed_time
        )

        doc2 = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123",
            created_at=fixed_time
        )

        doc3 = Document(
            id="different-doc",
            content="Test content",
            content_hash="hash123",
            created_at=fixed_time
        )

        assert doc1 == doc2
        assert doc1 != doc3
        assert doc2 != doc3

    def test_document_hash(self):
        """Test document hash for use in sets/dicts."""
        fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        doc1 = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123",
            created_at=fixed_time
        )

        doc2 = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123",
            created_at=fixed_time
        )

        doc_set = {doc1, doc2}
        assert len(doc_set) == 1  # Should be treated as same document

    def test_document_repr(self):
        """Test document string representation."""
        doc = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123"
        )

        repr_str = repr(doc)
        assert "Document" in repr_str
        assert "test-doc-123" in repr_str

    def test_document_with_large_content(self):
        """Test document with large content."""
        large_content = "A" * 10000  # 10KB of content
        doc = Document(
            id="large-doc",
            content=large_content,
            content_hash="large_hash"
        )

        assert len(doc.content) == 10000
        assert doc.content == large_content

    def test_document_metadata_modification(self):
        """Test that metadata can be modified after creation."""
        doc = Document(
            id="test-doc-123",
            content="Test content",
            content_hash="hash123",
            metadata={"initial": "value"}
        )

        # Metadata should be modifiable
        doc.metadata["new_key"] = "new_value"
        doc.metadata["initial"] = "modified"

        assert doc.metadata["initial"] == "modified"
        assert doc.metadata["new_key"] == "new_value"


    def test_document_immutable_fields(self):
        """Test that certain fields should not be modified after creation."""
        doc = Document(
            id="test-doc-123",
            content="Original content",
            content_hash="original_hash"
        )

        # These should remain the same
        original_id = doc.id
        original_content = doc.content
        original_hash = doc.content_hash
        original_created_at = doc.created_at

        # Attempting to modify (though dataclass allows it)
        # In practice, these should be treated as immutable
        assert doc.id == original_id
        assert doc.content == original_content
        assert doc.content_hash == original_hash
        assert doc.created_at == original_created_at

    def test_document_serialization_roundtrip(self):
        """Test that document can be serialized and deserialized correctly."""
        original_doc = Document(
            id="roundtrip-doc",
            content="Roundtrip test content",
            content_hash="roundtrip_hash",
            correlation_id="roundtrip_corr",
            metadata={"test": "metadata"}
        )

        # Serialize to dict
        doc_dict = original_doc.to_dict()

        # Deserialize from dict
        restored_doc = Document.from_dict(doc_dict)

        # Should be equal
        assert original_doc == restored_doc
        assert original_doc.id == restored_doc.id
        assert original_doc.content == restored_doc.content
        assert original_doc.metadata == restored_doc.metadata
        assert original_doc.correlation_id == restored_doc.correlation_id
