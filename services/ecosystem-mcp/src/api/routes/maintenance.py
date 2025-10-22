"""
Documentation Maintenance API (Phase 2.2)

API endpoints for documentation maintenance features:
- Staleness detection
- Coverage analysis
- Consistency checking
- Automated refresh
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query as QueryParam
from pydantic import BaseModel, Field

from ...services.maintenance import (
    StalenessDetector,
    CoverageAnalyzer,
    ConsistencyChecker,
    AutomatedRefresher,
    QualityDashboard,
    DependencyTracker,
    VersionComparator
)
from ...services.maintenance.automated_refresher import RefreshStrategy, RefreshTrigger

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class RefreshRequest(BaseModel):
    """Request for documentation refresh."""
    service_name: str = Field(
        ...,
        description="Service to refresh"
    )
    strategy: str = Field(
        default="smart",
        description="Refresh strategy: incremental, full, or smart"
    )
    trigger: str = Field(
        default="manual",
        description="Refresh trigger type"
    )
    force: bool = Field(
        default=False,
        description="Force refresh even if not needed"
    )


class ScheduleRefreshRequest(BaseModel):
    """Request to schedule automatic refresh."""
    service_name: str = Field(
        ...,
        description="Service to refresh"
    )
    schedule: str = Field(
        ...,
        description="Cron-style schedule (e.g., '0 2 * * *')"
    )
    strategy: str = Field(
        default="smart",
        description="Refresh strategy: incremental, full, or smart"
    )


# ============================================================================
# Staleness Detection Endpoints
# ============================================================================

@router.get(
    "/staleness/detect",
    summary="Detect stale documentation",
    description="""
    Detect documentation that has become outdated.
    
    Finds:
    - Documents not updated despite code changes
    - Documents with old timestamps
    - Code-documentation drift
    
    Results categorized by severity: CRITICAL, HIGH, MEDIUM, LOW
    """,
    tags=["Maintenance - Staleness"]
)
async def detect_stale_documents(
    service_name: Optional[str] = QueryParam(None, description="Service filter"),
    timeline_id: Optional[str] = QueryParam(None, description="Timeline filter"),
    limit: int = QueryParam(100, ge=1, le=500, description="Maximum results")
):
    """Detect stale documentation."""
    try:
        detector = StalenessDetector()
        
        result = await detector.detect_stale_documents(
            service_name=service_name,
            timeline_id=UUID(timeline_id) if timeline_id else None,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to detect stale documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.get(
    "/staleness/summary",
    summary="Get staleness summary",
    description="""
    Get a summary of documentation staleness.
    
    Returns:
    - Overall statistics
    - Count by severity
    - Recommendations
    """,
    tags=["Maintenance - Staleness"]
)
async def get_staleness_summary(
    service_name: Optional[str] = QueryParam(None, description="Service filter")
):
    """Get staleness summary."""
    try:
        detector = StalenessDetector()
        result = await detector.get_staleness_summary(service_name=service_name)
        return result
        
    except Exception as e:
        logger.error(f"Failed to get staleness summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Summary failed: {str(e)}")


# ============================================================================
# Coverage Analysis Endpoints
# ============================================================================

@router.get(
    "/coverage/analyze",
    summary="Analyze documentation coverage",
    description="""
    Analyze documentation coverage.
    
    Provides:
    - Overall coverage score
    - Coverage by file type
    - Coverage by service
    - Coverage by module
    - Recommendations
    """,
    tags=["Maintenance - Coverage"]
)
async def analyze_coverage(
    service_name: Optional[str] = QueryParam(None, description="Service filter"),
    repo_path: Optional[str] = QueryParam(None, description="Repository path")
):
    """Analyze documentation coverage."""
    try:
        analyzer = CoverageAnalyzer()
        result = await analyzer.analyze_coverage(
            service_name=service_name,
            repo_path=repo_path
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze coverage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get(
    "/coverage/trend",
    summary="Track coverage trend",
    description="""
    Track documentation coverage trend over time.
    
    Shows how coverage has changed in the past N days.
    """,
    tags=["Maintenance - Coverage"]
)
async def track_coverage_trend(
    service_name: str = QueryParam(..., description="Service to track"),
    days: int = QueryParam(30, ge=1, le=365, description="Days to look back")
):
    """Track coverage trend."""
    try:
        analyzer = CoverageAnalyzer()
        result = await analyzer.track_coverage_trend(
            service_name=service_name,
            days=days
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to track coverage trend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Tracking failed: {str(e)}")


@router.get(
    "/coverage/gaps",
    summary="Identify documentation gaps",
    description="""
    Identify areas lacking documentation.
    
    Finds:
    - Undocumented files
    - Undocumented APIs
    - Undocumented modules
    """,
    tags=["Maintenance - Coverage"]
)
async def identify_gaps(
    service_name: Optional[str] = QueryParam(None, description="Service filter"),
    limit: int = QueryParam(50, ge=1, le=200, description="Maximum gaps")
):
    """Identify documentation gaps."""
    try:
        analyzer = CoverageAnalyzer()
        result = await analyzer.identify_gaps(
            service_name=service_name,
            limit=limit
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to identify gaps: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


# ============================================================================
# Consistency Checking Endpoints
# ============================================================================

@router.get(
    "/consistency/check",
    summary="Check documentation consistency",
    description="""
    Check for inconsistencies in documentation.
    
    Detects:
    - Conflicting information
    - Broken cross-references
    - Terminology inconsistencies
    - Outdated references
    """,
    tags=["Maintenance - Consistency"]
)
async def check_consistency(
    service_name: Optional[str] = QueryParam(None, description="Service filter"),
    limit: int = QueryParam(100, ge=1, le=500, description="Maximum documents")
):
    """Check documentation consistency."""
    try:
        checker = ConsistencyChecker()
        result = await checker.check_consistency(
            service_name=service_name,
            limit=limit
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to check consistency: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Consistency check failed: {str(e)}")


@router.get(
    "/consistency/term/{term}",
    summary="Check term consistency",
    description="""
    Check consistency of a specific term across documentation.
    
    Analyzes:
    - How the term is used
    - Variations and inconsistencies
    - Usage frequency
    - Recommendations for standardization
    """,
    tags=["Maintenance - Consistency"]
)
async def check_term_consistency(
    term: str,
    service_name: Optional[str] = QueryParam(None, description="Service filter")
):
    """Check consistency of a specific term."""
    try:
        checker = ConsistencyChecker()
        result = await checker.check_specific_term(
            term=term,
            service_name=service_name
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to check term consistency: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Term check failed: {str(e)}")


# ============================================================================
# Automated Refresh Endpoints
# ============================================================================

@router.post(
    "/refresh",
    summary="Refresh documentation",
    description="""
    Refresh documentation for a service.
    
    Strategies:
    - **incremental**: Only refresh changed files
    - **full**: Refresh all files
    - **smart**: Intelligently decide based on staleness
    
    Triggers:
    - **manual**: User-initiated
    - **scheduled**: Time-based
    - **event_driven**: Code change detected
    - **staleness_threshold**: Staleness exceeded
    """,
    tags=["Maintenance - Refresh"]
)
async def refresh_documentation(request: RefreshRequest):
    """Refresh documentation."""
    try:
        refresher = AutomatedRefresher()
        
        result = await refresher.refresh_documentation(
            service_name=request.service_name,
            strategy=RefreshStrategy(request.strategy),
            trigger=RefreshTrigger(request.trigger),
            force=request.force
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to refresh documentation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@router.post(
    "/refresh/schedule",
    summary="Schedule automatic refresh",
    description="""
    Schedule automatic documentation refresh.
    
    Example schedule (cron format):
    - `0 2 * * *`: Daily at 2 AM
    - `0 2 * * 0`: Weekly on Sunday at 2 AM
    - `0 2 1 * *`: Monthly on the 1st at 2 AM
    """,
    tags=["Maintenance - Refresh"]
)
async def schedule_refresh(request: ScheduleRefreshRequest):
    """Schedule automatic refresh."""
    try:
        refresher = AutomatedRefresher()
        
        result = await refresher.schedule_refresh(
            service_name=request.service_name,
            schedule=request.schedule,
            strategy=RefreshStrategy(request.strategy)
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to schedule refresh: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scheduling failed: {str(e)}")


@router.get(
    "/refresh/status/{service_name}",
    summary="Get refresh status",
    description="""
    Get refresh status for a service.
    
    Returns:
    - Whether refresh is needed
    - Staleness summary
    - Recommended strategy
    - Last refresh time
    """,
    tags=["Maintenance - Refresh"]
)
async def get_refresh_status(service_name: str):
    """Get refresh status."""
    try:
        refresher = AutomatedRefresher()
        result = await refresher.get_refresh_status(service_name=service_name)
        return result
        
    except Exception as e:
        logger.error(f"Failed to get refresh status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post(
    "/refresh/document/{document_id}",
    summary="Refresh single document",
    description="""
    Refresh a single document.
    
    Useful for:
    - Quick fixes
    - Testing refresh logic
    - Manual document updates
    """,
    tags=["Maintenance - Refresh"]
)
async def refresh_single_document(document_id: str):
    """Refresh a single document."""
    try:
        refresher = AutomatedRefresher()
        
        result = await refresher.refresh_single_document(
            document_id=UUID(document_id)
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to refresh document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


# ============================================================================
# Quality Dashboard Endpoints
# ============================================================================

@router.get(
    "/quality/overview",
    summary="Get quality overview",
    description="""
    Get comprehensive documentation quality overview.
    
    Provides:
    - Overall quality score (0-100)
    - Component scores (freshness, coverage, consistency)
    - Top issues
    - Recommendations
    """,
    tags=["Maintenance - Quality"]
)
async def get_quality_overview(
    service_name: Optional[str] = QueryParam(None, description="Service filter")
):
    """Get quality overview."""
    try:
        dashboard = QualityDashboard()
        result = await dashboard.get_quality_overview(service_name=service_name)
        return result
        
    except Exception as e:
        logger.error(f"Failed to get quality overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Overview failed: {str(e)}")


@router.get(
    "/quality/compare",
    summary="Compare quality across services",
    description="""
    Compare documentation quality across multiple services.
    
    Returns comparative analysis with rankings.
    """,
    tags=["Maintenance - Quality"]
)
async def compare_services_quality(
    service_names: str = QueryParam(..., description="Comma-separated service names")
):
    """Compare quality across services."""
    try:
        dashboard = QualityDashboard()
        services = [s.strip() for s in service_names.split(",")]
        result = await dashboard.compare_services(service_names=services)
        return result
        
    except Exception as e:
        logger.error(f"Failed to compare services: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


# ============================================================================
# Dependency Tracking Endpoints
# ============================================================================

@router.get(
    "/dependencies/graph",
    summary="Build dependency graph",
    description="""
    Build documentation dependency graph.
    
    Shows:
    - Cross-references between documents
    - Hub documents (most referenced)
    - Orphaned documents (no references)
    - Connectivity metrics
    """,
    tags=["Maintenance - Dependencies"]
)
async def build_dependency_graph(
    service_name: Optional[str] = QueryParam(None, description="Service filter")
):
    """Build dependency graph."""
    try:
        tracker = DependencyTracker()
        result = await tracker.build_dependency_graph(service_name=service_name)
        return result
        
    except Exception as e:
        logger.error(f"Failed to build dependency graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Graph building failed: {str(e)}")


@router.get(
    "/dependencies/impact/{document_id}",
    summary="Analyze document impact",
    description="""
    Analyze the impact of changing a document.
    
    Shows which other documents reference this document
    and would be affected by changes.
    """,
    tags=["Maintenance - Dependencies"]
)
async def analyze_document_impact(document_id: str):
    """Analyze document impact."""
    try:
        tracker = DependencyTracker()
        result = await tracker.find_impact(document_id=UUID(document_id))
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to analyze impact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Impact analysis failed: {str(e)}")


@router.get(
    "/dependencies/circular",
    summary="Detect circular dependencies",
    description="""
    Detect circular dependencies in documentation.
    
    Finds cycles where documents reference each other in a loop.
    """,
    tags=["Maintenance - Dependencies"]
)
async def detect_circular_dependencies(
    service_name: Optional[str] = QueryParam(None, description="Service filter")
):
    """Detect circular dependencies."""
    try:
        tracker = DependencyTracker()
        result = await tracker.detect_circular_dependencies(service_name=service_name)
        return result
        
    except Exception as e:
        logger.error(f"Failed to detect circular dependencies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


# ============================================================================
# Version Comparison Endpoints
# ============================================================================

@router.post(
    "/versions/compare",
    summary="Compare document versions",
    description="""
    Compare two versions of a document.
    
    Provides:
    - Unified diff
    - Change statistics
    - Semantic change detection
    """,
    tags=["Maintenance - Versions"]
)
async def compare_document_versions(
    document_id: str = QueryParam(..., description="Document ID"),
    version1_date: str = QueryParam(..., description="First version date (ISO 8601)"),
    version2_date: str = QueryParam(..., description="Second version date (ISO 8601)")
):
    """Compare document versions."""
    try:
        from datetime import datetime
        
        comparator = VersionComparator()
        result = await comparator.compare_versions(
            document_id=UUID(document_id),
            version1_date=datetime.fromisoformat(version1_date),
            version2_date=datetime.fromisoformat(version2_date)
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to compare versions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get(
    "/versions/history/{document_id}",
    summary="Get version history",
    description="""
    Get version history for a document.
    
    Lists all versions with dates, commits, and messages.
    """,
    tags=["Maintenance - Versions"]
)
async def get_version_history(
    document_id: str,
    limit: int = QueryParam(10, ge=1, le=100, description="Maximum versions")
):
    """Get version history."""
    try:
        comparator = VersionComparator()
        result = await comparator.get_version_history(
            document_id=UUID(document_id),
            limit=limit
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get version history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.get(
    "/versions/compare-previous/{document_id}",
    summary="Compare with previous version",
    description="""
    Compare document with its previous version.
    
    Convenient shortcut for comparing with the immediate previous version.
    """,
    tags=["Maintenance - Versions"]
)
async def compare_with_previous(document_id: str):
    """Compare with previous version."""
    try:
        comparator = VersionComparator()
        result = await comparator.compare_with_previous(document_id=UUID(document_id))
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to compare with previous: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

