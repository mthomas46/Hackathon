"""Analytics handlers for Prompt Store service.

Handles the complex logic for analytics endpoints.
"""
from typing import Dict, Any

from .shared_utils import (
    get_prompt_store_client,
    handle_prompt_error,
    create_prompt_success_response,
    build_prompt_context
)


class AnalyticsHandlers:
    """Handles analytics operations."""

    @staticmethod
    async def handle_get_analytics() -> Dict[str, Any]:
        """Get usage analytics and performance metrics."""
        try:
            db = get_prompt_store_client()
            analytics_data = await AnalyticsHandlers._get_usage_analytics(db)

            context = build_prompt_context("analytics_retrieval", total_prompts=len(analytics_data.get('popular_categories', [])))
            return create_prompt_success_response("analytics retrieved", analytics_data, **context)

        except Exception as e:
            context = build_prompt_context("analytics_retrieval")
            return handle_prompt_error("retrieve analytics", e, **context)

    @staticmethod
    async def _get_usage_analytics(db) -> Dict[str, Any]:
        """Get comprehensive usage analytics."""
        # Get usage statistics for the last 7 days
        usage_stats = db.get_usage_stats(days=7)

        # Get total number of prompts
        total_prompts = db.get_total_prompts()

        # Get active A/B tests
        ab_tests = db.list_ab_tests(active_only=True)

        # Get popular categories
        popular_categories = {}
        for prompt in usage_stats.get('top_prompts', []):
            category = prompt.get('category', 'unknown')
            if category not in popular_categories:
                popular_categories[category] = 0
            popular_categories[category] += prompt.get('usage_count', 0)

        return {
            "total_prompts": total_prompts,
            "active_ab_tests": len(ab_tests),
            "usage_stats": usage_stats,
            "popular_categories": [
                {"category": category, "usage_count": count}
                for category, count in sorted(popular_categories.items(), key=lambda x: x[1], reverse=True)
            ],
            "performance_insights": await AnalyticsHandlers._generate_performance_insights(db)
        }

    @staticmethod
    async def _generate_performance_insights(db) -> Dict[str, Any]:
        """Generate performance insights."""
        insights = []

        # Check for prompts with low success rates
        usage_stats = db.get_usage_stats(days=30)
        if usage_stats.get('success_rate', 1.0) < 0.8:
            insights.append("Some prompts have low success rates - consider reviewing and updating them")

        # Check for high token usage
        if usage_stats.get('avg_input_tokens', 0) > 1000:
            insights.append("Average input token usage is high - consider optimizing prompt length")

        if not insights:
            insights.append("All prompts are performing well")

        return {
            "insights": insights,
            "recommendations": [
                "Monitor prompt performance regularly",
                "Consider A/B testing for significant prompt changes",
                "Review and update outdated prompts periodically"
            ]
        }


# Create singleton instance
analytics_handlers = AnalyticsHandlers()
