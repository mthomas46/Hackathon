"""
Health Monitor

Provides comprehensive health monitoring for all ecosystem services including:
- Real-time health status tracking
- Performance metrics collection
- Alerting and notification system
- Health history and trends
- Service availability analytics
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field

import httpx

from ...modules.discovery.client import DiscoveryClient
from ...config import Config


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    service_name: str
    status: str  # "healthy", "unhealthy", "unknown"
    response_time_ms: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    http_status_code: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "service_name": self.service_name,
            "status": self.status,
            "response_time_ms": self.response_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
            "http_status_code": self.http_status_code,
            "details": self.details
        }


@dataclass
class ServiceHealthMetrics:
    """Aggregated health metrics for a service."""
    service_name: str
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    average_response_time: float = 0.0
    last_check: Optional[datetime] = None
    first_check: Optional[datetime] = None
    uptime_percentage: float = 0.0
    consecutive_failures: int = 0
    status_history: deque = field(default_factory=lambda: deque(maxlen=100))

    def add_check_result(self, result: HealthCheckResult):
        """Add a health check result and update metrics."""
        self.total_checks += 1
        self.last_check = result.timestamp

        if not self.first_check:
            self.first_check = result.timestamp

        # Update success/failure counts
        if result.status == "healthy":
            self.successful_checks += 1
            self.consecutive_failures = 0
        else:
            self.failed_checks += 1
            self.consecutive_failures += 1

        # Update response time average
        if result.response_time_ms is not None:
            if self.average_response_time == 0:
                self.average_response_time = result.response_time_ms
            else:
                # Weighted average
                self.average_response_time = (
                    (self.average_response_time * (self.total_checks - 1)) +
                    result.response_time_ms
                ) / self.total_checks

        # Update uptime percentage
        if self.total_checks > 0:
            self.uptime_percentage = (self.successful_checks / self.total_checks) * 100

        # Add to status history
        self.status_history.append({
            "timestamp": result.timestamp,
            "status": result.status,
            "response_time": result.response_time_ms
        })

    def get_recent_status_trend(self, hours: int = 24) -> Dict[str, Any]:
        """Get status trend for the recent period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_checks = [
            check for check in self.status_history
            if check["timestamp"] >= cutoff_time
        ]

        if not recent_checks:
            return {"trend": "unknown", "data_points": 0}

        healthy_count = sum(1 for check in recent_checks if check["status"] == "healthy")
        unhealthy_count = len(recent_checks) - healthy_count

        recent_uptime = (healthy_count / len(recent_checks) * 100) if recent_checks else 0

        # Determine trend
        if recent_uptime >= 95:
            trend = "excellent"
        elif recent_uptime >= 90:
            trend = "good"
        elif recent_uptime >= 80:
            trend = "fair"
        elif recent_uptime >= 50:
            trend = "concerning"
        else:
            trend = "critical"

        return {
            "trend": trend,
            "uptime_percentage": round(recent_uptime, 2),
            "data_points": len(recent_checks),
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count,
            "period_hours": hours
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "service_name": self.service_name,
            "total_checks": self.total_checks,
            "successful_checks": self.successful_checks,
            "failed_checks": self.failed_checks,
            "average_response_time": round(self.average_response_time, 2),
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "first_check": self.first_check.isoformat() if self.first_check else None,
            "uptime_percentage": round(self.uptime_percentage, 2),
            "consecutive_failures": self.consecutive_failures,
            "status_trend": self.get_recent_status_trend()
        }


class HealthMonitor:
    """Monitors health of all ecosystem services."""

    def __init__(self, discovery_client: DiscoveryClient, config: Config):
        self.discovery_client = discovery_client
        self.config = config

        # Health monitoring state
        self.service_metrics: Dict[str, ServiceHealthMetrics] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None

        # HTTP client for health checks
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )

        # Alert thresholds
        self.alert_thresholds = {
            "consecutive_failures": 3,
            "response_time_threshold_ms": 5000,  # 5 seconds
            "uptime_threshold_percent": 95.0
        }

    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        print("🏥 Health monitoring started")

    async def stop_monitoring(self):
        """Stop health monitoring."""
        self.monitoring_active = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        await self.client.aclose()
        print("🏥 Health monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                await self._perform_health_checks()
                await self._check_alerts()
                await asyncio.sleep(self.config.api_polling_interval)

            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _perform_health_checks(self):
        """Perform health checks on all services."""
        try:
            # Get current service list
            services = await self.discovery_client.get_all_services()

            # Perform health checks concurrently
            tasks = []
            for service in services:
                service_name = service.get("name")
                service_url = service.get("url")

                if service_name and service_url:
                    task = self._check_service_health(service_name, service_url)
                    tasks.append(task)

            # Wait for all checks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, HealthCheckResult):
                    self._process_health_result(result)
                elif isinstance(result, Exception):
                    print(f"Health check error: {result}")

        except Exception as e:
            print(f"Error performing health checks: {e}")

    async def _check_service_health(self, service_name: str, service_url: str) -> HealthCheckResult:
        """Check health of a specific service."""
        health_url = f"{service_url.rstrip('/')}/health"

        try:
            start_time = time.time()

            response = await self.client.get(health_url)

            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds

            if response.status_code == 200:
                # Try to parse health response
                try:
                    health_data = response.json()
                    status = health_data.get("status", "healthy")
                    details = health_data
                except:
                    status = "healthy"
                    details = {"raw_response": response.text[:500]}

                return HealthCheckResult(
                    service_name=service_name,
                    status=status,
                    response_time_ms=response_time,
                    http_status_code=response.status_code,
                    details=details
                )
            else:
                return HealthCheckResult(
                    service_name=service_name,
                    status="unhealthy",
                    response_time_ms=response_time,
                    http_status_code=response.status_code,
                    error_message=f"HTTP {response.status_code}",
                    details={"response_body": response.text[:500]}
                )

        except httpx.TimeoutException:
            return HealthCheckResult(
                service_name=service_name,
                status="unhealthy",
                error_message="Request timeout",
                details={"timeout_seconds": self.client.timeout.read}
            )

        except httpx.ConnectError:
            return HealthCheckResult(
                service_name=service_name,
                status="unhealthy",
                error_message="Connection failed",
                details={"service_url": service_url}
            )

        except Exception as e:
            return HealthCheckResult(
                service_name=service_name,
                status="unhealthy",
                error_message=str(e),
                details={"exception_type": type(e).__name__}
            )

    def _process_health_result(self, result: HealthCheckResult):
        """Process a health check result."""
        service_name = result.service_name

        # Initialize metrics if not exists
        if service_name not in self.service_metrics:
            self.service_metrics[service_name] = ServiceHealthMetrics(service_name)

        # Add result to metrics
        self.service_metrics[service_name].add_check_result(result)

    async def _check_alerts(self):
        """Check for alert conditions and generate alerts."""
        current_time = datetime.now()

        for service_name, metrics in self.service_metrics.items():
            alerts = self._check_service_alerts(service_name, metrics, current_time)

            for alert in alerts:
                self.alerts.append(alert)

                # Keep only recent alerts (last 1000)
                if len(self.alerts) > 1000:
                    self.alerts = self.alerts[-1000:]

    def _check_service_alerts(self, service_name: str, metrics: ServiceHealthMetrics,
                            current_time: datetime) -> List[Dict[str, Any]]:
        """Check for alerts on a specific service."""
        alerts = []

        # Consecutive failures alert
        if metrics.consecutive_failures >= self.alert_thresholds["consecutive_failures"]:
            alerts.append({
                "id": f"consecutive_failures_{service_name}_{current_time.timestamp()}",
                "service_name": service_name,
                "type": "consecutive_failures",
                "severity": "high",
                "message": f"Service {service_name} has {metrics.consecutive_failures} consecutive failures",
                "timestamp": current_time.isoformat(),
                "data": {
                    "consecutive_failures": metrics.consecutive_failures,
                    "threshold": self.alert_thresholds["consecutive_failures"],
                    "last_status": metrics.status_history[-1] if metrics.status_history else None
                }
            })

        # Low uptime alert
        if metrics.total_checks >= 10 and metrics.uptime_percentage < self.alert_thresholds["uptime_threshold_percent"]:
            alerts.append({
                "id": f"low_uptime_{service_name}_{current_time.timestamp()}",
                "service_name": service_name,
                "type": "low_uptime",
                "severity": "medium",
                "message": f"Service {service_name} uptime is {metrics.uptime_percentage:.1f}% (below {self.alert_thresholds['uptime_threshold_percent']}%)",
                "timestamp": current_time.isoformat(),
                "data": {
                    "uptime_percentage": metrics.uptime_percentage,
                    "threshold": self.alert_thresholds["uptime_threshold_percent"],
                    "total_checks": metrics.total_checks
                }
            })

        # High response time alert
        if (metrics.average_response_time > self.alert_thresholds["response_time_threshold_ms"] and
            metrics.total_checks >= 5):
            alerts.append({
                "id": f"high_response_time_{service_name}_{current_time.timestamp()}",
                "service_name": service_name,
                "type": "high_response_time",
                "severity": "medium",
                "message": f"Service {service_name} average response time is {metrics.average_response_time:.0f}ms (above {self.alert_thresholds['response_time_threshold_ms']}ms)",
                "timestamp": current_time.isoformat(),
                "data": {
                    "average_response_time": metrics.average_response_time,
                    "threshold": self.alert_thresholds["response_time_threshold_ms"],
                    "total_checks": metrics.total_checks
                }
            })

        return alerts

    async def get_health_status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get current health status for services."""
        if service_name:
            if service_name not in self.service_metrics:
                return {"error": f"No health data available for service {service_name}"}

            metrics = self.service_metrics[service_name]
            return {
                "service_name": service_name,
                "current_status": self._get_current_status(service_name),
                "metrics": metrics.to_dict(),
                "alerts": self._get_service_alerts(service_name)
            }

        # Return all services
        services_status = {}
        for svc_name, metrics in self.service_metrics.items():
            services_status[svc_name] = {
                "status": self._get_current_status(svc_name),
                "metrics": metrics.to_dict(),
                "alerts_count": len(self._get_service_alerts(svc_name))
            }

        # Calculate overall health
        total_services = len(services_status)
        healthy_services = sum(1 for svc in services_status.values() if svc["status"] == "healthy")
        unhealthy_services = total_services - healthy_services

        return {
            "overall_health": {
                "total_services": total_services,
                "healthy_services": healthy_services,
                "unhealthy_services": unhealthy_services,
                "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0
            },
            "services": services_status,
            "recent_alerts": self._get_recent_alerts(limit=10),
            "last_updated": datetime.now().isoformat()
        }

    def _get_current_status(self, service_name: str) -> str:
        """Get current status of a service."""
        if service_name not in self.service_metrics:
            return "unknown"

        metrics = self.service_metrics[service_name]
        if not metrics.status_history:
            return "unknown"

        # Return status of most recent check
        latest = metrics.status_history[-1]
        return latest["status"]

    def _get_service_alerts(self, service_name: str) -> List[Dict[str, Any]]:
        """Get recent alerts for a service."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        return [
            alert for alert in self.alerts
            if alert["service_name"] == service_name and
            datetime.fromisoformat(alert["timestamp"]) >= cutoff_time
        ]

    def _get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts across all services."""
        sorted_alerts = sorted(
            self.alerts,
            key=lambda x: x["timestamp"],
            reverse=True
        )
        return sorted_alerts[:limit]

    def get_health_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get health analytics for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        analytics = {
            "period_hours": hours,
            "services_analyzed": len(self.service_metrics),
            "alerts_generated": len([
                alert for alert in self.alerts
                if datetime.fromisoformat(alert["timestamp"]) >= cutoff_time
            ]),
            "service_performance": {},
            "alert_summary": defaultdict(int)
        }

        # Service performance analysis
        for service_name, metrics in self.service_metrics.items():
            recent_checks = [
                check for check in metrics.status_history
                if check["timestamp"] >= cutoff_time
            ]

            if recent_checks:
                healthy_checks = sum(1 for check in recent_checks if check["status"] == "healthy")
                recent_uptime = (healthy_checks / len(recent_checks)) * 100

                response_times = [check["response_time"] for check in recent_checks if check["response_time"]]

                analytics["service_performance"][service_name] = {
                    "checks_performed": len(recent_checks),
                    "uptime_percentage": round(recent_uptime, 2),
                    "avg_response_time": round(sum(response_times) / len(response_times), 2) if response_times else None,
                    "min_response_time": min(response_times) if response_times else None,
                    "max_response_time": max(response_times) if response_times else None
                }

        # Alert summary
        for alert in self.alerts:
            if datetime.fromisoformat(alert["timestamp"]) >= cutoff_time:
                analytics["alert_summary"][alert["type"]] += 1
                analytics["alert_summary"][f"severity_{alert['severity']}"] += 1

        return analytics

    def export_health_report(self, format: str = "json") -> str:
        """Export comprehensive health report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "monitoring_status": "active" if self.monitoring_active else "inactive",
            "services_monitored": len(self.service_metrics),
            "total_alerts": len(self.alerts),
            "service_health": {},
            "alert_summary": defaultdict(int),
            "analytics": self.get_health_analytics(hours=24)
        }

        # Service health details
        for service_name, metrics in self.service_metrics.items():
            report["service_health"][service_name] = {
                "current_status": self._get_current_status(service_name),
                "metrics": metrics.to_dict(),
                "active_alerts": len(self._get_service_alerts(service_name))
            }

        # Alert summary
        for alert in self.alerts:
            report["alert_summary"][alert["type"]] += 1
            report["alert_summary"][f"severity_{alert['severity']}"] += 1

        if format == "json":
            return json.dumps(report, indent=2, default=str)
        else:
            return json.dumps(report, default=str)
