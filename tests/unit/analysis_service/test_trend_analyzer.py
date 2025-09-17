"""Tests for trend analysis functionality in Analysis Service.

Tests the trend analyzer module and its integration with the analysis service.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from services.analysis_service.modules.trend_analyzer import (
    TrendAnalyzer,
    analyze_document_trends,
    analyze_portfolio_trends,
    TREND_ANALYSIS_AVAILABLE
)


@pytest.fixture
def sample_analysis_results():
    """Create sample historical analysis results for testing."""
    base_date = datetime.now()

    return [
        {
            "document_id": "doc1",
            "timestamp": (base_date - timedelta(days=30)).isoformat(),
            "total_findings": 5,
            "critical_findings": 1,
            "high_findings": 2,
            "medium_findings": 1,
            "low_findings": 1,
            "quality_score": 0.75,
            "readability_score": 0.8,
            "sentiment_score": 0.7,
            "consistency_score": 0.85,
            "findings": [
                {"type": "drift", "severity": "high"},
                {"type": "consistency", "severity": "medium"},
                {"type": "missing_doc", "severity": "low"}
            ]
        },
        {
            "document_id": "doc1",
            "timestamp": (base_date - timedelta(days=20)).isoformat(),
            "total_findings": 7,
            "critical_findings": 2,
            "high_findings": 3,
            "medium_findings": 1,
            "low_findings": 1,
            "quality_score": 0.70,
            "readability_score": 0.75,
            "sentiment_score": 0.65,
            "consistency_score": 0.80,
            "findings": [
                {"type": "drift", "severity": "critical"},
                {"type": "consistency", "severity": "high"},
                {"type": "missing_doc", "severity": "medium"}
            ]
        },
        {
            "document_id": "doc1",
            "timestamp": (base_date - timedelta(days=10)).isoformat(),
            "total_findings": 4,
            "critical_findings": 0,
            "high_findings": 1,
            "medium_findings": 2,
            "low_findings": 1,
            "quality_score": 0.82,
            "readability_score": 0.85,
            "sentiment_score": 0.8,
            "consistency_score": 0.88,
            "findings": [
                {"type": "consistency", "severity": "high"},
                {"type": "missing_doc", "severity": "medium"}
            ]
        },
        {
            "document_id": "doc1",
            "timestamp": base_date.isoformat(),
            "total_findings": 3,
            "critical_findings": 0,
            "high_findings": 0,
            "medium_findings": 2,
            "low_findings": 1,
            "quality_score": 0.85,
            "readability_score": 0.88,
            "sentiment_score": 0.85,
            "consistency_score": 0.9,
            "findings": [
                {"type": "consistency", "severity": "medium"},
                {"type": "missing_doc", "severity": "low"}
            ]
        }
    ]


@pytest.fixture
def portfolio_analysis_results():
    """Create sample portfolio analysis results for testing."""
    base_date = datetime.now()

    results = []
    for i in range(3):  # 3 documents
        for j in range(4):  # 4 time points each
            results.append({
                "document_id": f"doc{i+1}",
                "timestamp": (base_date - timedelta(days=(j+1)*7)).isoformat(),
                "total_findings": max(1, 5 - j + i),  # Varying patterns
                "quality_score": min(0.95, 0.7 + (j * 0.05) - (i * 0.1)),
                "findings": [{"type": "drift", "severity": "medium"}]
            })

    return results


class TestTrendAnalyzer:
    """Test the TrendAnalyzer class."""

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization of the trend analyzer."""
        analyzer = TrendAnalyzer()
        success = analyzer._initialize_analyzer()
        assert success is True
        assert analyzer.initialized is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure when dependencies are not available."""
        original_available = TREND_ANALYSIS_AVAILABLE

        with patch('services.analysis_service.modules.trend_analyzer.TREND_ANALYSIS_AVAILABLE', False):
            analyzer = TrendAnalyzer()
            success = analyzer._initialize_analyzer()
            assert success is False
            assert analyzer.initialized is False

    @pytest.mark.asyncio
    async def test_extract_historical_data(self, sample_analysis_results):
        """Test extraction of historical data into DataFrame."""
        analyzer = TrendAnalyzer()

        df = analyzer._extract_historical_data(sample_analysis_results)

        assert len(df) == 4
        assert 'quality_score' in df.columns
        assert 'total_findings' in df.columns
        assert df.index.name == 'timestamp'
        assert df.index.is_monotonic_increasing  # Should be sorted by timestamp

    @pytest.mark.asyncio
    async def test_extract_historical_data_empty(self):
        """Test extraction with empty analysis results."""
        analyzer = TrendAnalyzer()

        df = analyzer._extract_historical_data([])
        assert df.empty

    @pytest.mark.asyncio
    async def test_analyze_trend_patterns_improving_quality(self, sample_analysis_results):
        """Test trend pattern analysis with improving quality."""
        analyzer = TrendAnalyzer()

        df = analyzer._extract_historical_data(sample_analysis_results)
        result = analyzer._analyze_trend_patterns(df)

        assert 'trend_direction' in result
        assert 'confidence' in result
        assert 'patterns' in result
        assert 'volatility' in result
        assert result['data_points'] == 4
        # Quality scores are improving: 0.75 -> 0.70 -> 0.82 -> 0.85
        # So trend should be improving or stable

    @pytest.mark.asyncio
    async def test_analyze_trend_patterns_insufficient_data(self):
        """Test trend pattern analysis with insufficient data."""
        analyzer = TrendAnalyzer()

        # Only one data point
        minimal_results = [{
            "document_id": "doc1",
            "timestamp": datetime.now().isoformat(),
            "quality_score": 0.8
        }]

        df = analyzer._extract_historical_data(minimal_results)
        result = analyzer._analyze_trend_patterns(df)

        assert result['trend_direction'] == 'insufficient_data'
        assert result['confidence'] == 0.0

    @pytest.mark.asyncio
    async def test_predict_future_issues(self, sample_analysis_results):
        """Test future issue prediction."""
        analyzer = TrendAnalyzer()

        df = analyzer._extract_historical_data(sample_analysis_results)
        predictions = analyzer._predict_future_issues(df, prediction_days=7)

        assert 'predictions' in predictions
        assert 'confidence' in predictions
        assert predictions['prediction_horizon_days'] == 7

        # Should have quality score predictions
        quality_pred = predictions['predictions'].get('quality_score', {})
        if quality_pred:
            assert 'predicted_values' in quality_pred
            assert 'current_trend' in quality_pred
            assert len(quality_pred['predicted_values']) == 7

    @pytest.mark.asyncio
    async def test_identify_risk_areas_declining_quality(self, sample_analysis_results):
        """Test risk area identification for declining quality."""
        analyzer = TrendAnalyzer()

        df = analyzer._extract_historical_data(sample_analysis_results)

        # Create mock predictions with declining trend
        predictions = {
            'predictions': {
                'quality_score': {
                    'current_trend': 'declining',
                    'predicted_values': [0.6, 0.55, 0.5]
                }
            }
        }

        risk_areas = analyzer._identify_risk_areas(df, predictions)

        assert len(risk_areas) > 0
        assert any(area['risk_type'] == 'quality_decline' for area in risk_areas)

    @pytest.mark.asyncio
    async def test_identify_risk_areas_increasing_findings(self, sample_analysis_results):
        """Test risk area identification for increasing findings."""
        analyzer = TrendAnalyzer()

        df = analyzer._extract_historical_data(sample_analysis_results)

        # Create mock predictions with increasing findings
        predictions = {
            'predictions': {
                'drift_findings': {
                    'trend': 'increasing',
                    'predicted_count': 8.5
                }
            }
        }

        risk_areas = analyzer._identify_risk_areas(df, predictions)

        assert len(risk_areas) > 0
        assert any('increasing' in area['risk_type'] for area in risk_areas)

    @pytest.mark.asyncio
    async def test_generate_trend_insights_improving(self):
        """Test insight generation for improving trends."""
        analyzer = TrendAnalyzer()

        analysis_results = {
            'trend_direction': 'improving',
            'patterns': {
                'quality_trend': {'direction': 'improving', 'confidence': 0.8}
            },
            'predictions': {}
        }

        insights = analyzer._generate_trend_insights(analysis_results)

        assert len(insights) > 0
        assert any('improving' in insight.lower() for insight in insights)

    @pytest.mark.asyncio
    async def test_generate_trend_insights_declining(self):
        """Test insight generation for declining trends."""
        analyzer = TrendAnalyzer()

        analysis_results = {
            'trend_direction': 'declining',
            'patterns': {
                'quality_trend': {'direction': 'declining', 'confidence': 0.7}
            },
            'predictions': {}
        }

        insights = analyzer._generate_trend_insights(analysis_results)

        assert len(insights) > 0
        assert any('declining' in insight.lower() or 'implement' in insight.lower() for insight in insights)

    @pytest.mark.asyncio
    async def test_analyze_documentation_trends_full(self, sample_analysis_results):
        """Test full document trend analysis."""
        analyzer = TrendAnalyzer()

        result = await analyzer.analyze_documentation_trends(
            document_id="doc1",
            analysis_results=sample_analysis_results,
            prediction_days=14,
            include_predictions=True
        )

        assert result['document_id'] == 'doc1'
        assert 'trend_direction' in result
        assert 'confidence' in result
        assert 'patterns' in result
        assert 'predictions' in result
        assert 'risk_areas' in result
        assert 'insights' in result
        assert 'processing_time' in result
        assert result['data_points'] == 4

    @pytest.mark.asyncio
    async def test_analyze_documentation_trends_insufficient_data(self):
        """Test trend analysis with insufficient data."""
        analyzer = TrendAnalyzer()

        minimal_results = [{
            "document_id": "doc1",
            "timestamp": datetime.now().isoformat(),
            "quality_score": 0.8
        }]

        result = await analyzer.analyze_documentation_trends(
            document_id="doc1",
            analysis_results=minimal_results
        )

        assert result['document_id'] == 'doc1'
        assert result['trend_direction'] == 'insufficient_data'
        assert result['data_points'] == 1
        assert 'Insufficient historical data' in result['insights'][0]

    @pytest.mark.asyncio
    async def test_analyze_portfolio_trends(self, portfolio_analysis_results):
        """Test portfolio trend analysis."""
        analyzer = TrendAnalyzer()

        result = await analyzer.analyze_portfolio_trends(
            analysis_results=portfolio_analysis_results,
            group_by='document_id',
            prediction_days=7
        )

        assert 'portfolio_summary' in result
        assert 'document_trends' in result
        assert 'processing_time' in result

        summary = result['portfolio_summary']
        assert 'total_documents' in summary
        assert 'analyzed_documents' in summary
        assert 'overall_trend' in summary

        # Should have 3 documents with trends
        assert len(result['document_trends']) == 3

    @pytest.mark.asyncio
    async def test_analyze_portfolio_trends_insufficient_data(self):
        """Test portfolio trend analysis with insufficient data."""
        analyzer = TrendAnalyzer()

        minimal_results = [{
            "document_id": "doc1",
            "timestamp": datetime.now().isoformat(),
            "quality_score": 0.8
        }]

        result = await analyzer.analyze_portfolio_trends(
            analysis_results=minimal_results
        )

        assert result['portfolio_summary']['total_documents'] == 1
        assert result['portfolio_summary']['analyzed_documents'] == 0
        assert result['portfolio_summary']['overall_trend'] == 'insufficient_data'


@pytest.mark.asyncio
class TestTrendAnalysisIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_analyze_document_trends_function(self, sample_analysis_results):
        """Test the convenience function for document trend analysis."""
        with patch('services.analysis_service.modules.trend_analyzer.trend_analyzer') as mock_analyzer:
            mock_analyzer.analyze_documentation_trends.return_value = {
                'document_id': 'doc1',
                'trend_direction': 'improving',
                'confidence': 0.8,
                'patterns': {'quality_trend': {'direction': 'improving'}},
                'predictions': {},
                'risk_areas': [],
                'insights': ['Quality is improving steadily'],
                'analysis_period_days': 30,
                'data_points': 4,
                'volatility': 0.05,
                'processing_time': 1.2,
                'analysis_timestamp': 1234567890
            }

            result = await analyze_document_trends(
                document_id="doc1",
                analysis_results=sample_analysis_results,
                prediction_days=14
            )

            assert result['document_id'] == 'doc1'
            assert result['trend_direction'] == 'improving'
            assert result['confidence'] == 0.8
            mock_analyzer.analyze_documentation_trends.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_portfolio_trends_function(self, portfolio_analysis_results):
        """Test the convenience function for portfolio trend analysis."""
        with patch('services.analysis_service.modules.trend_analyzer.trend_analyzer') as mock_analyzer:
            mock_analyzer.analyze_portfolio_trends.return_value = {
                'portfolio_summary': {
                    'total_documents': 3,
                    'analyzed_documents': 3,
                    'overall_trend': 'stable',
                    'average_confidence': 0.75
                },
                'document_trends': [],
                'processing_time': 2.1,
                'analysis_timestamp': 1234567890
            }

            result = await analyze_portfolio_trends(
                analysis_results=portfolio_analysis_results,
                group_by='document_id'
            )

            assert result['portfolio_summary']['total_documents'] == 3
            assert result['portfolio_summary']['overall_trend'] == 'stable'
            mock_analyzer.analyze_portfolio_trends.assert_called_once()


class TestTrendAnalysisHandlers:
    """Test the analysis handlers integration."""

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        client = Mock()
        client.doc_store_url.return_value = "http://docstore:5000"
        client.get_json = Mock()
        return client

    @pytest.mark.asyncio
    async def test_handle_trend_analysis_success(self, mock_service_client, sample_analysis_results):
        """Test successful trend analysis handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import TrendAnalysisRequest

        with patch('services.analysis_service.modules.analysis_handlers.analyze_document_trends') as mock_analyze:

            mock_analyze.return_value = {
                'document_id': 'doc1',
                'trend_direction': 'improving',
                'confidence': 0.8,
                'patterns': {'quality_trend': {'direction': 'improving', 'slope': 0.002}},
                'predictions': {'predictions': {'quality_score': {'predicted_values': [0.87, 0.89]}}},
                'risk_areas': [{'risk_type': 'minor_issue', 'severity': 'low'}],
                'insights': ['Quality is trending positively'],
                'analysis_period_days': 30,
                'data_points': 4,
                'volatility': 0.05,
                'processing_time': 1.5,
                'analysis_timestamp': 1234567890
            }

            request = TrendAnalysisRequest(
                document_id="doc1",
                analysis_results=sample_analysis_results,
                prediction_days=14,
                include_predictions=True
            )

            result = await AnalysisHandlers.handle_trend_analysis(request)

            assert result.document_id == 'doc1'
            assert result.trend_direction == 'improving'
            assert result.confidence == 0.8
            assert len(result.insights) > 0
            assert result.data_points == 4
            assert result.processing_time == 1.5

    @pytest.mark.asyncio
    async def test_handle_portfolio_trend_analysis_success(self, mock_service_client, portfolio_analysis_results):
        """Test successful portfolio trend analysis handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import PortfolioTrendAnalysisRequest

        with patch('services.analysis_service.modules.analysis_handlers.analyze_portfolio_trends') as mock_analyze:

            mock_analyze.return_value = {
                'portfolio_summary': {
                    'total_documents': 3,
                    'analyzed_documents': 3,
                    'overall_trend': 'stable',
                    'average_confidence': 0.75,
                    'trend_distribution': {'improving': 1, 'stable': 2},
                    'high_risk_documents': ['doc2']
                },
                'document_trends': [
                    {'document_id': 'doc1', 'trend_direction': 'improving'},
                    {'document_id': 'doc2', 'trend_direction': 'declining'},
                    {'document_id': 'doc3', 'trend_direction': 'stable'}
                ],
                'processing_time': 2.1,
                'analysis_timestamp': 1234567890
            }

            request = PortfolioTrendAnalysisRequest(
                analysis_results=portfolio_analysis_results,
                group_by='document_id',
                prediction_days=7
            )

            result = await AnalysisHandlers.handle_portfolio_trend_analysis(request)

            assert result.portfolio_summary['total_documents'] == 3
            assert result.portfolio_summary['analyzed_documents'] == 3
            assert result.portfolio_summary['overall_trend'] == 'stable'
            assert len(result.document_trends) == 3
            assert result.processing_time == 2.1

    @pytest.mark.asyncio
    async def test_handle_trend_analysis_error(self, mock_service_client, sample_analysis_results):
        """Test trend analysis error handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import TrendAnalysisRequest

        with patch('services.analysis_service.modules.analysis_handlers.analyze_document_trends') as mock_analyze:

            mock_analyze.side_effect = Exception("Analysis failed")

            request = TrendAnalysisRequest(
                document_id="doc1",
                analysis_results=sample_analysis_results
            )

            result = await AnalysisHandlers.handle_trend_analysis(request)

            assert result.document_id == 'doc1'
            assert result.trend_direction == 'error'
            assert result.confidence == 0.0
            assert 'Analysis failed due to error' in result.insights[0]


if __name__ == "__main__":
    pytest.main([__file__])
