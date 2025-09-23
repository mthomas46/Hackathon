"""Analytics API handlers for prompt performance insights."""

import time
from typing import Any, Dict, Optional

from services.shared.core.constants_new import ServiceNames
from services.shared.core.responses.responses import create_error_response, create_success_response
from services.shared.utilities.logging_client import get_log_collector_client

from ...core.handler import BaseHandler
from .service import AnalyticsService

# Global logger client instance
logger_client = None


async def get_logger_client():
    """Get or initialize the logger client."""
    global logger_client
    if logger_client is None:
        try:
            logger_client = await get_log_collector_client(ServiceNames.PROMPT_STORE)
        except Exception:
            pass  # Fallback to no logging if client unavailable
    return logger_client


class AnalyticsHandlers(BaseHandler):
    """Handlers for analytics API endpoints."""

    def __init__(self):
        super().__init__(AnalyticsService())

    async def handle_record_usage_metrics(
        self, prompt_id: str, version: int, usage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record usage metrics for analytics."""
        start_time = time.time()
        request_id = f"usage_metrics_record_{int(time.time() * 1000)}"
        logger = await get_logger_client()

        try:
            # Log usage metrics recording start
            if logger:
                await logger.log_business_event(
                    "usage_metrics_recording_started",
                    {
                        "request_id": request_id,
                        "prompt_id": prompt_id,
                        "prompt_version": version,
                        "operation": "prompt_performance_tracking",
                        "metrics_data_provided": bool(usage_data),
                        "metrics_keys_count": len(usage_data) if usage_data else 0,
                        "performance_data_collection": True,
                    },
                )

                await logger.log_info(
                    "Recording prompt usage metrics",
                    {
                        "request_id": request_id,
                        "prompt_id": prompt_id,
                        "version": version,
                        "metrics_count": len(usage_data) if usage_data else 0,
                        "has_token_usage": "tokens_used" in usage_data if usage_data else False,
                        "has_response_time": "response_time_ms" in usage_data if usage_data else False,
                        "has_error_rate": "error_count" in usage_data if usage_data else False,
                    },
                )

            await self.service.record_usage_metrics(prompt_id, version, usage_data)

            response_time = time.time() - start_time

            # Log successful usage metrics recording
            if logger:
                await logger.log_business_event(
                    "usage_metrics_recorded",
                    {
                        "request_id": request_id,
                        "prompt_id": prompt_id,
                        "prompt_version": version,
                        "operation": "prompt_performance_tracking",
                        "response_time_seconds": response_time,
                        "success": True,
                        "metrics_persisted": True,
                        "performance_data_aggregated": True,
                        "analytics_pipeline_updated": True,
                    },
                )

                await logger.log_performance_metric(
                    "usage_metrics_recording",
                    response_time,
                    {
                        "request_id": request_id,
                        "prompt_id": prompt_id,
                        "version": version,
                        "metrics_count": len(usage_data) if usage_data else 0,
                        "recording_success": True,
                        "data_persistence_time": response_time,
                    },
                )

            return create_success_response(message="Usage metrics recorded successfully").model_dump()

        except Exception as e:
            error_time = time.time() - start_time

            # Log usage metrics recording failure
            if logger:
                await logger.log_error(
                    f"Usage metrics recording failed: {str(e)}",
                    {
                        "request_id": request_id,
                        "operation": "prompt_performance_tracking",
                        "prompt_id": prompt_id,
                        "prompt_version": version,
                        "metrics_keys_count": len(usage_data) if usage_data else 0,
                        "error_type": type(e).__name__,
                        "response_time_seconds": error_time,
                        "usage_metrics_recording_failed": True,
                    },
                    error=e,
                )

                await logger.log_business_event(
                    "usage_metrics_recording_failed",
                    {
                        "request_id": request_id,
                        "operation": "prompt_performance_tracking",
                        "prompt_id": prompt_id,
                        "prompt_version": version,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "response_time_seconds": error_time,
                    },
                )

            return create_error_response(f"Failed to record usage metrics: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_record_satisfaction(self, satisfaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record user satisfaction feedback."""
        try:
            score = await self.service.record_user_satisfaction(satisfaction_data)
            return create_success_response(
                message="User satisfaction recorded successfully", data=score.to_dict()
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to record satisfaction: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_get_analytics_dashboard(self, time_range_days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard."""
        start_time = time.time()
        request_id = f"analytics_dashboard_{int(time.time() * 1000)}"
        logger = await get_logger_client()

        try:
            # Log analytics dashboard retrieval start
            if logger:
                await logger.log_business_event(
                    "analytics_dashboard_retrieval_started",
                    {
                        "request_id": request_id,
                        "operation": "prompt_performance_analytics",
                        "time_range_days": time_range_days,
                        "analytics_scope": "comprehensive_dashboard",
                        "performance_insights_requested": True,
                        "data_aggregation_required": True,
                    },
                )

                await logger.log_info(
                    "Retrieving comprehensive analytics dashboard",
                    {
                        "request_id": request_id,
                        "time_range_days": time_range_days,
                        "historical_data_scope": f"last_{time_range_days}_days",
                        "includes_usage_metrics": True,
                        "includes_satisfaction_scores": True,
                        "includes_performance_trends": True,
                    },
                )

            dashboard = await self.service.get_analytics_dashboard(time_range_days)

            response_time = time.time() - start_time
            dashboard_size = len(dashboard) if isinstance(dashboard, dict) else 0

            # Log successful analytics dashboard retrieval
            if logger:
                await logger.log_business_event(
                    "analytics_dashboard_retrieved",
                    {
                        "request_id": request_id,
                        "operation": "prompt_performance_analytics",
                        "response_time_seconds": response_time,
                        "success": True,
                        "time_range_days": time_range_days,
                        "dashboard_data_points": dashboard_size,
                        "performance_insights_generated": True,
                        "analytics_computation_complete": True,
                    },
                )

                await logger.log_performance_metric(
                    "analytics_dashboard_retrieval",
                    response_time,
                    {
                        "request_id": request_id,
                        "time_range_days": time_range_days,
                        "dashboard_size": dashboard_size,
                        "retrieval_success": True,
                        "analytics_computation_time": response_time,
                    },
                )

            return create_success_response(
                message="Analytics dashboard retrieved successfully", data=dashboard
            ).model_dump()

        except Exception as e:
            error_time = time.time() - start_time

            # Log analytics dashboard retrieval failure
            if logger:
                await logger.log_error(
                    f"Analytics dashboard retrieval failed: {str(e)}",
                    {
                        "request_id": request_id,
                        "operation": "prompt_performance_analytics",
                        "time_range_days": time_range_days,
                        "error_type": type(e).__name__,
                        "response_time_seconds": error_time,
                        "analytics_dashboard_failed": True,
                    },
                    error=e,
                )

                await logger.log_business_event(
                    "analytics_dashboard_retrieval_failed",
                    {
                        "request_id": request_id,
                        "operation": "prompt_performance_analytics",
                        "time_range_days": time_range_days,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "response_time_seconds": error_time,
                    },
                )

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
                message="Performance overview retrieved successfully", data=dashboard.get("performance_metrics", {})
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to get performance overview: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_get_usage_analytics(self, time_range_days: int = 30) -> Dict[str, Any]:
        """Get usage analytics and trends."""
        try:
            dashboard = await self.service.get_analytics_dashboard(time_range_days)
            return create_success_response(
                message="Usage analytics retrieved successfully", data=dashboard.get("usage_trends", {})
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to get usage analytics: {str(e)}", "INTERNAL_ERROR").model_dump()
