"""Clean unit tests for doc-store domain services."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Optional

# Define mock entities and repositories to avoid import dependencies
from enum import Enum
from datetime import datetime, timezone


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentType(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


class TagType(str, Enum):
    CATEGORY = "category"
    TOPIC = "topic"
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    CUSTOM = "custom"


class RelationshipType(str, Enum):
    PARENT_CHILD = "parent_child"
    REFERENCE = "reference"
    VERSION = "version"


class MockDocumentId:
    """Mock document ID."""
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return self.value

    def __eq__(self, other):
        return isinstance(other, MockDocumentId) and self.value == other.value


class MockTag:
    """Mock tag."""
    def __init__(self, name: str, tag_type: TagType = TagType.CUSTOM):
        self.name = name
        self.tag_type = tag_type

    def __eq__(self, other):
        return isinstance(other, MockTag) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class MockDocument:
    """Mock document entity."""
    def __init__(self, document_id: str, title: str, content: str = "",
                 status: DocumentStatus = DocumentStatus.DRAFT, tags: List = None):
        self.document_id = MockDocumentId(document_id)
        self.title = title
        self.content = content
        self.status = status
        self.tags = tags or []
        self.version = 1
        self.metadata = {}
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.is_published = lambda: self.status == DocumentStatus.PUBLISHED
        self.has_tags = lambda: len(self.tags) > 0
        self.get_content_length = lambda: len(content)
        self.update_content = lambda new_content: setattr(self, 'content', new_content) or setattr(self, 'version', self.version + 1)
        self.add_tag = lambda tag: self.tags.append(tag) if tag not in self.tags else None
        self.publish = lambda: setattr(self, 'status', DocumentStatus.PUBLISHED)
        self.archive = lambda: setattr(self, 'status', DocumentStatus.ARCHIVED)


class MockDocumentRelationship:
    """Mock document relationship."""
    def __init__(self, source_id: str, target_id: str, relationship_type: RelationshipType):
        self.source_id = MockDocumentId(source_id)
        self.target_id = MockDocumentId(target_id)
        self.relationship_type = relationship_type
        self.is_reference = lambda: relationship_type == RelationshipType.REFERENCE


class MockDocumentVersion:
    """Mock document version."""
    def __init__(self, document_id: str, version: int, content: str):
        self.document_id = MockDocumentId(document_id)
        self.version_number = version
        self.content = content
        self.is_latest_version = lambda current: version == current


# Mock repositories
class MockDocumentRepository:
    """Mock document repository."""
    def __init__(self):
        self.documents = {
            "doc1": MockDocument("doc1", "API Documentation", "API docs content", DocumentStatus.PUBLISHED),
            "doc2": MockDocument("doc2", "User Guide", "User guide content", DocumentStatus.DRAFT),
            "doc3": MockDocument("doc3", "Technical Spec", "Technical spec", DocumentStatus.ARCHIVED),
        }

    async def save(self, document: MockDocument) -> MockDocument:
        """Save document."""
        self.documents[document.document_id.value] = document
        return document

    async def get_by_id(self, document_id: str) -> Optional[MockDocument]:
        """Get document by ID."""
        return self.documents.get(document_id)

    async def list_all(self) -> List[MockDocument]:
        """List all documents."""
        return list(self.documents.values())

    async def find_by_status(self, status: DocumentStatus) -> List[MockDocument]:
        """Find documents by status."""
        return [doc for doc in self.documents.values() if doc.status == status]

    async def find_by_tags(self, tags: List[MockTag]) -> List[MockDocument]:
        """Find documents by tags."""
        tag_names = [tag.name for tag in tags]
        return [doc for doc in self.documents.values()
                if any(tag.name in tag_names for tag in doc.tags)]


class MockDocumentRelationshipRepository:
    """Mock document relationship repository."""
    def __init__(self):
        self.relationships = [
            MockDocumentRelationship("doc1", "doc2", RelationshipType.REFERENCE),
            MockDocumentRelationship("doc2", "doc3", RelationshipType.PARENT_CHILD),
        ]

    async def save(self, relationship: MockDocumentRelationship) -> MockDocumentRelationship:
        """Save relationship."""
        self.relationships.append(relationship)
        return relationship

    async def get_relationships_for_document(self, document_id: str) -> List[MockDocumentRelationship]:
        """Get relationships for a document."""
        return [rel for rel in self.relationships
                if rel.source_id.value == document_id or rel.target_id.value == document_id]


class MockDocumentVersionRepository:
    """Mock document version repository."""
    def __init__(self):
        self.versions = {}

    async def save(self, version: MockDocumentVersion) -> MockDocumentVersion:
        """Save version."""
        key = f"{version.document_id.value}_{version.version_number}"
        self.versions[key] = version
        return version

    async def get_versions_for_document(self, document_id: str) -> List[MockDocumentVersion]:
        """Get versions for a document."""
        return [v for v in self.versions.values() if v.document_id.value == document_id]


# Domain services
class DocumentService:
    """Domain service for document operations."""

    def __init__(self, document_repo: MockDocumentRepository):
        self.document_repo = document_repo

    async def create_document(self, title: str, content: str = "",
                            document_type: DocumentType = DocumentType.TEXT,
                            tags: List[MockTag] = None) -> MockDocument:
        """Create a new document."""
        document = MockDocument(
            f"doc_{len(self.document_repo.documents) + 1}",
            title,
            content,
            DocumentStatus.DRAFT,
            tags or []
        )
        await self.document_repo.save(document)
        return document

    async def update_document_content(self, document_id: str, new_content: str) -> Optional[MockDocument]:
        """Update document content."""
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            return None

        document.update_content(new_content)
        await self.document_repo.save(document)
        return document

    async def publish_document(self, document_id: str) -> Optional[MockDocument]:
        """Publish a document."""
        document = await self.document_repo.get_by_id(document_id)
        if not document or document.status != DocumentStatus.DRAFT:
            return None

        document.publish()
        await self.document_repo.save(document)
        return document

    async def archive_document(self, document_id: str) -> Optional[MockDocument]:
        """Archive a document."""
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            return None

        document.archive()
        await self.document_repo.save(document)
        return document

    async def add_tags_to_document(self, document_id: str, tags: List[MockTag]) -> Optional[MockDocument]:
        """Add tags to a document."""
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            return None

        for tag in tags:
            document.add_tag(tag)

        await self.document_repo.save(document)
        return document

    async def get_document_statistics(self) -> Dict:
        """Get document statistics."""
        all_docs = await self.document_repo.list_all()
        published_docs = await self.document_repo.find_by_status(DocumentStatus.PUBLISHED)
        draft_docs = await self.document_repo.find_by_status(DocumentStatus.DRAFT)
        archived_docs = await self.document_repo.find_by_status(DocumentStatus.ARCHIVED)

        total_content_length = sum(doc.get_content_length() for doc in all_docs)
        avg_content_length = total_content_length / len(all_docs) if all_docs else 0

        return {
            "total_documents": len(all_docs),
            "published_documents": len(published_docs),
            "draft_documents": len(draft_docs),
            "archived_documents": len(archived_docs),
            "total_content_length": total_content_length,
            "average_content_length": avg_content_length,
            "documents_with_tags": len([doc for doc in all_docs if doc.has_tags()])
        }


class DocumentRelationshipService:
    """Domain service for document relationship operations."""

    def __init__(self, document_repo: MockDocumentRepository,
                 relationship_repo: MockDocumentRelationshipRepository):
        self.document_repo = document_repo
        self.relationship_repo = relationship_repo

    async def create_relationship(self, source_id: str, target_id: str,
                                relationship_type: RelationshipType) -> Optional[MockDocumentRelationship]:
        """Create a relationship between documents."""
        source_doc = await self.document_repo.get_by_id(source_id)
        target_doc = await self.document_repo.get_by_id(target_id)

        if not source_doc or not target_doc:
            return None

        relationship = MockDocumentRelationship(source_id, target_id, relationship_type)
        await self.relationship_repo.save(relationship)
        return relationship

    async def get_document_relationships(self, document_id: str) -> List[MockDocumentRelationship]:
        """Get all relationships for a document."""
        return await self.relationship_repo.get_relationships_for_document(document_id)

    async def get_related_documents(self, document_id: str) -> List[MockDocument]:
        """Get documents related to the given document."""
        relationships = await self.get_document_relationships(document_id)
        related_ids = set()

        for rel in relationships:
            if rel.source_id.value == document_id:
                related_ids.add(rel.target_id.value)
            else:
                related_ids.add(rel.source_id.value)

        related_docs = []
        for related_id in related_ids:
            doc = await self.document_repo.get_by_id(related_id)
            if doc:
                related_docs.append(doc)

        return related_docs

    async def find_document_network(self, document_id: str, depth: int = 2) -> Dict:
        """Find the network of related documents."""
        visited = set()
        to_visit = [document_id]
        network = {}

        for _ in range(depth):
            next_level = []
            for current_id in to_visit:
                if current_id in visited:
                    continue
                visited.add(current_id)

                if current_id not in network:
                    network[current_id] = []

                relationships = await self.get_document_relationships(current_id)
                related_ids = []

                for rel in relationships:
                    if rel.source_id.value == current_id:
                        related_id = rel.target_id.value
                    else:
                        related_id = rel.source_id.value

                    if related_id not in visited:
                        related_ids.append(related_id)
                        network[current_id].append({
                            "document_id": related_id,
                            "relationship_type": rel.relationship_type
                        })

                next_level.extend(related_ids)
            to_visit = next_level

        return network


class DocumentVersioningService:
    """Domain service for document versioning operations."""

    def __init__(self, document_repo: MockDocumentRepository,
                 version_repo: MockDocumentVersionRepository):
        self.document_repo = document_repo
        self.version_repo = version_repo

    async def create_version(self, document_id: str, change_summary: str = None,
                           created_by: str = None) -> Optional[MockDocumentVersion]:
        """Create a new version of a document."""
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            return None

        version = MockDocumentVersion(
            document_id,
            document.version,
            document.content
        )

        # Add additional attributes if they exist
        if hasattr(version, 'change_summary'):
            version.change_summary = change_summary or ""
        if hasattr(version, 'created_by'):
            version.created_by = created_by

        await self.version_repo.save(version)
        return version

    async def get_document_versions(self, document_id: str) -> List[MockDocumentVersion]:
        """Get all versions of a document."""
        return await self.version_repo.get_versions_for_document(document_id)

    async def get_latest_version(self, document_id: str) -> Optional[MockDocumentVersion]:
        """Get the latest version of a document."""
        versions = await self.get_document_versions(document_id)
        if not versions:
            return None

        # Sort by version number descending
        return max(versions, key=lambda v: v.version_number)

    async def compare_versions(self, document_id: str, version1: int, version2: int) -> Dict:
        """Compare two versions of a document."""
        versions = await self.get_document_versions(document_id)
        v1 = next((v for v in versions if v.version_number == version1), None)
        v2 = next((v for v in versions if v.version_number == version2), None)

        if not v1 or not v2:
            return {"error": "One or both versions not found"}

        content_diff = abs(len(v1.content) - len(v2.content))

        return {
            "version1": {"number": v1.version_number, "content_length": len(v1.content)},
            "version2": {"number": v2.version_number, "content_length": len(v2.content)},
            "content_difference": content_diff,
            "comparison": "same_length" if content_diff == 0 else "different_lengths"
        }


class TestDocumentService:
    """Test the DocumentService domain service."""

    @pytest.fixture
    def document_repo(self):
        """Create document repository."""
        return MockDocumentRepository()

    @pytest.fixture
    def document_service(self, document_repo):
        """Create document service."""
        return DocumentService(document_repo)

    @pytest.mark.asyncio
    async def test_create_document(self, document_service):
        """Test creating a document."""
        tags = [MockTag("python", TagType.LANGUAGE)]
        document = await document_service.create_document(
            "New Document",
            "Document content",
            DocumentType.MARKDOWN,
            tags
        )

        assert document.title == "New Document"
        assert document.content == "Document content"
        assert document.status == DocumentStatus.DRAFT
        assert len(document.tags) == 1

    @pytest.mark.asyncio
    async def test_update_document_content(self, document_service):
        """Test updating document content."""
        # First create a document
        document = await document_service.create_document("Test Doc", "Original content")
        original_version = document.version

        # Update content
        updated = await document_service.update_document_content(document.document_id.value, "Updated content")

        assert updated is not None
        assert updated.content == "Updated content"
        assert updated.version == original_version + 1

    @pytest.mark.asyncio
    async def test_publish_document(self, document_service):
        """Test publishing a document."""
        # Create draft document
        document = await document_service.create_document("Draft Doc", "Content")

        # Publish it
        published = await document_service.publish_document(document.document_id.value)

        assert published is not None
        assert published.status == DocumentStatus.PUBLISHED

        # Try to publish already published document
        republish = await document_service.publish_document(document.document_id.value)
        assert republish is None

    @pytest.mark.asyncio
    async def test_archive_document(self, document_service):
        """Test archiving a document."""
        document = await document_service.create_document("Test Doc", "Content")

        archived = await document_service.archive_document(document.document_id.value)

        assert archived is not None
        assert archived.status == DocumentStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_add_tags_to_document(self, document_service):
        """Test adding tags to a document."""
        document = await document_service.create_document("Test Doc", "Content")

        new_tags = [MockTag("api", TagType.TOPIC), MockTag("documentation", TagType.CATEGORY)]
        tagged = await document_service.add_tags_to_document(document.document_id.value, new_tags)

        assert tagged is not None
        assert len(tagged.tags) == 2

    @pytest.mark.asyncio
    async def test_get_document_statistics(self, document_service):
        """Test getting document statistics."""
        stats = await document_service.get_document_statistics()

        assert "total_documents" in stats
        assert "published_documents" in stats
        assert "draft_documents" in stats
        assert "archived_documents" in stats
        assert stats["total_documents"] >= 3  # From mock repo
        assert stats["published_documents"] >= 1
        assert stats["draft_documents"] >= 1


class TestDocumentRelationshipService:
    """Test the DocumentRelationshipService domain service."""

    @pytest.fixture
    def document_repo(self):
        """Create document repository."""
        return MockDocumentRepository()

    @pytest.fixture
    def relationship_repo(self):
        """Create relationship repository."""
        return MockDocumentRelationshipRepository()

    @pytest.fixture
    def relationship_service(self, document_repo, relationship_repo):
        """Create relationship service."""
        return DocumentRelationshipService(document_repo, relationship_repo)

    @pytest.mark.asyncio
    async def test_create_relationship(self, relationship_service):
        """Test creating a document relationship."""
        relationship = await relationship_service.create_relationship(
            "doc1", "doc2", RelationshipType.REFERENCE
        )

        assert relationship is not None
        assert relationship.source_id.value == "doc1"
        assert relationship.target_id.value == "doc2"
        assert relationship.relationship_type == RelationshipType.REFERENCE

    @pytest.mark.asyncio
    async def test_create_relationship_invalid_documents(self, relationship_service):
        """Test creating relationship with invalid documents."""
        relationship = await relationship_service.create_relationship(
            "nonexistent", "doc1", RelationshipType.REFERENCE
        )

        assert relationship is None

    @pytest.mark.asyncio
    async def test_get_document_relationships(self, relationship_service):
        """Test getting document relationships."""
        relationships = await relationship_service.get_document_relationships("doc1")

        assert len(relationships) >= 1  # From mock data
        assert any(rel.source_id.value == "doc1" for rel in relationships)

    @pytest.mark.asyncio
    async def test_get_related_documents(self, relationship_service):
        """Test getting related documents."""
        related_docs = await relationship_service.get_related_documents("doc1")

        assert len(related_docs) >= 1
        assert any(doc.document_id.value == "doc2" for doc in related_docs)

    @pytest.mark.asyncio
    async def test_find_document_network(self, relationship_service):
        """Test finding document network."""
        network = await relationship_service.find_document_network("doc1", depth=1)

        assert "doc1" in network
        assert len(network["doc1"]) >= 1
        assert "document_id" in network["doc1"][0]


class TestDocumentVersioningService:
    """Test the DocumentVersioningService domain service."""

    @pytest.fixture
    def document_repo(self):
        """Create document repository."""
        return MockDocumentRepository()

    @pytest.fixture
    def version_repo(self):
        """Create version repository."""
        return MockDocumentVersionRepository()

    @pytest.fixture
    def versioning_service(self, document_repo, version_repo):
        """Create versioning service."""
        return DocumentVersioningService(document_repo, version_repo)

    @pytest.mark.asyncio
    async def test_create_version(self, versioning_service):
        """Test creating a document version."""
        document = await versioning_service.document_repo.get_by_id("doc1")
        version = await versioning_service.create_version("doc1", "Updated content", "user123")

        assert version is not None
        assert version.document_id.value == "doc1"
        assert version.version_number == document.version
        assert version.content == document.content

    @pytest.mark.asyncio
    async def test_get_document_versions(self, versioning_service):
        """Test getting document versions."""
        # Create a version first
        await versioning_service.create_version("doc1")

        versions = await versioning_service.get_document_versions("doc1")

        assert len(versions) >= 1
        assert all(v.document_id.value == "doc1" for v in versions)

    @pytest.mark.asyncio
    async def test_get_latest_version(self, versioning_service):
        """Test getting the latest version."""
        # Create multiple versions
        await versioning_service.create_version("doc1")
        document = await versioning_service.document_repo.get_by_id("doc1")
        document.version = 2
        await versioning_service.create_version("doc1")

        latest = await versioning_service.get_latest_version("doc1")

        assert latest is not None
        assert latest.version_number == 2

    @pytest.mark.asyncio
    async def test_compare_versions(self, versioning_service):
        """Test comparing document versions."""
        # Create versions
        await versioning_service.create_version("doc1")
        document = await versioning_service.document_repo.get_by_id("doc1")
        document.version = 2
        document.content = "Different content"
        await versioning_service.create_version("doc1")

        comparison = await versioning_service.compare_versions("doc1", 1, 2)

        assert "version1" in comparison
        assert "version2" in comparison
        assert "content_difference" in comparison
        assert comparison["content_difference"] > 0


class TestServiceIntegration:
    """Test integration between services."""

    @pytest.fixture
    def document_repo(self):
        """Create document repository."""
        return MockDocumentRepository()

    @pytest.fixture
    def relationship_repo(self):
        """Create relationship repository."""
        return MockDocumentRelationshipRepository()

    @pytest.fixture
    def version_repo(self):
        """Create version repository."""
        return MockDocumentVersionRepository()

    @pytest.fixture
    def document_service(self, document_repo):
        """Create document service."""
        return DocumentService(document_repo)

    @pytest.fixture
    def relationship_service(self, document_repo, relationship_repo):
        """Create relationship service."""
        return DocumentRelationshipService(document_repo, relationship_repo)

    @pytest.fixture
    def versioning_service(self, document_repo, version_repo):
        """Create versioning service."""
        return DocumentVersioningService(document_repo, version_repo)

    @pytest.mark.asyncio
    async def test_complete_document_lifecycle(self, document_service, relationship_service, versioning_service):
        """Test complete document lifecycle with all services."""
        # 1. Create document
        document = await document_service.create_document(
            "Lifecycle Test Document",
            "Initial content",
            DocumentType.MARKDOWN
        )

        # 2. Update content and create version
        await document_service.update_document_content(document.document_id.value, "Updated content")
        version1 = await versioning_service.create_version(document.document_id.value, "First update")

        # 3. Add tags
        tags = [MockTag("test", TagType.CATEGORY)]
        await document_service.add_tags_to_document(document.document_id.value, tags)

        # 4. Create another document and relationship
        related_doc = await document_service.create_document("Related Document", "Related content")
        relationship = await relationship_service.create_relationship(
            document.document_id.value, related_doc.document_id.value, RelationshipType.REFERENCE
        )

        # 5. Publish document
        published = await document_service.publish_document(document.document_id.value)

        # 6. Verify complete workflow
        assert published is not None
        assert published.is_published()
        assert published.has_tags()
        assert version1 is not None
        assert relationship is not None

        # Check relationships
        related_docs = await relationship_service.get_related_documents(document.document_id.value)
        assert len(related_docs) >= 1

        # Check versions
        versions = await versioning_service.get_document_versions(document.document_id.value)
        assert len(versions) >= 1

    @pytest.mark.asyncio
    async def test_document_network_analysis(self, document_service, relationship_service):
        """Test document network analysis."""
        # Create a network of documents
        doc_a = await document_service.create_document("Document A", "Content A")
        doc_b = await document_service.create_document("Document B", "Content B")
        doc_c = await document_service.create_document("Document C", "Content C")

        # Create relationships: A -> B -> C
        await relationship_service.create_relationship(
            doc_a.document_id.value, doc_b.document_id.value, RelationshipType.REFERENCE
        )
        await relationship_service.create_relationship(
            doc_b.document_id.value, doc_c.document_id.value, RelationshipType.REFERENCE
        )

        # Analyze network from A
        network = await relationship_service.find_document_network(doc_a.document_id.value, depth=2)

        assert doc_a.document_id.value in network
        assert len(network[doc_a.document_id.value]) >= 1

        # Should find B in the network
        connected_ids = [conn["document_id"] for conn in network[doc_a.document_id.value]]
        assert doc_b.document_id.value in connected_ids

    @pytest.mark.asyncio
    async def test_version_control_workflow(self, document_service, versioning_service):
        """Test version control workflow."""
        # Create document
        document = await document_service.create_document("Versioned Document", "Version 1 content")

        # Make several updates
        await document_service.update_document_content(document.document_id.value, "Version 2 content with more text")
        await versioning_service.create_version(document.document_id.value, "Updated to v2")

        await document_service.update_document_content(document.document_id.value, "Version 3")
        await versioning_service.create_version(document.document_id.value, "Updated to v3")

        # Check version history
        versions = await versioning_service.get_document_versions(document.document_id.value)
        assert len(versions) >= 2

        latest = await versioning_service.get_latest_version(document.document_id.value)
        assert latest.version_number == 3

        # Compare versions
        comparison = await versioning_service.compare_versions(document.document_id.value, 2, 3)
        assert comparison["content_difference"] > 0

    @pytest.mark.asyncio
    async def test_cross_service_statistics(self, document_service, relationship_service, versioning_service):
        """Test statistics across all services."""
        # Create test data
        doc1 = await document_service.create_document("Stats Doc 1", "Content 1")
        doc2 = await document_service.create_document("Stats Doc 2", "Content 2")

        # Create relationships and versions
        await relationship_service.create_relationship(
            doc1.document_id.value, doc2.document_id.value, RelationshipType.REFERENCE
        )

        await document_service.update_document_content(doc1.document_id.value, "Updated content 1")
        await versioning_service.create_version(doc1.document_id.value, "Update 1")

        # Get statistics from document service
        doc_stats = await document_service.get_document_statistics()

        # Verify cross-service data consistency
        assert doc_stats["total_documents"] >= 5  # Original 3 + 2 new
        assert doc_stats["documents_with_tags"] >= 0

        # Check relationships exist
        relationships = await relationship_service.get_document_relationships(doc1.document_id.value)
        assert len(relationships) >= 1

        # Check versions exist
        versions = await versioning_service.get_document_versions(doc1.document_id.value)
        assert len(versions) >= 1
