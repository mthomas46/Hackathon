"""Analytics API handlers for prompt performance insights."""

from typing import Dict, Any, Optional
from ...core.handler import BaseHandler
from .service import AnalyticsService
from services.shared.core.responses.responses import create_success_response, create_error_response


class AnalyticsHandlers(BaseHandler):
    """Handlers for analytics API endpoints."""

    def __init__(self):
        super().__init__(AnalyticsService())

    async def handle_record_usage_metrics(self, prompt_id: str, version: int, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record usage metrics for analytics."""
        try:
            await self.service.record_usage_metrics(prompt_id, version, usage_data)
            return create_success_response(
                message="Usage metrics recorded successfully"
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to record usage metrics: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_record_satisfaction(self, satisfaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record user satisfaction feedback."""
        try:
            score = await self.service.record_user_satisfaction(satisfaction_data)
            return create_success_response(
                message="User satisfaction recorded successfully",
                data=score.to_dict()
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to record satisfaction: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_get_analytics_dashboard(self, time_range_days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard."""
        try:
            dashboard = await self.service.get_analytics_dashboard(time_range_days)
            return create_success_response(
                message="Analytics dashboard retrieved successfully",
                data=dashboard
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to get analytics dashboard: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_get_prompt_metrics(self, prompt_id: str, version: Optional[int] = None) -> Dict[str, Any]:
        """Get metrics for a specific prompt."""
        try:
            # This would need to be implemented in the service
            return create_error_response("Not implemented yet", "NOT_IMPLEMENTED").model_dump()
        except Exception as e:
            return create_error_response(f"Failed to get prompt metrics: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_get_performance_overview(self, time_range_days: int = 30) -> Dict[str, Any]:
        """Get performance overview across all prompts."""
        try:
            # Get dashboard and extract performance metrics
            dashboard = await self.service.get_analytics_dashboard(time_range_days)
            return create_success_response(
                message="Performance overview retrieved successfully",
                data=dashboard.get("performance_metrics", {})
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to get performance overview: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_get_usage_analytics(self, time_range_days: int = 30) -> Dict[str, Any]:
        """Get usage analytics and trends."""
        try:
            dashboard = await self.service.get_analytics_dashboard(time_range_days)
            return create_success_response(
                message="Usage analytics retrieved successfully",
                data=dashboard.get("usage_trends", {})
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to get usage analytics: {str(e)}", "INTERNAL_ERROR").model_dump()