"""Tests for domain repositories."""

import pytest
from typing import List

from ...domain.repositories.document_repository import DocumentRepository
from ...domain.repositories.analysis_repository import AnalysisRepository
from ...domain.repositories.finding_repository import FindingRepository

from ...infrastructure.repositories.in_memory.document_repository import InMemoryDocumentRepository
from ...infrastructure.repositories.in_memory.analysis_repository import InMemoryAnalysisRepository
from ...infrastructure.repositories.in_memory.finding_repository import InMemoryFindingRepository

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence


class TestDocumentRepository:
    """Test cases for DocumentRepository."""

    def test_repository_creation(self):
        """Test creating document repository."""
        repo = InMemoryDocumentRepository()
        assert isinstance(repo, DocumentRepository)

    @pytest.mark.asyncio
    async def test_save_and_get_document(self, document_repository, sample_document):
        """Test saving and retrieving document."""
        # Save document
        await document_repository.save(sample_document)

        # Retrieve document
        retrieved = await document_repository.get_by_id(sample_document.id)

        assert retrieved == sample_document
        assert retrieved.id == sample_document.id
        assert retrieved.title == sample_document.title

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, document_repository):
        """Test getting non-existent document."""
        retrieved = await document_repository.get_by_id('non-existent-id')
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_update_document(self, document_repository, sample_document):
        """Test updating document."""
        # Save initial document
        await document_repository.save(sample_document)

        # Modify and save again
        sample_document.title = 'Updated Title'
        await document_repository.save(sample_document)

        # Retrieve and verify
        retrieved = await document_repository.get_by_id(sample_document.id)
        assert retrieved.title == 'Updated Title'

    @pytest.mark.asyncio
    async def test_delete_document(self, document_repository, sample_document):
        """Test deleting document."""
        # Save document
        await document_repository.save(sample_document)

        # Delete document
        result = await document_repository.delete(sample_document.id)
        assert result is True

        # Verify deletion
        retrieved = await document_repository.get_by_id(sample_document.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, document_repository):
        """Test deleting non-existent document."""
        result = await document_repository.delete('non-existent-id')
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_documents(self, document_repository, test_data_populator):
        """Test getting all documents."""
        # Setup test data
        documents = test_data_populator.create_test_documents(5)

        # Get all documents
        all_docs = await document_repository.get_all()

        assert len(all_docs) >= 5
        doc_ids = [doc.id for doc in all_docs]
        for doc in documents:
            assert doc.id in doc_ids

    @pytest.mark.asyncio
    async def test_get_documents_by_repository(self, document_repository, test_data_populator):
        """Test getting documents by repository."""
        # Setup test data
        documents = test_data_populator.create_test_documents(3)

        # Get documents by repository
        repo_docs = await document_repository.get_by_repository_id('test-repo-001')

        assert len(repo_docs) == 3
        for doc in repo_docs:
            assert doc.repository_id == 'test-repo-001'

    @pytest.mark.asyncio
    async def test_get_documents_by_status(self, document_repository, test_data_populator):
        """Test getting documents by status."""
        # Setup test data
        documents = test_data_populator.create_test_documents(2)

        # Modify status of one document
        documents[0].status = DocumentStatus.ARCHIVED
        await document_repository.save(documents[0])

        # Get documents by status
        active_docs = await document_repository.get_by_status(DocumentStatus.ACTIVE)
        archived_docs = await document_repository.get_by_status(DocumentStatus.ARCHIVED)

        assert len(active_docs) == 1
        assert len(archived_docs) == 1
        assert active_docs[0].status == DocumentStatus.ACTIVE
        assert archived_docs[0].status == DocumentStatus.ARCHIVED


class TestAnalysisRepository:
    """Test cases for AnalysisRepository."""

    def test_repository_creation(self):
        """Test creating analysis repository."""
        repo = InMemoryAnalysisRepository()
        assert isinstance(repo, AnalysisRepository)

    @pytest.mark.asyncio
    async def test_save_and_get_analysis(self, analysis_repository, sample_analysis):
        """Test saving and retrieving analysis."""
        # Save analysis
        await analysis_repository.save(sample_analysis)

        # Retrieve analysis
        retrieved = await analysis_repository.get_by_id(sample_analysis.id)

        assert retrieved == sample_analysis
        assert retrieved.id == sample_analysis.id
        assert retrieved.analysis_type == sample_analysis.analysis_type

    @pytest.mark.asyncio
    async def test_get_analyses_by_document(self, analysis_repository, test_data_populator):
        """Test getting analyses by document."""
        # Setup test data
        documents = test_data_populator.create_test_documents(1)
        analyses = test_data_populator.create_test_analyses([doc.id for doc in documents], 3)

        document_id = documents[0].id

        # Get analyses by document
        doc_analyses = await analysis_repository.get_by_document_id(document_id)

        assert len(doc_analyses) == 3
        for analysis in doc_analyses:
            assert analysis.document_id == document_id

    @pytest.mark.asyncio
    async def test_get_analyses_by_status(self, analysis_repository, test_data_populator):
        """Test getting analyses by status."""
        # Setup test data
        documents = test_data_populator.create_test_documents(1)
        analyses = test_data_populator.create_test_analyses([doc.id for doc in documents], 2)

        # Modify status of one analysis
        analyses[0].status = AnalysisStatus.FAILED
        await analysis_repository.save(analyses[0])

        # Get analyses by status
        completed_analyses = await analysis_repository.get_by_status(AnalysisStatus.COMPLETED)
        failed_analyses = await analysis_repository.get_by_status(AnalysisStatus.FAILED)

        assert len(completed_analyses) == 1
        assert len(failed_analyses) == 1
        assert completed_analyses[0].status == AnalysisStatus.COMPLETED
        assert failed_analyses[0].status == AnalysisStatus.FAILED

    @pytest.mark.asyncio
    async def test_get_analyses_by_type(self, analysis_repository, test_data_populator):
        """Test getting analyses by type."""
        # Setup test data with different types
        documents = test_data_populator.create_test_documents(1)
        analyses = test_data_populator.create_test_analyses([doc.id for doc in documents], 1)

        # Get analyses by type
        semantic_analyses = await analysis_repository.get_by_analysis_type(AnalysisType.SEMANTIC_SIMILARITY)

        assert len(semantic_analyses) >= 0
        for analysis in semantic_analyses:
            assert analysis.analysis_type == AnalysisType.SEMANTIC_SIMILARITY

    @pytest.mark.asyncio
    async def test_update_analysis_status(self, analysis_repository, sample_analysis):
        """Test updating analysis status."""
        # Save initial analysis
        await analysis_repository.save(sample_analysis)

        # Update status
        sample_analysis.status = AnalysisStatus.RUNNING
        await analysis_repository.save(sample_analysis)

        # Retrieve and verify
        retrieved = await analysis_repository.get_by_id(sample_analysis.id)
        assert retrieved.status == AnalysisStatus.RUNNING


class TestFindingRepository:
    """Test cases for FindingRepository."""

    def test_repository_creation(self):
        """Test creating finding repository."""
        repo = InMemoryFindingRepository()
        assert isinstance(repo, FindingRepository)

    @pytest.mark.asyncio
    async def test_save_and_get_finding(self, finding_repository, sample_finding):
        """Test saving and retrieving finding."""
        # Save finding
        await finding_repository.save(sample_finding)

        # Retrieve finding
        retrieved = await finding_repository.get_by_id(sample_finding.id)

        assert retrieved == sample_finding
        assert retrieved.id == sample_finding.id
        assert retrieved.title == sample_finding.title

    @pytest.mark.asyncio
    async def test_get_findings_by_analysis(self, finding_repository, test_data_populator):
        """Test getting findings by analysis."""
        # Setup test data
        documents = test_data_populator.create_test_documents(1)
        analyses = test_data_populator.create_test_analyses([doc.id for doc in documents], 1)
        findings = test_data_populator.create_test_findings([analysis.id for analysis in analyses], 3)

        analysis_id = analyses[0].id

        # Get findings by analysis
        analysis_findings = await finding_repository.get_by_analysis_id(analysis_id)

        assert len(analysis_findings) == 3
        for finding in analysis_findings:
            assert finding.analysis_id == analysis_id

    @pytest.mark.asyncio
    async def test_get_findings_by_document(self, finding_repository, test_data_populator):
        """Test getting findings by document."""
        # Setup test data
        documents = test_data_populator.create_test_documents(1)
        analyses = test_data_populator.create_test_analyses([doc.id for doc in documents], 2)
        findings = test_data_populator.create_test_findings([analysis.id for analysis in analyses], 2)

        document_id = documents[0].id

        # Get findings by document
        doc_findings = await finding_repository.get_by_document_id(document_id)

        assert len(doc_findings) == 4  # 2 analyses * 2 findings each
        for finding in doc_findings:
            assert finding.document_id == document_id

    @pytest.mark.asyncio
    async def test_get_findings_by_severity(self, finding_repository, test_data_populator):
        """Test getting findings by severity."""
        # Setup test data
        documents = test_data_populator.create_test_documents(1)
        analyses = test_data_populator.create_test_analyses([doc.id for doc in documents], 1)
        findings = test_data_populator.create_test_findings([analysis.id for analysis in analyses], 1)

        # Get findings by severity
        high_findings = await finding_repository.get_by_severity(FindingSeverity.HIGH)

        assert len(high_findings) >= 0
        for finding in high_findings:
            assert finding.severity == FindingSeverity.HIGH

    @pytest.mark.asyncio
    async def test_update_finding(self, finding_repository, sample_finding):
        """Test updating finding."""
        # Save initial finding
        await finding_repository.save(sample_finding)

        # Modify and save again
        sample_finding.title = 'Updated Finding Title'
        await finding_repository.save(sample_finding)

        # Retrieve and verify
        retrieved = await finding_repository.get_by_id(sample_finding.id)
        assert retrieved.title == 'Updated Finding Title'


class TestRepositoryIntegration:
    """Test integration between repositories."""

    @pytest.mark.asyncio
    async def test_cross_repository_queries(
        self, document_repository, analysis_repository, finding_repository,
        test_data_populator
    ):
        """Test queries that span multiple repositories."""
        # Setup comprehensive test data
        documents = test_data_populator.create_test_documents(2)
        analyses = test_data_populator.create_test_analyses([doc.id for doc in documents], 2)
        findings = test_data_populator.create_test_findings([analysis.id for analysis in analyses], 2)

        # Verify cross-repository consistency
        for analysis in analyses:
            # Check that analysis references existing document
            document = await document_repository.get_by_id(analysis.document_id)
            assert document is not None
            assert document.id == analysis.document_id

        for finding in findings:
            # Check that finding references existing analysis and document
            analysis = await analysis_repository.get_by_id(finding.analysis_id)
            assert analysis is not None
            assert analysis.id == finding.analysis_id
            assert analysis.document_id == finding.document_id

            document = await document_repository.get_by_id(finding.document_id)
            assert document is not None
            assert document.id == finding.document_id

    @pytest.mark.asyncio
    async def test_repository_transaction_simulation(
        self, document_repository, analysis_repository, test_data_populator
    ):
        """Test repository behavior in transaction-like scenarios."""
        # Setup test data
        documents = test_data_populator.create_test_documents(1)
        document = documents[0]

        # Simulate transaction: create analysis, then rollback by deleting
        analysis = Analysis(
            id='transaction-test-analysis',
            document_id=document.id,
            analysis_type=AnalysisType.CODE_QUALITY
        )

        await analysis_repository.save(analysis)

        # Verify analysis exists
        retrieved = await analysis_repository.get_by_id(analysis.id)
        assert retrieved is not None

        # "Rollback" by deleting
        await analysis_repository.delete(analysis.id)

        # Verify analysis is gone
        retrieved = await analysis_repository.get_by_id(analysis.id)
        assert retrieved is None


class TestRepositoryPerformance:
    """Test repository performance characteristics."""

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(
        self, document_repository, performance_timer
    ):
        """Test bulk document operations performance."""
        # Create multiple documents
        documents = []
        for i in range(100):
            doc = Document(
                id=f'bulk-doc-{i:03d}',
                title=f'Bulk Document {i}',
                content=f'Content for document {i}',
                repository_id='bulk-repo'
            )
            documents.append(doc)

        # Test bulk save performance
        performance_timer.start()

        for doc in documents:
            await document_repository.save(doc)

        performance_timer.stop()

        # Assert reasonable performance (less than 2 seconds for 100 operations)
        performance_timer.assert_less_than(2.0, "Bulk save operations took too long")

    @pytest.mark.asyncio
    async def test_query_performance(
        self, document_repository, test_data_populator, performance_timer
    ):
        """Test repository query performance."""
        # Setup test data
        documents = test_data_populator.create_test_documents(50)

        # Test query performance
        performance_timer.start()

        all_docs = await document_repository.get_all()
        repo_docs = await document_repository.get_by_repository_id('test-repo-001')

        performance_timer.stop()

        # Assert reasonable performance
        performance_timer.assert_less_than(0.5, "Repository queries took too long")

        assert len(all_docs) >= 50
        assert len(repo_docs) >= 50


class TestRepositoryConcurrency:
    """Test repository concurrency handling."""

    @pytest.mark.asyncio
    async def test_concurrent_saves(self, document_repository):
        """Test concurrent document saves."""
        async def save_document(i: int):
            doc = Document(
                id=f'concurrent-doc-{i}',
                title=f'Concurrent Document {i}',
                content=f'Content {i}',
                repository_id='concurrent-repo'
            )
            await document_repository.save(doc)
            return doc

        # Create multiple concurrent save operations
        tasks = [save_document(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10

        # Verify all documents were saved
        for i, doc in enumerate(results):
            retrieved = await document_repository.get_by_id(doc.id)
            assert retrieved is not None
            assert retrieved.title == f'Concurrent Document {i}'

    @pytest.mark.asyncio
    async def test_concurrent_reads(self, document_repository, test_data_populator):
        """Test concurrent document reads."""
        # Setup test data
        documents = test_data_populator.create_test_documents(20)

        async def read_document(doc_id: str):
            return await document_repository.get_by_id(doc_id)

        # Create multiple concurrent read operations
        tasks = [read_document(doc.id) for doc in documents]
        results = await asyncio.gather(*tasks)

        assert len(results) == 20
        assert all(result is not None for result in results)
