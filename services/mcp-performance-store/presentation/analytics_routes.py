"""
Analytics routes for MCP Performance Store.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime

from services.mcp_performance_store.infrastructure.analytics import AnalyticsService
from services.mcp_performance_store.presentation.dependencies import get_repository


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


async def get_analytics_service() -> AnalyticsService:
    """Get analytics service."""
    repository = await get_repository()
    return AnalyticsService(repository)


@router.get(
    "/patterns/{pattern_name}/stats",
    summary="Get pattern statistics",
    description="Get comprehensive statistics for a pattern"
)
async def get_pattern_stats(
    pattern_name: str,
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> dict:
    """Get pattern statistics."""
    try:
        stats = await analytics.get_execution_stats_by_pattern(
            pattern_name,
            start_time,
            end_time
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get(
    "/mcps/{mcp_id}/stats",
    summary="Get MCP statistics",
    description="Get comprehensive statistics for an MCP"
)
async def get_mcp_stats(
    mcp_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> dict:
    """Get MCP statistics."""
    try:
        stats = await analytics.get_execution_stats_by_mcp(
            mcp_id,
            start_time,
            end_time
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get(
    "/anomalies",
    summary="Detect anomalies",
    description="Detect anomalous executions"
)
async def detect_anomalies(
    pattern: Optional[str] = Query(None, description="Filter by pattern"),
    threshold_factor: float = Query(2.0, ge=1.0, le=5.0, description="Threshold factor"),
    lookback_hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> dict:
    """Detect anomalies."""
    try:
        anomalies = await analytics.detect_anomalies(
            pattern_used=pattern,
            threshold_factor=threshold_factor,
            lookback_hours=lookback_hours
        )
        return anomalies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect anomalies: {str(e)}")


@router.get(
    "/trends/{pattern_name}",
    summary="Get trend data",
    description="Get time-series trend data for a pattern"
)
async def get_trend_data(
    pattern_name: str,
    time_window_minutes: int = Query(60, ge=5, le=1440, description="Time window size"),
    lookback_hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> dict:
    """Get trend data."""
    try:
        trends = await analytics.get_trend_data(
            pattern_used=pattern_name,
            time_window_minutes=time_window_minutes,
            lookback_hours=lookback_hours
        )
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")


@router.get(
    "/comparison",
    summary="Compare patterns",
    description="Compare multiple patterns on a specific metric"
)
async def compare_patterns(
    patterns: List[str] = Query(..., description="Pattern names to compare"),
    metric: str = Query("avg_latency", description="Metric to compare"),
    lookback_hours: int = Query(24, ge=1, le=168),
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> dict:
    """Compare patterns."""
    try:
        comparison = await analytics.get_pattern_comparison(
            patterns=patterns,
            metric=metric,
            lookback_hours=lookback_hours
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare patterns: {str(e)}")


@router.get(
    "/health",
    summary="Get overall health",
    description="Get overall system health metrics"
)
async def get_overall_health(
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> dict:
    """Get overall health."""
    try:
        health = await analytics.get_overall_health()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health: {str(e)}")


@router.get(
    "/summary",
    summary="Get performance summary",
    description="Get comprehensive performance summary"
)
async def get_performance_summary(
    lookback_hours: int = Query(24, ge=1, le=168),
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> dict:
    """Get performance summary."""
    try:
        summary = await analytics.get_performance_summary(
            lookback_hours=lookback_hours
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")
