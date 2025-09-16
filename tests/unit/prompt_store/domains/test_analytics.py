"""Unit tests for analytics domain functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from services.prompt_store.domain.analytics.service import AnalyticsService
from services.prompt_store.domain.analytics.repository import AnalyticsRepository
from services.prompt_store.domain.analytics.entities import (
    PromptPerformanceMetrics,
    UserSatisfactionScore
)


@pytest.fixture
def analytics_repository():
    """Create a mock analytics repository."""
    repo = MagicMock(spec=AnalyticsRepository)
    return repo


@pytest.fixture
def analytics_service(analytics_repository):
    """Create analytics service with mocked repository."""
    service = AnalyticsService()
    service.repository = analytics_repository
    return service


@pytest.mark.asyncio
class TestAnalyticsService:
    """Test cases for analytics service functionality."""

    async def test_record_usage_metrics_success(self, analytics_service):
        """Test recording usage metrics successfully."""
        # Mock the repository methods
        analytics_service.repository.get_metrics_by_prompt_version.return_value = None
        analytics_service.repository.save = MagicMock()

        # Mock cache
        with patch('services.prompt_store.domain.analytics.service.prompt_store_cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            # Test data
            prompt_id = "test_prompt_123"
            version = 1
            usage_data = {
                "success": True,
                "response_time_ms": 1500,
                "input_tokens": 100,
                "output_tokens": 200,
                "llm_service": "gpt-4"
            }

            # Execute
            await analytics_service.record_usage_metrics(prompt_id, version, usage_data)

            # Verify repository was called to save metrics
            analytics_service.repository.save.assert_called_once()
            saved_entity = analytics_service.repository.save.call_args[0][0]

            # Verify entity properties
            assert saved_entity.prompt_id == prompt_id
            assert saved_entity.version == version
            assert saved_entity.total_requests == 1
            assert saved_entity.successful_requests == 1
            assert saved_entity.failed_requests == 0
            assert saved_entity.total_tokens_used == 300  # 100 + 200

    async def test_record_usage_metrics_existing_entity(self, analytics_service):
        """Test recording metrics when entity already exists."""
        # Mock existing metrics
        existing_metrics = PromptPerformanceMetrics(
            id="existing_id",
            prompt_id="test_prompt_123",
            version=1,
            total_requests=5,
            successful_requests=4,
            failed_requests=1,
            average_response_time_ms=1200.0,
            total_tokens_used=1000,
            cost_estimate_usd=0.5
        )

        analytics_service.repository.get_metrics_by_prompt_version.return_value = existing_metrics
        analytics_service.repository.update = AsyncMock()

        with patch('services.prompt_store.domain.analytics.service.prompt_store_cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            # Test data
            usage_data = {
                "success": True,
                "response_time_ms": 1500,
                "input_tokens": 50,
                "output_tokens": 75
            }

            await analytics_service.record_usage_metrics("test_prompt_123", 1, usage_data)

            # Verify update was called
            analytics_service.repository.update_entity.assert_called_once()
            updated_data = analytics_service.repository.update_entity.call_args[0][1]

            # Verify updated values
            assert updated_data["total_requests"] == 6  # 5 + 1
            assert updated_data["successful_requests"] == 5  # 4 + 1

    async def test_record_user_satisfaction(self, analytics_service):
        """Test recording user satisfaction feedback."""
        analytics_service.repository.create_satisfaction_score = MagicMock()

        satisfaction_data = {
            "prompt_id": "test_prompt_123",
            "user_id": "user_456",
            "session_id": "session_789",
            "rating": 4.5,
            "feedback_text": "Great prompt!",
            "context_tags": ["code_review", "python"],
            "use_case_category": "development"
        }

        result = await analytics_service.record_user_satisfaction(satisfaction_data)

        # Verify repository was called
        analytics_service.repository.create_satisfaction_score.assert_called_once()

        # Verify returned entity
        assert isinstance(result, UserSatisfactionScore)
        assert result.prompt_id == "test_prompt_123"
        assert result.user_id == "user_456"
        assert result.rating == 4.5
        assert result.feedback_text == "Great prompt!"

    async def test_get_analytics_dashboard(self, analytics_service):
        """Test getting comprehensive analytics dashboard."""
        # Mock the summary methods
        analytics_service._get_analytics_summary = AsyncMock(return_value={
            "total_prompts": 10,
            "total_requests": 150
        })
        analytics_service._get_performance_overview = AsyncMock(return_value={
            "top_performing_prompts": []
        })
        analytics_service._get_usage_trends = AsyncMock(return_value={
            "daily_usage": []
        })

        result = await analytics_service.get_analytics_dashboard(days=30)

        assert result["time_range_days"] == 30
        assert "summary" in result
        assert "performance_metrics" in result
        assert "usage_trends" in result

    async def test_calculate_cost_estimate_gpt4(self, analytics_service):
        """Test cost calculation for GPT-4."""
        cost = analytics_service._calculate_cost_estimate("gpt-4", 100, 200)
        expected = (100 / 1000) * 0.03 + (200 / 1000) * 0.06  # 0.003 + 0.012 = 0.015
        assert cost == pytest.approx(expected, rel=1e-6)

    async def test_calculate_cost_estimate_gpt3(self, analytics_service):
        """Test cost calculation for GPT-3.5-turbo."""
        cost = analytics_service._calculate_cost_estimate("gpt-3.5-turbo", 100, 200)
        expected = (100 / 1000) * 0.0015 + (200 / 1000) * 0.002  # 0.00015 + 0.0004 = 0.00055
        assert cost == pytest.approx(expected, rel=1e-6)

    async def test_calculate_cost_estimate_unknown(self, analytics_service):
        """Test cost calculation for unknown service defaults to GPT-3.5."""
        cost = analytics_service._calculate_cost_estimate("unknown", 100, 200)
        # Should default to GPT-3.5-turbo rates
        expected = (100 / 1000) * 0.0015 + (200 / 1000) * 0.002
        assert cost == pytest.approx(expected, rel=1e-6)


class TestAnalyticsRepository:
    """Test cases for analytics repository functionality."""

    @patch('services.prompt_store.domain.analytics.repository.execute_query')
    def test_get_metrics_by_prompt_version_found(self, mock_execute_query):
        """Test getting metrics by prompt version when found."""
        mock_execute_query.return_value = [{
            'id': 'test_id',
            'prompt_id': 'test_prompt',
            'version': 1,
            'total_requests': 10,
            'successful_requests': 8,
            'failed_requests': 2,
            'average_response_time_ms': 1200.0,
            'total_tokens_used': 1500,
            'cost_estimate_usd': 0.75,
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-02T00:00:00'
        }]

        repo = AnalyticsRepository()
        result = repo.get_metrics_by_prompt_version('test_prompt', 1)

        assert isinstance(result, PromptPerformanceMetrics)
        assert result.prompt_id == 'test_prompt'
        assert result.version == 1
        assert result.total_requests == 10

    @patch('services.prompt_store.domain.analytics.repository.execute_query')
    def test_get_metrics_by_prompt_version_not_found(self, mock_execute_query):
        """Test getting metrics by prompt version when not found."""
        mock_execute_query.return_value = []

        repo = AnalyticsRepository()
        result = repo.get_metrics_by_prompt_version('test_prompt', 1)

        assert result is None

    @patch('services.prompt_store.domain.analytics.repository.execute_query')
    def test_create_satisfaction_score(self, mock_execute_query):
        """Test creating user satisfaction score."""
        repo = AnalyticsRepository()
        score_data = {
            'id': 'test_id',
            'prompt_id': 'test_prompt',
            'user_id': 'test_user',
            'session_id': 'test_session',
            'rating': 4.5,
            'feedback_text': 'Good prompt!',
            'context_tags': ['test', 'review'],
            'use_case_category': 'development',
            'created_at': '2024-01-01T00:00:00'
        }

        repo.create_satisfaction_score(score_data)

        # Verify execute_query was called with correct parameters
        mock_execute_query.assert_called_once()
        call_args = mock_execute_query.call_args

        # Check SQL contains expected fields
        sql = call_args[0][0]
        assert 'user_satisfaction_scores' in sql
        assert 'rating' in sql
        assert 'feedback_text' in sql

        # Check parameters
        params = call_args[0][1]
        assert params[0] == 'test_id'
        assert params[1] == 'test_prompt'
        assert params[2] == 'test_user'
        assert params[3] == 'test_session'
        assert params[4] == 4.5
        assert params[5] == 'Good prompt!'
        assert params[6] == '["test", "review"]'  # JSON encoded
        assert params[7] == 'development'
        assert params[8] == '2024-01-01T00:00:00'