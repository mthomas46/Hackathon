#!/usr/bin/env python3
"""
Operational Excellence Framework

This module provides comprehensive health monitoring, automated service discovery,
and real-time performance dashboards for operational excellence.
"""

import asyncio
import json
import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from aiohttp import web
import redis.asyncio as redis
# from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry  # Optional for metrics collection
import socket
import subprocess

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from services.shared.intelligent_caching import get_cache_metrics
from services.shared.enterprise_error_handling import enterprise_error_handler
from services.shared.enterprise_integration import service_registry


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceRole(Enum):
    """Service role enumeration."""
    CORE = "core"
    SUPPORTING = "supporting"
    INFRASTRUCTURE = "infrastructure"
    MONITORING = "monitoring"


@dataclass
class ServiceHealth:
    """Service health information."""
    service_name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: datetime = field(default_factory=datetime.now)
    response_time_ms: Optional[float] = None
    uptime_seconds: int = 0
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    error_count: int = 0
    request_count: int = 0
    health_checks: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'service_name': self.service_name,
            'status': self.status.value,
            'last_check': self.last_check.isoformat(),
            'response_time_ms': self.response_time_ms,
            'uptime_seconds': self.uptime_seconds,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'error_count': self.error_count,
            'request_count': self.request_count,
            'health_checks': self.health_checks,
            'dependencies': self.dependencies,
            'metadata': self.metadata
        }


@dataclass
class SystemMetrics:
    """System-wide metrics."""
    total_services: int = 0
    healthy_services: int = 0
    degraded_services: int = 0
    unhealthy_services: int = 0
    total_requests: int = 0
    total_errors: int = 0
    average_response_time_ms: float = 0.0
    system_memory_usage_percent: float = 0.0
    system_cpu_usage_percent: float = 0.0
    network_traffic_mbps: float = 0.0
    disk_usage_percent: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total_services': self.total_services,
            'healthy_services': self.healthy_services,
            'degraded_services': self.degraded_services,
            'unhealthy_services': self.unhealthy_services,
            'total_requests': self.total_requests,
            'total_errors': self.total_errors,
            'average_response_time_ms': self.average_response_time_ms,
            'system_memory_usage_percent': self.system_memory_usage_percent,
            'system_cpu_usage_percent': self.system_cpu_usage_percent,
            'network_traffic_mbps': self.network_traffic_mbps,
            'disk_usage_percent': self.disk_usage_percent,
            'timestamp': self.timestamp.isoformat()
        }


class HealthMonitor:
    """Comprehensive health monitoring system."""

    def __init__(self):
        self.services_health: Dict[str, ServiceHealth] = {}
        self.system_metrics = SystemMetrics()
        self.health_check_interval = 30  # seconds
        self.metrics_interval = 15  # seconds
        self.alert_thresholds = {
            'response_time_ms': 5000,  # 5 seconds
            'error_rate_percent': 5.0,  # 5%
            'memory_usage_percent': 85.0,  # 85%
            'cpu_usage_percent': 90.0,  # 90%
            'disk_usage_percent': 90.0  # 90%
        }
        self.alerts: List[Dict[str, Any]] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None

    async def start_monitoring(self):
        """Start health monitoring."""
        self._monitoring_task = asyncio.create_task(self._health_check_loop())
        self._metrics_task = asyncio.create_task(self._metrics_collection_loop())

        fire_and_forget("info", "Health monitoring started", "health_monitor")

    async def stop_monitoring(self):
        """Stop health monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
        if self._metrics_task:
            self._metrics_task.cancel()

        fire_and_forget("info", "Health monitoring stopped", "health_monitor")

    async def register_service(self, service_name: str, endpoint: str,
                             dependencies: Optional[List[str]] = None,
                             role: ServiceRole = ServiceRole.CORE):
        """Register a service for health monitoring."""
        health_info = ServiceHealth(
            service_name=service_name,
            dependencies=dependencies or [],
            metadata={
                'endpoint': endpoint,
                'role': role.value,
                'registered_at': datetime.now().isoformat()
            }
        )

        self.services_health[service_name] = health_info

        # Register with service registry
        await service_registry.register_service(
            service_name,
            {'health_endpoint': f"{endpoint}/health"},
            {'role': role.value, 'monitored': True}
        )

        fire_and_forget("info", f"Service {service_name} registered for health monitoring", "health_monitor")

    async def _health_check_loop(self):
        """Continuous health check loop."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                # Check all registered services
                for service_name, health_info in self.services_health.items():
                    await self._check_service_health(service_name, health_info)

                # Update system-wide health status
                await self._update_system_health_status()

                # Check for alerts
                await self._check_alerts()

            except Exception as e:
                fire_and_forget("error", f"Health check loop error: {e}", "health_monitor")

    async def _check_service_health(self, service_name: str, health_info: ServiceHealth):
        """Check health of a specific service."""
        endpoint = health_info.metadata.get('endpoint')
        if not endpoint:
            return

        start_time = time.time()

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{endpoint}/health") as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        health_data = await response.json()

                        # Update health information
                        health_info.status = HealthStatus.HEALTHY
                        health_info.response_time_ms = response_time
                        health_info.last_check = datetime.now()
                        health_info.health_checks = health_data

                        # Update resource usage if available
                        if 'memory_mb' in health_data:
                            health_info.memory_usage_mb = health_data['memory_mb']
                        if 'cpu_percent' in health_data:
                            health_info.cpu_usage_percent = health_data['cpu_percent']

                    else:
                        health_info.status = HealthStatus.UNHEALTHY
                        health_info.response_time_ms = response_time
                        health_info.last_check = datetime.now()
                        health_info.error_count += 1

        except Exception as e:
            health_info.status = HealthStatus.UNHEALTHY
            health_info.response_time_ms = (time.time() - start_time) * 1000
            health_info.last_check = datetime.now()
            health_info.error_count += 1

            fire_and_forget("warning", f"Health check failed for {service_name}: {e}", "health_monitor")

        # Update uptime
        registered_at = datetime.fromisoformat(health_info.metadata.get('registered_at', datetime.now().isoformat()))
        health_info.uptime_seconds = int((datetime.now() - registered_at).total_seconds())

    async def _update_system_health_status(self):
        """Update system-wide health metrics."""
        total_services = len(self.services_health)
        healthy_count = sum(1 for h in self.services_health.values() if h.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for h in self.services_health.values() if h.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for h in self.services_health.values() if h.status == HealthStatus.UNHEALTHY)

        # Calculate system metrics
        total_requests = sum(h.request_count for h in self.services_health.values())
        total_errors = sum(h.error_count for h in self.services_health.values())
        response_times = [h.response_time_ms for h in self.services_health.values() if h.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        self.system_metrics = SystemMetrics(
            total_services=total_services,
            healthy_services=healthy_count,
            degraded_services=degraded_count,
            unhealthy_services=unhealthy_count,
            total_requests=total_requests,
            total_errors=total_errors,
            average_response_time_ms=avg_response_time,
            system_memory_usage_percent=psutil.virtual_memory().percent,
            system_cpu_usage_percent=psutil.cpu_percent(interval=1),
            disk_usage_percent=psutil.disk_usage('/').percent
        )

    async def _check_alerts(self):
        """Check for system alerts based on thresholds."""
        alerts = []

        # Service health alerts
        for service_name, health_info in self.services_health.items():
            if health_info.status == HealthStatus.UNHEALTHY:
                alerts.append({
                    'type': 'service_unhealthy',
                    'severity': 'critical',
                    'service': service_name,
                    'message': f'Service {service_name} is unhealthy',
                    'timestamp': datetime.now().isoformat()
                })

            # Response time alert
            if (health_info.response_time_ms and
                health_info.response_time_ms > self.alert_thresholds['response_time_ms']):
                alerts.append({
                    'type': 'high_response_time',
                    'severity': 'warning',
                    'service': service_name,
                    'value': health_info.response_time_ms,
                    'threshold': self.alert_thresholds['response_time_ms'],
                    'timestamp': datetime.now().isoformat()
                })

        # System resource alerts
        if self.system_metrics.system_memory_usage_percent > self.alert_thresholds['memory_usage_percent']:
            alerts.append({
                'type': 'high_memory_usage',
                'severity': 'warning',
                'value': self.system_metrics.system_memory_usage_percent,
                'threshold': self.alert_thresholds['memory_usage_percent'],
                'timestamp': datetime.now().isoformat()
            })

        if self.system_metrics.system_cpu_usage_percent > self.alert_thresholds['cpu_usage_percent']:
            alerts.append({
                'type': 'high_cpu_usage',
                'severity': 'warning',
                'value': self.system_metrics.system_cpu_usage_percent,
                'threshold': self.alert_thresholds['cpu_usage_percent'],
                'timestamp': datetime.now().isoformat()
            })

        # Store alerts
        self.alerts.extend(alerts)

        # Keep only recent alerts (last 1000)
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]

        # Fire alerts
        for alert in alerts:
            severity = alert.get('severity', 'info')
            if severity in ['warning', 'critical']:
                fire_and_forget(severity, alert['message'], "health_monitor")

    async def _metrics_collection_loop(self):
        """Continuous metrics collection loop."""
        while True:
            try:
                await asyncio.sleep(self.metrics_interval)

                # Collect detailed system metrics
                await self._collect_detailed_metrics()

                # Store metrics history
                await self._store_metrics_history()

            except Exception as e:
                fire_and_forget("error", f"Metrics collection error: {e}", "health_monitor")

    async def _collect_detailed_metrics(self):
        """Collect detailed system and service metrics."""
        # Update system metrics with more detail
        network_stats = psutil.net_io_counters()
        self.system_metrics.network_traffic_mbps = (
            (network_stats.bytes_sent + network_stats.bytes_recv) / (1024 * 1024)
        )  # Simplified calculation

        # Collect per-service detailed metrics
        for service_name, health_info in self.services_health.items():
            # Update request count from error handler if available
            error_stats = enterprise_error_handler.get_error_statistics(service_name)
            if error_stats.get('services', {}).get(service_name):
                service_stats = error_stats['services'][service_name]
                health_info.error_count = service_stats.get('total_errors', 0)
                health_info.request_count = health_info.error_count * 10  # Estimate based on error rate

    async def _store_metrics_history(self):
        """Store metrics history for trend analysis."""
        # This would typically store to a time-series database
        # For now, we'll just log significant changes
        if self.system_metrics.system_memory_usage_percent > 80:
            fire_and_forget("warning", f"High system memory usage: {self.system_metrics.system_memory_usage_percent}%", "health_monitor")

        if self.system_metrics.system_cpu_usage_percent > 80:
            fire_and_forget("warning", f"High system CPU usage: {self.system_metrics.system_cpu_usage_percent}%", "health_monitor")

    def get_health_status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get health status for service(s)."""
        if service_name:
            health_info = self.services_health.get(service_name)
            if health_info:
                return health_info.to_dict()
            return {'error': f'Service {service_name} not found'}

        # Return all services health
        return {
            'services': {name: health.to_dict() for name, health in self.services_health.items()},
            'system': self.system_metrics.to_dict(),
            'alerts': self.alerts[-10:],  # Last 10 alerts
            'timestamp': datetime.now().isoformat()
        }

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data."""
        cache_metrics = get_cache_metrics()

        dashboard = {
            'system_overview': self.system_metrics.to_dict(),
            'service_health': {
                name: {
                    'status': health.status.value,
                    'response_time_ms': health.response_time_ms,
                    'uptime_seconds': health.uptime_seconds,
                    'error_rate': (health.error_count / max(health.request_count, 1)) * 100,
                    'memory_usage_mb': health.memory_usage_mb,
                    'cpu_usage_percent': health.cpu_usage_percent
                }
                for name, health in self.services_health.items()
            },
            'cache_performance': cache_metrics,
            'error_summary': enterprise_error_handler.get_error_statistics(),
            'alert_summary': {
                'total_alerts': len(self.alerts),
                'critical_alerts': len([a for a in self.alerts if a.get('severity') == 'critical']),
                'warning_alerts': len([a for a in self.alerts if a.get('severity') == 'warning']),
                'recent_alerts': self.alerts[-5:]
            },
            'performance_trends': {
                'average_response_time_trend': [],  # Would be populated with historical data
                'error_rate_trend': [],
                'resource_usage_trend': []
            },
            'generated_at': datetime.now().isoformat()
        }

        return dashboard


class ServiceDiscovery:
    """Automated service discovery system."""

    def __init__(self):
        self.discovered_services: Dict[str, Dict[str, Any]] = {}
        self.discovery_methods: List[Callable] = []
        self.discovery_interval = 60  # seconds
        self._discovery_task: Optional[asyncio.Task] = None

    async def start_discovery(self):
        """Start automated service discovery."""
        self._setup_discovery_methods()
        self._discovery_task = asyncio.create_task(self._discovery_loop())

        fire_and_forget("info", "Service discovery started", "service_discovery")

    async def stop_discovery(self):
        """Stop automated service discovery."""
        if self._discovery_task:
            self._discovery_task.cancel()

        fire_and_forget("info", "Service discovery stopped", "service_discovery")

    def _setup_discovery_methods(self):
        """Setup service discovery methods."""
        self.discovery_methods = [
            self._discover_via_dns,
            self._discover_via_environment,
            self._discover_via_configuration,
            self._discover_via_docker_network
        ]

    async def _discovery_loop(self):
        """Continuous service discovery loop."""
        while True:
            try:
                await asyncio.sleep(self.discovery_interval)

                for discovery_method in self.discovery_methods:
                    try:
                        discovered = await discovery_method()
                        await self._process_discovered_services(discovered)
                    except Exception as e:
                        fire_and_forget("warning", f"Discovery method failed: {e}", "service_discovery")

                # Update service registry
                await self._update_service_registry()

            except Exception as e:
                fire_and_forget("error", f"Service discovery loop error: {e}", "service_discovery")

    async def _discover_via_dns(self) -> Dict[str, Dict[str, Any]]:
        """Discover services via DNS."""
        discovered = {}
        service_names = [s.value for s in ServiceNames]

        for service_name in service_names:
            try:
                # Try to resolve service DNS
                addr_info = socket.getaddrinfo(f"{service_name}", 8000, socket.AF_INET, socket.SOCK_STREAM)
                if addr_info:
                    ip_address = addr_info[0][4][0]
                    discovered[service_name] = {
                        'endpoint': f"http://{ip_address}:8000",
                        'discovery_method': 'dns',
                        'discovered_at': datetime.now().isoformat()
                    }
            except socket.gaierror:
                continue

        return discovered

    async def _discover_via_environment(self) -> Dict[str, Dict[str, Any]]:
        """Discover services via environment variables."""
        discovered = {}
        service_names = [s.value for s in ServiceNames]

        for service_name in service_names:
            env_var = f"{service_name.upper().replace('-', '_')}_URL"
            service_url = os.getenv(env_var)

            if service_url:
                discovered[service_name] = {
                    'endpoint': service_url,
                    'discovery_method': 'environment',
                    'discovered_at': datetime.now().isoformat()
                }

        return discovered

    async def _discover_via_configuration(self) -> Dict[str, Dict[str, Any]]:
        """Discover services via configuration files."""
        discovered = {}

        # This would read from configuration files
        # For now, return empty dict
        return discovered

    async def _discover_via_docker_network(self) -> Dict[str, Dict[str, Any]]:
        """Discover services via Docker network."""
        discovered = {}

        try:
            # Check if running in Docker
            with open('/proc/1/cgroup', 'r') as f:
                if 'docker' in f.read():
                    # Running in Docker, try to discover other containers
                    service_names = [s.value for s in ServiceNames]

                    for service_name in service_names:
                        try:
                            # Try to connect to service on Docker network
                            reader, writer = await asyncio.open_connection(service_name, 8000)
                            writer.close()
                            await writer.wait_closed()

                            discovered[service_name] = {
                                'endpoint': f"http://{service_name}:8000",
                                'discovery_method': 'docker_network',
                                'discovered_at': datetime.now().isoformat()
                            }
                        except:
                            continue

        except FileNotFoundError:
            # Not running in Docker
            pass

        return discovered

    async def _process_discovered_services(self, discovered: Dict[str, Dict[str, Any]]):
        """Process newly discovered services."""
        for service_name, service_info in discovered.items():
            if service_name not in self.discovered_services:
                self.discovered_services[service_name] = service_info
                fire_and_forget("info", f"Discovered new service: {service_name} at {service_info['endpoint']}", "service_discovery")

            # Update existing service info
            else:
                self.discovered_services[service_name].update(service_info)

    async def _update_service_registry(self):
        """Update service registry with discovered services."""
        for service_name, service_info in self.discovered_services.items():
            await service_registry.register_service(
                service_name,
                {'base_url': service_info['endpoint']},
                {
                    'discovery_method': service_info.get('discovery_method'),
                    'discovered_at': service_info.get('discovered_at')
                }
            )

    def get_discovered_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all discovered services."""
        return self.discovered_services.copy()

    async def manual_discovery(self, service_name: str, endpoint: str):
        """Manually register a discovered service."""
        self.discovered_services[service_name] = {
            'endpoint': endpoint,
            'discovery_method': 'manual',
            'discovered_at': datetime.now().isoformat()
        }

        await service_registry.register_service(
            service_name,
            {'base_url': endpoint},
            {'discovery_method': 'manual'}
        )


class PerformanceDashboard:
    """Real-time performance dashboard."""

    def __init__(self):
        # Use simple in-memory metrics storage instead of Prometheus
        self.metrics_store = {
            'service_health': {},
            'system_metrics': {},
            'cache_metrics': {},
            'error_metrics': {}
        }
        self.setup_metrics()

    def setup_metrics(self):
        """Setup in-memory metrics storage."""
        # Initialize metrics storage
        self.metrics_store = {
            'service_health': {},
            'system_metrics': {
                'memory_usage_percent': 0.0,
                'cpu_usage_percent': 0.0,
                'disk_usage_percent': 0.0
            },
            'cache_metrics': {},
            'error_metrics': {
                'total_errors': 0,
                'errors_by_service': {},
                'errors_by_severity': {}
            }
        }

    def update_metrics(self, health_monitor: HealthMonitor):
        """Update dashboard metrics from health monitor."""
        # Update service health metrics
        for service_name, health_info in health_monitor.services_health.items():
            # Health status
            status_value = {
                HealthStatus.UNKNOWN: 0,
                HealthStatus.HEALTHY: 1,
                HealthStatus.DEGRADED: 2,
                HealthStatus.UNHEALTHY: 3
            }[health_info.status]

            self.metrics_store['service_health'][service_name] = {
                'status': status_value,
                'status_text': health_info.status.value,
                'response_time_ms': health_info.response_time_ms,
                'last_check': health_info.last_check.isoformat()
            }

        # Update system metrics
        self.metrics_store['system_metrics'].update({
            'memory_usage_percent': health_monitor.system_metrics.system_memory_usage_percent,
            'cpu_usage_percent': health_monitor.system_metrics.system_cpu_usage_percent,
            'disk_usage_percent': health_monitor.system_metrics.disk_usage_percent
        })

        # Update cache metrics
        cache_metrics = get_cache_metrics()
        for service_name, metrics in cache_metrics.items():
            if 'performance' in metrics:
                perf = metrics['performance']
                self.metrics_store['cache_metrics'][service_name] = {
                    'hit_ratio': perf.get('hit_ratio', 0),
                    'cache_size_mb': metrics.get('total_size_mb', 0),
                    'cache_size_bytes': metrics.get('total_size_mb', 0) * 1024 * 1024
                }

    def get_metrics(self) -> str:
        """Get metrics as JSON string."""
        return json.dumps(self.metrics_store, indent=2)

    def get_dashboard_data(self, health_monitor: HealthMonitor) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        dashboard = health_monitor.get_performance_dashboard()

        # Add additional dashboard elements
        dashboard.update({
            'alerts_summary': self._get_alerts_summary(health_monitor),
            'trends': self._get_performance_trends(),
            'recommendations': self._get_system_recommendations(dashboard),
            'last_updated': datetime.now().isoformat()
        })

        return dashboard

    def _get_alerts_summary(self, health_monitor: HealthMonitor) -> Dict[str, Any]:
        """Get alerts summary for dashboard."""
        alerts = health_monitor.alerts[-50:]  # Last 50 alerts

        summary = {
            'total': len(alerts),
            'by_severity': {},
            'by_type': {},
            'recent': alerts[-10:]
        }

        for alert in alerts:
            severity = alert.get('severity', 'info')
            alert_type = alert.get('type', 'unknown')

            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            summary['by_type'][alert_type] = summary['by_type'].get(alert_type, 0) + 1

        return summary

    def _get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trends for dashboard."""
        # This would typically analyze historical data
        # For now, return placeholder
        return {
            'response_time_trend': 'stable',
            'error_rate_trend': 'decreasing',
            'resource_usage_trend': 'stable',
            'cache_performance_trend': 'improving'
        }

    def _get_system_recommendations(self, dashboard: Dict[str, Any]) -> List[str]:
        """Get system recommendations based on current state."""
        recommendations = []

        system_metrics = dashboard.get('system_overview', {})

        if system_metrics.get('system_memory_usage_percent', 0) > 85:
            recommendations.append("Consider increasing system memory or optimizing memory usage")

        if system_metrics.get('system_cpu_usage_percent', 0) > 90:
            recommendations.append("High CPU usage detected - consider scaling or optimization")

        if system_metrics.get('average_response_time_ms', 0) > 3000:
            recommendations.append("High average response time - investigate performance bottlenecks")

        service_health = dashboard.get('service_health', {})
        unhealthy_services = [name for name, health in service_health.items() if health.get('status') != 'healthy']
        if unhealthy_services:
            recommendations.append(f"Services needing attention: {', '.join(unhealthy_services)}")

        return recommendations


# Global instances
health_monitor = HealthMonitor()
service_discovery = ServiceDiscovery()
performance_dashboard = PerformanceDashboard()


async def initialize_operational_excellence():
    """Initialize operational excellence components."""
    # Start health monitoring
    await health_monitor.start_monitoring()

    # Register core services for monitoring
    core_services = [
        (ServiceNames.DOCUMENT_STORE, "http://localhost:8001"),
        (ServiceNames.PROMPT_STORE, "http://localhost:8002"),
        (ServiceNames.ANALYSIS_SERVICE, "http://localhost:8003"),
        (ServiceNames.INTERPRETER, "http://localhost:8004"),
        (ServiceNames.SUMMARIZER_HUB, "http://localhost:8005"),
        (ServiceNames.SOURCE_AGENT, "http://localhost:8006"),
        (ServiceNames.DISCOVERY_AGENT, "http://localhost:8007"),
    ]

    for service_name, endpoint in core_services:
        await health_monitor.register_service(
            service_name,
            endpoint,
            role=ServiceRole.CORE
        )

    # Start service discovery
    await service_discovery.start_discovery()

    fire_and_forget("info", "Operational excellence initialized successfully", "system")


async def shutdown_operational_excellence():
    """Shutdown operational excellence components."""
    await health_monitor.stop_monitoring()
    await service_discovery.stop_discovery()

    fire_and_forget("info", "Operational excellence shutdown completed", "system")


# Import os for environment variable access
import os
