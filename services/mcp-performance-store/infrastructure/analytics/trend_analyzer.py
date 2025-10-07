"""
Trend Analyzer for MCP Performance Store.

Analyzes trends in orchestration performance over time.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from services.mcp_performance_store.domain.repositories import PerformanceRepository


class TrendAnalyzer:
    """
    Service for analyzing performance trends.
    
    Provides time-series analysis and trend detection.
    """
    
    def __init__(self, repository: PerformanceRepository):
        """
        Initialize trend analyzer.
        
        Args:
            repository: Performance repository
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    async def get_trend_data(
        self,
        pattern_used: str,
        time_window_minutes: int = 60,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get time-series trend data for a pattern.
        
        Args:
            pattern_used: Pattern to analyze
            time_window_minutes: Size of time buckets (minutes)
            lookback_hours: Hours to look back
        
        Returns:
            Dictionary with trend data and analysis
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=lookback_hours)
        
        self.logger.info(
            f"Analyzing trends for {pattern_used} from {start_time} to {end_time}"
        )
        
        # Get trend data from repository
        trend_data = await self.repository.get_trend_data(
            pattern_used,
            time_window_minutes
        )
        
        if not trend_data:
            # Fallback: compute from raw executions
            trend_data = await self._compute_trend_data(
                pattern_used,
                start_time,
                end_time,
                time_window_minutes
            )
        
        # Analyze trends
        trend_analysis = self._analyze_trends(trend_data)
        
        return {
            "pattern": pattern_used,
            "time_window_minutes": time_window_minutes,
            "lookback_hours": lookback_hours,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "data_points": trend_data,
            "analysis": trend_analysis
        }
    
    async def _compute_trend_data(
        self,
        pattern_used: str,
        start_time: datetime,
        end_time: datetime,
        window_minutes: int
    ) -> List[Dict[str, Any]]:
        """Compute trend data from raw executions."""
        # Get executions
        executions = await self.repository.list_executions(
            pattern_used=pattern_used,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        if not executions:
            return []
        
        # Group into time buckets
        bucket_size = timedelta(minutes=window_minutes)
        buckets = defaultdict(list)
        
        for execution in executions:
            # Calculate bucket timestamp
            bucket_time = execution.timestamp - timedelta(
                minutes=execution.timestamp.minute % window_minutes,
                seconds=execution.timestamp.second,
                microseconds=execution.timestamp.microsecond
            )
            buckets[bucket_time].append(execution)
        
        # Compute metrics for each bucket
        trend_data = []
        for bucket_time in sorted(buckets.keys()):
            bucket_executions = buckets[bucket_time]
            
            total = len(bucket_executions)
            successful = sum(1 for e in bucket_executions if e.success)
            
            metrics = {
                "timestamp": bucket_time.isoformat(),
                "total_executions": total,
                "success_count": successful,
                "failure_count": total - successful,
                "success_rate": successful / total if total > 0 else 0,
                "avg_latency_ms": (
                    sum(e.latency_ms for e in bucket_executions) / total
                    if total > 0 else 0
                ),
                "avg_accuracy": (
                    sum(e.accuracy_score for e in bucket_executions) / total
                    if total > 0 else 0
                ),
                "avg_confidence": (
                    sum(e.confidence for e in bucket_executions) / total
                    if total > 0 else 0
                ),
                "total_cost_cents": sum(e.cost_cents for e in bucket_executions),
                "hallucination_count": sum(
                    1 for e in bucket_executions if e.hallucination_detected
                )
            }
            
            trend_data.append(metrics)
        
        return trend_data
    
    def _analyze_trends(self, trend_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze trend data to detect patterns.
        
        Returns:
            Dictionary with trend analysis
        """
        if len(trend_data) < 3:
            return {
                "trend_direction": "unknown",
                "confidence": 0.0,
                "summary": "Insufficient data for trend analysis"
            }
        
        # Extract key metrics over time
        latencies = [d["avg_latency_ms"] for d in trend_data]
        success_rates = [d["success_rate"] for d in trend_data]
        
        # Simple linear trend detection
        latency_trend = self._detect_simple_trend(latencies)
        success_trend = self._detect_simple_trend(success_rates)
        
        # Overall assessment
        if latency_trend == "increasing" or success_trend == "decreasing":
            overall_direction = "degrading"
        elif latency_trend == "decreasing" and success_trend == "increasing":
            overall_direction = "improving"
        elif latency_trend == "stable" and success_trend == "stable":
            overall_direction = "stable"
        else:
            overall_direction = "mixed"
        
        # Calculate volatility
        latency_volatility = self._calculate_volatility(latencies)
        
        return {
            "trend_direction": overall_direction,
            "latency_trend": latency_trend,
            "success_trend": success_trend,
            "volatility": {
                "latency": latency_volatility,
                "assessment": self._assess_volatility(latency_volatility)
            },
            "summary": self._generate_trend_summary(
                overall_direction,
                latency_trend,
                success_trend,
                latency_volatility
            ),
            "recommendations": self._generate_recommendations(
                overall_direction,
                latency_trend,
                success_trend
            )
        }
    
    def _detect_simple_trend(self, values: List[float]) -> str:
        """Detect simple trend in values."""
        if len(values) < 3:
            return "unknown"
        
        # Compare first half to second half
        mid_point = len(values) // 2
        first_half_avg = sum(values[:mid_point]) / mid_point
        second_half_avg = sum(values[mid_point:]) / (len(values) - mid_point)
        
        # Threshold for detecting change (5%)
        threshold = first_half_avg * 0.05
        
        if second_half_avg > first_half_avg + threshold:
            return "increasing"
        elif second_half_avg < first_half_avg - threshold:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (coefficient of variation)."""
        if not values or len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0
        
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Coefficient of variation
        cv = (std_dev / mean) * 100
        return round(cv, 2)
    
    def _assess_volatility(self, volatility: float) -> str:
        """Assess volatility level."""
        if volatility < 10:
            return "low"
        elif volatility < 25:
            return "moderate"
        elif volatility < 50:
            return "high"
        else:
            return "very_high"
    
    def _generate_trend_summary(
        self,
        overall: str,
        latency: str,
        success: str,
        volatility: float
    ) -> str:
        """Generate human-readable trend summary."""
        summaries = {
            "improving": "Performance is improving over time.",
            "degrading": "Performance is degrading. Immediate attention recommended.",
            "stable": "Performance is stable.",
            "mixed": "Performance shows mixed trends."
        }
        
        base_summary = summaries.get(overall, "Trend analysis inconclusive.")
        
        details = []
        if latency == "increasing":
            details.append("Latency is increasing.")
        elif latency == "decreasing":
            details.append("Latency is decreasing.")
        
        if success == "decreasing":
            details.append("Success rate is declining.")
        elif success == "increasing":
            details.append("Success rate is improving.")
        
        if volatility > 25:
            details.append(f"High volatility detected ({volatility}%).")
        
        if details:
            return f"{base_summary} {' '.join(details)}"
        return base_summary
    
    def _generate_recommendations(
        self,
        overall: str,
        latency: str,
        success: str
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if overall == "degrading":
            recommendations.append("Investigate recent changes to the pattern or MCP.")
            recommendations.append("Review error logs for common failure patterns.")
        
        if latency == "increasing":
            recommendations.append("Consider optimizing pattern execution.")
            recommendations.append("Check for resource constraints.")
        
        if success == "decreasing":
            recommendations.append("Review recent query patterns for complexity changes.")
            recommendations.append("Verify MCP data quality and coverage.")
        
        if overall == "stable":
            recommendations.append("Continue monitoring. Performance is within normal range.")
        
        if not recommendations:
            recommendations.append("No immediate action required.")
        
        return recommendations
