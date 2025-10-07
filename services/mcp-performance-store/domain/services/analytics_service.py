"""Analytics service for performance trend detection and analysis."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, stdev
from collections import defaultdict

from services.mcp_performance_store.domain.entities.orchestration_execution import OrchestrationExecution
from services.mcp_performance_store.domain.entities.pattern_performance import PatternPerformance

logger = logging.getLogger(__name__)


class TrendDirection:
    """Trend direction constants."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


class AnalyticsService:
    """
    Service for analyzing performance trends and patterns.
    
    Provides insights into:
    - Performance trends over time
    - Pattern-specific performance
    - Success/failure patterns
    - Duration trends
    - Token usage trends
    """
    
    def __init__(self, min_samples_for_trend: int = 5):
        """
        Initialize analytics service.
        
        Args:
            min_samples_for_trend: Minimum number of samples required for trend analysis
        """
        self.min_samples_for_trend = min_samples_for_trend
        logger.info(f"AnalyticsService initialized (min_samples={min_samples_for_trend})")
    
    def analyze_orchestration_trends(
        self,
        executions: List[OrchestrationExecution],
        time_window_days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze trends in orchestration executions.
        
        Args:
            executions: List of orchestration executions
            time_window_days: Time window for trend analysis
            
        Returns:
            Dictionary with trend analysis results
        """
        if len(executions) < self.min_samples_for_trend:
            return {
                "status": TrendDirection.INSUFFICIENT_DATA,
                "message": f"Need at least {self.min_samples_for_trend} samples for trend analysis",
                "sample_count": len(executions)
            }
        
        # Sort by timestamp
        sorted_executions = sorted(executions, key=lambda e: e.started_at)
        
        # Calculate basic statistics
        durations = [e.duration_seconds for e in sorted_executions if e.duration_seconds]
        success_rate = len([e for e in sorted_executions if e.status.value == "success"]) / len(sorted_executions)
        
        # Duration trends
        duration_trend = self._calculate_trend(durations)
        
        # Success rate trend (over time windows)
        success_trend = self._calculate_success_rate_trend(sorted_executions)
        
        # Token usage trends
        token_inputs = [e.total_tokens_input for e in sorted_executions if e.total_tokens_input]
        token_outputs = [e.total_tokens_output for e in sorted_executions if e.total_tokens_output]
        
        token_input_trend = self._calculate_trend(token_inputs) if token_inputs else TrendDirection.INSUFFICIENT_DATA
        token_output_trend = self._calculate_trend(token_outputs) if token_outputs else TrendDirection.INSUFFICIENT_DATA
        
        # Calculate percentiles
        duration_percentiles = self._calculate_percentiles(durations) if durations else {}
        
        return {
            "status": "analyzed",
            "sample_count": len(executions),
            "time_window_days": time_window_days,
            "duration": {
                "trend": duration_trend,
                "mean": mean(durations) if durations else 0,
                "stdev": stdev(durations) if len(durations) > 1 else 0,
                "percentiles": duration_percentiles
            },
            "success_rate": {
                "current": success_rate,
                "trend": success_trend
            },
            "tokens": {
                "input_trend": token_input_trend,
                "output_trend": token_output_trend,
                "mean_input": mean(token_inputs) if token_inputs else 0,
                "mean_output": mean(token_outputs) if token_outputs else 0
            },
            "patterns_used": len(set(e.patterns_used for e in sorted_executions if e.patterns_used)),
            "analyzed_at": datetime.now().isoformat()
        }
    
    def analyze_pattern_trends(
        self,
        pattern_performances: List[PatternPerformance],
        pattern_name: str
    ) -> Dict[str, Any]:
        """
        Analyze trends for a specific pattern.
        
        Args:
            pattern_performances: List of pattern performances
            pattern_name: Name of the pattern to analyze
            
        Returns:
            Dictionary with pattern-specific trend analysis
        """
        # Filter for specific pattern
        pattern_data = [p for p in pattern_performances if p.pattern_name == pattern_name]
        
        if len(pattern_data) < self.min_samples_for_trend:
            return {
                "status": TrendDirection.INSUFFICIENT_DATA,
                "pattern_name": pattern_name,
                "message": f"Need at least {self.min_samples_for_trend} samples",
                "sample_count": len(pattern_data)
            }
        
        # Sort by timestamp
        sorted_data = sorted(pattern_data, key=lambda p: p.started_at)
        
        # Duration trends
        durations = [p.duration_seconds for p in sorted_data if p.duration_seconds]
        duration_trend = self._calculate_trend(durations)
        
        # Success rate
        success_rate = len([p for p in sorted_data if p.status.value == "success"]) / len(sorted_data)
        success_trend = self._calculate_success_rate_trend(sorted_data)
        
        # Token usage
        token_inputs = [p.tokens_input for p in sorted_data if p.tokens_input]
        token_outputs = [p.tokens_output for p in sorted_data if p.tokens_output]
        
        # Confidence scores
        confidence_scores = [p.confidence_score for p in sorted_data if p.confidence_score is not None]
        confidence_trend = self._calculate_trend(confidence_scores) if confidence_scores else TrendDirection.INSUFFICIENT_DATA
        
        return {
            "status": "analyzed",
            "pattern_name": pattern_name,
            "sample_count": len(pattern_data),
            "duration": {
                "trend": duration_trend,
                "mean": mean(durations) if durations else 0,
                "stdev": stdev(durations) if len(durations) > 1 else 0,
                "percentiles": self._calculate_percentiles(durations) if durations else {}
            },
            "success_rate": {
                "current": success_rate,
                "trend": success_trend
            },
            "tokens": {
                "input": {
                    "mean": mean(token_inputs) if token_inputs else 0,
                    "trend": self._calculate_trend(token_inputs) if token_inputs else TrendDirection.INSUFFICIENT_DATA
                },
                "output": {
                    "mean": mean(token_outputs) if token_outputs else 0,
                    "trend": self._calculate_trend(token_outputs) if token_outputs else TrendDirection.INSUFFICIENT_DATA
                }
            },
            "confidence": {
                "mean": mean(confidence_scores) if confidence_scores else 0,
                "trend": confidence_trend
            },
            "analyzed_at": datetime.now().isoformat()
        }
    
    def compare_patterns(
        self,
        pattern_performances: List[PatternPerformance]
    ) -> Dict[str, Any]:
        """
        Compare performance across different patterns.
        
        Args:
            pattern_performances: List of pattern performances
            
        Returns:
            Dictionary with pattern comparison results
        """
        # Group by pattern
        by_pattern = defaultdict(list)
        for perf in pattern_performances:
            by_pattern[perf.pattern_name].append(perf)
        
        # Calculate statistics for each pattern
        pattern_stats = {}
        for pattern_name, perfs in by_pattern.items():
            durations = [p.duration_seconds for p in perfs if p.duration_seconds]
            success_rate = len([p for p in perfs if p.status.value == "success"]) / len(perfs)
            token_inputs = [p.tokens_input for p in perfs if p.tokens_input]
            token_outputs = [p.tokens_output for p in perfs if p.tokens_output]
            
            pattern_stats[pattern_name] = {
                "count": len(perfs),
                "success_rate": success_rate,
                "mean_duration": mean(durations) if durations else 0,
                "mean_tokens_input": mean(token_inputs) if token_inputs else 0,
                "mean_tokens_output": mean(token_outputs) if token_outputs else 0,
                "total_cost": sum(p.cost_usd for p in perfs if p.cost_usd)
            }
        
        # Find best and worst performers
        by_duration = sorted(pattern_stats.items(), key=lambda x: x[1]["mean_duration"])
        by_success_rate = sorted(pattern_stats.items(), key=lambda x: x[1]["success_rate"], reverse=True)
        
        return {
            "total_patterns": len(pattern_stats),
            "pattern_statistics": pattern_stats,
            "fastest_patterns": [
                {"pattern": name, "mean_duration": stats["mean_duration"]}
                for name, stats in by_duration[:5]
            ],
            "slowest_patterns": [
                {"pattern": name, "mean_duration": stats["mean_duration"]}
                for name, stats in by_duration[-5:]
            ],
            "most_reliable_patterns": [
                {"pattern": name, "success_rate": stats["success_rate"]}
                for name, stats in by_success_rate[:5]
            ],
            "analyzed_at": datetime.now().isoformat()
        }
    
    def detect_performance_degradation(
        self,
        recent_executions: List[OrchestrationExecution],
        historical_executions: List[OrchestrationExecution],
        threshold_percent: float = 20.0
    ) -> Dict[str, Any]:
        """
        Detect performance degradation by comparing recent vs historical performance.
        
        Args:
            recent_executions: Recent executions (e.g., last 24 hours)
            historical_executions: Historical baseline executions
            threshold_percent: Percentage threshold for degradation alert
            
        Returns:
            Dictionary with degradation detection results
        """
        if not recent_executions or not historical_executions:
            return {
                "status": "insufficient_data",
                "message": "Need both recent and historical data"
            }
        
        # Calculate recent metrics
        recent_durations = [e.duration_seconds for e in recent_executions if e.duration_seconds]
        recent_success_rate = len([e for e in recent_executions if e.status.value == "success"]) / len(recent_executions)
        
        # Calculate historical metrics
        hist_durations = [e.duration_seconds for e in historical_executions if e.duration_seconds]
        hist_success_rate = len([e for e in historical_executions if e.status.value == "success"]) / len(historical_executions)
        
        # Calculate percentage changes
        duration_change = ((mean(recent_durations) - mean(hist_durations)) / mean(hist_durations) * 100) if hist_durations and recent_durations else 0
        success_rate_change = ((recent_success_rate - hist_success_rate) / hist_success_rate * 100) if hist_success_rate > 0 else 0
        
        # Detect degradation
        duration_degraded = duration_change > threshold_percent
        success_degraded = success_rate_change < -threshold_percent
        
        degradation_detected = duration_degraded or success_degraded
        
        return {
            "status": "degradation_detected" if degradation_detected else "healthy",
            "duration": {
                "recent_mean": mean(recent_durations) if recent_durations else 0,
                "historical_mean": mean(hist_durations) if hist_durations else 0,
                "percent_change": duration_change,
                "degraded": duration_degraded
            },
            "success_rate": {
                "recent": recent_success_rate,
                "historical": hist_success_rate,
                "percent_change": success_rate_change,
                "degraded": success_degraded
            },
            "threshold_percent": threshold_percent,
            "recent_sample_count": len(recent_executions),
            "historical_sample_count": len(historical_executions),
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate trend direction using linear regression slope.
        
        Args:
            values: List of numeric values
            
        Returns:
            Trend direction string
        """
        if len(values) < self.min_samples_for_trend:
            return TrendDirection.INSUFFICIENT_DATA
        
        # Simple linear regression to determine trend
        n = len(values)
        x = list(range(n))
        
        # Calculate slope
        x_mean = mean(x)
        y_mean = mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return TrendDirection.STABLE
        
        slope = numerator / denominator
        
        # Determine trend based on slope
        # Normalize by mean to get percentage change
        slope_percent = (slope / y_mean * 100) if y_mean != 0 else 0
        
        if slope_percent > 5:  # More than 5% increase per step
            return TrendDirection.DECLINING  # For duration, increase is bad
        elif slope_percent < -5:  # More than 5% decrease per step
            return TrendDirection.IMPROVING  # For duration, decrease is good
        else:
            return TrendDirection.STABLE
    
    def _calculate_success_rate_trend(
        self,
        executions: List[Any]
    ) -> str:
        """
        Calculate success rate trend over time.
        
        Args:
            executions: List of executions (OrchestrationExecution or PatternPerformance)
            
        Returns:
            Trend direction string
        """
        if len(executions) < self.min_samples_for_trend:
            return TrendDirection.INSUFFICIENT_DATA
        
        # Split into windows and calculate success rate for each
        window_size = len(executions) // 3  # 3 windows
        if window_size < 2:
            return TrendDirection.INSUFFICIENT_DATA
        
        windows = [
            executions[i:i+window_size]
            for i in range(0, len(executions), window_size)
        ]
        
        success_rates = [
            len([e for e in window if e.status.value == "success"]) / len(window)
            for window in windows if len(window) > 0
        ]
        
        if len(success_rates) < 2:
            return TrendDirection.INSUFFICIENT_DATA
        
        # Calculate trend
        first_half_avg = mean(success_rates[:len(success_rates)//2])
        second_half_avg = mean(success_rates[len(success_rates)//2:])
        
        change = (second_half_avg - first_half_avg) / first_half_avg * 100 if first_half_avg > 0 else 0
        
        if change > 5:
            return TrendDirection.IMPROVING
        elif change < -5:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    def _calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """
        Calculate percentiles for a list of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Dictionary with percentile values
        """
        if not values:
            return {}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        def percentile(p: int) -> float:
            k = (n - 1) * p / 100
            f = int(k)
            c = int(k) + 1
            if c >= n:
                return sorted_values[-1]
            if f == c:
                return sorted_values[f]
            d0 = sorted_values[f] * (c - k)
            d1 = sorted_values[c] * (k - f)
            return d0 + d1
        
        return {
            "p50": percentile(50),
            "p75": percentile(75),
            "p90": percentile(90),
            "p95": percentile(95),
            "p99": percentile(99)
        }
