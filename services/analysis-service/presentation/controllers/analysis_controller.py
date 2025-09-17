"""Analysis Controller - Handles core document analysis endpoints."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from ...application.use_cases import PerformAnalysisUseCase
from ...application.dto import (
    PerformAnalysisRequest,
    AnalysisResultResponse,
    ErrorResponse
)
from ...infrastructure.repositories import (
    DocumentRepository,
    AnalysisRepository
)
from ...domain.services import AnalysisService
from ...presentation.models.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    SemanticSimilarityRequest,
    SemanticSimilarityResponse,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    ToneAnalysisRequest,
    ToneAnalysisResponse,
    ContentQualityRequest,
    ContentQualityResponse,
    TrendAnalysisRequest,
    TrendAnalysisResponse,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    MaintenanceForecastRequest,
    MaintenanceForecastResponse,
    QualityDegradationRequest,
    QualityDegradationResponse,
    ChangeImpactRequest,
    ChangeImpactResponse
)
from ...presentation.models.base import SuccessResponse, ErrorResponse
from ...modules.analysis_handlers import analysis_handlers


class AnalysisController:
    """Controller for analysis-related endpoints."""

    def __init__(self,
                 perform_analysis_use_case: PerformAnalysisUseCase,
                 document_repository: DocumentRepository,
                 analysis_repository: AnalysisRepository,
                 analysis_service: AnalysisService):
        """Initialize controller with dependencies."""
        self.perform_analysis_use_case = perform_analysis_use_case
        self.document_repository = document_repository
        self.analysis_repository = analysis_repository
        self.analysis_service = analysis_service
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.post("/analyze")
        async def analyze_documents(req: AnalysisRequest):
            """Analyze documents for consistency and issues with configurable detectors.

            Performs comprehensive document analysis using various detectors to identify
            consistency issues, quality problems, and maintenance concerns across
            multiple document sources and types.
            """
            return await analysis_handlers.handle_analyze_documents(req)

        @self.router.post("/analyze/semantic-similarity")
        async def analyze_semantic_similarity_endpoint(req: SemanticSimilarityRequest):
            """Analyze semantic similarity between documents using embeddings.

            Uses advanced embedding techniques to detect conceptually similar content
            across documents, helping identify redundancies and consolidation opportunities.
            """
            try:
                # Convert to our application request format
                app_request = PerformAnalysisRequest(
                    document_id=req.targets[0] if req.targets else "",
                    analysis_type="semantic_similarity",
                    configuration={
                        'threshold': req.threshold,
                        'embedding_model': req.embedding_model,
                        'similarity_metric': req.similarity_metric,
                        'options': req.options or {}
                    }
                )

                # Execute analysis
                result = await self.perform_analysis_use_case.execute(app_request)

                # Convert to API response format
                response = SemanticSimilarityResponse(
                    analysis_id=result.analysis.id,
                    analysis_type="semantic_similarity",
                    targets=req.targets,
                    status="completed",
                    results={
                        'similarities': [],  # Will be populated by the analysis
                        'threshold': req.threshold,
                        'metric': req.similarity_metric
                    },
                    findings=result.findings or []
                )

                return SuccessResponse.with_data(response.dict())

            except Exception as e:
                return ErrorResponse.from_exception(e).to_dict()

        @self.router.post("/analyze/sentiment")
        async def analyze_sentiment_endpoint(req: SentimentAnalysisRequest):
            """Analyze sentiment, tone, and clarity of documentation.

            Evaluates the emotional tone and clarity of documentation to ensure
            professional communication and effective knowledge transfer.
            """
            return await analysis_handlers.handle_sentiment_analysis(req)

        @self.router.post("/analyze/tone")
        async def analyze_tone_endpoint(req: ToneAnalysisRequest):
            """Analyze tone patterns and writing style in documents.

            Examines writing style, formality levels, and communication patterns
            to ensure consistent and appropriate documentation tone.
            """
            return await analysis_handlers.handle_tone_analysis(req)

        @self.router.post("/analyze/quality")
        async def analyze_quality_endpoint(req: ContentQualityRequest):
            """Analyze content quality with comprehensive assessment and recommendations.

            Provides detailed quality assessment with actionable recommendations
            for improving documentation clarity, completeness, and effectiveness.
            """
            return await analysis_handlers.handle_content_quality_assessment(req)

        @self.router.post("/analyze/trends")
        async def analyze_trends_endpoint(req: TrendAnalysisRequest):
            """Analyze trends and predict future issues for a document.

            Identifies patterns in documentation evolution and predicts potential
            future issues based on historical trends and current state.
            """
            return await analysis_handlers.handle_trend_analysis(req)

        @self.router.post("/analyze/trends/portfolio")
        async def analyze_trends_portfolio_endpoint(req: PortfolioTrendAnalysisRequest):
            """Analyze trends across a portfolio of documents.

            Performs comprehensive trend analysis across multiple documents to
            identify organizational patterns and predict future needs.
            """
            return await analysis_handlers.handle_portfolio_trend_analysis(req)

        @self.router.post("/analyze/risk")
        async def analyze_risk_endpoint(req: RiskAssessmentRequest):
            """Assess risk factors for documentation drift and quality degradation.

            Evaluates current documentation state against quality standards and
            identifies areas requiring immediate attention to prevent degradation.
            """
            return await analysis_handlers.handle_risk_assessment(req)

        @self.router.post("/analyze/risk/portfolio")
        async def analyze_risk_portfolio_endpoint(req: PortfolioRiskAssessmentRequest):
            """Assess risks across a portfolio of documents.

            Performs comprehensive risk assessment across multiple documents to
            identify organizational risks and prioritize mitigation efforts.
            """
            return await analysis_handlers.handle_portfolio_risk_assessment(req)

        @self.router.post("/analyze/maintenance/forecast")
        async def analyze_maintenance_forecast_endpoint(req: MaintenanceForecastRequest):
            """Forecast maintenance needs and schedule for documentation.

            Predicts when documentation will require updates based on multiple
            factors including usage patterns, team size, and content complexity.
            """
            return await analysis_handlers.handle_maintenance_forecast(req)

        @self.router.post("/analyze/maintenance/forecast/portfolio")
        async def analyze_maintenance_forecast_portfolio_endpoint(req: PortfolioMaintenanceForecastRequest):
            """Forecast maintenance needs across a portfolio of documents.

            Provides comprehensive maintenance forecasting across multiple documents
            to optimize resource allocation and maintenance scheduling.
            """
            return await analysis_handlers.handle_portfolio_maintenance_forecast(req)

        @self.router.post("/analyze/quality/degradation")
        async def analyze_quality_degradation_endpoint(req: QualityDegradationDetectionRequest):
            """Detect quality degradation in documentation over time.

            Monitors documentation quality metrics over time to identify
            degradation patterns and generate timely alerts.
            """
            return await analysis_handlers.handle_quality_degradation_detection(req)

        @self.router.post("/analyze/quality/degradation/portfolio")
        async def analyze_quality_degradation_portfolio_endpoint(req: PortfolioQualityDegradationRequest):
            """Monitor quality degradation across a portfolio of documents.

            Provides comprehensive quality monitoring across multiple documents
            with pattern recognition and predictive alerting.
            """
            return await analysis_handlers.handle_portfolio_quality_degradation(req)

        @self.router.post("/analyze/change/impact")
        async def analyze_change_impact_endpoint(req: ChangeImpactAnalysisRequest):
            """Analyze the impact of changes to documentation on related content.

            Evaluates how changes to specific documentation affect related content,
            stakeholders, and dependent systems to ensure coordinated updates.
            """
            return await analysis_handlers.handle_change_impact_analysis(req)

        @self.router.post("/analyze/change/impact/portfolio")
        async def analyze_change_impact_portfolio_endpoint(req: PortfolioChangeImpactRequest):
            """Analyze the impact of changes across a document portfolio.

            Performs comprehensive change impact analysis across multiple documents
            to understand the full scope of changes and required coordination.
            """
            return await analysis_handlers.handle_portfolio_change_impact_analysis(req)

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for this controller."""
        return self.router
