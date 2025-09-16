"""Analytics domain tests.

Comprehensive tests for analytics functionality, metrics calculation, and insights generation.
"""
import pytest
from unittest.mock import patch, Mock
from tests.unit.doc_store.conftest import BaseTestCase


@pytest.mark.unit
@pytest.mark.domain
class TestAnalyticsRepository(BaseTestCase):
    """Test AnalyticsRepository functionality."""

    @pytest.fixture
    def repository(self):
        """Create analytics repository instance."""
        from services.doc_store.domain.analytics.repository import AnalyticsRepository
        return AnalyticsRepository()

    @patch('services.doc_store.domain.analytics.repository.execute_query')
    def test_get_basic_counts(self, mock_execute, repository):
        """Test getting basic entity counts."""
        # Mock the query results for each table
        mock_execute.side_effect = [
            {'count': 100},  # documents
            {'count': 50},   # analyses
            {'count': 10},   # ensembles
            {'count': 25},   # style_examples
            {'count': 5},    # versions
            {'count': 75}    # tags
        ]

        counts = repository.get_basic_counts()

        assert counts['documents'] == 100
        assert counts['analyses'] == 50
        assert counts['ensembles'] == 10
        assert counts['style_examples'] == 25
        assert counts['versions'] == 5
        assert counts['tags'] == 75

    @patch('services.doc_store.domain.analytics.repository.execute_query')
    def test_get_storage_stats(self, mock_execute, repository):
        """Test getting storage statistics."""
        # Mock document sizes query
        mock_sizes = [
            {'size': 1000},
            {'size': 2000},
            {'size': 1500}
        ]
        mock_execute.return_value = mock_sizes

        stats = repository.get_storage_stats()

        assert stats['total_size_bytes'] == 4500
        assert stats['avg_document_size'] == 1500  # 4500 / 3
        assert stats['largest_document'] == 2000
        assert stats['smallest_document'] == 1000
        assert 'size_distribution' in stats

    @patch('services.doc_store.domain.analytics.repository.execute_query')
    @patch('services.doc_store.logic.compute_quality_flags')
    def test_get_quality_metrics(self, mock_compute_flags, mock_execute, repository):
        """Test getting quality metrics."""
        # Mock document queries
        mock_docs = [
            {'id': 'doc1', 'content_hash': 'hash1', 'metadata': '{"type": "test"}', 'created_at': '2024-01-01T00:00:00'},
            {'id': 'doc2', 'content_hash': 'hash2', 'metadata': '{"type": "api"}', 'created_at': '2024-01-01T01:00:00'}
        ]
        mock_execute.side_effect = [
            mock_docs,  # quality analysis docs
            [{'content_type': 'test', 'count': 1}, {'content_type': 'api', 'count': 1}]  # content type distribution
        ]

        # Mock the compute_quality_flags function
        mock_compute_flags.return_value = []

        metrics = repository.get_quality_metrics()

        assert 'stale_documents' in metrics
        assert 'redundant_documents' in metrics
        assert 'content_type_distribution' in metrics
        assert metrics['content_type_distribution']['test'] == 1
        assert metrics['content_type_distribution']['api'] == 1

    @patch('services.doc_store.domain.analytics.repository.execute_query')
    def test_get_temporal_trends(self, mock_execute, repository):
        """Test getting temporal trends."""
        mock_doc_counts = [
            {'date': '2024-01-01', 'count': 10},
            {'date': '2024-01-02', 'count': 15}
        ]
        mock_analysis_counts = [
            {'date': '2024-01-01', 'count': 5},
            {'date': '2024-01-02', 'count': 8}
        ]

        mock_execute.side_effect = [mock_doc_counts, mock_analysis_counts]

        trends = repository.get_temporal_trends(days_back=7)

        assert 'daily_document_creation' in trends
        assert 'daily_analysis_creation' in trends
        assert trends['daily_document_creation']['2024-01-01'] == 10
        assert trends['daily_analysis_creation']['2024-01-02'] == 8
        assert 'growth_rate' in trends

    @patch('services.doc_store.domain.analytics.repository.execute_query')
    def test_get_content_insights(self, mock_execute, repository):
        """Test getting content insights."""
        mock_languages = [
            {'language': 'python', 'count': 20},
            {'language': 'javascript', 'count': 15}
        ]
        mock_tags = [
            {'tag': 'api', 'count': 10},
            {'tag': 'documentation', 'count': 8}
        ]

        mock_execute.side_effect = [
            mock_languages,  # languages
            {'count': 100},  # total docs
            {'count': 80},   # analyzed docs
            mock_tags        # popular tags
        ]

        insights = repository.get_content_insights()

        assert insights['top_languages']['python'] == 20
        assert insights['analysis_coverage'] == 80.0  # 80/100 * 100
        assert insights['popular_tags']['api'] == 10

    @patch('services.doc_store.domain.analytics.repository.execute_query')
    def test_get_relationship_insights(self, mock_execute, repository):
        """Test getting relationship insights."""
        mock_relationships = [
            {'source_document_id': 'doc1', 'target_document_id': 'doc2', 'relationship_type': 'references'},
            {'source_document_id': 'doc2', 'target_document_id': 'doc3', 'relationship_type': 'extends'}
        ]

        mock_execute.side_effect = [
            {'count': 10},     # total relationships
            [{'relationship_type': 'references', 'count': 6}, {'relationship_type': 'extends', 'count': 4}],  # type distribution
            [{'document_id': 'doc1', 'connections': 5}, {'document_id': 'doc2', 'connections': 3}]  # most connected
        ]

        insights = repository.get_relationship_insights()

        assert insights['total_relationships'] == 10
        assert insights['relationship_types']['references'] == 6
        assert len(insights['most_connected_documents']) == 2
        assert insights['most_connected_documents'][0]['document_id'] == 'doc1'

    def test_generate_comprehensive_analytics(self, repository):
        """Test generating comprehensive analytics."""
        # Mock all the component methods
        with patch.object(repository, 'get_basic_counts', return_value={
            'documents': 100, 'analyses': 50, 'ensembles': 10, 'style_examples': 25, 'versions': 5, 'tags': 75
        }), \
             patch.object(repository, 'get_storage_stats', return_value={'total_size_bytes': 100000}), \
             patch.object(repository, 'get_quality_metrics', return_value={'stale_documents': 10}), \
             patch.object(repository, 'get_temporal_trends', return_value={'growth_rate': 0.1}), \
             patch.object(repository, 'get_content_insights', return_value={'analysis_coverage': 80.0}), \
             patch.object(repository, 'get_relationship_insights', return_value={'total_relationships': 25}):

            analytics = repository.generate_comprehensive_analytics(days_back=7)

            assert analytics.total_documents == 100
            assert analytics.total_analyses == 50
            assert analytics.storage_stats['total_size_bytes'] == 100000
            assert analytics.quality_metrics['stale_documents'] == 10
            assert analytics.temporal_trends['growth_rate'] == 0.1
            assert analytics.content_insights['analysis_coverage'] == 80.0
            assert analytics.relationship_insights['total_relationships'] == 25


@pytest.mark.unit
@pytest.mark.domain
class TestAnalyticsService(BaseTestCase):
    """Test AnalyticsService functionality."""

    @pytest.fixture
    def service(self):
        """Create analytics service instance."""
        from services.doc_store.domain.analytics.service import AnalyticsService
        return AnalyticsService()

    @pytest.fixture
    def mock_repository(self, service):
        """Mock the repository for isolated testing."""
        with patch.object(service, 'repository') as mock_repo:
            yield mock_repo

    def test_generate_analytics_valid_days(self, service, mock_repository):
        """Test analytics generation with valid days parameter."""
        mock_analytics = Mock()
        mock_analytics.total_documents = 100
        mock_repository.generate_comprehensive_analytics.return_value = mock_analytics

        result = service.generate_analytics(days_back=30)

        assert result.total_documents == 100
        mock_repository.generate_comprehensive_analytics.assert_called_once_with(30)

    def test_generate_analytics_invalid_days(self, service):
        """Test analytics generation with invalid days parameter."""
        with pytest.raises(ValueError, match="days_back must be positive"):
            service.generate_analytics(days_back=0)

        with pytest.raises(ValueError, match="days_back cannot exceed 365"):
            service.generate_analytics(days_back=400)

    def test_get_basic_counts(self, service, mock_repository):
        """Test getting basic counts."""
        mock_repository.get_basic_counts.return_value = {
            'documents': 100, 'analyses': 50, 'ensembles': 10,
            'style_examples': 25, 'versions': 5, 'tags': 75
        }

        counts = service.get_basic_counts()

        assert counts['total_documents'] == 100
        assert counts['total_analyses'] == 50
        assert counts['total_ensembles'] == 10
        assert counts['total_style_examples'] == 25
        assert counts['total_versions'] == 5
        assert counts['total_tags'] == 75

    def test_get_quality_metrics_with_calculations(self, service, mock_repository):
        """Test quality metrics with percentage calculations."""
        mock_metrics = {
            'stale_documents': 10,
            'redundant_documents': 5,
            'orphaned_analyses': 0
        }
        mock_repository.get_basic_counts.return_value = {'documents': 100}
        mock_repository.get_quality_metrics.return_value = mock_metrics

        result = service.get_quality_metrics()

        assert result['stale_documents'] == 10
        assert result['redundant_documents'] == 5
        assert result['stale_percentage'] == 10.0  # 10/100 * 100
        assert result['redundant_percentage'] == 5.0  # 5/100 * 100
        assert result['analyzed_percentage'] == 100.0  # (100-0)/100 * 100

    def test_get_analytics_summary_comprehensive(self, service, mock_repository):
        """Test comprehensive analytics summary generation."""
        # Mock analytics data
        mock_analytics = Mock()
        mock_analytics.total_documents = 100
        mock_analytics.total_analyses = 50
        mock_analytics.storage_stats = {'total_size_bytes': 1048576, 'avg_document_size': 1024}  # 1MB total, 1KB avg
        mock_analytics.quality_metrics = {'stale_documents': 15, 'stale_percentage': 15.0}
        mock_analytics.content_insights = {'analysis_coverage': 40.0}
        mock_analytics.relationship_insights = {'total_relationships': 5}

        mock_repository.generate_comprehensive_analytics.return_value = mock_analytics

        summary = service.get_analytics_summary()

        # Check overview section
        assert summary['overview']['total_documents'] == 100
        assert summary['overview']['total_analyses'] == 50
        assert summary['overview']['analysis_coverage'] == '40.0%'  # 40/100 * 100

        # Check quality section
        assert summary['quality']['stale_documents'] == 15
        assert summary['quality']['quality_score'] == "Good"  # < 20% stale

        # Check storage section
        assert summary['storage']['total_size_mb'] == 1.0  # 1048576 / (1024*1024)
        assert summary['storage']['avg_size_kb'] == 1.0    # 1024 / 1024

        # Check insights section
        assert len(summary['insights']) > 0
        # Should have insights for low analysis coverage and low connectivity
        insight_titles = [i['title'] for i in summary['insights']]
        assert "Low Analysis Coverage" in insight_titles
        assert "Low Connectivity" in insight_titles


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.domain
class TestAnalyticsHandlers(BaseTestCase):
    """Test AnalyticsHandlers functionality."""

    @pytest.fixture
    def handlers(self):
        """Create analytics handlers instance."""
        from services.doc_store.domain.analytics.handlers import AnalyticsHandlers
        return AnalyticsHandlers()

    @pytest.fixture
    def mock_service(self, handlers):
        """Mock the service for isolated testing."""
        with patch.object(handlers, 'service') as mock_svc:
            yield mock_svc

    async def test_handle_get_analytics_success(self, handlers, mock_service):
        """Test successful analytics retrieval."""
        mock_analytics = Mock()
        mock_analytics.total_documents = 100
        mock_analytics.total_analyses = 50
        mock_analytics.to_dict.return_value = {
            'total_documents': 100,
            'total_analyses': 50,
            'storage_stats': {'total_size_bytes': 1000000},
            'quality_metrics': {'stale_documents': 10},
            'temporal_trends': {'growth_rate': 0.05},
            'content_insights': {'analysis_coverage': 80.0},
            'relationship_insights': {'total_relationships': 25}
        }

        mock_service.generate_analytics.return_value = mock_analytics

        result = await handlers.handle_get_analytics(days_back=30)

        self.assert_success_response(result)
        assert result['data']['total_documents'] == 100
        assert result['data']['total_analyses'] == 50

    async def test_handle_get_analytics_summary_success(self, handlers, mock_service):
        """Test successful analytics summary retrieval."""
        mock_summary = {
            'overview': {'total_documents': 100, 'total_analyses': 50},
            'quality': {'stale_documents': 10},
            'storage': {'total_size_mb': 1.0},
            'insights': []
        }
        mock_service.get_analytics_summary.return_value = mock_summary

        result = await handlers.handle_get_analytics_summary()

        self.assert_success_response(result)
        assert result['data']['overview']['total_documents'] == 100
        assert result['data']['quality']['stale_documents'] == 10

    async def test_handle_get_analytics_invalid_days(self, handlers, mock_service):
        """Test analytics with invalid days parameter."""
        def mock_generate_analytics(days_back):
            if days_back <= 0:
                raise ValueError("days_back must be positive")
            return Mock()

        mock_service.generate_analytics.side_effect = mock_generate_analytics

        result = await handlers.handle_get_analytics(days_back=-1)

        assert result['success'] is False
        assert "positive" in result['message']
