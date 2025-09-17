"""Unit tests for LLM Gateway Metrics Collector.

Tests the comprehensive metrics collection functionality including
request tracking, cost analysis, performance monitoring, and error handling.
"""

import pytest
import asyncio
import time
from collections import deque
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

# Adjust path for local imports
import sys
from pathlib import Path

# Add the LLM Gateway service directory to Python path
llm_gateway_path = Path(__file__).parent.parent.parent.parent / "services" / "llm-gateway"
sys.path.insert(0, str(llm_gateway_path))

from modules.metrics_collector import MetricsCollector, RequestMetrics, ProviderMetrics

# Test markers for parallel execution
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.metrics
]


class TestMetricsCollector:
    """Test suite for MetricsCollector class."""

    @pytest.fixture
    def metrics_collector(self):
        """Create a MetricsCollector instance for testing."""
        return MetricsCollector()

    def test_metrics_collector_initialization(self, metrics_collector):
        """Test that MetricsCollector initializes correctly."""
        assert isinstance(metrics_collector, MetricsCollector)
        assert hasattr(metrics_collector, 'provider_metrics')
        assert hasattr(metrics_collector, 'request_history')
        assert hasattr(metrics_collector, 'start_time')
        assert isinstance(metrics_collector.provider_metrics, dict)
        assert isinstance(metrics_collector.request_history, deque)

    @pytest.mark.asyncio
    async def test_record_request_success(self, metrics_collector):
        """Test recording a successful request."""
        await metrics_collector.record_request(
            request_type="llm_query",
            provider="ollama",
            response_time=2.5,
            tokens_used=150,
            cost=0.0,
            success=True,
            user_id="test_user"
        )

        # Check that metrics were recorded
        assert "ollama" in metrics_collector.provider_metrics
        ollama_metrics = metrics_collector.provider_metrics["ollama"]

        assert ollama_metrics.total_requests == 1
        assert ollama_metrics.successful_requests == 1
        assert ollama_metrics.failed_requests == 0
        assert ollama_metrics.total_tokens == 150
        assert ollama_metrics.total_cost == 0.0

        # Check request history
        assert len(metrics_collector.request_history) == 1
        request = metrics_collector.request_history[0]
        assert request.provider == "ollama"
        assert request.response_time == 2.5
        assert request.tokens_used == 150
        assert request.success is True
        assert request.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_record_request_failure(self, metrics_collector):
        """Test recording a failed request."""
        await metrics_collector.record_request(
            request_type="llm_query",
            provider="openai",
            response_time=5.0,
            tokens_used=0,
            cost=0.0,
            success=False,
            error_type="timeout",
            user_id="test_user"
        )

        # Check that failure was recorded
        assert "openai" in metrics_collector.provider_metrics
        openai_metrics = metrics_collector.provider_metrics["openai"]

        assert openai_metrics.total_requests == 1
        assert openai_metrics.successful_requests == 0
        assert openai_metrics.failed_requests == 1
        assert openai_metrics.total_tokens == 0
        assert openai_metrics.total_cost == 0.0
        assert "timeout" in openai_metrics.error_counts
        assert openai_metrics.error_counts["timeout"] == 1

    @pytest.mark.asyncio
    async def test_record_multiple_requests(self, metrics_collector):
        """Test recording multiple requests from different providers."""
        # Record multiple successful requests
        await metrics_collector.record_request("llm_query", "ollama", 1.5, 100, 0.0, True)
        await metrics_collector.record_request("llm_query", "openai", 3.0, 200, 0.006, True)
        await metrics_collector.record_request("llm_query", "ollama", 2.0, 150, 0.0, True)
        await metrics_collector.record_request("llm_query", "anthropic", 4.0, 0, 0.0, False, "rate_limit")

        # Check Ollama metrics (2 requests)
        ollama_metrics = metrics_collector.provider_metrics["ollama"]
        assert ollama_metrics.total_requests == 2
        assert ollama_metrics.successful_requests == 2
        assert ollama_metrics.total_tokens == 250
        assert ollama_metrics.total_cost == 0.0

        # Check OpenAI metrics (1 request)
        openai_metrics = metrics_collector.provider_metrics["openai"]
        assert openai_metrics.total_requests == 1
        assert openai_metrics.successful_requests == 1
        assert openai_metrics.total_tokens == 200
        assert openai_metrics.total_cost == 0.006

        # Check Anthropic metrics (1 failed request)
        anthropic_metrics = metrics_collector.provider_metrics["anthropic"]
        assert anthropic_metrics.total_requests == 1
        assert anthropic_metrics.failed_requests == 1
        assert "rate_limit" in anthropic_metrics.error_counts

    def test_get_metrics_summary_empty(self, metrics_collector):
        """Test getting metrics summary with no data."""
        summary = metrics_collector.get_metrics_summary()

        assert isinstance(summary, dict)
        assert summary["total_requests"] == 0
        assert summary["total_tokens_used"] == 0
        assert summary["total_cost"] == 0.0
        assert "error" not in summary

    @pytest.mark.asyncio
    async def test_get_metrics_summary_with_data(self, metrics_collector):
        """Test getting metrics summary with data."""
        # Add some test data
        await metrics_collector.record_request("llm_query", "ollama", 1.5, 100, 0.0, True)
        await metrics_collector.record_request("llm_query", "openai", 3.0, 200, 0.006, True)
        await metrics_collector.record_request("llm_query", "openai", 5.0, 0, 0.0, False, "timeout")

        summary = metrics_collector.get_metrics_summary()

        assert summary["total_requests"] == 3
        assert summary["total_tokens_used"] == 300
        assert summary["total_cost"] == 0.006
        assert "ollama" in summary["requests_by_provider"]
        assert "openai" in summary["requests_by_provider"]
        assert summary["requests_by_provider"]["ollama"] == 1
        assert summary["requests_by_provider"]["openai"] == 2
        assert summary["average_response_time"] > 0
        assert summary["error_rate"] == (1/3) * 100  # 1 failure out of 3 requests

    def test_get_provider_metrics_nonexistent(self, metrics_collector):
        """Test getting metrics for non-existent provider."""
        result = metrics_collector.get_provider_metrics("nonexistent")

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_provider_metrics_existing(self, metrics_collector):
        """Test getting metrics for existing provider."""
        # Add data for a provider
        await metrics_collector.record_request("llm_query", "ollama", 2.0, 150, 0.0, True)
        await metrics_collector.record_request("llm_query", "ollama", 1.5, 100, 0.0, True)
        await metrics_collector.record_request("llm_query", "ollama", 3.0, 0, 0.0, False, "network_error")

        result = metrics_collector.get_provider_metrics("ollama")

        assert result["provider"] == "ollama"
        assert result["total_requests"] == 3
        assert result["successful_requests"] == 2
        assert result["failed_requests"] == 1
        assert result["success_rate"] == (2/3) * 100
        assert result["total_tokens"] == 250
        assert result["total_cost"] == 0.0
        assert result["average_response_time"] == 2.1666666666666665  # (2.0 + 1.5 + 3.0) / 3
        assert "network_error" in result["error_breakdown"]

    def test_get_performance_trends_no_data(self, metrics_collector):
        """Test getting performance trends with no data."""
        result = metrics_collector.get_performance_trends(hours=1)

        assert "error" in result
        assert "no requests found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_performance_trends_with_data(self, metrics_collector):
        """Test getting performance trends with data."""
        # Add some historical data (simulate by directly adding to history)
        import time
        current_time = time.time()

        # Add requests from different time periods
        old_request = RequestMetrics(
            timestamp=current_time - 7200,  # 2 hours ago
            provider="ollama",
            response_time=2.0,
            tokens_used=100,
            cost=0.0,
            success=True
        )

        recent_request = RequestMetrics(
            timestamp=current_time - 1800,  # 30 minutes ago
            provider="openai",
            response_time=3.0,
            tokens_used=200,
            cost=0.006,
            success=True
        )

        metrics_collector.request_history.append(old_request)
        metrics_collector.request_history.append(recent_request)

        result = metrics_collector.get_performance_trends(hours=1)

        assert "error" not in result
        assert result["time_period_hours"] == 1
        assert result["total_requests"] == 1  # Only recent request
        assert result["provider_breakdown"]["openai"]["requests"] == 1

    @pytest.mark.asyncio
    async def test_get_cost_analysis(self, metrics_collector):
        """Test cost analysis functionality."""
        # Add some cost data
        await metrics_collector.record_request("llm_query", "ollama", 2.0, 150, 0.0, True)
        await metrics_collector.record_request("llm_query", "openai", 3.0, 200, 0.006, True)
        await metrics_collector.record_request("llm_query", "anthropic", 4.0, 300, 0.015, True)

        cost_analysis = metrics_collector.get_cost_analysis()

        assert "total_cost" in cost_analysis
        assert cost_analysis["total_cost"] == 0.021  # 0.0 + 0.006 + 0.015
        assert "cost_by_provider" in cost_analysis
        assert cost_analysis["cost_by_provider"]["ollama"] == 0.0
        assert cost_analysis["cost_by_provider"]["openai"] == 0.006
        assert cost_analysis["cost_by_provider"]["anthropic"] == 0.015

    def test_reset_metrics(self, metrics_collector):
        """Test resetting all metrics."""
        # Add some data first
        metrics_collector.provider_metrics["test"] = ProviderMetrics()
        metrics_collector.request_history.append(RequestMetrics(
            timestamp=time.time(),
            provider="test",
            response_time=1.0,
            tokens_used=50,
            cost=0.001,
            success=True
        ))

        # Reset metrics
        metrics_collector.reset_metrics()

        assert len(metrics_collector.provider_metrics) == 0
        assert len(metrics_collector.request_history) == 0

    def test_request_metrics_structure(self):
        """Test RequestMetrics data structure."""
        metrics = RequestMetrics(
            timestamp=1234567890.0,
            provider="ollama",
            response_time=2.5,
            tokens_used=150,
            cost=0.0,
            success=True,
            error_type=None,
            user_id="test_user"
        )

        assert metrics.timestamp == 1234567890.0
        assert metrics.provider == "ollama"
        assert metrics.response_time == 2.5
        assert metrics.tokens_used == 150
        assert metrics.cost == 0.0
        assert metrics.success is True
        assert metrics.error_type is None
        assert metrics.user_id == "test_user"

    def test_provider_metrics_initialization(self):
        """Test ProviderMetrics initialization."""
        pm = ProviderMetrics()

        assert pm.total_requests == 0
        assert pm.successful_requests == 0
        assert pm.failed_requests == 0
        assert pm.total_tokens == 0
        assert pm.total_cost == 0.0
        assert pm.total_response_time == 0.0
        assert isinstance(pm.error_counts, dict)
        assert isinstance(pm.response_times, list)

    def test_provider_metrics_add_request(self):
        """Test adding requests to ProviderMetrics."""
        pm = ProviderMetrics()

        # Add successful request
        success_metrics = RequestMetrics(
            timestamp=time.time(),
            provider="ollama",
            response_time=2.0,
            tokens_used=100,
            cost=0.0,
            success=True
        )

        pm.add_request(success_metrics)

        assert pm.total_requests == 1
        assert pm.successful_requests == 1
        assert pm.failed_requests == 0
        assert pm.total_tokens == 100
        assert pm.total_cost == 0.0
        assert pm.total_response_time == 2.0
        assert len(pm.response_times) == 1

        # Add failed request
        failure_metrics = RequestMetrics(
            timestamp=time.time(),
            provider="ollama",
            response_time=5.0,
            tokens_used=0,
            cost=0.0,
            success=False,
            error_type="timeout"
        )

        pm.add_request(failure_metrics)

        assert pm.total_requests == 2
        assert pm.successful_requests == 1
        assert pm.failed_requests == 1
        assert "timeout" in pm.error_counts
        assert pm.error_counts["timeout"] == 1

    def test_provider_metrics_calculations(self):
        """Test ProviderMetrics calculation methods."""
        pm = ProviderMetrics()

        # Add some test data
        pm.add_request(RequestMetrics(time.time(), "test", 2.0, 100, 0.0, True))
        pm.add_request(RequestMetrics(time.time(), "test", 4.0, 200, 0.01, True))
        pm.add_request(RequestMetrics(time.time(), "test", 6.0, 0, 0.0, False, "error"))

        assert pm.get_success_rate() == 66.66666666666666  # 2/3 * 100
        assert pm.get_average_response_time() == 4.0  # (2+4+6)/3
        assert pm.get_average_cost_per_request() == 0.003333333333333333  # 0.01/3
        assert pm.get_tokens_per_second() > 0  # Should calculate based on response times
