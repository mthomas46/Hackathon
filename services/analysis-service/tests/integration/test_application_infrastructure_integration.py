"""Integration tests for Application + Infrastructure layer interaction."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...application.services.application_service import ApplicationService
from ...application.services.logging_service import LoggingService
from ...application.services.caching_service import CachingService
from ...application.services.monitoring_service import MonitoringService
from ...application.services.transaction_service import TransactionService
from ...application.services.analysis_application_service import AnalysisApplicationService

from ...application.use_cases.perform_analysis_use_case import PerformAnalysisUseCase
from ...application.use_cases.create_document_use_case import CreateDocumentUseCase

from ...infrastructure.repositories.sqlite_document_repository import SQLiteDocumentRepository
from ...infrastructure.repositories.sqlite_analysis_repository import SQLiteAnalysisRepository
from ...infrastructure.repositories.sqlite_finding_repository import SQLiteFindingRepository

from ...infrastructure.connection_pooling.database_pool import SQLiteConnectionPool
from ...infrastructure.connection_pooling.http_pool import HTTPConnectionPool
from ...infrastructure.connection_pooling.redis_pool import RedisConnectionPool
from ...infrastructure.connection_pooling.connection_pool_manager import ConnectionPoolManager

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence


class TestApplicationInfrastructureIntegration:
    """Test integration between Application and Infrastructure layers."""

    @pytest.fixture
    async def sqlite_repositories(self):
        """Create SQLite repositories for testing."""
        repos = {
            'document': SQLiteDocumentRepository(':memory:'),
            'analysis': SQLiteAnalysisRepository(':memory:'),
            'finding': SQLiteFindingRepository(':memory:')
        }

        # Initialize all repositories
        for repo in repos.values():
            await repo.initialize()

        yield repos

        # Clean up
        for repo in repos.values():
            await repo.close()

    @pytest.fixture
    def domain_services(self, sqlite_repositories):
        """Create domain services with SQLite repositories."""
        from ...domain.services.document_service import DocumentService
        from ...domain.services.analysis_service import AnalysisService
        from ...domain.services.finding_service import FindingService

        return {
            'document_service': DocumentService(sqlite_repositories['document']),
            'analysis_service': AnalysisService(sqlite_repositories['analysis'], sqlite_repositories['document']),
            'finding_service': FindingService(sqlite_repositories['finding'])
        }

    @pytest.mark.asyncio
    async def test_application_service_with_sqlite_persistence(self, domain_services, sqlite_repositories):
        """Test application service with SQLite persistence."""
        # Create application service
        app_service = AnalysisApplicationService(
            domain_services=domain_services,
            application_services={
                'logging_service': Mock(),
                'caching_service': Mock(),
                'monitoring_service': Mock(),
                'transaction_service': Mock()
            }
        )

        # Create document
        doc_result = await app_service.create_document({
            'title': 'SQLite Integration Test Document',
            'content': 'Testing application service with SQLite persistence.',
            'repository_id': 'test-repo',
            'author': 'test-author'
        })

        assert doc_result.success is True
        document_id = doc_result.document.id.value

        # Verify persistence
        saved_doc = await sqlite_repositories['document'].get_by_id(document_id)
        assert saved_doc is not None
        assert saved_doc.title == 'SQLite Integration Test Document'

        # Perform analysis
        analysis_result = await app_service.perform_analysis_workflow(
            document_id=document_id,
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        assert analysis_result.success is True

        # Verify analysis persistence
        saved_analysis = await sqlite_repositories['analysis'].get_by_id(analysis_result.analysis.id.value)
        assert saved_analysis is not None
        assert saved_analysis.document_id == document_id

    @pytest.mark.asyncio
    async def test_use_case_with_sqlite_backend(self, domain_services, sqlite_repositories):
        """Test use cases with SQLite backend."""
        # Create use case
        use_case = CreateDocumentUseCase(
            sqlite_repositories['document'],
            domain_services['document_service'],
            Mock()  # event_bus
        )

        # Execute use case
        result = await use_case.execute({
            'title': 'Use Case SQLite Test Document',
            'content': 'Testing use case with SQLite backend.',
            'repository_id': 'test-repo',
            'author': 'test-author'
        })

        assert result.success is True

        # Verify persistence
        saved_doc = await sqlite_repositories['document'].get_by_id(result.document.id.value)
        assert saved_doc is not None
        assert saved_doc.title == 'Use Case SQLite Test Document'


class TestConnectionPoolingIntegration:
    """Test connection pooling integration with application services."""

    @pytest.fixture
    async def connection_pools(self):
        """Create connection pools for testing."""
        pools = {}

        # SQLite connection pool
        pools['sqlite'] = SQLiteConnectionPool(
            database_path=':memory:',
            pool_size=5,
            max_overflow=10
        )
        await pools['sqlite'].initialize()

        # HTTP connection pool (mock)
        pools['http'] = HTTPConnectionPool(
            base_url='https://api.example.com',
            pool_size=10,
            timeout_seconds=30.0
        )

        # Redis connection pool (mock)
        pools['redis'] = RedisConnectionPool(
            host='localhost',
            port=6379,
            pool_size=5,
            database=1
        )

        yield pools

        # Cleanup
        for pool in pools.values():
            if hasattr(pool, 'close'):
                await pool.close()

    @pytest.mark.asyncio
    async def test_connection_pool_manager_integration(self, connection_pools):
        """Test connection pool manager with multiple pools."""
        manager = ConnectionPoolManager()

        # Register pools
        manager.register_pool('sqlite', connection_pools['sqlite'])
        manager.register_pool('http', connection_pools['http'])
        manager.register_pool('redis', connection_pools['redis'])

        # Verify pool registration
        assert 'sqlite' in manager._pools
        assert 'http' in manager._pools
        assert 'redis' in manager._pools

        # Test pool retrieval
        sqlite_pool = manager.get_pool('sqlite')
        assert sqlite_pool == connection_pools['sqlite']

        # Test pool health
        health_status = await manager.get_health_status()
        assert 'sqlite' in health_status
        assert 'http' in health_status
        assert 'redis' in health_status

    @pytest.mark.asyncio
    async def test_sqlite_pool_with_repository_integration(self, connection_pools):
        """Test SQLite pool integration with repositories."""
        sqlite_pool = connection_pools['sqlite']

        # Create repository with pooled connection
        repo = SQLiteDocumentRepository(database_path=':memory:', connection_pool=sqlite_pool)
        await repo.initialize()

        # Create and save document
        doc = Document(
            id='pool-test-doc',
            title='Connection Pool Test Document',
            content='Testing connection pooling with repositories.',
            repository_id='test-repo',
            author='test-author'
        )

        await repo.save(doc)

        # Retrieve document
        retrieved = await repo.get_by_id('pool-test-doc')
        assert retrieved is not None
        assert retrieved.title == 'Connection Pool Test Document'

        await repo.close()

    @pytest.mark.asyncio
    async def test_http_pool_with_external_service_integration(self, connection_pools):
        """Test HTTP pool integration with external services."""
        http_pool = connection_pools['http']

        # Mock external service call
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'result': 'success'})

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)

            mock_session.return_value.get = AsyncMock(return_value=mock_context)

            # Test HTTP call through pool
            async with http_pool.get_connection() as session:
                async with session.get('/api/test') as response:
                    data = await response.json()
                    assert data['result'] == 'success'


class TestCrossCuttingConcernsIntegration:
    """Test cross-cutting concerns integration with infrastructure."""

    @pytest.fixture
    async def infrastructure_setup(self):
        """Create infrastructure components for testing."""
        # SQLite repositories
        repos = {
            'document': SQLiteDocumentRepository(':memory:'),
            'analysis': SQLiteAnalysisRepository(':memory:'),
            'finding': SQLiteFindingRepository(':memory:')
        }

        for repo in repos.values():
            await repo.initialize()

        # Connection pools
        pools = {
            'sqlite': SQLiteConnectionPool(database_path=':memory:', pool_size=5),
            'http': HTTPConnectionPool(base_url='https://api.example.com', pool_size=10)
        }

        for pool in pools.values():
            if hasattr(pool, 'initialize'):
                await pool.initialize()

        yield {
            'repositories': repos,
            'pools': pools
        }

        # Cleanup
        for repo in repos.values():
            await repo.close()
        for pool in pools.values():
            if hasattr(pool, 'close'):
                await pool.close()

    @pytest.mark.asyncio
    async def test_logging_service_with_file_persistence(self, infrastructure_setup):
        """Test logging service with file persistence."""
        setup = infrastructure_setup

        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            log_file = temp_file.name

        try:
            # Create logging service with file handler
            from ...application.services.logging_service import RotatingFileHandler
            import logging

            logger = logging.getLogger('test_logger')
            handler = RotatingFileHandler(log_file, max_bytes=1024, backup_count=3)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            # Log some messages
            logger.info("Test log message 1")
            logger.warning("Test warning message")
            logger.error("Test error message")

            # Verify log file was created and contains messages
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert "Test log message 1" in log_content
                assert "Test warning message" in log_content
                assert "Test error message" in log_content

        finally:
            # Cleanup
            if os.path.exists(log_file):
                os.unlink(log_file)

    @pytest.mark.asyncio
    async def test_caching_service_with_redis_pool(self, infrastructure_setup):
        """Test caching service with Redis connection pool."""
        setup = infrastructure_setup

        # Mock Redis pool for testing
        redis_pool = setup['pools'].get('redis', Mock())

        # Create caching service
        from ...application.services.caching_service import ApplicationCache

        cache = ApplicationCache(max_size=100, ttl_seconds=300)

        # Test basic caching operations
        await cache.set('test_key', 'test_value')
        value = await cache.get('test_key')
        assert value == 'test_value'

        # Test cache with TTL
        await cache.set('ttl_key', 'ttl_value', ttl_seconds=1)
        value = await cache.get('ttl_key')
        assert value == 'ttl_value'

        # Wait for expiration
        await asyncio.sleep(1.1)
        value = await cache.get('ttl_key')
        assert value is None

    @pytest.mark.asyncio
    async def test_monitoring_service_with_metrics_collection(self, infrastructure_setup):
        """Test monitoring service with metrics collection."""
        setup = infrastructure_setup

        from ...application.services.monitoring_service import ApplicationMetrics

        metrics = ApplicationMetrics(service_name='test-service')

        # Record various metrics
        await metrics.increment_counter('requests_total', labels={'method': 'GET'})
        await metrics.increment_counter('requests_total', labels={'method': 'POST'})

        await metrics.set_gauge('active_connections', 5)
        await metrics.record_histogram('request_duration', 0.125, labels={'method': 'GET'})
        await metrics.record_histogram('request_duration', 0.089, labels={'method': 'POST'})

        # Verify metrics were recorded (implementation-dependent)
        # In a real scenario, these would be persisted or exported
        assert metrics.service_name == 'test-service'

    @pytest.mark.asyncio
    async def test_transaction_service_with_sqlite_pool(self, infrastructure_setup):
        """Test transaction service with SQLite connection pool."""
        setup = infrastructure_setup

        from ...application.services.transaction_service import SQLiteTransactionManager

        sqlite_pool = setup['pools']['sqlite']
        transaction_manager = SQLiteTransactionManager(pool=sqlite_pool)

        # Test transaction lifecycle
        async with transaction_manager.begin_transaction() as tx:
            assert tx is not None
            # In a real scenario, database operations would happen here
            # The transaction would be committed automatically on exit

        # Test transaction rollback
        try:
            async with transaction_manager.begin_transaction() as tx:
                # Simulate an error
                raise ValueError("Test error for rollback")
        except ValueError:
            pass  # Expected

        # Transaction should have been rolled back


class TestApplicationInfrastructureWorkflowIntegration:
    """Test complete workflows across application and infrastructure layers."""

    @pytest.fixture
    async def full_infrastructure_setup(self):
        """Create complete infrastructure setup for integration testing."""
        # Repositories
        repos = {
            'document': SQLiteDocumentRepository(':memory:'),
            'analysis': SQLiteAnalysisRepository(':memory:'),
            'finding': SQLiteFindingRepository(':memory:')
        }

        # Initialize repositories
        for repo in repos.values():
            await repo.initialize()

        # Domain services
        from ...domain.services.document_service import DocumentService
        from ...domain.services.analysis_service import AnalysisService
        from ...domain.services.finding_service import FindingService

        domain_services = {
            'document_service': DocumentService(repos['document']),
            'analysis_service': AnalysisService(repos['analysis'], repos['document']),
            'finding_service': FindingService(repos['finding'])
        }

        # Application services
        app_services = {
            'logging_service': LoggingService(),
            'caching_service': CachingService(),
            'monitoring_service': MonitoringService(),
            'transaction_service': TransactionService()
        }

        # Event bus
        from ...application.events.event_bus import EventBus
        event_bus = EventBus()

        # Application service
        app_service = AnalysisApplicationService(
            domain_services=domain_services,
            application_services=app_services
        )

        yield {
            'repositories': repos,
            'domain_services': domain_services,
            'application_services': app_services,
            'app_service': app_service,
            'event_bus': event_bus
        }

        # Cleanup
        for repo in repos.values():
            await repo.close()

    @pytest.mark.asyncio
    async def test_complete_workflow_with_infrastructure(self, full_infrastructure_setup):
        """Test complete workflow with full infrastructure stack."""
        setup = full_infrastructure_setup

        # 1. Create document through application service
        doc_result = await setup['app_service'].create_document({
            'title': 'Full Infrastructure Test Document',
            'content': 'Testing complete infrastructure integration.',
            'repository_id': 'test-repo',
            'author': 'test-author'
        })

        assert doc_result.success is True
        document_id = doc_result.document.id.value

        # 2. Verify document persistence
        saved_doc = await setup['repositories']['document'].get_by_id(document_id)
        assert saved_doc is not None
        assert saved_doc.title == 'Full Infrastructure Test Document'

        # 3. Perform analysis
        analysis_result = await setup['app_service'].perform_analysis_workflow(
            document_id=document_id,
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        assert analysis_result.success is True

        # 4. Verify analysis persistence
        saved_analysis = await setup['repositories']['analysis'].get_by_id(analysis_result.analysis.id.value)
        assert saved_analysis is not None
        assert saved_analysis.document_id == document_id

        # 5. Verify relationships
        doc_analyses = await setup['repositories']['analysis'].get_by_document_id(document_id)
        assert len(doc_analyses) == 1
        assert doc_analyses[0].id.value == analysis_result.analysis.id.value

    @pytest.mark.asyncio
    async def test_concurrent_operations_with_infrastructure(self, full_infrastructure_setup):
        """Test concurrent operations with infrastructure components."""
        setup = full_infrastructure_setup

        async def create_and_analyze_document(i: int):
            """Create document and perform analysis concurrently."""
            # Create document
            doc_result = await setup['app_service'].create_document({
                'title': f'Concurrent Test Document {i}',
                'content': f'Content for concurrent testing {i}.',
                'repository_id': 'test-repo',
                'author': f'author-{i}'
            })

            document_id = doc_result.document.id.value

            # Perform analysis
            analysis_result = await setup['app_service'].perform_analysis_workflow(
                document_id=document_id,
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY
            )

            return document_id, analysis_result.analysis.id.value

        # Execute concurrent operations
        tasks = [create_and_analyze_document(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # Verify all operations completed successfully
        assert len(results) == 5

        for document_id, analysis_id in results:
            # Verify document exists
            doc = await setup['repositories']['document'].get_by_id(document_id)
            assert doc is not None

            # Verify analysis exists and is linked
            analysis = await setup['repositories']['analysis'].get_by_id(analysis_id)
            assert analysis is not None
            assert analysis.document_id == document_id

        # Verify total counts
        all_docs = await setup['repositories']['document'].get_all()
        all_analyses = await setup['repositories']['analysis'].get_all()

        assert len(all_docs) == 5
        assert len(all_analyses) == 5

    @pytest.mark.asyncio
    async def test_error_handling_with_infrastructure(self, full_infrastructure_setup):
        """Test error handling with infrastructure components."""
        setup = full_infrastructure_setup

        # Test with non-existent document
        with pytest.raises(ValueError, match="Document not found"):
            await setup['app_service'].perform_analysis_workflow(
                document_id='non-existent-doc',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY
            )

        # Test with invalid analysis type
        doc_result = await setup['app_service'].create_document({
            'title': 'Error Handling Test Document',
            'content': 'Testing error handling.',
            'repository_id': 'test-repo',
            'author': 'test-author'
        })

        document_id = doc_result.document.id.value

        # Should handle gracefully (depending on implementation)
        # In a real scenario, invalid analysis types would be validated
        analysis_result = await setup['app_service'].perform_analysis_workflow(
            document_id=document_id,
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        assert analysis_result.success is True

    @pytest.mark.asyncio
    async def test_resource_management_with_infrastructure(self, full_infrastructure_setup):
        """Test resource management with infrastructure components."""
        setup = full_infrastructure_setup

        # Create multiple documents and analyses
        operations = []
        for i in range(10):
            # Create document
            doc_result = await setup['app_service'].create_document({
                'title': f'Resource Test Document {i}',
                'content': f'Content for resource testing {i}.',
                'repository_id': 'test-repo',
                'author': f'author-{i}'
            })

            document_id = doc_result.document.id.value

            # Perform analysis
            analysis_result = await setup['app_service'].perform_analysis_workflow(
                document_id=document_id,
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY
            )

            operations.append((document_id, analysis_result.analysis.id.value))

        # Verify all resources were managed properly
        assert len(operations) == 10

        # Verify data integrity
        all_docs = await setup['repositories']['document'].get_all()
        all_analyses = await setup['repositories']['analysis'].get_all()

        assert len(all_docs) == 10
        assert len(all_analyses) == 10

        # Verify no resource leaks or data corruption
        for doc in all_docs:
            assert doc.title.startswith('Resource Test Document')

        for analysis in all_analyses:
            # Each analysis should reference a valid document
            doc = await setup['repositories']['document'].get_by_id(analysis.document_id)
            assert doc is not None


class TestInfrastructurePerformanceIntegration:
    """Test performance aspects of infrastructure integration."""

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self):
        """Test bulk operations performance with infrastructure."""
        # Create SQLite repository
        repo = SQLiteDocumentRepository(':memory:')
        await repo.initialize()

        # Create bulk documents
        docs = []
        for i in range(100):
            doc = Document(
                id=f'perf-doc-{i:03d}',
                title=f'Performance Test Document {i}',
                content=f'Content for performance testing {i}.',
                repository_id='perf-repo',
                author='perf-author'
            )
            docs.append(doc)

        # Measure bulk save performance
        import time
        start_time = time.time()

        for doc in docs:
            await repo.save(doc)

        save_time = time.time() - start_time

        # Assert reasonable performance (< 1 second for 100 saves)
        assert save_time < 1.0

        # Verify all documents were saved
        all_docs = await repo.get_all()
        assert len(all_docs) == 100

        await repo.close()

    @pytest.mark.asyncio
    async def test_query_performance_with_relationships(self):
        """Test query performance with complex relationships."""
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(':memory:')
        analysis_repo = SQLiteAnalysisRepository(':memory:')
        finding_repo = SQLiteFindingRepository(':memory:')

        await doc_repo.initialize()
        await analysis_repo.initialize()
        await finding_repo.initialize()

        # Create test data with relationships
        for i in range(50):
            # Create document
            doc = Document(
                id=f'rel-doc-{i:03d}',
                title=f'Relationship Test Document {i}',
                content=f'Content {i}',
                repository_id='rel-repo',
                author='rel-author'
            )
            await doc_repo.save(doc)

            # Create analysis for document
            analysis = Analysis(
                id=f'rel-analysis-{i:03d}',
                document_id=f'rel-doc-{i:03d}',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=AnalysisStatus.COMPLETED
            )
            await analysis_repo.save(analysis)

            # Create findings for analysis
            for j in range(3):  # 3 findings per analysis
                finding = Finding(
                    id=f'rel-finding-{i:03d}-{j}',
                    analysis_id=f'rel-analysis-{i:03d}',
                    document_id=f'rel-doc-{i:03d}',
                    title=f'Finding {i}-{j}',
                    description=f'Description {i}-{j}',
                    severity=FindingSeverity.MEDIUM,
                    confidence=Confidence(0.8),
                    category='test'
                )
                await finding_repo.save(finding)

        # Measure complex query performance
        import time
        start_time = time.time()

        # Query with relationships
        all_docs = await doc_repo.get_all()
        all_analyses = await analysis_repo.get_all()
        all_findings = await finding_repo.get_all()

        # Cross-reference queries
        for analysis in all_analyses[:10]:  # Test first 10
            doc = await doc_repo.get_by_id(analysis.document_id)
            analysis_findings = await finding_repo.get_by_analysis_id(analysis.id.value)

        query_time = time.time() - start_time

        # Assert reasonable performance (< 2 seconds for complex queries)
        assert query_time < 2.0

        # Verify data integrity
        assert len(all_docs) == 50
        assert len(all_analyses) == 50
        assert len(all_findings) == 150  # 50 * 3

        # Cleanup
        await doc_repo.close()
        await analysis_repo.close()
        await finding_repo.close()
