"""Core Analysis Routes.

Primary analysis endpoints including document analysis, semantic similarity,
sentiment, tone, quality, trends, risk, maintenance forecasting, degradation
detection, change impact, and PR analysis.
"""
from fastapi import APIRouter

# Import shared utilities
from services.shared.presentation.api.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes
from services.shared.infrastructure.monitoring.logging import fire_and_forget

# Import models
from ...modules.models import (
    AnalysisRequest,
    SemanticSimilarityRequest,
    SentimentAnalysisRequest,
    ToneAnalysisRequest,
    ContentQualityRequest,
    TrendAnalysisRequest,
    PortfolioTrendAnalysisRequest,
    RiskAssessmentRequest,
    PortfolioRiskAssessmentRequest,
    MaintenanceForecastRequest,
    PortfolioMaintenanceForecastRequest,
    QualityDegradationRequest,
    PortfolioQualityDegradationRequest,
    ChangeImpactRequest,
    PortfolioChangeImpactRequest,
    AnalysisReportRequest,
    PRAnalysisRequest
)

# Service metadata
SERVICE_NAME = "analysis-service"

# Create router
router = APIRouter(tags=["Core Analysis"])


@router.post("/analyze")
async def analyze_documents(req: AnalysisRequest):
    """Analyze documents for consistency and issues with configurable detectors.

    Performs comprehensive document analysis using various detectors to identify
    consistency issues, quality problems, and maintenance concerns across
    multiple document sources and types.

    Args:
        req: Analysis request with documents and detector configuration

    Returns:
        Comprehensive analysis results with findings and recommendations
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    return await analysis_handlers.handle_analyze_documents(req)


@router.post("/analyze/semantic-similarity")
async def analyze_semantic_similarity_endpoint(req: SemanticSimilarityRequest):
    """Analyze semantic similarity between documents using embeddings.

    Uses sentence transformers to detect conceptually similar but differently
    worded content across documents. Useful for identifying duplicate content,
    consolidation opportunities, and semantic relationships between documents.

    Args:
        req: Semantic similarity request with documents to compare

    Returns:
        Similarity analysis with pairs and scores
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_semantic_similarity_analysis(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Semantic similarity analysis completed",
            SERVICE_NAME,
            {
                "total_documents": result.total_documents,
                "similarity_pairs_found": len(result.similarity_pairs),
                "processing_time": result.processing_time,
                "model_used": result.model_used
            }
        )

        return create_success_response(
            "Semantic similarity analysis completed successfully",
            {
                "total_documents": result.total_documents,
                "similarity_pairs": [pair.model_dump() for pair in result.similarity_pairs],
                "analysis_summary": result.analysis_summary,
                "processing_time": result.processing_time,
                "model_used": result.model_used
            },
            total_documents=result.total_documents,
            similarity_pairs_found=len(result.similarity_pairs),
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Semantic similarity analysis failed",
            SERVICE_NAME,
            {"error": str(e), "request": req.model_dump()}
        )

        return create_error_response(
            f"Semantic similarity analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/sentiment")
async def analyze_sentiment_endpoint(req: SentimentAnalysisRequest):
    """Analyze sentiment, tone, and clarity of a document.

    Performs comprehensive sentiment analysis including tone assessment,
    readability scoring, and clarity evaluation to provide insights into
    documentation quality and user experience.

    Args:
        req: Sentiment analysis request with document content

    Returns:
        Sentiment analysis results with tone and readability metrics
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_sentiment_analysis(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Sentiment analysis completed",
            SERVICE_NAME,
            {
                "document_id": result.document_id,
                "sentiment": result.sentiment_analysis.get('sentiment', 'unknown'),
                "quality_score": result.quality_score,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            "Sentiment analysis completed successfully",
            {
                "document_id": result.document_id,
                "sentiment_analysis": result.sentiment_analysis,
                "readability_metrics": result.readability_metrics,
                "tone_analysis": result.tone_analysis,
                "quality_score": result.quality_score,
                "recommendations": result.recommendations,
                "processing_time": result.processing_time
            },
            document_id=result.document_id,
            quality_score=result.quality_score,
            sentiment=result.sentiment_analysis.get('sentiment', 'unknown'),
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Sentiment analysis failed",
            SERVICE_NAME,
            {"error": str(e), "document_id": req.document_id}
        )

        return create_error_response(
            f"Sentiment analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/tone")
async def analyze_tone_endpoint(req: ToneAnalysisRequest):
    """Analyze tone patterns and writing style in a document.

    Provides detailed analysis of writing tone, style patterns, and
    communication effectiveness based on the specified analysis scope.

    Args:
        req: Tone analysis request with document and scope

    Returns:
        Tone analysis results with style patterns
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_tone_analysis(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Tone analysis completed",
            SERVICE_NAME,
            {
                "document_id": result.document_id,
                "primary_tone": result.primary_tone,
                "analysis_scope": req.analysis_scope,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            "Tone analysis completed successfully",
            {
                "document_id": result.document_id,
                "primary_tone": result.primary_tone,
                "tone_scores": result.tone_scores,
                "tone_indicators": result.tone_indicators,
                "sentiment_summary": result.sentiment_summary,
                "clarity_assessment": result.clarity_assessment,
                "processing_time": result.processing_time
            },
            document_id=result.document_id,
            primary_tone=result.primary_tone,
            analysis_scope=req.analysis_scope,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Tone analysis failed",
            SERVICE_NAME,
            {"error": str(e), "document_id": req.document_id}
        )

        return create_error_response(
            f"Tone analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/quality")
async def analyze_content_quality_endpoint(req: ContentQualityRequest):
    """Analyze content quality and provide comprehensive assessment.

    Performs automated evaluation of documentation quality including readability,
    structure, completeness, and technical accuracy with detailed recommendations
    for improvement.

    Args:
        req: Content quality request with document content

    Returns:
        Quality assessment with metrics and recommendations
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_content_quality_assessment(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Content quality analysis completed",
            SERVICE_NAME,
            {
                "document_id": result.document_id,
                "quality_score": result.quality_assessment.get('overall_score', 0.0),
                "grade": result.quality_assessment.get('grade', 'N/A'),
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            "Content quality analysis completed successfully",
            {
                "document_id": result.document_id,
                "quality_assessment": result.quality_assessment,
                "detailed_metrics": result.detailed_metrics,
                "recommendations": result.recommendations,
                "processing_time": result.processing_time,
                "analysis_timestamp": result.analysis_timestamp
            },
            document_id=result.document_id,
            quality_score=result.quality_assessment.get('overall_score', 0.0),
            grade=result.quality_assessment.get('grade', 'N/A'),
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Content quality analysis failed",
            SERVICE_NAME,
            {"error": str(e), "document_id": req.document_id}
        )

        return create_error_response(
            f"Content quality analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/trends")
async def analyze_document_trends_endpoint(req: TrendAnalysisRequest):
    """Analyze trends and predict future issues for a document.

    Performs comprehensive trend analysis on historical analysis results to identify
    patterns, predict future documentation issues, and provide proactive recommendations
    for maintaining documentation quality.

    Args:
        req: Trend analysis request with document history

    Returns:
        Trend analysis with predictions and insights
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_trend_analysis(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Trend analysis completed",
            SERVICE_NAME,
            {
                "document_id": result.document_id,
                "trend_direction": result.trend_direction,
                "confidence": result.confidence,
                "data_points": result.data_points,
                "risk_areas_count": len(result.risk_areas),
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            "Trend analysis completed successfully",
            {
                "document_id": result.document_id,
                "trend_direction": result.trend_direction,
                "confidence": result.confidence,
                "patterns": result.patterns,
                "predictions": result.predictions,
                "risk_areas": result.risk_areas,
                "insights": result.insights,
                "analysis_period_days": result.analysis_period_days,
                "data_points": result.data_points,
                "volatility": result.volatility,
                "processing_time": result.processing_time,
                "analysis_timestamp": result.analysis_timestamp
            },
            document_id=result.document_id,
            trend_direction=result.trend_direction,
            confidence=result.confidence,
            data_points=result.data_points,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Trend analysis failed",
            SERVICE_NAME,
            {"error": str(e), "document_id": req.document_id}
        )

        return create_error_response(
            f"Trend analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/trends/portfolio")
async def analyze_portfolio_trends_endpoint(req: PortfolioTrendAnalysisRequest):
    """Analyze trends across a portfolio of documents.

    Performs comprehensive trend analysis across multiple documents to identify
    organization-wide patterns, compare documentation health, and provide
    strategic insights for documentation portfolio management.

    Args:
        req: Portfolio trend analysis request with multiple documents

    Returns:
        Portfolio trend analysis with comparative insights
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_portfolio_trend_analysis(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Portfolio trend analysis completed",
            SERVICE_NAME,
            {
                "document_count": result.document_count,
                "overall_trend": result.overall_trend,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            f"Portfolio trend analysis completed for {result.document_count} documents",
            {
                "document_count": result.document_count,
                "overall_trend": result.overall_trend,
                "document_trends": result.document_trends,
                "insights": result.insights,
                "processing_time": result.processing_time
            },
            document_count=result.document_count,
            overall_trend=result.overall_trend,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Portfolio trend analysis failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Portfolio trend analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/risk")
async def assess_document_risk_endpoint(req: RiskAssessmentRequest):
    """Assess risk level for a single document.

    Performs comprehensive risk assessment for documentation health, identifying
    potential issues, maintenance concerns, and quality risks with prioritized
    recommendations for mitigation.

    Args:
        req: Risk assessment request with document details

    Returns:
        Risk assessment with severity and mitigation strategies
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_risk_assessment(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Risk assessment completed",
            SERVICE_NAME,
            {
                "document_id": result.document_id,
                "overall_risk_level": result.overall_risk_level,
                "risk_score": result.risk_score,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            "Risk assessment completed successfully",
            {
                "document_id": result.document_id,
                "overall_risk_level": result.overall_risk_level,
                "risk_score": result.risk_score,
                "risk_factors": result.risk_factors,
                "mitigation_strategies": result.mitigation_strategies,
                "processing_time": result.processing_time
            },
            document_id=result.document_id,
            overall_risk_level=result.overall_risk_level,
            risk_score=result.risk_score,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Risk assessment failed",
            SERVICE_NAME,
            {"error": str(e), "document_id": req.document_id}
        )

        return create_error_response(
            f"Risk assessment failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/risk/portfolio")
async def assess_portfolio_risk_endpoint(req: PortfolioRiskAssessmentRequest):
    """Assess risk levels across a portfolio of documents.

    Performs comprehensive risk assessment across multiple documents to identify
    high-risk areas, prioritize maintenance efforts, and provide strategic risk
    management recommendations for documentation portfolios.

    Args:
        req: Portfolio risk assessment request with multiple documents

    Returns:
        Portfolio risk assessment with prioritized recommendations
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_portfolio_risk_assessment(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Portfolio risk assessment completed",
            SERVICE_NAME,
            {
                "document_count": result.document_count,
                "overall_risk_level": result.overall_risk_level,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            f"Portfolio risk assessment completed for {result.document_count} documents",
            {
                "document_count": result.document_count,
                "overall_risk_level": result.overall_risk_level,
                "document_risks": result.document_risks,
                "prioritized_actions": result.prioritized_actions,
                "processing_time": result.processing_time
            },
            document_count=result.document_count,
            overall_risk_level=result.overall_risk_level,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Portfolio risk assessment failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Portfolio risk assessment failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/maintenance/forecast")
async def forecast_maintenance_needs_endpoint(req: MaintenanceForecastRequest):
    """Forecast maintenance needs for a single document.

    Predicts future maintenance requirements based on document age, change frequency,
    quality trends, and historical patterns to enable proactive maintenance planning
    and resource allocation.

    Args:
        req: Maintenance forecast request with document details

    Returns:
        Maintenance forecast with predicted needs and timing
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_maintenance_forecast(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Maintenance forecast completed",
            SERVICE_NAME,
            {
                "document_id": result.document_id,
                "predicted_maintenance_level": result.predicted_maintenance_level,
                "urgency_score": result.urgency_score,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            "Maintenance forecast completed successfully",
            {
                "document_id": result.document_id,
                "predicted_maintenance_level": result.predicted_maintenance_level,
                "urgency_score": result.urgency_score,
                "recommended_actions": result.recommended_actions,
                "forecast_period_days": result.forecast_period_days,
                "processing_time": result.processing_time
            },
            document_id=result.document_id,
            predicted_maintenance_level=result.predicted_maintenance_level,
            urgency_score=result.urgency_score,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Maintenance forecast failed",
            SERVICE_NAME,
            {"error": str(e), "document_id": req.document_id}
        )

        return create_error_response(
            f"Maintenance forecast failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/maintenance/forecast/portfolio")
async def forecast_portfolio_maintenance_endpoint(req: PortfolioMaintenanceForecastRequest):
    """Forecast maintenance needs across a portfolio of documents.

    Provides comprehensive maintenance forecasting across multiple documents to enable
    strategic planning, resource allocation, and proactive portfolio management.

    Args:
        req: Portfolio maintenance forecast request with multiple documents

    Returns:
        Portfolio maintenance forecast with resource planning insights
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_portfolio_maintenance_forecast(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Portfolio maintenance forecast completed",
            SERVICE_NAME,
            {
                "document_count": result.document_count,
                "overall_maintenance_level": result.overall_maintenance_level,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            f"Portfolio maintenance forecast completed for {result.document_count} documents",
            {
                "document_count": result.document_count,
                "overall_maintenance_level": result.overall_maintenance_level,
                "document_forecasts": result.document_forecasts,
                "resource_recommendations": result.resource_recommendations,
                "processing_time": result.processing_time
            },
            document_count=result.document_count,
            overall_maintenance_level=result.overall_maintenance_level,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Portfolio maintenance forecast failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Portfolio maintenance forecast failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/quality/degradation")
async def detect_quality_degradation_endpoint(req: QualityDegradationRequest):
    """Detect quality degradation in a single document over time.

    Analyzes historical quality metrics to identify degradation patterns, determine
    causes, and provide actionable recommendations for quality restoration and
    prevention of further decline.

    Args:
        req: Quality degradation request with historical metrics

    Returns:
        Quality degradation analysis with restoration recommendations
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_quality_degradation_detection(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Quality degradation detection completed",
            SERVICE_NAME,
            {
                "document_id": result.document_id,
                "degradation_detected": result.degradation_detected,
                "severity": result.severity,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            "Quality degradation detection completed successfully",
            {
                "document_id": result.document_id,
                "degradation_detected": result.degradation_detected,
                "severity": result.severity,
                "degradation_patterns": result.degradation_patterns,
                "contributing_factors": result.contributing_factors,
                "recommendations": result.recommendations,
                "processing_time": result.processing_time
            },
            document_id=result.document_id,
            degradation_detected=result.degradation_detected,
            severity=result.severity,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Quality degradation detection failed",
            SERVICE_NAME,
            {"error": str(e), "document_id": req.document_id}
        )

        return create_error_response(
            f"Quality degradation detection failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/quality/degradation/portfolio")
async def detect_portfolio_quality_degradation_endpoint(req: PortfolioQualityDegradationRequest):
    """Detect quality degradation across a portfolio of documents.

    Provides comprehensive quality degradation analysis across multiple documents
    to identify systemic issues, prioritize restoration efforts, and enable
    proactive quality management strategies.

    Args:
        req: Portfolio quality degradation request with multiple documents

    Returns:
        Portfolio degradation analysis with prioritized actions
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_portfolio_quality_degradation_detection(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Portfolio quality degradation detection completed",
            SERVICE_NAME,
            {
                "document_count": result.document_count,
                "degradation_detected_count": result.degradation_detected_count,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            f"Portfolio quality degradation detection completed for {result.document_count} documents",
            {
                "document_count": result.document_count,
                "degradation_detected_count": result.degradation_detected_count,
                "document_analyses": result.document_analyses,
                "systemic_issues": result.systemic_issues,
                "prioritized_actions": result.prioritized_actions,
                "processing_time": result.processing_time
            },
            document_count=result.document_count,
            degradation_detected_count=result.degradation_detected_count,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Portfolio quality degradation detection failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Portfolio quality degradation detection failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/change/impact")
async def analyze_change_impact_endpoint(req: ChangeImpactRequest):
    """Analyze the impact of changes on a single document.

    Evaluates the effects of proposed or recent changes on documentation quality,
    structure, and relationships with other documents to inform decision-making
    and identify potential risks.

    Args:
        req: Change impact request with change details

    Returns:
        Change impact analysis with risk assessment
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_change_impact_analysis(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Change impact analysis completed",
            SERVICE_NAME,
            {
                "document_id": result.document_id,
                "impact_level": result.impact_level,
                "risk_score": result.risk_score,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            "Change impact analysis completed successfully",
            {
                "document_id": result.document_id,
                "impact_level": result.impact_level,
                "risk_score": result.risk_score,
                "affected_areas": result.affected_areas,
                "recommendations": result.recommendations,
                "processing_time": result.processing_time
            },
            document_id=result.document_id,
            impact_level=result.impact_level,
            risk_score=result.risk_score,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Change impact analysis failed",
            SERVICE_NAME,
            {"error": str(e), "document_id": req.document_id}
        )

        return create_error_response(
            f"Change impact analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/change/impact/portfolio")
async def analyze_portfolio_change_impact_endpoint(req: PortfolioChangeImpactRequest):
    """Analyze the impact of changes across a portfolio of documents.

    Provides comprehensive change impact analysis across multiple documents to
    understand ripple effects, identify dependencies, and enable coordinated
    change management strategies.

    Args:
        req: Portfolio change impact request with multiple documents

    Returns:
        Portfolio change impact analysis with dependency mapping
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_portfolio_change_impact_analysis(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "Portfolio change impact analysis completed",
            SERVICE_NAME,
            {
                "document_count": result.document_count,
                "overall_impact_level": result.overall_impact_level,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            f"Portfolio change impact analysis completed for {result.document_count} documents",
            {
                "document_count": result.document_count,
                "overall_impact_level": result.overall_impact_level,
                "document_impacts": result.document_impacts,
                "cascade_effects": result.cascade_effects,
                "coordinated_actions": result.coordinated_actions,
                "processing_time": result.processing_time
            },
            document_count=result.document_count,
            overall_impact_level=result.overall_impact_level,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Portfolio change impact analysis failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Portfolio change impact analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/generate-report")
async def generate_analysis_report_endpoint(req: AnalysisReportRequest):
    """Generate a comprehensive analysis report for a document.

    Creates formatted, customizable reports from analysis results with support
    for multiple output formats and report types to facilitate communication
    and decision-making.

    Args:
        req: Analysis report request with report configuration

    Returns:
        Generated analysis report in the specified format
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_generate_analysis_report(req)

        # Log successful generation
        fire_and_forget(
            "info",
            "Analysis report generated",
            SERVICE_NAME,
            {
                "document_id": req.document_id,
                "report_type": req.report_type,
                "format": req.format,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            "Analysis report generated successfully",
            {
                "document_id": result.document_id,
                "report_type": result.report_type,
                "format": result.format,
                "report_content": result.report_content,
                "metadata": result.metadata,
                "processing_time": result.processing_time
            },
            document_id=result.document_id,
            report_type=result.report_type,
            format=result.format,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Analysis report generation failed",
            SERVICE_NAME,
            {"error": str(e), "document_id": req.document_id}
        )

        return create_error_response(
            f"Analysis report generation failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/pull-request")
async def analyze_pull_request_endpoint(req: PRAnalysisRequest):
    """Analyze a pull request for documentation impact and quality.

    Performs comprehensive PR analysis including code quality assessment,
    documentation review, commit message analysis, and structural impact
    evaluation to support informed code review decisions.

    Args:
        req: PR analysis request with PR details

    Returns:
        Comprehensive PR analysis with recommendations
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_pull_request_analysis(req)

        # Log successful analysis
        fire_and_forget(
            "info",
            "PR analysis completed",
            SERVICE_NAME,
            {
                "pr_number": req.pr_number,
                "overall_score": result.overall_score,
                "recommendation": result.recommendation,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            "PR analysis completed successfully",
            {
                "pr_number": result.pr_number,
                "overall_score": result.overall_score,
                "recommendation": result.recommendation,
                "analysis_results": result.analysis_results,
                "suggestions": result.suggestions,
                "processing_time": result.processing_time
            },
            pr_number=result.pr_number,
            overall_score=result.overall_score,
            recommendation=result.recommendation,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "PR analysis failed",
            SERVICE_NAME,
            {"error": str(e), "pr_number": req.pr_number}
        )

        return create_error_response(
            f"PR analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/analyze/test-pr-analysis")
async def test_pr_analysis_endpoint(req: PRAnalysisRequest):
    """Test endpoint for PR analysis (development/testing purposes).

    Provides a test harness for PR analysis functionality with mock data
    and detailed logging for development and debugging purposes.

    Args:
        req: PR analysis request with PR details

    Returns:
        Test PR analysis results
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_test_pr_analysis(req)

        # Log test execution
        fire_and_forget(
            "info",
            "Test PR analysis completed",
            SERVICE_NAME,
            {
                "pr_number": req.pr_number,
                "test_mode": True,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            "Test PR analysis completed successfully",
            {
                "pr_number": result.pr_number,
                "test_mode": True,
                "analysis_results": result.analysis_results,
                "processing_time": result.processing_time
            },
            pr_number=result.pr_number,
            test_mode=True,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Test PR analysis failed",
            SERVICE_NAME,
            {"error": str(e), "pr_number": req.pr_number}
        )

        return create_error_response(
            f"Test PR analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )

