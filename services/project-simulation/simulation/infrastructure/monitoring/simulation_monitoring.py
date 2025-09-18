"""Simulation Monitoring - Extended Monitoring Infrastructure for Project Simulation Service.

This module extends the services/shared/monitoring/ infrastructure with comprehensive
simulation-specific metrics collection, performance monitoring, and alerting capabilities.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
import asyncio
import threading
import time
from dataclasses import dataclass
from enum import Enum

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.domain.value_objects import SimulationStatus, ProjectType, ComplexityLevel

# Import shared monitoring (with fallbacks)
try:
    from shared.monitoring.metrics import MetricsCollector, MetricType, MetricConfig
    from shared.monitoring.alerts import AlertManager, AlertLevel, AlertRule
    from shared.monitoring.health import HealthMonitor, HealthIndicator
except ImportError:
    # Fallback implementations
    class MetricType(str, Enum):
        COUNTER = "counter"
        GAUGE = "gauge"
        HISTOGRAM = "histogram"
        SUMMARY = "summary"

    @dataclass
    class MetricConfig:
        name: str
        type: MetricType
        description: str
        labels: List[str] = None

    class MetricsCollector:
        def __init__(self):
            self.metrics = {}

        def create_metric(self, config: MetricConfig):
            self.metrics[config.name] = {"config": config, "values": []}

        def record_metric(self, name: str, value: Union[int, float], labels: Dict[str, str] = None):
            if name in self.metrics:
                self.metrics[name]["values"].append({
                    "value": value,
                    "labels": labels or {},
                    "timestamp": datetime.now()
                })

        def get_metric_value(self, name: str, labels: Dict[str, str] = None) -> Optional[float]:
            if name not in self.metrics:
                return None
            values = self.metrics[name]["values"]
            if not values:
                return None
            return values[-1]["value"]

    class AlertLevel(str, Enum):
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"

    @dataclass
    class AlertRule:
        name: str
        condition: Callable[[Dict[str, Any]], bool]
        level: AlertLevel
        message: str
        cooldown_seconds: int = 300

    class AlertManager:
        def __init__(self):
            self.alerts = []
            self.rules = []

        def add_rule(self, rule: AlertRule):
            self.rules.append(rule)

        def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
            triggered_alerts = []
            for rule in self.rules:
                if rule.condition(metrics):
                    triggered_alerts.append({
                        "rule": rule.name,
                        "level": rule.level,
                        "message": rule.message,
                        "timestamp": datetime.now()
                    })
            return triggered_alerts

    class HealthIndicator:
        def __init__(self, name: str):
            self.name = name
            self.status = "healthy"
            self.last_check = datetime.now()

        def update_status(self, status: str):
            self.status = status
            self.last_check = datetime.now()

    class HealthMonitor:
        def __init__(self):
            self.indicators = {}

        def add_indicator(self, name: str) -> HealthIndicator:
            indicator = HealthIndicator(name)
            self.indicators[name] = indicator
            return indicator

        def get_indicator(self, name: str) -> Optional[HealthIndicator]:
            return self.indicators.get(name)


class SimulationMetricsCollector(MetricsCollector):
    """Extended metrics collector for simulation-specific metrics."""

    def __init__(self):
        super().__init__()
        self.logger = get_simulation_logger()
        self._initialize_simulation_metrics()

    def _initialize_simulation_metrics(self):
        """Initialize simulation-specific metrics."""
        simulation_metrics = [
            MetricConfig(
                name="simulation_active_count",
                type=MetricType.GAUGE,
                description="Number of currently active simulations",
                labels=["project_type", "complexity"]
            ),
            MetricConfig(
                name="simulation_completed_total",
                type=MetricType.COUNTER,
                description="Total number of completed simulations",
                labels=["project_type", "complexity", "status"]
            ),
            MetricConfig(
                name="simulation_duration_seconds",
                type=MetricType.HISTOGRAM,
                description="Duration of simulation execution",
                labels=["project_type", "complexity"]
            ),
            MetricConfig(
                name="simulation_success_rate",
                type=MetricType.GAUGE,
                description="Simulation success rate percentage",
                labels=["project_type", "complexity"]
            ),
            MetricConfig(
                name="document_generation_count",
                type=MetricType.COUNTER,
                description="Number of documents generated",
                labels=["document_type", "simulation_id"]
            ),
            MetricConfig(
                name="ecosystem_service_calls",
                type=MetricType.COUNTER,
                description="Number of calls to ecosystem services",
                labels=["service_name", "operation"]
            ),
            MetricConfig(
                name="ecosystem_service_response_time",
                type=MetricType.HISTOGRAM,
                description="Response time for ecosystem service calls",
                labels=["service_name", "operation"]
            ),
            MetricConfig(
                name="simulation_queue_depth",
                type=MetricType.GAUGE,
                description="Number of simulations waiting in queue"
            ),
            MetricConfig(
                name="memory_usage_mb",
                type=MetricType.GAUGE,
                description="Current memory usage in MB"
            ),
            MetricConfig(
                name="cpu_usage_percent",
                type=MetricType.GAUGE,
                description="Current CPU usage percentage"
            ),
            MetricConfig(
                name="phase_completion_rate",
                type=MetricType.GAUGE,
                description="Phase completion rate",
                labels=["phase_name", "simulation_id"]
            ),
            MetricConfig(
                name="quality_score_average",
                type=MetricType.GAUGE,
                description="Average quality score of generated content",
                labels=["content_type"]
            ),
            MetricConfig(
                name="error_rate_percent",
                type=MetricType.GAUGE,
                description="Error rate percentage for operations",
                labels=["operation_type"]
            )
        ]

        for metric_config in simulation_metrics:
            self.create_metric(metric_config)

    def record_simulation_start(self, simulation_id: str, project_type: str, complexity: str):
        """Record simulation start event."""
        current_active = self.get_metric_value("simulation_active_count", {"project_type": project_type, "complexity": complexity}) or 0
        self.record_metric(
            "simulation_active_count",
            current_active + 1,
            {"project_type": project_type, "complexity": complexity}
        )
        self.logger.info("Recorded simulation start", simulation_id=simulation_id)

    def record_simulation_completion(self, simulation_id: str, project_type: str, complexity: str,
                                   status: str, duration_seconds: float):
        """Record simulation completion event."""
        # Update active count
        current_active = self.get_metric_value("simulation_active_count", {"project_type": project_type, "complexity": complexity}) or 0
        self.record_metric(
            "simulation_active_count",
            max(0, current_active - 1),
            {"project_type": project_type, "complexity": complexity}
        )

        # Record completion
        self.record_metric(
            "simulation_completed_total",
            1,
            {"project_type": project_type, "complexity": complexity, "status": status}
        )

        # Record duration
        self.record_metric(
            "simulation_duration_seconds",
            duration_seconds,
            {"project_type": project_type, "complexity": complexity}
        )

        self.logger.info("Recorded simulation completion", simulation_id=simulation_id, duration=duration_seconds)

    def record_document_generation(self, simulation_id: str, document_type: str, count: int = 1):
        """Record document generation event."""
        self.record_metric(
            "document_generation_count",
            count,
            {"document_type": document_type, "simulation_id": simulation_id}
        )

    def record_ecosystem_service_call(self, service_name: str, operation: str, response_time: float):
        """Record ecosystem service call."""
        self.record_metric("ecosystem_service_calls", 1, {"service_name": service_name, "operation": operation})
        self.record_metric("ecosystem_service_response_time", response_time, {"service_name": service_name, "operation": operation})

    def update_simulation_success_rate(self, project_type: str, complexity: str, success_rate: float):
        """Update simulation success rate."""
        self.record_metric(
            "simulation_success_rate",
            success_rate,
            {"project_type": project_type, "complexity": complexity}
        )

    def update_queue_depth(self, depth: int):
        """Update simulation queue depth."""
        self.record_metric("simulation_queue_depth", depth)

    def record_system_metrics(self, memory_mb: float, cpu_percent: float):
        """Record system resource metrics."""
        self.record_metric("memory_usage_mb", memory_mb)
        self.record_metric("cpu_usage_percent", cpu_percent)

    def record_phase_completion(self, simulation_id: str, phase_name: str, completion_rate: float):
        """Record phase completion rate."""
        self.record_metric(
            "phase_completion_rate",
            completion_rate,
            {"phase_name": phase_name, "simulation_id": simulation_id}
        )

    def record_quality_score(self, content_type: str, score: float):
        """Record content quality score."""
        self.record_metric("quality_score_average", score, {"content_type": content_type})

    def record_error_rate(self, operation_type: str, error_rate: float):
        """Record error rate for operations."""
        self.record_metric("error_rate_percent", error_rate, {"operation_type": operation_type})


class SimulationAlertManager(AlertManager):
    """Extended alert manager for simulation-specific alerts."""

    def __init__(self):
        super().__init__()
        self._initialize_simulation_alerts()

    def _initialize_simulation_alerts(self):
        """Initialize simulation-specific alert rules."""

        # High error rate alert
        self.add_rule(AlertRule(
            name="high_error_rate",
            condition=lambda metrics: self._check_error_rate(metrics, "simulation", 10.0),
            level=AlertLevel.ERROR,
            message="Simulation error rate exceeds 10%",
            cooldown_seconds=300
        ))

        # Simulation queue depth alert
        self.add_rule(AlertRule(
            name="simulation_queue_overflow",
            condition=lambda metrics: self._check_queue_depth(metrics, 20),
            level=AlertLevel.WARNING,
            message="Simulation queue depth exceeds 20",
            cooldown_seconds=600
        ))

        # Low success rate alert
        self.add_rule(AlertRule(
            name="low_success_rate",
            condition=lambda metrics: self._check_success_rate(metrics, 70.0),
            level=AlertLevel.WARNING,
            message="Simulation success rate below 70%",
            cooldown_seconds=600
        ))

        # High memory usage alert
        self.add_rule(AlertRule(
            name="high_memory_usage",
            condition=lambda metrics: self._check_memory_usage(metrics, 80.0),
            level=AlertLevel.WARNING,
            message="Memory usage exceeds 80%",
            cooldown_seconds=300
        ))

        # Ecosystem service failure alert
        self.add_rule(AlertRule(
            name="ecosystem_service_failure",
            condition=lambda metrics: self._check_service_failures(metrics, 5),
            level=AlertLevel.CRITICAL,
            message="Multiple ecosystem service failures detected",
            cooldown_seconds=300
        ))

    def _check_error_rate(self, metrics: Dict[str, Any], operation_type: str, threshold: float) -> bool:
        """Check if error rate exceeds threshold."""
        error_rate = metrics.get("error_rate_percent", {}).get(operation_type, 0)
        return error_rate > threshold

    def _check_queue_depth(self, metrics: Dict[str, Any], threshold: int) -> bool:
        """Check if queue depth exceeds threshold."""
        queue_depth = metrics.get("simulation_queue_depth", 0)
        return queue_depth > threshold

    def _check_success_rate(self, metrics: Dict[str, Any], threshold: float) -> bool:
        """Check if success rate is below threshold."""
        success_rate = metrics.get("simulation_success_rate", 100.0)
        return success_rate < threshold

    def _check_memory_usage(self, metrics: Dict[str, Any], threshold: float) -> bool:
        """Check if memory usage exceeds threshold."""
        memory_usage = metrics.get("memory_usage_mb", 0)
        # Assume 1GB threshold for percentage calculation
        memory_percent = (memory_usage / 1024) * 100
        return memory_percent > threshold

    def _check_service_failures(self, metrics: Dict[str, Any], threshold: int) -> bool:
        """Check for multiple ecosystem service failures."""
        service_failures = 0
        for service_name, calls in metrics.get("ecosystem_service_calls", {}).items():
            # Simplified failure detection - in real implementation would check response codes
            if calls > 10:  # High call volume might indicate retry loops
                service_failures += 1
        return service_failures >= threshold


class SimulationHealthMonitor(HealthMonitor):
    """Extended health monitor for simulation service health indicators."""

    def __init__(self):
        super().__init__()
        self._initialize_simulation_health_indicators()

    def _initialize_simulation_health_indicators(self):
        """Initialize simulation-specific health indicators."""

        # Core simulation health
        self.add_indicator("simulation_engine")
        self.add_indicator("database_connection")
        self.add_indicator("ecosystem_services")

        # Performance indicators
        self.add_indicator("memory_usage")
        self.add_indicator("cpu_usage")
        self.add_indicator("queue_health")

        # Service integration indicators
        self.add_indicator("mock_data_generator")
        self.add_indicator("doc_store")
        self.add_indicator("analysis_service")
        self.add_indicator("llm_gateway")

    def update_simulation_health(self, active_simulations: int, queue_depth: int, error_rate: float):
        """Update simulation engine health based on operational metrics."""
        indicator = self.get_indicator("simulation_engine")

        if error_rate > 20:
            indicator.update_status("unhealthy")
        elif queue_depth > 50 or active_simulations > 100:
            indicator.update_status("degraded")
        else:
            indicator.update_status("healthy")

    def update_service_health(self, service_name: str, is_healthy: bool, response_time: Optional[float] = None):
        """Update ecosystem service health."""
        indicator = self.get_indicator(service_name)

        if indicator:
            if not is_healthy:
                indicator.update_status("unhealthy")
            elif response_time and response_time > 5.0:  # 5 second threshold
                indicator.update_status("degraded")
            else:
                indicator.update_status("healthy")

    def get_overall_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        total_indicators = len(self.indicators)
        healthy_count = sum(1 for ind in self.indicators.values() if ind.status == "healthy")
        degraded_count = sum(1 for ind in self.indicators.values() if ind.status == "degraded")
        unhealthy_count = sum(1 for ind in self.indicators.values() if ind.status == "unhealthy")

        # Calculate overall status
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        health_score = (healthy_count / total_indicators) * 100 if total_indicators > 0 else 0

        return {
            "overall_status": overall_status,
            "health_score": health_score,
            "indicators": {
                "total": total_indicators,
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count
            },
            "timestamp": datetime.now(),
            "details": {name: {"status": ind.status, "last_check": ind.last_check}
                       for name, ind in self.indicators.items()}
        }


class SimulationMonitoringService:
    """Comprehensive monitoring service for the simulation system."""

    def __init__(self):
        """Initialize the simulation monitoring service."""
        self.logger = get_simulation_logger()
        self.metrics_collector = SimulationMetricsCollector()
        self.alert_manager = SimulationAlertManager()
        self.health_monitor = SimulationHealthMonitor()

        # Monitoring state
        self._monitoring_active = False
        self._collection_interval = 30  # seconds
        self._monitoring_thread = None

    def start_monitoring(self):
        """Start the monitoring service."""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()

        self.logger.info("Simulation monitoring service started")

    def stop_monitoring(self):
        """Stop the monitoring service."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)

        self.logger.info("Simulation monitoring service stopped")

    def record_simulation_event(self, event_type: str, simulation_id: str, **kwargs):
        """Record a simulation event for monitoring."""
        try:
            if event_type == "simulation_started":
                self.metrics_collector.record_simulation_start(
                    simulation_id,
                    kwargs.get("project_type", "unknown"),
                    kwargs.get("complexity", "unknown")
                )

            elif event_type == "simulation_completed":
                self.metrics_collector.record_simulation_completion(
                    simulation_id,
                    kwargs.get("project_type", "unknown"),
                    kwargs.get("complexity", "unknown"),
                    kwargs.get("status", "unknown"),
                    kwargs.get("duration_seconds", 0)
                )

            elif event_type == "document_generated":
                self.metrics_collector.record_document_generation(
                    simulation_id,
                    kwargs.get("document_type", "unknown"),
                    kwargs.get("count", 1)
                )

            elif event_type == "ecosystem_service_call":
                self.metrics_collector.record_ecosystem_service_call(
                    kwargs.get("service_name", "unknown"),
                    kwargs.get("operation", "unknown"),
                    kwargs.get("response_time", 0)
                )

        except Exception as e:
            self.logger.error("Failed to record simulation event", error=str(e), event_type=event_type)

    def get_monitoring_snapshot(self) -> Dict[str, Any]:
        """Get a comprehensive monitoring snapshot."""
        return {
            "timestamp": datetime.now(),
            "metrics": self._get_current_metrics(),
            "health": self.health_monitor.get_overall_health_status(),
            "alerts": self.alert_manager.check_alerts(self._get_current_metrics()),
            "performance_summary": self._get_performance_summary()
        }

    def _monitoring_loop(self):
        """Main monitoring collection loop."""
        while self._monitoring_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()

                # Check for alerts
                current_metrics = self._get_current_metrics()
                alerts = self.alert_manager.check_alerts(current_metrics)

                if alerts:
                    for alert in alerts:
                        self.logger.warning(
                            "Monitoring alert triggered",
                            alert_name=alert["rule"],
                            level=alert["level"],
                            message=alert["message"]
                        )

                # Sleep until next collection
                time.sleep(self._collection_interval)

            except Exception as e:
                self.logger.error("Error in monitoring loop", error=str(e))
                time.sleep(5)  # Brief pause before retry

    def _collect_system_metrics(self):
        """Collect system resource metrics."""
        try:
            # Memory usage (simplified - in production would use psutil)
            memory_mb = 256  # Placeholder
            cpu_percent = 45  # Placeholder

            self.metrics_collector.record_system_metrics(memory_mb, cpu_percent)

            # Update health indicators
            self.health_monitor.update_simulation_health(5, 2, 3.5)  # Sample values

        except Exception as e:
            self.logger.error("Failed to collect system metrics", error=str(e))

    def _get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        return {
            "simulation_active_count": self.metrics_collector.get_metric_value("simulation_active_count"),
            "simulation_success_rate": self.metrics_collector.get_metric_value("simulation_success_rate"),
            "simulation_queue_depth": self.metrics_collector.get_metric_value("simulation_queue_depth"),
            "memory_usage_mb": self.metrics_collector.get_metric_value("memory_usage_mb"),
            "cpu_usage_percent": self.metrics_collector.get_metric_value("cpu_usage_percent"),
            "error_rate_percent": self.metrics_collector.get_metric_value("error_rate_percent"),
            "ecosystem_service_calls": {}  # Would be populated from actual metrics
        }

    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary metrics."""
        return {
            "average_response_time": self.metrics_collector.get_metric_value("ecosystem_service_response_time"),
            "total_simulations_completed": self.metrics_collector.get_metric_value("simulation_completed_total"),
            "current_active_simulations": self.metrics_collector.get_metric_value("simulation_active_count"),
            "average_simulation_duration": self.metrics_collector.get_metric_value("simulation_duration_seconds")
        }


# Global monitoring service instance
_simulation_monitoring_service: Optional[SimulationMonitoringService] = None


def get_simulation_monitoring_service() -> SimulationMonitoringService:
    """Get the global simulation monitoring service instance."""
    global _simulation_monitoring_service
    if _simulation_monitoring_service is None:
        _simulation_monitoring_service = SimulationMonitoringService()
    return _simulation_monitoring_service


__all__ = [
    'SimulationMetricsCollector',
    'SimulationAlertManager',
    'SimulationHealthMonitor',
    'SimulationMonitoringService',
    'get_simulation_monitoring_service'
]
