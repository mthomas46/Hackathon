"""Tests for domain services."""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List

from ...domain.services.analysis_service import AnalysisService
from ...domain.services.document_service import DocumentService
from ...domain.services.finding_service import FindingService
from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence


class TestAnalysisService:
    """Test cases for AnalysisService domain service."""

    def test_analysis_service_creation(self, analysis_repository, document_repository):
        """Test creating analysis service."""
        service = AnalysisService(analysis_repository, document_repository)

        assert service.analysis_repository == analysis_repository
        assert service.document_repository == document_repository

    @pytest.mark.asyncio
    async def test_start_analysis_success(
        self, analysis_service, document_repository, sample_document
    ):
        """Test starting analysis successfully."""
        # Setup
        await document_repository.save(sample_document)

        analysis_type = AnalysisType.SEMANTIC_SIMILARITY

        # Execute
        analysis = await analysis_service.start_analysis(
            document_id=sample_document.id,
            analysis_type=analysis_type
        )

        # Assert
        assert analysis.document_id == sample_document.id
        assert analysis.analysis_type == analysis_type
        assert analysis.status == AnalysisStatus.RUNNING

    @pytest.mark.asyncio
    async def test_start_analysis_document_not_found(self, analysis_service):
        """Test starting analysis with non-existent document."""
        with pytest.raises(ValueError, match="Document not found"):
            await analysis_service.start_analysis(
                document_id='non-existent-doc',
                analysis_type=AnalysisType.CODE_QUALITY
            )

    @pytest.mark.asyncio
    async def test_complete_analysis_success(self, analysis_service, sample_analysis):
        """Test completing analysis successfully."""
        # Setup
        sample_analysis.status = AnalysisStatus.RUNNING

        results = {'similarity_score': 0.85}
        confidence = Confidence(0.85)

        # Execute
        completed_analysis = await analysis_service.complete_analysis(
            analysis_id=sample_analysis.id,
            results=results,
            confidence=confidence
        )

        # Assert
        assert completed_analysis.status == AnalysisStatus.COMPLETED
        assert completed_analysis.results == results
        assert completed_analysis.confidence == confidence
        assert completed_analysis.completed_at is not None

    @pytest.mark.asyncio
    async def test_get_analysis_status(self, analysis_service, sample_analysis):
        """Test getting analysis status."""
        # Execute
        status = await analysis_service.get_analysis_status(sample_analysis.id)

        # Assert
        assert status['id'] == sample_analysis.id
        assert status['status'] == sample_analysis.status.value
        assert 'created_at' in status

    def test_validate_analysis_type_support(self, analysis_service):
        """Test analysis type support validation."""
        # All analysis types should be supported
        for analysis_type in AnalysisType:
            assert analysis_service._is_analysis_type_supported(analysis_type)

    @pytest.mark.asyncio
    async def test_cancel_analysis(self, analysis_service, sample_analysis):
        """Test cancelling analysis."""
        # Setup
        sample_analysis.status = AnalysisStatus.RUNNING

        # Execute
        cancelled_analysis = await analysis_service.cancel_analysis(sample_analysis.id)

        # Assert
        assert cancelled_analysis.status == AnalysisStatus.CANCELLED
        assert cancelled_analysis.cancelled_at is not None


class TestDocumentService:
    """Test cases for DocumentService domain service."""

    def test_document_service_creation(self, document_repository):
        """Test creating document service."""
        service = DocumentService(document_repository)

        assert service.document_repository == document_repository

    @pytest.mark.asyncio
    async def test_create_document_success(self, document_service, sample_document_data):
        """Test creating document successfully."""
        # Execute
        document = await document_service.create_document(**sample_document_data)

        # Assert
        assert document.id == sample_document_data['id']
        assert document.title == sample_document_data['title']
        assert document.status == DocumentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_document_by_id(self, document_service, sample_document):
        """Test getting document by ID."""
        # Execute
        document = await document_service.get_document_by_id(sample_document.id)

        # Assert
        assert document == sample_document

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, document_service):
        """Test getting non-existent document."""
        with pytest.raises(ValueError, match="Document not found"):
            await document_service.get_document_by_id('non-existent-id')

    @pytest.mark.asyncio
    async def test_update_document_content(self, document_service, sample_document):
        """Test updating document content."""
        new_content = "# Updated Content\n\nThis is updated content."

        # Execute
        updated_doc = await document_service.update_document_content(
            document_id=sample_document.id,
            new_content=new_content
        )

        # Assert
        assert updated_doc.content == new_content
        assert updated_doc.updated_at > sample_document.updated_at

    @pytest.mark.asyncio
    async def test_archive_document(self, document_service, sample_document):
        """Test archiving document."""
        # Execute
        archived_doc = await document_service.archive_document(sample_document.id)

        # Assert
        assert archived_doc.status == DocumentStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_get_documents_by_repository(self, document_service, test_data_populator):
        """Test getting documents by repository."""
        # Setup test data
        documents = test_data_populator.create_test_documents(3)

        # Execute
        repo_docs = await document_service.get_documents_by_repository('test-repo-001')

        # Assert
        assert len(repo_docs) == 3
        for doc in repo_docs:
            assert doc.repository_id == 'test-repo-001'


class TestFindingService:
    """Test cases for FindingService domain service."""

    def test_finding_service_creation(self, finding_repository):
        """Test creating finding service."""
        service = FindingService(finding_repository)

        assert service.finding_repository == finding_repository

    @pytest.mark.asyncio
    async def test_create_finding_success(self, finding_service, sample_finding_data):
        """Test creating finding successfully."""
        # Execute
        finding = await finding_service.create_finding(**sample_finding_data)

        # Assert
        assert finding.id == sample_finding_data['id']
        assert finding.title == sample_finding_data['title']
        assert finding.severity == FindingSeverity.MEDIUM

    @pytest.mark.asyncio
    async def test_get_findings_by_analysis(self, finding_service, test_data_populator):
        """Test getting findings by analysis."""
        # Setup test data
        documents = test_data_populator.create_test_documents(1)
        analyses = test_data_populator.create_test_analyses([doc.id for doc in documents], 1)
        findings = test_data_populator.create_test_findings([analysis.id for analysis in analyses], 3)

        analysis_id = analyses[0].id

        # Execute
        analysis_findings = await finding_service.get_findings_by_analysis(analysis_id)

        # Assert
        assert len(analysis_findings) == 3
        for finding in analysis_findings:
            assert finding.analysis_id == analysis_id

    @pytest.mark.asyncio
    async def test_get_findings_by_severity(self, finding_service, test_data_populator):
        """Test getting findings by severity."""
        # Setup test data with different severities
        documents = test_data_populator.create_test_documents(1)
        analyses = test_data_populator.create_test_analyses([doc.id for doc in documents], 1)
        findings = test_data_populator.create_test_findings([analysis.id for analysis in analyses], 1)

        # Execute
        high_severity_findings = await finding_service.get_findings_by_severity(FindingSeverity.HIGH)

        # Assert
        for finding in high_severity_findings:
            assert finding.severity == FindingSeverity.HIGH

    @pytest.mark.asyncio
    async def test_update_finding_confidence(self, finding_service, sample_finding):
        """Test updating finding confidence."""
        new_confidence = Confidence(0.9)

        # Execute
        updated_finding = await finding_service.update_finding_confidence(
            finding_id=sample_finding.id,
            new_confidence=new_confidence
        )

        # Assert
        assert updated_finding.confidence == new_confidence

    @pytest.mark.asyncio
    async def test_resolve_finding(self, finding_service, sample_finding):
        """Test resolving finding."""
        resolution_notes = "Fixed by refactoring the code"

        # Execute
        resolved_finding = await finding_service.resolve_finding(
            finding_id=sample_finding.id,
            resolution_notes=resolution_notes
        )

        # Assert
        assert resolved_finding.resolved_at is not None
        assert resolved_finding.resolution_notes == resolution_notes


class TestDomainServiceIntegration:
    """Test integration between domain services."""

    @pytest.mark.asyncio
    async def test_analysis_workflow_integration(
        self, analysis_service, document_service, finding_service,
        test_data_populator
    ):
        """Test complete analysis workflow integration."""
        # Setup test document
        documents = test_data_populator.create_test_documents(1)
        document = documents[0]

        # Start analysis
        analysis = await analysis_service.start_analysis(
            document_id=document.id,
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        assert analysis.status == AnalysisStatus.RUNNING

        # Complete analysis
        results = {'test_result': 'completed'}
        confidence = Confidence(0.85)

        completed_analysis = await analysis_service.complete_analysis(
            analysis_id=analysis.id,
            results=results,
            confidence=confidence
        )

        assert completed_analysis.status == AnalysisStatus.COMPLETED
        assert completed_analysis.results == results

    @pytest.mark.asyncio
    async def test_cross_service_data_consistency(
        self, analysis_service, document_service, finding_service,
        test_data_populator
    ):
        """Test data consistency across services."""
        # Setup test data
        documents = test_data_populator.create_test_documents(2)
        analyses = test_data_populator.create_test_analyses([doc.id for doc in documents], 2)
        findings = test_data_populator.create_test_findings([analysis.id for analysis in analyses], 2)

        # Verify document-analysis relationship
        for analysis in analyses:
            document = await document_service.get_document_by_id(analysis.document_id)
            assert document is not None
            assert document.id == analysis.document_id

        # Verify analysis-finding relationship
        for finding in findings:
            analysis = await analysis_service.get_analysis_status(finding.analysis_id)
            assert analysis is not None
            assert analysis['id'] == finding.analysis_id


class TestDomainServiceErrorHandling:
    """Test error handling in domain services."""

    @pytest.mark.asyncio
    async def test_analysis_service_concurrent_access(
        self, analysis_service, sample_analysis
    ):
        """Test concurrent access to analysis service."""
        # This test would need proper async concurrency testing
        # For now, just test basic functionality
        assert sample_analysis.status == AnalysisStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_document_service_validation_errors(self, document_service):
        """Test document service validation errors."""
        # Test creating document with invalid data
        invalid_data = {
            'id': '',  # Invalid empty ID
            'title': 'Test',
            'content': 'Content',
            'repository_id': 'repo-001'
        }

        with pytest.raises(ValueError):
            await document_service.create_document(**invalid_data)

    @pytest.mark.asyncio
    async def test_finding_service_constraint_validation(self, finding_service):
        """Test finding service constraint validation."""
        # Test creating finding with invalid confidence
        invalid_data = {
            'id': 'test-finding',
            'analysis_id': 'analysis-001',
            'document_id': 'doc-001',
            'title': 'Test Finding',
            'description': 'Description',
            'severity': FindingSeverity.HIGH,
            'confidence': Confidence(1.5),  # Invalid confidence
            'category': 'test'
        }

        # This should fail during finding creation
        with pytest.raises(ValueError):
            await finding_service.create_finding(**invalid_data)


class TestDomainServicePerformance:
    """Test performance aspects of domain services."""

    @pytest.mark.asyncio
    async def test_analysis_service_bulk_operations(
        self, analysis_service, document_repository,
        test_data_populator, performance_timer
    ):
        """Test bulk analysis operations performance."""
        # Setup multiple documents
        documents = test_data_populator.create_test_documents(10)

        # Start performance timer
        performance_timer.start()

        # Perform bulk analysis starts
        analyses = []
        for doc in documents:
            analysis = await analysis_service.start_analysis(
                document_id=doc.id,
                analysis_type=AnalysisType.CODE_QUALITY
            )
            analyses.append(analysis)

        performance_timer.stop()

        # Assert reasonable performance (less than 1 second for 10 operations)
        performance_timer.assert_less_than(1.0, "Bulk analysis operations took too long")

        assert len(analyses) == 10

    @pytest.mark.asyncio
    async def test_document_service_query_performance(
        self, document_service, test_data_populator, performance_timer
    ):
        """Test document query performance."""
        # Setup test data
        documents = test_data_populator.create_test_documents(50)

        # Test query performance
        performance_timer.start()

        repo_docs = await document_service.get_documents_by_repository('test-repo-001')

        performance_timer.stop()

        # Assert reasonable performance
        performance_timer.assert_less_than(0.5, "Document query took too long")

        assert len(repo_docs) == 50
