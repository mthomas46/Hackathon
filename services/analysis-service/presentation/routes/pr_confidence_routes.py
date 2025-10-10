"""PR Confidence and Architecture Analysis Routes.

PR confidence scoring, architecture analysis, and analysis history.
"""
from typing import Any, Dict
from fastapi import APIRouter, HTTPException

# Import shared utilities
from services.shared.presentation.api.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes
from services.shared.infrastructure.monitoring.logging import fire_and_forget

# Import models
from ...modules.models import ArchitectureAnalysisRequest

# Service metadata
SERVICE_NAME = "analysis-service"

# Create router
router = APIRouter(tags=["PR Confidence & Architecture"])


@router.post("/architecture/analyze")
async def analyze_architecture(req: ArchitectureAnalysisRequest):
    """Analyze architectural diagrams for consistency, completeness, and best practices.

    Performs specialized analysis on normalized architecture data from the
    architecture-digitizer service, identifying potential issues, inconsistencies,
    and providing recommendations for improvement.

    Args:
        req: Architecture analysis request with components and connections

    Returns:
        Architecture analysis results with issues and recommendations
    """
    # Import here to avoid circular dependencies
    from ...modules.integration_handlers import integration_handlers
    
    try:
        # Get the appropriate analyzer for the analysis type
        analyzer = integration_handlers.get_architecture_analyzer(req.analysis_type)
        if not analyzer:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported architecture analysis type: {req.analysis_type}"
            )

        # Perform the analysis
        results = await analyzer.analyze_architecture(req.components, req.connections, req.options or {})

        # Log the analysis
        fire_and_forget(
            "info",
            f"Completed architecture analysis: {req.analysis_type}",
            SERVICE_NAME,
            {
                "analysis_type": req.analysis_type,
                "component_count": len(req.components),
                "connection_count": len(req.connections)
            }
        )

        return create_success_response(
            "Architecture analysis completed",
            results,
            analysis_type=req.analysis_type,
            component_count=len(req.components),
            connection_count=len(req.connections)
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            f"Architecture analysis failed: {req.analysis_type}",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Architecture analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/pr-confidence/analyze")
async def analyze_pr_confidence(req: Dict[str, Any]):
    """Analyze PR confidence with comprehensive cross-reference analysis.

    Performs detailed analysis of a pull request against its requirements
    and documentation to provide confidence scores and recommendations.

    Args:
        req: PR confidence analysis request with PR data, JIRA data, and Confluence docs

    Returns:
        Comprehensive PR confidence analysis with scores and recommendations
    """
    try:
        from ...modules.pr_confidence_analysis import (
            PRConfidenceAnalysisRequest,
            pr_confidence_analysis_service
        )

        # Create request object from dict
        analysis_request = PRConfidenceAnalysisRequest(
            pr_data=req.get("pr_data", {}),
            jira_data=req.get("jira_data"),
            confluence_docs=req.get("confluence_docs"),
            analysis_scope=req.get("analysis_scope", "comprehensive"),
            include_recommendations=req.get("include_recommendations", True),
            confidence_threshold=req.get("confidence_threshold", 0.7)
        )

        # Perform the analysis
        result = await pr_confidence_analysis_service.analyze_pr_confidence(analysis_request)

        # Log the analysis
        fire_and_forget(
            "info",
            f"Completed PR confidence analysis: {result.workflow_id}",
            SERVICE_NAME,
            {
                "workflow_id": result.workflow_id,
                "confidence_score": result.confidence_score,
                "confidence_level": result.confidence_level,
                "approval_recommendation": result.approval_recommendation
            }
        )

        return create_success_response(
            "PR confidence analysis completed successfully",
            {
                "workflow_id": result.workflow_id,
                "analysis_timestamp": result.analysis_timestamp,
                "confidence_score": result.confidence_score,
                "confidence_level": result.confidence_level,
                "approval_recommendation": result.approval_recommendation,
                "cross_reference_results": result.cross_reference_results,
                "detected_gaps": result.detected_gaps,
                "component_scores": result.component_scores,
                "recommendations": result.recommendations,
                "critical_concerns": result.critical_concerns,
                "strengths": result.strengths,
                "improvement_areas": result.improvement_areas,
                "risk_assessment": result.risk_assessment,
                "analysis_duration": result.analysis_duration
            },
            workflow_id=result.workflow_id,
            confidence_score=result.confidence_score,
            analysis_duration=result.analysis_duration
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            f"PR confidence analysis failed",
            SERVICE_NAME,
            {"error": str(e), "request": str(req)}
        )

        return create_error_response(
            f"PR confidence analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.get("/pr-confidence/history/{pr_id}")
async def get_pr_analysis_history(pr_id: str):
    """Get analysis history for a specific PR.

    Retrieves all historical PR confidence analysis results for the specified PR,
    allowing tracking of confidence scores over time and analysis evolution.

    Args:
        pr_id: Pull request identifier

    Returns:
        Historical analysis results for the PR
    """
    try:
        from ...modules.pr_confidence_analysis import pr_confidence_analysis_service

        history = await pr_confidence_analysis_service.get_pr_analysis_history(pr_id)

        return create_success_response(
            f"Retrieved analysis history for PR {pr_id}",
            {"pr_id": pr_id, "history": history},
            history_count=len(history)
        )

    except Exception as e:
        return create_error_response(
            f"Failed to retrieve PR analysis history: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@router.get("/pr-confidence/statistics")
async def get_analysis_statistics():
    """Get analysis statistics and metrics.

    Returns aggregate statistics across all PR confidence analyses,
    including average confidence scores, common issues, and trend data.

    Returns:
        Analysis statistics and metrics
    """
    try:
        from ...modules.pr_confidence_analysis import pr_confidence_analysis_service

        stats = await pr_confidence_analysis_service.get_analysis_statistics()

        return create_success_response(
            "Retrieved analysis statistics",
            stats
        )

    except Exception as e:
        return create_error_response(
            f"Failed to retrieve analysis statistics: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )

