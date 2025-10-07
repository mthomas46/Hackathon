"""Anomaly Detector - Detect anomalies in metrics and logs."""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class AnomalyType(Enum):
    """Types of anomalies."""
    ERROR_RATE = "error_rate"
    LATENCY_SPIKE = "latency_spike"
    MEMORY_LEAK = "memory_leak"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNUSUAL_PATTERN = "unusual_pattern"


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    type: AnomalyType
    description: str
    severity: str
    timestamp: datetime
    metric_name: str
    current_value: float
    expected_value: float
    deviation: float
    metadata: Dict[str, Any] = None


@dataclass
class AnomalyScore:
    """Anomaly detection result."""
    is_anomaly: bool
    score: float  # 0.0 to 1.0
    severity: str  # low, medium, high, critical
    type: Optional[AnomalyType] = None
    description: str = ""
    error: Optional[str] = None


class AnomalyDetector:
    """Detect anomalies in metrics and patterns."""
    
    def __init__(self):
        """Initialize anomaly detector."""
        self.z_score_threshold = 3.0  # Standard deviations
        self.memory_leak_threshold = 0.5  # % increase per hour
    
    def detect_anomaly(
        self,
        metric_name: str,
        current_value: float,
        baseline: Dict[str, float]
    ) -> AnomalyScore:
        """
        Detect if current value is anomalous.
        
        Args:
            metric_name: Name of metric
            current_value: Current metric value
            baseline: Baseline stats (mean, std_dev, etc.)
        
        Returns:
            AnomalyScore with detection result
        """
        try:
            expected = baseline.get("error_rate", 0.0)
            std_dev = baseline.get("std_dev", 0.01)
            
            # Calculate z-score
            if std_dev > 0:
                z_score = abs(current_value - expected) / std_dev
            else:
                z_score = 0.0
            
            is_anomaly = z_score > self.z_score_threshold
            
            # Determine severity
            if z_score > 5:
                severity = "critical"
            elif z_score > 4:
                severity = "high"
            elif z_score > 3:
                severity = "medium"
            else:
                severity = "low"
            
            # Calculate score (0-1)
            score = min(z_score / 10.0, 1.0)
            
            description = ""
            anomaly_type = None
            
            if is_anomaly:
                anomaly_type = AnomalyType.ERROR_RATE
                description = f"{metric_name} is {z_score:.1f} standard deviations from baseline"
            
            return AnomalyScore(
                is_anomaly=is_anomaly,
                score=score,
                severity=severity,
                type=anomaly_type,
                description=description
            )
        
        except Exception as e:
            return AnomalyScore(
                is_anomaly=False,
                score=0.0,
                severity="low",
                error=str(e)
            )
    
    def detect_trend_anomaly(
        self,
        metric_name: str,
        timestamps: List[datetime],
        values: List[float]
    ) -> AnomalyScore:
        """
        Detect anomalous trends (e.g., memory leaks).
        
        Args:
            metric_name: Metric name
            timestamps: Time points
            values: Metric values
        
        Returns:
            AnomalyScore
        """
        if len(values) < 10:
            return AnomalyScore(
                is_anomaly=False,
                score=0.0,
                severity="low",
                description="Insufficient data"
            )
        
        # Calculate rate of change
        time_span_hours = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
        if time_span_hours == 0:
            return AnomalyScore(is_anomaly=False, score=0.0, severity="low")
        
        value_change_pct = (values[-1] - values[0]) / max(values[0], 1) * 100
        rate_per_hour = value_change_pct / time_span_hours
        
        # Detect memory leak (gradual increase)
        is_leak = (
            rate_per_hour > self.memory_leak_threshold * 100
            and all(values[i] <= values[i+1] for i in range(len(values)-1))
        )
        
        if is_leak:
            return AnomalyScore(
                is_anomaly=True,
                score=min(rate_per_hour / 10.0, 1.0),
                severity="high",
                type=AnomalyType.MEMORY_LEAK,
                description=f"Memory leak detected: {rate_per_hour:.1f}% increase per hour"
            )
        
        return AnomalyScore(is_anomaly=False, score=0.0, severity="low")
    
    def detect_latency_anomaly(
        self,
        current: Dict[str, float],
        baseline: Dict[str, float]
    ) -> AnomalyScore:
        """
        Detect latency spikes.
        
        Args:
            current: Current latency percentiles
            baseline: Baseline latency percentiles
        
        Returns:
            AnomalyScore
        """
        # Check p95 and p99
        p95_increase = (current["p95"] - baseline["p95"]) / baseline["p95"]
        p99_increase = (current["p99"] - baseline["p99"]) / baseline["p99"]
        
        # Spike if p95 or p99 increased by >50%
        is_spike = p95_increase > 0.5 or p99_increase > 0.5
        
        if is_spike:
            max_increase = max(p95_increase, p99_increase)
            severity = "critical" if max_increase > 2.0 else "high"
            
            return AnomalyScore(
                is_anomaly=True,
                score=min(max_increase / 3.0, 1.0),
                severity=severity,
                type=AnomalyType.LATENCY_SPIKE,
                description=f"Latency spike: {max_increase*100:.0f}% increase"
            )
        
        return AnomalyScore(is_anomaly=False, score=0.0, severity="low")
