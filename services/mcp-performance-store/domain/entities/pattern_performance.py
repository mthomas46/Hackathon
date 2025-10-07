"""
Pattern Performance Entity.

Represents aggregated performance metrics for an LLM pattern across multiple executions.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class TrendDirection(str, Enum):
    """Enum for trend direction."""
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    UNKNOWN = "unknown"


class TimeWindowMetrics(BaseModel):
    """Metrics for a specific time window."""
    total_executions: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_latency_ms: float = Field(default=0.0, ge=0.0)
    avg_cost_cents: float = Field(default=0.0, ge=0.0)
    avg_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class PatternPerformance(BaseModel):
    """
    Entity representing aggregated performance metrics for an LLM pattern.
    
    Tracks performance across multiple time windows and provides
    trend analysis and anomaly detection.
    """
    
    # Identity
    pattern_id: str = Field(..., description="Unique identifier for the pattern")
    pattern_name: str = Field(..., description="Name of the LLM pattern")
    version: str = Field(..., description="Version of the pattern")
    
    # Overall Aggregated Metrics
    total_executions: int = Field(default=0, ge=0, description="Total number of executions")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall success rate")
    avg_latency_ms: float = Field(default=0.0, ge=0.0, description="Average latency in milliseconds")
    p50_latency_ms: float = Field(default=0.0, ge=0.0, description="P50 (median) latency")
    p95_latency_ms: float = Field(default=0.0, ge=0.0, description="P95 latency")
    p99_latency_ms: float = Field(default=0.0, ge=0.0, description="P99 latency")
    avg_cost_cents: float = Field(default=0.0, ge=0.0, description="Average cost per execution")
    avg_accuracy: float = Field(default=0.0, ge=0.0, le=1.0, description="Average accuracy score")
    avg_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Average confidence score")
    
    # Time Windows
    last_hour: TimeWindowMetrics = Field(default_factory=TimeWindowMetrics)
    last_day: TimeWindowMetrics = Field(default_factory=TimeWindowMetrics)
    last_week: TimeWindowMetrics = Field(default_factory=TimeWindowMetrics)
    last_month: TimeWindowMetrics = Field(default_factory=TimeWindowMetrics)
    
    # Trends
    trend_direction: TrendDirection = Field(
        default=TrendDirection.UNKNOWN,
        description="Overall trend direction"
    )
    anomalies_detected: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of detected anomalies"
    )
    
    # Timestamps
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.dict()
    
    def calculate_overall_score(self) -> float:
        """
        Calculate overall performance score (0-1).
        
        Combines success rate, accuracy, and efficiency metrics.
        """
        # Success and accuracy are most important
        quality_score = (self.success_rate * 0.4) + (self.avg_accuracy * 0.3)
        
        # Confidence and cost efficiency
        confidence_score = self.avg_confidence * 0.2
        
        # Latency efficiency (inverse relationship)
        # Assume 1000ms is baseline, lower is better
        latency_score = max(0.0, min(0.1, 0.1 * (1000.0 / max(1.0, self.avg_latency_ms))))
        
        overall_score = quality_score + confidence_score + latency_score
        
        return max(0.0, min(1.0, overall_score))
    
    def update_trend(self, previous_score: Optional[float] = None) -> TrendDirection:
        """
        Update trend direction based on recent performance.
        
        Args:
            previous_score: Previous overall score for comparison
        
        Returns:
            Updated trend direction
        """
        if previous_score is None:
            return TrendDirection.UNKNOWN
        
        current_score = self.calculate_overall_score()
        diff = current_score - previous_score
        
        # Define thresholds for trend detection
        IMPROVEMENT_THRESHOLD = 0.05
        DEGRADATION_THRESHOLD = -0.05
        
        if diff > IMPROVEMENT_THRESHOLD:
            self.trend_direction = TrendDirection.IMPROVING
        elif diff < DEGRADATION_THRESHOLD:
            self.trend_direction = TrendDirection.DEGRADING
        else:
            self.trend_direction = TrendDirection.STABLE
        
        return self.trend_direction
    
    def detect_latency_anomaly(self, threshold_ms: float = 5000.0) -> bool:
        """
        Detect if current latency is anomalous.
        
        Args:
            threshold_ms: Maximum acceptable latency
        
        Returns:
            True if anomaly detected
        """
        return self.avg_latency_ms > threshold_ms or self.p95_latency_ms > (threshold_ms * 1.5)
    
    def detect_accuracy_anomaly(self, threshold: float = 0.5) -> bool:
        """
        Detect if current accuracy is anomalously low.
        
        Args:
            threshold: Minimum acceptable accuracy
        
        Returns:
            True if anomaly detected
        """
        return self.avg_accuracy < threshold
    
    def add_anomaly(self, anomaly_type: str, details: Dict[str, Any]):
        """
        Add a detected anomaly.
        
        Args:
            anomaly_type: Type of anomaly (latency, accuracy, etc.)
            details: Details about the anomaly
        """
        anomaly = {
            "type": anomaly_type,
            "detected_at": datetime.utcnow().isoformat(),
            "details": details
        }
        self.anomalies_detected.append(anomaly)
        
        # Keep only last 10 anomalies
        if len(self.anomalies_detected) > 10:
            self.anomalies_detected = self.anomalies_detected[-10:]
    
    def get_health_status(self) -> str:
        """
        Get health status based on current metrics.
        
        Returns:
            Health status: "healthy", "warning", or "critical"
        """
        score = self.calculate_overall_score()
        
        if score >= 0.8:
            return "healthy"
        elif score >= 0.6:
            return "warning"
        else:
            return "critical"
    
    def __repr__(self) -> str:
        return (
            f"PatternPerformance(pattern_id={self.pattern_id}, "
            f"name={self.pattern_name}, executions={self.total_executions}, "
            f"success_rate={self.success_rate:.2f}, "
            f"avg_latency={self.avg_latency_ms:.0f}ms)"
        )
