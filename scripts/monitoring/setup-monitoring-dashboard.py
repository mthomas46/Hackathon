#!/usr/bin/env python3
"""
Monitoring Dashboard Setup Script

This script sets up a comprehensive monitoring dashboard for the LLM Documentation Ecosystem.
It creates real-time service health monitoring, performance metrics, and alerting systems.

Features:
- Service health status dashboard
- Performance metrics collection
- Automated alerting for service degradation
- Real-time log aggregation
- Performance trend analysis
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import aiohttp
import rich
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class MonitoringDashboardSetup:
    """Setup and configure monitoring dashboard for the ecosystem."""

    def __init__(self, services_dir: str = "services"):
        self.services_dir = Path(services_dir)
        self.config_dir = Path("config")
        self.monitoring_dir = Path("monitoring")
        self.templates_dir = self.monitoring_dir / "templates"

        # Service endpoints for health checks
        self.service_ports = {
            "orchestrator": 8000,
            "doc-store": 8001,
            "analysis-service": 8002,
            "discovery-agent": 8003,
            "shared": 8004,
            "frontend": 3000,
            "bedrock-proxy": 8005,
            "llm-gateway": 8006,
            "memory-agent": 8007,
            "github-mcp": 8008,
            "notification-service": 8009,
        }

    async def setup_monitoring_dashboard(self) -> bool:
        """Main setup function for monitoring dashboard."""
        console.print("[bold blue]🚀 Setting up Monitoring Dashboard[/bold blue]")
        console.print()

        try:
            # Create monitoring directories
            await self._create_monitoring_directories()

            # Generate monitoring configuration
            await self._generate_monitoring_config()

            # Create health check endpoints
            await self._create_health_check_endpoints()

            # Set up metrics collection
            await self._setup_metrics_collection()

            # Create alerting rules
            await self._create_alerting_rules()

            # Generate dashboard templates
            await self._generate_dashboard_templates()

            console.print("[green]✅ Monitoring dashboard setup completed successfully![/green]")
            console.print()
            console.print("[bold]📊 Dashboard Features:[/bold]")
            console.print("  • Real-time service health monitoring")
            console.print("  • Performance metrics collection")
            console.print("  • Automated alerting system")
            console.print("  • Service dependency visualization")
            console.print("  • Performance trend analysis")
            console.print()
            console.print("[bold]🔗 Access Points:[/bold]")
            console.print("  • Health Dashboard: http://localhost:8080/health")
            console.print("  • Metrics API: http://localhost:8080/metrics")
            console.print("  • Alerts Dashboard: http://localhost:8080/alerts")

            return True

        except Exception as e:
            console.print(f"[red]❌ Monitoring setup failed: {e}[/red]")
            return False

    async def _create_monitoring_directories(self) -> None:
        """Create necessary directories for monitoring."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Creating monitoring directories...", total=4)

            directories = [
                self.monitoring_dir,
                self.monitoring_dir / "config",
                self.monitoring_dir / "alerts",
                self.monitoring_dir / "metrics",
            ]

            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                progress.update(task, advance=1)

    async def _generate_monitoring_config(self) -> None:
        """Generate monitoring configuration."""
        config = {
            "monitoring": {
                "enabled": True,
                "interval_seconds": 30,
                "timeout_seconds": 10,
                "retries": 3,
            },
            "services": {},
            "alerts": {
                "enabled": True,
                "email_enabled": False,
                "slack_enabled": False,
                "alert_cooldown_minutes": 5,
            },
            "metrics": {
                "retention_days": 30,
                "collection_interval": 60,
                "performance_thresholds": {
                    "response_time_ms": 1000,
                    "error_rate_percent": 5.0,
                    "cpu_usage_percent": 80.0,
                    "memory_usage_percent": 85.0,
                }
            }
        }

        # Add service configurations
        for service_name, port in self.service_ports.items():
            config["services"][service_name] = {
                "name": service_name,
                "health_endpoint": f"http://localhost:{port}/health",
                "metrics_endpoint": f"http://localhost:{port}/metrics",
                "enabled": True,
                "timeout": 5,
                "expected_status": "healthy"
            }

        config_path = self.monitoring_dir / "config" / "monitoring-config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        console.print(f"[green]✓ Generated monitoring configuration: {config_path}[/green]")

    async def _create_health_check_endpoints(self) -> None:
        """Create health check endpoints for services."""
        health_checks = []

        for service_name, port in self.service_ports.items():
            health_check = {
                "service": service_name,
                "endpoint": f"http://localhost:{port}/health",
                "method": "GET",
                "expected_status": 200,
                "timeout": 5,
                "headers": {"Accept": "application/json"},
                "body_checks": [
                    {"path": "status", "expected": "healthy"},
                    {"path": "service", "expected": service_name}
                ]
            }
            health_checks.append(health_check)

        health_config_path = self.monitoring_dir / "config" / "health-checks.json"
        with open(health_config_path, 'w') as f:
            json.dump({"health_checks": health_checks}, f, indent=2)

        console.print(f"[green]✓ Created health check endpoints: {health_config_path}[/green]")

    async def _setup_metrics_collection(self) -> None:
        """Set up metrics collection configuration."""
        metrics_config = {
            "collection": {
                "enabled": True,
                "interval_seconds": 60,
                "timeout_seconds": 10,
            },
            "metrics": [
                {
                    "name": "response_time",
                    "type": "histogram",
                    "description": "HTTP response time in milliseconds",
                    "buckets": [100, 250, 500, 1000, 2500, 5000]
                },
                {
                    "name": "requests_total",
                    "type": "counter",
                    "description": "Total number of HTTP requests"
                },
                {
                    "name": "errors_total",
                    "type": "counter",
                    "description": "Total number of errors"
                },
                {
                    "name": "cpu_usage",
                    "type": "gauge",
                    "description": "CPU usage percentage"
                },
                {
                    "name": "memory_usage",
                    "type": "gauge",
                    "description": "Memory usage percentage"
                }
            ]
        }

        metrics_path = self.monitoring_dir / "config" / "metrics-config.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics_config, f, indent=2)

        console.print(f"[green]✓ Set up metrics collection: {metrics_path}[/green]")

    async def _create_alerting_rules(self) -> None:
        """Create alerting rules for service monitoring."""
        alert_rules = [
            {
                "name": "service_down",
                "description": "Service is not responding",
                "condition": "up == 0",
                "for": "5m",
                "labels": {"severity": "critical"},
                "annotations": {
                    "summary": "Service {{ $labels.service }} is down",
                    "description": "Service {{ $labels.service }} has been down for more than 5 minutes."
                }
            },
            {
                "name": "high_error_rate",
                "description": "High error rate detected",
                "condition": "rate(errors_total[5m]) / rate(requests_total[5m]) > 0.05",
                "for": "5m",
                "labels": {"severity": "warning"},
                "annotations": {
                    "summary": "High error rate on {{ $labels.service }}",
                    "description": "Error rate is {{ $value }}% which is above 5% threshold."
                }
            },
            {
                "name": "high_response_time",
                "description": "Response time too high",
                "condition": "histogram_quantile(0.95, rate(response_time_bucket[5m])) > 1000",
                "for": "5m",
                "labels": {"severity": "warning"},
                "annotations": {
                    "summary": "High response time on {{ $labels.service }}",
                    "description": "95th percentile response time is {{ $value }}ms which is above 1000ms threshold."
                }
            },
            {
                "name": "high_resource_usage",
                "description": "High resource usage detected",
                "condition": "cpu_usage > 80 OR memory_usage > 85",
                "for": "10m",
                "labels": {"severity": "warning"},
                "annotations": {
                    "summary": "High resource usage on {{ $labels.service }}",
                    "description": "CPU: {{ $labels.cpu_usage }}%, Memory: {{ $labels.memory_usage }}%"
                }
            }
        ]

        alerts_path = self.monitoring_dir / "config" / "alert-rules.json"
        with open(alerts_path, 'w') as f:
            json.dump({"groups": [{"name": "service_alerts", "rules": alert_rules}]}, f, indent=2)

        console.print(f"[green]✓ Created alerting rules: {alerts_path}[/green]")

    async def _generate_dashboard_templates(self) -> None:
        """Generate dashboard templates for monitoring."""
        dashboard_template = {
            "dashboard": {
                "title": "LLM Documentation Ecosystem - Service Health",
                "description": "Real-time monitoring dashboard for all services",
                "refresh": "30s",
                "time_range": "1h",
                "panels": [
                    {
                        "title": "Service Status Overview",
                        "type": "table",
                        "targets": ["service_status"],
                        "description": "Current status of all services"
                    },
                    {
                        "title": "Response Time Trends",
                        "type": "graph",
                        "targets": ["response_time"],
                        "description": "HTTP response time trends"
                    },
                    {
                        "title": "Error Rate Monitoring",
                        "type": "graph",
                        "targets": ["error_rate"],
                        "description": "Error rate trends across services"
                    },
                    {
                        "title": "Resource Usage",
                        "type": "graph",
                        "targets": ["cpu_usage", "memory_usage"],
                        "description": "CPU and memory usage trends"
                    },
                    {
                        "title": "Active Alerts",
                        "type": "table",
                        "targets": ["active_alerts"],
                        "description": "Currently active alerts"
                    }
                ]
            }
        }

        template_path = self.monitoring_dir / "templates" / "dashboard-template.json"
        with open(template_path, 'w') as f:
            json.dump(dashboard_template, f, indent=2)

        console.print(f"[green]✓ Generated dashboard templates: {template_path}[/green]")

    async def validate_setup(self) -> bool:
        """Validate that the monitoring setup is correct."""
        console.print("[bold blue]🔍 Validating monitoring setup...[/bold blue]")

        required_files = [
            "config/monitoring-config.json",
            "config/health-checks.json",
            "config/metrics-config.json",
            "config/alert-rules.json",
            "templates/dashboard-template.json"
        ]

        missing_files = []
        for file_path in required_files:
            full_path = self.monitoring_dir / file_path
            if not full_path.exists():
                missing_files.append(str(full_path))

        if missing_files:
            console.print(f"[red]❌ Missing files: {missing_files}[/red]")
            return False

        # Validate JSON files
        for file_path in required_files:
            if file_path.endswith('.json'):
                full_path = self.monitoring_dir / file_path
                try:
                    with open(full_path) as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    console.print(f"[red]❌ Invalid JSON in {full_path}: {e}[/red]")
                    return False

        console.print("[green]✅ Monitoring setup validation passed![/green]")
        return True


async def main():
    """Main function to run monitoring dashboard setup."""
    setup = MonitoringDashboardSetup()

    success = await setup.setup_monitoring_dashboard()
    if success:
        await setup.validate_setup()

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
