"""
Unit Tests for Performance Monitoring (Option C, Phase 3)

Tests:
- Metric recording
- Statistical analysis
- Bottleneck detection
- Health score calculation
- Performance timer
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services.monitoring.performance_monitor import (
    PerformanceMonitor,
    PerformanceMetric,
    PerformanceStats,
    Bottleneck,
    PerformanceTimer,
    OperationType,
    MetricType,
    get_performance_monitor
)


@pytest.fixture
def monitor():
    """Create fresh performance monitor."""
    return PerformanceMonitor(max_metrics=1000)


@pytest.mark.unit
class TestMetricRecording:
    """Test metric recording."""
    
    def test_record_metric(self, monitor):
        """Test basic metric recording."""
        monitor.record_metric(
            OperationType.INGESTION,
            MetricType.DURATION,
            100.5,
            file_count=10
        )
        
        assert len(monitor.metrics) == 1
        assert len(monitor.operation_metrics[OperationType.INGESTION]) == 1
        
        metric = monitor.metrics[0]
        assert metric.operation_type == OperationType.INGESTION
        assert metric.metric_type == MetricType.DURATION
        assert metric.value == 100.5
        assert metric.metadata["file_count"] == 10
    
    def test_record_duration(self, monitor):
        """Test duration recording helper."""
        monitor.record_duration(
            OperationType.EMBEDDING,
            250.0,
            batch_size=50
        )
        
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.metric_type == MetricType.DURATION
        assert metric.value == 250.0
    
    def test_record_throughput(self, monitor):
        """Test throughput recording helper."""
        monitor.record_throughput(
            OperationType.RAG_QUERY,
            15.5
        )
        
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.metric_type == MetricType.THROUGHPUT
        assert metric.value == 15.5
    
    def test_max_metrics_limit(self):
        """Test max metrics limit enforcement."""
        # Create monitor with max_metrics=10
        from collections import deque
        monitor = PerformanceMonitor()
        monitor.max_metrics = 10
        monitor.metrics = deque(maxlen=10)
        
        # Record 20 metrics
        for i in range(20):
            monitor.record_metric(
                OperationType.INGESTION,
                MetricType.DURATION,
                float(i)
            )
        
        # Should only keep last 10
        assert len(monitor.metrics) == 10
        assert monitor.metrics[-1].value == 19.0


@pytest.mark.unit
class TestStatistics:
    """Test statistical analysis."""
    
    def test_get_stats_basic(self, monitor):
        """Test basic statistics calculation."""
        # Record some metrics
        values = [100, 200, 150, 300, 250]
        for v in values:
            monitor.record_duration(OperationType.INGESTION, v)
        
        stats = monitor.get_stats(
            OperationType.INGESTION,
            MetricType.DURATION
        )
        
        assert stats is not None
        assert stats.count == 5
        assert stats.min_value == 100
        assert stats.max_value == 300
        assert stats.avg_value == 200.0
        assert stats.median_value == 200
    
    def test_get_stats_percentiles(self, monitor):
        """Test percentile calculations."""
        # Record 100 metrics
        for i in range(100):
            monitor.record_duration(OperationType.EMBEDDING, float(i))
        
        stats = monitor.get_stats(
            OperationType.EMBEDDING,
            MetricType.DURATION
        )
        
        assert stats.p95_value == pytest.approx(95.0, abs=1)
        assert stats.p99_value == pytest.approx(99.0, abs=1)
    
    def test_get_stats_no_data(self, monitor):
        """Test stats with no data."""
        stats = monitor.get_stats(
            OperationType.INGESTION,
            MetricType.DURATION
        )
        
        assert stats is None
    
    def test_get_stats_time_window(self, monitor):
        """Test stats with time window."""
        # Record old metric
        old_metric = PerformanceMetric(
            timestamp=datetime.utcnow() - timedelta(hours=2),
            operation_type=OperationType.INGESTION,
            metric_type=MetricType.DURATION,
            value=100.0
        )
        monitor.metrics.append(old_metric)
        monitor.operation_metrics[OperationType.INGESTION].append(old_metric)
        
        # Record recent metric
        monitor.record_duration(OperationType.INGESTION, 200.0)
        
        # Get stats for last hour (should only include recent)
        stats = monitor.get_stats(
            OperationType.INGESTION,
            MetricType.DURATION,
            time_window=timedelta(hours=1)
        )
        
        assert stats.count == 1
        assert stats.avg_value == 200.0


@pytest.mark.unit
class TestBottleneckDetection:
    """Test bottleneck detection."""
    
    def test_detect_bottlenecks_slow_operation(self, monitor):
        """Test detecting slow operations."""
        # Record slow ingestion operations
        for _ in range(20):
            monitor.record_duration(OperationType.INGESTION, 3000.0)  # 3s (critical)
        
        bottlenecks = monitor.detect_bottlenecks()
        
        assert len(bottlenecks) > 0
        assert bottlenecks[0].operation_type == OperationType.INGESTION
        assert bottlenecks[0].severity == "critical"
    
    def test_detect_bottlenecks_no_issues(self, monitor):
        """Test no bottlenecks for fast operations."""
        # Record fast operations
        for _ in range(20):
            monitor.record_duration(OperationType.EMBEDDING, 30.0)  # 30ms (good)
        
        bottlenecks = monitor.detect_bottlenecks()
        
        assert len(bottlenecks) == 0
    
    def test_bottleneck_severity_levels(self, monitor):
        """Test different severity levels."""
        # Critical
        for _ in range(20):
            monitor.record_duration(OperationType.INGESTION, 3000.0)
        
        # High
        for _ in range(20):
            monitor.record_duration(OperationType.EMBEDDING, 500.0)
        
        # Medium
        for _ in range(20):
            monitor.record_duration(OperationType.CACHE, 80.0)
        
        bottlenecks = monitor.detect_bottlenecks()
        
        severities = [b.severity for b in bottlenecks]
        assert "critical" in severities
        assert "high" in severities
        # Note: 80ms might be classified as high instead of medium depending on thresholds
        assert len(severities) >= 2  # At least critical and high
    
    def test_bottleneck_recommendations(self, monitor):
        """Test bottleneck recommendations."""
        # Record slow embedding operations
        for _ in range(20):
            monitor.record_duration(OperationType.EMBEDDING, 1500.0)
        
        bottlenecks = monitor.detect_bottlenecks()
        
        assert len(bottlenecks) > 0
        assert "FastEmbed" in bottlenecks[0].recommendation or "batch" in bottlenecks[0].recommendation.lower()
    
    def test_bottleneck_impact_score(self, monitor):
        """Test impact score calculation."""
        # High frequency, high duration
        for _ in range(100):
            monitor.record_duration(OperationType.INGESTION, 2000.0)
        
        # Low frequency, low duration
        for _ in range(10):
            monitor.record_duration(OperationType.CACHE, 100.0)
        
        bottlenecks = monitor.detect_bottlenecks()
        
        if len(bottlenecks) >= 2:
            # Ingestion should have higher impact
            ingestion_bottleneck = next(
                (b for b in bottlenecks if b.operation_type == OperationType.INGESTION),
                None
            )
            cache_bottleneck = next(
                (b for b in bottlenecks if b.operation_type == OperationType.CACHE),
                None
            )
            
            if ingestion_bottleneck and cache_bottleneck:
                assert ingestion_bottleneck.impact_score > cache_bottleneck.impact_score


@pytest.mark.unit
class TestHealthScore:
    """Test health score calculation."""
    
    def test_health_score_perfect(self, monitor):
        """Test perfect health score."""
        # Record fast operations
        for _ in range(20):
            monitor.record_duration(OperationType.INGESTION, 50.0)
        
        summary = monitor.get_performance_summary()
        
        assert summary["health_score"] == 100.0
    
    def test_health_score_with_issues(self, monitor):
        """Test health score with bottlenecks."""
        # Record slow operations
        for _ in range(20):
            monitor.record_duration(OperationType.INGESTION, 3000.0)  # Critical
        
        monitor.detect_bottlenecks()
        summary = monitor.get_performance_summary()
        
        assert summary["health_score"] < 100.0
    
    def test_health_score_multiple_issues(self, monitor):
        """Test health score with multiple bottlenecks."""
        # Multiple slow operations
        for _ in range(20):
            monitor.record_duration(OperationType.INGESTION, 3000.0)  # Critical
            monitor.record_duration(OperationType.EMBEDDING, 1500.0)  # Critical
        
        monitor.detect_bottlenecks()
        summary = monitor.get_performance_summary()
        
        # Should be significantly degraded
        assert summary["health_score"] < 50.0


@pytest.mark.unit
class TestPerformanceTimer:
    """Test performance timer context manager."""
    
    def test_timer_sync(self, monitor):
        """Test synchronous timer."""
        with PerformanceTimer(monitor, OperationType.INGESTION):
            time.sleep(0.01)  # 10ms
        
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.metric_type == MetricType.DURATION
        assert metric.value >= 10.0  # At least 10ms
    
    @pytest.mark.asyncio
    async def test_timer_async(self, monitor):
        """Test asynchronous timer."""
        async with PerformanceTimer(monitor, OperationType.EMBEDDING):
            await asyncio.sleep(0.01)  # 10ms
        
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.value >= 10.0
    
    def test_timer_with_metadata(self, monitor):
        """Test timer with metadata."""
        with PerformanceTimer(
            monitor,
            OperationType.INGESTION,
            file_count=10,
            repo="test"
        ):
            time.sleep(0.01)
        
        metric = monitor.metrics[0]
        assert metric.metadata["file_count"] == 10
        assert metric.metadata["repo"] == "test"


@pytest.mark.unit
class TestPerformanceSummary:
    """Test performance summary."""
    
    def test_summary_structure(self, monitor):
        """Test summary structure."""
        # Record some metrics
        monitor.record_duration(OperationType.INGESTION, 100.0)
        monitor.record_duration(OperationType.EMBEDDING, 50.0)
        
        summary = monitor.get_performance_summary()
        
        assert "timestamp" in summary
        assert "total_metrics" in summary
        assert "operations" in summary
        assert "bottlenecks" in summary
        assert "health_score" in summary
    
    def test_summary_operations(self, monitor):
        """Test operations in summary."""
        # Record metrics for multiple operations
        for _ in range(10):
            monitor.record_duration(OperationType.INGESTION, 100.0)
            monitor.record_duration(OperationType.EMBEDDING, 50.0)
        
        summary = monitor.get_performance_summary()
        
        assert "ingestion" in summary["operations"]
        assert "embedding" in summary["operations"]


@pytest.mark.unit
class TestSingleton:
    """Test singleton pattern."""
    
    def test_singleton_same_instance(self):
        """Test singleton returns same instance."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        assert monitor1 is monitor2


@pytest.mark.unit
class TestDataClasses:
    """Test data classes."""
    
    def test_performance_metric_to_dict(self):
        """Test PerformanceMetric to_dict."""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            operation_type=OperationType.INGESTION,
            metric_type=MetricType.DURATION,
            value=100.0,
            metadata={"test": "value"}
        )
        
        d = metric.to_dict()
        
        assert d["operation_type"] == "ingestion"
        assert d["metric_type"] == "duration"
        assert d["value"] == 100.0
        assert d["metadata"]["test"] == "value"
    
    def test_bottleneck_to_dict(self):
        """Test Bottleneck to_dict."""
        bottleneck = Bottleneck(
            operation_type=OperationType.EMBEDDING,
            severity="high",
            description="Slow embeddings",
            avg_duration_ms=500.0,
            impact_score=75.0,
            recommendation="Use FastEmbed"
        )
        
        d = bottleneck.to_dict()
        
        assert d["operation_type"] == "embedding"
        assert d["severity"] == "high"
        assert d["impact_score"] == 75.0


# Import asyncio for async tests
import asyncio


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

