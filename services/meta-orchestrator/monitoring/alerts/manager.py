"""Alert management system for configuration drift and health monitoring"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from monitoring.database.models import Alert
from monitoring.database.manager import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class AlertRule:
    """Rule for generating alerts"""
    name: str
    condition_type: str  # drift, health, performance
    severity: str
    threshold: Any
    message_template: str
    enabled: bool = True


class AlertManager:
    """Manages alerts for configuration drift and health issues"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.alert_rules = self._load_default_rules()

    def _load_default_rules(self) -> Dict[str, AlertRule]:
        """Load default alert rules"""
        return {
            "high_drift_frequency": AlertRule(
                name="High Configuration Drift Frequency",
                condition_type="drift",
                severity="warning",
                threshold={"drift_count": 5, "time_window_hours": 24},
                message_template="Service {service_name} has {drift_count} configuration changes in the last {time_window_hours} hours"
            ),
            "service_unhealthy": AlertRule(
                name="Service Unhealthy",
                condition_type="health",
                severity="error",
                threshold={"consecutive_failures": 3},
                message_template="Service {service_name} has been unhealthy for {consecutive_failures} consecutive checks"
            ),
            "low_overall_health": AlertRule(
                name="Low Overall Health",
                condition_type="health",
                severity="critical",
                threshold={"health_percentage": 70.0},
                message_template="Overall system health is {health_percentage:.1f}% - below acceptable threshold"
            ),
            "critical_drift_detected": AlertRule(
                name="Critical Configuration Drift",
                condition_type="drift",
                severity="critical",
                threshold={"severity": "critical"},
                message_template="Critical configuration drift detected in {service_name}: {description}"
            )
        }

    def add_alert_rule(self, rule: AlertRule):
        """Add a custom alert rule"""
        self.alert_rules[rule.name] = rule
        logger.info(f"✅ Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"❌ Removed alert rule: {rule_name}")

    def create_drift_alert(self, service_name: str, drift_count: int,
                          time_window_hours: int) -> Optional[Alert]:
        """Create an alert for high drift frequency"""
        rule = self.alert_rules.get("high_drift_frequency")
        if not rule or not rule.enabled:
            return None

        if drift_count >= rule.threshold["drift_count"]:
            alert = Alert(
                alert_type="drift",
                severity=rule.severity,
                service_name=service_name,
                title="High Configuration Drift Frequency",
                message=rule.message_template.format(
                    service_name=service_name,
                    drift_count=drift_count,
                    time_window_hours=time_window_hours
                ),
                metadata={
                    "drift_count": drift_count,
                    "time_window_hours": time_window_hours,
                    "rule": rule.name
                }
            )
            return alert
        return None

    def create_health_alert(self, service_name: str, consecutive_failures: int) -> Optional[Alert]:
        """Create an alert for service health issues"""
        rule = self.alert_rules.get("service_unhealthy")
        if not rule or not rule.enabled:
            return None

        if consecutive_failures >= rule.threshold["consecutive_failures"]:
            alert = Alert(
                alert_type="health",
                severity=rule.severity,
                service_name=service_name,
                title="Service Unhealthy",
                message=rule.message_template.format(
                    service_name=service_name,
                    consecutive_failures=consecutive_failures
                ),
                metadata={
                    "consecutive_failures": consecutive_failures,
                    "rule": rule.name
                }
            )
            return alert
        return None

    def create_overall_health_alert(self, health_percentage: float,
                                   total_services: int,
                                   healthy_services: int) -> Optional[Alert]:
        """Create an alert for low overall system health"""
        rule = self.alert_rules.get("low_overall_health")
        if not rule or not rule.enabled:
            return None

        if health_percentage <= rule.threshold["health_percentage"]:
            alert = Alert(
                alert_type="health",
                severity=rule.severity,
                service_name="system",
                title="Low Overall System Health",
                message=rule.message_template.format(
                    health_percentage=health_percentage
                ),
                metadata={
                    "health_percentage": health_percentage,
                    "total_services": total_services,
                    "healthy_services": healthy_services,
                    "rule": rule.name
                }
            )
            return alert
        return None

    def create_critical_drift_alert(self, service_name: str,
                                   drift_description: str,
                                   drift_severity: str) -> Optional[Alert]:
        """Create an alert for critical configuration drift"""
        rule = self.alert_rules.get("critical_drift_detected")
        if not rule or not rule.enabled:
            return None

        if drift_severity == rule.threshold["severity"]:
            alert = Alert(
                alert_type="drift",
                severity=rule.severity,
                service_name=service_name,
                title="Critical Configuration Drift Detected",
                message=rule.message_template.format(
                    service_name=service_name,
                    description=drift_description
                ),
                metadata={
                    "drift_severity": drift_severity,
                    "drift_description": drift_description,
                    "rule": rule.name
                }
            )
            return alert
        return None

    def send_alert(self, alert: Alert) -> int:
        """Send an alert and save it to the database"""
        try:
            # Save to database
            alert_id = self.db_manager.save_alert(alert)

            # Log the alert
            logger.warning(f"🚨 ALERT [{alert.severity.upper()}]: {alert.title} - {alert.message}")

            # Here you could add additional notification methods:
            # - Email notifications
            # - Slack/Discord webhooks
            # - SMS alerts
            # - Integration with monitoring systems (Prometheus, Grafana, etc.)

            return alert_id

        except Exception as e:
            logger.error(f"❌ Failed to send alert: {e}")
            return -1

    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        success = self.db_manager.acknowledge_alert(alert_id, acknowledged_by)
        if success:
            logger.info(f"✅ Alert {alert_id} acknowledged by {acknowledged_by}")
        return success

    def resolve_alert(self, alert_id: int) -> bool:
        """Resolve an alert"""
        success = self.db_manager.resolve_alert(alert_id)
        if success:
            logger.info(f"✅ Alert {alert_id} resolved")
        return success

    def get_active_alerts(self, service_name: Optional[str] = None) -> List[Alert]:
        """Get active (unresolved) alerts"""
        return self.db_manager.get_alerts(
            service_name=service_name,
            resolved=False,
            limit=100
        )

    def get_alert_history(self, service_name: Optional[str] = None,
                         days: int = 7) -> List[Alert]:
        """Get alert history"""
        # For simplicity, get all alerts and filter by date in application
        alerts = self.db_manager.get_alerts(
            service_name=service_name,
            limit=500
        )

        # Filter by date (simple implementation)
        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)

        return [alert for alert in alerts if alert.timestamp >= cutoff_date]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        all_alerts = self.db_manager.get_alerts(limit=1000)

        stats = {
            "total_alerts": len(all_alerts),
            "active_alerts": len([a for a in all_alerts if not a.resolved]),
            "acknowledged_alerts": len([a for a in all_alerts if a.acknowledged]),
            "resolved_alerts": len([a for a in all_alerts if a.resolved]),
            "severity_breakdown": {},
            "type_breakdown": {}
        }

        for alert in all_alerts:
            # Severity breakdown
            if alert.severity not in stats["severity_breakdown"]:
                stats["severity_breakdown"][alert.severity] = 0
            stats["severity_breakdown"][alert.severity] += 1

            # Type breakdown
            if alert.alert_type not in stats["type_breakdown"]:
                stats["type_breakdown"][alert.alert_type] = 0
            stats["type_breakdown"][alert.alert_type] += 1

        return stats
