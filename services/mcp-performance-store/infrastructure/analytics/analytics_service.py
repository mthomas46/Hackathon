"""
Analytics Service for MCP Performance Store.

Provides comprehensive analytics, statistics, and insights on
orchestration performance.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.mcp_performance_store.domain.repositories import PerformanceRepository
from services.mcp_performance_store.infrastructure.analytics.anomaly_detector import AnomalyDetector
from services.mcp_performance_store.infrastructure.analytics.trend_analyzer import TrendAnalyzer


class AnalyticsService:
    """
    Service for advanced analytics on performance data.
    
    Provides trend analysis, anomaly detection, and statistical
    insights on orchestration executions.
    """
    
    def __init__(self, repository: PerformanceRepository):
        """
        Initialize analytics service.
        
        Args:
            repository: Performance repository
        """
        self.repository = repository
        self.anomaly_detector = AnomalyDetector(repository)
        self.trend_analyzer = TrendAnalyzer(repository)
        self.logger = logging.getLogger(__name__)
    
    async def get_execution_stats_by_pattern(
        self,
        pattern_used: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a pattern.
        
        Args:
            pattern_used: Pattern to analyze
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            Dictionary of statistics
        """
        self.logger.info(f"Computing statistics for pattern: {pattern_used}")
        
        # Get raw stats from repository
        stats = await self.repository.get_execution_stats_by_pattern(
            pattern_used,
            start_time,
            end_time
        )
        
        # Get percentiles
        percentiles = await self.repository.get_latency_percentiles(
            pattern_used=pattern_used,
            start_time=start_time,
            end_time=end_time
        )
        
        # Enhance with analytics
        stats["percentiles"] = percentiles
        stats["time_range"] = {
            "start": start_time.isoformat() if start_time else None,
            "end": end_time.isoformat() if end_time else None
        }
        
        return stats
    
    async def get_execution_stats_by_mcp(
        self,
        mcp_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics for an MCP.
        
        Args:
            mcp_id: MCP to analyze
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            Dictionary of statistics
        """
        self.logger.info(f"Computing statistics for MCP: {mcp_id}")
        
        stats = await self.repository.get_execution_stats_by_mcp(
            mcp_id,
            start_time,
            end_time
        )
        
        # Get percentiles
        percentiles = await self.repository.get_latency_percentiles(
            mcp_id=mcp_id,
            start_time=start_time,
            end_time=end_time
        )
        
        stats["percentiles"] = percentiles
        stats["time_range"] = {
            "start": start_time.isoformat() if start_time else None,
            "end": end_time.isoformat() if end_time else None
        }
        
        return stats
    
    async def detect_anomalies(
        self,
        pattern_used: Optional[str] = None,
        threshold_factor: float = 2.0,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Detect anomalous executions.
        
        Args:
            pattern_used: Optional pattern filter
            threshold_factor: Threshold for anomaly detection
            lookback_hours: Hours to look back
        
        Returns:
            Dictionary with anomalies and summary
        """
        self.logger.info(
            f"Detecting anomalies for pattern={pattern_used}, "
            f"threshold={threshold_factor}"
        )
        
        return await self.anomaly_detector.detect_anomalies(
            pattern_used=pattern_used,
            threshold_factor=threshold_factor,
            lookback_hours=lookback_hours
        )
    
    async def get_trend_data(
        self,
        pattern_used: str,
        time_window_minutes: int = 60,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get trend data for a pattern.
        
        Args:
            pattern_used: Pattern to analyze
            time_window_minutes: Size of time buckets
            lookback_hours: Hours to look back
        
        Returns:
            Dictionary with trend data and analysis
        """
        self.logger.info(
            f"Computing trends for pattern={pattern_used}, "
            f"window={time_window_minutes}min"
        )
        
        return await self.trend_analyzer.get_trend_data(
            pattern_used=pattern_used,
            time_window_minutes=time_window_minutes,
            lookback_hours=lookback_hours
        )
    
    async def get_pattern_comparison(
        self,
        patterns: List[str],
        metric: str = "avg_latency",
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Compare multiple patterns.
        
        Args:
            patterns: List of pattern names
            metric: Metric to compare
            lookback_hours: Hours to look back
        
        Returns:
            Comparison data
        """
        self.logger.info(f"Comparing patterns: {patterns} on metric={metric}")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=lookback_hours)
        
        comparison = {
            "patterns": patterns,
            "metric": metric,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "data": {}
        }
        
        for pattern in patterns:
            stats = await self.get_execution_stats_by_pattern(
                pattern,
                start_time,
                end_time
            )
            comparison["data"][pattern] = stats
        
        # Calculate rankings
        if metric == "avg_latency":
            # Lower is better
            sorted_patterns = sorted(
                comparison["data"].items(),
                key=lambda x: x[1].get("avg_latency", float('inf'))
            )
        elif metric == "success_rate":
            # Higher is better
            sorted_patterns = sorted(
                comparison["data"].items(),
                key=lambda x: x[1].get("success_rate", 0),
                reverse=True
            )
        else:
            sorted_patterns = list(comparison["data"].items())
        
        comparison["rankings"] = [p[0] for p in sorted_patterns]
        
        return comparison
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall system health metrics.
        
        Returns:
            System health summary
        """
        self.logger.info("Computing overall system health")
        
        # Get all pattern performances
        patterns = await self.repository.list_pattern_performances(limit=100)
        
        # Calculate overall metrics
        total_executions = sum(p.total_executions for p in patterns)
        avg_success_rate = (
            sum(p.success_rate for p in patterns) / len(patterns)
            if patterns else 0.0
        )
        avg_latency = (
            sum(p.avg_latency_ms for p in patterns) / len(patterns)
            if patterns else 0.0
        )
        
        # Count health statuses
        health_counts = {
            "healthy": sum(1 for p in patterns if p.get_health_status() == "healthy"),
            "warning": sum(1 for p in patterns if p.get_health_status() == "warning"),
            "critical": sum(1 for p in patterns if p.get_health_status() == "critical")
        }
        
        # Determine overall status
        if health_counts["critical"] > 0:
            overall_status = "critical"
        elif health_counts["warning"] > len(patterns) * 0.3:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "total_patterns": len(patterns),
            "total_executions": total_executions,
            "avg_success_rate": round(avg_success_rate, 4),
            "avg_latency_ms": round(avg_latency, 2),
            "health_breakdown": health_counts,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_performance_summary(
        self,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Args:
            lookback_hours: Hours to analyze
        
        Returns:
            Performance summary
        """
        self.logger.info(f"Generating performance summary for last {lookback_hours}h")
        
        # Get overall health
        health = await self.get_overall_health()
        
        # Detect anomalies
        anomalies = await self.detect_anomalies(lookback_hours=lookback_hours)
        
        # Get top patterns by usage
        patterns = await self.repository.list_pattern_performances(limit=10)
        top_patterns = sorted(
            patterns,
            key=lambda p: p.total_executions,
            reverse=True
        )[:5]
        
        return {
            "health": health,
            "anomalies_summary": {
                "total_detected": len(anomalies.get("anomalies", [])),
                "critical_count": len([
                    a for a in anomalies.get("anomalies", [])
                    if a.get("severity") == "critical"
                ])
            },
            "top_patterns": [
                {
                    "name": p.pattern_name,
                    "executions": p.total_executions,
                    "success_rate": p.success_rate,
                    "avg_latency_ms": p.avg_latency_ms
                }
                for p in top_patterns
            ],
            "lookback_hours": lookback_hours,
            "generated_at": datetime.utcnow().isoformat()
        }
