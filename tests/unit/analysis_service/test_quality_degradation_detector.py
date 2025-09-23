"""Tests for quality degradation detection functionality in Analysis Service.

Tests the quality degradation detector module and its integration with the analysis service.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from services.analysis_service.modules.quality_degradation_detector import (
    QualityDegradationDetector,
    detect_document_degradation,
    monitor_portfolio_degradation,
    QUALITY_DEGRADATION_AVAILABLE
)


@pytest.fixture
def sample_analysis_history():
    """Create sample analysis history for testing."""
    base_date = datetime.now()

    return [
        {
            'timestamp': (base_date - timedelta(days=90)).isoformat(),
            'quality_score': 0.85,
            'total_findings': 3,
            'critical_findings': 0,
            'high_findings': 1,
            'sentiment_score': 0.8,
            'readability_score': 0.88
        },
        {
            'timestamp': (base_date - timedelta(days=75)).isoformat(),
            'quality_score': 0.83,
            'total_findings': 4,
            'critical_findings': 0,
            'high_findings': 1,
            'sentiment_score': 0.79,
            'readability_score': 0.86
        },
        {
            'timestamp': (base_date - timedelta(days=60)).isoformat(),
            'quality_score': 0.80,
            'total_findings': 6,
            'critical_findings': 1,
            'high_findings': 2,
            'sentiment_score': 0.77,
            'readability_score': 0.84
        },
        {
            'timestamp': (base_date - timedelta(days=45)).isoformat(),
            'quality_score': 0.78,
            'total_findings': 7,
            'critical_findings': 1,
            'high_findings': 2,
            'sentiment_score': 0.75,
            'readability_score': 0.82
        },
        {
            'timestamp': (base_date - timedelta(days=30)).isoformat(),
            'quality_score': 0.76,
            'total_findings': 8,
            'critical_findings': 2,
            'high_findings': 3,
            'sentiment_score': 0.73,
            'readability_score': 0.80
        },
        {
            'timestamp': (base_date - timedelta(days=15)).isoformat(),
            'quality_score': 0.74,
            'total_findings': 9,
            'critical_findings': 2,
            'high_findings': 3,
            'sentiment_score': 0.71,
            'readability_score': 0.78
        },
        {
            'timestamp': base_date.isoformat(),
            'quality_score': 0.72,
            'total_findings': 10,
            'critical_findings': 3,
            'high_findings': 4,
            'sentiment_score': 0.69,
            'readability_score': 0.76
        }
    ]


@pytest.fixture
def portfolio_documents():
    """Create sample portfolio of documents for testing."""
    base_date = datetime.now()

    return [
        {
            'document_id': 'doc1',
            'analysis_history': [
                {
                    'timestamp': (base_date - timedelta(days=60)).isoformat(),
                    'quality_score': 0.85,
                    'total_findings': 3
                },
                {
                    'timestamp': (base_date - timedelta(days=30)).isoformat(),
                    'quality_score': 0.78,
                    'total_findings': 7
                },
                {
                    'timestamp': base_date.isoformat(),
                    'quality_score': 0.72,
                    'total_findings': 10
                }
            ]
        },
        {
            'document_id': 'doc2',
            'analysis_history': [
                {
                    'timestamp': (base_date - timedelta(days=60)).isoformat(),
                    'quality_score': 0.82,
                    'total_findings': 4
                },
                {
                    'timestamp': (base_date - timedelta(days=30)).isoformat(),
                    'quality_score': 0.85,
                    'total_findings': 3
                },
                {
                    'timestamp': base_date.isoformat(),
                    'quality_score': 0.88,
                    'total_findings': 2
                }
            ]
        },
        {
            'document_id': 'doc3',
            'analysis_history': [
                {
                    'timestamp': (base_date - timedelta(days=60)).isoformat(),
                    'quality_score': 0.90,
                    'total_findings': 1
                },
                {
                    'timestamp': (base_date - timedelta(days=30)).isoformat(),
                    'quality_score': 0.88,
                    'total_findings': 2
                },
                {
                    'timestamp': base_date.isoformat(),
                    'quality_score': 0.85,
                    'total_findings': 3
                }
            ]
        }
    ]


class TestQualityDegradationDetector:
    """Test the QualityDegradationDetector class."""

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization of the quality degradation detector."""
        detector = QualityDegradationDetector()
        success = detector._initialize_detector()
        assert success is True
        assert detector.initialized is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure when dependencies are not available."""
        original_available = QUALITY_DEGRADATION_AVAILABLE

        with patch('services.analysis_service.modules.quality_degradation_detector.QUALITY_DEGRADATION_AVAILABLE', False):
            detector = QualityDegradationDetector()
            success = detector._initialize_detector()
            assert success is False
            assert detector.initialized is False

    @pytest.mark.asyncio
    async def test_extract_quality_metrics(self, sample_analysis_history):
        """Test extraction of quality metrics from analysis history."""
        detector = QualityDegradationDetector()

        metrics_df = detector._extract_quality_metrics(sample_analysis_history)

        assert len(metrics_df) == 7
        assert 'quality_score' in metrics_df.columns
        assert 'total_findings' in metrics_df.columns
        assert metrics_df.index.is_monotonic_increasing  # Should be sorted by timestamp

        # Check that values are properly extracted
        assert metrics_df['quality_score'].iloc[0] == 0.85  # First entry
        assert metrics_df['quality_score'].iloc[-1] == 0.72  # Last entry

    @pytest.mark.asyncio
    async def test_extract_quality_metrics_empty(self):
        """Test extraction with empty analysis history."""
        detector = QualityDegradationDetector()

        metrics_df = detector._extract_quality_metrics([])
        assert metrics_df.empty

    @pytest.mark.asyncio
    async def test_calculate_trend_analysis_degrading(self, sample_analysis_history):
        """Test trend analysis calculation for degrading quality."""
        detector = QualityDegradationDetector()

        metrics_df = detector._extract_quality_metrics(sample_analysis_history)
        quality_scores = metrics_df['quality_score']
        trend_analysis = detector._calculate_trend_analysis(quality_scores)

        assert 'slope' in trend_analysis
        assert 'r_squared' in trend_analysis
        assert 'trend_direction' in trend_analysis
        assert 'confidence' in trend_analysis

        # Should detect degrading trend
        assert trend_analysis['slope'] < 0  # Negative slope
        assert trend_analysis['trend_direction'] == 'degrading'

    @pytest.mark.asyncio
    async def test_calculate_trend_analysis_insufficient_data(self):
        """Test trend analysis with insufficient data."""
        detector = QualityDegradationDetector()

        # Only one data point
        quality_scores = pd.Series([0.8], index=[datetime.now()])

        trend_analysis = detector._calculate_trend_analysis(quality_scores)

        assert trend_analysis['trend_direction'] == 'insufficient_data'
        assert trend_analysis['confidence'] == 0.0

    @pytest.mark.asyncio
    async def test_calculate_volatility_analysis(self, sample_analysis_history):
        """Test volatility analysis calculation."""
        detector = QualityDegradationDetector()

        metrics_df = detector._extract_quality_metrics(sample_analysis_history)
        quality_scores = metrics_df['quality_score']
        volatility_analysis = detector._calculate_volatility_analysis(quality_scores)

        assert 'current_volatility' in volatility_analysis
        assert 'baseline_volatility' in volatility_analysis
        assert 'volatility_change' in volatility_analysis
        assert 'volatility_ratio' in volatility_analysis

        # Check that volatility values are reasonable
        assert volatility_analysis['current_volatility'] >= 0
        assert volatility_analysis['baseline_volatility'] >= 0

    @pytest.mark.asyncio
    async def test_detect_degradation_events(self, sample_analysis_history):
        """Test detection of degradation events."""
        detector = QualityDegradationDetector()

        metrics_df = detector._extract_quality_metrics(sample_analysis_history)
        quality_scores = metrics_df['quality_score']
        degradation_events = detector._detect_degradation_events(quality_scores, threshold=-0.05)

        assert isinstance(degradation_events, list)

        # With the sample data showing gradual decline, there might not be sharp degradation events
        # But the function should still return a list

    @pytest.mark.asyncio
    async def test_assess_degradation_severity_high(self, sample_analysis_history):
        """Test degradation severity assessment for high degradation."""
        detector = QualityDegradationDetector()

        metrics_df = detector._extract_quality_metrics(sample_analysis_history)
        quality_scores = metrics_df['quality_score']
        finding_counts = metrics_df['total_findings']

        trend_analysis = detector._calculate_trend_analysis(quality_scores)
        volatility_analysis = detector._calculate_volatility_analysis(quality_scores)
        degradation_events = detector._detect_degradation_events(quality_scores)
        finding_trend = detector._calculate_trend_analysis(finding_counts)

        severity_assessment = detector._assess_degradation_severity(
            trend_analysis, volatility_analysis, degradation_events, finding_trend
        )

        assert 'overall_severity' in severity_assessment
        assert 'severity_score' in severity_assessment
        assert 'severity_factors' in severity_assessment
        assert 'requires_attention' in severity_assessment

        # With sample data showing degradation, should require attention
        assert severity_assessment['requires_attention'] is True

    @pytest.mark.asyncio
    async def test_generate_alerts_critical(self):
        """Test alert generation for critical degradation."""
        detector = QualityDegradationDetector()

        severity_assessment = {
            'overall_severity': 'critical',
            'severity_score': 0.85,
            'severity_factors': [
                {'factor': 'trend_slope', 'severity': 'critical', 'description': 'Steep negative trend'}
            ]
        }

        trend_analysis = {'slope': -0.01, 'confidence': 0.9}

        alerts = detector._generate_degradation_alerts(severity_assessment, trend_analysis)

        assert len(alerts) > 0
        alert = alerts[0]
        assert alert['alert_type'] == 'quality_degradation'
        assert alert['severity'] == 'critical'
        assert alert['priority'] == 'critical'
        assert 'CRITICAL' in alert['message'].upper()

    @pytest.mark.asyncio
    async def test_generate_alerts_minimal(self):
        """Test alert generation for minimal degradation."""
        detector = QualityDegradationDetector()

        severity_assessment = {
            'overall_severity': 'minimal',
            'severity_score': 0.05,
            'severity_factors': []
        }

        trend_analysis = {'slope': -0.001, 'confidence': 0.3}

        alerts = detector._generate_degradation_alerts(severity_assessment, trend_analysis)

        assert len(alerts) > 0
        alert = alerts[0]
        assert alert['severity'] == 'minimal'
        assert alert['priority'] == 'low'

    @pytest.mark.asyncio
    async def test_detect_quality_degradation_full(self, sample_analysis_history):
        """Test full quality degradation detection."""
        detector = QualityDegradationDetector()

        result = await detector.detect_quality_degradation(
            document_id="test_doc",
            analysis_history=sample_analysis_history,
            baseline_period_days=60,
            alert_threshold=0.05
        )

        assert result['document_id'] == 'test_doc'
        assert 'degradation_detected' in result
        assert 'severity_assessment' in result
        assert 'trend_analysis' in result
        assert 'volatility_analysis' in result
        assert 'degradation_events' in result
        assert 'finding_trend' in result
        assert 'alerts' in result
        assert 'processing_time' in result
        assert 'detection_timestamp' in result

        # With sample data showing degradation, should detect degradation
        assert result['degradation_detected'] is True

    @pytest.mark.asyncio
    async def test_detect_quality_degradation_insufficient_data(self):
        """Test quality degradation detection with insufficient data."""
        detector = QualityDegradationDetector()

        minimal_history = [
            {
                'timestamp': datetime.now().isoformat(),
                'quality_score': 0.8
            }
        ]

        result = await detector.detect_quality_degradation(
            document_id="test_doc",
            analysis_history=minimal_history
        )

        assert result['document_id'] == 'test_doc'
        assert result['degradation_detected'] is False
        assert result['severity_assessment']['overall_severity'] == 'insufficient_data'
        assert result['data_points'] == 1

    @pytest.mark.asyncio
    async def test_monitor_portfolio_degradation(self, portfolio_documents):
        """Test portfolio quality degradation monitoring."""
        detector = QualityDegradationDetector()

        result = await detector.monitor_portfolio_degradation(
            documents=portfolio_documents,
            baseline_period_days=60,
            alert_threshold=0.05
        )

        assert 'portfolio_summary' in result
        assert 'degradation_results' in result
        assert 'alerts_summary' in result
        assert 'processing_time' in result

        portfolio_summary = result['portfolio_summary']
        assert 'total_documents' in portfolio_summary
        assert 'analyzed_documents' in portfolio_summary
        assert 'degradation_detected' in portfolio_summary
        assert 'degradation_rate' in portfolio_summary
        assert 'average_severity_score' in portfolio_summary

        # Should have results for all documents
        assert len(result['degradation_results']) == len(portfolio_documents)

    @pytest.mark.asyncio
    async def test_monitor_portfolio_degradation_empty(self):
        """Test portfolio monitoring with empty document list."""
        detector = QualityDegradationDetector()

        result = await detector.monitor_portfolio_degradation(
            documents=[],
            baseline_period_days=60
        )

        assert result['portfolio_summary']['total_documents'] == 0
        assert result['portfolio_summary']['analyzed_documents'] == 0

    @pytest.mark.asyncio
    async def test_update_detection_thresholds(self):
        """Test updating quality degradation detection thresholds."""
        detector = QualityDegradationDetector()

        custom_thresholds = {
            'trend_slope': {
                'warning_threshold': -0.002,
                'critical_threshold': -0.008,
                'minimum_samples': 6,
                'confidence_required': 0.9
            }
        }

        success = detector.update_detection_thresholds(custom_thresholds)
        assert success is True
        assert detector.degradation_thresholds['trend_slope']['warning_threshold'] == -0.002


@pytest.mark.asyncio
class TestQualityDegradationIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_detect_document_degradation_function(self, sample_analysis_history):
        """Test the convenience function for document degradation detection."""
        with patch('services.analysis_service.modules.quality_degradation_detector.quality_degradation_detector') as mock_detector:
            mock_detector.detect_quality_degradation.return_value = {
                'document_id': 'test_doc',
                'degradation_detected': True,
                'severity_assessment': {
                    'overall_severity': 'high',
                    'severity_score': 0.65,
                    'severity_factors': [
                        {'factor': 'trend_slope', 'severity': 'high', 'description': 'Negative trend detected'}
                    ],
                    'requires_attention': True
                },
                'trend_analysis': {'slope': -0.005, 'trend_direction': 'degrading'},
                'volatility_analysis': {'current_volatility': 0.08},
                'degradation_events': [],
                'finding_trend': {'slope': 0.2},
                'analysis_period_days': 60,
                'data_points': 7,
                'baseline_period_days': 60,
                'alert_threshold': 0.05,
                'alerts': [
                    {
                        'alert_type': 'quality_degradation',
                        'severity': 'high',
                        'message': 'Significant quality degradation detected'
                    }
                ],
                'processing_time': 1.2,
                'detection_timestamp': 1234567890
            }

            result = await detect_document_degradation(
                document_id="test_doc",
                analysis_history=sample_analysis_history,
                baseline_period_days=60,
                alert_threshold=0.05
            )

            assert result['document_id'] == 'test_doc'
            assert result['degradation_detected'] is True
            assert result['severity_assessment']['overall_severity'] == 'high'
            mock_detector.detect_quality_degradation.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitor_portfolio_degradation_function(self, portfolio_documents):
        """Test the convenience function for portfolio degradation monitoring."""
        with patch('services.analysis_service.modules.quality_degradation_detector.quality_degradation_detector') as mock_detector:
            mock_detector.monitor_portfolio_degradation.return_value = {
                'portfolio_summary': {
                    'total_documents': 3,
                    'analyzed_documents': 3,
                    'degradation_detected': 2,
                    'degradation_rate': 0.667,
                    'average_severity_score': 0.55,
                    'severity_distribution': {'low': 1, 'medium': 1, 'high': 1},
                    'high_risk_documents': ['doc1', 'doc3'],
                    'baseline_period_days': 60,
                    'alert_threshold': 0.05
                },
                'degradation_results': [],
                'alerts_summary': [],
                'processing_time': 2.1,
                'monitoring_timestamp': 1234567890
            }

            result = await monitor_portfolio_degradation(
                documents=portfolio_documents,
                baseline_period_days=60,
                alert_threshold=0.05
            )

            assert result['portfolio_summary']['total_documents'] == 3
            assert result['portfolio_summary']['degradation_detected'] == 2
            assert result['portfolio_summary']['degradation_rate'] == 0.667
            mock_detector.monitor_portfolio_degradation.assert_called_once()


class TestQualityDegradationHandlers:
    """Test the analysis handlers integration."""

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        client = Mock()
        client.doc_store_url.return_value = "http://docstore:5000"
        client.get_json = Mock()
        return client

    @pytest.mark.asyncio
    async def test_handle_quality_degradation_detection_success(self, mock_service_client, sample_analysis_history):
        """Test successful quality degradation detection handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import QualityDegradationDetectionRequest

        with patch('services.analysis_service.modules.analysis_handlers.detect_document_degradation') as mock_detect:

            mock_detect.return_value = {
                'document_id': 'test_doc',
                'degradation_detected': True,
                'severity_assessment': {
                    'overall_severity': 'medium',
                    'severity_score': 0.45,
                    'severity_factors': [
                        {'factor': 'trend_slope', 'severity': 'medium', 'description': 'Moderate negative trend'}
                    ],
                    'requires_attention': True
                },
                'trend_analysis': {'slope': -0.003, 'trend_direction': 'degrading'},
                'volatility_analysis': {'current_volatility': 0.06},
                'degradation_events': [],
                'finding_trend': {'slope': 0.1},
                'analysis_period_days': 60,
                'data_points': 7,
                'baseline_period_days': 60,
                'alert_threshold': 0.05,
                'alerts': [
                    {
                        'alert_type': 'quality_degradation',
                        'severity': 'medium',
                        'message': 'Moderate quality degradation detected'
                    }
                ],
                'processing_time': 1.2,
                'detection_timestamp': 1234567890
            }

            request = QualityDegradationDetectionRequest(
                document_id="test_doc",
                analysis_history=sample_analysis_history,
                baseline_period_days=60,
                alert_threshold=0.05
            )

            result = await AnalysisHandlers.handle_quality_degradation_detection(request)

            assert result.document_id == 'test_doc'
            assert result.degradation_detected is True
            assert result.severity_assessment['overall_severity'] == 'medium'
            assert len(result.alerts) > 0
            assert result.processing_time == 1.2

    @pytest.mark.asyncio
    async def test_handle_portfolio_quality_degradation_success(self, mock_service_client, portfolio_documents):
        """Test successful portfolio quality degradation monitoring handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import PortfolioQualityDegradationRequest

        with patch('services.analysis_service.modules.analysis_handlers.monitor_portfolio_degradation') as mock_monitor:

            mock_monitor.return_value = {
                'portfolio_summary': {
                    'total_documents': 3,
                    'analyzed_documents': 3,
                    'degradation_detected': 2,
                    'degradation_rate': 0.667,
                    'average_severity_score': 0.55,
                    'severity_distribution': {'low': 1, 'medium': 1, 'high': 1},
                    'high_risk_documents': ['doc1', 'doc3'],
                    'baseline_period_days': 60,
                    'alert_threshold': 0.05
                },
                'degradation_results': [],
                'alerts_summary': [],
                'processing_time': 2.1,
                'monitoring_timestamp': 1234567890
            }

            request = PortfolioQualityDegradationRequest(
                documents=portfolio_documents,
                baseline_period_days=60,
                alert_threshold=0.05
            )

            result = await AnalysisHandlers.handle_portfolio_quality_degradation(request)

            assert result.portfolio_summary['total_documents'] == 3
            assert result.portfolio_summary['degradation_detected'] == 2
            assert result.portfolio_summary['degradation_rate'] == 0.667
            assert result.processing_time == 2.1

    @pytest.mark.asyncio
    async def test_handle_quality_degradation_detection_error(self, mock_service_client, sample_analysis_history):
        """Test quality degradation detection error handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import QualityDegradationDetectionRequest

        with patch('services.analysis_service.modules.analysis_handlers.detect_document_degradation') as mock_detect:

            mock_detect.side_effect = Exception("Detection failed")

            request = QualityDegradationDetectionRequest(
                document_id="test_doc",
                analysis_history=sample_analysis_history
            )

            result = await AnalysisHandlers.handle_quality_degradation_detection(request)

            assert result.document_id == 'test_doc'
            assert result.degradation_detected is False
            assert result.severity_assessment['overall_severity'] == 'error'
            assert 'Analysis failed due to error' in result.recommendations[0]


if __name__ == "__main__":
    pytest.main([__file__])
