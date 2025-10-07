"""Predictive Maintenance - Predict failures before they happen."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class Prediction:
    """Failure prediction result."""
    service: str
    metric: str
    likely_failure: bool
    confidence: float
    estimated_time_to_failure: Optional[timedelta] = None
    reason: str = ""


@dataclass
class TrendAnalysis:
    """Trend analysis result."""
    metric_name: str
    direction: str  # increasing, decreasing, stable
    slope: float
    confidence: float


@dataclass
class MaintenanceAction:
    """Recommended maintenance action."""
    description: str
    priority: str  # low, medium, high, critical
    estimated_impact: str
    steps: List[str]


class PredictiveMaintenance:
    """Predict failures and recommend preventive actions."""
    
    def __init__(self):
        """Initialize predictive maintenance."""
        self.failure_threshold = 0.7  # Confidence threshold
        self.trend_threshold = 0.1  # % change per time unit
    
    def predict_failure(
        self,
        service: str,
        metric: str,
        timestamps: List[datetime],
        values: List[float]
    ) -> Prediction:
        """
        Predict if service will fail.
        
        Args:
            service: Service name
            metric: Metric name
            timestamps: Time points
            values: Metric values
        
        Returns:
            Prediction result
        """
        if len(values) < 3:
            return Prediction(
                service=service,
                metric=metric,
                likely_failure=False,
                confidence=0.0,
                reason="Insufficient data"
            )
        
        # Analyze trend
        trend = self.analyze_trend(metric, timestamps, values)
        
        # Check if trending towards failure
        if trend.direction == "increasing" and trend.slope > self.trend_threshold:
            # Estimate time to failure
            current_value = values[-1]
            failure_threshold = 1.0  # Assume 100% is failure
            
            if trend.slope > 0:
                time_to_failure_hours = (failure_threshold - current_value) / (trend.slope / 24)
                time_to_failure = timedelta(hours=max(time_to_failure_hours, 0))
            else:
                time_to_failure = None
            
            confidence = min(trend.slope * 10, 1.0)
            
            return Prediction(
                service=service,
                metric=metric,
                likely_failure=True,
                confidence=confidence,
                estimated_time_to_failure=time_to_failure,
                reason=f"Increasing trend detected: {trend.slope:.3f} per day"
            )
        
        return Prediction(
            service=service,
            metric=metric,
            likely_failure=False,
            confidence=0.3,
            reason="Metrics are stable"
        )
    
    def analyze_trend(
        self,
        metric_name: str,
        timestamps: List[datetime],
        values: List[float]
    ) -> TrendAnalysis:
        """
        Analyze metric trend.
        
        Args:
            metric_name: Metric name
            timestamps: Time points
            values: Metric values
        
        Returns:
            TrendAnalysis
        """
        if len(values) < 2:
            return TrendAnalysis(
                metric_name=metric_name,
                direction="stable",
                slope=0.0,
                confidence=0.0
            )
        
        # Simple linear regression
        n = len(values)
        
        # Convert timestamps to hours
        time_hours = [(t - timestamps[0]).total_seconds() / 3600 for t in timestamps]
        
        # Calculate slope
        x_mean = sum(time_hours) / n
        y_mean = sum(values) / n
        
        numerator = sum((time_hours[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((time_hours[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0.0
        else:
            slope = numerator / denominator
        
        # Determine direction
        if slope > self.trend_threshold:
            direction = "increasing"
        elif slope < -self.trend_threshold:
            direction = "decreasing"
        else:
            direction = "stable"
        
        # Calculate confidence (R-squared approximation)
        if denominator == 0:
            confidence = 0.0
        else:
            predictions = [y_mean + slope * (time_hours[i] - x_mean) for i in range(n)]
            ss_res = sum((values[i] - predictions[i]) ** 2 for i in range(n))
            ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
            confidence = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return TrendAnalysis(
            metric_name=metric_name,
            direction=direction,
            slope=slope,
            confidence=max(0.0, min(confidence, 1.0))
        )
    
    def recommend_actions(self, prediction: Prediction) -> List[MaintenanceAction]:
        """
        Recommend maintenance actions.
        
        Args:
            prediction: Failure prediction
        
        Returns:
            List of recommended actions
        """
        actions = []
        
        if not prediction.likely_failure:
            return actions
        
        metric = prediction.metric.lower()
        
        if 'memory' in metric:
            actions.append(MaintenanceAction(
                description="Increase memory allocation",
                priority="high",
                estimated_impact="Prevents out-of-memory errors",
                steps=[
                    "Review current memory usage",
                    "Identify memory-intensive processes",
                    "Scale up memory resources",
                    "Monitor for improvement"
                ]
            ))
            
            actions.append(MaintenanceAction(
                description="Investigate memory leaks",
                priority="high",
                estimated_impact="Addresses root cause",
                steps=[
                    "Profile application memory usage",
                    "Check for unclosed connections",
                    "Review object lifecycle management",
                    "Deploy fixes"
                ]
            ))
        
        elif 'error' in metric:
            actions.append(MaintenanceAction(
                description="Review and fix error sources",
                priority="high",
                estimated_impact="Reduces error rate",
                steps=[
                    "Analyze error logs",
                    "Identify root causes",
                    "Deploy fixes",
                    "Monitor error rate"
                ]
            ))
        
        elif 'latency' in metric or 'response' in metric:
            actions.append(MaintenanceAction(
                description="Optimize performance",
                priority="medium",
                estimated_impact="Improves response times",
                steps=[
                    "Profile slow operations",
                    "Add caching where appropriate",
                    "Optimize database queries",
                    "Consider horizontal scaling"
                ]
            ))
        
        else:
            actions.append(MaintenanceAction(
                description=f"Monitor {prediction.metric}",
                priority="medium",
                estimated_impact="Prevents service degradation",
                steps=[
                    "Set up alerts",
                    "Review service health",
                    "Plan capacity increase",
                    "Schedule maintenance window"
                ]
            ))
        
        return actions
