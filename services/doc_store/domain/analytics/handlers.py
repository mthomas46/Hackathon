"""Analytics handlers for API endpoints.

Handles analytics-related HTTP requests and responses.
"""
from typing import Dict, Any
from ...core.handler import BaseHandler
from .service import AnalyticsService


class AnalyticsHandlers(BaseHandler):
    """Handlers for analytics API endpoints."""

    def __init__(self):
        super().__init__(AnalyticsService())

    async def handle_get_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Handle comprehensive analytics request."""
        analytics = self.service.generate_analytics(days_back)

        return await self._handle_request(
            lambda: {
                "total_documents": analytics.total_documents,
                "total_analyses": analytics.total_analyses,
                "total_ensembles": analytics.total_ensembles,
                "total_style_examples": analytics.total_style_examples,
                "storage_stats": analytics.storage_stats,
                "quality_metrics": self.service.get_quality_metrics(),
                "temporal_trends": analytics.temporal_trends,
                "content_insights": analytics.content_insights,
                "relationship_insights": analytics.relationship_insights
            },
            operation="get_analytics",
            days_back=days_back
        )

    async def handle_get_analytics_summary(self) -> Dict[str, Any]:
        """Handle analytics summary request."""
        summary = self.service.get_analytics_summary()

        return await self._handle_request(
            lambda: summary,
            operation="get_analytics_summary"
        )
