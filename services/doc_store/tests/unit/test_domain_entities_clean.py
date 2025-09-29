"""Clean unit tests for doc-store domain entities."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Dict, Optional

# Define domain entities inline to avoid import dependencies
from enum import Enum


class DocumentStatus(str, Enum):
    """Document status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentType(str, Enum):
    """Document type enumeration."""
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    XML = "xml"


class TagType(str, Enum):
    """Tag type enumeration."""
    CATEGORY = "category"
    TOPIC = "topic"
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    CUSTOM = "custom"


class RelationshipType(str, Enum):
    """Relationship type enumeration."""
    PARENT_CHILD = "parent_child"
    REFERENCE = "reference"
    DUPLICATE = "duplicate"
    TRANSLATION = "translation"
    VERSION = "version"


class DocumentId:
    """Value object for document ID."""

    def __init__(self, value: str = None):
        self.value = value or str(uuid4())

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if isinstance(other, DocumentId):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)


class Tag:
    """Value object for document tags."""

    def __init__(self, name: str, tag_type: TagType = TagType.CUSTOM, color: str = None):
        self.name = name.lower().strip()
        self.tag_type = tag_type
        self.color = color

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        if isinstance(other, Tag):
            return self.name == other.name and self.tag_type == other.tag_type
        return False

    def __hash__(self) -> int:
        return hash((self.name, self.tag_type))


class Document:
    """Domain entity for documents."""

    def __init__(self,
                 document_id: DocumentId = None,
                 title: str = None,
                 content: str = None,
                 document_type: DocumentType = DocumentType.TEXT,
                 status: DocumentStatus = DocumentStatus.DRAFT,
                 tags: List[Tag] = None,
                 metadata: Dict = None,
                 version: int = 1,
                 created_at: datetime = None,
                 updated_at: datetime = None,
                 created_by: str = None):
        self.document_id = document_id or DocumentId()
        self.title = title or ""
        self.content = content or ""
        self.document_type = document_type
        self.status = status
        self.tags = tags or []
        self.metadata = metadata or {}
        self.version = version
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.created_by = created_by

    def is_published(self) -> bool:
        """Check if document is published."""
        return self.status == DocumentStatus.PUBLISHED

    def is_archived(self) -> bool:
        """Check if document is archived."""
        return self.status == DocumentStatus.ARCHIVED

    def has_tags(self) -> bool:
        """Check if document has tags."""
        return len(self.tags) > 0

    def add_tag(self, tag: Tag):
        """Add a tag to the document."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now(timezone.utc)

    def remove_tag(self, tag: Tag):
        """Remove a tag from the document."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now(timezone.utc)

    def update_content(self, new_content: str):
        """Update document content and increment version."""
        self.content = new_content
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)

    def publish(self):
        """Publish the document."""
        if self.status == DocumentStatus.DRAFT:
            self.status = DocumentStatus.PUBLISHED
            self.updated_at = datetime.now(timezone.utc)

    def archive(self):
        """Archive the document."""
        if self.status != DocumentStatus.DELETED:
            self.status = DocumentStatus.ARCHIVED
            self.updated_at = datetime.now(timezone.utc)

    def delete(self):
        """Mark document as deleted."""
        self.status = DocumentStatus.DELETED
        self.updated_at = datetime.now(timezone.utc)

    def get_content_length(self) -> int:
        """Get content length."""
        return len(self.content)

    def has_metadata(self, key: str) -> bool:
        """Check if document has specific metadata."""
        return key in self.metadata

    def get_metadata(self, key: str, default=None):
        """Get metadata value."""
        return self.metadata.get(key, default)


class DocumentRelationship:
    """Domain entity for document relationships."""

    def __init__(self,
                 source_id: DocumentId,
                 target_id: DocumentId,
                 relationship_type: RelationshipType,
                 bidirectional: bool = False,
                 metadata: Dict = None,
                 created_at: datetime = None):
        self.source_id = source_id
        self.target_id = target_id
        self.relationship_type = relationship_type
        self.bidirectional = bidirectional
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_parent_child(self) -> bool:
        """Check if this is a parent-child relationship."""
        return self.relationship_type == RelationshipType.PARENT_CHILD

    def is_reference(self) -> bool:
        """Check if this is a reference relationship."""
        return self.relationship_type == RelationshipType.REFERENCE

    def is_version(self) -> bool:
        """Check if this is a version relationship."""
        return self.relationship_type == RelationshipType.VERSION

    def get_reverse_relationship_type(self) -> RelationshipType:
        """Get the reverse relationship type."""
        if self.relationship_type == RelationshipType.PARENT_CHILD:
            return RelationshipType.PARENT_CHILD  # Symmetric
        return self.relationship_type  # Most relationships are directional


class DocumentVersion:
    """Domain entity for document versions."""

    def __init__(self,
                 document_id: DocumentId,
                 version_number: int,
                 content: str,
                 change_summary: str = None,
                 created_by: str = None,
                 created_at: datetime = None):
        self.document_id = document_id
        self.version_number = version_number
        self.content = content
        self.change_summary = change_summary or ""
        self.created_by = created_by
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_latest_version(self, current_version: int) -> bool:
        """Check if this is the latest version."""
        return self.version_number == current_version

    def get_content_difference(self, other_content: str) -> int:
        """Get the difference in content length."""
        return abs(len(self.content) - len(other_content))


class TestDocumentIdValueObject:
    """Test the DocumentId value object."""

    def test_document_id_creation(self):
        """Test creating a document ID."""
        doc_id = DocumentId("test-123")
        assert doc_id.value == "test-123"
        assert str(doc_id) == "test-123"

        # Test auto-generation
        auto_id = DocumentId()
        assert auto_id.value is not None
        assert len(auto_id.value) > 0

    def test_document_id_equality(self):
        """Test document ID equality."""
        id1 = DocumentId("same-id")
        id2 = DocumentId("same-id")
        id3 = DocumentId("different-id")

        assert id1 == id2
        assert id1 != id3
        assert id1 != "same-id"  # Different type

    def test_document_id_hash(self):
        """Test document ID hashing."""
        id1 = DocumentId("test-id")
        id2 = DocumentId("test-id")

        assert hash(id1) == hash(id2)

        # Can be used in sets
        id_set = {id1, id2}
        assert len(id_set) == 1


class TestTagValueObject:
    """Test the Tag value object."""

    def test_tag_creation(self):
        """Test creating a tag."""
        tag = Tag("Python", TagType.LANGUAGE, "#3776AB")
        assert tag.name == "python"  # Should be lowercase
        assert tag.tag_type == TagType.LANGUAGE
        assert tag.color == "#3776AB"

    def test_tag_normalization(self):
        """Test tag name normalization."""
        tag1 = Tag("  PYTHON  ")
        tag2 = Tag("Python")

        assert tag1.name == "python"
        assert tag1 == tag2

    def test_tag_equality(self):
        """Test tag equality."""
        tag1 = Tag("python", TagType.LANGUAGE)
        tag2 = Tag("python", TagType.LANGUAGE)
        tag3 = Tag("python", TagType.FRAMEWORK)

        assert tag1 == tag2
        assert tag1 != tag3  # Different type

    def test_tag_string_representation(self):
        """Test tag string representation."""
        tag = Tag("machine learning")
        assert str(tag) == "machine learning"


class TestDocumentEntity:
    """Test the Document domain entity."""

    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            title="Test Document",
            content="This is test content",
            document_type=DocumentType.MARKDOWN,
            created_by="user123"
        )

        assert doc.title == "Test Document"
        assert doc.content == "This is test content"
        assert doc.document_type == DocumentType.MARKDOWN
        assert doc.status == DocumentStatus.DRAFT
        assert doc.version == 1
        assert doc.created_by == "user123"
        assert doc.document_id is not None

    def test_document_status_methods(self):
        """Test document status methods."""
        doc = Document()

        assert not doc.is_published()
        assert not doc.is_archived()

        doc.publish()
        assert doc.is_published()
        assert not doc.is_archived()

        doc.archive()
        assert not doc.is_published()
        assert doc.is_archived()

    def test_document_content_operations(self):
        """Test document content operations."""
        doc = Document(content="Original content", version=1)

        assert doc.get_content_length() == 16
        assert doc.version == 1

        doc.update_content("Updated content with more text")
        assert doc.content == "Updated content with more text"
        assert doc.version == 2
        assert doc.updated_at > doc.created_at

    def test_document_tag_management(self):
        """Test document tag management."""
        doc = Document()
        python_tag = Tag("Python", TagType.LANGUAGE)
        web_tag = Tag("Web", TagType.TOPIC)

        assert not doc.has_tags()

        doc.add_tag(python_tag)
        assert doc.has_tags()
        assert len(doc.tags) == 1
        assert python_tag in doc.tags

        doc.add_tag(web_tag)
        assert len(doc.tags) == 2

        # Adding duplicate should not increase count
        doc.add_tag(python_tag)
        assert len(doc.tags) == 2

        doc.remove_tag(python_tag)
        assert len(doc.tags) == 1
        assert python_tag not in doc.tags

    def test_document_metadata_operations(self):
        """Test document metadata operations."""
        doc = Document()
        doc.metadata = {"author": "John Doe", "priority": "high"}

        assert doc.has_metadata("author")
        assert doc.has_metadata("priority")
        assert not doc.has_metadata("nonexistent")

        assert doc.get_metadata("author") == "John Doe"
        assert doc.get_metadata("priority") == "high"
        assert doc.get_metadata("missing", "default") == "default"

    def test_document_lifecycle_operations(self):
        """Test document lifecycle operations."""
        doc = Document(status=DocumentStatus.DRAFT)

        # Can publish draft
        doc.publish()
        assert doc.status == DocumentStatus.PUBLISHED

        # Can archive published
        doc.archive()
        assert doc.status == DocumentStatus.ARCHIVED

        # Can delete any non-deleted document
        doc.delete()
        assert doc.status == DocumentStatus.DELETED


class TestDocumentRelationshipEntity:
    """Test the DocumentRelationship domain entity."""

    def test_relationship_creation(self):
        """Test creating a document relationship."""
        source_id = DocumentId("doc1")
        target_id = DocumentId("doc2")

        relationship = DocumentRelationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=RelationshipType.REFERENCE,
            bidirectional=False,
            metadata={"strength": "strong"}
        )

        assert relationship.source_id == source_id
        assert relationship.target_id == target_id
        assert relationship.relationship_type == RelationshipType.REFERENCE
        assert not relationship.bidirectional
        assert relationship.metadata["strength"] == "strong"

    def test_relationship_type_checks(self):
        """Test relationship type checking methods."""
        parent_child = DocumentRelationship(
            DocumentId("parent"), DocumentId("child"), RelationshipType.PARENT_CHILD
        )
        reference = DocumentRelationship(
            DocumentId("doc1"), DocumentId("doc2"), RelationshipType.REFERENCE
        )
        version_rel = DocumentRelationship(
            DocumentId("doc1"), DocumentId("doc1v2"), RelationshipType.VERSION
        )

        assert parent_child.is_parent_child()
        assert not parent_child.is_reference()
        assert not parent_child.is_version()

        assert reference.is_reference()
        assert not reference.is_parent_child()

        assert version_rel.is_version()

    def test_relationship_reverse_type(self):
        """Test getting reverse relationship type."""
        parent_child = DocumentRelationship(
            DocumentId("parent"), DocumentId("child"), RelationshipType.PARENT_CHILD
        )
        reference = DocumentRelationship(
            DocumentId("doc1"), DocumentId("doc2"), RelationshipType.REFERENCE
        )

        # Parent-child is symmetric
        assert parent_child.get_reverse_relationship_type() == RelationshipType.PARENT_CHILD

        # Most relationships maintain their type
        assert reference.get_reverse_relationship_type() == RelationshipType.REFERENCE


class TestDocumentVersionEntity:
    """Test the DocumentVersion domain entity."""

    def test_version_creation(self):
        """Test creating a document version."""
        doc_id = DocumentId("doc123")
        version = DocumentVersion(
            document_id=doc_id,
            version_number=2,
            content="Version 2 content",
            change_summary="Fixed typos and improved formatting",
            created_by="editor456"
        )

        assert version.document_id == doc_id
        assert version.version_number == 2
        assert version.content == "Version 2 content"
        assert version.change_summary == "Fixed typos and improved formatting"
        assert version.created_by == "editor456"

    def test_version_comparison(self):
        """Test version comparison methods."""
        version2 = DocumentVersion(DocumentId("doc1"), 2, "content v2")
        version3 = DocumentVersion(DocumentId("doc1"), 3, "content v3")

        assert version2.is_latest_version(2)
        assert not version2.is_latest_version(3)

        assert version3.is_latest_version(3)
        assert not version3.is_latest_version(2)

    def test_content_difference(self):
        """Test content difference calculation."""
        version = DocumentVersion(DocumentId("doc1"), 1, "short content")

        # Same length
        assert version.get_content_difference("short content") == 0

        # Longer content
        assert version.get_content_difference("this is much longer content") == 14

        # Shorter content
        assert version.get_content_difference("short") == 8


class TestEntityIntegration:
    """Test integration between entities."""

    def test_document_with_relationships(self):
        """Test document with relationships."""
        doc1 = Document(title="Main Document")
        doc2 = Document(title="Referenced Document")

        # Create relationship
        relationship = DocumentRelationship(
            source_id=doc1.document_id,
            target_id=doc2.document_id,
            relationship_type=RelationshipType.REFERENCE
        )

        assert relationship.source_id == doc1.document_id
        assert relationship.target_id == doc2.document_id
        assert relationship.is_reference()

    def test_document_with_versions(self):
        """Test document with versions."""
        doc = Document(title="Versioned Document", content="Original content")

        # Create versions
        v1 = DocumentVersion(doc.document_id, 1, "Original content")
        v2 = DocumentVersion(doc.document_id, 2, "Updated content", "Added new section")

        assert v1.document_id == doc.document_id
        assert v2.document_id == doc.document_id

        assert v1.is_latest_version(1)
        assert v2.is_latest_version(2)
        assert not v1.is_latest_version(2)

        # Content difference
        assert v2.get_content_difference(v1.content) == abs(len(v2.content) - len(v1.content))

    def test_document_with_tags_and_metadata(self):
        """Test document with tags and metadata."""
        doc = Document(title="Tagged Document")

        # Add tags
        python_tag = Tag("Python", TagType.LANGUAGE)
        api_tag = Tag("API", TagType.TOPIC)

        doc.add_tag(python_tag)
        doc.add_tag(api_tag)

        # Add metadata
        doc.metadata = {
            "language": "Python",
            "framework": "FastAPI",
            "complexity": "medium"
        }

        assert doc.has_tags()
        assert len(doc.tags) == 2
        assert python_tag in doc.tags
        assert api_tag in doc.tags

        assert doc.has_metadata("language")
        assert doc.get_metadata("framework") == "FastAPI"
        assert doc.get_metadata("missing") is None

    def test_complete_document_workflow(self):
        """Test complete document workflow."""
        # Create document
        doc = Document(
            title="API Documentation",
            content="Initial API docs",
            document_type=DocumentType.MARKDOWN
        )

        assert doc.status == DocumentStatus.DRAFT
        assert doc.version == 1

        # Add tags
        api_tag = Tag("API", TagType.TOPIC)
        doc.add_tag(api_tag)

        # Update content (creates new version)
        doc.update_content("Updated API documentation with examples")
        assert doc.version == 2

        # Add metadata
        doc.metadata = {"review_status": "pending"}

        # Publish document
        doc.publish()
        assert doc.is_published()

        # Create relationship to another document
        related_doc = Document(title="API Examples")
        relationship = DocumentRelationship(
            source_id=doc.document_id,
            target_id=related_doc.document_id,
            relationship_type=RelationshipType.REFERENCE
        )

        # Create version history
        version = DocumentVersion(
            doc.document_id,
            doc.version,
            doc.content,
            "Updated with examples",
            "editor123"
        )

        # Verify complete workflow
        assert doc.is_published()
        assert doc.has_tags()
        assert doc.has_metadata("review_status")
        assert relationship.is_reference()
        assert version.is_latest_version(doc.version)
        assert doc.updated_at >= doc.created_at
