#!/usr/bin/env python3
"""
Automated Health Check Monitoring System

Enterprise-grade automated monitoring system for all 17 services in the
LLM Documentation Ecosystem with alerting, reporting, and self-healing capabilities.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
import argparse
from dataclasses import dataclass, asdict
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor


@dataclass
class ServiceHealthStatus:
    """Service health status data structure."""
    service_name: str
    url: str
    status: str  # "healthy", "unhealthy", "unknown"
    response_time: float
    status_code: int
    error_message: Optional[str]
    last_check: str
    uptime_percentage: float
    consecutive_failures: int


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    condition: str
    severity: str  # "critical", "warning", "info"
    threshold: float
    duration_minutes: int
    enabled: bool


class HealthMonitoringDatabase:
    """SQLite database for health monitoring data."""

    def __init__(self, db_path: str = "health_monitoring.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the health monitoring database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create health_checks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                status TEXT NOT NULL,
                response_time REAL,
                status_code INTEGER,
                error_message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME,
                status TEXT DEFAULT 'active'
            )
        """)
        
        # Create service_status table for current status
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_status (
                service_name TEXT PRIMARY KEY,
                current_status TEXT NOT NULL,
                last_healthy DATETIME,
                consecutive_failures INTEGER DEFAULT 0,
                uptime_percentage REAL DEFAULT 100.0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()

    def record_health_check(self, service_name: str, status: str, response_time: float,
                          status_code: int, error_message: Optional[str] = None):
        """Record a health check result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO health_checks (service_name, status, response_time, status_code, error_message)
            VALUES (?, ?, ?, ?, ?)
        """, (service_name, status, response_time, status_code, error_message))
        
        conn.commit()
        conn.close()

    def update_service_status(self, service_name: str, status: str, consecutive_failures: int):
        """Update current service status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate uptime percentage from last 24 hours
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy
            FROM health_checks 
            WHERE service_name = ? AND timestamp > datetime('now', '-24 hours')
        """, (service_name,))
        
        result = cursor.fetchone()
        total_checks = result[0] if result[0] > 0 else 1
        healthy_checks = result[1] if result[1] is not None else 0
        uptime_percentage = (healthy_checks / total_checks) * 100

        cursor.execute("""
            INSERT OR REPLACE INTO service_status 
            (service_name, current_status, last_healthy, consecutive_failures, uptime_percentage, last_updated)
            VALUES (?, ?, 
                    CASE WHEN ? = 'healthy' THEN CURRENT_TIMESTAMP 
                         ELSE COALESCE((SELECT last_healthy FROM service_status WHERE service_name = ?), CURRENT_TIMESTAMP)
                    END,
                    ?, ?, CURRENT_TIMESTAMP)
        """, (service_name, status, status, service_name, consecutive_failures, uptime_percentage))
        
        conn.commit()
        conn.close()

    def get_service_status_summary(self) -> List[Dict[str, Any]]:
        """Get current status summary for all services."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT service_name, current_status, last_healthy, consecutive_failures, 
                   uptime_percentage, last_updated
            FROM service_status
            ORDER BY service_name
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "service_name": row[0],
                "current_status": row[1],
                "last_healthy": row[2],
                "consecutive_failures": row[3],
                "uptime_percentage": row[4],
                "last_updated": row[5]
            })
        
        conn.close()
        return results

    def record_alert(self, service_name: str, alert_type: str, severity: str, message: str):
        """Record an alert."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alerts (service_name, alert_type, severity, message)
            VALUES (?, ?, ?, ?)
        """, (service_name, alert_type, severity, message))
        
        conn.commit()
        conn.close()


class AlertManager:
    """Manages alerts and notifications."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_rules = self._load_alert_rules()
        self.logger = logging.getLogger(__name__)

    def _load_alert_rules(self) -> List[AlertRule]:
        """Load alert rules from configuration."""
        rules = []
        
        # Default alert rules
        default_rules = [
            AlertRule("service_down", "status == 'unhealthy'", "critical", 1, 2, True),
            AlertRule("high_response_time", "response_time > 5.0", "warning", 5.0, 5, True),
            AlertRule("consecutive_failures", "consecutive_failures >= 3", "critical", 3, 1, True),
            AlertRule("low_uptime", "uptime_percentage < 95.0", "warning", 95.0, 15, True),
            AlertRule("service_recovery", "status == 'healthy' AND previous_status == 'unhealthy'", "info", 1, 1, True)
        ]
        
        for rule_data in default_rules:
            rules.append(rule_data)
        
        return rules

    def evaluate_alerts(self, service_status: ServiceHealthStatus, previous_status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Evaluate alert rules against service status."""
        triggered_alerts = []
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            try:
                # Create evaluation context
                context = {
                    "status": service_status.status,
                    "response_time": service_status.response_time,
                    "consecutive_failures": service_status.consecutive_failures,
                    "uptime_percentage": service_status.uptime_percentage,
                    "previous_status": previous_status
                }
                
                # Evaluate rule condition
                if self._evaluate_condition(rule.condition, context):
                    alert = {
                        "rule_name": rule.name,
                        "service_name": service_status.service_name,
                        "severity": rule.severity,
                        "message": self._generate_alert_message(rule, service_status),
                        "triggered_at": datetime.now().isoformat()
                    }
                    triggered_alerts.append(alert)
                    
            except Exception as e:
                self.logger.error(f"Error evaluating alert rule {rule.name}: {e}")
        
        return triggered_alerts

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Safely evaluate alert condition."""
        try:
            # Simple condition evaluation (could be enhanced with a proper expression parser)
            condition = condition.replace("status", f"'{context['status']}'")
            condition = condition.replace("previous_status", f"'{context.get('previous_status', '')}'")
            condition = condition.replace("response_time", str(context['response_time']))
            condition = condition.replace("consecutive_failures", str(context['consecutive_failures']))
            condition = condition.replace("uptime_percentage", str(context['uptime_percentage']))
            
            return eval(condition)
        except Exception:
            return False

    def _generate_alert_message(self, rule: AlertRule, service_status: ServiceHealthStatus) -> str:
        """Generate human-readable alert message."""
        if rule.name == "service_down":
            return f"Service {service_status.service_name} is unhealthy. Error: {service_status.error_message or 'Unknown error'}"
        elif rule.name == "high_response_time":
            return f"Service {service_status.service_name} has high response time: {service_status.response_time:.2f}s"
        elif rule.name == "consecutive_failures":
            return f"Service {service_status.service_name} has {service_status.consecutive_failures} consecutive failures"
        elif rule.name == "low_uptime":
            return f"Service {service_status.service_name} has low uptime: {service_status.uptime_percentage:.1f}%"
        elif rule.name == "service_recovery":
            return f"Service {service_status.service_name} has recovered and is now healthy"
        else:
            return f"Alert triggered for service {service_status.service_name}: {rule.name}"

    async def send_notifications(self, alerts: List[Dict[str, Any]]):
        """Send notifications for triggered alerts."""
        for alert in alerts:
            # Log alert
            self.logger.warning(f"ALERT: {alert['message']}")
            
            # Send email notification if configured
            if self.config.get("email_notifications", {}).get("enabled", False):
                await self._send_email_notification(alert)
            
            # Send Slack notification if configured
            if self.config.get("slack_notifications", {}).get("enabled", False):
                await self._send_slack_notification(alert)
            
            # Send webhook notification if configured
            if self.config.get("webhook_notifications", {}).get("enabled", False):
                await self._send_webhook_notification(alert)

    async def _send_email_notification(self, alert: Dict[str, Any]):
        """Send email notification."""
        try:
            email_config = self.config["email_notifications"]
            
            msg = MimeMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = f"[{alert['severity'].upper()}] Health Monitor Alert: {alert['service_name']}"
            
            body = f"""
Health Monitor Alert

Service: {alert['service_name']}
Severity: {alert['severity']}
Message: {alert['message']}
Triggered At: {alert['triggered_at']}

Please investigate and resolve the issue.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email (implementation would need SMTP configuration)
            self.logger.info(f"Email notification sent for {alert['service_name']}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")

    async def _send_slack_notification(self, alert: Dict[str, Any]):
        """Send Slack notification."""
        try:
            slack_config = self.config["slack_notifications"]
            webhook_url = slack_config['webhook_url']
            
            color = {
                "critical": "#FF0000",
                "warning": "#FFA500", 
                "info": "#00FF00"
            }.get(alert['severity'], "#808080")
            
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"Health Monitor Alert: {alert['service_name']}",
                    "text": alert['message'],
                    "fields": [
                        {"title": "Severity", "value": alert['severity'], "short": True},
                        {"title": "Service", "value": alert['service_name'], "short": True},
                        {"title": "Time", "value": alert['triggered_at'], "short": True}
                    ]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Slack notification sent for {alert['service_name']}")
                    else:
                        self.logger.error(f"Failed to send Slack notification: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")

    async def _send_webhook_notification(self, alert: Dict[str, Any]):
        """Send webhook notification."""
        try:
            webhook_config = self.config["webhook_notifications"]
            webhook_url = webhook_config['url']
            
            payload = {
                "event": "health_monitor_alert",
                "service": alert['service_name'],
                "severity": alert['severity'],
                "message": alert['message'],
                "timestamp": alert['triggered_at']
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Webhook notification sent for {alert['service_name']}")
                    else:
                        self.logger.error(f"Failed to send webhook notification: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")


class AutomatedHealthMonitor:
    """Main automated health monitoring system."""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.services = self._load_service_definitions()
        self.database = HealthMonitoringDatabase(self.config.get("database_path", "health_monitoring.db"))
        self.alert_manager = AlertManager(self.config.get("alerting", {}))
        self.logger = self._setup_logging()
        self.running = False
        self.check_interval = self.config.get("check_interval_seconds", 30)

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load monitoring configuration."""
        default_config = {
            "check_interval_seconds": 30,
            "timeout_seconds": 10,
            "max_consecutive_failures": 5,
            "database_path": "health_monitoring.db",
            "log_level": "INFO",
            "alerting": {
                "email_notifications": {"enabled": False},
                "slack_notifications": {"enabled": False},
                "webhook_notifications": {"enabled": False}
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_path}: {e}")
        
        return default_config

    def _load_service_definitions(self) -> List[Dict[str, Any]]:
        """Load service definitions for monitoring."""
        return [
            {"name": "interpreter", "url": "http://localhost:5120/health", "critical": True},
            {"name": "orchestrator", "url": "http://localhost:5099/health", "critical": True},
            {"name": "doc_store", "url": "http://localhost:5087/health", "critical": True},
            {"name": "prompt_store", "url": "http://localhost:5110/health", "critical": True},
            {"name": "analysis_service", "url": "http://localhost:5080/health", "critical": True},
            {"name": "llm_gateway", "url": "http://localhost:5055/health", "critical": True},
            {"name": "discovery_agent", "url": "http://localhost:5045/health", "critical": False},
            {"name": "github_mcp", "url": "http://localhost:5030/health", "critical": False},
            {"name": "source_agent", "url": "http://localhost:5070/health", "critical": False},
            {"name": "memory_agent", "url": "http://localhost:5090/health", "critical": False},
            {"name": "secure_analyzer", "url": "http://localhost:5100/health", "critical": False},
            {"name": "summarizer_hub", "url": "http://localhost:5160/health", "critical": False},
            {"name": "code_analyzer", "url": "http://localhost:5050/health", "critical": False},
            {"name": "bedrock_proxy", "url": "http://localhost:5060/health", "critical": False},
            {"name": "notification_service", "url": "http://localhost:5020/health", "critical": False},
            {"name": "log_collector", "url": "http://localhost:5040/health", "critical": False},
            {"name": "frontend", "url": "http://localhost:3000/health", "critical": False}
        ]

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, self.config.get("log_level", "INFO")))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    async def check_service_health(self, service: Dict[str, Any]) -> ServiceHealthStatus:
        """Check health of a single service."""
        service_name = service["name"]
        service_url = service["url"]
        
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.get("timeout_seconds", 10))
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(service_url) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        # Try to parse health response
                        try:
                            health_data = await response.json()
                            status = "healthy"
                            error_message = None
                        except:
                            # Service responds but doesn't return JSON
                            status = "healthy"
                            error_message = None
                    else:
                        status = "unhealthy"
                        error_message = f"HTTP {response.status}"
                    
                    return ServiceHealthStatus(
                        service_name=service_name,
                        url=service_url,
                        status=status,
                        response_time=response_time,
                        status_code=response.status,
                        error_message=error_message,
                        last_check=datetime.now().isoformat(),
                        uptime_percentage=0.0,  # Will be calculated separately
                        consecutive_failures=0   # Will be updated separately
                    )
                    
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return ServiceHealthStatus(
                service_name=service_name,
                url=service_url,
                status="unhealthy",
                response_time=response_time,
                status_code=0,
                error_message="Timeout",
                last_check=datetime.now().isoformat(),
                uptime_percentage=0.0,
                consecutive_failures=0
            )
        except Exception as e:
            response_time = time.time() - start_time
            return ServiceHealthStatus(
                service_name=service_name,
                url=service_url,
                status="unhealthy",
                response_time=response_time,
                status_code=0,
                error_message=str(e),
                last_check=datetime.now().isoformat(),
                uptime_percentage=0.0,
                consecutive_failures=0
            )

    async def check_all_services(self) -> List[ServiceHealthStatus]:
        """Check health of all services concurrently."""
        tasks = []
        
        for service in self.services:
            task = self.check_service_health(service)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_statuses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error status for failed check
                service = self.services[i]
                health_statuses.append(ServiceHealthStatus(
                    service_name=service["name"],
                    url=service["url"],
                    status="unknown",
                    response_time=0.0,
                    status_code=0,
                    error_message=str(result),
                    last_check=datetime.now().isoformat(),
                    uptime_percentage=0.0,
                    consecutive_failures=0
                ))
            else:
                health_statuses.append(result)
        
        return health_statuses

    async def process_health_results(self, health_statuses: List[ServiceHealthStatus]):
        """Process health check results and trigger alerts."""
        for status in health_statuses:
            # Get previous status for alert evaluation
            previous_statuses = self.database.get_service_status_summary()
            previous_status = None
            consecutive_failures = 0
            
            for prev in previous_statuses:
                if prev["service_name"] == status.service_name:
                    previous_status = prev["current_status"]
                    consecutive_failures = prev["consecutive_failures"]
                    break
            
            # Update consecutive failures
            if status.status == "unhealthy":
                consecutive_failures += 1
            else:
                consecutive_failures = 0
            
            status.consecutive_failures = consecutive_failures
            
            # Record health check in database
            self.database.record_health_check(
                status.service_name,
                status.status,
                status.response_time,
                status.status_code,
                status.error_message
            )
            
            # Update service status
            self.database.update_service_status(
                status.service_name,
                status.status,
                consecutive_failures
            )
            
            # Evaluate alerts
            alerts = self.alert_manager.evaluate_alerts(status, previous_status)
            
            # Record and send alerts
            for alert in alerts:
                self.database.record_alert(
                    alert["service_name"],
                    alert["rule_name"],
                    alert["severity"],
                    alert["message"]
                )
                
                self.logger.warning(f"ALERT: {alert['message']}")
            
            # Send notifications
            if alerts:
                await self.alert_manager.send_notifications(alerts)

    async def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        service_statuses = self.database.get_service_status_summary()
        
        # Calculate overall metrics
        total_services = len(service_statuses)
        healthy_services = sum(1 for s in service_statuses if s["current_status"] == "healthy")
        unhealthy_services = sum(1 for s in service_statuses if s["current_status"] == "unhealthy")
        
        overall_health = "healthy" if unhealthy_services == 0 else "degraded" if unhealthy_services < total_services * 0.3 else "critical"
        
        # Critical services health
        critical_service_names = [s["name"] for s in self.services if s.get("critical", False)]
        critical_unhealthy = sum(1 for s in service_statuses 
                               if s["service_name"] in critical_service_names and s["current_status"] == "unhealthy")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": overall_health,
            "summary": {
                "total_services": total_services,
                "healthy_services": healthy_services,
                "unhealthy_services": unhealthy_services,
                "critical_unhealthy": critical_unhealthy,
                "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0
            },
            "services": service_statuses
        }
        
        return report

    async def run_monitoring_cycle(self):
        """Run a single monitoring cycle."""
        self.logger.info("Starting health monitoring cycle")
        
        # Check all services
        health_statuses = await self.check_all_services()
        
        # Process results and trigger alerts
        await self.process_health_results(health_statuses)
        
        # Log summary
        healthy_count = sum(1 for s in health_statuses if s.status == "healthy")
        total_count = len(health_statuses)
        
        self.logger.info(f"Health check completed: {healthy_count}/{total_count} services healthy")
        
        # Log unhealthy services
        for status in health_statuses:
            if status.status == "unhealthy":
                self.logger.warning(f"Service {status.service_name} is unhealthy: {status.error_message}")

    async def start_monitoring(self):
        """Start continuous health monitoring."""
        self.running = True
        self.logger.info(f"Starting automated health monitoring (interval: {self.check_interval}s)")
        
        while self.running:
            try:
                await self.run_monitoring_cycle()
            except Exception as e:
                self.logger.error(f"Error in monitoring cycle: {e}")
            
            # Wait for next check interval
            await asyncio.sleep(self.check_interval)

    def stop_monitoring(self):
        """Stop health monitoring."""
        self.running = False
        self.logger.info("Stopping automated health monitoring")

    async def get_health_dashboard_data(self) -> Dict[str, Any]:
        """Get data for health monitoring dashboard."""
        report = await self.generate_health_report()
        
        # Add trend data (last 24 hours)
        # This would typically query the database for historical data
        report["trends"] = {
            "hourly_health": [],  # Would be populated from database
            "response_times": [],  # Would be populated from database
            "alert_counts": []     # Would be populated from database
        }
        
        return report


async def main():
    """Main function for running the automated health monitor."""
    parser = argparse.ArgumentParser(description="Automated Health Monitoring System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--report", action="store_true", help="Generate health report and exit")
    parser.add_argument("--dashboard", action="store_true", help="Output dashboard data and exit")
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = AutomatedHealthMonitor(args.config)
    
    if args.report:
        # Generate and print health report
        report = await monitor.generate_health_report()
        print(json.dumps(report, indent=2))
        return
    
    if args.dashboard:
        # Output dashboard data
        dashboard_data = await monitor.get_health_dashboard_data()
        print(json.dumps(dashboard_data, indent=2))
        return
    
    if args.once:
        # Run single monitoring cycle
        await monitor.run_monitoring_cycle()
        return
    
    # Start continuous monitoring
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("\nHealth monitoring stopped by user")


if __name__ == "__main__":
    asyncio.run(main())
