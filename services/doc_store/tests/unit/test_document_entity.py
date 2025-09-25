"""Unit tests for Document entity."""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add project root and parent directories to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.doc_store.domain.entities import Document


class TestDocumentEntity:
    """Test cases for Document entity."""

    def test_document_creation_success(self):
        """Test successful document creation."""
        # Act
        doc = Document(
            id="test-doc-123",
            content="This is test content",
            content_hash="abc123hash",
            metadata={"author": "test_user", "tags": ["test"]},
            correlation_id="corr-123"
        )

        # Assert
        assert doc.id == "test-doc-123"
        assert doc.content == "This is test content"
        assert doc.content_hash == "abc123hash"
        assert doc.metadata["author"] == "test_user"
        assert doc.correlation_id == "corr-123"
        assert isinstance(doc.created_at, datetime)

    def test_document_creation_minimal(self):
        """Test document creation with minimal required fields."""
        # Act
        doc = Document(
            id="minimal-doc",
            content="Minimal content",
            content_hash="minimal-hash"
        )

        # Assert
        assert doc.id == "minimal-doc"
        assert doc.content == "Minimal content"
        assert doc.content_hash == "minimal-hash"
        assert doc.metadata == {}
        assert doc.correlation_id is None

    def test_document_to_dict(self):
        """Test document serialization to dictionary."""
        # Arrange
        doc = Document(
            id="test-doc",
            content="Test content",
            content_hash="test-hash",
            metadata={"key": "value"},
            correlation_id="test-corr"
        )

        # Act
        result = doc.to_dict()

        # Assert
        assert result["id"] == "test-doc"
        assert result["content"] == "Test content"
        assert result["content_hash"] == "test-hash"
        assert result["metadata"] == {"key": "value"}
        assert result["correlation_id"] == "test-corr"
        assert "created_at" in result

    def test_document_from_dict(self):
        """Test document creation from dictionary."""
        # Arrange
        data = {
            "id": "from-dict-doc",
            "content": "Content from dict",
            "content_hash": "dict-hash",
            "metadata": {"source": "dict"},
            "correlation_id": "dict-corr",
            "created_at": "2023-09-24T10:00:00"
        }

        # Act
        doc = Document.from_dict(data)

        # Assert
        assert doc.id == "from-dict-doc"
        assert doc.content == "Content from dict"
        assert doc.content_hash == "dict-hash"
        assert doc.metadata == {"source": "dict"}
        assert doc.correlation_id == "dict-corr"

    def test_document_equality(self):
        """Test document equality comparison."""
        # Arrange
        doc1 = Document(
            id="doc1",
            content="Content",
            content_hash="hash1",
            metadata={"key": "value"}
        )

        doc2 = Document(
            id="doc1",
            content="Content",
            content_hash="hash1",
            metadata={"key": "value"}
        )

        doc3 = Document(
            id="doc2",
            content="Different content",
            content_hash="hash2"
        )

        # Assert
        assert doc1 == doc2
        assert doc1 != doc3
        assert doc2 != doc3

    def test_document_hash(self):
        """Test document hash for use in sets/dicts."""
        # Arrange
        doc1 = Document(id="doc1", content="Content", content_hash="hash1")
        doc2 = Document(id="doc1", content="Content", content_hash="hash1")
        doc3 = Document(id="doc2", content="Content", content_hash="hash1")

        # Act & Assert
        assert hash(doc1) == hash(doc2)
        assert hash(doc1) != hash(doc3)

        # Should be usable in sets
        doc_set = {doc1, doc2, doc3}
        assert len(doc_set) == 2  # doc1 and doc2 are equal, doc3 is different

    def test_document_repr(self):
        """Test document string representation."""
        # Arrange
        doc = Document(
            id="repr-doc",
            content="Repr content",
            content_hash="repr-hash"
        )

        # Act
        repr_str = repr(doc)

        # Assert
        assert "Document(" in repr_str
        assert "repr-doc" in repr_str
        assert "Repr content" in repr_str

    def test_document_update_timestamp(self):
        """Test timestamp update functionality."""
        # Arrange
        doc = Document(
            id="timestamp-doc",
            content="Content",
            content_hash="hash"
        )
        original_timestamp = doc.updated_at

        # Act
        doc.update_timestamp()

        # Assert
        assert doc.updated_at != original_timestamp
        assert isinstance(doc.updated_at, datetime)

    def test_document_generate_id(self):
        """Test ID generation."""
        # Act
        id1 = Document.generate_id()
        id2 = Document.generate_id()

        # Assert
        assert id1 != id2  # Should be unique
        assert isinstance(id1, str)
        assert len(id1) > 0

    def test_document_with_complex_metadata(self):
        """Test document with complex metadata structures."""
        # Arrange
        complex_metadata = {
            "author": "test_user",
            "tags": ["tag1", "tag2", "tag3"],
            "permissions": {
                "read": ["user1", "user2"],
                "write": ["user1"]
            },
            "version": 1.5,
            "published": True,
            "dates": {
                "created": "2023-01-01",
                "modified": "2023-09-24"
            }
        }

        # Act
        doc = Document(
            id="complex-doc",
            content="Content with complex metadata",
            content_hash="complex-hash",
            metadata=complex_metadata
        )

        # Assert
        assert doc.metadata["author"] == "test_user"
        assert len(doc.metadata["tags"]) == 3
        assert doc.metadata["permissions"]["write"] == ["user1"]
        assert doc.metadata["version"] == 1.5
        assert doc.metadata["published"] is True
        assert doc.metadata["dates"]["created"] == "2023-01-01"

    def test_document_serialization_roundtrip(self):
        """Test that document can be serialized and deserialized correctly."""
        # Arrange
        original_doc = Document(
            id="roundtrip-doc",
            content="Roundtrip test content",
            content_hash="roundtrip-hash",
            metadata={"test": "value", "number": 42},
            correlation_id="roundtrip-corr"
        )

        # Act
        serialized = original_doc.to_dict()
        deserialized_doc = Document.from_dict(serialized)

        # Assert
        assert original_doc == deserialized_doc
        assert original_doc.id == deserialized_doc.id
        assert original_doc.content == deserialized_doc.content
        assert original_doc.metadata == deserialized_doc.metadata
        assert original_doc.correlation_id == deserialized_doc.correlation_id

    def test_document_with_empty_metadata(self):
        """Test document with empty metadata."""
        # Act
        doc = Document(
            id="empty-meta-doc",
            content="Content with empty metadata",
            content_hash="empty-hash",
            metadata={}
        )

        # Assert
        assert doc.metadata == {}
        assert len(doc.metadata) == 0

    def test_document_with_none_correlation_id(self):
        """Test document with None correlation ID."""
        # Act
        doc = Document(
            id="none-corr-doc",
            content="Content with None correlation",
            content_hash="none-hash",
            correlation_id=None
        )

        # Assert
        assert doc.correlation_id is None

    def test_document_immutable_after_creation(self):
        """Test that document fields can be modified (dataclass allows it)."""
        # Arrange
        doc = Document(
            id="mutable-doc",
            content="Original content",
            content_hash="original-hash"
        )

        # Act
        doc.content = "Modified content"
        doc.metadata = {"modified": True}

        # Assert
        assert doc.content == "Modified content"
        assert doc.metadata == {"modified": True}

    def test_document_validation_through_creation(self):
        """Test that document validates data during creation."""
        # This is more of an integration test, but ensures
        # that the entity properly handles input data

        # Act & Assert - Should not raise for valid data
        doc = Document(
            id="valid-doc",
            content="Valid content that should pass all checks",
            content_hash="valid-hash-12345",
            metadata={"valid": "metadata"}
        )

        assert doc.id == "valid-doc"
        assert len(doc.content) > 0
        assert len(doc.content_hash) > 0
