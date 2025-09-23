"""
Performance Monitoring and Bottleneck Detection System

Features:
- Real-time performance monitoring
- Bottleneck detection and analysis
- Performance trend analysis
- Resource usage tracking
- Automated optimization recommendations
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Real-time performance metrics."""

    timestamp: datetime = field(default_factory=datetime.now)

    # System metrics
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_bytes: int = 0
    memory_available_bytes: int = 0
    disk_usage_percent: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0

    # Application metrics
    active_connections: int = 0
    request_queue_length: int = 0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    throughput_rps: float = 0.0

    # Cache metrics
    cache_hit_ratio: float = 0.0
    cache_memory_usage: int = 0

    # Database metrics
    db_connections_active: int = 0
    db_query_average_time: float = 0.0
    db_connection_pool_size: int = 0


@dataclass
class BottleneckAnalysis:
    """Analysis of performance bottlenecks."""

    bottleneck_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    impact_score: float  # 0-100
    recommendations: List[str]
    affected_components: List[str]
    detected_at: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.

    Features:
    - Real-time metrics collection
    - Historical trend analysis
    - Performance alerting
    - Resource usage tracking
    - Automated bottleneck detection
    """

    def __init__(self, collection_interval: int = 30, history_size: int = 1000):
        self.collection_interval = collection_interval
        self.history_size = history_size

        # Metrics storage
        self.metrics_history: deque[PerformanceMetrics] = deque(maxlen=history_size)
        self.current_metrics = PerformanceMetrics()

        # Monitoring state
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None

        # Alert thresholds
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "error_rate": 5.0,  # 5%
            "response_time": 2000.0,  # 2 seconds
            "cache_hit_ratio": 70.0,  # 70%
        }

        # Callbacks for external integration
        self.metric_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []

    async def start_monitoring(self):
        """Start performance monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())

        logger.info("Performance monitoring started")

    async def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect metrics
                await self._collect_system_metrics()
                await self._collect_application_metrics()

                # Store metrics
                self.metrics_history.append(self.current_metrics)

                # Check for alerts
                await self._check_alerts()

                # Trigger callbacks
                await self._trigger_metric_callbacks()

                # Wait for next collection
                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry

    async def _collect_system_metrics(self):
        """Collect system-level performance metrics."""
        try:
            # CPU usage
            self.current_metrics.cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            self.current_metrics.memory_percent = memory.percent
            self.current_metrics.memory_used_bytes = memory.used
            self.current_metrics.memory_available_bytes = memory.available

            # Disk usage
            disk = psutil.disk_usage("/")
            self.current_metrics.disk_usage_percent = disk.percent

            # Network I/O
            network = psutil.net_io_counters()
            self.current_metrics.network_bytes_sent = network.bytes_sent
            self.current_metrics.network_bytes_recv = network.bytes_recv

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def _collect_application_metrics(self):
        """Collect application-specific metrics."""
        try:
            # These would be populated by integrating with the application
            # For now, these are placeholders that would be updated by other modules

            # Example integrations:
            # - Get active connections from web server
            # - Get queue length from task queue
            # - Get response times from middleware
            # - Get error rates from error handler
            # - Get cache metrics from cache manager
            # - Get DB metrics from query optimizer

            pass

        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")

    def update_application_metrics(self, metrics: Dict[str, Any]):
        """Update application metrics from external sources."""
        for key, value in metrics.items():
            if hasattr(self.current_metrics, key):
                setattr(self.current_metrics, key, value)

    async def _check_alerts(self):
        """Check for performance alerts."""
        alerts = []

        # CPU usage alert
        if self.current_metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append(
                {
                    "type": "high_cpu_usage",
                    "severity": "warning",
                    "message": ".1f",
                    "threshold": self.alert_thresholds["cpu_percent"],
                }
            )

        # Memory usage alert
        if self.current_metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append(
                {
                    "type": "high_memory_usage",
                    "severity": "warning",
                    "message": ".1f",
                    "threshold": self.alert_thresholds["memory_percent"],
                }
            )

        # Error rate alert
        if self.current_metrics.error_rate > self.alert_thresholds["error_rate"]:
            alerts.append(
                {
                    "type": "high_error_rate",
                    "severity": "critical",
                    "message": ".2f",
                    "threshold": self.alert_thresholds["error_rate"],
                }
            )

        # Response time alert
        if self.current_metrics.average_response_time > self.alert_thresholds["response_time"]:
            alerts.append(
                {
                    "type": "high_response_time",
                    "severity": "warning",
                    "message": ".0f",
                    "threshold": self.alert_thresholds["response_time"],
                }
            )

        # Cache hit ratio alert
        if self.current_metrics.cache_hit_ratio < self.alert_thresholds["cache_hit_ratio"]:
            alerts.append(
                {
                    "type": "low_cache_hit_ratio",
                    "severity": "warning",
                    "message": ".1f",
                    "threshold": self.alert_thresholds["cache_hit_ratio"],
                }
            )

        # Trigger alert callbacks
        for alert in alerts:
            await self._trigger_alert_callbacks(alert)

    async def _trigger_metric_callbacks(self):
        """Trigger metric collection callbacks."""
        for callback in self.metric_callbacks:
            try:
                await callback(self.current_metrics)
            except Exception as e:
                logger.error(f"Error in metric callback: {e}")

    async def _trigger_alert_callbacks(self, alert: Dict[str, Any]):
        """Trigger alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def add_metric_callback(self, callback: Callable):
        """Add a metric collection callback."""
        self.metric_callbacks.append(callback)

    def add_alert_callback(self, callback: Callable):
        """Add an alert callback."""
        self.alert_callbacks.append(callback)

    def set_alert_threshold(self, metric: str, threshold: float):
        """Set alert threshold for a metric."""
        self.alert_thresholds[metric] = threshold

    async def get_performance_report(self, time_range_minutes: int = 60) -> Dict[str, Any]:
        """Generate comprehensive performance report."""

        # Get metrics for time range
        cutoff_time = datetime.now() - timedelta(minutes=time_range_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]

        if not recent_metrics:
            return {"error": "No metrics available for the specified time range"}

        # Calculate averages and trends
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.average_response_time for m in recent_metrics) / len(recent_metrics)
        avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
        avg_throughput = sum(m.throughput_rps for m in recent_metrics) / len(recent_metrics)

        # Calculate trends (comparing first half vs second half)
        midpoint = len(recent_metrics) // 2
        first_half = recent_metrics[:midpoint]
        second_half = recent_metrics[midpoint:]

        if first_half and second_half:
            cpu_trend = (sum(m.cpu_percent for m in second_half) / len(second_half)) - (
                sum(m.cpu_percent for m in first_half) / len(first_half)
            )
            memory_trend = (sum(m.memory_percent for m in second_half) / len(second_half)) - (
                sum(m.memory_percent for m in first_half) / len(first_half)
            )
            response_time_trend = (sum(m.average_response_time for m in second_half) / len(second_half)) - (
                sum(m.average_response_time for m in first_half) / len(first_half)
            )
        else:
            cpu_trend = memory_trend = response_time_trend = 0

        return {
            "time_range_minutes": time_range_minutes,
            "metrics_count": len(recent_metrics),
            "averages": {
                "cpu_percent": avg_cpu,
                "memory_percent": avg_memory,
                "response_time_ms": avg_response_time,
                "error_rate_percent": avg_error_rate,
                "throughput_rps": avg_throughput,
            },
            "trends": {
                "cpu_trend": cpu_trend,
                "memory_trend": memory_trend,
                "response_time_trend": response_time_trend,
            },
            "current_metrics": self.current_metrics.__dict__,
            "alert_thresholds": self.alert_thresholds,
            "collection_interval_seconds": self.collection_interval,
        }


class BottleneckDetector:
    """
    Intelligent bottleneck detection and analysis system.

    Features:
    - Automatic bottleneck identification
    - Root cause analysis
    - Performance optimization recommendations
    - Trend analysis for predictive detection
    """

    def __init__(self, performance_monitor: PerformanceMonitor):
        self.monitor = performance_monitor
        self.bottlenecks: List[BottleneckAnalysis] = []
        self.analysis_history: deque[BottleneckAnalysis] = deque(maxlen=100)

    async def analyze_bottlenecks(self) -> List[BottleneckAnalysis]:
        """Analyze current system for performance bottlenecks."""

        bottlenecks = []
        current_metrics = self.monitor.current_metrics

        # CPU bottleneck detection
        if current_metrics.cpu_percent > 90:
            bottlenecks.append(
                BottleneckAnalysis(
                    bottleneck_type="cpu_saturation",
                    severity="critical",
                    description=".1f",
                    impact_score=95.0,
                    recommendations=[
                        "Scale horizontally by adding more instances",
                        "Optimize CPU-intensive operations",
                        "Consider using async processing for I/O operations",
                        "Review and optimize database queries",
                    ],
                    affected_components=["application", "database"],
                )
            )

        # Memory bottleneck detection
        if current_metrics.memory_percent > 95:
            bottlenecks.append(
                BottleneckAnalysis(
                    bottleneck_type="memory_exhaustion",
                    severity="critical",
                    description=".1f",
                    impact_score=98.0,
                    recommendations=[
                        "Increase instance memory allocation",
                        "Implement memory-efficient data structures",
                        "Add memory monitoring and alerts",
                        "Consider using external caching (Redis)",
                        "Review memory leaks in application code",
                    ],
                    affected_components=["application", "cache"],
                )
            )

        # Database bottleneck detection
        if current_metrics.db_connections_active > 100:
            bottlenecks.append(
                BottleneckAnalysis(
                    bottleneck_type="database_connection_exhaustion",
                    severity="high",
                    description="Database connection pool exhausted",
                    impact_score=85.0,
                    recommendations=[
                        "Increase database connection pool size",
                        "Optimize database queries and add indexes",
                        "Implement query result caching",
                        "Consider read replicas for read-heavy workloads",
                    ],
                    affected_components=["database", "application"],
                )
            )

        # Cache bottleneck detection
        if current_metrics.cache_hit_ratio < 50:
            bottlenecks.append(
                BottleneckAnalysis(
                    bottleneck_type="cache_inefficiency",
                    severity="medium",
                    description=".1f",
                    impact_score=70.0,
                    recommendations=[
                        "Increase cache memory allocation",
                        "Optimize cache key generation",
                        "Implement cache warming strategies",
                        "Review cache TTL settings",
                    ],
                    affected_components=["cache", "application"],
                )
            )

        # Network bottleneck detection
        if current_metrics.average_response_time > 5000:  # 5 seconds
            bottlenecks.append(
                BottleneckAnalysis(
                    bottleneck_type="network_latency",
                    severity="high",
                    description=".0f",
                    impact_score=80.0,
                    recommendations=[
                        "Optimize network configuration",
                        "Implement response compression",
                        "Use CDN for static assets",
                        "Consider geographic distribution",
                    ],
                    affected_components=["network", "cdn"],
                )
            )

        # Store analysis results
        self.bottlenecks = bottlenecks
        for bottleneck in bottlenecks:
            self.analysis_history.append(bottleneck)

        return bottlenecks

    async def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on analysis."""

        recommendations = []
        bottlenecks = await self.analyze_bottlenecks()

        for bottleneck in bottlenecks:
            recommendations.append(
                {
                    "bottleneck_type": bottleneck.bottleneck_type,
                    "severity": bottleneck.severity,
                    "impact_score": bottleneck.impact_score,
                    "recommendations": bottleneck.recommendations,
                    "estimated_effort": self._estimate_effort(bottleneck.bottleneck_type),
                    "expected_improvement": self._estimate_improvement(bottleneck.bottleneck_type),
                }
            )

        # Add general recommendations
        recommendations.extend(self._get_general_recommendations())

        return recommendations

    async def predict_future_bottlenecks(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """Predict potential future bottlenecks based on trends."""

        predictions = []

        # Analyze trends in metrics
        report = await self.monitor.get_performance_report(time_range_minutes=60)

        if "trends" in report:
            trends = report["trends"]

            # Predict CPU bottleneck
            if trends.get("cpu_trend", 0) > 5:  # CPU usage increasing by 5% per hour
                hours_to_bottleneck = (100 - report["averages"]["cpu_percent"]) / trends["cpu_trend"]
                if hours_to_bottleneck < hours_ahead:
                    predictions.append(
                        {
                            "bottleneck_type": "cpu_saturation",
                            "predicted_in_hours": hours_to_bottleneck,
                            "confidence": 0.8,
                            "preventive_actions": ["Scale instances preemptively", "Optimize CPU usage"],
                        }
                    )

            # Predict memory bottleneck
            if trends.get("memory_trend", 0) > 3:
                hours_to_bottleneck = (100 - report["averages"]["memory_percent"]) / trends["memory_trend"]
                if hours_to_bottleneck < hours_ahead:
                    predictions.append(
                        {
                            "bottleneck_type": "memory_exhaustion",
                            "predicted_in_hours": hours_to_bottleneck,
                            "confidence": 0.9,
                            "preventive_actions": ["Increase memory allocation", "Implement memory optimization"],
                        }
                    )

        return predictions

    def _estimate_effort(self, bottleneck_type: str) -> str:
        """Estimate implementation effort for bottleneck fixes."""
        effort_map = {
            "cpu_saturation": "medium",
            "memory_exhaustion": "high",
            "database_connection_exhaustion": "medium",
            "cache_inefficiency": "low",
            "network_latency": "medium",
        }
        return effort_map.get(bottleneck_type, "medium")

    def _estimate_improvement(self, bottleneck_type: str) -> str:
        """Estimate expected performance improvement."""
        improvement_map = {
            "cpu_saturation": "significant",
            "memory_exhaustion": "significant",
            "database_connection_exhaustion": "high",
            "cache_inefficiency": "moderate",
            "network_latency": "high",
        }
        return improvement_map.get(bottleneck_type, "moderate")

    def _get_general_recommendations(self) -> List[Dict[str, Any]]:
        """Get general performance optimization recommendations."""
        return [
            {
                "bottleneck_type": "general_optimization",
                "severity": "low",
                "impact_score": 30.0,
                "recommendations": [
                    "Implement response compression",
                    "Add database query optimization",
                    "Implement multi-level caching",
                    "Use CDN for static assets",
                    "Enable lazy loading for large datasets",
                ],
                "estimated_effort": "medium",
                "expected_improvement": "moderate",
            }
        ]

    async def get_bottleneck_report(self) -> Dict[str, Any]:
        """Generate comprehensive bottleneck analysis report."""

        current_bottlenecks = await self.analyze_bottlenecks()
        recommendations = await self.get_optimization_recommendations()
        predictions = await self.predict_future_bottlenecks()

        return {
            "current_bottlenecks": [
                {
                    "type": b.bottleneck_type,
                    "severity": b.severity,
                    "description": b.description,
                    "impact_score": b.impact_score,
                    "detected_at": b.detected_at.isoformat(),
                }
                for b in current_bottlenecks
            ],
            "optimization_recommendations": recommendations,
            "future_predictions": predictions,
            "analysis_history_count": len(self.analysis_history),
            "most_common_bottleneck": self._get_most_common_bottleneck(),
        }

    def _get_most_common_bottleneck(self) -> Optional[str]:
        """Get the most common bottleneck type."""
        if not self.analysis_history:
            return None

        bottleneck_counts = {}
        for bottleneck in self.analysis_history:
            bottleneck_counts[bottleneck.bottleneck_type] = bottleneck_counts.get(bottleneck.bottleneck_type, 0) + 1

        return max(bottleneck_counts, key=bottleneck_counts.get) if bottleneck_counts else None
