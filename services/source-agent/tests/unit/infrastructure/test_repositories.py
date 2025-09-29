"""Unit tests for source-agent infrastructure repositories."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone

from services.source-agent.infrastructure.repositories.document_repository import DocumentRepository


class TestDocumentRepository:
    """Test cases for DocumentRepository."""

    @pytest.fixture
    def repository(self):
        """Create DocumentRepository instance for testing."""
        return DocumentRepository()

    @pytest.mark.asyncio
    async def test_save_and_retrieve_document(self, repository):
        """Test saving and retrieving a document."""
        from services.source-agent.domain.entities import Document

        doc = Document(
            source_type="github",
            source_id="test/repo",
            title="Test Document",
            content="Test content"
        )

        # Save document
        await repository.save(doc)

        # Retrieve by ID
        retrieved = await repository.find_by_id(doc.id)
        assert retrieved is not None
        assert retrieved.id == doc.id
        assert retrieved.title == "Test Document"

    @pytest.mark.asyncio
    async def test_find_documents_by_source(self, repository):
        """Test finding documents by source."""
        from services.source-agent.domain.entities import Document

        docs = [
            Document(source_type="github", source_id="org/repo1", title="Doc 1", content="Content 1"),
            Document(source_type="github", source_id="org/repo1", title="Doc 2", content="Content 2"),
            Document(source_type="jira", source_id="PROJ", title="Doc 3", content="Content 3")
        ]

        for doc in docs:
            await repository.save(doc)

        # Find by GitHub source
        github_docs = await repository.find_by_source("github", "org/repo1")
        assert len(github_docs) == 2
        assert all(doc.source_type == "github" for doc in github_docs)

        # Find by Jira source
        jira_docs = await repository.find_by_source("jira", "PROJ")
        assert len(jira_docs) == 1
        assert jira_docs[0].source_type == "jira"

    @pytest.mark.asyncio
    async def test_find_documents_by_tags(self, repository):
        """Test finding documents by tags."""
        from services.source-agent.domain.entities import Document

        docs = [
            Document(source_type="github", source_id="test", title="Doc 1", content="Content 1", tags=["api", "docs"]),
            Document(source_type="github", source_id="test", title="Doc 2", content="Content 2", tags=["tutorial"]),
            Document(source_type="github", source_id="test", title="Doc 3", content="Content 3", tags=["api", "guide"])
        ]

        for doc in docs:
            await repository.save(doc)

        # Find by single tag
        api_docs = await repository.find_by_tags(["api"])
        assert len(api_docs) == 2

        # Find by multiple tags (OR logic)
        tutorial_or_guide_docs = await repository.find_by_tags(["tutorial", "guide"])
        assert len(tutorial_or_guide_docs) == 2

    @pytest.mark.asyncio
    async def test_update_document(self, repository):
        """Test updating an existing document."""
        from services.source-agent.domain.entities import Document

        doc = Document(
            source_type="github",
            source_id="test/repo",
            title="Original Title",
            content="Original content"
        )

        await repository.save(doc)

        # Update document
        doc.title = "Updated Title"
        doc.content = "Updated content"
        await repository.update(doc)

        # Verify update
        updated = await repository.find_by_id(doc.id)
        assert updated.title == "Updated Title"
        assert updated.content == "Updated content"

    @pytest.mark.asyncio
    async def test_delete_document(self, repository):
        """Test deleting a document."""
        from services.source-agent.domain.entities import Document

        doc = Document(
            source_type="github",
            source_id="test/repo",
            title="Test Document",
            content="Test content"
        )

        await repository.save(doc)

        # Verify exists
        assert await repository.find_by_id(doc.id) is not None

        # Delete
        deleted = await repository.delete(doc.id)
        assert deleted is True

        # Verify no longer exists
        assert await repository.find_by_id(doc.id) is None

    @pytest.mark.asyncio
    async def test_get_recent_documents(self, repository):
        """Test retrieving recent documents."""
        from services.source-agent.domain.entities import Document
        from datetime import timedelta

        # Create documents with different timestamps
        base_time = datetime.now(timezone.utc)
        docs = []

        for i in range(5):
            doc = Document(
                source_type="github",
                source_id=f"test/repo{i}",
                title=f"Document {i}",
                content=f"Content {i}"
            )
            # Simulate different creation times
            doc.fetched_at = base_time - timedelta(minutes=i*10)
            docs.append(doc)
            await repository.save(doc)

        # Get recent documents
        recent_docs = await repository.get_recent(limit=3)
        assert len(recent_docs) == 3

        # Should be ordered by recency (most recent first)
        assert recent_docs[0].fetched_at >= recent_docs[1].fetched_at

    @pytest.mark.asyncio
    async def test_search_documents(self, repository):
        """Test searching documents by content and filters."""
        from services.source-agent.domain.entities import Document

        docs = [
            Document(source_type="github", source_id="test", title="API Guide", content="This guide covers API usage"),
            Document(source_type="github", source_id="test", title="Database Setup", content="Setting up the database"),
            Document(source_type="jira", source_id="PROJ", title="Bug Report", content="API authentication bug")
        ]

        for doc in docs:
            await repository.save(doc)

        # Search by content
        api_results = await repository.search("API")
        assert len(api_results) >= 2  # API Guide and Bug Report

        # Search with filters
        github_results = await repository.search("setup", {"source_type": "github"})
        assert len(github_results) == 1
        assert github_results[0].title == "Database Setup"

    def test_repository_initialization(self, repository):
        """Test repository initialization."""
        assert repository is not None
        assert hasattr(repository, 'save')
        assert hasattr(repository, 'find_by_id')
        assert hasattr(repository, 'find_by_source')
        assert hasattr(repository, 'find_by_tags')
        assert hasattr(repository, 'update')
        assert hasattr(repository, 'delete')
        assert hasattr(repository, 'search')
        assert hasattr(repository, 'get_recent')

    @pytest.mark.asyncio
    async def test_bulk_operations(self, repository):
        """Test bulk save and retrieval operations."""
        from services.source-agent.domain.entities import Document

        # Create multiple documents
        docs = []
        for i in range(10):
            doc = Document(
                source_type="github",
                source_id=f"bulk/repo{i}",
                title=f"Bulk Document {i}",
                content=f"Bulk content {i}"
            )
            docs.append(doc)

        # Bulk save (if supported)
        for doc in docs:
            await repository.save(doc)

        # Bulk retrieval by source
        for i in range(10):
            retrieved = await repository.find_by_source("github", f"bulk/repo{i}")
            assert len(retrieved) == 1
            assert retrieved[0].title == f"Bulk Document {i}"

    @pytest.mark.asyncio
    async def test_error_handling(self, repository):
        """Test error handling in repository operations."""
        # Test finding non-existent document
        result = await repository.find_by_id("non-existent-id")
        assert result is None

        # Test deleting non-existent document
        deleted = await repository.delete("non-existent-id")
        assert deleted is False

        # Test searching with no matches
        results = await repository.search("nonexistentterm")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_repository_metrics(self, repository):
        """Test repository performance metrics."""
        # Test that repository exposes metrics
        assert hasattr(repository, 'get_operation_counts') or hasattr(repository, 'get_stats')

        # Repository should track basic metrics
        metrics = getattr(repository, 'get_stats', lambda: {})()
        assert isinstance(metrics, dict)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repository):
        """Test concurrent repository operations."""
        import asyncio
        from services.source-agent.domain.entities import Document

        async def create_and_save_doc(index):
            doc = Document(
                source_type="github",
                source_id=f"concurrent/repo{index}",
                title=f"Concurrent Document {index}",
                content=f"Concurrent content {index}"
            )
            await repository.save(doc)
            return doc.id

        # Create multiple concurrent operations
        tasks = [create_and_save_doc(i) for i in range(5)]
        doc_ids = await asyncio.gather(*tasks)

        # Verify all documents were created
        assert len(doc_ids) == 5
        assert len(set(doc_ids)) == 5  # All IDs should be unique

        # Verify all can be retrieved
        for doc_id in doc_ids:
            retrieved = await repository.find_by_id(doc_id)
            assert retrieved is not None
