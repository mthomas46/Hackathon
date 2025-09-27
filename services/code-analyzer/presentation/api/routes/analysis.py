"""Code analysis REST API routes."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, UploadFile, File
from pydantic import BaseModel, Field
from datetime import datetime

from ....application.use_cases.analyze_code_use_case import (
    AnalyzeCodeUseCase,
    AnalyzeCodeRequest,
    AnalyzeCodeResponse
)


# Pydantic models for API
class AnalysisRequestModel(BaseModel):
    """API model for code analysis request."""
    source_type: str = Field(..., description="Source system type (github, jira, etc.)")
    title: str = Field(..., description="Analysis title")
    content: str = Field(..., description="Code content to analyze")
    source_refs: Optional[List[Dict[str, Any]]] = Field(None, description="Source references")
    repo: Optional[str] = Field(None, description="Repository name")
    path: Optional[str] = Field(None, description="File path")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    include_endpoints: bool = Field(True, description="Extract API endpoints")
    include_style_check: bool = Field(True, description="Perform style checking")


class AnalysisResultModel(BaseModel):
    """API model for analysis result."""
    id: str
    source_type: str
    title: str
    quality_score: float
    endpoints_found: int
    security_issues: int
    style_violations: int
    processing_time_seconds: float
    analysis_timestamp: datetime


class AnalysisResponseModel(BaseModel):
    """API model for analysis response."""
    success: bool
    result: AnalysisResultModel
    endpoints_found: int
    style_violations: int
    processing_time_seconds: float
    message: str


class AnalysisStatsModel(BaseModel):
    """API model for analysis statistics."""
    total_analyses: int
    average_quality_score: float
    total_security_issues: int
    total_endpoints_found: int
    sources_analyzed: int


class CodeAnalysisRouter:
    """FastAPI router for code analysis operations."""

    def __init__(
        self,
        analyze_code_use_case: AnalyzeCodeUseCase
    ):
        """Initialize router with use cases."""
        self._analyze_code_use_case = analyze_code_use_case
        self.router = APIRouter(prefix="/api/v1/analysis", tags=["code-analysis"])

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all analysis routes."""

        @self.router.post("/analyze", response_model=AnalysisResponseModel)
        async def analyze_code(
            request: AnalysisRequestModel,
            background_tasks: BackgroundTasks
        ) -> AnalysisResponseModel:
            """Analyze code and generate comprehensive report.

            Performs complete code analysis including endpoint extraction,
            security scanning, style validation, and quality assessment.
            """
            try:
                # Convert API model to use case request
                use_case_request = AnalyzeCodeRequest(
                    source_type=request.source_type,
                    title=request.title,
                    content=request.content,
                    source_refs=request.source_refs,
                    repo=request.repo,
                    path=request.path,
                    correlation_id=request.correlation_id,
                    include_endpoints=request.include_endpoints,
                    include_style_check=request.include_style_check
                )

                # Execute use case
                response = await self._analyze_code_use_case.execute(use_case_request)

                # Convert domain entity to API model
                result_model = AnalysisResultModel(
                    id=response.analysis_result.id,
                    source_type=response.analysis_result.source_type,
                    title=response.analysis_result.title,
                    quality_score=response.analysis_result.quality_score,
                    endpoints_found=len(response.analysis_result.endpoints_found),
                    security_issues=len(response.analysis_result.security_issues),
                    style_violations=len(response.analysis_result.style_violations),
                    processing_time_seconds=response.analysis_result.processing_time_seconds,
                    analysis_timestamp=response.analysis_result.analysis_timestamp
                )

                return AnalysisResponseModel(
                    success=response.success,
                    result=result_model,
                    endpoints_found=response.endpoints_found,
                    style_violations=response.style_violations,
                    processing_time_seconds=response.processing_time_seconds,
                    message=response.message
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Code analysis failed: {str(e)}"
                )

        @self.router.post("/analyze/file")
        async def analyze_code_file(
            background_tasks: BackgroundTasks,
            file: UploadFile = File(...),
            source_type: str = Query(..., description="Source system type"),
            title: Optional[str] = Query(None, description="Analysis title"),
            include_endpoints: bool = Query(True, description="Extract endpoints"),
            include_style_check: bool = Query(True, description="Check style")
        ) -> AnalysisResponseModel:
            """Analyze uploaded code file.

            Upload a code file for comprehensive analysis including
            security scanning, quality assessment, and endpoint extraction.
            """
            try:
                # Read file content
                content = await file.read()
                content_str = content.decode('utf-8')

                # Generate title if not provided
                analysis_title = title or f"Analysis of {file.filename}"

                # Create analysis request
                use_case_request = AnalyzeCodeRequest(
                    source_type=source_type,
                    title=analysis_title,
                    content=content_str,
                    include_endpoints=include_endpoints,
                    include_style_check=include_style_check
                )

                # Execute use case
                response = await self._analyze_code_use_case.execute(use_case_request)

                # Convert to API model
                result_model = AnalysisResultModel(
                    id=response.analysis_result.id,
                    source_type=response.analysis_result.source_type,
                    title=response.analysis_result.title,
                    quality_score=response.analysis_result.quality_score,
                    endpoints_found=len(response.analysis_result.endpoints_found),
                    security_issues=len(response.analysis_result.security_issues),
                    style_violations=len(response.analysis_result.style_violations),
                    processing_time_seconds=response.analysis_result.processing_time_seconds,
                    analysis_timestamp=response.analysis_result.analysis_timestamp
                )

                return AnalysisResponseModel(
                    success=response.success,
                    result=result_model,
                    endpoints_found=response.endpoints_found,
                    style_violations=response.style_violations,
                    processing_time_seconds=response.processing_time_seconds,
                    message=f"File {file.filename} analyzed successfully"
                )

            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="File encoding not supported. Please upload UTF-8 encoded text files."
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"File analysis failed: {str(e)}"
                )

        @self.router.get("/stats", response_model=AnalysisStatsModel)
        async def get_analysis_stats() -> AnalysisStatsModel:
            """Get overall code analysis statistics."""
            try:
                # In a real implementation, this would query the repository
                # For now, return mock statistics
                return AnalysisStatsModel(
                    total_analyses=150,
                    average_quality_score=78.5,
                    total_security_issues=45,
                    total_endpoints_found=320,
                    sources_analyzed=12
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to retrieve statistics: {str(e)}"
                )

        @self.router.get("/results", response_model=List[AnalysisResultModel])
        async def get_recent_results(
            limit: int = Query(10, description="Number of results to return"),
            min_score: Optional[float] = Query(None, description="Minimum quality score")
        ) -> List[AnalysisResultModel]:
            """Get recent analysis results."""
            try:
                # In a real implementation, this would query the repository
                # For now, return mock results
                mock_results = []
                for i in range(min(limit, 5)):
                    result = AnalysisResultModel(
                        id=f"result-{i}",
                        source_type="github",
                        title=f"Analysis Result {i}",
                        quality_score=75.0 + (i * 2),
                        endpoints_found=i * 3,
                        security_issues=max(0, i - 2),
                        style_violations=i,
                        processing_time_seconds=2.5 + (i * 0.5),
                        analysis_timestamp=datetime.now()
                    )

                    # Apply score filter
                    if min_score is None or result.quality_score >= min_score:
                        mock_results.append(result)

                return mock_results

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to retrieve results: {str(e)}"
                )

        @self.router.get("/results/{result_id}")
        async def get_analysis_result(
            result_id: str
        ) -> Dict[str, Any]:
            """Get detailed analysis result by ID."""
            try:
                # In a real implementation, this would query the repository
                # For now, return mock detailed result
                return {
                    "id": result_id,
                    "source_type": "github",
                    "title": "Detailed Analysis Result",
                    "content": "# Sample code for analysis\n\ndef hello_world():\n    print('Hello, World!')",
                    "quality_score": 85.5,
                    "endpoints_found": [
                        {"method": "GET", "path": "/api/health", "line": 5}
                    ],
                    "security_issues": [
                        {
                            "type": "input_validation",
                            "severity": "medium",
                            "description": "Consider adding input validation"
                        }
                    ],
                    "style_violations": [
                        {
                            "type": "line_length",
                            "description": "Line too long",
                            "line": 3
                        }
                    ],
                    "complexity_metrics": {
                        "cyclomatic_complexity": 1,
                        "cognitive_complexity": 1,
                        "maintainability_index": 85.5
                    },
                    "processing_time_seconds": 3.2,
                    "analysis_timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                raise HTTPException(
                    status_code=404,
                    detail=f"Analysis result {result_id} not found"
                )

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "code-analyzer",
                "version": "1.0.0",
                "capabilities": [
                    "endpoint_extraction",
                    "security_scanning",
                    "style_validation",
                    "quality_assessment"
                ]
            }

        @self.router.get("/capabilities")
        async def get_capabilities():
            """Get analysis capabilities and supported features."""
            return {
                "supported_languages": ["python", "javascript", "java", "go"],
                "analysis_features": [
                    "endpoint_extraction",
                    "security_scanning",
                    "style_validation",
                    "complexity_analysis",
                    "quality_assessment"
                ],
                "supported_sources": ["github", "gitlab", "bitbucket", "local"],
                "max_file_size_mb": 10,
                "rate_limit_per_minute": 60
            }


# Factory function to create router
def create_analysis_router(
    analyze_code_use_case: AnalyzeCodeUseCase
) -> APIRouter:
    """Create analysis router with dependencies."""
    router_instance = CodeAnalysisRouter(analyze_code_use_case)
    return router_instance.router
