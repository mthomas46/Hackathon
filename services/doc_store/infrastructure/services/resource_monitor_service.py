"""System Resource Monitoring for Doc Store Service.

Provides comprehensive monitoring of CPU, memory, and I/O usage with:
- Real-time resource tracking and alerting
- Performance profiling and bottleneck detection
- Memory leak detection and trend analysis
- Automated optimization recommendations
- Prometheus metrics integration
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from services.shared.infrastructure.monitoring.metrics import ServiceMetrics
from services.shared.infrastructure.utilities.process_monitor_service import (
    ProcessMonitorService,
    ResourceType,
    AlertSeverity,
)

logger = logging.getLogger(__name__)


class DocStoreResourceMonitor:
    """Resource monitor specifically configured for Doc Store service requirements.

    Monitors system resources with Doc Store specific thresholds and provides
    detailed insights into service performance and resource utilization.
    """

    def __init__(self, service_name: str = "doc_store"):
        self.service_name = service_name

        # Initialize shared monitoring components
        self.process_monitor = ProcessMonitorService()
        self.metrics = ServiceMetrics(service_name)

        # Configure Doc Store specific thresholds
        self._configure_doc_store_thresholds()

        # Resource tracking state
        self.monitoring_active = False
        self.last_measurement_time = 0
        self.measurement_interval = 30  # seconds

        # Performance insights
        self.resource_insights: Dict[str, Any] = {
            "peak_memory_usage_mb": 0,
            "average_cpu_percent": 0.0,
            "total_measurements": 0,
            "memory_trend": [],
            "cpu_trend": [],
            "io_operations": [],
        }

    def _configure_doc_store_thresholds(self) -> None:
        """Configure monitoring thresholds specific to Doc Store workloads.

        Doc Store has specific resource requirements due to:
        - Document processing and storage operations
        - Search and indexing workloads
        - API request handling
        - Cache management
        """
        # Memory thresholds (Doc Store is memory-intensive for caching and processing)
        self.process_monitor.set_threshold(
            ResourceType.MEMORY,
            self.process_monitor.resource_thresholds[ResourceType.MEMORY]._replace(
                warning_threshold=300,  # 300MB warning
                critical_threshold=500,  # 500MB critical
                emergency_threshold=800,  # 800MB emergency
                measurement_unit="MB"
            )
        )

        # CPU thresholds (moderate CPU usage for document processing)
        self.process_monitor.set_threshold(
            ResourceType.CPU,
            self.process_monitor.resource_thresholds[ResourceType.CPU]._replace(
                warning_threshold=60.0,  # 60% warning
                critical_threshold=80.0,  # 80% critical
                emergency_threshold=95.0,  # 95% emergency
                measurement_unit="%"
            )
        )

        # File descriptors (Doc Store may have many open files for caching)
        self.process_monitor.set_threshold(
            ResourceType.FILE_DESCRIPTORS,
            self.process_monitor.resource_thresholds[ResourceType.FILE_DESCRIPTORS]._replace(
                warning_threshold=500,  # 500 files warning
                critical_threshold=800,  # 800 files critical
                emergency_threshold=1000,  # 1000 files emergency
                measurement_unit="files"
            )
        )

        # Network connections (API service connections)
        self.process_monitor.set_threshold(
            ResourceType.NETWORK_CONNECTIONS,
            self.process_monitor.resource_thresholds[ResourceType.NETWORK_CONNECTIONS]._replace(
                warning_threshold=100,  # 100 connections warning
                critical_threshold=200,  # 200 connections critical
                emergency_threshold=500,  # 500 connections emergency
                measurement_unit="connections"
            )
        )

    async def start_monitoring(self) -> None:
        """Start comprehensive resource monitoring."""
        if self.monitoring_active:
            return

        logger.info(f"Starting resource monitoring for {self.service_name}")
        self.monitoring_active = True

        # Start background monitoring task
        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        logger.info(f"Stopping resource monitoring for {self.service_name}")
        self.monitoring_active = False

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that collects metrics periodically."""
        while self.monitoring_active:
            try:
                await self._collect_resource_metrics()
                await asyncio.sleep(self.measurement_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def _collect_resource_metrics(self) -> None:
        """Collect comprehensive resource metrics."""
        current_time = time.time()

        # CPU monitoring
        cpu_percent = self.process_monitor.take_measurement(ResourceType.CPU)
        self.metrics.cpu_usage_percent.set(cpu_percent)

        # Memory monitoring
        memory_mb = self.process_monitor.take_measurement(ResourceType.MEMORY)
        self.metrics.memory_usage_bytes.set(memory_mb * 1024 * 1024)  # Convert MB to bytes

        # I/O monitoring
        io_bytes = self.process_monitor.take_measurement(ResourceType.DISK_IO)

        # Update insights
        self._update_resource_insights(cpu_percent, memory_mb, io_bytes, current_time)

        # Check thresholds and generate alerts
        alerts = self.process_monitor.check_thresholds()
        if alerts:
            await self._handle_resource_alerts(alerts)

        # Update Prometheus metrics
        self._update_prometheus_metrics(cpu_percent, memory_mb, io_bytes)

        self.last_measurement_time = current_time

    def _update_resource_insights(
        self,
        cpu_percent: float,
        memory_mb: float,
        io_bytes: int,
        timestamp: float
    ) -> None:
        """Update resource usage insights and trends."""
        # Update peak memory
        if memory_mb > self.resource_insights["peak_memory_usage_mb"]:
            self.resource_insights["peak_memory_usage_mb"] = memory_mb

        # Update CPU average
        total_measurements = self.resource_insights["total_measurements"]
        current_avg = self.resource_insights["average_cpu_percent"]

        new_avg = (current_avg * total_measurements + cpu_percent) / (total_measurements + 1)
        self.resource_insights["average_cpu_percent"] = new_avg

        # Update trends (keep last 100 measurements)
        self.resource_insights["cpu_trend"].append({
            "timestamp": timestamp,
            "value": cpu_percent
        })
        self.resource_insights["memory_trend"].append({
            "timestamp": timestamp,
            "value": memory_mb
        })

        if len(self.resource_insights["cpu_trend"]) > 100:
            self.resource_insights["cpu_trend"].pop(0)
            self.resource_insights["memory_trend"].pop(0)

        # Track I/O operations
        if io_bytes > 0:
            self.resource_insights["io_operations"].append({
                "timestamp": timestamp,
                "bytes": io_bytes
            })

        self.resource_insights["total_measurements"] += 1

    async def _handle_resource_alerts(self, alerts: List[Any]) -> None:
        """Handle resource alerts and log them appropriately."""
        for alert in alerts:
            log_level = logging.INFO
            if alert.severity == AlertSeverity.WARNING:
                log_level = logging.WARNING
            elif alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
                log_level = logging.ERROR

            logger.log(
                log_level,
                f"Resource alert: {alert.message} "
                f"(Current: {alert.current_value:.1f}, "
                f"Threshold: {alert.threshold_value:.1f})"
            )

            # Log recommendations if available
            if hasattr(alert, 'recommendations') and alert.recommendations:
                logger.log(log_level, f"Recommendations: {', '.join(alert.recommendations)}")

    def _update_prometheus_metrics(
        self,
        cpu_percent: float,
        memory_mb: float,
        io_bytes: int
    ) -> None:
        """Update Prometheus metrics with current resource usage."""
        # CPU and memory are already set above
        # Add additional metrics as needed

        # Track I/O if significant
        if io_bytes > 0:
            # Could add custom metrics for I/O tracking
            pass

    def get_resource_status(self) -> Dict[str, Any]:
        """Get comprehensive resource status and insights."""
        current_alerts = self.process_monitor.check_thresholds()

        return {
            "service_name": self.service_name,
            "monitoring_active": self.monitoring_active,
            "current_measurements": {
                "cpu_percent": self.process_monitor.take_measurement(ResourceType.CPU),
                "memory_mb": self.process_monitor.take_measurement(ResourceType.MEMORY),
                "file_descriptors": self.process_monitor.take_measurement(ResourceType.FILE_DESCRIPTORS),
                "network_connections": self.process_monitor.take_measurement(ResourceType.NETWORK_CONNECTIONS),
                "disk_io_bytes": self.process_monitor.take_measurement(ResourceType.DISK_IO),
            },
            "insights": self.resource_insights,
            "active_alerts": [
                {
                    "severity": alert.severity.value,
                    "resource_type": alert.resource_type.value,
                    "message": alert.message,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "recommendations": getattr(alert, 'recommendations', [])
                }
                for alert in current_alerts
            ],
            "last_measurement": self.last_measurement_time,
            "measurement_interval": self.measurement_interval
        }

    def get_performance_recommendations(self) -> List[str]:
        """Get performance optimization recommendations based on resource usage."""
        recommendations = []

        insights = self.resource_insights
        current_cpu = self.process_monitor.take_measurement(ResourceType.CPU)
        current_memory = self.process_monitor.take_measurement(ResourceType.MEMORY)

        # Memory recommendations
        if current_memory > 400:  # High memory usage
            recommendations.append("Consider optimizing cache size or implementing cache eviction policies")
            recommendations.append("Review document processing to reduce memory footprint")

        if insights["peak_memory_usage_mb"] > 600:
            recommendations.append("Implement memory profiling to identify memory leaks")
            recommendations.append("Consider pagination for large document operations")

        # CPU recommendations
        if current_cpu > 70:
            recommendations.append("Optimize document processing algorithms")
            recommendations.append("Consider implementing request queuing for high-load periods")

        if insights["average_cpu_percent"] > 50:
            recommendations.append("Review search and indexing operations for optimization")
            recommendations.append("Consider implementing async processing for CPU-intensive tasks")

        # I/O recommendations
        io_operations = insights["io_operations"]
        if len(io_operations) > 10:  # Frequent I/O
            recommendations.append("Optimize database queries and indexing")
            recommendations.append("Consider implementing read/write caching strategies")

        # General recommendations
        if not recommendations:
            recommendations.append("Resource usage is within normal parameters")
            recommendations.append("Continue monitoring for optimal performance")

        return recommendations

    async def force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection and report memory cleanup."""
        import gc

        # Get memory before GC
        memory_before = self.process_monitor.take_measurement(ResourceType.MEMORY)

        # Force garbage collection
        collected_objects = gc.collect()

        # Get memory after GC
        memory_after = self.process_monitor.take_measurement(ResourceType.MEMORY)
        memory_freed = memory_before - memory_after

        result = {
            "objects_collected": collected_objects,
            "memory_before_mb": memory_before,
            "memory_after_mb": memory_after,
            "memory_freed_mb": memory_freed,
            "gc_cycles": gc.get_count()
        }

        logger.info(f"Garbage collection completed: {result}")
        return result

    def reset_insights(self) -> None:
        """Reset resource insights and trends."""
        self.resource_insights = {
            "peak_memory_usage_mb": 0,
            "average_cpu_percent": 0.0,
            "total_measurements": 0,
            "memory_trend": [],
            "cpu_trend": [],
            "io_operations": [],
        }
        logger.info("Resource insights reset")
