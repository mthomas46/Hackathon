"""
Anomaly Detector for MCP Performance Store.

Detects anomalous executions based on statistical analysis.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import statistics

from services.mcp_performance_store.domain.repositories import PerformanceRepository


class AnomalyDetector:
    """
    Service for detecting anomalous orchestration executions.
    
    Uses statistical methods to identify outliers and unusual patterns.
    """
    
    def __init__(self, repository: PerformanceRepository):
        """
        Initialize anomaly detector.
        
        Args:
            repository: Performance repository
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
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
            threshold_factor: Standard deviations from mean
            lookback_hours: Hours to analyze
        
        Returns:
            Dictionary with detected anomalies
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=lookback_hours)
        
        self.logger.info(
            f"Detecting anomalies from {start_time} to {end_time}, "
            f"pattern={pattern_used}"
        )
        
        # Get executions
        executions = await self.repository.list_executions(
            pattern_used=pattern_used,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        if not executions:
            return {
                "anomalies": [],
                "summary": {
                    "total_analyzed": 0,
                    "anomalies_detected": 0,
                    "lookback_hours": lookback_hours
                }
            }
        
        # Detect different types of anomalies
        latency_anomalies = self._detect_latency_anomalies(
            executions,
            threshold_factor
        )
        
        error_anomalies = self._detect_error_anomalies(executions)
        
        quality_anomalies = self._detect_quality_anomalies(executions)
        
        cost_anomalies = self._detect_cost_anomalies(executions, threshold_factor)
        
        # Combine all anomalies
        all_anomalies = (
            latency_anomalies +
            error_anomalies +
            quality_anomalies +
            cost_anomalies
        )
        
        # Sort by severity
        all_anomalies.sort(
            key=lambda x: {"critical": 0, "warning": 1, "info": 2}.get(
                x.get("severity", "info"), 2
            )
        )
        
        return {
            "anomalies": all_anomalies,
            "summary": {
                "total_analyzed": len(executions),
                "anomalies_detected": len(all_anomalies),
                "by_type": {
                    "latency": len(latency_anomalies),
                    "error": len(error_anomalies),
                    "quality": len(quality_anomalies),
                    "cost": len(cost_anomalies)
                },
                "by_severity": {
                    "critical": len([a for a in all_anomalies if a["severity"] == "critical"]),
                    "warning": len([a for a in all_anomalies if a["severity"] == "warning"]),
                    "info": len([a for a in all_anomalies if a["severity"] == "info"])
                },
                "lookback_hours": lookback_hours,
                "threshold_factor": threshold_factor
            },
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        }
    
    def _detect_latency_anomalies(
        self,
        executions: List,
        threshold_factor: float
    ) -> List[Dict[str, Any]]:
        """Detect latency anomalies using statistical analysis."""
        if len(executions) < 10:
            return []
        
        latencies = [e.latency_ms for e in executions]
        mean_latency = statistics.mean(latencies)
        stdev_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0
        
        threshold = mean_latency + (threshold_factor * stdev_latency)
        
        anomalies = []
        for execution in executions:
            if execution.latency_ms > threshold:
                # Determine severity
                if execution.latency_ms > mean_latency + (3 * stdev_latency):
                    severity = "critical"
                elif execution.latency_ms > mean_latency + (2 * stdev_latency):
                    severity = "warning"
                else:
                    severity = "info"
                
                anomalies.append({
                    "type": "latency",
                    "severity": severity,
                    "execution_id": execution.execution_id,
                    "timestamp": execution.timestamp.isoformat(),
                    "mcp_id": execution.mcp_id,
                    "pattern": execution.pattern_used,
                    "value": execution.latency_ms,
                    "threshold": round(threshold, 2),
                    "deviation_factor": round(
                        (execution.latency_ms - mean_latency) / stdev_latency if stdev_latency > 0 else 0,
                        2
                    ),
                    "message": f"Latency {execution.latency_ms}ms exceeds threshold {threshold:.0f}ms"
                })
        
        return anomalies
    
    def _detect_error_anomalies(self, executions: List) -> List[Dict[str, Any]]:
        """Detect failed executions."""
        anomalies = []
        
        for execution in executions:
            if not execution.success:
                anomalies.append({
                    "type": "error",
                    "severity": "critical",
                    "execution_id": execution.execution_id,
                    "timestamp": execution.timestamp.isoformat(),
                    "mcp_id": execution.mcp_id,
                    "pattern": execution.pattern_used,
                    "error": execution.error,
                    "message": f"Execution failed: {execution.error or 'Unknown error'}"
                })
        
        return anomalies
    
    def _detect_quality_anomalies(self, executions: List) -> List[Dict[str, Any]]:
        """Detect quality issues (low accuracy, hallucinations)."""
        anomalies = []
        
        for execution in executions:
            # Check for hallucinations
            if execution.hallucination_detected:
                anomalies.append({
                    "type": "quality",
                    "severity": "warning",
                    "execution_id": execution.execution_id,
                    "timestamp": execution.timestamp.isoformat(),
                    "mcp_id": execution.mcp_id,
                    "pattern": execution.pattern_used,
                    "issue": "hallucination",
                    "message": "Hallucination detected in response"
                })
            
            # Check for low accuracy
            if execution.accuracy_score < 0.5:
                severity = "critical" if execution.accuracy_score < 0.3 else "warning"
                anomalies.append({
                    "type": "quality",
                    "severity": severity,
                    "execution_id": execution.execution_id,
                    "timestamp": execution.timestamp.isoformat(),
                    "mcp_id": execution.mcp_id,
                    "pattern": execution.pattern_used,
                    "issue": "low_accuracy",
                    "value": execution.accuracy_score,
                    "message": f"Low accuracy score: {execution.accuracy_score:.2f}"
                })
            
            # Check for low confidence
            if execution.confidence < 0.4 and execution.success:
                anomalies.append({
                    "type": "quality",
                    "severity": "info",
                    "execution_id": execution.execution_id,
                    "timestamp": execution.timestamp.isoformat(),
                    "mcp_id": execution.mcp_id,
                    "pattern": execution.pattern_used,
                    "issue": "low_confidence",
                    "value": execution.confidence,
                    "message": f"Low confidence score: {execution.confidence:.2f}"
                })
        
        return anomalies
    
    def _detect_cost_anomalies(
        self,
        executions: List,
        threshold_factor: float
    ) -> List[Dict[str, Any]]:
        """Detect unusually high costs."""
        if len(executions) < 10:
            return []
        
        costs = [e.cost_cents for e in executions]
        mean_cost = statistics.mean(costs)
        stdev_cost = statistics.stdev(costs) if len(costs) > 1 else 0
        
        threshold = mean_cost + (threshold_factor * stdev_cost)
        
        anomalies = []
        for execution in executions:
            if execution.cost_cents > threshold and execution.cost_cents > mean_cost * 2:
                anomalies.append({
                    "type": "cost",
                    "severity": "warning",
                    "execution_id": execution.execution_id,
                    "timestamp": execution.timestamp.isoformat(),
                    "mcp_id": execution.mcp_id,
                    "pattern": execution.pattern_used,
                    "value": execution.cost_cents,
                    "threshold": round(threshold, 4),
                    "message": f"High cost: {execution.cost_cents:.4f} cents (threshold: {threshold:.4f})"
                })
        
        return anomalies
