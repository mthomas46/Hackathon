"""Tests for Analysis Repository Implementation."""

import pytest
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...infrastructure.repositories.analysis_repository import (
    AnalysisRepository, InMemoryAnalysisRepository
)
from ...infrastructure.repositories.sqlite_analysis_repository import SQLiteAnalysisRepository

from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence
from ...domain.value_objects.metrics import AnalysisMetrics


class TestAnalysisRepositoryInterface:
    """Test cases for AnalysisRepository interface."""

    def test_repository_interface_definition(self):
        """Test that AnalysisRepository defines the expected interface."""
        repo_methods = [method for method in dir(AnalysisRepository) if not method.startswith('_')]

        expected_methods = [
            'save', 'get_by_id', 'get_all', 'get_by_document_id',
            'get_by_status', 'get_by_analysis_type', 'delete'
        ]

        for method in expected_methods:
            assert method in repo_methods, f"Method {method} should be defined in AnalysisRepository"


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
            status=AnalysisStatus.COMPLETED,
            confidence=Confidence(0.85),
            results={'similarity_score': 0.85},
            metadata={'model': 'bert'}
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
        assert retrieved.id.value == sample_analysis.id.value
        assert retrieved.analysis_type == AnalysisType.SEMANTIC_SIMILARITY
        assert retrieved.status == AnalysisStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent(self, repository):
        """Test getting non-existent analysis."""
        retrieved = await repository.get_by_id('non-existent-id')
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_all_analyses(self, repository):
        """Test getting all analyses."""
        # Create and save multiple analyses
        analyses = []
        for i in range(3):
            analysis = Analysis(
                id=f'test-analysis-{i}',
                document_id='doc-123',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=AnalysisStatus.COMPLETED
            )
            await repository.save(analysis)
            analyses.append(analysis)

        all_analyses = await repository.get_all()
        assert len(all_analyses) == 3

        retrieved_ids = [a.id.value for a in all_analyses]
        expected_ids = [a.id.value for a in analyses]
        assert set(retrieved_ids) == set(expected_ids)

    @pytest.mark.asyncio
    async def test_get_by_document_id(self, repository):
        """Test getting analyses by document ID."""
        # Create analyses for different documents
        doc_ids = ['doc-1', 'doc-2', 'doc-1', 'doc-3']  # 2 for doc-1, 1 for doc-2, 1 for doc-3

        for i, doc_id in enumerate(doc_ids):
            analysis = Analysis(
                id=f'analysis-{i}',
                document_id=doc_id,
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=AnalysisStatus.COMPLETED
            )
            await repository.save(analysis)

        # Get analyses for doc-1
        doc_analyses = await repository.get_by_document_id('doc-1')
        assert len(doc_analyses) == 2
        for analysis in doc_analyses:
            assert analysis.document_id == 'doc-1'

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

        # Get failed analyses
        failed_analyses = await repository.get_by_status(AnalysisStatus.FAILED)
        assert len(failed_analyses) == 1
        assert failed_analyses[0].status == AnalysisStatus.FAILED

    @pytest.mark.asyncio
    async def test_get_by_analysis_type(self, repository):
        """Test getting analyses by analysis type."""
        types = [AnalysisType.SEMANTIC_SIMILARITY, AnalysisType.CODE_QUALITY, AnalysisType.SECURITY_SCAN, AnalysisType.SEMANTIC_SIMILARITY]

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
        assert len(semantic_analyses) == 2
        for analysis in semantic_analyses:
            assert analysis.analysis_type == AnalysisType.SEMANTIC_SIMILARITY

    @pytest.mark.asyncio
    async def test_delete_analysis(self, repository, sample_analysis):
        """Test deleting an analysis."""
        await repository.save(sample_analysis)
        assert len(repository._analyses) == 1

        result = await repository.delete(sample_analysis.id.value)
        assert result is True
        assert len(repository._analyses) == 0

        # Verify analysis is gone
        retrieved = await repository.get_by_id(sample_analysis.id.value)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_analysis(self, repository):
        """Test deleting non-existent analysis."""
        result = await repository.delete('non-existent-id')
        assert result is False

    @pytest.mark.asyncio
    async def test_analysis_with_metrics(self, repository):
        """Test analysis with performance metrics."""
        metrics = AnalysisMetrics(
            processing_time_seconds=2.5,
            memory_usage_mb=150.0,
            confidence_score=0.88
        )

        analysis = Analysis(
            id='metrics-analysis',
            document_id='doc-123',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
            status=AnalysisStatus.COMPLETED,
            metrics=metrics
        )

        await repository.save(analysis)

        retrieved = await repository.get_by_id('metrics-analysis')
        assert retrieved is not None
        assert retrieved.metrics == metrics
        assert retrieved.metrics.processing_time_seconds == 2.5

    @pytest.mark.asyncio
    async def test_analysis_with_complex_results(self, repository):
        """Test analysis with complex results data."""
        complex_results = {
            'similarity_score': 0.92,
            'matched_documents': ['doc-1', 'doc-2', 'doc-3'],
            'confidence_intervals': {'lower': 0.88, 'upper': 0.96},
            'processing_stats': {
                'tokens_processed': 2500,
                'model_used': 'sentence-transformers/all-MiniLM-L6-v2',
                'algorithm_version': '2.1.0'
            },
            'recommendations': [
                'Consider reviewing document doc-1 for consistency',
                'Document doc-2 has high similarity - potential duplicate content'
            ]
        }

        analysis = Analysis(
            id='complex-analysis',
            document_id='doc-main',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
            status=AnalysisStatus.COMPLETED,
            results=complex_results
        )

        await repository.save(analysis)

        retrieved = await repository.get_by_id('complex-analysis')
        assert retrieved is not None
        assert retrieved.results == complex_results
        assert retrieved.results['similarity_score'] == 0.92
        assert len(retrieved.results['matched_documents']) == 3


class TestSQLiteAnalysisRepository:
    """Test cases for SQLiteAnalysisRepository."""

    @pytest.fixture
    async def repository(self):
        """Create a fresh SQLite analysis repository for each test."""
        repo = SQLiteAnalysisRepository(':memory:')
        await repo.initialize()
        yield repo
        await repo.close()

    @pytest.fixture
    def sample_analysis(self):
        """Create a sample analysis for testing."""
        return Analysis(
            id='test-analysis-123',
            document_id='doc-456',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
            status=AnalysisStatus.COMPLETED,
            confidence=Confidence(0.85),
            results={'similarity_score': 0.85}
        )

    @pytest.mark.asyncio
    async def test_repository_creation(self, repository):
        """Test creating a SQLite analysis repository."""
        assert repository is not None
        assert isinstance(repository, AnalysisRepository)
        assert isinstance(repository, SQLiteAnalysisRepository)
        assert repository.database_path == ':memory:'

    @pytest.mark.asyncio
    async def test_save_and_retrieve_analysis_sqlite(self, repository, sample_analysis):
        """Test saving and retrieving an analysis with SQLite."""
        await repository.save(sample_analysis)

        retrieved = await repository.get_by_id(sample_analysis.id.value)

        assert retrieved is not None
        assert retrieved.id.value == sample_analysis.id.value
        assert retrieved.document_id == sample_analysis.document_id
        assert retrieved.analysis_type == sample_analysis.analysis_type
        assert retrieved.status == sample_analysis.status

    @pytest.mark.asyncio
    async def test_get_by_document_id_sqlite(self, repository):
        """Test getting analyses by document ID with SQLite."""
        # Create analyses for different documents
        for i in range(3):
            analysis = Analysis(
                id=f'analysis-{i}',
                document_id=f'doc-{i % 2}',  # 2 for doc-0, 1 for doc-1
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=AnalysisStatus.COMPLETED
            )
            await repository.save(analysis)

        doc_analyses = await repository.get_by_document_id('doc-0')
        assert len(doc_analyses) == 2
        for analysis in doc_analyses:
            assert analysis.document_id == 'doc-0'

    @pytest.mark.asyncio
    async def test_get_by_status_sqlite(self, repository):
        """Test getting analyses by status with SQLite."""
        for i, status in enumerate([AnalysisStatus.PENDING, AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]):
            analysis = Analysis(
                id=f'analysis-{i}',
                document_id='doc-123',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=status
            )
            await repository.save(analysis)

        completed_analyses = await repository.get_by_status(AnalysisStatus.COMPLETED)
        assert len(completed_analyses) == 1
        assert completed_analyses[0].status == AnalysisStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_get_by_analysis_type_sqlite(self, repository):
        """Test getting analyses by analysis type with SQLite."""
        types = [AnalysisType.SEMANTIC_SIMILARITY, AnalysisType.CODE_QUALITY, AnalysisType.SEMANTIC_SIMILARITY]

        for i, analysis_type in enumerate(types):
            analysis = Analysis(
                id=f'analysis-{i}',
                document_id='doc-123',
                analysis_type=analysis_type,
                status=AnalysisStatus.COMPLETED
            )
            await repository.save(analysis)

        semantic_analyses = await repository.get_by_analysis_type(AnalysisType.SEMANTIC_SIMILARITY)
        assert len(semantic_analyses) == 2
        for analysis in semantic_analyses:
            assert analysis.analysis_type == AnalysisType.SEMANTIC_SIMILARITY

    @pytest.mark.asyncio
    async def test_delete_analysis_sqlite(self, repository, sample_analysis):
        """Test deleting an analysis with SQLite."""
        await repository.save(sample_analysis)

        result = await repository.delete(sample_analysis.id.value)
        assert result is True

        retrieved = await repository.get_by_id(sample_analysis.id.value)
        assert retrieved is None


class TestAnalysisRepositoryIntegration:
    """Test integration between analysis repository and other components."""

    @pytest.mark.asyncio
    async def test_analysis_repository_with_document_repository(self):
        """Test analysis repository integration with document repository."""
        from ...infrastructure.repositories.document_repository import InMemoryDocumentRepository

        doc_repo = InMemoryDocumentRepository()
        analysis_repo = InMemoryAnalysisRepository()

        # Create a document
        doc = await doc_repo.save(Document(
            id='integration-doc',
            title='Integration Document',
            content='Test content',
            repository_id='integration-repo',
            author='integration-author'
        ))

        # Create analyses for the document
        analyses = []
        for i in range(2):
            analysis = Analysis(
                id=f'integration-analysis-{i}',
                document_id='integration-doc',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=AnalysisStatus.COMPLETED
            )
            await analysis_repo.save(analysis)
            analyses.append(analysis)

        # Verify the relationship
        doc_analyses = await analysis_repo.get_by_document_id('integration-doc')
        assert len(doc_analyses) == 2

        for analysis in doc_analyses:
            assert analysis.document_id == 'integration-doc'

    @pytest.mark.asyncio
    async def test_analysis_repository_workflow_simulation(self):
        """Test analysis repository in a typical workflow."""
        repo = InMemoryAnalysisRepository()

        # Simulate analysis workflow
        analysis_id = 'workflow-analysis'

        # 1. Create analysis (initial state)
        analysis = Analysis(
            id=analysis_id,
            document_id='doc-123',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
            status=AnalysisStatus.PENDING
        )
        await repo.save(analysis)

        # 2. Start analysis (running state)
        analysis.status = AnalysisStatus.RUNNING
        await repo.save(analysis)

        # 3. Complete analysis (completed state)
        analysis.status = AnalysisStatus.COMPLETED
        analysis.confidence = Confidence(0.88)
        analysis.results = {'score': 0.88}
        await repo.save(analysis)

        # Verify final state
        retrieved = await repo.get_by_id(analysis_id)
        assert retrieved.status == AnalysisStatus.COMPLETED
        assert retrieved.confidence.value == 0.88
        assert retrieved.results['score'] == 0.88

    @pytest.mark.asyncio
    async def test_analysis_repository_bulk_operations(self):
        """Test bulk operations on analysis repository."""
        repo = InMemoryAnalysisRepository()

        # Create multiple analyses
        analyses = []
        for i in range(50):
            analysis = Analysis(
                id=f'bulk-analysis-{i:03d}',
                document_id='bulk-doc',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=AnalysisStatus.COMPLETED,
                confidence=Confidence(0.8 + (i % 20) * 0.01)  # Vary confidence slightly
            )
            analyses.append(analysis)
            await repo.save(analysis)

        # Verify bulk save
        all_analyses = await repo.get_all()
        assert len(all_analyses) == 50

        # Test bulk query by document
        doc_analyses = await repo.get_by_document_id('bulk-doc')
        assert len(doc_analyses) == 50

        # Test bulk query by status
        completed_analyses = await repo.get_by_status(AnalysisStatus.COMPLETED)
        assert len(completed_analyses) == 50

    @pytest.mark.asyncio
    async def test_analysis_repository_performance_metrics(self):
        """Test analysis repository with performance metrics."""
        repo = InMemoryAnalysisRepository()

        # Create analyses with various performance metrics
        performance_scenarios = [
            {'time': 0.5, 'memory': 50.0, 'confidence': 0.95},  # Fast, low memory, high confidence
            {'time': 5.0, 'memory': 200.0, 'confidence': 0.85},  # Slow, high memory, medium confidence
            {'time': 15.0, 'memory': 500.0, 'confidence': 0.75},  # Very slow, very high memory, low confidence
        ]

        for i, scenario in enumerate(performance_scenarios):
            metrics = AnalysisMetrics(
                processing_time_seconds=scenario['time'],
                memory_usage_mb=scenario['memory'],
                confidence_score=scenario['confidence']
            )

            analysis = Analysis(
                id=f'perf-analysis-{i}',
                document_id='perf-doc',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=AnalysisStatus.COMPLETED,
                metrics=metrics
            )
            await repo.save(analysis)

        # Query and verify metrics
        all_analyses = await repo.get_all()
        assert len(all_analyses) == 3

        for analysis in all_analyses:
            assert analysis.metrics is not None
            assert analysis.metrics.processing_time_seconds > 0
            assert analysis.metrics.memory_usage_mb > 0
            assert 0 <= analysis.metrics.confidence_score <= 1


class TestAnalysisRepositoryErrorHandling:
    """Test error handling in analysis repository."""

    @pytest.mark.asyncio
    async def test_sqlite_repository_invalid_path(self):
        """Test SQLite repository with invalid database path."""
        with pytest.raises(Exception):
            repo = SQLiteAnalysisRepository('/invalid/path/database.db')
            await repo.initialize()

    @pytest.mark.asyncio
    async def test_repository_invalid_analysis_data(self):
        """Test repository handling of invalid analysis data."""
        repo = InMemoryAnalysisRepository()

        # Try to save analysis with invalid data
        try:
            invalid_analysis = Analysis(
                id='',  # Invalid empty ID
                document_id='doc-123',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=AnalysisStatus.PENDING
            )
            await repo.save(invalid_analysis)
        except ValueError:
            # Expected for invalid data
            pass

    @pytest.mark.asyncio
    async def test_repository_concurrent_analysis_operations(self):
        """Test concurrent analysis operations."""
        repo = InMemoryAnalysisRepository()

        async def create_and_save_analysis(i: int):
            analysis = Analysis(
                id=f'concurrent-analysis-{i}',
                document_id='concurrent-doc',
                analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
                status=AnalysisStatus.COMPLETED
            )
            await repo.save(analysis)
            return analysis

        # Create concurrent operations
        tasks = [create_and_save_analysis(i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        # Verify all analyses were created
        assert len(results) == 20

        all_analyses = await repo.get_all()
        assert len(all_analyses) == 20

        # Verify no duplicates
        analysis_ids = [a.id.value for a in all_analyses]
        assert len(set(analysis_ids)) == 20


class TestAnalysisRepositoryEdgeCases:
    """Test analysis repository edge cases."""

    @pytest.mark.asyncio
    async def test_empty_analysis_repository(self):
        """Test operations on empty analysis repository."""
        repo = InMemoryAnalysisRepository()

        # Operations on empty repository
        all_analyses = await repo.get_all()
        assert len(all_analyses) == 0

        retrieved = await repo.get_by_id('non-existent')
        assert retrieved is None

        doc_analyses = await repo.get_by_document_id('non-existent-doc')
        assert len(doc_analyses) == 0

        status_analyses = await repo.get_by_status(AnalysisStatus.PENDING)
        assert len(status_analyses) == 0

        type_analyses = await repo.get_by_analysis_type(AnalysisType.SEMANTIC_SIMILARITY)
        assert len(type_analyses) == 0

        delete_result = await repo.delete('non-existent')
        assert delete_result is False

    @pytest.mark.asyncio
    async def test_analysis_repository_special_data(self):
        """Test repository with special data types."""
        repo = InMemoryAnalysisRepository()

        # Create analysis with special characters and unicode
        special_analysis = Analysis(
            id='special-analysis-🚀',
            document_id='doc-ñáéíóú',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
            status=AnalysisStatus.COMPLETED,
            results={
                'special_field': 'value with @#$%^&*()',
                'unicode_content': '🚀 Analysis complete 📊',
                'nested_data': {
                    'array': [1, 'string', {'key': 'value'}],
                    'special_chars': 'ñáéíóú'
                }
            }
        )

        await repo.save(special_analysis)

        retrieved = await repo.get_by_id('special-analysis-🚀')
        assert retrieved is not None
        assert '🚀' in retrieved.id.value
        assert 'ñáéíóú' in retrieved.document_id
        assert retrieved.results['unicode_content'] == '🚀 Analysis complete 📊'

    @pytest.mark.asyncio
    async def test_analysis_repository_large_result_sets(self):
        """Test repository with large result sets."""
        repo = InMemoryAnalysisRepository()

        # Create analyses with large result data
        large_results = {
            'similarity_matrix': [[0.8 + i * 0.01] * 1000 for i in range(100)],  # 100x1000 matrix
            'matched_documents': [f'doc-{i}' for i in range(1000)],  # 1000 matches
            'detailed_scores': {f'doc-{i}': 0.5 + (i % 50) * 0.01 for i in range(500)},  # 500 detailed scores
            'processing_metadata': {
                'algorithm_steps': [f'step-{i}' for i in range(100)],
                'intermediate_results': [{'step': i, 'data': 'x' * 1000} for i in range(50)]
            }
        }

        analysis = Analysis(
            id='large-results-analysis',
            document_id='large-doc',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
            status=AnalysisStatus.COMPLETED,
            results=large_results
        )

        await repo.save(analysis)

        retrieved = await repo.get_by_id('large-results-analysis')
        assert retrieved is not None
        assert len(retrieved.results['matched_documents']) == 1000
        assert len(retrieved.results['detailed_scores']) == 500
