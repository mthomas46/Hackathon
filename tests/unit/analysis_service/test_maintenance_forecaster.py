"""Tests for maintenance forecasting functionality in Analysis Service.

Tests the maintenance forecaster module and its integration with the analysis service.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from services.analysis_service.modules.maintenance_forecaster import (
    MaintenanceForecaster,
    forecast_document_maintenance,
    forecast_portfolio_maintenance,
    MAINTENANCE_FORECASTING_AVAILABLE
)


@pytest.fixture
def sample_document_data():
    """Create sample document data for maintenance forecasting testing."""
    return {
        'document_id': 'test_doc_1',
        'document_type': 'api_reference',
        'content': """
        # API Reference Documentation

        This is a comprehensive API reference document that contains detailed information
        about our REST API endpoints, authentication methods, and usage examples.

        ## Authentication
        The API uses OAuth 2.0 for authentication. You need to obtain an access token
        by sending a POST request to /oauth/token with your client credentials.

        ## Endpoints
        - GET /users - List users
        - POST /users - Create user
        - PUT /users/{id} - Update user
        - DELETE /users/{id} - Delete user

        ## Error Handling
        The API uses standard HTTP status codes to indicate the result of operations.
        """,
        'last_modified': (datetime.now() - timedelta(days=120)).isoformat(),
        'author': 'api_team',
        'tags': ['api', 'reference', 'documentation'],
        'word_count': 500,
        'quality_score': 0.75,
        'risk_score': 0.65,
        'usage_frequency': 150,
        'business_criticality': 'high'
    }


@pytest.fixture
def sample_analysis_history():
    """Create sample analysis history for testing."""
    base_date = datetime.now()

    return [
        {
            'timestamp': (base_date - timedelta(days=90)).isoformat(),
            'quality_score': 0.8,
            'risk_score': 0.6,
            'total_findings': 5
        },
        {
            'timestamp': (base_date - timedelta(days=60)).isoformat(),
            'quality_score': 0.78,
            'risk_score': 0.62,
            'total_findings': 6
        },
        {
            'timestamp': (base_date - timedelta(days=30)).isoformat(),
            'quality_score': 0.75,
            'risk_score': 0.65,
            'total_findings': 7
        }
    ]


@pytest.fixture
def portfolio_documents():
    """Create sample portfolio of documents for testing."""
    base_date = datetime.now()

    return [
        {
            'document_id': 'api_doc_1',
            'document_type': 'api_reference',
            'content': 'API documentation content...',
            'last_modified': (base_date - timedelta(days=100)).isoformat(),
            'quality_score': 0.8,
            'risk_score': 0.6,
            'business_criticality': 'high'
        },
        {
            'document_id': 'user_guide_1',
            'document_type': 'user_guide',
            'content': 'User guide content...',
            'last_modified': (base_date - timedelta(days=200)).isoformat(),
            'quality_score': 0.65,
            'risk_score': 0.75,
            'business_criticality': 'medium'
        },
        {
            'document_id': 'tutorial_1',
            'document_type': 'tutorial',
            'content': 'Tutorial content...',
            'last_modified': (base_date - timedelta(days=50)).isoformat(),
            'quality_score': 0.85,
            'risk_score': 0.4,
            'business_criticality': 'low'
        }
    ]


class TestMaintenanceForecaster:
    """Test the MaintenanceForecaster class."""

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization of the maintenance forecaster."""
        forecaster = MaintenanceForecaster()
        success = forecaster._initialize_forecaster()
        assert success is True
        assert forecaster.initialized is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure when dependencies are not available."""
        original_available = MAINTENANCE_FORECASTING_AVAILABLE

        with patch('services.analysis_service.modules.maintenance_forecaster.MAINTENANCE_FORECASTING_AVAILABLE', False):
            forecaster = MaintenanceForecaster()
            success = forecaster._initialize_forecaster()
            assert success is False
            assert forecaster.initialized is False

    @pytest.mark.asyncio
    async def test_calculate_maintenance_urgency_risk_score(self):
        """Test maintenance urgency calculation for risk score factor."""
        forecaster = MaintenanceForecaster()

        # High risk score should result in high urgency
        high_risk = forecaster._calculate_maintenance_urgency('risk_score', 0.8, forecaster.maintenance_factors['risk_score'])
        assert high_risk['urgency_score'] > 0.5
        assert high_risk['predicted_days'] < 200  # Sooner maintenance

        # Low risk score should result in lower urgency
        low_risk = forecaster._calculate_maintenance_urgency('risk_score', 0.2, forecaster.maintenance_factors['risk_score'])
        assert low_risk['urgency_score'] < 0.5
        assert low_risk['predicted_days'] > 200  # Later maintenance

    @pytest.mark.asyncio
    async def test_calculate_maintenance_urgency_document_age(self):
        """Test maintenance urgency calculation for document age factor."""
        forecaster = MaintenanceForecaster()

        # Old document should have higher urgency
        old_doc = forecaster._calculate_maintenance_urgency('document_age', 300, forecaster.maintenance_factors['document_age'])
        assert old_doc['urgency_score'] > 0.5

        # Recent document should have lower urgency
        recent_doc = forecaster._calculate_maintenance_urgency('document_age', 30, forecaster.maintenance_factors['document_age'])
        assert recent_doc['urgency_score'] < 0.5

    @pytest.mark.asyncio
    async def test_calculate_maintenance_urgency_usage_frequency(self):
        """Test maintenance urgency calculation for usage frequency factor."""
        forecaster = MaintenanceForecaster()

        # High usage should result in lower urgency (later maintenance)
        high_usage = forecaster._calculate_maintenance_urgency('usage_frequency', 500, forecaster.maintenance_factors['usage_frequency'])
        assert high_usage['urgency_score'] < 0.5
        assert high_usage['predicted_days'] > 100

        # Low usage should result in higher urgency (sooner maintenance)
        low_usage = forecaster._calculate_maintenance_urgency('usage_frequency', 10, forecaster.maintenance_factors['usage_frequency'])
        assert low_usage['urgency_score'] > 0.5
        assert low_usage['predicted_days'] < 100

    @pytest.mark.asyncio
    async def test_calculate_maintenance_urgency_business_criticality(self):
        """Test maintenance urgency calculation for business criticality factor."""
        forecaster = MaintenanceForecaster()

        # Critical business impact should result in urgent maintenance
        critical = forecaster._calculate_maintenance_urgency('business_criticality', 'critical', forecaster.maintenance_factors['business_criticality'])
        assert critical['urgency_score'] > 0.5
        assert critical['predicted_days'] <= 60

        # Low business impact should result in less urgent maintenance
        low_impact = forecaster._calculate_maintenance_urgency('business_criticality', 'low', forecaster.maintenance_factors['business_criticality'])
        assert low_impact['urgency_score'] < 0.5
        assert low_impact['predicted_days'] >= 150

    @pytest.mark.asyncio
    async def test_forecast_maintenance_schedule(self, sample_document_data, sample_analysis_history):
        """Test maintenance schedule forecasting."""
        forecaster = MaintenanceForecaster()

        forecast_data = forecaster._forecast_maintenance_schedule(sample_document_data, sample_analysis_history)

        assert 'overall_forecast' in forecast_data
        assert 'factor_forecasts' in forecast_data
        assert 'urgent_factors' in forecast_data
        assert 'maintenance_schedule' in forecast_data

        overall_forecast = forecast_data['overall_forecast']
        assert 'predicted_days' in overall_forecast
        assert 'predicted_date' in overall_forecast
        assert 'urgency_score' in overall_forecast
        assert 'priority_level' in overall_forecast
        assert 'confidence' in overall_forecast

        # Check that predicted days are reasonable
        assert 7 <= overall_forecast['predicted_days'] <= 730

    @pytest.mark.asyncio
    async def test_generate_maintenance_schedule_critical(self):
        """Test maintenance schedule generation for critical priority."""
        forecaster = MaintenanceForecaster()

        schedule = forecaster._generate_maintenance_schedule(30, 'critical', [])

        assert schedule['priority_level'] == 'critical'
        assert schedule['maintenance_type'] == 'major_overhaul'
        assert len(schedule['milestones']) >= 2
        assert 'assessment' in schedule['milestones'][0]['type']

    @pytest.mark.asyncio
    async def test_generate_maintenance_schedule_medium(self):
        """Test maintenance schedule generation for medium priority."""
        forecaster = MaintenanceForecaster()

        schedule = forecaster._generate_maintenance_schedule(90, 'medium', [])

        assert schedule['priority_level'] == 'medium'
        assert schedule['maintenance_type'] == 'targeted_updates'
        assert len(schedule['milestones']) >= 1

    @pytest.mark.asyncio
    async def test_generate_maintenance_recommendations_critical(self):
        """Test maintenance recommendation generation for critical scenarios."""
        forecaster = MaintenanceForecaster()

        forecast_data = {
            'overall_forecast': {'priority_level': 'critical', 'predicted_days': 15},
            'urgent_factors': [{'factor': 'risk_score', 'urgency': 0.9}]
        }

        recommendations = forecaster._generate_maintenance_recommendations(forecast_data)

        assert len(recommendations) > 0
        assert any('CRITICAL' in rec.upper() for rec in recommendations)
        assert any('immediate' in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_generate_maintenance_recommendations_low_priority(self):
        """Test maintenance recommendation generation for low priority scenarios."""
        forecaster = MaintenanceForecaster()

        forecast_data = {
            'overall_forecast': {'priority_level': 'low', 'predicted_days': 180},
            'urgent_factors': []
        }

        recommendations = forecaster._generate_maintenance_recommendations(forecast_data)

        assert len(recommendations) > 0
        assert any('low priority' in rec.lower() or 'maintain' in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_forecast_document_maintenance_full(self, sample_document_data, sample_analysis_history):
        """Test full document maintenance forecasting."""
        forecaster = MaintenanceForecaster()

        result = await forecaster.forecast_document_maintenance(
            document_id="test_doc_1",
            document_data=sample_document_data,
            analysis_history=sample_analysis_history
        )

        assert result['document_id'] == 'test_doc_1'
        assert 'forecast_data' in result
        assert 'recommendations' in result
        assert 'processing_time' in result
        assert 'forecast_timestamp' in result

        forecast_data = result['forecast_data']
        assert 'overall_forecast' in forecast_data
        assert 'maintenance_schedule' in forecast_data

        assert len(result['recommendations']) > 0

    @pytest.mark.asyncio
    async def test_forecast_portfolio_maintenance(self, portfolio_documents):
        """Test portfolio maintenance forecasting."""
        forecaster = MaintenanceForecaster()

        result = await forecaster.forecast_portfolio_maintenance(
            documents=portfolio_documents,
            group_by='document_type'
        )

        assert 'portfolio_summary' in result
        assert 'maintenance_schedule' in result
        assert 'document_forecasts' in result
        assert 'processing_time' in result

        portfolio_summary = result['portfolio_summary']
        assert 'total_documents' in portfolio_summary
        assert 'forecasted_documents' in portfolio_summary
        assert 'average_urgency' in portfolio_summary
        assert 'priority_distribution' in portfolio_summary

        # Should have forecasts for all documents
        assert len(result['document_forecasts']) == len(portfolio_documents)

        # Should have maintenance schedule
        assert len(result['maintenance_schedule']) > 0

    @pytest.mark.asyncio
    async def test_forecast_document_maintenance_minimal_data(self):
        """Test maintenance forecasting with minimal data."""
        forecaster = MaintenanceForecaster()

        minimal_data = {
            'document_id': 'minimal_doc',
            'content': 'Some minimal content'
        }

        result = await forecaster.forecast_document_maintenance(
            document_id="minimal_doc",
            document_data=minimal_data
        )

        assert result['document_id'] == 'minimal_doc'
        assert 'forecast_data' in result
        assert result['forecast_data']['overall_forecast']['predicted_days'] > 0

    @pytest.mark.asyncio
    async def test_update_maintenance_factors(self):
        """Test updating maintenance forecasting factors configuration."""
        forecaster = MaintenanceForecaster()

        custom_factors = {
            'custom_factor': {
                'weight': 0.1,
                'description': 'Custom maintenance factor',
                'forecast_impact': 'linear_increase',
                'base_interval_days': 60,
                'urgency_multiplier': 0.5
            }
        }

        success = forecaster.update_maintenance_factors(custom_factors)
        assert success is True
        assert 'custom_factor' in forecaster.maintenance_factors


@pytest.mark.asyncio
class TestMaintenanceForecastingIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_forecast_document_maintenance_function(self, sample_document_data, sample_analysis_history):
        """Test the convenience function for document maintenance forecasting."""
        with patch('services.analysis_service.modules.maintenance_forecaster.maintenance_forecaster') as mock_forecaster:
            mock_forecaster.forecast_document_maintenance.return_value = {
                'document_id': 'test_doc_1',
                'forecast_data': {
                    'overall_forecast': {
                        'predicted_days': 75,
                        'predicted_date': '2024-02-15T00:00:00',
                        'urgency_score': 0.65,
                        'priority_level': 'medium',
                        'confidence': 0.85
                    },
                    'factor_forecasts': {},
                    'urgent_factors': [],
                    'maintenance_schedule': {}
                },
                'recommendations': ['Schedule maintenance within 2-3 months'],
                'processing_time': 1.2,
                'forecast_timestamp': 1234567890
            }

            result = await forecast_document_maintenance(
                document_id="test_doc_1",
                document_data=sample_document_data,
                analysis_history=sample_analysis_history
            )

            assert result['document_id'] == 'test_doc_1'
            assert result['forecast_data']['overall_forecast']['priority_level'] == 'medium'
            mock_forecaster.forecast_document_maintenance.assert_called_once()

    @pytest.mark.asyncio
    async def test_forecast_portfolio_maintenance_function(self, portfolio_documents):
        """Test the convenience function for portfolio maintenance forecasting."""
        with patch('services.analysis_service.modules.maintenance_forecaster.maintenance_forecaster') as mock_forecaster:
            mock_forecaster.forecast_portfolio_maintenance.return_value = {
                'portfolio_summary': {
                    'total_documents': 3,
                    'forecasted_documents': 3,
                    'average_urgency': 0.55,
                    'priority_distribution': {'low': 1, 'medium': 2},
                    'maintenance_dates': 8
                },
                'maintenance_schedule': [],
                'document_forecasts': [],
                'processing_time': 2.1,
                'forecast_timestamp': 1234567890
            }

            result = await forecast_portfolio_maintenance(
                documents=portfolio_documents,
                group_by='document_type'
            )

            assert result['portfolio_summary']['total_documents'] == 3
            assert result['portfolio_summary']['average_urgency'] == 0.55
            mock_forecaster.forecast_portfolio_maintenance.assert_called_once()


class TestMaintenanceForecastingHandlers:
    """Test the analysis handlers integration."""

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        client = Mock()
        client.doc_store_url.return_value = "http://docstore:5000"
        client.get_json = Mock()
        return client

    @pytest.mark.asyncio
    async def test_handle_maintenance_forecast_success(self, mock_service_client, sample_document_data, sample_analysis_history):
        """Test successful maintenance forecasting handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import MaintenanceForecastRequest

        with patch('services.analysis_service.modules.analysis_handlers.forecast_document_maintenance') as mock_forecast:

            mock_forecast.return_value = {
                'document_id': 'test_doc_1',
                'forecast_data': {
                    'overall_forecast': {
                        'predicted_days': 75,
                        'predicted_date': '2024-02-15T00:00:00',
                        'urgency_score': 0.65,
                        'priority_level': 'medium',
                        'confidence': 0.85
                    },
                    'factor_forecasts': {},
                    'urgent_factors': [],
                    'maintenance_schedule': {}
                },
                'recommendations': ['Schedule maintenance within 2-3 months'],
                'processing_time': 1.2,
                'forecast_timestamp': 1234567890
            }

            request = MaintenanceForecastRequest(
                document_id="test_doc_1",
                document_data=sample_document_data,
                analysis_history=sample_analysis_history
            )

            result = await AnalysisHandlers.handle_maintenance_forecast(request)

            assert result.document_id == 'test_doc_1'
            assert result.forecast_data['overall_forecast']['priority_level'] == 'medium'
            assert len(result.recommendations) > 0
            assert result.processing_time == 1.2

    @pytest.mark.asyncio
    async def test_handle_portfolio_maintenance_forecast_success(self, mock_service_client, portfolio_documents):
        """Test successful portfolio maintenance forecasting handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import PortfolioMaintenanceForecastRequest

        with patch('services.analysis_service.modules.analysis_handlers.forecast_portfolio_maintenance') as mock_forecast:

            mock_forecast.return_value = {
                'portfolio_summary': {
                    'total_documents': 3,
                    'forecasted_documents': 3,
                    'average_urgency': 0.55,
                    'priority_distribution': {'low': 1, 'medium': 2},
                    'maintenance_dates': 8
                },
                'maintenance_schedule': [],
                'document_forecasts': [],
                'processing_time': 2.1,
                'forecast_timestamp': 1234567890
            }

            request = PortfolioMaintenanceForecastRequest(
                documents=portfolio_documents,
                group_by='document_type'
            )

            result = await AnalysisHandlers.handle_portfolio_maintenance_forecast(request)

            assert result.portfolio_summary['total_documents'] == 3
            assert result.portfolio_summary['forecasted_documents'] == 3
            assert result.processing_time == 2.1

    @pytest.mark.asyncio
    async def test_handle_maintenance_forecast_error(self, mock_service_client, sample_document_data):
        """Test maintenance forecasting error handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import MaintenanceForecastRequest

        with patch('services.analysis_service.modules.analysis_handlers.forecast_document_maintenance') as mock_forecast:

            mock_forecast.side_effect = Exception("Forecasting failed")

            request = MaintenanceForecastRequest(
                document_id="test_doc_1",
                document_data=sample_document_data
            )

            result = await AnalysisHandlers.handle_maintenance_forecast(request)

            assert result.document_id == 'test_doc_1'
            assert result.forecast_data['overall_forecast']['priority_level'] == 'medium'
            assert 'Analysis failed due to error' in result.recommendations[0]


if __name__ == "__main__":
    pytest.main([__file__])
