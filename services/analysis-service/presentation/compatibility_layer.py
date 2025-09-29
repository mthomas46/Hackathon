# =============================================================================
# API COMPATIBILITY LAYER - BACKWARD COMPATIBILITY FOR EXISTING CLIENTS
# =============================================================================
# This module provides backward compatibility for all existing API endpoints
# while the underlying implementation uses the new DDD architecture.
#
# All endpoints maintain their original request/response formats and behavior.
# Deprecation warnings are added to guide clients to new endpoints when available.
# =============================================================================

import logging
import warnings
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from ..domain.models import (
    AnalysisRequest, AnalysisResponse, SemanticSimilarityRequest, SentimentAnalysisRequest,
    ToneAnalysisRequest, ContentQualityRequest, TrendAnalysisRequest, RiskAssessmentRequest,
    MaintenanceForecastRequest, QualityDegradationRequest, ChangeImpactRequest,
    RemediationRequest, WorkflowEventRequest, RepositoryAnalysisRequest,
    DistributedTaskRequest, ReportRequest, FindingsRequest, NotifyOwnersRequest,
    ArchitectureAnalysisRequest, PRConfidenceRequest
)
from .controllers import (
    AnalysisController, RemediationController, WorkflowController,
    RepositoryController, DistributedController, ReportsController,
    FindingsController, PRConfidenceController
)

logger = logging.getLogger(__name__)

# Create compatibility router
compatibility_router = APIRouter(prefix="", tags=["compatibility"])

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def add_deprecation_warning(response_data: Dict[str, Any], endpoint: str, new_endpoint: Optional[str] = None) -> Dict[str, Any]:
    """Add deprecation warning to response data."""
    warnings.warn(
        f"Endpoint '{endpoint}' is deprecated. " +
        (f"Consider using '{new_endpoint}' instead." if new_endpoint else "This endpoint will be removed in a future version."),
        DeprecationWarning,
        stacklevel=2
    )

    if isinstance(response_data, dict) and "warnings" not in response_data:
        response_data["warnings"] = []

    if isinstance(response_data, dict):
        response_data["warnings"].append({
            "type": "deprecation",
            "message": f"Endpoint '{endpoint}' is deprecated",
            "recommended_action": f"Use '{new_endpoint}' instead" if new_endpoint else "Migrate to new API version"
        })

    return response_data

def ensure_backward_compatibility(response: Any) -> Any:
    """Ensure response maintains backward compatibility."""
    if hasattr(response, 'dict'):
        response_dict = response.dict()
    elif isinstance(response, dict):
        response_dict = response
    else:
        return response

    # Add metadata for compatibility
    if isinstance(response_dict, dict):
        response_dict["_compatibility"] = {
            "version": "legacy",
            "ddd_backend": True,
            "maintained_until": "2026-09-17"
        }

    return response_dict

# ============================================================================
# LEGACY ENDPOINT IMPLEMENTATIONS
# ============================================================================

@compatibility_router.post("/analyze")
async def legacy_analyze_endpoint(request: AnalysisRequest):
    """LEGACY: Document consistency analysis - Original endpoint preserved for compatibility."""
    try:
        result = await AnalysisController.analyze_documents(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze", "/analyze (same endpoint)")
        return result
    except Exception as e:
        logger.error(f"Error in legacy /analyze endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/semantic-similarity")
async def legacy_semantic_similarity_endpoint(request: SemanticSimilarityRequest):
    """LEGACY: Semantic similarity analysis - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_semantic_similarity(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/semantic-similarity")
        return result
    except Exception as e:
        logger.error(f"Error in legacy semantic similarity endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/sentiment")
async def legacy_sentiment_analysis_endpoint(request: SentimentAnalysisRequest):
    """LEGACY: Sentiment analysis - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_sentiment(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/sentiment")
        return result
    except Exception as e:
        logger.error(f"Error in legacy sentiment analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/tone")
async def legacy_tone_analysis_endpoint(request: ToneAnalysisRequest):
    """LEGACY: Tone analysis - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_tone(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/tone")
        return result
    except Exception as e:
        logger.error(f"Error in legacy tone analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/quality")
async def legacy_content_quality_endpoint(request: ContentQualityRequest):
    """LEGACY: Content quality assessment - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_content_quality(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/quality")
        return result
    except Exception as e:
        logger.error(f"Error in legacy content quality endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/trends")
async def legacy_trend_analysis_endpoint(request: TrendAnalysisRequest):
    """LEGACY: Trend analysis - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_trends(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/trends")
        return result
    except Exception as e:
        logger.error(f"Error in legacy trend analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/trends/portfolio")
async def legacy_portfolio_trend_analysis_endpoint(request: Dict[str, Any]):
    """LEGACY: Portfolio trend analysis - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_portfolio_trends(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/trends/portfolio")
        return result
    except Exception as e:
        logger.error(f"Error in legacy portfolio trend analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/risk")
async def legacy_risk_assessment_endpoint(request: RiskAssessmentRequest):
    """LEGACY: Risk assessment - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_risk(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/risk")
        return result
    except Exception as e:
        logger.error(f"Error in legacy risk assessment endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/risk/portfolio")
async def legacy_portfolio_risk_assessment_endpoint(request: Dict[str, Any]):
    """LEGACY: Portfolio risk assessment - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_portfolio_risk(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/risk/portfolio")
        return result
    except Exception as e:
        logger.error(f"Error in legacy portfolio risk assessment endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/maintenance/forecast")
async def legacy_maintenance_forecast_endpoint(request: MaintenanceForecastRequest):
    """LEGACY: Maintenance forecast - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_maintenance_forecast(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/maintenance/forecast")
        return result
    except Exception as e:
        logger.error(f"Error in legacy maintenance forecast endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/maintenance/forecast/portfolio")
async def legacy_portfolio_maintenance_forecast_endpoint(request: Dict[str, Any]):
    """LEGACY: Portfolio maintenance forecast - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_portfolio_maintenance_forecast(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/maintenance/forecast/portfolio")
        return result
    except Exception as e:
        logger.error(f"Error in legacy portfolio maintenance forecast endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/quality/degradation")
async def legacy_quality_degradation_endpoint(request: QualityDegradationRequest):
    """LEGACY: Quality degradation detection - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_quality_degradation(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/quality/degradation")
        return result
    except Exception as e:
        logger.error(f"Error in legacy quality degradation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/quality/degradation/portfolio")
async def legacy_portfolio_quality_degradation_endpoint(request: Dict[str, Any]):
    """LEGACY: Portfolio quality degradation - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_portfolio_quality_degradation(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/quality/degradation/portfolio")
        return result
    except Exception as e:
        logger.error(f"Error in legacy portfolio quality degradation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/change/impact")
async def legacy_change_impact_endpoint(request: ChangeImpactRequest):
    """LEGACY: Change impact analysis - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_change_impact(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/change/impact")
        return result
    except Exception as e:
        logger.error(f"Error in legacy change impact endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/analyze/change/impact/portfolio")
async def legacy_portfolio_change_impact_endpoint(request: Dict[str, Any]):
    """LEGACY: Portfolio change impact analysis - Original endpoint preserved."""
    try:
        result = await AnalysisController.analyze_portfolio_change_impact(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/analyze/change/impact/portfolio")
        return result
    except Exception as e:
        logger.error(f"Error in legacy portfolio change impact endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/remediate")
async def legacy_remediation_endpoint(request: RemediationRequest):
    """LEGACY: Automated remediation - Original endpoint preserved."""
    try:
        result = await RemediationController.remediate(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/remediate")
        return result
    except Exception as e:
        logger.error(f"Error in legacy remediation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/remediate/preview")
async def legacy_remediation_preview_endpoint(request: Dict[str, Any]):
    """LEGACY: Remediation preview - Original endpoint preserved."""
    try:
        result = await RemediationController.preview_remediation(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/remediate/preview")
        return result
    except Exception as e:
        logger.error(f"Error in legacy remediation preview endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/workflows/events")
async def legacy_workflow_events_endpoint(request: WorkflowEventRequest):
    """LEGACY: Workflow events - Original endpoint preserved."""
    try:
        result = await WorkflowController.process_event(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/workflows/events")
        return result
    except Exception as e:
        logger.error(f"Error in legacy workflow events endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/workflows/{workflow_id}")
async def legacy_workflow_status_endpoint(workflow_id: str):
    """LEGACY: Workflow status - Original endpoint preserved."""
    try:
        result = await WorkflowController.get_workflow_status(workflow_id)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/workflows/{workflow_id}")
        return result
    except Exception as e:
        logger.error(f"Error in legacy workflow status endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/workflows/queue/status")
async def legacy_workflow_queue_status_endpoint():
    """LEGACY: Workflow queue status - Original endpoint preserved."""
    try:
        result = await WorkflowController.get_queue_status()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/workflows/queue/status")
        return result
    except Exception as e:
        logger.error(f"Error in legacy workflow queue status endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/workflows/webhook/config")
async def legacy_webhook_config_endpoint(request: Dict[str, Any]):
    """LEGACY: Webhook configuration - Original endpoint preserved."""
    try:
        result = await WorkflowController.configure_webhook(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/workflows/webhook/config")
        return result
    except Exception as e:
        logger.error(f"Error in legacy webhook config endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/repositories/analyze")
async def legacy_repository_analysis_endpoint(request: RepositoryAnalysisRequest):
    """LEGACY: Repository analysis - Original endpoint preserved."""
    try:
        result = await RepositoryController.analyze_repositories(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/repositories/analyze")
        return result
    except Exception as e:
        logger.error(f"Error in legacy repository analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/repositories/connectivity")
async def legacy_repository_connectivity_endpoint(request: Dict[str, Any]):
    """LEGACY: Repository connectivity test - Original endpoint preserved."""
    try:
        result = await RepositoryController.test_connectivity(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/repositories/connectivity")
        return result
    except Exception as e:
        logger.error(f"Error in legacy repository connectivity endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/repositories/connectors/config")
async def legacy_connector_config_endpoint(request: Dict[str, Any]):
    """LEGACY: Connector configuration - Original endpoint preserved."""
    try:
        result = await RepositoryController.configure_connector(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/repositories/connectors/config")
        return result
    except Exception as e:
        logger.error(f"Error in legacy connector config endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/repositories/connectors")
async def legacy_supported_connectors_endpoint():
    """LEGACY: Supported connectors - Original endpoint preserved."""
    try:
        result = await RepositoryController.get_supported_connectors()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/repositories/connectors")
        return result
    except Exception as e:
        logger.error(f"Error in legacy supported connectors endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/repositories/frameworks")
async def legacy_analysis_frameworks_endpoint():
    """LEGACY: Analysis frameworks - Original endpoint preserved."""
    try:
        result = await RepositoryController.get_analysis_frameworks()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/repositories/frameworks")
        return result
    except Exception as e:
        logger.error(f"Error in legacy analysis frameworks endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/distributed/tasks")
async def legacy_submit_task_endpoint(request: DistributedTaskRequest):
    """LEGACY: Submit distributed task - Original endpoint preserved."""
    try:
        result = await DistributedController.submit_task(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/tasks")
        return result
    except Exception as e:
        logger.error(f"Error in legacy submit task endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/distributed/tasks/batch")
async def legacy_submit_batch_tasks_endpoint(request: Dict[str, Any]):
    """LEGACY: Submit batch tasks - Original endpoint preserved."""
    try:
        result = await DistributedController.submit_batch_tasks(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/tasks/batch")
        return result
    except Exception as e:
        logger.error(f"Error in legacy submit batch tasks endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/distributed/tasks/{task_id}")
async def legacy_get_task_status_endpoint(task_id: str):
    """LEGACY: Get task status - Original endpoint preserved."""
    try:
        result = await DistributedController.get_task_status(task_id)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/tasks/{task_id}")
        return result
    except Exception as e:
        logger.error(f"Error in legacy get task status endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.delete("/distributed/tasks/{task_id}")
async def legacy_cancel_task_endpoint(task_id: str):
    """LEGACY: Cancel task - Original endpoint preserved."""
    try:
        result = await DistributedController.cancel_task(task_id)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/tasks/{task_id}")
        return result
    except Exception as e:
        logger.error(f"Error in legacy cancel task endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/distributed/workers")
async def legacy_get_workers_status_endpoint():
    """LEGACY: Get workers status - Original endpoint preserved."""
    try:
        result = await DistributedController.get_workers_status()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/workers")
        return result
    except Exception as e:
        logger.error(f"Error in legacy get workers status endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/distributed/stats")
async def legacy_get_processing_stats_endpoint():
    """LEGACY: Get processing stats - Original endpoint preserved."""
    try:
        result = await DistributedController.get_processing_stats()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/stats")
        return result
    except Exception as e:
        logger.error(f"Error in legacy get processing stats endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/distributed/workers/scale")
async def legacy_scale_workers_endpoint(request: Dict[str, Any]):
    """LEGACY: Scale workers - Original endpoint preserved."""
    try:
        result = await DistributedController.scale_workers(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/workers/scale")
        return result
    except Exception as e:
        logger.error(f"Error in legacy scale workers endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/distributed/start")
async def legacy_start_distributed_processing_endpoint():
    """LEGACY: Start distributed processing - Original endpoint preserved."""
    try:
        result = await DistributedController.start_processing()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/start")
        return result
    except Exception as e:
        logger.error(f"Error in legacy start distributed processing endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.put("/distributed/load-balancing/strategy")
async def legacy_set_load_balancing_strategy_endpoint(request: Dict[str, Any]):
    """LEGACY: Set load balancing strategy - Original endpoint preserved."""
    try:
        result = await DistributedController.set_load_balancing_strategy(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/load-balancing/strategy")
        return result
    except Exception as e:
        logger.error(f"Error in legacy set load balancing strategy endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/distributed/queue/status")
async def legacy_get_queue_status_endpoint():
    """LEGACY: Get queue status - Original endpoint preserved."""
    try:
        result = await DistributedController.get_queue_status()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/queue/status")
        return result
    except Exception as e:
        logger.error(f"Error in legacy get queue status endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.put("/distributed/load-balancing/config")
async def legacy_configure_load_balancing_endpoint(request: Dict[str, Any]):
    """LEGACY: Configure load balancing - Original endpoint preserved."""
    try:
        result = await DistributedController.configure_load_balancing(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/load-balancing/config")
        return result
    except Exception as e:
        logger.error(f"Error in legacy configure load balancing endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/distributed/load-balancing/config")
async def legacy_get_load_balancing_config_endpoint():
    """LEGACY: Get load balancing config - Original endpoint preserved."""
    try:
        result = await DistributedController.get_load_balancing_config()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/distributed/load-balancing/config")
        return result
    except Exception as e:
        logger.error(f"Error in legacy get load balancing config endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/reports/generate")
async def legacy_generate_report_endpoint(request: ReportRequest):
    """LEGACY: Generate report - Original endpoint preserved."""
    try:
        result = await ReportsController.generate_report(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/reports/generate")
        return result
    except Exception as e:
        logger.error(f"Error in legacy generate report endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/findings")
async def legacy_get_findings_endpoint(request: FindingsRequest = None):
    """LEGACY: Get findings - Original endpoint preserved."""
    try:
        if request is None:
            request = FindingsRequest()
        result = await FindingsController.get_findings(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/findings")
        return result
    except Exception as e:
        logger.error(f"Error in legacy get findings endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/detectors")
async def legacy_list_detectors_endpoint():
    """LEGACY: List detectors - Original endpoint preserved."""
    try:
        result = await FindingsController.list_detectors()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/detectors")
        return result
    except Exception as e:
        logger.error(f"Error in legacy list detectors endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/reports/confluence/consolidation")
async def legacy_confluence_consolidation_endpoint():
    """LEGACY: Confluence consolidation report - Original endpoint preserved."""
    try:
        result = await ReportsController.get_confluence_consolidation()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/reports/confluence/consolidation")
        return result
    except Exception as e:
        logger.error(f"Error in legacy confluence consolidation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/reports/jira/staleness")
async def legacy_jira_staleness_endpoint():
    """LEGACY: Jira staleness report - Original endpoint preserved."""
    try:
        result = await ReportsController.get_jira_staleness()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/reports/jira/staleness")
        return result
    except Exception as e:
        logger.error(f"Error in legacy jira staleness endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/reports/findings/notify-owners")
async def legacy_notify_owners_endpoint(request: NotifyOwnersRequest):
    """LEGACY: Notify owners - Original endpoint preserved."""
    try:
        result = await ReportsController.notify_owners(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/reports/findings/notify-owners")
        return result
    except Exception as e:
        logger.error(f"Error in legacy notify owners endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/integration/health")
async def legacy_integration_health_endpoint():
    """LEGACY: Integration health - Original endpoint preserved."""
    try:
        result = await IntegrationController.get_health()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/integration/health")
        return result
    except Exception as e:
        logger.error(f"Error in legacy integration health endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/integration/analyze-with-prompt")
async def legacy_analyze_with_prompt_endpoint(request: Dict[str, Any]):
    """LEGACY: Analyze with prompt - Original endpoint preserved."""
    try:
        result = await IntegrationController.analyze_with_prompt(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/integration/analyze-with-prompt")
        return result
    except Exception as e:
        logger.error(f"Error in legacy analyze with prompt endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/integration/natural-language-analysis")
async def legacy_natural_language_analysis_endpoint(request: Dict[str, Any]):
    """LEGACY: Natural language analysis - Original endpoint preserved."""
    try:
        result = await IntegrationController.natural_language_analysis(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/integration/natural-language-analysis")
        return result
    except Exception as e:
        logger.error(f"Error in legacy natural language analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/integration/prompts/categories")
async def legacy_prompts_categories_endpoint():
    """LEGACY: Prompts categories - Original endpoint preserved."""
    try:
        result = await IntegrationController.get_prompt_categories()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/integration/prompts/categories")
        return result
    except Exception as e:
        logger.error(f"Error in legacy prompts categories endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/integration/log-analysis")
async def legacy_log_analysis_endpoint(request: Dict[str, Any]):
    """LEGACY: Log analysis - Original endpoint preserved."""
    try:
        result = await IntegrationController.analyze_logs(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/integration/log-analysis")
        return result
    except Exception as e:
        logger.error(f"Error in legacy log analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/architecture/analyze")
async def legacy_architecture_analysis_endpoint(request: ArchitectureAnalysisRequest):
    """LEGACY: Architecture analysis - Original endpoint preserved."""
    try:
        result = await IntegrationController.analyze_architecture(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/architecture/analyze")
        return result
    except Exception as e:
        logger.error(f"Error in legacy architecture analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.post("/pr-confidence/analyze")
async def legacy_pr_confidence_analysis_endpoint(request: PRConfidenceRequest):
    """LEGACY: PR confidence analysis - Original endpoint preserved."""
    try:
        result = await PRConfidenceController.analyze_pr_confidence(request)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/pr-confidence/analyze")
        return result
    except Exception as e:
        logger.error(f"Error in legacy PR confidence analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/pr-confidence/history/{pr_id}")
async def legacy_pr_confidence_history_endpoint(pr_id: str):
    """LEGACY: PR confidence history - Original endpoint preserved."""
    try:
        result = await PRConfidenceController.get_pr_history(pr_id)
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/pr-confidence/history/{pr_id}")
        return result
    except Exception as e:
        logger.error(f"Error in legacy PR confidence history endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compatibility_router.get("/pr-confidence/statistics")
async def legacy_pr_confidence_statistics_endpoint():
    """LEGACY: PR confidence statistics - Original endpoint preserved."""
    try:
        result = await PRConfidenceController.get_statistics()
        result = ensure_backward_compatibility(result)
        result = add_deprecation_warning(result, "/pr-confidence/statistics")
        return result
    except Exception as e:
        logger.error(f"Error in legacy PR confidence statistics endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# COMPATIBILITY ENDPOINT REGISTRATION
# ============================================================================

def register_compatibility_endpoints(app: Any) -> None:
    """Register all compatibility endpoints with the FastAPI application."""
    app.include_router(compatibility_router)

    # Log compatibility layer activation
    logger.info("API Compatibility Layer activated - All 53 legacy endpoints preserved")
    logger.info("Deprecation warnings enabled for legacy endpoints")
    logger.info("DDD backend compatibility mode: ACTIVE")
