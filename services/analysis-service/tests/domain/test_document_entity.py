"""Unit tests for Document domain entity."""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from ...domain.entities.document import Document
from ...domain.exceptions import ValidationError
from ..conftest import assert_validation_error


class TestDocumentEntity:
    """Test cases for Document entity."""

    def test_document_creation_valid_data(self, sample_document_data):
        """Test creating a document with valid data."""
        doc = Document(**sample_document_data)

        assert doc.id == sample_document_data['id']
        assert doc.title == sample_document_data['title']
        assert doc.content == sample_document_data['content']
        assert doc.author == sample_document_data['author']
        assert doc.tags == sample_document_data['tags']
        assert doc.metadata == sample_document_data['metadata']
        assert doc.created_at is not None
        assert doc.updated_at is not None

    def test_document_creation_missing_required_fields(self):
        """Test creating a document with missing required fields."""
        # Missing title
        with pytest.raises((ValueError, TypeError)):
            Document(
                id='doc-123',
                content='Test content',
                author='Test Author'
            )

        # Missing content
        with pytest.raises((ValueError, TypeError)):
            Document(
                id='doc-123',
                title='Test Title',
                author='Test Author'
            )

    def test_document_creation_empty_title(self):
        """Test creating a document with empty title."""
        assert_validation_error(
            Document,
            id='doc-123',
            title='',
            content='Test content',
            author='Test Author'
        )

    def test_document_creation_empty_content(self):
        """Test creating a document with empty content."""
        assert_validation_error(
            Document,
            id='doc-123',
            title='Test Title',
            content='',
            author='Test Author'
        )

    def test_document_update_content(self, document_entity):
        """Test updating document content."""
        new_content = "Updated content for testing."
        original_updated_at = document_entity.updated_at

        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.001)

        document_entity.update_content(new_content)

        assert document_entity.content == new_content
        assert document_entity.updated_at > original_updated_at
        assert document_entity.word_count == len(new_content.split())

    def test_document_update_metadata(self, document_entity):
        """Test updating document metadata."""
        new_metadata = {'language': 'es', 'word_count': 100}
        original_updated_at = document_entity.updated_at

        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.001)

        document_entity.update_metadata(new_metadata)

        assert document_entity.metadata == new_metadata
        assert document_entity.updated_at > original_updated_at

    def test_document_add_tag(self, document_entity):
        """Test adding a tag to document."""
        new_tag = 'new-tag'
        original_updated_at = document_entity.updated_at

        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.001)

        document_entity.add_tag(new_tag)

        assert new_tag in document_entity.tags
        assert document_entity.updated_at > original_updated_at

    def test_document_add_duplicate_tag(self, document_entity):
        """Test adding a duplicate tag to document."""
        existing_tag = document_entity.tags[0]
        original_tags_count = len(document_entity.tags)
        original_updated_at = document_entity.updated_at

        document_entity.add_tag(existing_tag)

        assert len(document_entity.tags) == original_tags_count
        assert document_entity.updated_at == original_updated_at  # Should not update for duplicate

    def test_document_remove_tag(self, document_entity):
        """Test removing a tag from document."""
        tag_to_remove = document_entity.tags[0]
        original_updated_at = document_entity.updated_at

        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.001)

        document_entity.remove_tag(tag_to_remove)

        assert tag_to_remove not in document_entity.tags
        assert document_entity.updated_at > original_updated_at

    def test_document_remove_nonexistent_tag(self, document_entity):
        """Test removing a nonexistent tag from document."""
        nonexistent_tag = 'nonexistent-tag'
        original_tags_count = len(document_entity.tags)
        original_updated_at = document_entity.updated_at

        document_entity.remove_tag(nonexistent_tag)

        assert len(document_entity.tags) == original_tags_count
        assert document_entity.updated_at == original_updated_at  # Should not update

    def test_document_word_count_calculation(self):
        """Test word count calculation."""
        content = "This is a test document with multiple words."
        doc = Document(
            id='doc-123',
            title='Test',
            content=content,
            author='Test Author'
        )

        expected_word_count = len(content.split())
        assert doc.word_count == expected_word_count

    def test_document_to_dict(self, document_entity):
        """Test converting document to dictionary."""
        doc_dict = document_entity.to_dict()

        assert isinstance(doc_dict, dict)
        assert 'id' in doc_dict
        assert 'title' in doc_dict
        assert 'content' in doc_dict
        assert 'author' in doc_dict
        assert 'tags' in doc_dict
        assert 'created_at' in doc_dict
        assert 'updated_at' in doc_dict

    def test_document_from_dict(self, sample_document_data):
        """Test creating document from dictionary."""
        doc = Document.from_dict(sample_document_data)

        assert isinstance(doc, Document)
        assert doc.id == sample_document_data['id']
        assert doc.title == sample_document_data['title']

    def test_document_equality(self, document_entity, sample_document_data):
        """Test document equality comparison."""
        doc2 = Document(**sample_document_data)

        assert document_entity == doc2
        assert document_entity.id == doc2.id

    def test_document_hash(self, document_entity):
        """Test document hash for use in sets/dicts."""
        doc_hash = hash(document_entity)

        assert isinstance(doc_hash, int)
        assert doc_hash == hash(document_entity.id)

    def test_document_repr(self, document_entity):
        """Test document string representation."""
        repr_str = repr(document_entity)

        assert 'Document' in repr_str
        assert document_entity.id in repr_str
        assert document_entity.title in repr_str

    def test_document_validation_title_too_long(self):
        """Test validation for title that is too long."""
        long_title = 'A' * 201  # Assuming max length is 200
        assert_validation_error(
            Document,
            id='doc-123',
            title=long_title,
            content='Test content',
            author='Test Author'
        )

    def test_document_validation_invalid_tags(self):
        """Test validation for invalid tags."""
        # Non-string tags
        assert_validation_error(
            Document,
            id='doc-123',
            title='Test Title',
            content='Test content',
            author='Test Author',
            tags=[123, 456]  # Should be strings
        )

    def test_document_validation_empty_tags_list(self):
        """Test validation for empty tags list."""
        # This should be allowed
        doc = Document(
            id='doc-123',
            title='Test Title',
            content='Test content',
            author='Test Author',
            tags=[]
        )
        assert doc.tags == []

    def test_document_timestamp_creation(self):
        """Test that timestamps are created correctly."""
        before_creation = datetime.now(timezone.utc)

        doc = Document(
            id='doc-123',
            title='Test Title',
            content='Test content',
            author='Test Author'
        )

        after_creation = datetime.now(timezone.utc)

        assert before_creation <= doc.created_at <= after_creation
        assert before_creation <= doc.updated_at <= after_creation
        assert doc.created_at == doc.updated_at  # Should be equal at creation

    def test_document_update_preserves_creation_time(self, document_entity):
        """Test that updating preserves creation time."""
        original_created_at = document_entity.created_at
        original_updated_at = document_entity.updated_at

        # Wait a bit
        import time
        time.sleep(0.001)

        # Update something
        document_entity.add_tag('new-tag')

        assert document_entity.created_at == original_created_at
        assert document_entity.updated_at > original_updated_at
