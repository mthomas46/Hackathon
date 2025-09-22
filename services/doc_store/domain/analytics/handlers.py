"""
Analytics handlers for API endpoints.

Handles analytics-related HTTP requests and responses.
"""

import time
from typing import Any, Dict

from services.shared.core.constants_new import ServiceNames
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
            logger_client = await get_log_collector_client(ServiceNames.DOC_STORE)
        except Exception:
            pass  # Fallback to no logging if client unavailable
    return logger_client


class AnalyticsHandlers(BaseHandler):
    """Handlers for analytics API endpoints."""

    def __init__(self):
        super().__init__(AnalyticsService())

    async def handle_get_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Handle comprehensive analytics request."""
        start_time = time.time()
        request_id = f"doc_analytics_comprehensive_{int(time.time() * 1000)}"
        logger = await get_logger_client()

        try:
            # Log analytics retrieval start
            if logger:
                await logger.log_business_event(
                    "document_analytics_retrieval_started",
                    {
                        "request_id": request_id,
                        "operation": "document_analytics_computation",
                        "analytics_scope": "comprehensive_dashboard",
                        "time_range_days": days_back,
                        "data_aggregation_required": True,
                        "performance_insights_requested": True,
                    },
                )

                await logger.log_info(
                    "Retrieving comprehensive document analytics",
                    {
                        "request_id": request_id,
                        "time_range_days": days_back,
                        "historical_data_scope": f"last_{days_back}_days",
                        "analytics_types": ["documents", "analyses", "ensembles", "quality", "trends", "insights"],
                        "computation_engine_activated": True,
                    },
                )

            analytics = self.service.generate_analytics(days_back)

            response_time = time.time() - start_time
            documents_count = analytics.total_documents if hasattr(analytics, "total_documents") else 0
            analyses_count = analytics.total_analyses if hasattr(analytics, "total_analyses") else 0

            # Log successful analytics retrieval
            if logger:
                await logger.log_business_event(
                    "document_analytics_retrieved",
                    {
                        "request_id": request_id,
                        "operation": "document_analytics_computation",
                        "response_time_seconds": response_time,
                        "success": True,
                        "time_range_days": days_back,
                        "total_documents_analyzed": documents_count,
                        "total_analyses_processed": analyses_count,
                        "analytics_data_generated": True,
                        "insights_computed": True,
                    },
                )

                await logger.log_performance_metric(
                    "document_analytics_computation",
                    response_time,
                    {
                        "request_id": request_id,
                        "time_range_days": days_back,
                        "documents_processed": documents_count,
                        "analyses_computed": analyses_count,
                        "analytics_success": True,
                        "computation_time": response_time,
                    },
                )

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
                    "relationship_insights": analytics.relationship_insights,
                },
                operation="get_analytics",
                days_back=days_back,
            )

        except Exception as e:
            error_time = time.time() - start_time

            # Log analytics retrieval failure
            if logger:
                await logger.log_error(
                    f"Document analytics retrieval failed: {str(e)}",
                    {
                        "request_id": request_id,
                        "operation": "document_analytics_computation",
                        "time_range_days": days_back,
                        "error_type": type(e).__name__,
                        "response_time_seconds": error_time,
                        "analytics_retrieval_failed": True,
                    },
                    error=e,
                )

                await logger.log_business_event(
                    "document_analytics_retrieval_failed",
                    {
                        "request_id": request_id,
                        "operation": "document_analytics_computation",
                        "time_range_days": days_back,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "response_time_seconds": error_time,
                    },
                )

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
                    "relationship_insights": analytics.relationship_insights,
                },
                operation="get_analytics",
                days_back=days_back,
            )

    async def handle_get_analytics_summary(self) -> Dict[str, Any]:
        """Handle analytics summary request."""
        summary = self.service.get_analytics_summary()

        return await self._handle_request(lambda: summary)
