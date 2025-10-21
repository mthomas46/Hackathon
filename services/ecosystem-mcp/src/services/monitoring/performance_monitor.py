"""
Performance Monitoring System (Option C, Phase 3, Days 6-8)

Comprehensive performance monitoring with:
- Real-time metrics collection
- Performance tracking across all operations
- Bottleneck detection
- Resource utilization monitoring
- Optimization recommendations

Provides deep insights for system optimization.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics."""
    DURATION = "duration"  # Time taken (ms)
    THROUGHPUT = "throughput"  # Operations per second
    COUNT = "count"  # Number of operations
    SIZE = "size"  # Data size (bytes)
    RATE = "rate"  # Success/failure rate
    UTILIZATION = "utilization"  # Resource usage (%)


class OperationType(Enum):
    """Types of operations to monitor."""
    INGESTION = "ingestion"
    EMBEDDING = "embedding"
    RAG_QUERY = "rag_query"
    DOCUMENTATION = "documentation"
    DATABASE = "database"
    CACHE = "cache"
    API_REQUEST = "api_request"


@dataclass
class PerformanceMetric:
    """Single performance metric measurement."""
    timestamp: datetime
    operation_type: OperationType
    metric_type: MetricType
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "operation_type": self.operation_type.value,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "metadata": self.metadata
        }


@dataclass
class PerformanceStats:
    """Statistical summary of performance metrics."""
    operation_type: OperationType
    metric_type: MetricType
    count: int
    min_value: float
    max_value: float
    avg_value: float
    median_value: float
    p95_value: float
    p99_value: float
    std_dev: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_type": self.operation_type.value,
            "metric_type": self.metric_type.value,
            "count": self.count,
            "min": self.min_value,
            "max": self.max_value,
            "avg": self.avg_value,
            "median": self.median_value,
            "p95": self.p95_value,
            "p99": self.p99_value,
            "std_dev": self.std_dev
        }


@dataclass
class Bottleneck:
    """Identified performance bottleneck."""
    operation_type: OperationType
    severity: str  # "low", "medium", "high", "critical"
    description: str
    avg_duration_ms: float
    impact_score: float  # 0-100
    recommendation: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_type": self.operation_type.value,
            "severity": self.severity,
            "description": self.description,
            "avg_duration_ms": self.avg_duration_ms,
            "impact_score": self.impact_score,
            "recommendation": self.recommendation,
            "detected_at": self.detected_at.isoformat()
        }


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.
    
    Features:
    - Real-time metrics collection
    - Statistical analysis
    - Bottleneck detection
    - Trend analysis
    - Optimization recommendations
    """
    
    def __init__(self, max_metrics: int = 10000):
        """
        Initialize performance monitor.
        
        Args:
            max_metrics: Maximum metrics to keep in memory
        """
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.operation_metrics: Dict[OperationType, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.bottlenecks: List[Bottleneck] = []
        logger.info("PerformanceMonitor initialized")
    
    def record_metric(
        self,
        operation_type: OperationType,
        metric_type: MetricType,
        value: float,
        **metadata
    ):
        """
        Record a performance metric.
        
        Args:
            operation_type: Type of operation
            metric_type: Type of metric
            value: Metric value
            **metadata: Additional metadata
        """
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            operation_type=operation_type,
            metric_type=metric_type,
            value=value,
            metadata=metadata
        )
        
        self.metrics.append(metric)
        self.operation_metrics[operation_type].append(metric)
    
    def record_duration(
        self,
        operation_type: OperationType,
        duration_ms: float,
        **metadata
    ):
        """Record operation duration."""
        self.record_metric(
            operation_type,
            MetricType.DURATION,
            duration_ms,
            **metadata
        )
    
    def record_throughput(
        self,
        operation_type: OperationType,
        ops_per_sec: float,
        **metadata
    ):
        """Record throughput metric."""
        self.record_metric(
            operation_type,
            MetricType.THROUGHPUT,
            ops_per_sec,
            **metadata
        )
    
    def get_stats(
        self,
        operation_type: OperationType,
        metric_type: MetricType,
        time_window: Optional[timedelta] = None
    ) -> Optional[PerformanceStats]:
        """
        Get statistical summary for operation and metric type.
        
        Args:
            operation_type: Type of operation
            metric_type: Type of metric
            time_window: Optional time window (None = all time)
        
        Returns:
            PerformanceStats or None if no data
        """
        # Filter metrics
        metrics = self.operation_metrics[operation_type]
        
        if time_window:
            cutoff = datetime.utcnow() - time_window
            metrics = [m for m in metrics if m.timestamp >= cutoff]
        else:
            metrics = list(metrics)
        
        # Filter by metric type
        metrics = [m for m in metrics if m.metric_type == metric_type]
        
        if not metrics:
            return None
        
        values = [m.value for m in metrics]
        
        # Calculate statistics
        sorted_values = sorted(values)
        count = len(values)
        
        stats = PerformanceStats(
            operation_type=operation_type,
            metric_type=metric_type,
            count=count,
            min_value=min(values),
            max_value=max(values),
            avg_value=statistics.mean(values),
            median_value=statistics.median(values),
            p95_value=sorted_values[int(count * 0.95)] if count > 0 else 0,
            p99_value=sorted_values[int(count * 0.99)] if count > 0 else 0,
            std_dev=statistics.stdev(values) if count > 1 else 0
        )
        
        return stats
    
    def detect_bottlenecks(self) -> List[Bottleneck]:
        """
        Detect performance bottlenecks.
        
        Analyzes recent metrics to identify slow operations.
        
        Returns:
            List of detected bottlenecks
        """
        bottlenecks = []
        
        # Analyze each operation type
        for op_type in OperationType:
            stats = self.get_stats(
                op_type,
                MetricType.DURATION,
                time_window=timedelta(minutes=15)
            )
            
            if not stats or stats.count < 10:
                continue
            
            # Check if operation is slow
            severity, description, recommendation = self._analyze_performance(
                op_type,
                stats
            )
            
            if severity:
                impact_score = self._calculate_impact_score(stats)
                
                bottleneck = Bottleneck(
                    operation_type=op_type,
                    severity=severity,
                    description=description,
                    avg_duration_ms=stats.avg_value,
                    impact_score=impact_score,
                    recommendation=recommendation
                )
                
                bottlenecks.append(bottleneck)
        
        # Sort by impact score
        bottlenecks.sort(key=lambda b: b.impact_score, reverse=True)
        
        self.bottlenecks = bottlenecks
        return bottlenecks
    
    def _analyze_performance(
        self,
        op_type: OperationType,
        stats: PerformanceStats
    ) -> tuple[Optional[str], str, str]:
        """
        Analyze performance and provide recommendations.
        
        Returns:
            (severity, description, recommendation)
        """
        # Define thresholds for each operation type (in ms)
        thresholds = {
            OperationType.INGESTION: {"ok": 100, "slow": 500, "critical": 2000},
            OperationType.EMBEDDING: {"ok": 50, "slow": 200, "critical": 1000},
            OperationType.RAG_QUERY: {"ok": 500, "slow": 2000, "critical": 5000},
            OperationType.DOCUMENTATION: {"ok": 1000, "slow": 5000, "critical": 15000},
            OperationType.DATABASE: {"ok": 50, "slow": 200, "critical": 1000},
            OperationType.CACHE: {"ok": 10, "slow": 50, "critical": 200},
            OperationType.API_REQUEST: {"ok": 200, "slow": 1000, "critical": 3000}
        }
        
        threshold = thresholds.get(op_type, {"ok": 100, "slow": 500, "critical": 2000})
        avg = stats.avg_value
        
        if avg > threshold["critical"]:
            return (
                "critical",
                f"{op_type.value} operations are critically slow (avg: {avg:.0f}ms)",
                self._get_recommendation(op_type, "critical", stats)
            )
        elif avg > threshold["slow"]:
            return (
                "high",
                f"{op_type.value} operations are slow (avg: {avg:.0f}ms)",
                self._get_recommendation(op_type, "high", stats)
            )
        elif avg > threshold["ok"]:
            return (
                "medium",
                f"{op_type.value} operations could be faster (avg: {avg:.0f}ms)",
                self._get_recommendation(op_type, "medium", stats)
            )
        
        return None, "", ""
    
    def _get_recommendation(
        self,
        op_type: OperationType,
        severity: str,
        stats: PerformanceStats
    ) -> str:
        """Get optimization recommendation."""
        recommendations = {
            OperationType.INGESTION: {
                "critical": "Enable parallel processing with sub-job orchestration. Check for slow file parsing.",
                "high": "Increase batch sizes for embedding generation. Review file processing logic.",
                "medium": "Consider caching normalized content. Optimize file classification."
            },
            OperationType.EMBEDDING: {
                "critical": "Switch to FastEmbed service. Increase batch sizes significantly.",
                "high": "Use larger batch sizes (50-100). Enable embedding cache.",
                "medium": "Optimize batch size. Consider pre-computing common embeddings."
            },
            OperationType.RAG_QUERY: {
                "critical": "Add vector search caching. Optimize LLM prompt size. Use faster LLM.",
                "high": "Enable query result caching. Reduce context size. Optimize vector search.",
                "medium": "Cache frequent queries. Optimize embedding generation."
            },
            OperationType.DOCUMENTATION: {
                "critical": "Use incremental documentation. Parallelize doc generation. Optimize LLM calls.",
                "high": "Enable incremental updates. Batch documentation generation.",
                "medium": "Use incremental documentation for updates. Cache common patterns."
            },
            OperationType.DATABASE: {
                "critical": "Add database indexes. Use connection pooling. Optimize queries.",
                "high": "Review slow queries. Add missing indexes. Increase connection pool.",
                "medium": "Optimize query patterns. Consider read replicas."
            },
            OperationType.CACHE: {
                "critical": "Check Redis connection. Increase cache size. Review cache keys.",
                "high": "Optimize cache key structure. Increase TTL for stable data.",
                "medium": "Review cache hit rates. Optimize serialization."
            },
            OperationType.API_REQUEST: {
                "critical": "Add request caching. Optimize database queries. Enable compression.",
                "high": "Add response caching. Optimize slow endpoints.",
                "medium": "Enable HTTP caching. Optimize serialization."
            }
        }
        
        return recommendations.get(op_type, {}).get(
            severity,
            "Review operation implementation for optimization opportunities."
        )
    
    def _calculate_impact_score(self, stats: PerformanceStats) -> float:
        """
        Calculate impact score (0-100) based on frequency and duration.
        
        Higher score = more impact on overall system performance.
        """
        # Frequency component (0-50)
        frequency_score = min(stats.count / 100 * 50, 50)
        
        # Duration component (0-50)
        # Normalize to 0-50 range (assuming max 10s)
        duration_score = min(stats.avg_value / 10000 * 50, 50)
        
        return frequency_score + duration_score
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with performance summary
        """
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_metrics": len(self.metrics),
            "operations": {},
            "bottlenecks": [b.to_dict() for b in self.bottlenecks],
            "health_score": self._calculate_health_score()
        }
        
        # Get stats for each operation type
        for op_type in OperationType:
            duration_stats = self.get_stats(
                op_type,
                MetricType.DURATION,
                time_window=timedelta(hours=1)
            )
            
            if duration_stats:
                summary["operations"][op_type.value] = duration_stats.to_dict()
        
        return summary
    
    def _calculate_health_score(self) -> float:
        """
        Calculate overall system health score (0-100).
        
        100 = perfect, 0 = critical issues
        """
        if not self.bottlenecks:
            return 100.0
        
        # Deduct points based on bottleneck severity
        deductions = {
            "low": 5,
            "medium": 10,
            "high": 20,
            "critical": 40
        }
        
        total_deduction = sum(
            deductions.get(b.severity, 0) for b in self.bottlenecks
        )
        
        return max(0, 100 - total_deduction)


# Context manager for timing operations
class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(
        self,
        monitor: PerformanceMonitor,
        operation_type: OperationType,
        **metadata
    ):
        self.monitor = monitor
        self.operation_type = operation_type
        self.metadata = metadata
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        self.monitor.record_duration(
            self.operation_type,
            duration_ms,
            **self.metadata
        )
    
    async def __aenter__(self):
        self.start_time = time.perf_counter()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        self.monitor.record_duration(
            self.operation_type,
            duration_ms,
            **self.metadata
        )


# Singleton
_performance_monitor_instance: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get singleton performance monitor instance."""
    global _performance_monitor_instance
    if _performance_monitor_instance is None:
        _performance_monitor_instance = PerformanceMonitor()
    return _performance_monitor_instance

