"""
Documentation Analysis API (Phase 3)

API endpoints for advanced analysis features:
- Gap analysis with root cause
- Drift detection
- Export functionality
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query as QueryParam
from pydantic import BaseModel, Field

from ...services.timeline import GapAnalyzer, DriftDetector
from ...services.maintenance import ExportService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ExportRequest(BaseModel):
    """Request for documentation export."""
    export_format: str = Field(
        ...,
        description="Export format: markdown, html, json, pdf, docx"
    )
    service_name: Optional[str] = Field(
        None,
        description="Service to export (optional)"
    )
    timeline_id: Optional[str] = Field(
        None,
        description="Timeline to export (optional)"
    )
    output_path: Optional[str] = Field(
        None,
        description="Output directory path"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include metadata in export"
    )


# ============================================================================
# Gap Analysis Endpoints
# ============================================================================

@router.get(
    "/gaps/analyze",
    summary="Analyze documentation gaps",
    description="""
    Analyze documentation gaps with root cause analysis.
    
    Detects:
    - Missing documentation
    - Topic gaps
    - Coverage gaps
    - Temporal gaps (if timeline provided)
    
    Results categorized by severity: CRITICAL, HIGH, MEDIUM, LOW
    """,
    tags=["Analysis - Gaps"]
)
async def analyze_gaps(
    service_name: Optional[str] = QueryParam(None, description="Service filter"),
    timeline_id: Optional[str] = QueryParam(None, description="Timeline filter"),
    include_root_cause: bool = QueryParam(True, description="Perform root cause analysis")
):
    """Analyze documentation gaps."""
    try:
        analyzer = GapAnalyzer()
        
        result = await analyzer.analyze_gaps(
            service_name=service_name,
            timeline_id=UUID(timeline_id) if timeline_id else None,
            include_root_cause=include_root_cause
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze gaps: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


@router.get(
    "/gaps/trend",
    summary="Track gap trends",
    description="""
    Track how documentation gaps have changed over time.
    
    Shows trends for a specific service over a specified number of days.
    """,
    tags=["Analysis - Gaps"]
)
async def track_gap_trend(
    service_name: str = QueryParam(..., description="Service to track"),
    days: int = QueryParam(30, ge=1, le=365, description="Days to look back")
):
    """Track gap trends."""
    try:
        analyzer = GapAnalyzer()
        result = await analyzer.get_gap_trend(service_name=service_name, days=days)
        return result
        
    except Exception as e:
        logger.error(f"Failed to track gap trend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trend tracking failed: {str(e)}")


# ============================================================================
# Drift Detection Endpoints
# ============================================================================

@router.get(
    "/drift/detect",
    summary="Detect code-documentation drift",
    description="""
    Detect when code and documentation have drifted apart.
    
    Detection modes:
    - **hybrid**: Use both git and content analysis (recommended)
    - **git_only**: Only use git history (requires git integration)
    - **content_only**: Only use content analysis (fallback mode)
    
    Detects:
    - Code updated after documentation
    - Outdated content markers
    - API/contract changes
    """,
    tags=["Analysis - Drift"]
)
async def detect_drift(
    service_name: Optional[str] = QueryParam(None, description="Service filter"),
    timeline_id: Optional[str] = QueryParam(None, description="Timeline filter"),
    detection_mode: str = QueryParam(
        "hybrid",
        description="Detection mode: hybrid, git_only, or content_only"
    )
):
    """Detect code-documentation drift."""
    try:
        detector = DriftDetector()
        
        result = await detector.detect_drift(
            service_name=service_name,
            timeline_id=UUID(timeline_id) if timeline_id else None,
            detection_mode=detection_mode
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to detect drift: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Drift detection failed: {str(e)}")


@router.get(
    "/drift/summary/{service_name}",
    summary="Get drift summary",
    description="""
    Get a summary of drift for a specific service.
    
    Provides:
    - Total drifts
    - Drifts by severity
    - Top recommendations
    - Detection confidence
    """,
    tags=["Analysis - Drift"]
)
async def get_drift_summary(service_name: str):
    """Get drift summary."""
    try:
        detector = DriftDetector()
        result = await detector.get_drift_summary(service_name=service_name)
        return result
        
    except Exception as e:
        logger.error(f"Failed to get drift summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Summary failed: {str(e)}")


# ============================================================================
# Export Endpoints
# ============================================================================

@router.post(
    "/export",
    summary="Export documentation",
    description="""
    Export documentation in various formats.
    
    Supported formats:
    - **markdown**: Standard Markdown files
    - **html**: HTML with CSS styling
    - **json**: Structured JSON export
    - **pdf**: PDF format (requires additional libraries)
    - **docx**: Microsoft Word format (requires additional libraries)
    
    Options:
    - Filter by service or timeline
    - Include/exclude metadata
    - Specify output path
    """,
    tags=["Analysis - Export"]
)
async def export_documentation(request: ExportRequest):
    """Export documentation."""
    try:
        export_service = ExportService()
        
        result = await export_service.export_documentation(
            export_format=request.export_format,
            service_name=request.service_name,
            timeline_id=UUID(request.timeline_id) if request.timeline_id else None,
            output_path=request.output_path,
            include_metadata=request.include_metadata
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to export documentation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post(
    "/export/github-pages/{service_name}",
    summary="Export for GitHub Pages",
    description="""
    Export documentation optimized for GitHub Pages.
    
    Generates:
    - HTML files with styling
    - Index page
    - Jekyll configuration (_config.yml)
    - Setup instructions
    
    The exported files can be committed to a repository
    and hosted on GitHub Pages.
    """,
    tags=["Analysis - Export"]
)
async def export_github_pages(
    service_name: str,
    output_path: str = QueryParam("./docs", description="Output directory")
):
    """Export for GitHub Pages."""
    try:
        export_service = ExportService()
        result = await export_service.export_github_pages(
            service_name=service_name,
            output_path=output_path
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to export for GitHub Pages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"GitHub Pages export failed: {str(e)}")
