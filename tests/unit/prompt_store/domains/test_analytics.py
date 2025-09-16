"""Tests for analytics domain.

Tests covering repository, service, and handler layers for usage analytics.
"""

import pytest
from unittest.mock import Mock, patch

from services.prompt_store.domain.analytics.repository import AnalyticsRepository
from services.prompt_store.domain.analytics.service import AnalyticsService
from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers


@pytest.mark.unit
class TestAnalyticsRepository:
    """Test AnalyticsRepository operations."""

    def test_record_usage_event_success(self, prompt_store_db):
        """Test successful usage event recording."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        prompt = prompt_service.create_entity({
            "name": "analytics_test_prompt",
            "category": "test",
            "content": "Test content",
            "created_by": "test_user"
        })

        repo = AnalyticsRepository()
        event_data = {
            "prompt_id": prompt.id,
            "user_id": "test_user_123",
            "session_id": "session_456",
            "event_type": "usage",
            "metric_value": 0.85,
            "metadata": {"model": "gpt-4", "tokens": 150}
        }

        usage = repo.record_usage_event(event_data)
        assert usage.prompt_id == prompt.id
        assert usage.user_id == "test_user_123"
        assert usage.metric_value == 0.85

    def test_get_usage_stats_success(self, prompt_store_db):
        """Test getting usage statistics."""
        repo = AnalyticsRepository()

        # Record some test data
        for i in range(3):
            repo.record_usage_event({
                "prompt_id": f"prompt_{i}",
                "user_id": f"user_{i}",
                "session_id": f"session_{i}",
                "event_type": "usage",
                "metric_value": 0.8 + i * 0.05
            })

        stats = repo.get_usage_stats()
        assert "total_events" in stats
        assert "average_metric" in stats
        assert stats["total_events"] >= 3

    def test_get_prompt_performance_success(self, prompt_store_db):
        """Test getting prompt performance metrics."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        prompt = prompt_service.create_entity({
            "name": "performance_test",
            "category": "test",
            "content": "Test content",
            "created_by": "test_user"
        })

        repo = AnalyticsRepository()

        # Record performance data
        for i in range(5):
            repo.record_usage_event({
                "prompt_id": prompt.id,
                "user_id": f"user_{i}",
                "session_id": f"session_{i}",
                "event_type": "performance",
                "metric_value": 0.7 + i * 0.05
            })

        performance = repo.get_prompt_performance(prompt.id)
        assert performance["prompt_id"] == prompt.id
        assert "average_score" in performance
        assert "usage_count" in performance


@pytest.mark.unit
class TestAnalyticsService:
    """Test AnalyticsService business logic."""

    def test_get_summary_stats_success(self, prompt_store_db):
        """Test getting summary statistics."""
        service = AnalyticsService()
        stats = service.get_summary_stats()

        assert "total_prompts" in stats
        assert "total_usage_events" in stats
        assert "top_performing_prompts" in stats
        assert "recent_activity" in stats

    def test_get_prompt_analytics_success(self, prompt_store_db):
        """Test getting prompt-specific analytics."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        prompt = prompt_service.create_entity({
            "name": "analytics_prompt",
            "category": "test",
            "content": "Test content",
            "created_by": "test_user"
        })

        service = AnalyticsService()
        analytics = service.get_prompt_analytics(prompt.id)

        assert analytics["prompt_id"] == prompt.id
        assert "performance_metrics" in analytics
        assert "usage_trends" in analytics
        assert "comparison_data" in analytics


@pytest.mark.unit
class TestAnalyticsHandlers:
    """Test AnalyticsHandlers HTTP operations."""

    def test_handle_get_summary_success(self):
        """Test successful summary analytics handler."""
        handlers = AnalyticsHandlers()

        with patch.object(handlers.analytics_service, 'get_summary_stats') as mock_summary:
            mock_summary.return_value = {
                "total_prompts": 10,
                "total_usage_events": 150,
                "top_performing_prompts": [],
                "recent_activity": []
            }

            result = handlers.handle_get_summary()

            assert result["success"] is True
            assert result["data"]["total_prompts"] == 10
            mock_summary.assert_called_once()

    def test_handle_get_prompt_analytics_success(self):
        """Test successful prompt analytics handler."""
        handlers = AnalyticsHandlers()

        with patch.object(handlers.analytics_service, 'get_prompt_analytics') as mock_analytics:
            mock_analytics.return_value = {
                "prompt_id": "test_id",
                "performance_metrics": {"average_score": 0.85},
                "usage_trends": [],
                "comparison_data": {}
            }

            result = handlers.handle_get_prompt_analytics("test_id")

            assert result["success"] is True
            assert result["data"]["prompt_id"] == "test_id"
            mock_analytics.assert_called_once_with("test_id")
