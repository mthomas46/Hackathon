"""
Performance Monitoring API (Option C, Phase 3)

API endpoints for performance monitoring:
- Real-time metrics
- Performance statistics
- Bottleneck detection
- Health scores
- Optimization recommendations
"""

import logging
from typing import Dict, List, Optional
from datetime import timedelta

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from ...services.monitoring.performance_monitor import (
    get_performance_monitor,
    OperationType,
    MetricType
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class PerformanceStatsResponse(BaseModel):
    """Performance statistics response."""
    operation_type: str
    metric_type: str
    count: int
    min: float
    max: float
    avg: float
    median: float
    p95: float
    p99: float
    std_dev: float


class BottleneckResponse(BaseModel):
    """Bottleneck response."""
    operation_type: str
    severity: str
    description: str
    avg_duration_ms: float
    impact_score: float
    recommendation: str
    detected_at: str


class PerformanceSummaryResponse(BaseModel):
    """Performance summary response."""
    timestamp: str
    total_metrics: int
    operations: Dict[str, PerformanceStatsResponse]
    bottlenecks: List[BottleneckResponse]
    health_score: float


class HealthScoreResponse(BaseModel):
    """Health score response."""
    health_score: float
    status: str  # "healthy", "degraded", "critical"
    bottleneck_count: int
    critical_issues: int


# ============================================================================
# Performance Monitoring Endpoints
# ============================================================================

@router.get(
    "/performance/summary",
    response_model=Dict,
    summary="Get performance summary",
    description="Get comprehensive performance summary with all metrics"
)
async def get_performance_summary():
    """
    Get comprehensive performance summary.
    
    Returns:
    - Total metrics collected
    - Statistics for each operation type
    - Detected bottlenecks
    - Overall health score
    """
    try:
        monitor = get_performance_monitor()
        summary = monitor.get_performance_summary()
        
        logger.info(f"📊 Performance summary retrieved: {summary['total_metrics']} metrics")
        
        return summary
    
    except Exception as e:
        logger.error(f"❌ Failed to get performance summary: {e}", exc_info=True)
        return {
            "error": str(e),
            "timestamp": "",
            "total_metrics": 0,
            "operations": {},
            "bottlenecks": [],
            "health_score": 0
        }


@router.get(
    "/performance/stats/{operation_type}",
    response_model=Optional[PerformanceStatsResponse],
    summary="Get operation statistics",
    description="Get detailed statistics for specific operation type"
)
async def get_operation_stats(
    operation_type: str,
    metric_type: str = "duration",
    time_window_minutes: Optional[int] = Query(None, description="Time window in minutes")
):
    """
    Get statistics for specific operation type.
    
    Args:
        operation_type: Type of operation (ingestion, embedding, rag_query, etc.)
        metric_type: Type of metric (duration, throughput, count, etc.)
        time_window_minutes: Optional time window in minutes
    
    Returns:
        Performance statistics or None if no data
    """
    try:
        monitor = get_performance_monitor()
        
        # Parse operation type
        try:
            op_type = OperationType(operation_type)
        except ValueError:
            logger.error(f"❌ Invalid operation type: {operation_type}")
            return None
        
        # Parse metric type
        try:
            m_type = MetricType(metric_type)
        except ValueError:
            logger.error(f"❌ Invalid metric type: {metric_type}")
            return None
        
        # Get stats
        time_window = timedelta(minutes=time_window_minutes) if time_window_minutes else None
        stats = monitor.get_stats(op_type, m_type, time_window)
        
        if not stats:
            logger.info(f"ℹ️  No stats for {operation_type}/{metric_type}")
            return None
        
        logger.info(f"📊 Stats retrieved for {operation_type}: {stats.count} samples")
        
        return PerformanceStatsResponse(**stats.to_dict())
    
    except Exception as e:
        logger.error(f"❌ Failed to get operation stats: {e}", exc_info=True)
        return None


@router.get(
    "/performance/bottlenecks",
    response_model=List[BottleneckResponse],
    summary="Detect bottlenecks",
    description="Detect current performance bottlenecks"
)
async def detect_bottlenecks():
    """
    Detect current performance bottlenecks.
    
    Analyzes recent metrics to identify slow operations and provides
    optimization recommendations.
    
    Returns:
        List of detected bottlenecks sorted by impact
    """
    try:
        monitor = get_performance_monitor()
        bottlenecks = monitor.detect_bottlenecks()
        
        logger.info(f"🔍 Detected {len(bottlenecks)} bottlenecks")
        
        return [BottleneckResponse(**b.to_dict()) for b in bottlenecks]
    
    except Exception as e:
        logger.error(f"❌ Failed to detect bottlenecks: {e}", exc_info=True)
        return []


@router.get(
    "/performance/health",
    response_model=HealthScoreResponse,
    summary="Get health score",
    description="Get overall system health score"
)
async def get_health_score():
    """
    Get overall system health score.
    
    Returns:
    - Health score (0-100)
    - Status (healthy/degraded/critical)
    - Bottleneck counts
    """
    try:
        monitor = get_performance_monitor()
        
        # Detect bottlenecks
        bottlenecks = monitor.detect_bottlenecks()
        
        # Calculate health score
        summary = monitor.get_performance_summary()
        health_score = summary["health_score"]
        
        # Determine status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 50:
            status = "degraded"
        else:
            status = "critical"
        
        # Count critical issues
        critical_issues = sum(
            1 for b in bottlenecks if b.severity == "critical"
        )
        
        logger.info(f"💚 Health score: {health_score:.1f} ({status})")
        
        return HealthScoreResponse(
            health_score=health_score,
            status=status,
            bottleneck_count=len(bottlenecks),
            critical_issues=critical_issues
        )
    
    except Exception as e:
        logger.error(f"❌ Failed to get health score: {e}", exc_info=True)
        return HealthScoreResponse(
            health_score=0,
            status="unknown",
            bottleneck_count=0,
            critical_issues=0
        )


@router.post(
    "/performance/record",
    summary="Record metric",
    description="Record a performance metric (for testing/debugging)"
)
async def record_metric(
    operation_type: str,
    metric_type: str,
    value: float,
    metadata: Optional[Dict] = None
):
    """
    Record a performance metric.
    
    Useful for testing and debugging.
    """
    try:
        monitor = get_performance_monitor()
        
        # Parse types
        op_type = OperationType(operation_type)
        m_type = MetricType(metric_type)
        
        # Record metric
        monitor.record_metric(
            op_type,
            m_type,
            value,
            **(metadata or {})
        )
        
        logger.info(f"✅ Metric recorded: {operation_type}/{metric_type} = {value}")
        
        return {
            "success": True,
            "message": "Metric recorded"
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to record metric: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@router.get(
    "/performance/operations",
    summary="List operation types",
    description="Get list of all operation types being monitored"
)
async def list_operation_types():
    """Get list of all operation types."""
    return {
        "operation_types": [op.value for op in OperationType],
        "metric_types": [mt.value for mt in MetricType]
    }


@router.delete(
    "/performance/clear",
    summary="Clear metrics",
    description="Clear all collected metrics (for testing)"
)
async def clear_metrics():
    """Clear all collected metrics."""
    try:
        monitor = get_performance_monitor()
        monitor.metrics.clear()
        monitor.operation_metrics.clear()
        monitor.bottlenecks.clear()
        
        logger.info("🗑️  All metrics cleared")
        
        return {
            "success": True,
            "message": "All metrics cleared"
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to clear metrics: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

