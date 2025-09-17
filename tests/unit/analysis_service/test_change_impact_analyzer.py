"""Tests for change impact analysis functionality in Analysis Service.

Tests the change impact analyzer module and its integration with the analysis service.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from services.analysis_service.modules.change_impact_analyzer import (
    ChangeImpactAnalyzer,
    analyze_change_impact,
    analyze_portfolio_change_impact,
    CHANGE_IMPACT_AVAILABLE
)


@pytest.fixture
def sample_document_data():
    """Create sample document data for change impact analysis testing."""
    return {
        'document_id': 'api_guide_v2',
        'title': 'API Developer Guide v2.0',
        'document_type': 'developer_guide',
        'content': """
        # API Developer Guide

        This comprehensive guide covers the REST API for our platform, including authentication,
        endpoints, error handling, and best practices for developers.

        ## Authentication

        The API uses OAuth 2.0 for authentication. You must obtain an access token by making
        a POST request to `/oauth/token` with your client credentials.

        ## Core Endpoints

        ### GET /users
        Retrieves a paginated list of users.

        **Parameters:**
        - `limit` (integer): Maximum number of users to return (default: 100)
        - `offset` (integer): Number of users to skip (default: 0)

        **Response:**
        ```json
        {
          "users": [
            {
              "id": 123,
              "name": "John Doe",
              "email": "john@example.com",
              "role": "admin"
            }
          ],
          "total": 150,
          "has_more": true
        }
        ```

        ### POST /users
        Creates a new user account.

        **Request Body:**
        ```json
        {
          "name": "Jane Smith",
          "email": "jane@example.com",
          "role": "user",
          "department": "engineering"
        }
        ```

        **Response:**
        ```json
        {
          "id": 124,
          "name": "Jane Smith",
          "email": "jane@example.com",
          "role": "user",
          "department": "engineering",
          "created_at": "2024-01-15T10:30:00Z"
        }
        ```

        ## Error Handling

        The API returns standard HTTP status codes:

        - `200 OK`: Success
        - `400 Bad Request`: Invalid request parameters
        - `401 Unauthorized`: Missing or invalid authentication
        - `403 Forbidden`: Insufficient permissions
        - `404 Not Found`: Resource not found
        - `429 Too Many Requests`: Rate limit exceeded
        - `500 Internal Server Error`: Server error

        ## Rate Limiting

        API requests are limited to:
        - 1000 requests per hour for authenticated users
        - 100 requests per hour for anonymous users
        """,
        'tags': ['api', 'rest', 'authentication', 'developers'],
        'last_modified': '2024-01-15T09:00:00Z'
    }


@pytest.fixture
def sample_related_documents():
    """Create sample related documents for testing."""
    return [
        {
            'document_id': 'api_reference_v1',
            'title': 'API Reference v1.0',
            'document_type': 'api_reference',
            'content': """
            # API Reference

            Complete reference for all API endpoints and data models.

            ## Authentication
            Uses OAuth 2.0 flow...

            ## Endpoints
            - GET /users
            - POST /users
            - PUT /users/{id}
            - DELETE /users/{id}
            """,
            'tags': ['api', 'reference'],
            'last_modified': '2023-12-01T10:00:00Z'
        },
        {
            'document_id': 'user_tutorial',
            'title': 'Getting Started Tutorial',
            'document_type': 'tutorial',
            'content': """
            # Getting Started with Our API

            Learn how to authenticate and make your first API calls.

            ## Step 1: Get Access Token
            Make a POST request to get your token...

            ## Step 2: Make Your First Call
            Use the token to call the API...
            """,
            'tags': ['tutorial', 'getting-started'],
            'last_modified': '2024-01-10T14:00:00Z'
        },
        {
            'document_id': 'security_guide',
            'title': 'API Security Best Practices',
            'document_type': 'security',
            'content': """
            # API Security Guide

            Security best practices for API usage and integration.

            ## Authentication Security
            Always use HTTPS and secure token storage...

            ## Rate Limiting
            Respect API rate limits to prevent abuse...
            """,
            'tags': ['security', 'api', 'best-practices'],
            'last_modified': '2024-01-12T11:00:00Z'
        }
    ]


@pytest.fixture
def sample_change_description():
    """Create sample change description for testing."""
    return {
        'change_type': 'major_change',
        'change_scope': 'major_section',
        'description': 'Updated authentication flow to include MFA requirements',
        'affected_sections': ['Authentication', 'Security'],
        'breaking_change': False,
        'estimated_impact': 'medium',
        'stakeholder_groups': ['developers', 'security_team']
    }


@pytest.fixture
def portfolio_changes():
    """Create sample portfolio changes for testing."""
    return [
        {
            'document_id': 'api_guide_v2',
            'change_description': {
                'change_type': 'major_change',
                'change_scope': 'major_section',
                'description': 'Updated authentication flow with MFA'
            }
        },
        {
            'document_id': 'user_tutorial',
            'change_description': {
                'change_type': 'minor_change',
                'change_scope': 'minor_section',
                'description': 'Updated screenshots for new UI'
            }
        }
    ]


@pytest.fixture
def portfolio_documents():
    """Create sample portfolio documents for testing."""
    return [
        {
            'document_id': 'api_guide_v2',
            'document_type': 'developer_guide',
            'content': 'API guide content...',
            'tags': ['api', 'guide']
        },
        {
            'document_id': 'user_tutorial',
            'document_type': 'tutorial',
            'content': 'Tutorial content...',
            'tags': ['tutorial', 'getting-started']
        },
        {
            'document_id': 'api_reference_v1',
            'document_type': 'api_reference',
            'content': 'API reference content...',
            'tags': ['api', 'reference']
        }
    ]


class TestChangeImpactAnalyzer:
    """Test the ChangeImpactAnalyzer class."""

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization of the change impact analyzer."""
        analyzer = ChangeImpactAnalyzer()
        success = analyzer._initialize_analyzer()
        assert success is True
        assert analyzer.initialized is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure when dependencies are not available."""
        original_available = CHANGE_IMPACT_AVAILABLE

        with patch('services.analysis_service.modules.change_impact_analyzer.CHANGE_IMPACT_AVAILABLE', False):
            analyzer = ChangeImpactAnalyzer()
            success = analyzer._initialize_analyzer()
            assert success is False
            assert analyzer.initialized is False

    @pytest.mark.asyncio
    async def test_extract_document_features(self, sample_document_data):
        """Test extraction of document features."""
        analyzer = ChangeImpactAnalyzer()

        features = analyzer._extract_document_features(sample_document_data)

        assert features['document_id'] == 'api_guide_v2'
        assert features['document_type'] == 'developer_guide'
        assert features['word_count'] > 0
        assert features['character_count'] > 0
        assert len(features['technical_terms']) > 0
        assert len(features['stakeholder_groups']) > 0

    @pytest.mark.asyncio
    async def test_identify_stakeholder_groups(self, sample_document_data):
        """Test stakeholder group identification."""
        analyzer = ChangeImpactAnalyzer()

        stakeholders = analyzer._identify_stakeholder_groups(sample_document_data)

        assert isinstance(stakeholders, list)
        assert len(stakeholders) > 0
        # Should identify developers based on content and document type
        assert 'developers' in stakeholders

    @pytest.mark.asyncio
    async def test_analyze_semantic_similarity(self, sample_document_data, sample_related_documents):
        """Test semantic similarity analysis."""
        analyzer = ChangeImpactAnalyzer()

        similarities = analyzer._analyze_semantic_similarity(sample_document_data, sample_related_documents)

        assert isinstance(similarities, dict)
        assert len(similarities) > 0

        # Check that similarity scores are reasonable
        for doc_id, similarity_data in similarities.items():
            assert 'similarity_score' in similarity_data
            assert 0.0 <= similarity_data['similarity_score'] <= 1.0
            assert 'similarity_level' in similarity_data

    @pytest.mark.asyncio
    async def test_analyze_content_overlap(self, sample_document_data, sample_related_documents):
        """Test content overlap analysis."""
        analyzer = ChangeImpactAnalyzer()

        overlaps = analyzer._analyze_content_overlap(sample_document_data, sample_related_documents)

        assert isinstance(overlaps, dict)
        assert len(overlaps) > 0

        # Check overlap structure
        for doc_id, overlap_data in overlaps.items():
            assert 'overlap_score' in overlap_data
            assert 'overlap_level' in overlap_data
            assert 'shared_sentences' in overlap_data

    @pytest.mark.asyncio
    async def test_analyze_relationships(self, sample_document_data, sample_related_documents):
        """Test relationship analysis between documents."""
        analyzer = ChangeImpactAnalyzer()

        relationships = analyzer._analyze_relationships(sample_document_data, sample_related_documents)

        assert isinstance(relationships, dict)
        assert len(relationships) > 0

        # Check relationship structure
        for doc_id, relationship_data in relationships.items():
            assert 'relationship_score' in relationship_data
            assert 'primary_relationship' in relationship_data
            assert 'relationship_factors' in relationship_data

    @pytest.mark.asyncio
    async def test_assess_change_severity(self, sample_change_description):
        """Test change severity assessment."""
        analyzer = ChangeImpactAnalyzer()

        severity = analyzer._assess_change_severity(sample_change_description)

        assert 'severity_score' in severity
        assert 'severity_level' in severity
        assert 'severity_factors' in severity

        # Major change should have appropriate severity
        assert severity['severity_level'] in ['low', 'medium', 'high', 'critical']

    @pytest.mark.asyncio
    async def test_assess_stakeholder_impact(self, sample_document_data):
        """Test stakeholder impact assessment."""
        analyzer = ChangeImpactAnalyzer()

        document_features = analyzer._extract_document_features(sample_document_data)
        change_severity = {'severity_score': 0.6, 'severity_level': 'medium'}

        stakeholder_impact = analyzer._assess_stakeholder_impact(document_features, change_severity)

        assert 'stakeholder_impact_score' in stakeholder_impact
        assert 'impact_level' in stakeholder_impact
        assert 'affected_stakeholder_groups' in stakeholder_impact

    @pytest.mark.asyncio
    async def test_calculate_change_impact(self, sample_document_data, sample_change_description, sample_related_documents):
        """Test overall change impact calculation."""
        analyzer = ChangeImpactAnalyzer()

        document_features = analyzer._extract_document_features(sample_document_data)
        relationships = analyzer._analyze_relationships(sample_document_data, sample_related_documents)

        impact_analysis = analyzer._calculate_change_impact(
            sample_change_description, document_features, relationships
        )

        assert 'overall_impact' in impact_analysis
        assert 'document_impacts' in impact_analysis
        assert 'change_analysis' in impact_analysis

        overall_impact = impact_analysis['overall_impact']
        assert 'overall_impact_score' in overall_impact
        assert 'impact_level' in overall_impact
        assert 'affected_documents_count' in overall_impact

    @pytest.mark.asyncio
    async def test_generate_impact_recommendations_critical(self, sample_document_data):
        """Test impact recommendation generation for critical impacts."""
        analyzer = ChangeImpactAnalyzer()

        impact_analysis = {
            'overall_impact': {
                'impact_level': 'critical',
                'affected_documents_count': 5,
                'high_impact_documents_count': 3
            },
            'document_impacts': {},
            'change_analysis': {'change_type': 'breaking_change'}
        }

        recommendations = analyzer._generate_impact_recommendations(impact_analysis)

        assert len(recommendations) > 0
        assert any('CRITICAL' in rec.upper() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_analyze_change_impact_full(self, sample_document_data, sample_change_description, sample_related_documents):
        """Test full change impact analysis."""
        analyzer = ChangeImpactAnalyzer()

        result = await analyzer.analyze_change_impact(
            document_id="api_guide_v2",
            document_data=sample_document_data,
            change_description=sample_change_description,
            related_documents=sample_related_documents
        )

        assert result['document_id'] == 'api_guide_v2'
        assert 'impact_analysis' in result
        assert 'document_features' in result
        assert 'related_documents_analysis' in result
        assert 'recommendations' in result
        assert 'processing_time' in result

        # Should have analyzed relationships
        assert len(result['related_documents_analysis']) > 0

        # Should have recommendations
        assert len(result['recommendations']) > 0

    @pytest.mark.asyncio
    async def test_analyze_portfolio_change_impact(self, portfolio_changes, portfolio_documents):
        """Test portfolio change impact analysis."""
        analyzer = ChangeImpactAnalyzer()

        result = await analyzer.analyze_portfolio_change_impact(
            changes=portfolio_changes,
            document_portfolio=portfolio_documents
        )

        assert 'portfolio_summary' in result
        assert 'change_impacts' in result
        assert 'processing_time' in result

        portfolio_summary = result['portfolio_summary']
        assert 'total_changes' in portfolio_summary
        assert 'analyzed_changes' in portfolio_summary
        assert 'average_impact_score' in portfolio_summary

        # Should have analyzed changes
        assert len(result['change_impacts']) > 0

    @pytest.mark.asyncio
    async def test_analyze_change_impact_minimal_data(self):
        """Test change impact analysis with minimal data."""
        analyzer = ChangeImpactAnalyzer()

        minimal_document = {
            'document_id': 'minimal_doc',
            'content': 'Some minimal content'
        }

        minimal_change = {
            'change_type': 'minor_change',
            'description': 'Small update'
        }

        result = await analyzer.analyze_change_impact(
            document_id="minimal_doc",
            document_data=minimal_document,
            change_description=minimal_change,
            related_documents=[]
        )

        assert result['document_id'] == 'minimal_doc'
        assert 'impact_analysis' in result
        assert result['impact_analysis']['overall_impact']['overall_impact_score'] >= 0.0

    @pytest.mark.asyncio
    async def test_update_impact_thresholds(self):
        """Test updating impact analysis thresholds."""
        analyzer = ChangeImpactAnalyzer()

        custom_thresholds = {
            'semantic_similarity': {
                'high_impact': 0.9,
                'medium_impact': 0.7,
                'low_impact': 0.5
            }
        }

        success = analyzer.update_impact_thresholds(custom_thresholds)
        assert success is True
        assert analyzer.impact_thresholds['semantic_similarity']['high_impact'] == 0.9


@pytest.mark.asyncio
class TestChangeImpactIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_analyze_change_impact_function(self, sample_document_data, sample_change_description, sample_related_documents):
        """Test the convenience function for change impact analysis."""
        with patch('services.analysis_service.modules.change_impact_analyzer.change_impact_analyzer') as mock_analyzer:
            mock_analyzer.analyze_change_impact.return_value = {
                'document_id': 'api_guide_v2',
                'impact_analysis': {
                    'overall_impact': {
                        'overall_impact_score': 0.65,
                        'impact_level': 'high',
                        'affected_documents_count': 3,
                        'high_impact_documents_count': 2
                    },
                    'document_impacts': {},
                    'change_analysis': sample_change_description
                },
                'document_features': {},
                'related_documents_analysis': {},
                'recommendations': [
                    '⚠️ HIGH IMPACT: Schedule change review within 2-4 weeks',
                    'Focus on high-risk areas identified in assessment'
                ],
                'processing_time': 1.2,
                'analysis_timestamp': 1234567890
            }

            result = await analyze_change_impact(
                document_id="api_guide_v2",
                document_data=sample_document_data,
                change_description=sample_change_description,
                related_documents=sample_related_documents
            )

            assert result['document_id'] == 'api_guide_v2'
            assert result['impact_analysis']['overall_impact']['impact_level'] == 'high'
            mock_analyzer.analyze_change_impact.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_portfolio_change_impact_function(self, portfolio_changes, portfolio_documents):
        """Test the convenience function for portfolio change impact analysis."""
        with patch('services.analysis_service.modules.change_impact_analyzer.change_impact_analyzer') as mock_analyzer:
            mock_analyzer.analyze_portfolio_change_impact.return_value = {
                'portfolio_summary': {
                    'total_changes': 2,
                    'analyzed_changes': 2,
                    'average_impact_score': 0.55,
                    'high_impact_changes_count': 1,
                    'most_impacted_documents': [
                        {'document_id': 'api_guide_v2', 'impact_frequency': 2}
                    ]
                },
                'change_impacts': [],
                'processing_time': 2.1,
                'analysis_timestamp': 1234567890
            }

            result = await analyze_portfolio_change_impact(
                changes=portfolio_changes,
                document_portfolio=portfolio_documents
            )

            assert result['portfolio_summary']['total_changes'] == 2
            assert result['portfolio_summary']['average_impact_score'] == 0.55
            mock_analyzer.analyze_portfolio_change_impact.assert_called_once()


class TestChangeImpactHandlers:
    """Test the analysis handlers integration."""

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        client = Mock()
        client.doc_store_url.return_value = "http://docstore:5000"
        client.get_json = Mock()
        return client

    @pytest.mark.asyncio
    async def test_handle_change_impact_analysis_success(self, mock_service_client, sample_document_data, sample_change_description, sample_related_documents):
        """Test successful change impact analysis handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import ChangeImpactAnalysisRequest

        with patch('services.analysis_service.modules.analysis_handlers.analyze_change_impact') as mock_analyze:

            mock_analyze.return_value = {
                'document_id': 'api_guide_v2',
                'impact_analysis': {
                    'overall_impact': {
                        'overall_impact_score': 0.65,
                        'impact_level': 'high',
                        'affected_documents_count': 3,
                        'high_impact_documents_count': 2
                    },
                    'document_impacts': {},
                    'change_analysis': sample_change_description
                },
                'document_features': {},
                'related_documents_analysis': {},
                'recommendations': ['High impact change detected'],
                'processing_time': 1.2,
                'analysis_timestamp': 1234567890
            }

            request = ChangeImpactAnalysisRequest(
                document_id="api_guide_v2",
                document_data=sample_document_data,
                change_description=sample_change_description,
                related_documents=sample_related_documents
            )

            result = await AnalysisHandlers.handle_change_impact_analysis(request)

            assert result.document_id == 'api_guide_v2'
            assert result.impact_analysis['overall_impact']['impact_level'] == 'high'
            assert len(result.recommendations) > 0
            assert result.processing_time == 1.2

    @pytest.mark.asyncio
    async def test_handle_portfolio_change_impact_success(self, mock_service_client, portfolio_changes, portfolio_documents):
        """Test successful portfolio change impact analysis handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import PortfolioChangeImpactRequest

        with patch('services.analysis_service.modules.analysis_handlers.analyze_portfolio_change_impact') as mock_analyze:

            mock_analyze.return_value = {
                'portfolio_summary': {
                    'total_changes': 2,
                    'analyzed_changes': 2,
                    'average_impact_score': 0.55,
                    'high_impact_changes_count': 1
                },
                'change_impacts': [],
                'processing_time': 2.1,
                'analysis_timestamp': 1234567890
            }

            request = PortfolioChangeImpactRequest(
                changes=portfolio_changes,
                document_portfolio=portfolio_documents
            )

            result = await AnalysisHandlers.handle_portfolio_change_impact_analysis(request)

            assert result.portfolio_summary['total_changes'] == 2
            assert result.portfolio_summary['analyzed_changes'] == 2
            assert result.processing_time == 2.1

    @pytest.mark.asyncio
    async def test_handle_change_impact_analysis_error(self, mock_service_client, sample_document_data, sample_change_description):
        """Test change impact analysis error handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import ChangeImpactAnalysisRequest

        with patch('services.analysis_service.modules.analysis_handlers.analyze_change_impact') as mock_analyze:

            mock_analyze.side_effect = Exception("Analysis failed")

            request = ChangeImpactAnalysisRequest(
                document_id="api_guide_v2",
                document_data=sample_document_data,
                change_description=sample_change_description
            )

            result = await AnalysisHandlers.handle_change_impact_analysis(request)

            assert result.document_id == 'api_guide_v2'
            assert result.impact_analysis['overall_impact']['impact_level'] == 'error'
            assert 'Analysis failed due to error' in result.recommendations[0]


if __name__ == "__main__":
    pytest.main([__file__])
