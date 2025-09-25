"""Analysis Service - Document Analysis Routes

This module contains the API routes for document analysis functionality.
"""

from fastapi import APIRouter, HTTPException
from typing import List

# Import request/response models and handlers
from ....application.schemas.requests import (
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
from ....application.schemas.responses import (
    AnalysisResponse,
    SemanticSimilarityResponse,
    SentimentAnalysisResponse,
)
from ....application.handlers import analysis_handlers
from ....infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_documents(request: AnalysisRequest):
    """Analyze documents for consistency and issues with configurable detectors.

    Performs comprehensive document analysis using various detectors to identify
    consistency issues, quality problems, and maintenance concerns across
    multiple document sources and types.

    Args:
        request: Analysis request with documents and configuration

    Returns:
        AnalysisResponse: Comprehensive analysis results
    """
    try:
        return await analysis_handlers.handle_analyze_documents(request)
    except Exception as e:
        logger.error(f"Document analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/semantic-similarity", response_model=SemanticSimilarityResponse)
async def analyze_semantic_similarity(request: SemanticSimilarityRequest):
    """Analyze semantic similarity between documents using embeddings.

    Uses sentence transformers to detect conceptually similar but differently
    worded content across documents. Useful for identifying duplicate content,
    consolidation opportunities, and semantic relationships between documents.

    Args:
        request: Semantic similarity analysis request

    Returns:
        SemanticSimilarityResponse: Similarity analysis results
    """
    try:
        return await analysis_handlers.handle_semantic_similarity_analysis(request)
    except Exception as e:
        logger.error(f"Semantic similarity analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/sentiment", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(request: SentimentAnalysisRequest):
    """Analyze sentiment, tone, and clarity of documentation.

    Performs sentiment analysis to understand the emotional tone and clarity
    of documentation content, helping identify areas that may confuse or
    frustrate users.

    Args:
        request: Sentiment analysis request

    Returns:
        SentimentAnalysisResponse: Sentiment analysis results
    """
    try:
        return await analysis_handlers.handle_sentiment_analysis(request)
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
