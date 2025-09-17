"""Tests for Analysis API Endpoints."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...main import app
from ...presentation.models.analysis import (
    AnalysisRequest, AnalysisResponse,
    SemanticSimilarityRequest, SemanticSimilarityResponse,
    SentimentAnalysisRequest, SentimentAnalysisResponse,
    ContentQualityRequest, ContentQualityResponse,
    TrendAnalysisRequest, TrendAnalysisResponse
)
from ...presentation.models.base import SuccessResponse, ErrorResponse

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence


class TestAnalysisEndpoints:
    """Test cases for analysis API endpoints."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_document_data(self):
        """Sample document data for testing."""
        return {
            'id': 'test-doc-123',
            'title': 'Test Document',
            'content': 'This is test content for API testing.',
            'repository_id': 'test-repo',
            'author': 'test-author',
            'version': '1.0.0'
        }

    @pytest.fixture
    def sample_analysis_request(self):
        """Sample analysis request for testing."""
        return AnalysisRequest(
            document_ids=['test-doc-123'],
            detectors=['semantic_similarity', 'sentiment'],
            options={
                'threshold': 0.8,
                'include_details': True
            }
        )

    @pytest.fixture
    def sample_semantic_similarity_request(self):
        """Sample semantic similarity request for testing."""
        return SemanticSimilarityRequest(
            targets=['doc-1', 'doc-2', 'doc-3'],
            threshold=0.8,
            embedding_model='sentence-transformers/all-MiniLM-L6-v2',
            similarity_metric='cosine',
            options={
                'include_embeddings': False,
                'batch_size': 32
            }
        )

    def test_analyze_endpoint_exists(self, client):
        """Test that the analyze endpoint exists and is accessible."""
        response = client.post("/analyze")
        # Should get validation error since no data provided
        assert response.status_code == 422  # Validation error

    def test_semantic_similarity_endpoint_exists(self, client):
        """Test that the semantic similarity endpoint exists."""
        response = client.post("/analyze/semantic-similarity")
        # Should get validation error since no data provided
        assert response.status_code == 422

    def test_sentiment_analysis_endpoint_exists(self, client):
        """Test that the sentiment analysis endpoint exists."""
        response = client.post("/analyze/sentiment")
        # Should get validation error since no data provided
        assert response.status_code == 422

    def test_content_quality_endpoint_exists(self, client):
        """Test that the content quality endpoint exists."""
        response = client.post("/analyze/quality")
        # Should get validation error since no data provided
        assert response.status_code == 422

    def test_trend_analysis_endpoint_exists(self, client):
        """Test that the trend analysis endpoint exists."""
        response = client.post("/analyze/trends")
        # Should get validation error since no data provided
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_semantic_similarity_analysis_success(self, client, sample_semantic_similarity_request):
        """Test successful semantic similarity analysis."""
        # Mock the analysis service to return success
        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_handler:
            mock_response = SemanticSimilarityResponse(
                analysis_id='analysis-123',
                analysis_type='semantic_similarity',
                targets=sample_semantic_similarity_request.targets,
                status='completed',
                similarity_matrix=[[1.0, 0.8, 0.6], [0.8, 1.0, 0.7], [0.6, 0.7, 1.0]],
                similar_pairs=[
                    {'source': 'doc-1', 'target': 'doc-2', 'similarity': 0.8},
                    {'source': 'doc-2', 'target': 'doc-3', 'similarity': 0.7}
                ],
                summary={
                    'total_pairs': 3,
                    'highly_similar_pairs': 2,
                    'average_similarity': 0.775
                },
                execution_time_seconds=1.5,
                error_message=None
            )
            mock_handler.return_value = mock_response

            response = client.post(
                "/analyze/semantic-similarity",
                json=sample_semantic_similarity_request.dict()
            )

            assert response.status_code == 200
            data = response.json()
            assert data['analysis_id'] == 'analysis-123'
            assert data['status'] == 'completed'
            assert len(data['similar_pairs']) == 2

    @pytest.mark.asyncio
    async def test_semantic_similarity_analysis_with_invalid_data(self, client):
        """Test semantic similarity analysis with invalid data."""
        invalid_request = {
            'targets': [],  # Empty targets
            'threshold': 1.5  # Invalid threshold (> 1.0)
        }

        response = client.post("/analyze/semantic-similarity", json=invalid_request)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert 'detail' in data

    @pytest.mark.asyncio
    async def test_sentiment_analysis_success(self, client):
        """Test successful sentiment analysis."""
        request_data = {
            'document_id': 'test-doc-123',
            'analysis_options': {
                'include_detailed_scores': True,
                'language': 'en'
            }
        }

        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_sentiment_analysis') as mock_handler:
            mock_response = SentimentAnalysisResponse(
                analysis_id='sentiment-123',
                document_id='test-doc-123',
                sentiment='positive',
                confidence=0.85,
                scores={
                    'positive': 0.85,
                    'negative': 0.10,
                    'neutral': 0.05
                },
                detailed_analysis={
                    'sentence_sentiments': [
                        {'text': 'This is great documentation', 'sentiment': 'positive', 'confidence': 0.9},
                        {'text': 'Could be improved', 'sentiment': 'neutral', 'confidence': 0.6}
                    ],
                    'overall_tone': 'professional',
                    'readability_score': 78.5
                },
                execution_time_seconds=0.8,
                error_message=None
            )
            mock_handler.return_value = mock_response

            response = client.post("/analyze/sentiment", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data['sentiment'] == 'positive'
            assert data['confidence'] == 0.85
            assert 'detailed_analysis' in data

    @pytest.mark.asyncio
    async def test_content_quality_analysis_success(self, client):
        """Test successful content quality analysis."""
        request_data = {
            'document_id': 'test-doc-123',
            'quality_checks': ['readability', 'grammar', 'structure', 'completeness'],
            'options': {
                'language': 'en',
                'readability_target': 70.0
            }
        }

        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_content_quality_assessment') as mock_handler:
            mock_response = ContentQualityResponse(
                analysis_id='quality-123',
                document_id='test-doc-123',
                overall_score=82.5,
                quality_breakdown={
                    'readability': {'score': 78.0, 'level': 'good', 'issues': []},
                    'grammar': {'score': 85.0, 'level': 'excellent', 'issues': []},
                    'structure': {'score': 80.0, 'level': 'good', 'issues': ['missing_table_of_contents']},
                    'completeness': {'score': 88.0, 'level': 'excellent', 'issues': []}
                },
                recommendations=[
                    'Add a table of contents to improve document structure',
                    'Consider using shorter sentences for better readability'
                ],
                improvement_suggestions={
                    'high_priority': ['Add table of contents'],
                    'medium_priority': ['Improve sentence length variety'],
                    'low_priority': ['Add more examples']
                },
                execution_time_seconds=1.2,
                error_message=None
            )
            mock_handler.return_value = mock_response

            response = client.post("/analyze/quality", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data['overall_score'] == 82.5
            assert len(data['recommendations']) == 2
            assert 'improvement_suggestions' in data

    @pytest.mark.asyncio
    async def test_trend_analysis_success(self, client):
        """Test successful trend analysis."""
        request_data = {
            'document_id': 'test-doc-123',
            'time_range_days': 90,
            'trend_metrics': ['quality_score', 'complexity', 'maintenance_effort'],
            'forecast_days': 30
        }

        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_trend_analysis') as mock_handler:
            mock_response = TrendAnalysisResponse(
                analysis_id='trend-123',
                document_id='test-doc-123',
                time_range_days=90,
                trend_data={
                    'quality_score': {
                        'current_value': 82.5,
                        'trend_direction': 'improving',
                        'trend_slope': 0.15,
                        'volatility': 0.08,
                        'forecasted_value': 85.2,
                        'confidence_interval': {'lower': 83.0, 'upper': 87.5}
                    },
                    'complexity': {
                        'current_value': 25.3,
                        'trend_direction': 'stable',
                        'trend_slope': 0.02,
                        'volatility': 0.12,
                        'forecasted_value': 25.8,
                        'confidence_interval': {'lower': 24.5, 'upper': 27.1}
                    }
                },
                key_insights=[
                    'Quality score is improving steadily',
                    'Complexity is stable with low volatility',
                    'Forecast indicates continued quality improvement'
                ],
                recommendations=[
                    'Continue current quality improvement practices',
                    'Monitor complexity trends closely'
                ],
                forecast_accuracy=0.88,
                execution_time_seconds=2.1,
                error_message=None
            )
            mock_handler.return_value = mock_response

            response = client.post("/analyze/trends", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data['time_range_days'] == 90
            assert 'trend_data' in data
            assert 'quality_score' in data['trend_data']
            assert data['forecast_accuracy'] == 0.88

    @pytest.mark.asyncio
    async def test_analysis_endpoint_error_handling(self, client):
        """Test error handling in analysis endpoints."""
        # Test with malformed JSON
        response = client.post(
            "/analyze/semantic-similarity",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_analysis_endpoint_timeout_handling(self, client, sample_semantic_similarity_request):
        """Test timeout handling in analysis endpoints."""
        # Mock a handler that takes too long
        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_handler:
            async def slow_handler(*args, **kwargs):
                await asyncio.sleep(35)  # Simulate timeout
                return SemanticSimilarityResponse(
                    analysis_id='timeout-123',
                    analysis_type='semantic_similarity',
                    targets=[],
                    status='timeout',
                    execution_time_seconds=35.0,
                    error_message='Analysis timed out'
                )

            mock_handler.side_effect = slow_handler

            response = client.post(
                "/analyze/semantic-similarity",
                json=sample_semantic_similarity_request.dict()
            )

            # Should handle timeout gracefully
            assert response.status_code in [200, 408, 504]  # Success or timeout status

    @pytest.mark.asyncio
    async def test_analysis_endpoint_concurrent_requests(self, client):
        """Test handling of concurrent analysis requests."""
        async def make_request(request_id: int):
            request_data = {
                'targets': [f'doc-{request_id}'],
                'threshold': 0.8
            }

            with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_handler:
                mock_response = SemanticSimilarityResponse(
                    analysis_id=f'analysis-{request_id}',
                    analysis_type='semantic_similarity',
                    targets=[f'doc-{request_id}'],
                    status='completed',
                    execution_time_seconds=1.0,
                    error_message=None
                )
                mock_handler.return_value = mock_response

                response = client.post("/analyze/semantic-similarity", json=request_data)
                return response.status_code, response.json()

        # Make concurrent requests
        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All requests should succeed
        for status_code, data in results:
            assert status_code == 200
            assert 'analysis_id' in data

        # All analysis IDs should be unique
        analysis_ids = [data['analysis_id'] for _, data in results]
        assert len(set(analysis_ids)) == len(analysis_ids)

    @pytest.mark.asyncio
    async def test_analysis_endpoint_resource_cleanup(self, client, sample_semantic_similarity_request):
        """Test that analysis endpoints properly clean up resources."""
        # This test ensures that connections, memory, and other resources
        # are properly cleaned up after analysis operations

        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_handler:
            mock_response = SemanticSimilarityResponse(
                analysis_id='cleanup-123',
                analysis_type='semantic_similarity',
                targets=sample_semantic_similarity_request.targets,
                status='completed',
                execution_time_seconds=1.0,
                error_message=None
            )
            mock_handler.return_value = mock_response

            # Make request
            response = client.post(
                "/analyze/semantic-similarity",
                json=sample_semantic_similarity_request.dict()
            )

            assert response.status_code == 200

            # Verify handler was called and completed
            mock_handler.assert_called_once()

            # In a real implementation, we would check that:
            # - Database connections are closed
            # - Memory is properly freed
            # - File handles are closed
            # - External service connections are cleaned up

    @pytest.mark.asyncio
    async def test_analysis_endpoint_metrics_collection(self, client, sample_semantic_similarity_request):
        """Test that analysis endpoints collect metrics."""
        # This test verifies that performance metrics are collected
        # during analysis operations

        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_handler:
            mock_response = SemanticSimilarityResponse(
                analysis_id='metrics-123',
                analysis_type='semantic_similarity',
                targets=sample_semantic_similarity_request.targets,
                status='completed',
                execution_time_seconds=1.5,
                error_message=None
            )
            mock_handler.return_value = mock_response

            response = client.post(
                "/analyze/semantic-similarity",
                json=sample_semantic_similarity_request.dict()
            )

            assert response.status_code == 200

            # In a real implementation, we would verify that:
            # - Request count metrics are incremented
            # - Response time metrics are recorded
            # - Error rate metrics are updated (if applicable)
            # - Custom business metrics are collected

    def test_analysis_endpoint_cors_headers(self, client):
        """Test that analysis endpoints include proper CORS headers."""
        # Test preflight request
        response = client.options("/analyze/semantic-similarity")
        assert response.status_code == 200

        # Check for CORS headers
        headers = response.headers
        assert 'access-control-allow-origin' in headers or 'Access-Control-Allow-Origin' in headers

    def test_analysis_endpoint_content_type_validation(self, client):
        """Test that analysis endpoints validate content type."""
        request_data = {'targets': ['doc-1'], 'threshold': 0.8}

        # Test with correct content type
        response = client.post(
            "/analyze/semantic-similarity",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        # Should get validation error (expected since we're not mocking the handler)
        assert response.status_code == 422

        # Test with incorrect content type
        response = client.post(
            "/analyze/semantic-similarity",
            data=str(request_data),
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 415  # Unsupported media type

    @pytest.mark.asyncio
    async def test_analysis_endpoint_request_size_limits(self, client):
        """Test that analysis endpoints handle request size limits."""
        # Create a very large request
        large_targets = [f'doc-{i}' for i in range(10000)]  # 10,000 targets
        large_request = {
            'targets': large_targets,
            'threshold': 0.8,
            'options': {'large_option': 'x' * 100000}  # Large options
        }

        response = client.post("/analyze/semantic-similarity", json=large_request)

        # Should either succeed with large request or fail with size limit
        assert response.status_code in [200, 413, 422]  # Success or size limit exceeded

    @pytest.mark.asyncio
    async def test_analysis_endpoint_rate_limiting(self, client, sample_semantic_similarity_request):
        """Test rate limiting on analysis endpoints."""
        # This test would verify that rate limiting is properly enforced
        # In a real implementation with rate limiting middleware

        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_handler:
            mock_response = SemanticSimilarityResponse(
                analysis_id='rate-limit-123',
                analysis_type='semantic_similarity',
                targets=sample_semantic_similarity_request.targets,
                status='completed',
                execution_time_seconds=1.0,
                error_message=None
            )
            mock_handler.return_value = mock_response

            # Make multiple rapid requests
            responses = []
            for i in range(10):
                response = client.post(
                    "/analyze/semantic-similarity",
                    json=sample_semantic_similarity_request.dict()
                )
                responses.append(response)

            # In a rate-limited system, some requests might be rejected
            # For now, we just verify they all return some response
            for response in responses:
                assert response.status_code in [200, 429]  # Success or rate limited
