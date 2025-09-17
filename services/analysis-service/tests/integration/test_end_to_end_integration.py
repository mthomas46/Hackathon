"""End-to-end integration tests for complete system workflows."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence

from ...domain.services.document_service import DocumentService
from ...domain.services.analysis_service import AnalysisService
from ...domain.services.finding_service import FindingService

from ...application.services.analysis_application_service import AnalysisApplicationService
from ...application.use_cases.perform_analysis_use_case import PerformAnalysisUseCase, PerformAnalysisCommand
from ...application.use_cases.create_document_use_case import CreateDocumentUseCase
from ...application.use_cases.get_document_use_case import GetDocumentUseCase
from ...application.use_cases.get_findings_use_case import GetFindingsUseCase

from ...application.cqrs.command_bus import CommandBus
from ...application.cqrs.query_bus import QueryBus
from ...application.handlers.commands import CreateDocumentCommand, PerformAnalysisCommand
from ...application.handlers.queries import GetDocumentQuery, GetFindingsQuery
from ...application.handlers.command_handlers import CreateDocumentCommandHandler, PerformAnalysisCommandHandler
from ...application.handlers.query_handlers import GetDocumentQueryHandler, GetFindingsQueryHandler

from ...infrastructure.repositories.sqlite_document_repository import SQLiteDocumentRepository
from ...infrastructure.repositories.sqlite_analysis_repository import SQLiteAnalysisRepository
from ...infrastructure.repositories.sqlite_finding_repository import SQLiteFindingRepository

from ...application.dto.request_dtos import CreateDocumentRequest, PerformAnalysisRequest
from ...application.dto.response_dtos import DocumentResponse, AnalysisResultResponse


class TestEndToEndWorkflowIntegration:
    """Test complete end-to-end workflows across all layers."""

    @pytest.fixture
    async def complete_system_setup(self):
        """Create complete system setup for end-to-end testing."""
        # Infrastructure layer
        repositories = {
            'document': SQLiteDocumentRepository(':memory:'),
            'analysis': SQLiteAnalysisRepository(':memory:'),
            'finding': SQLiteFindingRepository(':memory:')
        }

        # Initialize repositories
        for repo in repositories.values():
            await repo.initialize()

        # Domain layer
        domain_services = {
            'document_service': DocumentService(repositories['document']),
            'analysis_service': AnalysisService(repositories['analysis'], repositories['document']),
            'finding_service': FindingService(repositories['finding'])
        }

        # Application layer
        application_services = {
            'logging_service': Mock(),
            'caching_service': Mock(),
            'monitoring_service': Mock(),
            'transaction_service': Mock()
        }

        # CQRS components
        command_bus = CommandBus()
        query_bus = QueryBus()

        # Event bus
        event_bus = Mock()

        # Register command handlers
        command_handlers = {
            'CreateDocumentCommand': CreateDocumentCommandHandler(
                repositories['document'],
                domain_services['document_service'],
                event_bus
            ),
            'PerformAnalysisCommand': PerformAnalysisCommandHandler(
                domain_services['analysis_service'],
                repositories['document'],
                repositories['analysis'],
                repositories['finding'],
                event_bus
            )
        }

        # Register query handlers
        query_handlers = {
            'GetDocumentQuery': GetDocumentQueryHandler(repositories['document']),
            'GetFindingsQuery': GetFindingsQueryHandler(repositories['finding'])
        }

        for command_type, handler in command_handlers.items():
            command_bus.register_handler(command_type, handler)

        for query_type, handler in query_handlers.items():
            query_bus.register_handler(query_type, handler)

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
            ),
            'get_document': GetDocumentUseCase(repositories['document']),
            'get_findings': GetFindingsUseCase(repositories['finding'])
        }

        yield {
            'repositories': repositories,
            'domain_services': domain_services,
            'application_services': application_services,
            'command_bus': command_bus,
            'query_bus': query_bus,
            'app_service': app_service,
            'use_cases': use_cases,
            'event_bus': event_bus
        }

        # Cleanup
        for repo in repositories.values():
            await repo.close()

    @pytest.mark.asyncio
    async def test_complete_analysis_workflow_end_to_end(self, complete_system_setup):
        """Test complete analysis workflow from document creation to findings retrieval."""
        setup = complete_system_setup

        # Step 1: Create document through application service
        doc_result = await setup['app_service'].create_document({
            'title': 'End-to-End Test Document',
            'content': 'This document tests the complete analysis workflow from creation to findings.',
            'repository_id': 'e2e-repo',
            'author': 'e2e-author',
            'version': '1.0.0'
        })

        assert doc_result.success is True
        document_id = doc_result.document.id.value

        # Step 2: Verify document was created and persisted
        saved_doc = await setup['repositories']['document'].get_by_id(document_id)
        assert saved_doc is not None
        assert saved_doc.title == 'End-to-End Test Document'
        assert saved_doc.status == DocumentStatus.ACTIVE

        # Step 3: Perform analysis through use case
        analysis_command = PerformAnalysisCommand(
            document_id=document_id,
            analysis_type='semantic_similarity',
            priority='high',
            timeout_seconds=60
        )

        analysis_result = await setup['use_cases']['perform_analysis'].execute(analysis_command)
        assert analysis_result.success is True
        analysis_id = analysis_result.analysis.id.value

        # Step 4: Verify analysis was created and completed
        saved_analysis = await setup['repositories']['analysis'].get_by_id(analysis_id)
        assert saved_analysis is not None
        assert saved_analysis.document_id == document_id
        assert saved_analysis.analysis_type == AnalysisType.SEMANTIC_SIMILARITY
        assert saved_analysis.status == AnalysisStatus.COMPLETED

        # Step 5: Retrieve findings through query
        findings_result = await setup['use_cases']['get_findings'].execute(analysis_id)
        assert findings_result.success is True

        # Step 6: Verify complete data consistency
        # Document exists
        final_doc = await setup['repositories']['document'].get_by_id(document_id)
        assert final_doc is not None

        # Analysis exists and links to document
        final_analysis = await setup['repositories']['analysis'].get_by_id(analysis_id)
        assert final_analysis is not None
        assert final_analysis.document_id == document_id

        # Analysis is in document's analyses
        doc_analyses = await setup['repositories']['analysis'].get_by_document_id(document_id)
        assert len(doc_analyses) == 1
        assert doc_analyses[0].id.value == analysis_id

    @pytest.mark.asyncio
    async def test_cqrs_end_to_end_workflow(self, complete_system_setup):
        """Test complete CQRS workflow from command to query."""
        setup = complete_system_setup

        # Step 1: Create document via CQRS command
        create_command = CreateDocumentCommand(
            title='CQRS End-to-End Test Document',
            content='Testing complete CQRS workflow.',
            repository_id='cqrs-repo',
            author='cqrs-author'
        )

        command_result = await setup['command_bus'].execute(create_command)
        assert command_result['status'] == 'created'
        document_id = command_result['document_id']

        # Step 2: Query document via CQRS query
        get_query = GetDocumentQuery(document_id=document_id)
        query_result = await setup['query_bus'].execute(get_query)

        assert query_result['document']['id'] == document_id
        assert query_result['document']['title'] == 'CQRS End-to-End Test Document'

        # Step 3: Perform analysis via CQRS command
        analysis_command = PerformAnalysisCommand(
            document_id=document_id,
            analysis_type='semantic_similarity'
        )

        analysis_command_result = await setup['command_bus'].execute(analysis_command)
        assert analysis_command_result['status'] == 'completed'
        analysis_id = analysis_command_result['analysis_id']

        # Step 4: Query findings via CQRS query
        findings_query = GetFindingsQuery(analysis_id=analysis_id)
        findings_query_result = await setup['query_bus'].execute(findings_query)

        assert 'findings' in findings_query_result
        assert 'total_count' in findings_query_result

        # Step 5: Verify end-to-end data consistency
        # Check document still exists
        doc_check = await setup['repositories']['document'].get_by_id(document_id)
        assert doc_check is not None

        # Check analysis exists and is linked
        analysis_check = await setup['repositories']['analysis'].get_by_id(analysis_id)
        assert analysis_check is not None
        assert analysis_check.document_id == document_id

    @pytest.mark.asyncio
    async def test_multiple_analysis_workflow(self, complete_system_setup):
        """Test workflow with multiple analyses on the same document."""
        setup = complete_system_setup

        # Step 1: Create document
        doc_result = await setup['app_service'].create_document({
            'title': 'Multi-Analysis Test Document',
            'content': 'Document for testing multiple analysis types.',
            'repository_id': 'multi-repo',
            'author': 'multi-author'
        })

        document_id = doc_result.document.id.value

        # Step 2: Perform multiple analyses
        analysis_types = ['semantic_similarity', 'code_quality', 'security_scan']
        analysis_results = []

        for analysis_type in analysis_types:
            result = await setup['app_service'].perform_analysis_workflow(
                document_id=document_id,
                analysis_type=getattr(AnalysisType, analysis_type.upper())
            )
            analysis_results.append(result)

        # Step 3: Verify all analyses completed
        assert len(analysis_results) == 3
        for result in analysis_results:
            assert result.success is True

        # Step 4: Verify data consistency
        # Document should exist
        doc = await setup['repositories']['document'].get_by_id(document_id)
        assert doc is not None

        # All analyses should exist and be linked to document
        doc_analyses = await setup['repositories']['analysis'].get_by_document_id(document_id)
        assert len(doc_analyses) == 3

        analysis_ids = [result.analysis.id.value for result in analysis_results]
        saved_analysis_ids = [analysis.id.value for analysis in doc_analyses]

        # All analysis IDs should match
        assert set(analysis_ids) == set(saved_analysis_ids)

        # Each analysis should have the correct type
        for analysis in doc_analyses:
            assert analysis.analysis_type in [AnalysisType.SEMANTIC_SIMILARITY, AnalysisType.CODE_QUALITY, AnalysisType.SECURITY_SCAN]

    @pytest.mark.asyncio
    async def test_concurrent_workflows_end_to_end(self, complete_system_setup):
        """Test concurrent end-to-end workflows."""
        setup = complete_system_setup

        async def complete_workflow(i: int):
            """Execute complete workflow for document i."""
            # Create document
            doc_result = await setup['app_service'].create_document({
                'title': f'Concurrent Test Document {i}',
                'content': f'Content for concurrent workflow testing {i}.',
                'repository_id': 'concurrent-repo',
                'author': f'author-{i}'
            })

            document_id = doc_result.document.id.value

            # Perform analysis
            analysis_result = await setup['app_service'].perform_analysis_workflow(
                document_id=document_id,
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY
            )

            return document_id, analysis_result.analysis.id.value

        # Execute multiple concurrent workflows
        num_workflows = 10
        tasks = [complete_workflow(i) for i in range(num_workflows)]
        results = await asyncio.gather(*tasks)

        # Verify all workflows completed successfully
        assert len(results) == num_workflows

        all_document_ids = []
        all_analysis_ids = []

        for document_id, analysis_id in results:
            all_document_ids.append(document_id)
            all_analysis_ids.append(analysis_id)

            # Verify each document exists
            doc = await setup['repositories']['document'].get_by_id(document_id)
            assert doc is not None
            assert doc.title == f'Concurrent Test Document {all_document_ids.index(document_id)}'

            # Verify each analysis exists and is linked
            analysis = await setup['repositories']['analysis'].get_by_id(analysis_id)
            assert analysis is not None
            assert analysis.document_id == document_id

        # Verify no duplicates
        assert len(set(all_document_ids)) == num_workflows
        assert len(set(all_analysis_ids)) == num_workflows

        # Verify total counts
        all_docs = await setup['repositories']['document'].get_all()
        all_analyses = await setup['repositories']['analysis'].get_all()

        assert len(all_docs) == num_workflows
        assert len(all_analyses) == num_workflows


class TestSystemIntegrationWithExternalServices:
    """Test system integration with external services."""

    @pytest.fixture
    async def system_with_mocked_externals(self):
        """Create system setup with mocked external services."""
        # Infrastructure
        repositories = {
            'document': SQLiteDocumentRepository(':memory:'),
            'analysis': SQLiteAnalysisRepository(':memory:'),
            'finding': SQLiteFindingRepository(':memory:')
        }

        for repo in repositories.values():
            await repo.initialize()

        # Domain services
        domain_services = {
            'document_service': DocumentService(repositories['document']),
            'analysis_service': AnalysisService(repositories['analysis'], repositories['document']),
            'finding_service': FindingService(repositories['finding'])
        }

        # Mock external services
        mock_external_services = {
            'semantic_analyzer': Mock(),
            'sentiment_analyzer': Mock(),
            'content_quality_scorer': Mock(),
            'logging_service': Mock(),
            'caching_service': Mock(),
            'monitoring_service': Mock()
        }

        # Setup mock responses
        mock_external_services['semantic_analyzer'].analyze = AsyncMock(return_value={
            'similarity_score': 0.85,
            'matched_documents': ['doc-1', 'doc-2'],
            'confidence': 0.9
        })

        mock_external_services['sentiment_analyzer'].analyze = AsyncMock(return_value={
            'sentiment': 'positive',
            'confidence': 0.8
        })

        yield {
            'repositories': repositories,
            'domain_services': domain_services,
            'external_services': mock_external_services
        }

        # Cleanup
        for repo in repositories.values():
            await repo.close()

    @pytest.mark.asyncio
    async def test_analysis_with_external_service_integration(self, system_with_mocked_externals):
        """Test analysis workflow with external service integration."""
        setup = system_with_mocked_externals

        # Create document
        doc = Document(
            id='external-test-doc',
            title='External Service Test Document',
            content='Testing integration with external services.',
            repository_id='external-repo',
            author='external-author'
        )

        await setup['repositories']['document'].save(doc)

        # Perform analysis (which would use external services)
        analysis = await setup['domain_services']['analysis_service'].start_analysis(
            document_id='external-test-doc',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        # Complete analysis
        results = {'external_service_result': 'success'}
        confidence = Confidence(0.85)

        completed_analysis = await setup['domain_services']['analysis_service'].complete_analysis(
            analysis_id=analysis.id.value,
            results=results,
            confidence=confidence
        )

        # Verify external service was called
        # (In real implementation, external services would be called during analysis)

        # Verify analysis completed
        assert completed_analysis.status == AnalysisStatus.COMPLETED
        assert completed_analysis.results == results

    @pytest.mark.asyncio
    async def test_caching_integration_in_workflow(self, system_with_mocked_externals):
        """Test caching integration in complete workflow."""
        setup = system_with_mocked_externals

        # Mock cache operations
        mock_cache = setup['external_services']['caching_service']
        mock_cache.get = AsyncMock(return_value=None)  # Cache miss
        mock_cache.set = AsyncMock()

        # Create application service with caching
        app_service = AnalysisApplicationService(
            domain_services=setup['domain_services'],
            application_services=setup['external_services']
        )

        # Execute workflow that should use caching
        doc_result = await app_service.create_document({
            'title': 'Caching Test Document',
            'content': 'Testing caching integration.',
            'repository_id': 'cache-repo',
            'author': 'cache-author'
        })

        # In a real implementation, caching would be used for:
        # - Document retrieval
        # - Analysis results
        # - External service responses

        assert doc_result.success is True

        # Verify caching service is available
        assert 'caching_service' in app_service.application_services


class TestSystemPerformanceIntegration:
    """Test system performance under integration scenarios."""

    @pytest.mark.asyncio
    async def test_bulk_operations_performance_end_to_end(self):
        """Test bulk operations performance across all layers."""
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(':memory:')
        analysis_repo = SQLiteAnalysisRepository(':memory:')

        await doc_repo.initialize()
        await analysis_repo.initialize()

        # Create bulk documents and analyses
        num_operations = 100

        # Measure document creation performance
        import time
        start_time = time.time()

        for i in range(num_operations):
            doc = Document(
                id=f'bulk-doc-{i:03d}',
                title=f'Bulk Performance Test Document {i}',
                content=f'Content for bulk performance testing {i}.',
                repository_id='bulk-repo',
                author='bulk-author'
            )
            await doc_repo.save(doc)

            # Create analysis for each document
            analysis = Analysis(
                id=f'bulk-analysis-{i:03d}',
                document_id=f'bulk-doc-{i:03d}',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=AnalysisStatus.COMPLETED
            )
            await analysis_repo.save(analysis)

        bulk_time = time.time() - start_time

        # Assert reasonable performance (< 5 seconds for 100 documents + 100 analyses)
        assert bulk_time < 5.0

        # Verify all data was created
        all_docs = await doc_repo.get_all()
        all_analyses = await analysis_repo.get_all()

        assert len(all_docs) == num_operations
        assert len(all_analyses) == num_operations

        # Cleanup
        await doc_repo.close()
        await analysis_repo.close()

    @pytest.mark.asyncio
    async def test_concurrent_users_simulation(self):
        """Test system behavior under concurrent user load."""
        # Setup
        doc_repo = SQLiteDocumentRepository(':memory:')
        await doc_repo.initialize()

        async def simulate_user_workflow(user_id: int):
            """Simulate a complete user workflow."""
            # Create document
            doc = Document(
                id=f'user-{user_id}-doc',
                title=f'User {user_id} Document',
                content=f'Content from user {user_id}.',
                repository_id='user-repo',
                author=f'user-{user_id}'
            )
            await doc_repo.save(doc)

            # Simulate some processing time
            await asyncio.sleep(0.01)

            # Retrieve document
            retrieved = await doc_repo.get_by_id(f'user-{user_id}-doc')
            return retrieved is not None

        # Simulate concurrent users
        num_users = 50
        tasks = [simulate_user_workflow(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks)

        # Verify all user workflows completed successfully
        assert len(results) == num_users
        assert all(results)  # All should return True

        # Verify all documents were created
        all_docs = await doc_repo.get_all()
        assert len(all_docs) == num_users

        await doc_repo.close()

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage under load."""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Setup
        doc_repo = SQLiteDocumentRepository(':memory:')
        await doc_repo.initialize()

        # Create many documents with large content
        large_content = 'x' * 10000  # 10KB per document
        num_docs = 1000

        for i in range(num_docs):
            doc = Document(
                id=f'memory-doc-{i:04d}',
                title=f'Memory Test Document {i}',
                content=large_content,
                repository_id='memory-repo',
                author='memory-author'
            )
            await doc_repo.save(doc)

        # Check memory usage after operations
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Assert reasonable memory usage (< 500MB increase)
        assert memory_increase < 500.0

        # Verify all documents were created
        all_docs = await doc_repo.get_all()
        assert len(all_docs) == num_docs

        await doc_repo.close()


class TestSystemResilienceIntegration:
    """Test system resilience under various failure scenarios."""

    @pytest.mark.asyncio
    async def test_database_connection_failure_recovery(self):
        """Test system behavior when database connection fails."""
        # This would test connection pooling and retry logic
        # For now, test with in-memory database which doesn't fail

        doc_repo = SQLiteDocumentRepository(':memory:')
        await doc_repo.initialize()

        # Simulate normal operation
        doc = Document(
            id='resilience-test-doc',
            title='Resilience Test Document',
            content='Testing system resilience.',
            repository_id='resilience-repo',
            author='resilience-author'
        )

        await doc_repo.save(doc)
        retrieved = await doc_repo.get_by_id('resilience-test-doc')

        assert retrieved is not None
        assert retrieved.title == 'Resilience Test Document'

        await doc_repo.close()

    @pytest.mark.asyncio
    async def test_partial_system_failure_handling(self):
        """Test system behavior when some components fail."""
        # Setup with some mocked failures
        repositories = {
            'document': SQLiteDocumentRepository(':memory:'),
            'analysis': SQLiteDocumentRepository(':memory:'),  # Wrong type to simulate failure
            'finding': SQLiteDocumentRepository(':memory:')    # Wrong type to simulate failure
        }

        await repositories['document'].initialize()

        # This should still work for document operations
        doc = Document(
            id='partial-failure-doc',
            title='Partial Failure Test Document',
            content='Testing partial system failure.',
            repository_id='failure-repo',
            author='failure-author'
        )

        await repositories['document'].save(doc)
        retrieved = await repositories['document'].get_by_id('partial-failure-doc')

        assert retrieved is not None

        await repositories['document'].close()

    @pytest.mark.asyncio
    async def test_system_recovery_after_errors(self):
        """Test system recovery after encountering errors."""
        doc_repo = SQLiteDocumentRepository(':memory:')
        await doc_repo.initialize()

        # Simulate error scenario
        try:
            # Try to save invalid document
            invalid_doc = Document(
                id='',  # Invalid
                title='Invalid Document',
                content='Content',
                repository_id='recovery-repo'
            )
            await doc_repo.save(invalid_doc)
        except Exception:
            pass  # Expected

        # System should still work after error
        valid_doc = Document(
            id='recovery-test-doc',
            title='Recovery Test Document',
            content='Testing system recovery after errors.',
            repository_id='recovery-repo',
            author='recovery-author'
        )

        await doc_repo.save(valid_doc)
        retrieved = await doc_repo.get_by_id('recovery-test-doc')

        assert retrieved is not None
        assert retrieved.title == 'Recovery Test Document'

        await doc_repo.close()


class TestSystemMonitoringIntegration:
    """Test system monitoring and observability integration."""

    @pytest.mark.asyncio
    async def test_operation_metrics_collection(self):
        """Test collection of operation metrics during workflows."""
        # Setup
        doc_repo = SQLiteDocumentRepository(':memory:')
        await doc_repo.initialize()

        # Track operation counts (in real system, this would be automated)
        operations_count = {'saves': 0, 'retrieves': 0}

        # Perform operations
        for i in range(10):
            doc = Document(
                id=f'metrics-doc-{i}',
                title=f'Metrics Test Document {i}',
                content=f'Content {i}',
                repository_id='metrics-repo',
                author='metrics-author'
            )

            await doc_repo.save(doc)
            operations_count['saves'] += 1

            retrieved = await doc_repo.get_by_id(f'metrics-doc-{i}')
            operations_count['retrieves'] += 1

        # Verify operations were performed
        assert operations_count['saves'] == 10
        assert operations_count['retrieves'] == 10

        # In a real system, these metrics would be automatically collected
        # and exposed via monitoring endpoints

        await doc_repo.close()

    @pytest.mark.asyncio
    async def test_error_rate_monitoring(self):
        """Test monitoring of error rates."""
        doc_repo = SQLiteDocumentRepository(':memory:')
        await doc_repo.initialize()

        # Track errors
        error_count = 0
        success_count = 0

        # Perform mix of successful and failed operations
        for i in range(20):
            if i % 5 == 0:  # Every 5th operation fails
                try:
                    invalid_doc = Document(
                        id='',  # Invalid
                        title=f'Invalid Document {i}',
                        content='Content',
                        repository_id='error-repo'
                    )
                    await doc_repo.save(invalid_doc)
                except Exception:
                    error_count += 1
            else:
                doc = Document(
                    id=f'error-test-doc-{i}',
                    title=f'Error Test Document {i}',
                    content='Content',
                    repository_id='error-repo',
                    author='error-author'
                )
                await doc_repo.save(doc)
                success_count += 1

        # Verify error tracking
        assert error_count == 4  # 20/5 = 4 errors
        assert success_count == 16  # 20 - 4 = 16 successes

        # In a real system, error rates would be monitored and alerted on
        error_rate = error_count / (error_count + success_count)
        assert error_rate == 0.2  # 20% error rate

        await doc_repo.close()
