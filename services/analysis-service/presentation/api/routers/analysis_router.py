"""Analysis API endpoints router."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from application.dto.request_dtos import (
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
    ChangeImpactAnalysisRequest,
    PortfolioChangeImpactRequest,
)
from application.dto.response_dtos import AnalysisResponse
from application.services.analysis_application_service import AnalysisApplicationService

router = APIRouter(prefix="/analyze", tags=["analysis"])
application_service = AnalysisApplicationService()


@router.post("", response_model=AnalysisResponse)
async def analyze_documents(req: AnalysisRequest) -> Dict[str, Any]:
    """Analyze documents for consistency and issues with configurable detectors."""
    try:
        return await application_service.analyze_documents(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/semantic-similarity", response_model=AnalysisResponse)
async def analyze_semantic_similarity_endpoint(req: SemanticSimilarityRequest) -> Dict[str, Any]:
    """Analyze semantic similarity between documents using embeddings."""
    try:
        return await application_service.analyze_semantic_similarity(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic similarity analysis failed: {str(e)}")


@router.post("/sentiment", response_model=AnalysisResponse)
async def analyze_sentiment_endpoint(req: SentimentAnalysisRequest) -> Dict[str, Any]:
    """Analyze sentiment, tone, and clarity of documentation."""
    try:
        return await application_service.analyze_sentiment(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")


@router.post("/tone", response_model=AnalysisResponse)
async def analyze_tone_endpoint(req: ToneAnalysisRequest) -> Dict[str, Any]:
    """Analyze tone patterns and writing style in documents."""
    try:
        return await application_service.analyze_tone(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tone analysis failed: {str(e)}")


@router.post("/quality", response_model=AnalysisResponse)
async def analyze_content_quality_endpoint(req: ContentQualityRequest) -> Dict[str, Any]:
    """Analyze content quality with comprehensive assessment and recommendations."""
    try:
        return await application_service.analyze_content_quality(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content quality analysis failed: {str(e)}")


@router.post("/trends", response_model=AnalysisResponse)
async def analyze_document_trends_endpoint(req: TrendAnalysisRequest) -> Dict[str, Any]:
    """Analyze trends and predict future issues for a document."""
    try:
        return await application_service.analyze_document_trends(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.post("/trends/portfolio", response_model=AnalysisResponse)
async def analyze_portfolio_trends_endpoint(req: PortfolioTrendAnalysisRequest) -> Dict[str, Any]:
    """Analyze trends across a portfolio of documents."""
    try:
        return await application_service.analyze_portfolio_trends(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio trend analysis failed: {str(e)}")


@router.post("/risk", response_model=AnalysisResponse)
async def assess_document_risk_endpoint(req: RiskAssessmentRequest) -> Dict[str, Any]:
    """Assess risk factors for documentation drift and quality degradation."""
    try:
        return await application_service.assess_document_risk(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")


@router.post("/risk/portfolio", response_model=AnalysisResponse)
async def assess_portfolio_risk_endpoint(req: PortfolioRiskAssessmentRequest) -> Dict[str, Any]:
    """Assess risks across a portfolio of documents."""
    try:
        return await application_service.assess_portfolio_risk(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio risk assessment failed: {str(e)}")


@router.post("/maintenance/forecast", response_model=AnalysisResponse)
async def forecast_document_maintenance_endpoint(req: MaintenanceForecastRequest) -> Dict[str, Any]:
    """Forecast maintenance needs and schedule for documentation."""
    try:
        return await application_service.forecast_document_maintenance(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Maintenance forecast failed: {str(e)}")


@router.post("/quality/degradation", response_model=AnalysisResponse)
async def detect_document_quality_degradation_endpoint(req: QualityDegradationRequest) -> Dict[str, Any]:
    """Detect quality degradation in documentation over time."""
    try:
        return await application_service.detect_quality_degradation(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality degradation detection failed: {str(e)}")


@router.post("/change/impact", response_model=AnalysisResponse)
async def analyze_document_change_impact_endpoint(req: ChangeImpactAnalysisRequest) -> Dict[str, Any]:
    """Analyze the impact of changes to documentation on related content."""
    try:
        return await application_service.analyze_change_impact(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Change impact analysis failed: {str(e)}")


@router.post("/change/impact/portfolio", response_model=AnalysisResponse)
async def analyze_portfolio_change_impact_endpoint(req: PortfolioChangeImpactRequest) -> Dict[str, Any]:
    """Analyze the impact of changes across a document portfolio."""
    try:
        return await application_service.analyze_portfolio_change_impact(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio change impact analysis failed: {str(e)}")
