"""Analyze code use case."""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from ...domain.entities.analysis_result import AnalysisResult
from ...domain.services.analysis_processor import create_analysis_result
from ...domain.services.endpoint_extractor import extract_endpoints_from_text
from ...domain.services.style_manager import style_manager


@dataclass
class AnalyzeCodeRequest:
    """Request DTO for code analysis."""
    source_type: str
    title: str
    content: str
    source_refs: Optional[list[Dict[str, Any]]] = None
    repo: Optional[str] = None
    path: Optional[str] = None
    correlation_id: Optional[str] = None
    include_endpoints: bool = True
    include_style_check: bool = True


@dataclass
class AnalyzeCodeResponse:
    """Response DTO for code analysis."""
    success: bool
    analysis_result: AnalysisResult
    endpoints_found: int
    style_violations: int
    processing_time_seconds: float
    message: str


class AnalyzeCodeUseCase:
    """Use case for analyzing code and generating comprehensive reports.

    Orchestrates the complete code analysis process including endpoint extraction,
    style validation, and security checking.
    """

    def __init__(self):
        """Initialize use case with required dependencies."""
        pass  # Dependencies would be injected here

    async def execute(self, request: AnalyzeCodeRequest) -> AnalyzeCodeResponse:
        """Execute the code analysis use case.

        Args:
            request: The analyze code request

        Returns:
            Response containing analysis results and metadata
        """
        import time
        start_time = time.time()

        try:
            # Create initial analysis result
            analysis_result = create_analysis_result(
                source_type=request.source_type,
                title=request.title,
                content=request.content,
                source_refs=request.source_refs or [],
                repo=request.repo,
                path=request.path,
                correlation_id=request.correlation_id
            )

            # Extract endpoints if requested
            endpoints_found = 0
            if request.include_endpoints:
                try:
                    endpoints = extract_endpoints_from_text(request.content)
                    for endpoint in endpoints:
                        analysis_result.add_endpoint(endpoint)
                    endpoints_found = len(endpoints)
                except Exception as e:
                    # Log error but continue with analysis
                    analysis_result.warnings.append(f"Endpoint extraction failed: {str(e)}")

            # Perform style checking if requested
            style_violations = 0
            if request.include_style_check:
                try:
                    style_issues = style_manager.analyze_code_style(request.content)
                    for issue in style_issues:
                        analysis_result.add_style_violation(issue)
                    style_violations = len(style_issues)
                except Exception as e:
                    # Log error but continue with analysis
                    analysis_result.warnings.append(f"Style analysis failed: {str(e)}")

            # Calculate quality score
            analysis_result.calculate_quality_score()

            # Set processing metadata
            processing_time = time.time() - start_time
            analysis_result.set_processing_metadata(
                processing_time=processing_time,
                lines=len(request.content.split('\n')),
                files=1  # Single file analysis for now
            )

            success_message = f"Code analysis completed successfully. Found {endpoints_found} endpoints, {style_violations} style violations."

            return AnalyzeCodeResponse(
                success=True,
                analysis_result=analysis_result,
                endpoints_found=endpoints_found,
                style_violations=style_violations,
                processing_time_seconds=processing_time,
                message=success_message
            )

        except Exception as e:
            processing_time = time.time() - start_time

            # Create failed analysis result
            failed_result = AnalysisResult(
                source_type=request.source_type,
                title=request.title,
                content=request.content
            )
            failed_result.set_processing_metadata(processing_time, 0, 0)

            return AnalyzeCodeResponse(
                success=False,
                analysis_result=failed_result,
                endpoints_found=0,
                style_violations=0,
                processing_time_seconds=processing_time,
                message=f"Code analysis failed: {str(e)}"
            )
