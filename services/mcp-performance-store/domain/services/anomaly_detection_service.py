"""Anomaly detection service for identifying unusual performance patterns."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, stdev
from collections import defaultdict

from services.mcp_performance_store.domain.entities.orchestration_execution import OrchestrationExecution
from services.mcp_performance_store.domain.entities.pattern_performance import PatternPerformance

logger = logging.getLogger(__name__)


class AnomalyType:
    """Types of anomalies that can be detected."""
    DURATION_SPIKE = "duration_spike"
    DURATION_DROP = "duration_drop"
    FAILURE_SPIKE = "failure_spike"
    TOKEN_SPIKE = "token_spike"
    COST_SPIKE = "cost_spike"
    CONFIDENCE_DROP = "confidence_drop"


class AnomalySeverity:
    """Severity levels for anomalies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Anomaly:
    """Represents a detected anomaly."""
    
    def __init__(
        self,
        anomaly_type: str,
        severity: str,
        description: str,
        value: float,
        expected_value: float,
        deviation_percent: float,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.anomaly_type = anomaly_type
        self.severity = severity
        self.description = description
        self.value = value
        self.expected_value = expected_value
        self.deviation_percent = deviation_percent
        self.timestamp = timestamp
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.anomaly_type,
            "severity": self.severity,
            "description": self.description,
            "value": self.value,
            "expected_value": self.expected_value,
            "deviation_percent": self.deviation_percent,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class AnomalyDetectionService:
    """
    Service for detecting anomalies in performance data.
    
    Uses statistical methods (Z-score, IQR) to identify outliers and anomalies.
    """
    
    def __init__(
        self,
        z_score_threshold: float = 3.0,
        min_samples: int = 10,
        iqr_multiplier: float = 1.5
    ):
        """
        Initialize anomaly detection service.
        
        Args:
            z_score_threshold: Z-score threshold for anomaly detection
            min_samples: Minimum number of samples required for detection
            iqr_multiplier: IQR multiplier for outlier detection
        """
        self.z_score_threshold = z_score_threshold
        self.min_samples = min_samples
        self.iqr_multiplier = iqr_multiplier
        logger.info(f"AnomalyDetectionService initialized (z_threshold={z_score_threshold})")
    
    def detect_orchestration_anomalies(
        self,
        executions: List[OrchestrationExecution]
    ) -> List[Anomaly]:
        """
        Detect anomalies in orchestration executions.
        
        Args:
            executions: List of orchestration executions
            
        Returns:
            List of detected anomalies
        """
        if len(executions) < self.min_samples:
            logger.info(f"Insufficient samples for anomaly detection: {len(executions)} < {self.min_samples}")
            return []
        
        anomalies = []
        
        # Sort by timestamp
        sorted_executions = sorted(executions, key=lambda e: e.started_at)
        
        # Detect duration anomalies
        anomalies.extend(self._detect_duration_anomalies(sorted_executions))
        
        # Detect failure spikes
        anomalies.extend(self._detect_failure_spikes(sorted_executions))
        
        # Detect token usage anomalies
        anomalies.extend(self._detect_token_anomalies(sorted_executions))
        
        # Detect cost anomalies
        anomalies.extend(self._detect_cost_anomalies(sorted_executions))
        
        logger.info(f"Detected {len(anomalies)} anomalies in {len(executions)} executions")
        return anomalies
    
    def detect_pattern_anomalies(
        self,
        pattern_performances: List[PatternPerformance],
        pattern_name: Optional[str] = None
    ) -> List[Anomaly]:
        """
        Detect anomalies in pattern performances.
        
        Args:
            pattern_performances: List of pattern performances
            pattern_name: Optional pattern name to filter by
            
        Returns:
            List of detected anomalies
        """
        # Filter by pattern if specified
        if pattern_name:
            pattern_performances = [p for p in pattern_performances if p.pattern_name == pattern_name]
        
        if len(pattern_performances) < self.min_samples:
            logger.info(f"Insufficient samples for pattern anomaly detection: {len(pattern_performances)} < {self.min_samples}")
            return []
        
        anomalies = []
        
        # Sort by timestamp
        sorted_perfs = sorted(pattern_performances, key=lambda p: p.started_at)
        
        # Detect duration anomalies
        anomalies.extend(self._detect_pattern_duration_anomalies(sorted_perfs))
        
        # Detect confidence score anomalies
        anomalies.extend(self._detect_confidence_anomalies(sorted_perfs))
        
        # Detect token usage anomalies
        anomalies.extend(self._detect_pattern_token_anomalies(sorted_perfs))
        
        logger.info(f"Detected {len(anomalies)} anomalies in {len(pattern_performances)} pattern performances")
        return anomalies
    
    def detect_real_time_anomaly(
        self,
        current_execution: OrchestrationExecution,
        historical_executions: List[OrchestrationExecution]
    ) -> Optional[Anomaly]:
        """
        Detect anomaly in real-time for a single execution.
        
        Args:
            current_execution: Current execution to check
            historical_executions: Historical executions for baseline
            
        Returns:
            Anomaly if detected, None otherwise
        """
        if len(historical_executions) < self.min_samples:
            return None
        
        # Check duration anomaly
        durations = [e.duration_seconds for e in historical_executions if e.duration_seconds]
        if durations and current_execution.duration_seconds:
            z_score = self._calculate_z_score(current_execution.duration_seconds, durations)
            
            if abs(z_score) > self.z_score_threshold:
                severity = self._determine_severity(abs(z_score))
                deviation = ((current_execution.duration_seconds - mean(durations)) / mean(durations) * 100)
                
                return Anomaly(
                    anomaly_type=AnomalyType.DURATION_SPIKE if z_score > 0 else AnomalyType.DURATION_DROP,
                    severity=severity,
                    description=f"Execution duration {'increased' if z_score > 0 else 'decreased'} significantly",
                    value=current_execution.duration_seconds,
                    expected_value=mean(durations),
                    deviation_percent=deviation,
                    timestamp=current_execution.started_at,
                    metadata={
                        "execution_id": current_execution.execution_id,
                        "z_score": z_score
                    }
                )
        
        return None
    
    def _detect_duration_anomalies(
        self,
        executions: List[OrchestrationExecution]
    ) -> List[Anomaly]:
        """Detect duration anomalies using Z-score."""
        anomalies = []
        durations = [e.duration_seconds for e in executions if e.duration_seconds]
        
        if len(durations) < self.min_samples:
            return anomalies
        
        mean_duration = mean(durations)
        std_duration = stdev(durations) if len(durations) > 1 else 0
        
        if std_duration == 0:
            return anomalies
        
        for execution in executions:
            if not execution.duration_seconds:
                continue
            
            z_score = (execution.duration_seconds - mean_duration) / std_duration
            
            if abs(z_score) > self.z_score_threshold:
                severity = self._determine_severity(abs(z_score))
                deviation = ((execution.duration_seconds - mean_duration) / mean_duration * 100)
                
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.DURATION_SPIKE if z_score > 0 else AnomalyType.DURATION_DROP,
                    severity=severity,
                    description=f"Execution duration {'significantly higher' if z_score > 0 else 'significantly lower'} than expected",
                    value=execution.duration_seconds,
                    expected_value=mean_duration,
                    deviation_percent=deviation,
                    timestamp=execution.started_at,
                    metadata={
                        "execution_id": execution.execution_id,
                        "z_score": z_score
                    }
                ))
        
        return anomalies
    
    def _detect_failure_spikes(
        self,
        executions: List[OrchestrationExecution],
        window_size: int = 10
    ) -> List[Anomaly]:
        """Detect unusual spikes in failure rates."""
        anomalies = []
        
        if len(executions) < window_size * 2:
            return anomalies
        
        # Calculate rolling failure rate
        for i in range(window_size, len(executions)):
            window = executions[i-window_size:i]
            failures = len([e for e in window if e.status.value == "failed"])
            failure_rate = failures / window_size
            
            # Alert if failure rate exceeds 30%
            if failure_rate > 0.3:
                severity = AnomalySeverity.CRITICAL if failure_rate > 0.5 else AnomalySeverity.HIGH
                
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.FAILURE_SPIKE,
                    severity=severity,
                    description=f"High failure rate detected in recent executions",
                    value=failure_rate * 100,
                    expected_value=10.0,  # Expected < 10% failure rate
                    deviation_percent=(failure_rate - 0.1) / 0.1 * 100,
                    timestamp=executions[i].started_at,
                    metadata={
                        "failures_in_window": failures,
                        "window_size": window_size
                    }
                ))
        
        return anomalies
    
    def _detect_token_anomalies(
        self,
        executions: List[OrchestrationExecution]
    ) -> List[Anomaly]:
        """Detect token usage anomalies."""
        anomalies = []
        
        # Input tokens
        input_tokens = [e.total_tokens_input for e in executions if e.total_tokens_input]
        if len(input_tokens) >= self.min_samples:
            mean_input = mean(input_tokens)
            std_input = stdev(input_tokens) if len(input_tokens) > 1 else 0
            
            if std_input > 0:
                for execution in executions:
                    if not execution.total_tokens_input:
                        continue
                    
                    z_score = (execution.total_tokens_input - mean_input) / std_input
                    
                    if z_score > self.z_score_threshold:
                        severity = self._determine_severity(z_score)
                        deviation = ((execution.total_tokens_input - mean_input) / mean_input * 100)
                        
                        anomalies.append(Anomaly(
                            anomaly_type=AnomalyType.TOKEN_SPIKE,
                            severity=severity,
                            description="Input token usage significantly higher than expected",
                            value=execution.total_tokens_input,
                            expected_value=mean_input,
                            deviation_percent=deviation,
                            timestamp=execution.started_at,
                            metadata={
                                "execution_id": execution.execution_id,
                                "token_type": "input"
                            }
                        ))
        
        return anomalies
    
    def _detect_cost_anomalies(
        self,
        executions: List[OrchestrationExecution]
    ) -> List[Anomaly]:
        """Detect cost anomalies."""
        anomalies = []
        costs = [e.total_cost_usd for e in executions if e.total_cost_usd]
        
        if len(costs) < self.min_samples:
            return anomalies
        
        mean_cost = mean(costs)
        std_cost = stdev(costs) if len(costs) > 1 else 0
        
        if std_cost == 0:
            return anomalies
        
        for execution in executions:
            if not execution.total_cost_usd:
                continue
            
            z_score = (execution.total_cost_usd - mean_cost) / std_cost
            
            if z_score > self.z_score_threshold:
                severity = self._determine_severity(z_score)
                deviation = ((execution.total_cost_usd - mean_cost) / mean_cost * 100)
                
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.COST_SPIKE,
                    severity=severity,
                    description="Execution cost significantly higher than expected",
                    value=execution.total_cost_usd,
                    expected_value=mean_cost,
                    deviation_percent=deviation,
                    timestamp=execution.started_at,
                    metadata={
                        "execution_id": execution.execution_id
                    }
                ))
        
        return anomalies
    
    def _detect_pattern_duration_anomalies(
        self,
        performances: List[PatternPerformance]
    ) -> List[Anomaly]:
        """Detect duration anomalies in pattern performances."""
        anomalies = []
        durations = [p.duration_seconds for p in performances if p.duration_seconds]
        
        if len(durations) < self.min_samples:
            return anomalies
        
        mean_duration = mean(durations)
        std_duration = stdev(durations) if len(durations) > 1 else 0
        
        if std_duration == 0:
            return anomalies
        
        for performance in performances:
            if not performance.duration_seconds:
                continue
            
            z_score = (performance.duration_seconds - mean_duration) / std_duration
            
            if abs(z_score) > self.z_score_threshold:
                severity = self._determine_severity(abs(z_score))
                deviation = ((performance.duration_seconds - mean_duration) / mean_duration * 100)
                
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.DURATION_SPIKE if z_score > 0 else AnomalyType.DURATION_DROP,
                    severity=severity,
                    description=f"Pattern '{performance.pattern_name}' duration anomaly",
                    value=performance.duration_seconds,
                    expected_value=mean_duration,
                    deviation_percent=deviation,
                    timestamp=performance.started_at,
                    metadata={
                        "performance_id": performance.performance_id,
                        "pattern_name": performance.pattern_name
                    }
                ))
        
        return anomalies
    
    def _detect_confidence_anomalies(
        self,
        performances: List[PatternPerformance]
    ) -> List[Anomaly]:
        """Detect confidence score anomalies."""
        anomalies = []
        confidence_scores = [p.confidence_score for p in performances if p.confidence_score is not None]
        
        if len(confidence_scores) < self.min_samples:
            return anomalies
        
        mean_confidence = mean(confidence_scores)
        std_confidence = stdev(confidence_scores) if len(confidence_scores) > 1 else 0
        
        if std_confidence == 0:
            return anomalies
        
        for performance in performances:
            if performance.confidence_score is None:
                continue
            
            z_score = (performance.confidence_score - mean_confidence) / std_confidence
            
            if z_score < -self.z_score_threshold:  # Only alert on drops
                severity = self._determine_severity(abs(z_score))
                deviation = ((performance.confidence_score - mean_confidence) / mean_confidence * 100)
                
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.CONFIDENCE_DROP,
                    severity=severity,
                    description=f"Pattern '{performance.pattern_name}' confidence score dropped significantly",
                    value=performance.confidence_score,
                    expected_value=mean_confidence,
                    deviation_percent=deviation,
                    timestamp=performance.started_at,
                    metadata={
                        "performance_id": performance.performance_id,
                        "pattern_name": performance.pattern_name
                    }
                ))
        
        return anomalies
    
    def _detect_pattern_token_anomalies(
        self,
        performances: List[PatternPerformance]
    ) -> List[Anomaly]:
        """Detect token usage anomalies in patterns."""
        anomalies = []
        token_totals = [
            (p.tokens_input or 0) + (p.tokens_output or 0)
            for p in performances
        ]
        
        if len(token_totals) < self.min_samples:
            return anomalies
        
        mean_tokens = mean(token_totals)
        std_tokens = stdev(token_totals) if len(token_totals) > 1 else 0
        
        if std_tokens == 0:
            return anomalies
        
        for i, performance in enumerate(performances):
            total_tokens = (performance.tokens_input or 0) + (performance.tokens_output or 0)
            z_score = (total_tokens - mean_tokens) / std_tokens
            
            if z_score > self.z_score_threshold:
                severity = self._determine_severity(z_score)
                deviation = ((total_tokens - mean_tokens) / mean_tokens * 100)
                
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.TOKEN_SPIKE,
                    severity=severity,
                    description=f"Pattern '{performance.pattern_name}' token usage spike",
                    value=total_tokens,
                    expected_value=mean_tokens,
                    deviation_percent=deviation,
                    timestamp=performance.started_at,
                    metadata={
                        "performance_id": performance.performance_id,
                        "pattern_name": performance.pattern_name
                    }
                ))
        
        return anomalies
    
    def _calculate_z_score(self, value: float, values: List[float]) -> float:
        """Calculate Z-score for a value."""
        mean_val = mean(values)
        std_val = stdev(values) if len(values) > 1 else 0
        
        if std_val == 0:
            return 0.0
        
        return (value - mean_val) / std_val
    
    def _determine_severity(self, z_score: float) -> str:
        """Determine severity based on Z-score."""
        if z_score >= 5:
            return AnomalySeverity.CRITICAL
        elif z_score >= 4:
            return AnomalySeverity.HIGH
        elif z_score >= 3:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
