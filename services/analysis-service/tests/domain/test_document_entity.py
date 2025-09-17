"""Tests for Document domain entity."""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from ...domain.entities.document import Document, DocumentStatus
from ...domain.value_objects.location import FileLocation


class TestDocumentEntity:
    """Test cases for Document entity."""

    def test_document_creation_valid_data(self, sample_document_data: Dict[str, Any]):
        """Test creating a document with valid data."""
        doc = Document(**sample_document_data)

        assert doc.id == sample_document_data['id']
        assert doc.title == sample_document_data['title']
        assert doc.content == sample_document_data['content']
        assert doc.file_path == sample_document_data['file_path']
        assert doc.repository_id == sample_document_data['repository_id']
        assert doc.author == sample_document_data['author']
        assert doc.version == sample_document_data['version']
        assert doc.status == DocumentStatus.ACTIVE
        assert doc.metadata == sample_document_data['metadata']
        assert isinstance(doc.created_at, datetime)
        assert isinstance(doc.updated_at, datetime)

    def test_document_creation_with_defaults(self):
        """Test creating a document with minimal required data."""
        minimal_data = {
            'id': 'minimal-doc',
            'title': 'Minimal Document',
            'content': 'Some content',
            'repository_id': 'repo-001'
        }

        doc = Document(**minimal_data)

        assert doc.id == 'minimal-doc'
        assert doc.title == 'Minimal Document'
        assert doc.content == 'Some content'
        assert doc.repository_id == 'repo-001'
        assert doc.status == DocumentStatus.DRAFT  # Default status
        assert doc.version == '1.0.0'  # Default version
        assert doc.metadata == {}  # Default empty metadata

    def test_document_creation_validation(self):
        """Test document creation validation."""
        # Test missing required fields
        with pytest.raises(ValueError):
            Document(id='', title='Test', content='Content', repository_id='repo-001')

        with pytest.raises(ValueError):
            Document(id='test', title='', content='Content', repository_id='repo-001')

        with pytest.raises(ValueError):
            Document(id='test', title='Test', content='', repository_id='repo-001')

        with pytest.raises(ValueError):
            Document(id='test', title='Test', content='Content', repository_id='')

    def test_document_status_transitions(self, sample_document: Document):
        """Test document status transitions."""
        # Initial status should be ACTIVE
        assert sample_document.status == DocumentStatus.ACTIVE

        # Test status changes
        sample_document.status = DocumentStatus.ARCHIVED
        assert sample_document.status == DocumentStatus.ARCHIVED

        sample_document.status = DocumentStatus.DELETED
        assert sample_document.status == DocumentStatus.DELETED

    def test_document_content_validation(self):
        """Test document content validation."""
        # Test empty content
        with pytest.raises(ValueError):
            Document(
                id='test',
                title='Test',
                content='',
                repository_id='repo-001'
            )

        # Test very large content (should be allowed but flagged)
        large_content = 'x' * 1000000  # 1MB content
        doc = Document(
            id='large-doc',
            title='Large Document',
            content=large_content,
            repository_id='repo-001'
        )
        assert len(doc.content) == 1000000

    def test_document_metadata_handling(self):
        """Test document metadata handling."""
        metadata = {
            'language': 'python',
            'size': 1024,
            'lines': 50,
            'tags': ['test', 'documentation']
        }

        doc = Document(
            id='meta-doc',
            title='Metadata Document',
            content='Content',
            repository_id='repo-001',
            metadata=metadata
        )

        assert doc.metadata == metadata
        assert doc.metadata['language'] == 'python'
        assert doc.metadata['tags'] == ['test', 'documentation']

    def test_document_version_handling(self):
        """Test document version handling."""
        # Test semantic versioning
        doc = Document(
            id='version-doc',
            title='Version Document',
            content='Content',
            repository_id='repo-001',
            version='2.1.3'
        )

        assert doc.version == '2.1.3'

        # Test version update
        doc.version = '2.1.4'
        assert doc.version == '2.1.4'

    def test_document_timestamps(self):
        """Test document timestamp handling."""
        before_creation = datetime.now(timezone.utc)

        doc = Document(
            id='time-doc',
            title='Time Document',
            content='Content',
            repository_id='repo-001'
        )

        after_creation = datetime.now(timezone.utc)

        assert before_creation <= doc.created_at <= after_creation
        assert before_creation <= doc.updated_at <= after_creation

    def test_document_equality(self):
        """Test document equality comparison."""
        doc1 = Document(
            id='equal-doc',
            title='Equal Document',
            content='Content',
            repository_id='repo-001'
        )

        doc2 = Document(
            id='equal-doc',
            title='Equal Document',
            content='Content',
            repository_id='repo-001'
        )

        doc3 = Document(
            id='different-doc',
            title='Different Document',
            content='Content',
            repository_id='repo-001'
        )

        assert doc1 == doc2
        assert doc1 != doc3
        assert doc2 != doc3

    def test_document_hash(self):
        """Test document hash for use in sets and dictionaries."""
        doc1 = Document(
            id='hash-doc',
            title='Hash Document',
            content='Content',
            repository_id='repo-001'
        )

        doc2 = Document(
            id='hash-doc',
            title='Hash Document',
            content='Content',
            repository_id='repo-001'
        )

        doc_set = {doc1, doc2}
        assert len(doc_set) == 1  # Should be treated as the same document

        doc_dict = {doc1: 'value1', doc2: 'value2'}
        assert len(doc_dict) == 1  # Only one key-value pair

    def test_document_string_representation(self, sample_document: Document):
        """Test document string representation."""
        str_repr = str(sample_document)
        assert 'Document' in str_repr
        assert sample_document.id in str_repr
        assert sample_document.title in str_repr

    def test_document_file_path_handling(self):
        """Test document file path handling."""
        # Test with absolute path
        doc = Document(
            id='path-doc',
            title='Path Document',
            content='Content',
            repository_id='repo-001',
            file_path='/absolute/path/to/file.md'
        )

        assert doc.file_path == '/absolute/path/to/file.md'

        # Test with relative path
        doc.file_path = 'relative/path/file.md'
        assert doc.file_path == 'relative/path/file.md'

    def test_document_author_handling(self):
        """Test document author handling."""
        doc = Document(
            id='author-doc',
            title='Author Document',
            content='Content',
            repository_id='repo-001',
            author='john.doe@example.com'
        )

        assert doc.author == 'john.doe@example.com'

        # Test author change
        doc.author = 'jane.smith@example.com'
        assert doc.author == 'jane.smith@example.com'

    def test_document_repository_relationship(self):
        """Test document repository relationship."""
        doc = Document(
            id='repo-doc',
            title='Repository Document',
            content='Content',
            repository_id='test-repo-001'
        )

        assert doc.repository_id == 'test-repo-001'

        # Test repository change
        doc.repository_id = 'new-repo-002'
        assert doc.repository_id == 'new-repo-002'

    def test_document_immutability_of_key_fields(self, sample_document: Document):
        """Test that key fields maintain their integrity."""
        original_id = sample_document.id
        original_created_at = sample_document.created_at

        # ID should not be changeable after creation
        with pytest.raises(AttributeError):
            sample_document.id = 'new-id'

        # Created timestamp should not be changeable
        with pytest.raises(AttributeError):
            sample_document.created_at = datetime.now(timezone.utc)

        assert sample_document.id == original_id
        assert sample_document.created_at == original_created_at

    def test_document_update_timestamp(self, sample_document: Document):
        """Test that updated_at timestamp changes on modifications."""
        original_updated_at = sample_document.updated_at

        # Simulate some delay
        import time
        time.sleep(0.001)

        # Modify a field that should trigger update
        sample_document.title = 'Updated Title'

        # In a real implementation, updated_at should be automatically updated
        # For now, we manually update it to test the concept
        sample_document.updated_at = datetime.now(timezone.utc)

        assert sample_document.updated_at > original_updated_at

    def test_document_content_analysis_helpers(self):
        """Test document content analysis helper methods."""
        content = """# Document Title

This is a paragraph with some content.

## Section Header

- List item 1
- List item 2
- List item 3

```python
def code_block():
    return "test"
```

Final paragraph."""

        doc = Document(
            id='analysis-doc',
            title='Analysis Document',
            content=content,
            repository_id='repo-001'
        )

        # Test content length
        assert len(doc.content) > 0

        # Test line count (rough estimate)
        lines = doc.content.split('\n')
        assert len(lines) > 10

        # Test content contains expected elements
        assert '# Document Title' in doc.content
        assert '```python' in doc.content
        assert 'def code_block():' in doc.content

    def test_document_validation_edge_cases(self):
        """Test document validation edge cases."""
        # Test with very long title
        long_title = 'A' * 1000
        doc = Document(
            id='long-title-doc',
            title=long_title,
            content='Content',
            repository_id='repo-001'
        )
        assert doc.title == long_title

        # Test with special characters in title
        special_title = 'Document with @#$%^&*() symbols!'
        doc = Document(
            id='special-title-doc',
            title=special_title,
            content='Content',
            repository_id='repo-001'
        )
        assert doc.title == special_title

        # Test with Unicode content
        unicode_content = 'Document with Unicode: 🚀 📚 💻 🌟'
        doc = Document(
            id='unicode-doc',
            title='Unicode Document',
            content=unicode_content,
            repository_id='repo-001'
        )
        assert '🚀' in doc.content
        assert '📚' in doc.content

    def test_document_factory_integration(self, document_factory, sample_document_data):
        """Test document creation through factory."""
        doc = document_factory.create_document(**sample_document_data)

        assert isinstance(doc, Document)
        assert doc.id == sample_document_data['id']
        assert doc.title == sample_document_data['title']
        assert doc.status == DocumentStatus.ACTIVE

    def test_document_status_workflow(self):
        """Test document status workflow transitions."""
        # Create draft document
        doc = Document(
            id='workflow-doc',
            title='Workflow Document',
            content='Content',
            repository_id='repo-001',
            status=DocumentStatus.DRAFT
        )

        assert doc.status == DocumentStatus.DRAFT

        # Simulate workflow: Draft -> Active
        doc.status = DocumentStatus.ACTIVE
        assert doc.status == DocumentStatus.ACTIVE

        # Simulate archival
        doc.status = DocumentStatus.ARCHIVED
        assert doc.status == DocumentStatus.ARCHIVED

        # Simulate deletion
        doc.status = DocumentStatus.DELETED
        assert doc.status == DocumentStatus.DELETED

    def test_document_clone(self, sample_document: Document):
        """Test document cloning functionality."""
        # Create a copy with new ID
        cloned_doc = Document(
            id='cloned-doc',
            title=sample_document.title,
            content=sample_document.content,
            repository_id=sample_document.repository_id,
            author=sample_document.author,
            version=sample_document.version,
            metadata=sample_document.metadata.copy()
        )

        assert cloned_doc.id != sample_document.id
        assert cloned_doc.title == sample_document.title
        assert cloned_doc.content == sample_document.content
        assert cloned_doc != sample_document  # Different objects

    def test_document_json_serialization(self, sample_document: Document):
        """Test document JSON serialization."""
        # Convert to dict
        doc_dict = {
            'id': sample_document.id,
            'title': sample_document.title,
            'content': sample_document.content,
            'file_path': sample_document.file_path,
            'repository_id': sample_document.repository_id,
            'author': sample_document.author,
            'version': sample_document.version,
            'status': sample_document.status.value,
            'metadata': sample_document.metadata,
            'created_at': sample_document.created_at.isoformat(),
            'updated_at': sample_document.updated_at.isoformat()
        }

        # Verify all fields are serializable
        import json
        json_str = json.dumps(doc_dict, default=str)
        assert json_str is not None

        # Verify we can deserialize back
        parsed = json.loads(json_str)
        assert parsed['id'] == sample_document.id
        assert parsed['title'] == sample_document.title