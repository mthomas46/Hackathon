"""Advanced analytics service for prompt performance, optimization, and insights."""

import asyncio
import statistics
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from .entities import PromptPerformanceMetrics, UserSatisfactionScore
from .repository import AnalyticsRepository
from ...core.service import BaseService
from ...infrastructure.cache import prompt_store_cache
from ...shared.clients import ServiceClients
from ...shared.utilities import generate_id, utc_now


class AnalyticsService(BaseService[PromptPerformanceMetrics]):
    """Advanced analytics service for prompt ecosystem insights."""

    def __init__(self):
        super().__init__(AnalyticsRepository())
        self.clients = ServiceClients()

    async def record_usage_metrics(self, prompt_id: str, version: int, usage_data: Dict[str, Any]) -> None:
        """Record usage metrics for a prompt execution."""
        metrics = await self._get_or_create_metrics(prompt_id, version)

        # Update metrics
        metrics.total_requests += 1
        if usage_data.get("success", True):
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        # Update response time statistics
        response_time = usage_data.get("response_time_ms", 0)
        await self._update_response_time_metrics(metrics, response_time)

        # Update token usage
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        total_tokens = input_tokens + output_tokens
        metrics.total_tokens_used += total_tokens

        # Calculate cost estimate
        cost_estimate = self._calculate_cost_estimate(
            usage_data.get("llm_service", "unknown"),
            input_tokens, output_tokens
        )
        metrics.cost_estimate_usd += cost_estimate

        # Recalculate averages
        self._recalculate_averages(metrics)

        # Save updated metrics
        self.update_entity(metrics.id, metrics.__dict__)

        # Cache for performance
        cache_key = f"analytics:metrics:{prompt_id}:{version}"
        await prompt_store_cache.set(cache_key, metrics.to_dict(), ttl=3600)

    async def _get_or_create_metrics(self, prompt_id: str, version: int) -> PromptPerformanceMetrics:
        """Get existing metrics or create new ones."""
        cache_key = f"analytics:metrics:{prompt_id}:{version}"
        cached = await prompt_store_cache.get(cache_key)
        if cached:
            return PromptPerformanceMetrics(**cached)

        existing = self.repository.get_metrics_by_prompt_version(prompt_id, version)
        if existing:
            return existing

        metrics = PromptPerformanceMetrics(
            id=generate_id(),
            prompt_id=prompt_id,
            version=version
        )
        self.create_entity(metrics.__dict__)
        return metrics

    async def _update_response_time_metrics(self, metrics: PromptPerformanceMetrics, response_time: float) -> None:
        """Update response time statistics."""
        if metrics.total_requests == 1:
            metrics.average_response_time_ms = response_time
            metrics.median_response_time_ms = response_time
            metrics.p95_response_time_ms = response_time
            metrics.p99_response_time_ms = response_time
        else:
            alpha = 0.1
            metrics.average_response_time_ms = (
                alpha * response_time + (1 - alpha) * metrics.average_response_time_ms
            )
            metrics.p95_response_time_ms = metrics.average_response_time_ms * 1.5
            metrics.p99_response_time_ms = metrics.average_response_time_ms * 2.0

    def _calculate_cost_estimate(self, llm_service: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost estimate based on token usage."""
        cost_rates = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "claude-3": {"input": 0.015, "output": 0.075},
            "interpreter": {"input": 0.001, "output": 0.002},
            "bedrock": {"input": 0.0015, "output": 0.002}
        }

        rates = cost_rates.get(llm_service.lower(), cost_rates["gpt-3.5-turbo"])
        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]

        return input_cost + output_cost

    def _recalculate_averages(self, metrics: PromptPerformanceMetrics) -> None:
        """Recalculate average metrics."""
        if metrics.total_requests > 0:
            metrics.average_tokens_per_request = metrics.total_tokens_used / metrics.total_requests

    async def record_user_satisfaction(self, satisfaction_data: Dict[str, Any]) -> UserSatisfactionScore:
        """Record user satisfaction feedback."""
        score = UserSatisfactionScore(
            id=generate_id(),
            prompt_id=satisfaction_data["prompt_id"],
            user_id=satisfaction_data["user_id"],
            session_id=satisfaction_data["session_id"],
            rating=satisfaction_data["rating"],
            feedback_text=satisfaction_data.get("feedback_text"),
            context_tags=satisfaction_data.get("context_tags", []),
            use_case_category=satisfaction_data.get("use_case_category", "general")
        )

        self.repository.create_satisfaction_score(score.__dict__)
        return score

    async def get_analytics_dashboard(self, time_range_days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard data."""
        return {
            "time_range_days": time_range_days,
            "summary": await self._get_analytics_summary(time_range_days),
            "performance_metrics": await self._get_performance_overview(time_range_days),
            "usage_trends": await self._get_usage_trends(time_range_days)
        }

    async def _get_analytics_summary(self, days: int) -> Dict[str, Any]:
        """Get analytics summary statistics."""
        total_prompts = len(self.repository.get_all_prompts())
        total_requests = self.repository.get_total_requests(days)

        return {
            "total_prompts": total_prompts,
            "total_requests": total_requests,
            "active_prompts": self.repository.get_active_prompts_count()
        }

    async def _get_performance_overview(self, days: int) -> Dict[str, Any]:
        """Get performance metrics overview."""
        top_performing = self.repository.get_top_performing_prompts(days, limit=5)

        return {
            "top_performing_prompts": top_performing,
            "average_response_time_ms": self.repository.get_average_response_time(days)
        }

    async def _get_usage_trends(self, days: int) -> Dict[str, Any]:
        """Get usage trends and patterns."""
        usage_by_day = self.repository.get_usage_by_day(days)
        popular_prompts = self.repository.get_most_used_prompts(days, limit=10)

        return {
            "daily_usage": usage_by_day,
            "popular_prompts": popular_prompts
        }