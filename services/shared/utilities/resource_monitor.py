"""Shared resource monitoring utilities for all services."""

import psutil
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_mb: float
    network_connections: int
    open_files: int
    threads_count: int
    timestamp: datetime


class ResourceMonitor:
    """Comprehensive resource monitoring utility."""

    def __init__(self, service_name: str):
        """Initialize resource monitor for a specific service."""
        self.service_name = service_name
        self.start_time = time.time()
        self._baseline_cpu = psutil.cpu_percent(interval=None)
        self._baseline_memory = psutil.virtual_memory()

    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics."""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process-specific metrics if available
        process_metrics = self._get_process_metrics()
        
        return ResourceMetrics(
            cpu_percent=psutil.cpu_percent(interval=None),
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_available_mb=memory.available / 1024 / 1024,
            disk_usage_percent=disk.percent,
            disk_free_mb=disk.free / 1024 / 1024,
            network_connections=len(psutil.net_connections()),
            open_files=process_metrics.get(open_files, 0),
            threads_count=process_metrics.get(threads, 0),
            timestamp=datetime.now(timezone.utc)
        )

    def _get_process_metrics(self) -> Dict[str, Any]:
        """Get process-specific metrics."""
        try:
            # Try to get current process metrics
            process = psutil.Process()
            return {
                open_files: len(process.open_files()),
                threads: process.num_threads(),
                cpu_times: process.cpu_times(),
                memory_info: process.memory_info()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}

    def get_resource_summary(self) -> Dict[str, Any]:
        """Get comprehensive resource usage summary."""
        current = self.get_current_metrics()
        uptime_seconds = time.time() - self.start_time
        
        return {
            service_name: self.service_name,
            uptime_seconds: uptime_seconds,
            current_metrics: {
                cpu_percent: current.cpu_percent,
                memory_percent: current.memory_percent,
                memory_used_mb: current.memory_used_mb,
                disk_usage_percent: current.disk_usage_percent,
                network_connections: current.network_connections,
                threads_count: current.threads_count
            },
            system_info: {
                cpu_count: psutil.cpu_count(),
                cpu_count_logical: psutil.cpu_count(logical=True),
                total_memory_mb: psutil.virtual_memory().total / 1024 / 1024,
                total_disk_mb: psutil.disk_usage('/').total / 1024 / 1024
            },
            health_status: self._assess_health_status(current),
            timestamp: current.timestamp.isoformat()
        }

    def _assess_health_status(self, metrics: ResourceMetrics) -> str:
        """Assess overall health status based on metrics."""
        if metrics.memory_percent > 90 or metrics.cpu_percent > 95:
            return "critical"
        elif metrics.memory_percent > 80 or metrics.cpu_percent > 85:
            return "warning"
        elif metrics.memory_percent > 70 or metrics.cpu_percent > 75:
            return "degraded"
        else:
            return "healthy"

    def monitor_operation(self, operation_name: str):
        """Context manager for monitoring operation resource usage."""
        class OperationMonitor:
            def __init__(self, monitor, op_name):
                self.monitor = monitor
                self.op_name = op_name
                self.start_metrics = None
                self.start_time = None
            
            def __enter__(self):
                self.start_metrics = self.monitor.get_current_metrics()
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                end_time = time.time()
                end_metrics = self.monitor.get_current_metrics()
                
                duration = end_time - self.start_time
                
                # Log operation metrics
                print(f"Operation {self.op_name} completed in {duration:.2f}s")
                print(f"CPU delta: {end_metrics.cpu_percent - self.start_metrics.cpu_percent:.1f}%")
                print(f"Memory delta: {end_metrics.memory_used_mb - self.start_metrics.memory_used_mb:.1f}MB")
        
        return OperationMonitor(self, operation_name)


# Global monitor instances (would be dependency injected in real implementation)
_resource_monitors = {}

def get_resource_monitor(service_name: str) -> ResourceMonitor:
    """Get or create a resource monitor for a service."""
    if service_name not in _resource_monitors:
        _resource_monitors[service_name] = ResourceMonitor(service_name)
    return _resource_monitors[service_name]

def monitor_resources(service_name: str) -> Dict[str, Any]:
    """Get current resource metrics for a service."""
    monitor = get_resource_monitor(service_name)
    return monitor.get_resource_summary()

def monitor_operation(service_name: str, operation_name: str):
    """Monitor resource usage for an operation."""
    monitor = get_resource_monitor(service_name)
    return monitor.monitor_operation(operation_name)

