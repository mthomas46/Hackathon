"""Anomaly Detector."""

import logging
from typing import List, Optional

from ...domain.entities.anomaly import Anomaly
from ...domain.entities.log_entry import LogEntry

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Anomaly detection engine.
    
    Uses statistical methods and ML for detecting anomalies in log patterns.
    """
    
    def __init__(self, threshold: float = 2.0):
        """
        Initialize anomaly detector.
        
        Args:
            threshold: Standard deviation threshold for anomalies
        """
        self.threshold = threshold
        self.baseline_rates: dict = {}
        logger.info(f"Anomaly detector initialized (threshold: {threshold})")
    
    async def detect_rate_anomaly(
        self,
        service: str,
        current_rate: float,
        baseline_rate: float,
    ) -> Optional[Anomaly]:
        """
        Detect rate anomaly.
        
        Args:
            service: Service name
            current_rate: Current log rate
            baseline_rate: Baseline log rate
            
        Returns:
            Anomaly if detected, None otherwise
        """
        if baseline_rate == 0:
            return None
        
        deviation = abs(current_rate - baseline_rate) / baseline_rate
        
        if deviation > self.threshold:
            confidence = min(deviation / (self.threshold * 2), 1.0)
            severity = "critical" if deviation > self.threshold * 2 else "high"
            
            anomaly = Anomaly(
                service=service,
                type="rate",
                severity=severity,
                description=f"Log rate anomaly: {current_rate:.2f} vs baseline {baseline_rate:.2f}",
                confidence=confidence,
                baseline_value=baseline_rate,
                observed_value=current_rate,
                deviation=deviation,
                detection_method="statistical",
            )
            
            logger.warning(f"Rate anomaly detected for {service}: {deviation:.2%} deviation")
            return anomaly
        
        return None
    
    async def detect_error_spike(
        self,
        service: str,
        error_count: int,
        baseline_errors: int,
    ) -> Optional[Anomaly]:
        """
        Detect error spike.
        
        Args:
            service: Service name
            error_count: Current error count
            baseline_errors: Baseline error count
            
        Returns:
            Anomaly if detected, None otherwise
        """
        if baseline_errors == 0 and error_count > 10:
            # Spike from zero
            anomaly = Anomaly(
                service=service,
                type="error_spike",
                severity="critical",
                description=f"Error spike detected: {error_count} errors from baseline 0",
                confidence=1.0,
                baseline_value=float(baseline_errors),
                observed_value=float(error_count),
                detection_method="threshold",
            )
            
            logger.warning(f"Error spike detected for {service}: {error_count} errors")
            return anomaly
        
        if baseline_errors > 0:
            ratio = error_count / baseline_errors
            if ratio > self.threshold:
                confidence = min(ratio / (self.threshold * 2), 1.0)
                severity = "critical" if ratio > self.threshold * 2 else "high"
                
                anomaly = Anomaly(
                    service=service,
                    type="error_spike",
                    severity=severity,
                    description=f"Error spike: {error_count} vs baseline {baseline_errors}",
                    confidence=confidence,
                    baseline_value=float(baseline_errors),
                    observed_value=float(error_count),
                    deviation=ratio - 1.0,
                    detection_method="statistical",
                )
                
                logger.warning(f"Error spike detected for {service}: {ratio:.2f}x increase")
                return anomaly
        
        return None
    
    async def analyze_log_pattern(self, logs: List[LogEntry]) -> List[Anomaly]:
        """
        Analyze log patterns for anomalies.
        
        Args:
            logs: List of log entries
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Group by service
        by_service = {}
        for log in logs:
            if log.service not in by_service:
                by_service[log.service] = []
            by_service[log.service].append(log)
        
        # Detect anomalies per service
        for service, service_logs in by_service.items():
            error_count = sum(1 for log in service_logs if log.is_error())
            
            # Get baseline (simplified)
            baseline_errors = self.baseline_rates.get(f"{service}:errors", 0)
            
            anomaly = await self.detect_error_spike(service, error_count, baseline_errors)
            if anomaly:
                anomalies.append(anomaly)
        
        return anomalies
    
    def update_baseline(self, service: str, metric: str, value: float) -> None:
        """Update baseline metric."""
        key = f"{service}:{metric}"
        self.baseline_rates[key] = value

