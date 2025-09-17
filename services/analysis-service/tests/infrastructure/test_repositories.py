"""Tests for Repository Implementations - In-memory and SQLite repositories."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ...infrastructure.repositories.document_repository import (
    DocumentRepository, InMemoryDocumentRepository
)
from ...infrastructure.repositories.analysis_repository import (
    AnalysisRepository, InMemoryAnalysisRepository
)
from ...infrastructure.repositories.finding_repository import (
    FindingRepository, InMemoryFindingRepository
)
from ...infrastructure.repositories.sqlite_document_repository import SQLiteDocumentRepository
from ...infrastructure.repositories.sqlite_analysis_repository import SQLiteAnalysisRepository
from ...infrastructure.repositories.sqlite_finding_repository import SQLiteFindingRepository

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence


class TestDocumentRepositoryInterface:
    """Test cases for DocumentRepository interface."""

    def test_repository_interface_definition(self):
        """Test that DocumentRepository defines the expected interface."""
        # This is a base class test to ensure the interface is properly defined
        repo_methods = [method for method in dir(DocumentRepository) if not method.startswith('_')]

        expected_methods = [
            'save', 'get_by_id', 'get_all', 'get_by_author', 'delete'
        ]

        for method in expected_methods:
            assert method in repo_methods, f"Method {method} should be defined in DocumentRepository"

    def test_abstract_methods_are_abstract(self):
        """Test that repository methods are properly marked as abstract."""
        # Abstract methods should raise NotImplementedError when called
        repo = DocumentRepository()

        with pytest.raises(NotImplementedError):
            asyncio.run(repo.save(Mock()))

        with pytest.raises(NotImplementedError):
            asyncio.run(repo.get_by_id("test-id"))

        with pytest.raises(NotImplementedError):
            asyncio.run(repo.get_all())

        with pytest.raises(NotImplementedError):
            asyncio.run(repo.get_by_author("test-author"))

        with pytest.raises(NotImplementedError):
            asyncio.run(repo.delete("test-id"))


class TestInMemoryDocumentRepository:
    """Test cases for InMemoryDocumentRepository."""

    @pytest.fixture
    def repository(self):
        """Create a fresh in-memory document repository for each test."""
        return InMemoryDocumentRepository()

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return Document(
            id='test-doc-123',
            title='Test Document',
            content='This is test content',
            repository_id='repo-456',
            author='test-author',
            version='1.0.0',
            status=DocumentStatus.ACTIVE
        )

    def test_repository_creation(self, repository):
        """Test creating an in-memory document repository."""
        assert repository is not None
        assert isinstance(repository, DocumentRepository)
        assert isinstance(repository, InMemoryDocumentRepository)
        assert len(repository._documents) == 0

    @pytest.mark.asyncio
    async def test_save_document(self, repository, sample_document):
        """Test saving a document."""
        # Initially empty
        assert len(repository._documents) == 0

        # Save document
        await repository.save(sample_document)

        # Verify document was saved
        assert len(repository._documents) == 1
        assert sample_document.id.value in repository._documents
        assert repository._documents[sample_document.id.value] == sample_document

    @pytest.mark.asyncio
    async def test_get_by_id_existing_document(self, repository, sample_document):
        """Test getting an existing document by ID."""
        await repository.save(sample_document)

        retrieved = await repository.get_by_id(sample_document.id.value)

        assert retrieved is not None
        assert retrieved == sample_document
        assert retrieved.id == sample_document.id
        assert retrieved.title == sample_document.title

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_document(self, repository):
        """Test getting a non-existent document by ID."""
        retrieved = await repository.get_by_id('non-existent-id')

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_all_documents(self, repository):
        """Test getting all documents."""
        # Create and save multiple documents
        docs = []
        for i in range(3):
            doc = Document(
                id=f'test-doc-{i}',
                title=f'Document {i}',
                content=f'Content {i}',
                repository_id='repo-123',
                author=f'author-{i}'
            )
            await repository.save(doc)
            docs.append(doc)

        # Get all documents
        all_docs = await repository.get_all()

        assert len(all_docs) == 3
        # Documents may not be in specific order
        retrieved_ids = [doc.id.value for doc in all_docs]
        expected_ids = [doc.id.value for doc in docs]
        assert set(retrieved_ids) == set(expected_ids)

    @pytest.mark.asyncio
    async def test_get_by_author(self, repository):
        """Test getting documents by author."""
        # Create documents with different authors
        authors = ['alice', 'bob', 'alice', 'charlie']
        docs = []

        for i, author in enumerate(authors):
            doc = Document(
                id=f'test-doc-{i}',
                title=f'Document {i}',
                content=f'Content {i}',
                repository_id='repo-123',
                author=author
            )
            await repository.save(doc)
            docs.append(doc)

        # Get documents by author
        alice_docs = await repository.get_by_author('alice')

        assert len(alice_docs) == 2
        for doc in alice_docs:
            assert doc.author == 'alice'

    @pytest.mark.asyncio
    async def test_delete_existing_document(self, repository, sample_document):
        """Test deleting an existing document."""
        await repository.save(sample_document)
        assert len(repository._documents) == 1

        # Delete document
        result = await repository.delete(sample_document.id.value)

        assert result is True
        assert len(repository._documents) == 0
        assert sample_document.id.value not in repository._documents

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, repository):
        """Test deleting a non-existent document."""
        result = await repository.delete('non-existent-id')

        assert result is False

    @pytest.mark.asyncio
    async def test_update_document(self, repository, sample_document):
        """Test updating a document (save existing document)."""
        await repository.save(sample_document)

        # Modify document
        sample_document.title = 'Updated Title'
        sample_document.version = '2.0.0'

        # Save again (update)
        await repository.save(sample_document)

        # Verify update
        retrieved = await repository.get_by_id(sample_document.id.value)
        assert retrieved.title == 'Updated Title'
        assert retrieved.version == '2.0.0'

    @pytest.mark.asyncio
    async def test_repository_isolation(self):
        """Test that repositories are properly isolated."""
        repo1 = InMemoryDocumentRepository()
        repo2 = InMemoryDocumentRepository()

        doc1 = Document(
            id='doc-1',
            title='Document 1',
            content='Content 1',
            repository_id='repo-1',
            author='author-1'
        )

        doc2 = Document(
            id='doc-2',
            title='Document 2',
            content='Content 2',
            repository_id='repo-2',
            author='author-2'
        )

        # Save to repo1
        await repo1.save(doc1)

        # Save to repo2
        await repo2.save(doc2)

        # Verify isolation
        assert len(repo1._documents) == 1
        assert len(repo2._documents) == 1

        retrieved1 = await repo1.get_by_id('doc-1')
        retrieved2 = await repo2.get_by_id('doc-2')

        assert retrieved1 == doc1
        assert retrieved2 == doc2

        # Cross-repository queries should return None
        cross_retrieved1 = await repo1.get_by_id('doc-2')
        cross_retrieved2 = await repo2.get_by_id('doc-1')

        assert cross_retrieved1 is None
        assert cross_retrieved2 is None


class TestInMemoryAnalysisRepository:
    """Test cases for InMemoryAnalysisRepository."""

    @pytest.fixture
    def repository(self):
        """Create a fresh in-memory analysis repository for each test."""
        return InMemoryAnalysisRepository()

    @pytest.fixture
    def sample_analysis(self):
        """Create a sample analysis for testing."""
        return Analysis(
            id='test-analysis-123',
            document_id='doc-456',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
            status=AnalysisStatus.COMPLETED
        )

    def test_repository_creation(self, repository):
        """Test creating an in-memory analysis repository."""
        assert repository is not None
        assert isinstance(repository, AnalysisRepository)
        assert isinstance(repository, InMemoryAnalysisRepository)
        assert len(repository._analyses) == 0

    @pytest.mark.asyncio
    async def test_save_and_retrieve_analysis(self, repository, sample_analysis):
        """Test saving and retrieving an analysis."""
        await repository.save(sample_analysis)

        retrieved = await repository.get_by_id(sample_analysis.id.value)

        assert retrieved is not None
        assert retrieved == sample_analysis
        assert retrieved.analysis_type == AnalysisType.SEMANTIC_SIMILARITY

    @pytest.mark.asyncio
    async def test_get_by_document_id(self, repository):
        """Test getting analyses by document ID."""
        # Create multiple analyses for different documents
        analyses = []
        for i in range(3):
            analysis = Analysis(
                id=f'analysis-{i}',
                document_id=f'doc-{i % 2}',  # 2 docs, 3 analyses (2 for doc-0, 1 for doc-1)
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=AnalysisStatus.COMPLETED
            )
            await repository.save(analysis)
            analyses.append(analysis)

        # Get analyses for doc-0
        doc_analyses = await repository.get_by_document_id('doc-0')

        assert len(doc_analyses) == 2
        for analysis in doc_analyses:
            assert analysis.document_id == 'doc-0'

    @pytest.mark.asyncio
    async def test_get_by_status(self, repository):
        """Test getting analyses by status."""
        statuses = [AnalysisStatus.PENDING, AnalysisStatus.RUNNING, AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]

        for i, status in enumerate(statuses):
            analysis = Analysis(
                id=f'analysis-{i}',
                document_id='doc-123',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=status
            )
            await repository.save(analysis)

        # Get completed analyses
        completed_analyses = await repository.get_by_status(AnalysisStatus.COMPLETED)

        assert len(completed_analyses) == 1
        assert completed_analyses[0].status == AnalysisStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_get_by_analysis_type(self, repository):
        """Test getting analyses by analysis type."""
        types = [AnalysisType.SEMANTIC_SIMILARITY, AnalysisType.CODE_QUALITY, AnalysisType.SECURITY_SCAN]

        for i, analysis_type in enumerate(types):
            analysis = Analysis(
                id=f'analysis-{i}',
                document_id='doc-123',
                analysis_type=analysis_type,
                status=AnalysisStatus.COMPLETED
            )
            await repository.save(analysis)

        # Get semantic similarity analyses
        semantic_analyses = await repository.get_by_analysis_type(AnalysisType.SEMANTIC_SIMILARITY)

        assert len(semantic_analyses) == 1
        assert semantic_analyses[0].analysis_type == AnalysisType.SEMANTIC_SIMILARITY


class TestInMemoryFindingRepository:
    """Test cases for InMemoryFindingRepository."""

    @pytest.fixture
    def repository(self):
        """Create a fresh in-memory finding repository for each test."""
        return InMemoryFindingRepository()

    @pytest.fixture
    def sample_finding(self):
        """Create a sample finding for testing."""
        return Finding(
            id='test-finding-123',
            analysis_id='analysis-456',
            document_id='doc-789',
            title='Test Finding',
            description='This is a test finding',
            severity=FindingSeverity.MEDIUM,
            confidence=Confidence(0.8),
            category='code_quality'
        )

    def test_repository_creation(self, repository):
        """Test creating an in-memory finding repository."""
        assert repository is not None
        assert isinstance(repository, FindingRepository)
        assert isinstance(repository, InMemoryFindingRepository)
        assert len(repository._findings) == 0

    @pytest.mark.asyncio
    async def test_save_and_retrieve_finding(self, repository, sample_finding):
        """Test saving and retrieving a finding."""
        await repository.save(sample_finding)

        retrieved = await repository.get_by_id(sample_finding.id.value)

        assert retrieved is not None
        assert retrieved == sample_finding
        assert retrieved.severity == FindingSeverity.MEDIUM

    @pytest.mark.asyncio
    async def test_get_by_analysis_id(self, repository):
        """Test getting findings by analysis ID."""
        # Create findings for different analyses
        findings = []
        for i in range(3):
            finding = Finding(
                id=f'finding-{i}',
                analysis_id=f'analysis-{i % 2}',  # 2 analyses, 3 findings (2 for analysis-0, 1 for analysis-1)
                document_id='doc-123',
                title=f'Finding {i}',
                description=f'Description {i}',
                severity=FindingSeverity.MEDIUM,
                confidence=Confidence(0.8),
                category='test'
            )
            await repository.save(finding)
            findings.append(finding)

        # Get findings for analysis-0
        analysis_findings = await repository.get_by_analysis_id('analysis-0')

        assert len(analysis_findings) == 2
        for finding in analysis_findings:
            assert finding.analysis_id == 'analysis-0'

    @pytest.mark.asyncio
    async def test_get_by_document_id(self, repository):
        """Test getting findings by document ID."""
        # Create findings for different documents
        documents = ['doc-1', 'doc-2', 'doc-1']  # 2 docs, 3 findings (2 for doc-1, 1 for doc-2)

        for i, doc_id in enumerate(documents):
            finding = Finding(
                id=f'finding-{i}',
                analysis_id='analysis-123',
                document_id=doc_id,
                title=f'Finding {i}',
                description=f'Description {i}',
                severity=FindingSeverity.MEDIUM,
                confidence=Confidence(0.8),
                category='test'
            )
            await repository.save(finding)

        # Get findings for doc-1
        doc_findings = await repository.get_by_document_id('doc-1')

        assert len(doc_findings) == 2
        for finding in doc_findings:
            assert finding.document_id == 'doc-1'

    @pytest.mark.asyncio
    async def test_get_by_severity(self, repository):
        """Test getting findings by severity."""
        severities = [FindingSeverity.LOW, FindingSeverity.MEDIUM, FindingSeverity.HIGH]

        for i, severity in enumerate(severities):
            finding = Finding(
                id=f'finding-{i}',
                analysis_id='analysis-123',
                document_id='doc-123',
                title=f'Finding {i}',
                description=f'Description {i}',
                severity=severity,
                confidence=Confidence(0.8),
                category='test'
            )
            await repository.save(finding)

        # Get high severity findings
        high_findings = await repository.get_by_severity(FindingSeverity.HIGH)

        assert len(high_findings) == 1
        assert high_findings[0].severity == FindingSeverity.HIGH


class TestSQLiteDocumentRepository:
    """Test cases for SQLiteDocumentRepository."""

    @pytest.fixture
    async def repository(self):
        """Create a fresh SQLite document repository for each test."""
        # Use in-memory SQLite database for testing
        repo = SQLiteDocumentRepository(':memory:')
        await repo.initialize()
        yield repo
        await repo.close()

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return Document(
            id='test-doc-123',
            title='Test Document',
            content='This is test content',
            repository_id='repo-456',
            author='test-author',
            version='1.0.0',
            status=DocumentStatus.ACTIVE
        )

    @pytest.mark.asyncio
    async def test_repository_creation(self, repository):
        """Test creating a SQLite document repository."""
        assert repository is not None
        assert isinstance(repository, DocumentRepository)
        assert isinstance(repository, SQLiteDocumentRepository)
        assert repository.database_path == ':memory:'

    @pytest.mark.asyncio
    async def test_save_and_retrieve_document(self, repository, sample_document):
        """Test saving and retrieving a document with SQLite."""
        await repository.save(sample_document)

        retrieved = await repository.get_by_id(sample_document.id.value)

        assert retrieved is not None
        assert retrieved.id.value == sample_document.id.value
        assert retrieved.title == sample_document.title
        assert retrieved.content == sample_document.content
        assert retrieved.author == sample_document.author

    @pytest.mark.asyncio
    async def test_get_all_documents_sqlite(self, repository):
        """Test getting all documents with SQLite."""
        # Create and save multiple documents
        docs = []
        for i in range(3):
            doc = Document(
                id=f'test-doc-{i}',
                title=f'Document {i}',
                content=f'Content {i}',
                repository_id='repo-123',
                author=f'author-{i}'
            )
            await repository.save(doc)
            docs.append(doc)

        # Get all documents
        all_docs = await repository.get_all()

        assert len(all_docs) == 3
        retrieved_ids = [doc.id.value for doc in all_docs]
        expected_ids = [doc.id.value for doc in docs]
        assert set(retrieved_ids) == set(expected_ids)

    @pytest.mark.asyncio
    async def test_get_by_author_sqlite(self, repository):
        """Test getting documents by author with SQLite."""
        # Create documents with different authors
        authors = ['alice', 'bob', 'alice', 'charlie']

        for i, author in enumerate(authors):
            doc = Document(
                id=f'test-doc-{i}',
                title=f'Document {i}',
                content=f'Content {i}',
                repository_id='repo-123',
                author=author
            )
            await repository.save(doc)

        # Get documents by author
        alice_docs = await repository.get_by_author('alice')

        assert len(alice_docs) == 2
        for doc in alice_docs:
            assert doc.author == 'alice'

    @pytest.mark.asyncio
    async def test_delete_document_sqlite(self, repository, sample_document):
        """Test deleting a document with SQLite."""
        await repository.save(sample_document)

        # Verify document exists
        retrieved = await repository.get_by_id(sample_document.id.value)
        assert retrieved is not None

        # Delete document
        result = await repository.delete(sample_document.id.value)
        assert result is True

        # Verify document is deleted
        retrieved = await repository.get_by_id(sample_document.id.value)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_update_document_sqlite(self, repository, sample_document):
        """Test updating a document with SQLite."""
        await repository.save(sample_document)

        # Modify document
        sample_document.title = 'Updated Title'
        sample_document.version = '2.0.0'

        # Save again (update)
        await repository.save(sample_document)

        # Verify update
        retrieved = await repository.get_by_id(sample_document.id.value)
        assert retrieved.title == 'Updated Title'
        assert retrieved.version == '2.0.0'


class TestRepositoryIntegration:
    """Test integration between different repository types."""

    @pytest.mark.asyncio
    async def test_repository_interface_compatibility(self):
        """Test that different repository implementations are compatible."""
        # Test that both in-memory and SQLite repositories implement the same interface

        # In-memory repository
        memory_repo = InMemoryDocumentRepository()
        assert isinstance(memory_repo, DocumentRepository)

        # SQLite repository (in-memory database)
        sqlite_repo = SQLiteDocumentRepository(':memory:')
        await sqlite_repo.initialize()
        assert isinstance(sqlite_repo, DocumentRepository)

        # Both should have the same interface
        memory_methods = [method for method in dir(memory_repo) if not method.startswith('_') and callable(getattr(memory_repo, method))]
        sqlite_methods = [method for method in dir(sqlite_repo) if not method.startswith('_') and callable(getattr(sqlite_repo, method))]

        # Core methods should be the same
        core_methods = ['save', 'get_by_id', 'get_all', 'get_by_author', 'delete']
        for method in core_methods:
            assert method in memory_methods
            assert method in sqlite_methods

        await sqlite_repo.close()

    @pytest.mark.asyncio
    async def test_cross_repository_data_consistency(self):
        """Test data consistency across different repositories."""
        # Create repositories
        doc_repo = InMemoryDocumentRepository()
        analysis_repo = InMemoryAnalysisRepository()
        finding_repo = InMemoryFindingRepository()

        # Create related entities
        doc = Document(
            id='doc-123',
            title='Test Document',
            content='Test content',
            repository_id='repo-456',
            author='test-author'
        )

        analysis = Analysis(
            id='analysis-456',
            document_id='doc-123',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
            status=AnalysisStatus.COMPLETED
        )

        finding = Finding(
            id='finding-789',
            analysis_id='analysis-456',
            document_id='doc-123',
            title='Test Finding',
            description='Test description',
            severity=FindingSeverity.MEDIUM,
            confidence=Confidence(0.8),
            category='test'
        )

        # Save entities
        await doc_repo.save(doc)
        await analysis_repo.save(analysis)
        await finding_repo.save(finding)

        # Verify relationships
        retrieved_doc = await doc_repo.get_by_id('doc-123')
        assert retrieved_doc is not None

        doc_analyses = await analysis_repo.get_by_document_id('doc-123')
        assert len(doc_analyses) == 1
        assert doc_analyses[0].id.value == 'analysis-456'

        analysis_findings = await finding_repo.get_by_analysis_id('analysis-456')
        assert len(analysis_findings) == 1
        assert analysis_findings[0].id.value == 'finding-789'

    @pytest.mark.asyncio
    async def test_repository_transaction_simulation(self):
        """Test repository behavior in transaction-like scenarios."""
        repo = InMemoryDocumentRepository()

        # Create multiple documents
        docs = []
        for i in range(5):
            doc = Document(
                id=f'doc-{i}',
                title=f'Document {i}',
                content=f'Content {i}',
                repository_id='repo-123',
                author='test-author'
            )
            docs.append(doc)

        # "Transaction": save all documents
        for doc in docs:
            await repo.save(doc)

        # Verify all were saved
        all_docs = await repo.get_all()
        assert len(all_docs) == 5

        # "Rollback": delete all documents
        for doc in docs:
            await repo.delete(doc.id.value)

        # Verify all were deleted
        all_docs = await repo.get_all()
        assert len(all_docs) == 0


class TestRepositoryPerformance:
    """Test performance aspects of repository implementations."""

    @pytest.mark.asyncio
    async def test_in_memory_repository_bulk_operations(self):
        """Test bulk operations performance with in-memory repository."""
        repo = InMemoryDocumentRepository()

        # Create many documents
        docs = []
        for i in range(100):
            doc = Document(
                id=f'bulk-doc-{i:03d}',
                title=f'Bulk Document {i}',
                content=f'Content for document {i}',
                repository_id='bulk-repo',
                author='bulk-author'
            )
            docs.append(doc)

        # Measure bulk save performance
        import time
        start_time = time.time()

        for doc in docs:
            await repo.save(doc)

        save_time = time.time() - start_time

        # Assert reasonable performance (< 0.5 seconds for 100 saves)
        assert save_time < 0.5

        # Verify all documents were saved
        all_docs = await repo.get_all()
        assert len(all_docs) == 100

    @pytest.mark.asyncio
    async def test_repository_query_performance(self):
        """Test repository query performance."""
        repo = InMemoryDocumentRepository()

        # Setup test data
        authors = ['alice', 'bob', 'charlie'] * 50  # 150 documents total

        for i in range(150):
            doc = Document(
                id=f'perf-doc-{i:03d}',
                title=f'Performance Document {i}',
                content=f'Content {i}',
                repository_id='perf-repo',
                author=authors[i % len(authors)]
            )
            await repo.save(doc)

        # Measure query performance
        import time
        start_time = time.time()

        alice_docs = await repo.get_by_author('alice')
        all_docs = await repo.get_all()

        query_time = time.time() - start_time

        # Assert reasonable performance (< 0.1 seconds for queries)
        assert query_time < 0.1

        # Verify query results
        assert len(alice_docs) == 50  # alice appears every 3rd document
        assert len(all_docs) == 150


class TestRepositoryErrorHandling:
    """Test error handling in repository implementations."""

    @pytest.mark.asyncio
    async def test_sqlite_repository_connection_errors(self):
        """Test SQLite repository connection error handling."""
        # Try to create repository with invalid database path
        with pytest.raises(Exception):
            repo = SQLiteDocumentRepository('/invalid/path/database.db')
            await repo.initialize()

    @pytest.mark.asyncio
    async def test_repository_invalid_data_handling(self):
        """Test repository handling of invalid data."""
        repo = InMemoryDocumentRepository()

        # Try to save invalid document (should work as Document validates itself)
        # Document constructor should handle validation
        try:
            invalid_doc = Document(
                id='',  # Invalid empty ID
                title='Invalid Document',
                content='Content',
                repository_id='repo-123'
            )
            # If we get here, the repository should handle it gracefully
            await repo.save(invalid_doc)
        except ValueError:
            # This is expected - invalid data should be caught
            pass

    @pytest.mark.asyncio
    async def test_repository_concurrent_access(self):
        """Test repository concurrent access handling."""
        repo = InMemoryDocumentRepository()

        async def save_document(i: int):
            doc = Document(
                id=f'concurrent-doc-{i}',
                title=f'Concurrent Document {i}',
                content=f'Content {i}',
                repository_id='concurrent-repo',
                author='concurrent-author'
            )
            await repo.save(doc)
            return doc

        # Create concurrent save operations
        tasks = [save_document(i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        # Verify all documents were saved
        assert len(results) == 20

        all_docs = await repo.get_all()
        assert len(all_docs) == 20

        # Verify no duplicates or data corruption
        doc_ids = [doc.id.value for doc in all_docs]
        assert len(set(doc_ids)) == 20  # All IDs should be unique


class TestRepositoryEdgeCases:
    """Test repository edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_repository_operations(self):
        """Test repository operations on empty repository."""
        repo = InMemoryDocumentRepository()

        # Operations on empty repository
        all_docs = await repo.get_all()
        assert len(all_docs) == 0

        retrieved = await repo.get_by_id('non-existent')
        assert retrieved is None

        author_docs = await repo.get_by_author('non-existent-author')
        assert len(author_docs) == 0

        delete_result = await repo.delete('non-existent')
        assert delete_result is False

    @pytest.mark.asyncio
    async def test_repository_large_data_sets(self):
        """Test repository with large data sets."""
        repo = InMemoryDocumentRepository()

        # Create documents with large content
        large_docs = []
        for i in range(10):
            large_content = 'x' * 10000  # 10KB content per document
            doc = Document(
                id=f'large-doc-{i}',
                title=f'Large Document {i}',
                content=large_content,
                repository_id='large-repo',
                author='large-author'
            )
            large_docs.append(doc)
            await repo.save(doc)

        # Verify all large documents were saved
        all_docs = await repo.get_all()
        assert len(all_docs) == 10

        # Verify content integrity
        for doc in all_docs:
            assert len(doc.content) == 10000

    @pytest.mark.asyncio
    async def test_repository_special_characters(self):
        """Test repository handling of special characters."""
        repo = InMemoryDocumentRepository()

        # Create document with special characters
        special_doc = Document(
            id='special-doc-ñáéíóú',
            title='Document with ñáéíóú 🚀 📚 💻',
            content='Content with special chars: @#$%^&*()[]{}',
            repository_id='special-repo',
            author='special-author@domain.com'
        )

        await repo.save(special_doc)

        # Verify retrieval works
        retrieved = await repo.get_by_id('special-doc-ñáéíóú')
        assert retrieved is not None
        assert retrieved.title == 'Document with ñáéíóú 🚀 📚 💻'
        assert '🚀' in retrieved.title

    @pytest.mark.asyncio
    async def test_repository_null_empty_values(self):
        """Test repository handling of null and empty values."""
        repo = InMemoryDocumentRepository()

        # Create document with empty/None values where allowed
        doc = Document(
            id='empty-doc',
            title='Empty Document',
            content='',  # Empty content (might be allowed)
            repository_id='empty-repo',
            author=''  # Empty author
        )

        await repo.save(doc)

        # Verify it was saved
        retrieved = await repo.get_by_id('empty-doc')
        assert retrieved is not None
        assert retrieved.content == ''
        assert retrieved.author == ''
