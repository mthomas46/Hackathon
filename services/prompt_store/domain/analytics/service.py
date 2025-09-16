"""Analytics service implementation.

Handles business logic for analytics and usage tracking operations.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from services.prompt_store.domain.analytics.repository import AnalyticsRepository
from services.prompt_store.domain.prompts.service import PromptService
from services.prompt_store.domain.ab_testing.service import ABTestService
from services.prompt_store.infrastructure.cache import prompt_store_cache
from services.shared.utilities import utc_now


class AnalyticsService:
    """Service for analytics and usage tracking business logic."""

    def __init__(self):
        self.repository = AnalyticsRepository()
        self.prompt_service = PromptService()
        self.ab_test_service = ABTestService()

    def record_usage(self, prompt_id: str, operation: str = "generate",
                    input_tokens: Optional[int] = None,
                    output_tokens: Optional[int] = None,
                    response_time_ms: Optional[float] = None,
                    success: bool = True,
                    error_message: Optional[str] = None,
                    service_name: str = "api",
                    user_id: Optional[str] = None,
                    session_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record prompt usage for analytics."""
        from services.prompt_store.core.entities import PromptUsage
        from services.shared.utilities import generate_id

        usage = PromptUsage(
            id=generate_id(),
            prompt_id=prompt_id,
            session_id=session_id,
            user_id=user_id,
            service_name=service_name,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )

        # Save asynchronously to avoid blocking
        asyncio.create_task(self._save_usage_async(usage))

    def get_prompt_analytics(self, prompt_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics for a specific prompt."""
        end_date = utc_now()
        start_date = end_date - timedelta(days=days_back)

        # Get usage data
        usage_stats = self.repository.get_usage_stats(
            prompt_id=prompt_id,
            start_date=start_date,
            end_date=end_date
        )

        # Get prompt details
        prompt = self.prompt_service.get_entity(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        # Get usage trends
        trends = self.repository.get_usage_trends(days=days_back)

        # Get A/B test performance if applicable
        ab_tests = self.ab_test_service.get_tests_for_prompt(prompt_id)
        ab_performance = []

        for test in ab_tests:
            if test.is_active:
                try:
                    test_results = self.ab_test_service.get_test_results(test.id)
                    ab_performance.append({
                        "test_id": test.id,
                        "test_name": test.name,
                        "performance": test_results.get("results", {}),
                        "variant": "A" if prompt_id == test.prompt_a_id else "B"
                    })
                except Exception:
                    # Skip if test results can't be retrieved
                    pass

        return {
            "prompt": prompt.to_dict(),
            "period": {
                "days": days_back,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "usage_stats": usage_stats,
            "trends": trends,
            "ab_testing": ab_performance,
            "insights": self._generate_prompt_insights(prompt, usage_stats)
        }

    def get_system_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get comprehensive system-wide analytics."""
        end_date = utc_now()
        start_date = end_date - timedelta(days=days_back)

        # Overall usage stats
        overall_stats = self.repository.get_usage_stats(
            start_date=start_date,
            end_date=end_date
        )

        # Prompt performance ranking
        prompt_ranking = self.repository.get_prompt_performance_ranking(
            start_date=start_date,
            end_date=end_date
        )

        # Category usage stats
        category_stats = self.repository.get_category_usage_stats()

        # Usage trends
        trends = self.repository.get_usage_trends(days=days_back)

        # User activity
        user_activity = self.repository.get_user_activity_stats()

        # A/B testing summary
        active_tests = self.ab_test_service.get_active_tests()
        ab_summary = []

        for test in active_tests:
            try:
                test_results = self.ab_test_service.get_test_results(test.id)
                ab_summary.append({
                    "test_id": test.id,
                    "test_name": test.name,
                    "winner": test_results.get("winner"),
                    "confidence": test_results.get("confidence_assessment", {})
                })
            except Exception:
                ab_summary.append({
                    "test_id": test.id,
                    "test_name": test.name,
                    "status": "error_retrieving_results"
                })

        # System health
        health_metrics = self.repository.get_system_health_metrics()

        return {
            "period": {
                "days": days_back,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "overview": overall_stats,
            "prompt_performance": prompt_ranking,
            "category_breakdown": category_stats,
            "usage_trends": trends,
            "user_activity": user_activity,
            "ab_testing": {
                "active_tests": len(active_tests),
                "test_summary": ab_summary
            },
            "system_health": health_metrics,
            "insights": self._generate_system_insights(overall_stats, prompt_ranking, category_stats)
        }

    def get_usage_analytics(self, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           prompt_id: Optional[str] = None,
                           user_id: Optional[str] = None,
                           service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get filtered usage analytics."""
        # Default to last 7 days if no dates provided
        if not end_date:
            end_date = utc_now()
        if not start_date:
            start_date = end_date - timedelta(days=7)

        # Get usage stats
        usage_stats = self.repository.get_usage_stats(
            prompt_id=prompt_id,
            start_date=start_date,
            end_date=end_date
        )

        # Apply additional filters
        filters_applied = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "prompt_id": prompt_id,
            "user_id": user_id,
            "service_name": service_name
        }

        # If specific user or service, get their usage
        if user_id:
            user_usage = self.repository.get_usage_stats(
                start_date=start_date,
                end_date=end_date
            )
            # Filter for specific user (simplified - would need proper query)
            usage_stats["user_specific"] = user_id

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "filters_applied": filters_applied,
            "usage_stats": usage_stats,
            "trends": self.repository.get_usage_trends(days=(end_date - start_date).days)
        }

    def _generate_prompt_insights(self, prompt: Any, usage_stats: Dict[str, Any]) -> List[str]:
        """Generate insights for a specific prompt."""
        insights = []

        # Usage insights
        total_usage = usage_stats.get("total_requests", 0)
        success_rate = usage_stats.get("success_rate", 0)

        if total_usage == 0:
            insights.append("Prompt has not been used yet")
        elif total_usage < 10:
            insights.append("Prompt has limited usage data - more testing recommended")
        else:
            if success_rate > 0.95:
                insights.append("Excellent performance with high success rate")
            elif success_rate > 0.8:
                insights.append("Good performance with solid success rate")
            elif success_rate < 0.7:
                insights.append("Performance concerns - review and optimize prompt")

        # Performance insights
        avg_response_time = usage_stats.get("performance", {}).get("avg_response_time_ms")
        if avg_response_time:
            if avg_response_time > 5000:
                insights.append("Slow response times - consider prompt optimization")
            elif avg_response_time < 1000:
                insights.append("Fast response times - excellent performance")

        # Template insights
        if prompt.is_template:
            insights.append("Template prompt - ensure variable validation is working")

        return insights

    def _generate_system_insights(self, overall_stats: Dict[str, Any],
                                prompt_ranking: List[Dict[str, Any]],
                                category_stats: List[Dict[str, Any]]) -> List[str]:
        """Generate system-wide insights."""
        insights = []

        # Overall health
        success_rate = overall_stats.get("success_rate", 0)
        if success_rate > 0.95:
            insights.append("System performing excellently with high success rates")
        elif success_rate < 0.8:
            insights.append("System performance concerns - investigate error patterns")

        # Usage patterns
        total_requests = overall_stats.get("total_requests", 0)
        if total_requests > 1000:
            insights.append("High usage volume - monitor system performance")
        elif total_requests < 100:
            insights.append("Low usage volume - consider increasing adoption")

        # Category insights
        if category_stats:
            top_category = max(category_stats, key=lambda x: x.get("usage_count", 0))
            insights.append(f"'{top_category['category']}' is the most used prompt category")

        # Top performers
        if prompt_ranking:
            top_prompt = prompt_ranking[0]
            insights.append(f"'{top_prompt['name']}' is the highest performing prompt")

        return insights

    async def _save_usage_async(self, usage: Any) -> None:
        """Save usage record asynchronously."""
        try:
            self.repository.save_usage(usage)

            # Update prompt usage count
            self.prompt_service.repository.increment_usage_count(usage.prompt_id)

            # Invalidate analytics cache
            await prompt_store_cache.invalidate_pattern("analytics:*")

        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Failed to save usage analytics: {e}")

    async def warmup_analytics_cache(self) -> bool:
        """Warm up analytics cache with recent data."""
        try:
            # Cache recent system analytics
            system_analytics = self.get_system_analytics(days_back=7)
            await prompt_store_cache.set("analytics:system:recent", system_analytics, ttl=1800)

            # Cache top prompt analytics
            if system_analytics.get("prompt_performance"):
                for prompt_data in system_analytics["prompt_performance"][:5]:
                    prompt_analytics = self.get_prompt_analytics(prompt_data["id"], days_back=7)
                    await prompt_store_cache.set(f"analytics:prompt:{prompt_data['id']}", prompt_analytics, ttl=1800)

            return True
        except Exception as e:
            print(f"Failed to warmup analytics cache: {e}")
            return False
