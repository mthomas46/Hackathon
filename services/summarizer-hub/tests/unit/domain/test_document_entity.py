"""Unit tests for Document domain entity."""

import pytest
from datetime import datetime
from domain.entities.document import Document, DocumentId, DocumentMetadata


class TestDocumentId:
    """Test cases for DocumentId value object."""

    def test_generate_creates_unique_ids(self):
        """Test that generated IDs are unique."""
        id1 = DocumentId.generate()
        id2 = DocumentId.generate()

        assert id1 != id2
        assert isinstance(id1.value, str)
        assert isinstance(id2.value, str)

    def test_id_string_representation(self):
        """Test string representation of DocumentId."""
        doc_id = DocumentId("test-123")
        assert str(doc_id) == "test-123"

    def test_empty_id_raises_error(self):
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Document ID cannot be empty"):
            DocumentId("")


class TestDocumentMetadata:
    """Test cases for DocumentMetadata value object."""

    def test_default_initialization(self):
        """Test default metadata initialization."""
        metadata = DocumentMetadata()
        assert metadata.source is None
        assert metadata.author is None
        assert metadata.language == "en"
        assert metadata.word_count == 0
        assert metadata.tags == []
        assert metadata.custom_fields == {}

    def test_custom_initialization(self):
        """Test custom metadata initialization."""
        metadata = DocumentMetadata(
            source="web",
            author="Test Author",
            language="es",
            tags=["test", "sample"],
            custom_fields={"priority": "high"}
        )
        assert metadata.source == "web"
        assert metadata.author == "Test Author"
        assert metadata.language == "es"
        assert metadata.tags == ["test", "sample"]
        assert metadata.custom_fields == {"priority": "high"}


class TestDocument:
    """Test cases for Document aggregate root."""

    def test_create_document_success(self):
        """Test successful document creation."""
        doc = Document.create(
            content="This is a test document with enough content for processing.",
            title="Test Document",
            source="test",
            author="Test Author"
        )

        assert isinstance(doc.id, DocumentId)
        assert doc.content == "This is a test document with enough content for processing."
        assert doc.title == "Test Document"
        assert doc.metadata.source == "test"
        assert doc.metadata.author == "Test Author"
        assert doc.version == 1
        assert isinstance(doc.created_at, datetime)
        assert isinstance(doc.updated_at, datetime)

    def test_create_document_without_optional_fields(self):
        """Test document creation with minimal required fields."""
        doc = Document.create(content="This is a test document with enough content for processing.")

        assert doc.title is None
        assert doc.metadata.source is None
        assert doc.metadata.author is None

    def test_create_document_content_too_short(self):
        """Test that short content raises ValueError."""
        with pytest.raises(ValueError, match="Document content too short"):
            Document.create(content="Short")

    def test_create_document_empty_content(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            Document.create(content="")

    def test_update_content(self):
        """Test content update functionality."""
        doc = Document.create(content="Original content for testing.")
        original_version = doc.version
        original_updated = doc.updated_at

        doc.update_content("Updated content for testing.", "New Title")

        assert doc.content == "Updated content for testing."
        assert doc.title == "New Title"
        assert doc.version == original_version + 1
        assert doc.updated_at > original_updated

    def test_update_metadata(self):
        """Test metadata update functionality."""
        doc = Document.create(content="Test content.")
        original_updated = doc.updated_at

        doc.update_metadata(source="web", author="New Author")

        assert doc.metadata.source == "web"
        assert doc.metadata.author == "New Author"
        assert doc.updated_at > original_updated

    def test_add_and_remove_tags(self):
        """Test tag management functionality."""
        doc = Document.create(content="Test content.")
        original_updated = doc.updated_at

        # Add tags
        doc.add_tag("important")
        doc.add_tag("test")

        assert "important" in doc.metadata.tags
        assert "test" in doc.metadata.tags
        assert doc.updated_at > original_updated

        # Remove tag
        updated_time = doc.updated_at
        doc.remove_tag("test")

        assert "important" in doc.metadata.tags
        assert "test" not in doc.metadata.tags
        assert doc.updated_at > updated_time

    def test_get_word_count(self):
        """Test word count calculation."""
        doc = Document.create(content="This is a test document with multiple words.")
        assert doc.get_word_count() == 8

    def test_is_recent(self):
        """Test recent document detection."""
        doc = Document.create(content="Test content.")
        assert doc.is_recent(days=1)  # Should be recent

        # Create old document
        old_doc = Document(
            id=DocumentId.generate(),
            content="Old content.",
            created_at=datetime(2020, 1, 1),
            updated_at=datetime(2020, 1, 1)
        )
        assert not old_doc.is_recent(days=1)

    def test_document_immutability_protection(self):
        """Test that critical fields are properly initialized."""
        doc = Document.create(content="Test content.")

        # These should be set during creation
        assert doc.created_at is not None
        assert doc.updated_at is not None
        assert doc.version == 1
