"""Pattern Performance Entity - Domain Layer.

Aggregates performance metrics for a specific LLM pattern across multiple executions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from statistics import mean, median

from services.mcp_performance_store.domain.entities.orchestration_execution import OrchestrationExecution
from services.mcp_performance_store.domain.value_objects.execution_status import ExecutionStatus


@dataclass
class PatternPerformance:
    """
    Represents aggregated performance metrics for a specific pattern.
    
    Tracks success rates, timing metrics, quality metrics, and trends
    for a particular LLM pattern (e.g., Chain-of-Thought, RAG, etc.)
    """
    
    # Identity
    pattern_name: str
    
    # Execution counts
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    timeout_executions: int = 0
    cancelled_executions: int = 0
    
    # Timing metrics (milliseconds)
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    p50_duration_ms: float = 0.0  # Median
    p95_duration_ms: float = 0.0  # 95th percentile
    p99_duration_ms: float = 0.0  # 99th percentile
    
    # Quality metrics
    avg_confidence: float = 0.0
    avg_sources: float = 0.0
    avg_response_length: float = 0.0
    
    # Trend data (time windows)
    executions_1h: int = 0
    executions_24h: int = 0
    executions_7d: int = 0
    executions_30d: int = 0
    
    # Success rates by time window
    success_rate_1h: float = 0.0
    success_rate_24h: float = 0.0
    success_rate_7d: float = 0.0
    success_rate_30d: float = 0.0
    
    # Recent durations for percentile calculation (last 100)
    recent_durations: List[float] = field(default_factory=list)
    
    # Timestamps
    first_seen: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    last_execution: Optional[datetime] = None
    
    # Error tracking
    error_types: Dict[str, int] = field(default_factory=dict)  # error_type -> count
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_from_execution(self, execution: OrchestrationExecution) -> None:
        """
        Update metrics from a new execution.
        
        Args:
            execution: The completed execution to incorporate
        """
        self.total_executions += 1
        self.last_execution = execution.end_time or datetime.now()
        self.last_updated = datetime.now()
        
        # Update counts by status
        if execution.status == ExecutionStatus.SUCCESS:
            self.successful_executions += 1
        elif execution.status == ExecutionStatus.FAILED:
            self.failed_executions += 1
            # Track error types
            if execution.error_type:
                self.error_types[execution.error_type] = self.error_types.get(execution.error_type, 0) + 1
        elif execution.status == ExecutionStatus.TIMEOUT:
            self.timeout_executions += 1
        elif execution.status == ExecutionStatus.CANCELLED:
            self.cancelled_executions += 1
        
        # Update timing metrics
        if execution.total_duration_ms > 0:
            self._update_duration_metrics(execution.total_duration_ms)
        
        # Update quality metrics (only for successful executions)
        if execution.status == ExecutionStatus.SUCCESS:
            self._update_quality_metrics(execution)
    
    def _update_duration_metrics(self, duration_ms: float) -> None:
        """Update timing metrics with new duration."""
        # Update min/max
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)
        
        # Update average (incremental calculation)
        if self.avg_duration_ms == 0:
            self.avg_duration_ms = duration_ms
        else:
            # Weighted average
            n = self.total_executions
            self.avg_duration_ms = ((self.avg_duration_ms * (n - 1)) + duration_ms) / n
        
        # Track recent durations for percentile calculation
        self.recent_durations.append(duration_ms)
        if len(self.recent_durations) > 100:
            self.recent_durations.pop(0)  # Keep only last 100
        
        # Update percentiles
        self._calculate_percentiles()
    
    def _update_quality_metrics(self, execution: OrchestrationExecution) -> None:
        """Update quality metrics from successful execution."""
        n = self.successful_executions
        
        # Confidence
        if n == 1:
            self.avg_confidence = execution.confidence
        else:
            self.avg_confidence = ((self.avg_confidence * (n - 1)) + execution.confidence) / n
        
        # Sources
        if n == 1:
            self.avg_sources = float(execution.num_sources)
        else:
            self.avg_sources = ((self.avg_sources * (n - 1)) + execution.num_sources) / n
        
        # Response length
        if n == 1:
            self.avg_response_length = float(execution.response_length)
        else:
            self.avg_response_length = ((self.avg_response_length * (n - 1)) + execution.response_length) / n
    
    def _calculate_percentiles(self) -> None:
        """Calculate percentile metrics from recent durations."""
        if not self.recent_durations:
            return
        
        sorted_durations = sorted(self.recent_durations)
        n = len(sorted_durations)
        
        # p50 (median)
        self.p50_duration_ms = median(sorted_durations)
        
        # p95
        p95_index = int(n * 0.95)
        self.p95_duration_ms = sorted_durations[min(p95_index, n - 1)]
        
        # p99
        p99_index = int(n * 0.99)
        self.p99_duration_ms = sorted_durations[min(p99_index, n - 1)]
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    def get_failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_executions == 0:
            return 0.0
        return self.failed_executions / self.total_executions
    
    def get_timeout_rate(self) -> float:
        """Calculate timeout rate."""
        if self.total_executions == 0:
            return 0.0
        return self.timeout_executions / self.total_executions
    
    def is_degrading(self, threshold: float = 0.1) -> bool:
        """
        Check if performance is degrading.
        
        Compares recent (24h) success rate to longer-term (7d).
        
        Args:
            threshold: Minimum difference to consider degrading
            
        Returns:
            True if 24h success rate is significantly lower than 7d
        """
        if self.success_rate_7d == 0:
            return False
        
        diff = self.success_rate_7d - self.success_rate_24h
        return diff > threshold
    
    def is_improving(self, threshold: float = 0.1) -> bool:
        """Check if performance is improving."""
        if self.success_rate_7d == 0:
            return False
        
        diff = self.success_rate_24h - self.success_rate_7d
        return diff > threshold
    
    def get_most_common_error(self) -> Optional[str]:
        """Get the most common error type."""
        if not self.error_types:
            return None
        return max(self.error_types.items(), key=lambda x: x[1])[0]
    
    def is_stable(self) -> bool:
        """Check if pattern performance is stable (not degrading or improving significantly)."""
        return not self.is_degrading() and not self.is_improving()
    
    def get_health_score(self) -> float:
        """
        Calculate overall health score (0-100).
        
        Factors:
        - Success rate (60% weight)
        - Average duration vs p95 (20% weight)
        - Trend (20% weight)
        """
        # Success rate component (0-60)
        success_component = self.get_success_rate() * 60
        
        # Duration component (0-20)
        # Good if avg is close to p50, bad if close to p95
        if self.p95_duration_ms > 0:
            duration_ratio = self.avg_duration_ms / self.p95_duration_ms
            duration_component = (1 - min(duration_ratio, 1.0)) * 20
        else:
            duration_component = 20
        
        # Trend component (0-20)
        if self.is_improving():
            trend_component = 20
        elif self.is_degrading():
            trend_component = 0
        else:
            trend_component = 10  # Stable
        
        return min(success_component + duration_component + trend_component, 100.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_name": self.pattern_name,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "timeout_executions": self.timeout_executions,
            "cancelled_executions": self.cancelled_executions,
            "success_rate": self.get_success_rate(),
            "failure_rate": self.get_failure_rate(),
            "timeout_rate": self.get_timeout_rate(),
            "avg_duration_ms": self.avg_duration_ms,
            "min_duration_ms": self.min_duration_ms if self.min_duration_ms != float('inf') else 0,
            "max_duration_ms": self.max_duration_ms,
            "p50_duration_ms": self.p50_duration_ms,
            "p95_duration_ms": self.p95_duration_ms,
            "p99_duration_ms": self.p99_duration_ms,
            "avg_confidence": self.avg_confidence,
            "avg_sources": self.avg_sources,
            "avg_response_length": self.avg_response_length,
            "executions_1h": self.executions_1h,
            "executions_24h": self.executions_24h,
            "executions_7d": self.executions_7d,
            "executions_30d": self.executions_30d,
            "success_rate_1h": self.success_rate_1h,
            "success_rate_24h": self.success_rate_24h,
            "success_rate_7d": self.success_rate_7d,
            "success_rate_30d": self.success_rate_30d,
            "recent_durations": self.recent_durations,
            "first_seen": self.first_seen.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "error_types": self.error_types,
            "metadata": self.metadata,
            "health_score": self.get_health_score(),
            "is_degrading": self.is_degrading(),
            "is_improving": self.is_improving(),
            "most_common_error": self.get_most_common_error()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatternPerformance":
        """Create from dictionary."""
        return cls(
            pattern_name=data["pattern_name"],
            total_executions=data.get("total_executions", 0),
            successful_executions=data.get("successful_executions", 0),
            failed_executions=data.get("failed_executions", 0),
            timeout_executions=data.get("timeout_executions", 0),
            cancelled_executions=data.get("cancelled_executions", 0),
            avg_duration_ms=data.get("avg_duration_ms", 0.0),
            min_duration_ms=data.get("min_duration_ms", float('inf')),
            max_duration_ms=data.get("max_duration_ms", 0.0),
            p50_duration_ms=data.get("p50_duration_ms", 0.0),
            p95_duration_ms=data.get("p95_duration_ms", 0.0),
            p99_duration_ms=data.get("p99_duration_ms", 0.0),
            avg_confidence=data.get("avg_confidence", 0.0),
            avg_sources=data.get("avg_sources", 0.0),
            avg_response_length=data.get("avg_response_length", 0.0),
            executions_1h=data.get("executions_1h", 0),
            executions_24h=data.get("executions_24h", 0),
            executions_7d=data.get("executions_7d", 0),
            executions_30d=data.get("executions_30d", 0),
            success_rate_1h=data.get("success_rate_1h", 0.0),
            success_rate_24h=data.get("success_rate_24h", 0.0),
            success_rate_7d=data.get("success_rate_7d", 0.0),
            success_rate_30d=data.get("success_rate_30d", 0.0),
            recent_durations=data.get("recent_durations", []),
            first_seen=datetime.fromisoformat(data["first_seen"]) if isinstance(data.get("first_seen"), str) else data.get("first_seen", datetime.now()),
            last_updated=datetime.fromisoformat(data["last_updated"]) if isinstance(data.get("last_updated"), str) else data.get("last_updated", datetime.now()),
            last_execution=datetime.fromisoformat(data["last_execution"]) if data.get("last_execution") and isinstance(data["last_execution"], str) else None,
            error_types=data.get("error_types", {}),
            metadata=data.get("metadata", {})
        )