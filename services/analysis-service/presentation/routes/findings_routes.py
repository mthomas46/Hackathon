"""Findings and Detectors Routes.

Endpoints for retrieving analysis findings and listing available detectors.
"""
from typing import Optional
from fastapi import APIRouter

# Create router
router = APIRouter(tags=["Findings & Detectors"])


@router.get("/findings")
async def get_findings(
    limit: int = 100,
    severity: Optional[str] = None,
    finding_type_filter: Optional[str] = None
):
    """Get analysis findings with optional filtering by severity and type.

    Retrieves findings from document analysis operations with support for
    pagination and filtering by severity levels and finding types for
    targeted issue management and reporting.

    Args:
        limit: Maximum number of findings to return (default: 100)
        severity: Filter by severity level (low, medium, high, critical)
        finding_type_filter: Filter by finding type

    Returns:
        List of findings matching the specified criteria
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    return await analysis_handlers.handle_get_findings(limit, severity, finding_type_filter)


@router.get("/detectors")
async def list_detectors():
    """List available analysis detectors and their capabilities.

    Provides information about all configured detectors including their
    analysis capabilities, supported document types, and configuration
    options for analysis customization.

    Returns:
        List of available detectors with their capabilities
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    return analysis_handlers.handle_list_detectors()

