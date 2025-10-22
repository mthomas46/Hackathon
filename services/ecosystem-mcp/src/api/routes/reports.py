"""
Report Generation API Routes (Phase 5)

Endpoints for generating comprehensive reports with citations.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from enum import Enum

from ...services.timeline import ReportGenerator, ReportFormat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


class ReportFormatParam(str, Enum):
    """Report format parameter."""
    markdown = "markdown"
    html = "html"
    json = "json"


@router.post("/progression")
async def generate_progression_report(
    timeline_id: str = Query(..., description="Timeline ID to analyze"),
    service_name: Optional[str] = Query(None, description="Optional service filter"),
    format: ReportFormatParam = Query(ReportFormatParam.markdown, description="Output format")
):
    """
    Generate progression report showing documentation evolution over time.
    
    Features:
    - Document count by period
    - Growth analysis
    - Velocity metrics
    - Trend identification
    
    Returns:
        Report with progression analysis and recommendations
    """
    try:
        logger.info(f"Generating progression report for timeline {timeline_id}")
        
        generator = ReportGenerator()
        
        # Convert format parameter
        report_format = ReportFormat[format.value.upper()]
        
        result = await generator.generate_progression_report(
            timeline_id=timeline_id,
            service_name=service_name,
            format=report_format
        )
        
        logger.info(f"✅ Progression report generated successfully")
        
        return {
            'success': True,
            'report': result
        }
        
    except Exception as e:
        logger.error(f"Error generating progression report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gaps")
async def generate_gap_report(
    service_name: str = Query(..., description="Service to analyze"),
    include_root_cause: bool = Query(False, description="Include root cause analysis"),
    format: ReportFormatParam = Query(ReportFormatParam.markdown, description="Output format")
):
    """
    Generate gap report identifying missing documentation.
    
    Features:
    - Gap identification
    - Severity classification
    - Root cause analysis (optional)
    - Actionable recommendations
    
    Returns:
        Report with gaps and recommendations
    """
    try:
        logger.info(f"Generating gap report for service {service_name}")
        
        generator = ReportGenerator()
        
        # Convert format parameter
        report_format = ReportFormat[format.value.upper()]
        
        result = await generator.generate_gap_report(
            service_name=service_name,
            include_root_cause=include_root_cause,
            format=report_format
        )
        
        logger.info(f"✅ Gap report generated successfully")
        
        return {
            'success': True,
            'report': result
        }
        
    except Exception as e:
        logger.error(f"Error generating gap report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drift")
async def generate_drift_report(
    service_name: str = Query(..., description="Service to analyze"),
    detection_mode: str = Query("hybrid", description="Detection mode (hybrid/git/content)"),
    format: ReportFormatParam = Query(ReportFormatParam.markdown, description="Output format")
):
    """
    Generate drift report showing code-documentation divergence.
    
    Features:
    - Drift detection
    - Severity classification
    - Confidence indicators
    - Update recommendations
    
    Returns:
        Report with drifts and recommendations
    """
    try:
        logger.info(f"Generating drift report for service {service_name}")
        
        generator = ReportGenerator()
        
        # Convert format parameter
        report_format = ReportFormat[format.value.upper()]
        
        result = await generator.generate_drift_report(
            service_name=service_name,
            detection_mode=detection_mode,
            format=report_format
        )
        
        logger.info(f"✅ Drift report generated successfully")
        
        return {
            'success': True,
            'report': result
        }
        
    except Exception as e:
        logger.error(f"Error generating drift report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def get_available_formats():
    """
    Get list of available report formats.
    
    Returns:
        List of supported formats with descriptions
    """
    return {
        'success': True,
        'formats': [
            {
                'value': 'markdown',
                'label': 'Markdown',
                'description': 'Human-readable Markdown format',
                'extension': '.md'
            },
            {
                'value': 'html',
                'label': 'HTML',
                'description': 'Web-viewable HTML format',
                'extension': '.html'
            },
            {
                'value': 'json',
                'label': 'JSON',
                'description': 'Machine-readable JSON format',
                'extension': '.json'
            }
        ]
    }

