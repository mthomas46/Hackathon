#!/usr/bin/env python3
"""
Monitoring Dashboard and Alerting System
=========================================

Comprehensive monitoring dashboard for the ecosystem services.
Provides real-time health monitoring, metrics visualization, and alerting.

Features:
- Real-time service health dashboard
- Performance metrics visualization
- Alerting system for critical issues
- Historical metrics analysis
- Service dependency monitoring
- Automated recovery suggestions

Author: Ecosystem Hardening Framework
"""

import json
import time
import threading
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import sys
from standardized_logger import StandardizedLogger, get_all_loggers


@dataclass
class ServiceStatus:
    """Service status information"""
    name: str
    status: str  # "healthy", "warning", "critical", "unknown"
    last_check: datetime
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    version: Optional[str] = None
    uptime: Optional[float] = None


@dataclass
class Alert:
    """Monitoring alert"""
    alert_id: str
    service_name: str
    alert_type: str  # "health", "performance", "error_rate", "resource"
    severity: str    # "info", "warning", "critical"
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class DashboardMetrics:
    """Dashboard metrics summary"""
    total_services: int
    healthy_services: int
    warning_services: int
    critical_services: int
    unknown_services: int
    active_alerts: int
    avg_response_time: float
    total_requests: int
    error_rate: float
    last_updated: datetime = field(default_factory=datetime.now)


class MonitoringDashboard:
    """
    Real-time monitoring dashboard for the ecosystem.

    Provides comprehensive monitoring of all services with health status,
    performance metrics, and alerting capabilities.
    """

    def __init__(self, workspace_path: Optional[str] = None):
        """Initialize the monitoring dashboard"""
        self.workspace_path = Path(workspace_path or Path.cwd())
        self.services: Dict[str, ServiceStatus] = {}
        self.alerts: List[Alert] = []
        self.metrics_history: List[DashboardMetrics] = []
        self.reports_dir = self.workspace_path / "reports" / "monitoring"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Monitoring configuration
        self.check_interval = 30  # seconds
        self.alert_thresholds = {
            "response_time": 2.0,  # seconds
            "error_rate": 0.05,    # 5%
            "cpu_usage": 80.0,     # percent
            "memory_usage": 85.0   # percent
        }

        # Dashboard state
        self.is_running = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # Get logger
        self.logger = StandardizedLogger("monitoring-dashboard")

        self.logger.info("📊 Monitoring Dashboard initialized")

    def start_monitoring(self):
        """Start the monitoring dashboard"""
        if self.is_running:
            return

        self.is_running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="monitoring-dashboard"
        )
        self.monitoring_thread.start()
        self.logger.info("📊 Monitoring dashboard started")

    def stop_monitoring(self):
        """Stop the monitoring dashboard"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("📊 Monitoring dashboard stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                self._update_service_status()
                self._check_alerts()
                self._update_dashboard_metrics()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(5)

    def _update_service_status(self):
        """Update status of all monitored services"""
        # Get all loggers (represents all services)
        service_loggers = get_all_loggers()

        for service_name, logger in service_loggers.items():
            try:
                # Get health status from logger
                health_status = logger.get_health_status()

                service_status = ServiceStatus(
                    name=service_name,
                    status=health_status["status"],
                    last_check=datetime.now(),
                    response_time=health_status["metrics"].get("response_time"),
                    version=health_status.get("version"),
                    uptime=health_status.get("uptime_seconds")
                )

                self.services[service_name] = service_status

            except Exception as e:
                self.logger.error(f"Failed to update status for {service_name}: {e}")

                # Create unknown status
                self.services[service_name] = ServiceStatus(
                    name=service_name,
                    status="unknown",
                    last_check=datetime.now(),
                    error_message=str(e)
                )

    def _check_alerts(self):
        """Check for alerts based on service status and metrics"""
        for service_name, service_status in self.services.items():
            # Health status alerts
            if service_status.status == "critical":
                self._create_alert(
                    service_name=service_name,
                    alert_type="health",
                    severity="critical",
                    message=f"Service {service_name} is in critical health state"
                )
            elif service_status.status == "warning":
                self._create_alert(
                    service_name=service_name,
                    alert_type="health",
                    severity="warning",
                    message=f"Service {service_name} health status is warning"
                )

            # Response time alerts
            if service_status.response_time and service_status.response_time > self.alert_thresholds["response_time"]:
                self._create_alert(
                    service_name=service_name,
                    alert_type="performance",
                    severity="warning",
                    message=f"Service {service_name} response time ({service_status.response_time:.2f}s) exceeds threshold"
                )

    def _create_alert(self, service_name: str, alert_type: str, severity: str, message: str):
        """Create a new alert"""
        # Check if similar alert already exists and is unresolved
        for alert in self.alerts:
            if (alert.service_name == service_name and
                alert.alert_type == alert_type and
                alert.severity == severity and
                not alert.resolved):
                # Update existing alert timestamp
                alert.timestamp = datetime.now()
                return

        # Create new alert
        alert_id = f"{service_name}_{alert_type}_{int(time.time())}"
        alert = Alert(
            alert_id=alert_id,
            service_name=service_name,
            alert_type=alert_type,
            severity=severity,
            message=message
        )

        self.alerts.append(alert)
        self.logger.warning(f"🚨 Alert created: {message}", extra={
            "alert_id": alert_id,
            "alert_type": alert_type,
            "severity": severity
        })

    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                self.logger.info(f"✅ Alert resolved: {alert.message}", extra={
                    "alert_id": alert_id,
                    "resolution_time": alert.resolved_at.isoformat()
                })
                break

    def _update_dashboard_metrics(self):
        """Update dashboard metrics summary"""
        if not self.services:
            return

        total_services = len(self.services)
        healthy_services = sum(1 for s in self.services.values() if s.status == "healthy")
        warning_services = sum(1 for s in self.services.values() if s.status == "warning")
        critical_services = sum(1 for s in self.services.values() if s.status == "critical")
        unknown_services = sum(1 for s in self.services.values() if s.status == "unknown")

        active_alerts = sum(1 for a in self.alerts if not a.resolved)

        # Calculate average response time
        response_times = [s.response_time for s in self.services.values() if s.response_time]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Get total requests and error rate from all loggers
        total_requests = 0
        total_errors = 0

        for logger in get_all_loggers().values():
            health = logger.get_health_status()
            metrics = health.get("metrics", {})
            total_requests += metrics.get("request_count", 0)
            total_errors += metrics.get("error_count", 0)

        error_rate = total_errors / max(total_requests, 1)

        metrics = DashboardMetrics(
            total_services=total_services,
            healthy_services=healthy_services,
            warning_services=warning_services,
            critical_services=critical_services,
            unknown_services=unknown_services,
            active_alerts=active_alerts,
            avg_response_time=avg_response_time,
            total_requests=total_requests,
            error_rate=error_rate
        )

        self.metrics_history.append(metrics)

        # Keep only last 100 metrics
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        if not self.services:
            return {"error": "No services monitored"}

        # Get latest metrics
        latest_metrics = self.metrics_history[-1] if self.metrics_history else None

        # Get active alerts
        active_alerts = [a for a in self.alerts if not a.resolved]

        # Service status summary
        service_summary = []
        for service_name, service_status in self.services.items():
            service_summary.append({
                "name": service_name,
                "status": service_status.status,
                "last_check": service_status.last_check.isoformat(),
                "response_time": service_status.response_time,
                "uptime": service_status.uptime,
                "version": service_status.version
            })

        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "services": service_summary,
            "alerts": [{
                "id": a.alert_id,
                "service": a.service_name,
                "type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "timestamp": a.timestamp.isoformat()
            } for a in active_alerts],
            "metrics": {
                "total_services": latest_metrics.total_services if latest_metrics else 0,
                "healthy_services": latest_metrics.healthy_services if latest_metrics else 0,
                "warning_services": latest_metrics.warning_services if latest_metrics else 0,
                "critical_services": latest_metrics.critical_services if latest_metrics else 0,
                "unknown_services": latest_metrics.unknown_services if latest_metrics else 0,
                "active_alerts": latest_metrics.active_alerts if latest_metrics else 0,
                "avg_response_time": latest_metrics.avg_response_time if latest_metrics else 0,
                "total_requests": latest_metrics.total_requests if latest_metrics else 0,
                "error_rate": latest_metrics.error_rate if latest_metrics else 0
            } if latest_metrics else {}
        }

        return dashboard_data

    def print_dashboard(self):
        """Print formatted dashboard"""
        data = self.get_dashboard_data()

        if "error" in data:
            print(f"❌ {data['error']}")
            return

        print("\n" + "="*80)
        print("📊 ECOSYSTEM MONITORING DASHBOARD")
        print("="*80)

        # Service status overview
        metrics = data["metrics"]
        print(f"🖥️  Services: {metrics.get('total_services', 0)} total")
        print(f"  ✅ Healthy: {metrics.get('healthy_services', 0)}")
        print(f"  ⚠️  Warning: {metrics.get('warning_services', 0)}")
        print(f"  🔴 Critical: {metrics.get('critical_services', 0)}")
        print(f"  ❓ Unknown: {metrics.get('unknown_services', 0)}")

        print(f"\n🚨 Active Alerts: {metrics.get('active_alerts', 0)}")

        # Performance metrics
        if metrics.get('avg_response_time', 0) > 0:
            print("
⚡ Performance:"            print(".2f"            print(f"  📊 Total Requests: {metrics.get('total_requests', 0)}")
            print(".1f"
        # Service details
        print("
🏥 Service Status:"        for service in data["services"]:
            status_icon = {
                "healthy": "✅",
                "warning": "⚠️",
                "critical": "🔴",
                "unknown": "❓"
            }.get(service["status"], "❓")

            response_time = ".2f" if service["response_time"] else "N/A"
            print(f"  {status_icon} {service['name']:<20} {service['status']:<8} {response_time}")

        # Active alerts
        if data["alerts"]:
            print("
🚨 Active Alerts:"            for alert in data["alerts"]:
                severity_icon = "🔴" if alert["severity"] == "critical" else "⚠️"
                print(f"  {severity_icon} [{alert['service']}] {alert['message']}")

        print(f"\n📅 Last Updated: {data['timestamp']}")
        print("="*80)

    def save_dashboard_report(self, filename: Optional[str] = None) -> Path:
        """Save dashboard report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dashboard_report_{timestamp}.json"

        report_path = self.reports_dir / filename

        data = self.get_dashboard_data()
        with open(report_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        self.logger.info(f"💾 Dashboard report saved: {report_path}")
        return report_path

    def get_service_logs(self, service_name: str, lines: int = 50) -> Optional[List[str]]:
        """Get recent logs for a specific service"""
        # This would integrate with log aggregation system
        # For now, return a placeholder
        return [f"Sample log entry for {service_name}"]

    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over the specified time period"""
        if not self.metrics_history:
            return {"error": "No metrics history available"}

        # Filter metrics for the specified time period
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history
            if m.last_updated >= cutoff_time
        ]

        if not recent_metrics:
            return {"error": "No metrics available for the specified time period"}

        # Calculate trends
        trends = {
            "period_hours": hours,
            "data_points": len(recent_metrics),
            "avg_response_time_trend": self._calculate_trend([m.avg_response_time for m in recent_metrics]),
            "error_rate_trend": self._calculate_trend([m.error_rate for m in recent_metrics]),
            "healthy_services_trend": self._calculate_trend([m.healthy_services for m in recent_metrics]),
            "active_alerts_trend": self._calculate_trend([m.active_alerts for m in recent_metrics])
        }

        return trends

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0

        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"


# Global dashboard instance
_dashboard_instance: Optional[MonitoringDashboard] = None


def get_monitoring_dashboard() -> MonitoringDashboard:
    """Get the global monitoring dashboard instance"""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = MonitoringDashboard()
    return _dashboard_instance


def start_monitoring():
    """Start the monitoring dashboard"""
    dashboard = get_monitoring_dashboard()
    dashboard.start_monitoring()


def stop_monitoring():
    """Stop the monitoring dashboard"""
    dashboard = get_monitoring_dashboard()
    dashboard.stop_monitoring()


# Example usage and testing
if __name__ == "__main__":
    # Create dashboard
    dashboard = MonitoringDashboard()

    # Create some sample loggers to monitor
    logger1 = StandardizedLogger("sample-service-1")
    logger2 = StandardizedLogger("sample-service-2")

    # Start monitoring
    dashboard.start_monitoring()

    # Let it run for a bit
    print("Monitoring dashboard running... Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(10)
            dashboard.print_dashboard()
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        dashboard.stop_monitoring()
        logger1.stop_monitoring()
        logger2.stop_monitoring()
        print("Monitoring stopped.")
