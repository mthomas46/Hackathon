"""Comprehensive tests for DocumentRepository."""
import pytest
import sqlite3
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

from services.doc_store.domain.entities import Document
from services.doc_store.domain.repository import DocumentRepository


class TestDocumentRepository:
    """Comprehensive test cases for DocumentRepository."""

    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """Create a temporary database path."""
        return str(tmp_path / "test_docs.db")

    @pytest.fixture
    def repository(self, temp_db_path):
        """Create a test repository instance."""
        repo = DocumentRepository(f"sqlite:///{temp_db_path}")
        # Database is initialized automatically by the base class
        return repo

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return Document(
            id="test-doc-123",
            content="This is test content for repository testing",
            content_hash="test_hash_123",
            correlation_id="test-correlation-456",
            metadata={"title": "Test Document", "author": "Test Author"}
        )

    def test_repository_initialization(self, repository, temp_db_path):
        """Test repository initialization creates database tables."""
        # Check that the database file was created
        import os
        assert os.path.exists(temp_db_path)

        # Check that tables were created by querying them
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            # Check if documents table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            assert cursor.fetchone() is not None

    @pytest.mark.asyncio
    async def test_create_document(self, repository, sample_document):
        """Test creating a new document."""
        # Create the document
        created_doc = await repository.save(sample_document)

        # Verify it was created and returned
        assert created_doc is not None
        assert created_doc.id == sample_document.id
        assert created_doc.content == sample_document.content
        assert created_doc.content_hash == sample_document.content_hash

        # Verify it exists in database
        retrieved = await repository.find_by_id(sample_document.id)
        assert retrieved is not None
        assert retrieved.id == sample_document.id

    @pytest.mark.asyncio
    async def test_find_by_id_existing_document(self, repository, sample_document):
        """Test retrieving an existing document by ID."""
        # First create the document
        await repository.save(sample_document)

        # Then retrieve it
        retrieved = await repository.find_by_id(sample_document.id)

        assert retrieved is not None
        assert retrieved.id == sample_document.id
        assert retrieved.content == sample_document.content
        assert retrieved.metadata == sample_document.metadata

    @pytest.mark.asyncio
    async def test_find_by_id_nonexistent_document(self, repository):
        """Test retrieving a nonexistent document returns None."""
        retrieved = await repository.find_by_id("nonexistent-id")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_update_document(self, repository, sample_document):
        """Test updating an existing document."""
        # Create initial document
        await repository.save(sample_document)

        # Update the document
        sample_document.content = "Updated content"
        sample_document.metadata["updated"] = True

        updated_doc = await repository.save(sample_document)

        # Verify update
        assert updated_doc.content == "Updated content"
        assert updated_doc.metadata["updated"] is True
        assert updated_doc.updated_at is not None

        # Verify in database
        retrieved = await repository.find_by_id(sample_document.id)
        assert retrieved.content == "Updated content"
        assert retrieved.metadata["updated"] is True

    @pytest.mark.asyncio
    async def test_update_nonexistent_document(self, repository, sample_document):
        """Test updating a nonexistent document raises EntityNotFoundError."""
        from services.shared.domain.repositories.base_repository import EntityNotFoundError

        with pytest.raises(EntityNotFoundError):
            await repository.save(sample_document)

    @pytest.mark.asyncio
    async def test_delete_document(self, repository, sample_document):
        """Test deleting an existing document."""
        # Create the document
        await repository.save(sample_document)

        # Delete it
        result = await repository.delete_by_id(sample_document.id)
        assert result is True

        # Verify it's gone
        retrieved = await repository.find_by_id(sample_document.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, repository):
        """Test deleting a nonexistent document returns False."""
        result = await repository.delete_by_id("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_find_all_documents(self, repository):
        """Test retrieving all documents."""
        # Create multiple documents
        docs = []
        for i in range(3):
            doc = Document(
                id=f"doc-{i}",
                content=f"Content {i}",
                content_hash=f"hash-{i}"
            )
            docs.append(doc)
            await repository.save(doc)

        # Get all documents
        all_docs = await repository.find_all()

        assert len(all_docs) == 3
        doc_ids = {doc.id for doc in all_docs}
        expected_ids = {f"doc-{i}" for i in range(3)}
        assert doc_ids == expected_ids

    @pytest.mark.asyncio
    async def test_find_all_documents_empty_repository(self, repository):
        """Test getting all documents from empty repository."""
        all_docs = await repository.find_all()
        assert all_docs == []

    @pytest.mark.asyncio
    async def test_find_by_criteria(self, repository):
        """Test finding documents by custom criteria."""
        # Create documents with different statuses
        draft_doc = Document(
            id="draft-doc",
            content="Draft content",
            content_hash="draft-hash",
            status=DocumentStatus.DRAFT
        )

        published_doc = Document(
            id="published-doc",
            content="Published content",
            content_hash="published-hash",
            status=DocumentStatus.PUBLISHED
        )

        await repository.create(draft_doc)
        await repository.create(published_doc)

        # Find documents by content
        draft_docs = await repository.search_by_content("Draft")
        published_docs = await repository.search_by_content("Published")

        assert len(draft_docs) == 1
        assert draft_docs[0].id == "draft-doc"
        assert "Draft" in draft_docs[0].content

        assert len(published_docs) == 1
        assert published_docs[0].id == "published-doc"
        assert "Published" in published_docs[0].content

    @pytest.mark.asyncio
    async def test_find_by_correlation_id(self, repository):
        """Test finding documents by correlation ID."""
        # Create documents with correlation IDs
        doc1 = Document(
            id="doc1",
            content="Content 1",
            content_hash="hash1",
            correlation_id="corr-123"
        )

        doc2 = Document(
            id="doc2",
            content="Content 2",
            content_hash="hash2",
            correlation_id="corr-456"
        )

        doc3 = Document(
            id="doc3",
            content="Content 3",
            content_hash="hash3",
            correlation_id="corr-123"  # Same correlation ID as doc1
        )

        await repository.create(doc1)
        await repository.create(doc2)
        await repository.create(doc3)

        # Find by correlation ID
        correlated_docs = await repository.find_by_correlation_id("corr-123")

        assert len(correlated_docs) == 2
        doc_ids = {doc.id for doc in correlated_docs}
        assert doc_ids == {"doc1", "doc3"}

    @pytest.mark.asyncio
    async def test_exists_check(self, repository, sample_document):
        """Test checking if document exists by ID."""
        # Document doesn't exist initially
        assert not await repository.exists(sample_document.id)

        # Create document
        await repository.save(sample_document)

        # Now it should exist
        assert await repository.exists(sample_document.id)

        # Delete document
        await repository.delete_by_id(sample_document.id)

        # Should not exist anymore
        assert not await repository.exists(sample_document.id)

    @pytest.mark.asyncio
    async def test_count_documents(self, repository):
        """Test counting total documents."""
        # Initially empty
        assert await repository.count() == 0

        # Create some documents
        for i in range(5):
            doc = Document(
                id=f"count-doc-{i}",
                content=f"Content {i}",
                content_hash=f"hash-{i}"
            )
            await repository.save(doc)

        # Should have 5 documents
        assert await repository.count() == 5

    @pytest.mark.asyncio
    async def test_bulk_create_documents(self, repository):
        """Test bulk creating multiple documents."""
        docs = []
        for i in range(10):
            doc = Document(
                id=f"bulk-doc-{i}",
                content=f"Bulk content {i}",
                content_hash=f"bulk-hash-{i}"
            )
            docs.append(doc)

        # The repository doesn't have bulk operations, so we'll save them individually
        for doc in docs:
            await repository.save(doc)

        # Verify all exist in database
        all_docs = await repository.find_all()
        assert len(all_docs) == 10

    @pytest.mark.asyncio
    async def test_bulk_delete_documents(self, repository):
        """Test bulk deleting multiple documents."""
        # Create documents
        docs = []
        for i in range(5):
            doc = Document(
                id=f"delete-doc-{i}",
                content=f"Content {i}",
                content_hash=f"hash-{i}"
            )
            docs.append(doc)
            await repository.save(doc)

        # Delete individually (no bulk delete method)
        for doc in docs:
            await repository.delete_by_id(doc.id)

        # Verify all are gone
        remaining = await repository.find_all()
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, repository):
        """Test that transactions rollback on errors."""
        initial_count = await repository.count()

        try:
            async with repository.transaction():
                # Create a document
                doc1 = Document(id="tx-doc-1", content="Content 1", content_hash="hash1")
                await repository.create(doc1)

                # Create another document
                doc2 = Document(id="tx-doc-2", content="Content 2", content_hash="hash2")
                await repository.create(doc2)

                # Simulate an error
                raise ValueError("Simulated transaction error")
        except ValueError:
            pass  # Expected error

        # Transaction should have rolled back
        final_count = await repository.count()
        assert final_count == initial_count

        # Documents should not exist
        assert not await repository.exists_by_id("tx-doc-1")
        assert not await repository.exists_by_id("tx-doc-2")

    @pytest.mark.asyncio
    async def test_concurrent_access(self, repository):
        """Test repository handles concurrent access properly."""
        import asyncio

        async def create_document(i):
            doc = Document(
                id=f"concurrent-doc-{i}",
                content=f"Concurrent content {i}",
                content_hash=f"concurrent-hash-{i}"
            )
            await repository.save(doc)
            return doc

        # Create multiple documents concurrently
        tasks = [create_document(i) for i in range(20)]
        created_docs = await asyncio.gather(*tasks)

        assert len(created_docs) == 20

        # Verify all documents exist
        all_docs = await repository.find_all()
        assert len(all_docs) == 20

        doc_ids = {doc.id for doc in all_docs}
        expected_ids = {f"concurrent-doc-{i}" for i in range(20)}
        assert doc_ids == expected_ids

    def test_repository_table_name(self, repository):
        """Test that repository uses correct table name."""
        assert repository.table_name == "documents"

    def test_repository_entity_class(self, repository):
        """Test that repository uses correct entity class."""
        assert repository.entity_class == Document

    @pytest.mark.asyncio
    async def test_search_by_content(self, repository):
        """Test searching documents by content."""
        # Create documents with different content
        docs = [
            Document(id="doc1", content="Python programming tutorial", content_hash="h1"),
            Document(id="doc2", content="JavaScript guide", content_hash="h2"),
            Document(id="doc3", content="Python data structures", content_hash="h3"),
        ]

        for doc in docs:
            await repository.save(doc)

        # Search for Python-related documents
        python_docs = await repository.search_by_content("Python")
        assert len(python_docs) == 2

        python_ids = {doc.id for doc in python_docs}
        assert python_ids == {"doc1", "doc3"}
