"""Analysis Handlers - Refactored handler delegation.

This module now delegates to the refactored handler system for improved maintainability.
The original 1969+ line monolithic implementation has been broken down into focused
handler modules in the handlers/ package.
"""

import logging
import time
from typing import Any

from services.shared.core.constants_new import ServiceNames
from services.shared.utilities.logging_client import get_log_collector_client

from .handlers import handler_registry

logger = logging.getLogger(__name__)

# Global logger client instance
logger_client = None


async def get_logger_client():
    """Get or initialize the logger client."""
    global logger_client
    if logger_client is None:
        try:
            logger_client = await get_log_collector_client(ServiceNames.ANALYSIS_SERVICE)
        except Exception:
            pass  # Fallback to no logging if client unavailable
    return logger_client


class AnalysisHandlers:
    """Delegates analysis operations to refactored handlers."""

    @staticmethod
    async def handle_analyze_documents(req) -> Any:
        """Analyze documents for consistency and issues - delegates to semantic similarity handler."""
        start_time = time.time()
        request_id = f"analysis_{int(time.time() * 1000)}"
        logger = await get_logger_client()

        try:
            # Log analysis start
            if logger:
                await logger.log_business_event(
                    "document_analysis_started",
                    {
                        "request_id": request_id,
                        "analysis_type": "document_consistency",
                        "target_count": len(getattr(req, "targets", [])),
                        "detectors": getattr(req, "detectors", []),
                        "correlation_id": getattr(req, "correlation_id", None),
                    },
                )

                await logger.log_info(
                    "Starting document analysis",
                    {
                        "request_id": request_id,
                        "analysis_type": "consistency_check",
                        "has_targets": bool(getattr(req, "targets", [])),
                        "detector_count": len(getattr(req, "detectors", [])),
                    },
                )

            handler = handler_registry.get_handler("semantic_similarity")
            if handler:
                result = await handler.handle(req)
                response_time = time.time() - start_time

                # Log successful analysis
                if logger:
                    await logger.log_business_event(
                        "document_analysis_completed",
                        {
                            "request_id": request_id,
                            "analysis_type": "document_consistency",
                            "response_time_seconds": response_time,
                            "success": True,
                            "findings_count": len(result.get("findings", [])),
                            "documents_analyzed": len(result.get("analyzed_documents", [])),
                        },
                    )

                    await logger.log_performance_metric(
                        "document_analysis",
                        response_time,
                        {
                            "request_id": request_id,
                            "analysis_type": "consistency",
                            "findings_discovered": len(result.get("findings", [])),
                            "analysis_success": True,
                        },
                    )

                return result
            else:
                error_time = time.time() - start_time

                # Log handler unavailable error
                if logger:
                    await logger.log_error(
                        "Document analysis failed: No semantic similarity handler available",
                        {
                            "request_id": request_id,
                            "error_type": "handler_unavailable",
                            "response_time_seconds": error_time,
                        },
                        error=Exception("No semantic similarity handler available"),
                    )

                    await logger.log_business_event(
                        "document_analysis_failed",
                        {
                            "request_id": request_id,
                            "error_type": "handler_unavailable",
                            "error_message": "No semantic similarity handler available",
                            "response_time_seconds": error_time,
                        },
                    )

                logger.error("No semantic similarity handler available")
                return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

        except Exception as e:
            error_time = time.time() - start_time

            # Log analysis failure
            if logger:
                await logger.log_error(
                    f"Document analysis failed: {str(e)}",
                    {"request_id": request_id, "error_type": type(e).__name__, "response_time_seconds": error_time},
                    error=e,
                )

                await logger.log_business_event(
                    "document_analysis_failed",
                    {
                        "request_id": request_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "response_time_seconds": error_time,
                    },
                )

            logger.error(f"Document analysis error: {e}")
            return {"error": str(e), "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_semantic_similarity_analysis(req):
        """Handle semantic similarity analysis."""
        handler = handler_registry.get_handler("semantic_similarity")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No semantic similarity handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_sentiment_analysis(req):
        """Handle sentiment analysis."""
        handler = handler_registry.get_handler("sentiment_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No sentiment analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_tone_analysis(req):
        """Handle tone analysis."""
        handler = handler_registry.get_handler("sentiment_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No sentiment analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_content_quality_assessment(req):
        """Handle content quality assessment."""
        handler = handler_registry.get_handler("quality_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No quality analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_trend_analysis(req):
        """Handle trend analysis."""
        handler = handler_registry.get_handler("trend_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No trend analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_portfolio_trend_analysis(req):
        """Handle portfolio trend analysis."""
        handler = handler_registry.get_handler("portfolio_trend_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No portfolio trend analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_risk_assessment(req):
        """Handle risk assessment."""
        start_time = time.time()
        request_id = f"risk_analysis_{int(time.time() * 1000)}"
        logger = await get_logger_client()

        try:
            # Log risk assessment start
            if logger:
                await logger.log_business_event(
                    "risk_assessment_started",
                    {
                        "request_id": request_id,
                        "analysis_type": "risk_assessment",
                        "target_count": len(getattr(req, "targets", [])),
                        "assessment_type": getattr(req, "assessment_type", "comprehensive"),
                    },
                )

                await logger.log_info(
                    "Starting risk assessment analysis",
                    {
                        "request_id": request_id,
                        "assessment_type": getattr(req, "assessment_type", "comprehensive"),
                        "has_targets": bool(getattr(req, "targets", [])),
                    },
                )

            handler = handler_registry.get_handler("risk_assessment")
            if handler:
                result = await handler.handle(req)
                response_time = time.time() - start_time

                # Log successful risk assessment
                if logger:
                    risk_score = result.get("overall_risk_score", 0)
                    critical_issues = len([f for f in result.get("findings", []) if f.get("severity") == "critical"])

                    await logger.log_business_event(
                        "risk_assessment_completed",
                        {
                            "request_id": request_id,
                            "analysis_type": "risk_assessment",
                            "response_time_seconds": response_time,
                            "success": True,
                            "overall_risk_score": risk_score,
                            "critical_issues_count": critical_issues,
                            "findings_count": len(result.get("findings", [])),
                        },
                    )

                    await logger.log_performance_metric(
                        "risk_assessment",
                        response_time,
                        {
                            "request_id": request_id,
                            "risk_score": risk_score,
                            "critical_issues": critical_issues,
                            "assessment_success": True,
                        },
                    )

                return result
            else:
                error_time = time.time() - start_time

                # Log handler unavailable error
                if logger:
                    await logger.log_error(
                        "Risk assessment failed: No risk assessment handler available",
                        {
                            "request_id": request_id,
                            "error_type": "handler_unavailable",
                            "response_time_seconds": error_time,
                        },
                        error=Exception("No risk assessment handler available"),
                    )

                logger.error("No risk assessment handler available")
                return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

        except Exception as e:
            error_time = time.time() - start_time

            # Log risk assessment failure
            if logger:
                await logger.log_error(
                    f"Risk assessment failed: {str(e)}",
                    {"request_id": request_id, "error_type": type(e).__name__, "response_time_seconds": error_time},
                    error=e,
                )

                await logger.log_business_event(
                    "risk_assessment_failed",
                    {
                        "request_id": request_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "response_time_seconds": error_time,
                    },
                )

            logger.error(f"Risk assessment error: {e}")
            return {"error": str(e), "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_portfolio_risk_assessment(req):
        """Handle portfolio risk assessment."""
        handler = handler_registry.get_handler("portfolio_risk_assessment")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No portfolio risk assessment handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_maintenance_forecast(req):
        """Handle maintenance forecast."""
        handler = handler_registry.get_handler("maintenance_forecast")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No maintenance forecast handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_portfolio_maintenance_forecast(req):
        """Handle portfolio maintenance forecast."""
        handler = handler_registry.get_handler("portfolio_maintenance_forecast")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No portfolio maintenance forecast handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_quality_degradation_detection(req):
        """Handle quality degradation detection."""
        # Use trend analysis for degradation detection
        handler = handler_registry.get_handler("trend_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No trend analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_portfolio_quality_degradation(req):
        """Handle portfolio quality degradation detection."""
        # Use portfolio trend analysis for degradation detection
        handler = handler_registry.get_handler("portfolio_trend_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No portfolio trend analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_change_impact_analysis(req):
        """Handle change impact analysis."""
        handler = handler_registry.get_handler("impact_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No impact analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_portfolio_change_impact_analysis(req):
        """Handle portfolio change impact analysis."""
        handler = handler_registry.get_handler("impact_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No impact analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_automated_remediation(req):
        """Handle automated remediation."""
        handler = handler_registry.get_handler("remediation")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No remediation handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_remediation_preview(req):
        """Handle remediation preview."""
        handler = handler_registry.get_handler("remediation")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No remediation handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_workflow_event(req):
        """Handle workflow event."""
        handler = handler_registry.get_handler("workflow_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No workflow analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_workflow_status(req):
        """Handle workflow status request."""
        # This could be handled by a dedicated workflow handler
        handler = handler_registry.get_handler("workflow_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No workflow analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_workflow_queue_status(req):
        """Handle workflow queue status request."""
        # This could be handled by a dedicated workflow handler
        handler = handler_registry.get_handler("workflow_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No workflow analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_webhook_config(req):
        """Handle webhook configuration."""
        # This could be handled by a dedicated workflow handler
        handler = handler_registry.get_handler("workflow_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No workflow analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_cross_repository_analysis(req):
        """Handle cross-repository analysis."""
        handler = handler_registry.get_handler("cross_repository_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No cross-repository analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_repository_connectivity(req):
        """Handle repository connectivity analysis."""
        # This could be handled by a dedicated repository handler
        handler = handler_registry.get_handler("cross_repository_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No cross-repository analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_repository_connector_config(req):
        """Handle repository connector configuration."""
        # This could be handled by a dedicated repository handler
        handler = handler_registry.get_handler("cross_repository_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No cross-repository analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"error-{id(req)}"}

    @staticmethod
    async def handle_supported_connectors():
        """Handle supported connectors request."""
        # This could be handled by a dedicated repository handler
        handler = handler_registry.get_handler("cross_repository_analysis")
        if handler:
            return await handler.handle({"type": "connectors_request"})
        else:
            logger.error("No cross-repository analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"connectors-{id({})}"}

    @staticmethod
    async def handle_analysis_frameworks():
        """Handle analysis frameworks request."""
        # This could be handled by a dedicated system handler
        handler = handler_registry.get_handler("cross_repository_analysis")
        if handler:
            return await handler.handle({"type": "frameworks_request"})
        else:
            logger.error("No cross-repository analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"frameworks-{id({})}"}

    @staticmethod
    async def handle_submit_distributed_task(req):
        """Handle distributed task submission."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"distributed-{id(req)}"}

    @staticmethod
    async def handle_submit_batch_tasks(req):
        """Handle batch tasks submission."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"batch-{id(req)}"}

    @staticmethod
    async def handle_get_task_status(req):
        """Handle task status request."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"status-{id(req)}"}

    @staticmethod
    async def handle_cancel_task(req):
        """Handle task cancellation."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"cancel-{id(req)}"}

    @staticmethod
    async def handle_get_workers_status():
        """Handle workers status request."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle({"type": "workers_status"})
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"workers-{id({})}"}

    @staticmethod
    async def handle_get_processing_stats():
        """Handle processing statistics request."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle({"type": "processing_stats"})
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"stats-{id({})}"}

    @staticmethod
    async def handle_scale_workers(req):
        """Handle worker scaling."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"scale-{id(req)}"}

    @staticmethod
    async def handle_start_processing():
        """Handle start processing request."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle({"type": "start_processing"})
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"start-{id({})}"}

    @staticmethod
    async def handle_set_load_balancing_strategy(req):
        """Handle load balancing strategy configuration."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"strategy-{id(req)}"}

    @staticmethod
    async def handle_get_queue_status():
        """Handle queue status request."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle({"type": "queue_status"})
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"queue-{id({})}"}

    @staticmethod
    async def handle_configure_load_balancing(req):
        """Handle load balancing configuration."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle(req)
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"config-{id(req)}"}

    @staticmethod
    async def handle_get_load_balancing_config():
        """Handle load balancing configuration retrieval."""
        handler = handler_registry.get_handler("distributed_analysis")
        if handler:
            return await handler.handle({"type": "get_load_balancing_config"})
        else:
            logger.error("No distributed analysis handler available")
            return {"error": "Handler not available", "analysis_id": f"get-config-{id({})}"}
