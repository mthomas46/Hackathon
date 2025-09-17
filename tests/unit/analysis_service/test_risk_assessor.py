"""Tests for risk assessment functionality in Analysis Service.

Tests the risk assessor module and its integration with the analysis service.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from services.analysis_service.modules.risk_assessor import (
    RiskAssessor,
    assess_document_risk,
    assess_portfolio_risks,
    RISK_ASSESSMENT_AVAILABLE
)


@pytest.fixture
def sample_document_data():
    """Create sample document data for risk assessment testing."""
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

        ### GET /users
        Retrieves a list of users in the system.

        **Parameters:**
        - limit (integer): Maximum number of users to return (default: 100)
        - offset (integer): Number of users to skip (default: 0)

        **Response:**
        ```json
        {
          "users": [...],
          "total": 150
        }
        ```

        ### POST /users
        Creates a new user in the system.

        **Request Body:**
        ```json
        {
          "name": "John Doe",
          "email": "john@example.com",
          "role": "user"
        }
        ```

        **Response:**
        ```json
        {
          "id": 123,
          "name": "John Doe",
          "email": "john@example.com",
          "role": "user",
          "created_at": "2024-01-15T10:30:00Z"
        }
        ```

        ## Error Handling
        The API uses standard HTTP status codes to indicate the result of operations.

        - 200 OK: Success
        - 400 Bad Request: Invalid request parameters
        - 401 Unauthorized: Authentication required
        - 403 Forbidden: Insufficient permissions
        - 404 Not Found: Resource not found
        - 500 Internal Server Error: Server error

        ## Rate Limiting
        API calls are rate limited to prevent abuse. The current limits are:
        - 1000 requests per hour for authenticated users
        - 100 requests per hour for anonymous users

        ## SDKs and Libraries
        We provide official SDKs in several programming languages:
        - JavaScript/Node.js
        - Python
        - Java
        - C#
        - Go

        ## Changelog
        - v1.2.0 (2024-01-10): Added pagination support
        - v1.1.0 (2023-12-05): Improved error messages
        - v1.0.0 (2023-10-15): Initial release
        """,
        'last_modified': (datetime.now() - timedelta(days=45)).isoformat(),
        'author': 'api_team',
        'tags': ['api', 'reference', 'documentation'],
        'word_count': 850,
        'complexity_score': 0.75,
        'quality_score': 0.85,
        'usage_frequency': 500,
        'stakeholder_impact': 'high'
    }


@pytest.fixture
def sample_analysis_history():
    """Create sample analysis history for testing."""
    base_date = datetime.now()

    return [
        {
            'timestamp': (base_date - timedelta(days=30)).isoformat(),
            'quality_score': 0.88,
            'total_findings': 3,
            'critical_findings': 0,
            'high_findings': 1,
            'sentiment_score': 0.8
        },
        {
            'timestamp': (base_date - timedelta(days=20)).isoformat(),
            'quality_score': 0.82,
            'total_findings': 5,
            'critical_findings': 1,
            'high_findings': 2,
            'sentiment_score': 0.75
        },
        {
            'timestamp': (base_date - timedelta(days=10)).isoformat(),
            'quality_score': 0.79,
            'total_findings': 8,
            'critical_findings': 2,
            'high_findings': 3,
            'sentiment_score': 0.7
        },
        {
            'timestamp': base_date.isoformat(),
            'quality_score': 0.76,
            'total_findings': 10,
            'critical_findings': 3,
            'high_findings': 4,
            'sentiment_score': 0.65
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
            'last_modified': (base_date - timedelta(days=30)).isoformat(),
            'quality_score': 0.85,
            'complexity_score': 0.8,
            'stakeholder_impact': 'high'
        },
        {
            'document_id': 'user_guide_1',
            'document_type': 'user_guide',
            'content': 'User guide content...',
            'last_modified': (base_date - timedelta(days=60)).isoformat(),
            'quality_score': 0.7,
            'complexity_score': 0.4,
            'stakeholder_impact': 'medium'
        },
        {
            'document_id': 'tutorial_1',
            'document_type': 'tutorial',
            'content': 'Tutorial content...',
            'last_modified': (base_date - timedelta(days=90)).isoformat(),
            'quality_score': 0.6,
            'complexity_score': 0.3,
            'stakeholder_impact': 'low'
        }
    ]


class TestRiskAssessor:
    """Test the RiskAssessor class."""

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization of the risk assessor."""
        assessor = RiskAssessor()
        success = assessor._initialize_assessor()
        assert success is True
        assert assessor.initialized is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure when dependencies are not available."""
        original_available = RISK_ASSESSMENT_AVAILABLE

        with patch('services.analysis_service.modules.risk_assessor.RISK_ASSESSMENT_AVAILABLE', False):
            assessor = RiskAssessor()
            success = assessor._initialize_assessor()
            assert success is False
            assert assessor.initialized is False

    @pytest.mark.asyncio
    async def test_calculate_risk_factor_score_linear_increase(self, sample_document_data):
        """Test risk score calculation for linear increase factors."""
        assessor = RiskAssessor()

        # Test document age (older = higher risk)
        age_score = assessor._calculate_risk_factor_score('document_age', 200, assessor.risk_factors['document_age'])
        assert age_score > 0.5  # High risk for 200 days

        # Test with low value
        age_score_low = assessor._calculate_risk_factor_score('document_age', 10, assessor.risk_factors['document_age'])
        assert age_score_low < 0.5  # Low risk for 10 days

    @pytest.mark.asyncio
    async def test_calculate_risk_factor_score_inverse_linear(self, sample_document_data):
        """Test risk score calculation for inverse linear factors."""
        assessor = RiskAssessor()

        # Test quality score (lower = higher risk)
        quality_score = assessor._calculate_risk_factor_score('quality_score', 0.5, assessor.risk_factors['quality_score'])
        assert quality_score > 0.5  # High risk for low quality

        # Test with high value
        quality_score_high = assessor._calculate_risk_factor_score('quality_score', 0.95, assessor.risk_factors['quality_score'])
        assert quality_score_high < 0.5  # Low risk for high quality

    @pytest.mark.asyncio
    async def test_calculate_risk_factor_score_categorical(self, sample_document_data):
        """Test risk score calculation for categorical factors."""
        assessor = RiskAssessor()

        # Test stakeholder impact
        high_impact_score = assessor._calculate_risk_factor_score('stakeholder_impact', 'high', assessor.risk_factors['stakeholder_impact'])
        assert high_impact_score > 0.5  # High risk for high impact

        low_impact_score = assessor._calculate_risk_factor_score('stakeholder_impact', 'low', assessor.risk_factors['stakeholder_impact'])
        assert low_impact_score < 0.5  # Low risk for low impact

    @pytest.mark.asyncio
    async def test_assess_individual_risks(self, sample_document_data, sample_analysis_history):
        """Test assessment of individual risk factors."""
        assessor = RiskAssessor()

        risk_scores = assessor._assess_individual_risks({
            **sample_document_data,
            'analysis_history': sample_analysis_history
        })

        # Check that all risk factors are assessed
        expected_factors = ['document_age', 'complexity_score', 'change_frequency',
                          'quality_score', 'trend_decline', 'finding_density',
                          'stakeholder_impact', 'usage_frequency']

        for factor in expected_factors:
            assert factor in risk_scores
            assert 'risk_score' in risk_scores[factor]
            assert 'weight' in risk_scores[factor]
            assert 'value' in risk_scores[factor]
            assert 'description' in risk_scores[factor]

    @pytest.mark.asyncio
    async def test_calculate_overall_risk_score(self, sample_document_data):
        """Test calculation of overall risk score."""
        assessor = RiskAssessor()

        # Create mock risk scores
        risk_scores = {
            'document_age': {'risk_score': 0.8, 'weight': 0.15},
            'quality_score': {'risk_score': 0.3, 'weight': 0.18},
            'complexity_score': {'risk_score': 0.7, 'weight': 0.20},
            'stakeholder_impact': {'risk_score': 0.9, 'weight': 0.12}
        }

        overall_risk = assessor._calculate_overall_risk_score(risk_scores)

        assert 'overall_score' in overall_risk
        assert 'risk_level' in overall_risk
        assert 'weighted_sum' in overall_risk
        assert 'total_weight' in overall_risk

        # Check risk level classification
        score = overall_risk['overall_score']
        if score >= 0.8:
            assert overall_risk['risk_level'] == 'critical'
        elif score >= 0.6:
            assert overall_risk['risk_level'] == 'high'
        elif score >= 0.4:
            assert overall_risk['risk_level'] == 'medium'
        elif score >= 0.2:
            assert overall_risk['risk_level'] == 'low'
        else:
            assert overall_risk['risk_level'] == 'minimal'

    @pytest.mark.asyncio
    async def test_generate_risk_recommendations_high_risk(self, sample_document_data):
        """Test generation of risk recommendations for high-risk scenarios."""
        assessor = RiskAssessor()

        risk_scores = {
            'document_age': {'risk_score': 0.9, 'value': 300},
            'quality_score': {'risk_score': 0.8, 'value': 0.5},
            'complexity_score': {'risk_score': 0.7, 'value': 0.8}
        }
        overall_risk = {'risk_level': 'high'}

        recommendations = assessor._generate_risk_recommendations(risk_scores, overall_risk)

        assert len(recommendations) > 0
        assert any('immediate' in rec.lower() or 'review' in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_generate_risk_recommendations_low_risk(self, sample_document_data):
        """Test generation of risk recommendations for low-risk scenarios."""
        assessor = RiskAssessor()

        risk_scores = {
            'document_age': {'risk_score': 0.2, 'value': 30},
            'quality_score': {'risk_score': 0.1, 'value': 0.9},
            'complexity_score': {'risk_score': 0.3, 'value': 0.4}
        }
        overall_risk = {'risk_level': 'low'}

        recommendations = assessor._generate_risk_recommendations(risk_scores, overall_risk)

        assert len(recommendations) > 0
        assert any('maintain' in rec.lower() or 'low' in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_identify_risk_drivers(self, sample_document_data):
        """Test identification of primary risk drivers."""
        assessor = RiskAssessor()

        risk_scores = {
            'document_age': {'risk_score': 0.9, 'weight': 0.15, 'description': 'Document age'},
            'quality_score': {'risk_score': 0.8, 'weight': 0.18, 'description': 'Quality score'},
            'complexity_score': {'risk_score': 0.3, 'weight': 0.20, 'description': 'Complexity'},
            'stakeholder_impact': {'risk_score': 0.2, 'weight': 0.12, 'description': 'Stakeholder impact'}
        }

        risk_drivers = assessor._identify_risk_drivers(risk_scores)

        assert len(risk_drivers) <= 5  # Limited to top 5
        # First driver should have highest contribution
        assert risk_drivers[0]['contribution'] >= risk_drivers[-1]['contribution']

    @pytest.mark.asyncio
    async def test_assess_document_risk_full(self, sample_document_data, sample_analysis_history):
        """Test full document risk assessment."""
        assessor = RiskAssessor()

        result = await assessor.assess_document_risk(
            document_id="test_doc_1",
            document_data=sample_document_data,
            analysis_history=sample_analysis_history
        )

        assert result['document_id'] == 'test_doc_1'
        assert 'overall_risk' in result
        assert 'risk_factors' in result
        assert 'risk_drivers' in result
        assert 'recommendations' in result
        assert 'processing_time' in result
        assert 'assessment_timestamp' in result

        # Validate overall risk structure
        overall_risk = result['overall_risk']
        assert 'overall_score' in overall_risk
        assert 'risk_level' in overall_risk
        assert overall_risk['overall_score'] >= 0.0 and overall_risk['overall_score'] <= 1.0

    @pytest.mark.asyncio
    async def test_assess_portfolio_risks(self, portfolio_documents):
        """Test portfolio risk assessment."""
        assessor = RiskAssessor()

        result = await assessor.assess_portfolio_risks(
            documents=portfolio_documents,
            group_by='document_type'
        )

        assert 'portfolio_summary' in result
        assert 'document_assessments' in result
        assert 'high_risk_documents' in result
        assert 'processing_time' in result

        portfolio_summary = result['portfolio_summary']
        assert 'total_documents' in portfolio_summary
        assert 'assessed_documents' in portfolio_summary
        assert 'average_risk_score' in portfolio_summary
        assert 'risk_distribution' in portfolio_summary
        assert 'high_risk_document_count' in portfolio_summary

        # Should have assessments for all documents
        assert len(result['document_assessments']) == len(portfolio_documents)

    @pytest.mark.asyncio
    async def test_assess_document_risk_missing_data(self):
        """Test risk assessment with minimal data."""
        assessor = RiskAssessor()

        minimal_data = {
            'document_id': 'minimal_doc',
            'content': 'Some minimal content'
        }

        result = await assessor.assess_document_risk(
            document_id="minimal_doc",
            document_data=minimal_data
        )

        assert result['document_id'] == 'minimal_doc'
        assert 'overall_risk' in result
        assert result['overall_risk']['overall_score'] >= 0.0

    @pytest.mark.asyncio
    async def test_update_risk_factors(self):
        """Test updating risk factor configuration."""
        assessor = RiskAssessor()

        custom_factors = {
            'custom_factor': {
                'weight': 0.1,
                'description': 'Custom risk factor',
                'risk_function': 'linear_increase',
                'thresholds': {'low': 0, 'medium': 50, 'high': 100}
            }
        }

        success = assessor.update_risk_factors(custom_factors)
        assert success is True
        assert 'custom_factor' in assessor.risk_factors


@pytest.mark.asyncio
class TestRiskAssessmentIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_assess_document_risk_function(self, sample_document_data, sample_analysis_history):
        """Test the convenience function for document risk assessment."""
        with patch('services.analysis_service.modules.risk_assessor.risk_assessor') as mock_assessor:
            mock_assessor.assess_document_risk.return_value = {
                'document_id': 'test_doc_1',
                'overall_risk': {
                    'overall_score': 0.65,
                    'risk_level': 'medium',
                    'weighted_sum': 0.45,
                    'total_weight': 0.95
                },
                'risk_factors': {
                    'document_age': {'risk_score': 0.7, 'weight': 0.15, 'value': 45}
                },
                'risk_drivers': [
                    {'factor': 'document_age', 'contribution': 0.105}
                ],
                'recommendations': ['Consider updating the document'],
                'assessment_timestamp': 1234567890,
                'processing_time': 1.2
            }

            result = await assess_document_risk(
                document_id="test_doc_1",
                document_data=sample_document_data,
                analysis_history=sample_analysis_history
            )

            assert result['document_id'] == 'test_doc_1'
            assert result['overall_risk']['risk_level'] == 'medium'
            mock_assessor.assess_document_risk.assert_called_once()

    @pytest.mark.asyncio
    async def test_assess_portfolio_risks_function(self, portfolio_documents):
        """Test the convenience function for portfolio risk assessment."""
        with patch('services.analysis_service.modules.risk_assessor.risk_assessor') as mock_assessor:
            mock_assessor.assess_portfolio_risks.return_value = {
                'portfolio_summary': {
                    'total_documents': 3,
                    'assessed_documents': 3,
                    'average_risk_score': 0.55,
                    'risk_distribution': {'low': 1, 'medium': 2},
                    'high_risk_document_count': 1
                },
                'document_assessments': [],
                'high_risk_documents': ['api_doc_1'],
                'processing_time': 2.1,
                'assessment_timestamp': 1234567890
            }

            result = await assess_portfolio_risks(
                documents=portfolio_documents,
                group_by='document_type'
            )

            assert result['portfolio_summary']['total_documents'] == 3
            assert result['portfolio_summary']['average_risk_score'] == 0.55
            mock_assessor.assess_portfolio_risks.assert_called_once()


class TestRiskAssessmentHandlers:
    """Test the analysis handlers integration."""

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        client = Mock()
        client.doc_store_url.return_value = "http://docstore:5000"
        client.get_json = Mock()
        return client

    @pytest.mark.asyncio
    async def test_handle_risk_assessment_success(self, mock_service_client, sample_document_data, sample_analysis_history):
        """Test successful risk assessment handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import RiskAssessmentRequest

        with patch('services.analysis_service.modules.analysis_handlers.assess_document_risk') as mock_assess:

            mock_assess.return_value = {
                'document_id': 'test_doc_1',
                'overall_risk': {
                    'overall_score': 0.65,
                    'risk_level': 'medium'
                },
                'risk_factors': {},
                'risk_drivers': [],
                'recommendations': ['Consider regular updates'],
                'assessment_timestamp': 1234567890,
                'processing_time': 1.5
            }

            request = RiskAssessmentRequest(
                document_id="test_doc_1",
                document_data=sample_document_data,
                analysis_history=sample_analysis_history
            )

            result = await AnalysisHandlers.handle_risk_assessment(request)

            assert result.document_id == 'test_doc_1'
            assert result.overall_risk['risk_level'] == 'medium'
            assert len(result.recommendations) > 0
            assert result.processing_time == 1.5

    @pytest.mark.asyncio
    async def test_handle_portfolio_risk_assessment_success(self, mock_service_client, portfolio_documents):
        """Test successful portfolio risk assessment handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import PortfolioRiskAssessmentRequest

        with patch('services.analysis_service.modules.analysis_handlers.assess_portfolio_risks') as mock_assess:

            mock_assess.return_value = {
                'portfolio_summary': {
                    'total_documents': 3,
                    'assessed_documents': 3,
                    'average_risk_score': 0.55,
                    'risk_distribution': {'low': 1, 'medium': 2},
                    'high_risk_document_count': 1
                },
                'document_assessments': [],
                'high_risk_documents': ['api_doc_1'],
                'processing_time': 2.1,
                'assessment_timestamp': 1234567890
            }

            request = PortfolioRiskAssessmentRequest(
                documents=portfolio_documents,
                group_by='document_type'
            )

            result = await AnalysisHandlers.handle_portfolio_risk_assessment(request)

            assert result.portfolio_summary['total_documents'] == 3
            assert result.portfolio_summary['assessed_documents'] == 3
            assert len(result.high_risk_documents) == 1
            assert result.processing_time == 2.1

    @pytest.mark.asyncio
    async def test_handle_risk_assessment_error(self, mock_service_client, sample_document_data):
        """Test risk assessment error handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import RiskAssessmentRequest

        with patch('services.analysis_service.modules.analysis_handlers.assess_document_risk') as mock_assess:

            mock_assess.side_effect = Exception("Assessment failed")

            request = RiskAssessmentRequest(
                document_id="test_doc_1",
                document_data=sample_document_data
            )

            result = await AnalysisHandlers.handle_risk_assessment(request)

            assert result.document_id == 'test_doc_1'
            assert result.overall_risk['risk_level'] == 'unknown'
            assert 'Analysis failed due to error' in result.recommendations[0]


if __name__ == "__main__":
    pytest.main([__file__])
