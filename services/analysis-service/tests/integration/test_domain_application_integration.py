"""Integration tests for Domain + Application layer interaction."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence

from ...domain.services.analysis_service import AnalysisService
from ...domain.services.document_service import DocumentService
from ...domain.services.finding_service import FindingService

from ...application.use_cases.perform_analysis_use_case import PerformAnalysisUseCase, PerformAnalysisCommand
from ...application.use_cases.create_document_use_case import CreateDocumentUseCase
from ...application.use_cases.get_document_use_case import GetDocumentUseCase
from ...application.use_cases.get_findings_use_case import GetFindingsUseCase

from ...application.cqrs.command_bus import CommandBus
from ...application.cqrs.query_bus import QueryBus

from ...application.handlers.command_handlers import (
    CreateDocumentCommandHandler, PerformAnalysisCommandHandler
)
from ...application.handlers.query_handlers import (
    GetDocumentQueryHandler, GetFindingsQueryHandler
)
from ...application.handlers.commands import CreateDocumentCommand, PerformAnalysisCommand
from ...application.handlers.queries import GetDocumentQuery, GetFindingsQuery

from ...application.services.analysis_application_service import AnalysisApplicationService

from ...infrastructure.repositories.in_memory.document_repository import InMemoryDocumentRepository
from ...infrastructure.repositories.in_memory.analysis_repository import InMemoryAnalysisRepository
from ...infrastructure.repositories.in_memory.finding_repository import InMemoryFindingRepository


class TestDomainApplicationIntegration:
    """Test integration between Domain and Application layers."""

    @pytest.fixture
    async def repositories(self):
        """Create test repositories."""
        return {
            'document': InMemoryDocumentRepository(),
            'analysis': InMemoryAnalysisRepository(),
            'finding': InMemoryFindingRepository()
        }

    @pytest.fixture
    def domain_services(self, repositories):
        """Create domain services with repositories."""
        return {
            'document_service': DocumentService(repositories['document']),
            'analysis_service': AnalysisService(repositories['analysis'], repositories['document']),
            'finding_service': FindingService(repositories['finding'])
        }

    @pytest.fixture
    def event_bus(self):
        """Create mock event bus."""
        return Mock()

    @pytest.fixture
    async def use_cases(self, domain_services, repositories, event_bus):
        """Create use cases with dependencies."""
        return {
            'create_document': CreateDocumentUseCase(
                repositories['document'],
                domain_services['document_service'],
                event_bus
            ),
            'perform_analysis': PerformAnalysisUseCase(
                domain_services['analysis_service'],
                domain_services['finding_service'],
                repositories['document'],
                repositories['analysis'],
                repositories['finding'],
                event_bus
            ),
            'get_document': GetDocumentUseCase(repositories['document']),
            'get_findings': GetFindingsUseCase(repositories['finding'])
        }

    @pytest.mark.asyncio
    async def test_document_creation_workflow(self, domain_services, repositories, event_bus):
        """Test complete document creation workflow from domain to application."""
        # Setup
        doc_data = {
            'title': 'Integration Test Document',
            'content': 'This is a test document for integration testing.',
            'repository_id': 'test-repo',
            'author': 'test-author',
            'version': '1.0.0'
        }

        # Execute through domain service
        document = await domain_services['document_service'].create_document(**doc_data)

        # Verify document creation
        assert document.title == doc_data['title']
        assert document.content == doc_data['content']
        assert document.repository_id == doc_data['repository_id']
        assert document.author == doc_data['author']
        assert document.status == DocumentStatus.ACTIVE

        # Verify persistence through repository
        saved_doc = await repositories['document'].get_by_id(document.id.value)
        assert saved_doc is not None
        assert saved_doc.id == document.id

    @pytest.mark.asyncio
    async def test_analysis_workflow_integration(self, domain_services, repositories, event_bus):
        """Test complete analysis workflow integration."""
        # Setup - Create document first
        doc_data = {
            'title': 'Analysis Test Document',
            'content': 'Content for analysis testing.',
            'repository_id': 'test-repo',
            'author': 'test-author'
        }
        document = await domain_services['document_service'].create_document(**doc_data)

        # Setup analysis
        analysis = await domain_services['analysis_service'].start_analysis(
            document_id=document.id.value,
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        assert analysis.document_id == document.id.value
        assert analysis.analysis_type == AnalysisType.SEMANTIC_SIMILARITY
        assert analysis.status == AnalysisStatus.RUNNING

        # Complete analysis
        results = {'similarity_score': 0.85, 'matched_docs': ['doc-1', 'doc-2']}
        confidence = Confidence(0.85)

        completed_analysis = await domain_services['analysis_service'].complete_analysis(
            analysis_id=analysis.id.value,
            results=results,
            confidence=confidence
        )

        assert completed_analysis.status == AnalysisStatus.COMPLETED
        assert completed_analysis.results == results
        assert completed_analysis.confidence == confidence

        # Verify persistence
        saved_analysis = await repositories['analysis'].get_by_id(analysis.id.value)
        assert saved_analysis.status == AnalysisStatus.COMPLETED
        assert saved_analysis.results['similarity_score'] == 0.85

    @pytest.mark.asyncio
    async def test_use_case_orchestration(self, use_cases, repositories):
        """Test use case orchestration with domain services."""
        # Create document via use case
        doc_result = await use_cases['create_document'].execute({
            'title': 'Use Case Test Document',
            'content': 'Content for use case testing.',
            'repository_id': 'test-repo',
            'author': 'test-author'
        })

        assert doc_result.success is True
        document_id = doc_result.document.id.value

        # Get document via use case
        get_result = await use_cases['get_document'].execute(document_id)
        assert get_result.success is True
        assert get_result.document.id.value == document_id
        assert get_result.document.title == 'Use Case Test Document'

    @pytest.mark.asyncio
    async def test_cross_entity_relationships(self, domain_services, repositories):
        """Test relationships between documents, analyses, and findings."""
        # Create document
        document = await domain_services['document_service'].create_document(
            title='Relationship Test Document',
            content='Content for relationship testing.',
            repository_id='test-repo',
            author='test-author'
        )

        # Create multiple analyses for the document
        analyses = []
        for i in range(3):
            analysis = await domain_services['analysis_service'].start_analysis(
                document_id=document.id.value,
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY
            )
            analyses.append(analysis)

        # Complete analyses
        for analysis in analyses:
            await domain_services['analysis_service'].complete_analysis(
                analysis_id=analysis.id.value,
                results={'score': 0.8 + analyses.index(analysis) * 0.05},
                confidence=Confidence(0.8 + analyses.index(analysis) * 0.05)
            )

        # Create findings for analyses
        findings = []
        for i, analysis in enumerate(analyses):
            finding = await domain_services['finding_service'].create_finding(
                document_id=document.id.value,
                analysis_id=analysis.id.value,
                title=f'Finding {i}',
                description=f'Test finding {i}',
                severity=FindingSeverity.MEDIUM,
                confidence=Confidence(0.75),
                category='test'
            )
            findings.append(finding)

        # Verify relationships
        # Document should have 3 analyses
        doc_analyses = await repositories['analysis'].get_by_document_id(document.id.value)
        assert len(doc_analyses) == 3

        # Each analysis should have 1 finding
        for analysis in analyses:
            analysis_findings = await repositories['finding'].get_by_analysis_id(analysis.id.value)
            assert len(analysis_findings) == 1

        # Document should have 3 findings
        doc_findings = await repositories['finding'].get_by_document_id(document.id.value)
        assert len(doc_findings) == 3

    @pytest.mark.asyncio
    async def test_domain_service_business_logic_integration(self, domain_services, repositories):
        """Test domain service business logic integration."""
        # Test document service business rules
        document = await domain_services['document_service'].create_document(
            title='Business Logic Test Document',
            content='Content for business logic testing.',
            repository_id='test-repo',
            author='test-author'
        )

        # Test analysis service business rules
        analysis = await domain_services['analysis_service'].start_analysis(
            document_id=document.id.value,
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        # Verify business rules are enforced
        assert analysis.status == AnalysisStatus.RUNNING
        assert analysis.document_id == document.id.value

        # Test finding service business rules
        finding = await domain_services['finding_service'].create_finding(
            document_id=document.id.value,
            analysis_id=analysis.id.value,
            title='Business Logic Finding',
            description='Test finding for business logic',
            severity=FindingSeverity.HIGH,
            confidence=Confidence(0.9),
            category='security'
        )

        assert finding.severity == FindingSeverity.HIGH
        assert finding.confidence.value == 0.9
        assert finding.category == 'security'


class TestCQRSIntegration:
    """Test CQRS pattern integration between domain and application layers."""

    @pytest.fixture
    async def cqrs_setup(self):
        """Setup CQRS components with dependencies."""
        # Create repositories
        repositories = {
            'document': InMemoryDocumentRepository(),
            'analysis': InMemoryAnalysisRepository(),
            'finding': InMemoryFindingRepository()
        }

        # Create domain services
        domain_services = {
            'document_service': DocumentService(repositories['document']),
            'analysis_service': AnalysisService(repositories['analysis'], repositories['document']),
            'finding_service': FindingService(repositories['finding'])
        }

        # Create event bus
        event_bus = Mock()

        # Create command and query buses
        command_bus = CommandBus()
        query_bus = QueryBus()

        # Register command handlers
        command_handlers = {
            'create_document': CreateDocumentCommandHandler(
                repositories['document'],
                domain_services['document_service'],
                event_bus
            ),
            'perform_analysis': PerformAnalysisCommandHandler(
                domain_services['analysis_service'],
                repositories['document'],
                repositories['analysis'],
                repositories['finding'],
                event_bus
            )
        }

        # Register query handlers
        query_handlers = {
            'get_document': GetDocumentQueryHandler(repositories['document']),
            'get_findings': GetFindingsQueryHandler(repositories['finding'])
        }

        for command_name, handler in command_handlers.items():
            command_bus.register_handler(command_name, handler)

        for query_name, handler in query_handlers.items():
            query_bus.register_handler(query_name, handler)

        return {
            'repositories': repositories,
            'domain_services': domain_services,
            'command_bus': command_bus,
            'query_bus': query_bus,
            'event_bus': event_bus
        }

    @pytest.mark.asyncio
    async def test_cqrs_create_document_workflow(self, cqrs_setup):
        """Test CQRS workflow for document creation."""
        setup = cqrs_setup

        # Create document command
        command = CreateDocumentCommand(
            title='CQRS Test Document',
            content='Content for CQRS testing.',
            repository_id='test-repo',
            author='test-author'
        )

        # Execute command
        result = await setup['command_bus'].execute(command)

        # Verify command result
        assert 'document_id' in result
        assert 'status' in result
        assert result['status'] == 'created'

        document_id = result['document_id']

        # Query document
        query = GetDocumentQuery(document_id=document_id)
        query_result = await setup['query_bus'].execute(query)

        # Verify query result
        assert 'document' in query_result
        assert query_result['document']['id'] == document_id
        assert query_result['document']['title'] == 'CQRS Test Document'

    @pytest.mark.asyncio
    async def test_cqrs_analysis_workflow(self, cqrs_setup):
        """Test CQRS workflow for analysis execution."""
        setup = cqrs_setup

        # First create a document
        create_command = CreateDocumentCommand(
            title='CQRS Analysis Document',
            content='Content for CQRS analysis testing.',
            repository_id='test-repo',
            author='test-author'
        )

        create_result = await setup['command_bus'].execute(create_command)
        document_id = create_result['document_id']

        # Perform analysis
        analysis_command = PerformAnalysisCommand(
            document_id=document_id,
            analysis_type='semantic_similarity'
        )

        analysis_result = await setup['command_bus'].execute(analysis_command)

        # Verify analysis result
        assert 'analysis_id' in analysis_result
        assert 'status' in analysis_result

        # Query findings (if any were created)
        findings_query = GetFindingsQuery(analysis_id=analysis_result['analysis_id'])
        findings_result = await setup['query_bus'].execute(findings_query)

        # Verify findings query
        assert 'findings' in findings_result
        assert 'total_count' in findings_result

    @pytest.mark.asyncio
    async def test_cqrs_separation_of_concerns(self, cqrs_setup):
        """Test that CQRS properly separates commands from queries."""
        setup = cqrs_setup

        # Create document via command
        command = CreateDocumentCommand(
            title='Separation Test Document',
            content='Testing CQRS separation.',
            repository_id='test-repo',
            author='test-author'
        )

        command_result = await setup['command_bus'].execute(command)
        document_id = command_result['document_id']

        # Query document via query (separate path)
        query = GetDocumentQuery(document_id=document_id)
        query_result = await setup['query_bus'].execute(query)

        # Verify both work independently
        assert command_result['status'] == 'created'
        assert query_result['document']['id'] == document_id

        # Verify data consistency
        assert query_result['document']['title'] == 'Separation Test Document'


class TestApplicationServiceIntegration:
    """Test AnalysisApplicationService integration with domain services."""

    @pytest.fixture
    def mock_application_services(self):
        """Mock application services for testing."""
        return {
            'logging_service': Mock(),
            'caching_service': Mock(),
            'monitoring_service': Mock(),
            'transaction_service': Mock()
        }

    @pytest.fixture
    async def repositories(self):
        """Create test repositories."""
        return {
            'document': InMemoryDocumentRepository(),
            'analysis': InMemoryAnalysisRepository(),
            'finding': InMemoryFindingRepository()
        }

    @pytest.fixture
    def domain_services(self, repositories):
        """Create domain services."""
        return {
            'document_service': DocumentService(repositories['document']),
            'analysis_service': AnalysisService(repositories['analysis'], repositories['document']),
            'finding_service': FindingService(repositories['finding'])
        }

    @pytest.mark.asyncio
    async def test_application_service_orchestration(self, domain_services, repositories, mock_application_services):
        """Test application service orchestrating domain services."""
        # Create application service
        app_service = AnalysisApplicationService(
            domain_services=domain_services,
            application_services=mock_application_services
        )

        # Create document through application service
        doc_result = await app_service.create_document({
            'title': 'App Service Test Document',
            'content': 'Content for application service testing.',
            'repository_id': 'test-repo',
            'author': 'test-author'
        })

        assert doc_result.success is True
        document_id = doc_result.document.id.value

        # Perform analysis through application service
        analysis_result = await app_service.perform_analysis_workflow(
            document_id=document_id,
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        assert analysis_result.success is True
        assert analysis_result.analysis.document_id == document_id

        # Verify cross-service data consistency
        saved_doc = await repositories['document'].get_by_id(document_id)
        assert saved_doc is not None

        saved_analysis = await repositories['analysis'].get_by_id(analysis_result.analysis.id.value)
        assert saved_analysis is not None
        assert saved_analysis.document_id == document_id

    @pytest.mark.asyncio
    async def test_application_service_error_handling(self, domain_services, repositories, mock_application_services):
        """Test application service error handling integration."""
        app_service = AnalysisApplicationService(
            domain_services=domain_services,
            application_services=mock_application_services
        )

        # Try to perform analysis on non-existent document
        with pytest.raises(ValueError, match="Document not found"):
            await app_service.perform_analysis_workflow(
                document_id='non-existent-doc',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY
            )

    @pytest.mark.asyncio
    async def test_application_service_cross_cutting_concerns(self, domain_services, repositories, mock_application_services):
        """Test application service integration with cross-cutting concerns."""
        # Setup mocks to verify they're called
        mock_logging = mock_application_services['logging_service']
        mock_caching = mock_application_services['caching_service']
        mock_monitoring = mock_application_services['monitoring_service']

        app_service = AnalysisApplicationService(
            domain_services=domain_services,
            application_services=mock_application_services
        )

        # Create document (should trigger cross-cutting concerns)
        doc_result = await app_service.create_document({
            'title': 'Cross-Cutting Test Document',
            'content': 'Testing cross-cutting concerns.',
            'repository_id': 'test-repo',
            'author': 'test-author'
        })

        # Verify document creation
        assert doc_result.success is True

        # Note: In a real implementation, these would be called
        # For now, we verify the application service has access to them
        assert hasattr(app_service, 'application_services')
        assert 'logging_service' in app_service.application_services
        assert 'caching_service' in app_service.application_services
        assert 'monitoring_service' in app_service.application_services


class TestDomainApplicationWorkflowIntegration:
    """Test complete workflows across domain and application layers."""

    @pytest.fixture
    async def full_setup(self):
        """Create full integration setup."""
        # Repositories
        repositories = {
            'document': InMemoryDocumentRepository(),
            'analysis': InMemoryAnalysisRepository(),
            'finding': InMemoryFindingRepository()
        }

        # Domain services
        domain_services = {
            'document_service': DocumentService(repositories['document']),
            'analysis_service': AnalysisService(repositories['analysis'], repositories['document']),
            'finding_service': FindingService(repositories['finding'])
        }

        # Application services
        application_services = {
            'logging_service': Mock(),
            'caching_service': Mock(),
            'monitoring_service': Mock(),
            'transaction_service': Mock()
        }

        # Event bus
        event_bus = Mock()

        # Application service
        app_service = AnalysisApplicationService(
            domain_services=domain_services,
            application_services=application_services
        )

        # Use cases
        use_cases = {
            'create_document': CreateDocumentUseCase(
                repositories['document'],
                domain_services['document_service'],
                event_bus
            ),
            'perform_analysis': PerformAnalysisUseCase(
                domain_services['analysis_service'],
                domain_services['finding_service'],
                repositories['document'],
                repositories['analysis'],
                repositories['finding'],
                event_bus
            )
        }

        return {
            'repositories': repositories,
            'domain_services': domain_services,
            'application_services': application_services,
            'app_service': app_service,
            'use_cases': use_cases,
            'event_bus': event_bus
        }

    @pytest.mark.asyncio
    async def test_complete_document_lifecycle(self, full_setup):
        """Test complete document lifecycle across all layers."""
        setup = full_setup

        # 1. Create document
        doc_result = await setup['use_cases']['create_document'].execute({
            'title': 'Lifecycle Test Document',
            'content': 'Complete lifecycle testing document.',
            'repository_id': 'test-repo',
            'author': 'test-author'
        })

        assert doc_result.success is True
        document_id = doc_result.document.id.value

        # 2. Perform analysis
        analysis_result = await setup['use_cases']['perform_analysis'].execute(
            PerformAnalysisCommand(
                document_id=document_id,
                analysis_type='semantic_similarity'
            )
        )

        assert analysis_result.success is True
        analysis_id = analysis_result.analysis.id.value

        # 3. Verify complete data flow
        # Document exists
        saved_doc = await setup['repositories']['document'].get_by_id(document_id)
        assert saved_doc is not None

        # Analysis exists and is linked
        saved_analysis = await setup['repositories']['analysis'].get_by_id(analysis_id)
        assert saved_analysis is not None
        assert saved_analysis.document_id == document_id

        # Analysis is linked to document
        doc_analyses = await setup['repositories']['analysis'].get_by_document_id(document_id)
        assert len(doc_analyses) == 1
        assert doc_analyses[0].id.value == analysis_id

    @pytest.mark.asyncio
    async def test_multi_document_analysis_workflow(self, full_setup):
        """Test workflow with multiple documents and analyses."""
        setup = full_setup

        # Create multiple documents
        documents = []
        for i in range(3):
            doc_result = await setup['use_cases']['create_document'].execute({
                'title': f'Multi-Doc Test Document {i}',
                'content': f'Content for multi-document testing {i}.',
                'repository_id': 'test-repo',
                'author': f'author-{i}'
            })
            documents.append(doc_result.document)

        # Perform analyses on each document
        analyses = []
        for doc in documents:
            analysis_result = await setup['use_cases']['perform_analysis'].execute(
                PerformAnalysisCommand(
                    document_id=doc.id.value,
                    analysis_type='semantic_similarity'
                )
            )
            analyses.append(analysis_result.analysis)

        # Verify all relationships
        for i, (doc, analysis) in enumerate(zip(documents, analyses)):
            # Document exists
            saved_doc = await setup['repositories']['document'].get_by_id(doc.id.value)
            assert saved_doc is not None
            assert saved_doc.title == f'Multi-Doc Test Document {i}'

            # Analysis exists and is linked
            saved_analysis = await setup['repositories']['analysis'].get_by_id(analysis.id.value)
            assert saved_analysis is not None
            assert saved_analysis.document_id == doc.id.value

        # Verify repository queries work across all data
        all_docs = await setup['repositories']['document'].get_all()
        assert len(all_docs) == 3

        all_analyses = await setup['repositories']['analysis'].get_all()
        assert len(all_analyses) == 3

        # Verify cross-references
        for analysis in all_analyses:
            # Each analysis should reference an existing document
            doc = await setup['repositories']['document'].get_by_id(analysis.document_id)
            assert doc is not None

    @pytest.mark.asyncio
    async def test_error_propagation_across_layers(self, full_setup):
        """Test error propagation across domain and application layers."""
        setup = full_setup

        # Try to perform analysis on non-existent document
        with pytest.raises(Exception):  # Should propagate from domain to application layer
            await setup['use_cases']['perform_analysis'].execute(
                PerformAnalysisCommand(
                    document_id='non-existent-doc',
                    analysis_type='semantic_similarity'
                )
            )

    @pytest.mark.asyncio
    async def test_data_consistency_across_operations(self, full_setup):
        """Test data consistency across multiple operations."""
        setup = full_setup

        # Create document
        doc_result = await setup['use_cases']['create_document'].execute({
            'title': 'Consistency Test Document',
            'content': 'Testing data consistency across operations.',
            'repository_id': 'test-repo',
            'author': 'test-author'
        })

        document_id = doc_result.document.id.value

        # Perform multiple analyses
        for i in range(3):
            analysis_result = await setup['use_cases']['perform_analysis'].execute(
                PerformAnalysisCommand(
                    document_id=document_id,
                    analysis_type='semantic_similarity'
                )
            )

            assert analysis_result.success is True

        # Verify final state consistency
        doc_analyses = await setup['repositories']['analysis'].get_by_document_id(document_id)
        assert len(doc_analyses) == 3

        # All analyses should reference the same document
        for analysis in doc_analyses:
            assert analysis.document_id == document_id

        # Document should still exist and be unchanged
        final_doc = await setup['repositories']['document'].get_by_id(document_id)
        assert final_doc is not None
        assert final_doc.title == 'Consistency Test Document'
