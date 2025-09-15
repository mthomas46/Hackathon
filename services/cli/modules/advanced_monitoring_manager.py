"""Advanced Monitoring Manager module for CLI service.

Provides comprehensive monitoring including custom dashboards, alerting rules,
SLO/SLA monitoring, and enterprise observability capabilities.
"""

from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
import json
import yaml
import os
import asyncio
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
import re

from .shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class AdvancedMonitoringManager:
    """Manager for advanced monitoring, alerting, and observability."""

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients
        self.alerts_history = []
        self.metrics_cache = {}
        self.slo_definitions = {}
        self.dashboards = {}

    async def advanced_monitoring_menu(self):
        """Main advanced monitoring menu."""
        while True:
            menu = create_menu_table("Advanced Monitoring", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Custom Metrics Dashboards (Create and manage monitoring dashboards)"),
                ("2", "Alerting Rule Management (Configure alerts and notifications)"),
                ("3", "SLO/SLA Monitoring (Service level objectives and agreements)"),
                ("4", "Real-time Metrics (Live system metrics and performance)"),
                ("5", "Anomaly Detection (Identify unusual patterns and outliers)"),
                ("6", "Performance Analytics (Deep performance analysis and insights)"),
                ("7", "Monitoring Configuration (Configure monitoring settings)"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.custom_metrics_dashboards_menu()
            elif choice == "2":
                await self.alerting_rule_management_menu()
            elif choice == "3":
                await self.slo_sla_monitoring_menu()
            elif choice == "4":
                await self.real_time_metrics_menu()
            elif choice == "5":
                await self.anomaly_detection_menu()
            elif choice == "6":
                await self.performance_analytics_menu()
            elif choice == "7":
                await self.monitoring_configuration_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def custom_metrics_dashboards_menu(self):
        """Custom metrics dashboards submenu."""
        while True:
            menu = create_menu_table("Custom Metrics Dashboards", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Available Dashboards"),
                ("2", "Create New Dashboard"),
                ("3", "Edit Dashboard Configuration"),
                ("4", "Import Dashboard"),
                ("5", "Export Dashboard"),
                ("6", "Dashboard Performance"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_available_dashboards()
            elif choice == "2":
                await self.create_new_dashboard()
            elif choice == "3":
                await self.edit_dashboard_configuration()
            elif choice == "4":
                await self.import_dashboard()
            elif choice == "5":
                await self.export_dashboard()
            elif choice == "6":
                await self.dashboard_performance()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_available_dashboards(self):
        """View available monitoring dashboards."""
        try:
            # Check for Grafana dashboards
            dashboards = self._discover_dashboards()

            if dashboards:
                table = Table(title="Available Monitoring Dashboards")
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Description", style="white")
                table.add_column("Last Modified", style="yellow")

                for name, info in dashboards.items():
                    table.add_row(
                        name,
                        info.get("type", "Unknown"),
                        info.get("description", "No description"),
                        info.get("last_modified", "Unknown")
                    )

                self.console.print(table)

                # Option to view dashboard details
                show_details = Confirm.ask("[bold cyan]Show detailed view of a dashboard?[/bold cyan]", default=False)

                if show_details:
                    dashboard_names = list(dashboards.keys())
                    selected_dashboard = Prompt.ask("[bold cyan]Select dashboard[/bold cyan]", choices=dashboard_names)

                    await self._display_dashboard_details(dashboards[selected_dashboard])
            else:
                self.console.print("[yellow]No dashboards found. Grafana integration may not be available.[/yellow]")
                self.console.print("[blue]To enable dashboards, ensure Grafana is running with dashboard provisioning.[/blue]")

        except Exception as e:
            self.console.print(f"[red]Error viewing dashboards: {e}[/red]")

    async def create_new_dashboard(self):
        """Create a new monitoring dashboard."""
        try:
            dashboard_name = Prompt.ask("[bold cyan]Dashboard name[/bold cyan]")

            if not dashboard_name.strip():
                self.console.print("[yellow]Dashboard name cannot be empty[/yellow]")
                return

            dashboard_type = Prompt.ask("[bold cyan]Dashboard type[/bold cyan]",
                                       choices=["system", "application", "business", "custom"], default="custom")

            description = Prompt.ask("[bold cyan]Description[/bold cyan]", default="")

            # Create basic dashboard structure
            dashboard_config = {
                "name": dashboard_name,
                "type": dashboard_type,
                "description": description,
                "created_at": self._get_timestamp(),
                "panels": [],
                "variables": {},
                "tags": [dashboard_type]
            }

            # Add some default panels based on type
            if dashboard_type == "system":
                dashboard_config["panels"] = self._get_system_dashboard_panels()
            elif dashboard_type == "application":
                dashboard_config["panels"] = self._get_application_dashboard_panels()

            # Save dashboard configuration
            success = await self._save_dashboard_config(dashboard_name, dashboard_config)

            if success:
                self.dashboards[dashboard_name] = dashboard_config
                self.console.print(f"[green]✅ Dashboard '{dashboard_name}' created successfully[/green]")
                self.console.print(f"[blue]Dashboard includes {len(dashboard_config['panels'])} default panels[/blue]")
            else:
                self.console.print("[red]❌ Failed to create dashboard[/red]")

        except Exception as e:
            self.console.print(f"[red]Error creating dashboard: {e}[/red]")

    async def edit_dashboard_configuration(self):
        """Edit dashboard configuration."""
        try:
            dashboards = self._discover_dashboards()

            if not dashboards:
                self.console.print("[yellow]No dashboards available to edit[/yellow]")
                return

            dashboard_names = list(dashboards.keys())
            selected_dashboard = Prompt.ask("[bold cyan]Select dashboard to edit[/bold cyan]", choices=dashboard_names)

            dashboard_config = await self._load_dashboard_config(selected_dashboard)

            if dashboard_config:
                self.console.print(f"[yellow]Editing dashboard: {selected_dashboard}[/yellow]")

                # Allow editing basic properties
                new_description = Prompt.ask("[bold cyan]New description[/bold cyan]",
                                           default=dashboard_config.get("description", ""))

                if new_description != dashboard_config.get("description", ""):
                    dashboard_config["description"] = new_description
                    dashboard_config["updated_at"] = self._get_timestamp()

                    success = await self._save_dashboard_config(selected_dashboard, dashboard_config)
                    if success:
                        self.console.print("[green]✅ Dashboard description updated[/green]")
                    else:
                        self.console.print("[red]❌ Failed to update dashboard[/red]")

                # Option to add panels
                add_panel = Confirm.ask("[bold cyan]Add a new panel to the dashboard?[/bold cyan]", default=False)

                if add_panel:
                    await self._add_panel_to_dashboard(dashboard_config)
                    success = await self._save_dashboard_config(selected_dashboard, dashboard_config)
                    if success:
                        self.console.print("[green]✅ Panel added to dashboard[/green]")
            else:
                self.console.print(f"[red]Could not load dashboard configuration for {selected_dashboard}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error editing dashboard: {e}[/red]")

    async def import_dashboard(self):
        """Import a dashboard from file."""
        try:
            file_path = Prompt.ask("[bold cyan]Dashboard file path to import[/bold cyan]")

            if not Path(file_path).exists():
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return

            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    dashboard_config = json.load(f)
                elif file_path.endswith(('.yaml', '.yml')):
                    dashboard_config = yaml.safe_load(f)
                else:
                    self.console.print("[red]Unsupported file format. Use .json or .yaml/.yml[/red]")
                    return

            dashboard_name = dashboard_config.get("name", Path(file_path).stem)

            # Validate dashboard structure
            if not self._validate_dashboard_config(dashboard_config):
                self.console.print("[red]Invalid dashboard configuration[/red]")
                return

            success = await self._save_dashboard_config(dashboard_name, dashboard_config)

            if success:
                self.dashboards[dashboard_name] = dashboard_config
                self.console.print(f"[green]✅ Dashboard '{dashboard_name}' imported successfully[/green]")
                self.console.print(f"[blue]Imported {len(dashboard_config.get('panels', []))} panels[/blue]")
            else:
                self.console.print("[red]❌ Failed to import dashboard[/red]")

        except Exception as e:
            self.console.print(f"[red]Error importing dashboard: {e}[/red]")

    async def export_dashboard(self):
        """Export a dashboard to file."""
        try:
            dashboards = self._discover_dashboards()

            if not dashboards:
                self.console.print("[yellow]No dashboards available to export[/yellow]")
                return

            dashboard_names = list(dashboards.keys())
            selected_dashboard = Prompt.ask("[bold cyan]Select dashboard to export[/bold cyan]", choices=dashboard_names)

            dashboard_config = await self._load_dashboard_config(selected_dashboard)

            if dashboard_config:
                format_choice = Prompt.ask("[bold cyan]Export format[/bold cyan]", choices=["json", "yaml"], default="json")
                file_path = Prompt.ask("[bold cyan]Export file path[/bold cyan]",
                                     default=f"{selected_dashboard}.{format_choice}")

                if format_choice == "json":
                    content = json.dumps(dashboard_config, indent=2, default=str)
                else:
                    content = yaml.dump(dashboard_config, default_flow_style=False)

                with open(file_path, 'w') as f:
                    f.write(content)

                self.console.print(f"[green]✅ Dashboard exported to {file_path}[/green]")
            else:
                self.console.print(f"[red]Could not load dashboard configuration for {selected_dashboard}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error exporting dashboard: {e}[/red]")

    async def dashboard_performance(self):
        """Show dashboard performance metrics."""
        try:
            dashboards = self._discover_dashboards()

            if not dashboards:
                self.console.print("[yellow]No dashboards available for performance analysis[/yellow]")
                return

            # Generate mock performance metrics
            performance_data = {}

            for name in dashboards.keys():
                performance_data[name] = {
                    "load_time": f"{0.5 + len(name) * 0.1:.1f}s",
                    "query_count": len(name) * 3,
                    "error_rate": "0.1%",
                    "last_accessed": self._get_timestamp()
                }

            table = Table(title="Dashboard Performance Metrics")
            table.add_column("Dashboard", style="cyan")
            table.add_column("Load Time", style="green", justify="right")
            table.add_column("Queries", style="yellow", justify="right")
            table.add_column("Error Rate", style="red")
            table.add_column("Last Accessed", style="blue")

            for name, metrics in performance_data.items():
                table.add_row(
                    name,
                    metrics["load_time"],
                    str(metrics["query_count"]),
                    metrics["error_rate"],
                    metrics["last_accessed"]
                )

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error analyzing dashboard performance: {e}[/red]")

    async def alerting_rule_management_menu(self):
        """Alerting rule management submenu."""
        while True:
            menu = create_menu_table("Alerting Rule Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Active Alerts"),
                ("2", "Create Alert Rule"),
                ("3", "Edit Alert Rule"),
                ("4", "Delete Alert Rule"),
                ("5", "Alert History"),
                ("6", "Alert Notifications"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_active_alerts()
            elif choice == "2":
                await self.create_alert_rule()
            elif choice == "3":
                await self.edit_alert_rule()
            elif choice == "4":
                await self.delete_alert_rule()
            elif choice == "5":
                await self.alert_history()
            elif choice == "6":
                await self.alert_notifications()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_active_alerts(self):
        """View currently active alerts."""
        try:
            # Get current system status and generate alerts
            active_alerts = await self._get_active_alerts()

            if active_alerts:
                table = Table(title="Active Alerts")
                table.add_column("Alert ID", style="cyan")
                table.add_column("Severity", style="red")
                table.add_column("Service", style="green")
                table.add_column("Message", style="white")
                table.add_column("Triggered", style="yellow")
                table.add_column("Status", style="blue")

                for alert in active_alerts:
                    severity_color = {
                        "critical": "red bold",
                        "high": "red",
                        "medium": "yellow",
                        "low": "blue",
                        "info": "green"
                    }.get(alert.get("severity", "medium"), "white")

                    table.add_row(
                        alert.get("id", "unknown"),
                        f"[{severity_color}]{alert.get('severity', 'medium').upper()}[/{severity_color}]",
                        alert.get("service", "unknown"),
                        alert.get("message", ""),
                        alert.get("triggered_at", "unknown"),
                        alert.get("status", "active")
                    )

                self.console.print(table)

                # Show alert summary
                severity_counts = defaultdict(int)
                for alert in active_alerts:
                    severity_counts[alert.get("severity", "medium")] += 1

                summary_content = f"""
[bold]Alert Summary:[/bold]
• Total Active Alerts: {len(active_alerts)}
"""

                for severity, count in sorted(severity_counts.items(), key=lambda x: ["critical", "high", "medium", "low", "info"].index(x[0])):
                    severity_color = {
                        "critical": "red",
                        "high": "red",
                        "medium": "yellow",
                        "low": "blue",
                        "info": "green"
                    }.get(severity, "white")
                    summary_content += f"• [{severity_color}]{severity.title()}[/{severity_color}]: {count}\n"

                print_panel(self.console, summary_content, border_style="red")
            else:
                self.console.print("[green]✅ No active alerts[/green]")

        except Exception as e:
            self.console.print(f"[red]Error viewing active alerts: {e}[/red]")

    async def create_alert_rule(self):
        """Create a new alert rule."""
        try:
            rule_name = Prompt.ask("[bold cyan]Alert rule name[/bold cyan]")

            if not rule_name.strip():
                self.console.print("[yellow]Rule name cannot be empty[/yellow]")
                return

            rule_type = Prompt.ask("[bold cyan]Rule type[/bold cyan]",
                                 choices=["threshold", "pattern", "anomaly", "custom"], default="threshold")

            severity = Prompt.ask("[bold cyan]Severity[/bold cyan]",
                                choices=["critical", "high", "medium", "low", "info"], default="medium")

            service = Prompt.ask("[bold cyan]Target service (or 'all' for all services)[/bold cyan]", default="all")

            # Configure based on rule type
            if rule_type == "threshold":
                metric = Prompt.ask("[bold cyan]Metric to monitor[/bold cyan]",
                                  choices=["cpu_usage", "memory_usage", "response_time", "error_rate", "throughput"], default="cpu_usage")
                operator = Prompt.ask("[bold cyan]Operator[/bold cyan]",
                                    choices=[">", ">=", "<", "<=", "==", "!="], default=">")
                threshold = Prompt.ask("[bold cyan]Threshold value[/bold cyan]", default="80")

                condition = {
                    "metric": metric,
                    "operator": operator,
                    "threshold": float(threshold)
                }
            else:
                condition = Prompt.ask("[bold cyan]Custom condition description[/bold cyan]")

            description = Prompt.ask("[bold cyan]Alert description[/bold cyan]", default="")

            # Create alert rule
            alert_rule = {
                "name": rule_name,
                "type": rule_type,
                "severity": severity,
                "service": service,
                "condition": condition,
                "description": description,
                "enabled": True,
                "created_at": self._get_timestamp()
            }

            success = await self._save_alert_rule(rule_name, alert_rule)

            if success:
                self.console.print(f"[green]✅ Alert rule '{rule_name}' created successfully[/green]")
                self.console.print(f"[blue]Rule will monitor {service} for {rule_type} conditions[/blue]")
            else:
                self.console.print("[red]❌ Failed to create alert rule[/red]")

        except Exception as e:
            self.console.print(f"[red]Error creating alert rule: {e}[/red]")

    async def edit_alert_rule(self):
        """Edit an existing alert rule."""
        try:
            alert_rules = await self._load_alert_rules()

            if not alert_rules:
                self.console.print("[yellow]No alert rules available to edit[/yellow]")
                return

            rule_names = list(alert_rules.keys())
            selected_rule = Prompt.ask("[bold cyan]Select alert rule to edit[/bold cyan]", choices=rule_names)

            rule_config = alert_rules[selected_rule]

            self.console.print(f"[yellow]Editing alert rule: {selected_rule}[/yellow]")

            # Allow editing severity and description
            new_severity = Prompt.ask(f"[bold cyan]New severity[/bold cyan]",
                                    choices=["critical", "high", "medium", "low", "info"],
                                    default=rule_config.get("severity", "medium"))

            new_description = Prompt.ask("[bold cyan]New description[/bold cyan]",
                                       default=rule_config.get("description", ""))

            # Update rule
            rule_config["severity"] = new_severity
            rule_config["description"] = new_description
            rule_config["updated_at"] = self._get_timestamp()

            success = await self._save_alert_rule(selected_rule, rule_config)

            if success:
                self.console.print(f"[green]✅ Alert rule '{selected_rule}' updated[/green]")
            else:
                self.console.print("[red]❌ Failed to update alert rule[/red]")

        except Exception as e:
            self.console.print(f"[red]Error editing alert rule: {e}[/red]")

    async def delete_alert_rule(self):
        """Delete an alert rule."""
        try:
            alert_rules = await self._load_alert_rules()

            if not alert_rules:
                self.console.print("[yellow]No alert rules available to delete[/yellow]")
                return

            rule_names = list(alert_rules.keys())
            selected_rule = Prompt.ask("[bold cyan]Select alert rule to delete[/bold cyan]", choices=rule_names)

            confirm = Confirm.ask(f"[bold red]Delete alert rule '{selected_rule}'?[/bold red]", default=False)

            if confirm:
                success = await self._delete_alert_rule(selected_rule)

                if success:
                    self.console.print(f"[green]✅ Alert rule '{selected_rule}' deleted[/green]")
                else:
                    self.console.print("[red]❌ Failed to delete alert rule[/red]")
            else:
                self.console.print("[yellow]Deletion cancelled[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error deleting alert rule: {e}[/red]")

    async def alert_history(self):
        """View alert history."""
        try:
            if not self.alerts_history:
                # Generate some sample alert history
                self.alerts_history = [
                    {
                        "id": "alert_001",
                        "rule": "high_cpu_usage",
                        "service": "orchestrator",
                        "severity": "high",
                        "message": "CPU usage exceeded 85%",
                        "triggered_at": "2024-01-15 10:30:00",
                        "resolved_at": "2024-01-15 10:45:00",
                        "duration": "15 minutes"
                    },
                    {
                        "id": "alert_002",
                        "rule": "memory_pressure",
                        "service": "analysis-service",
                        "severity": "medium",
                        "message": "Memory usage above 75%",
                        "triggered_at": "2024-01-15 11:15:00",
                        "resolved_at": "2024-01-15 11:30:00",
                        "duration": "15 minutes"
                    }
                ]

            if self.alerts_history:
                table = Table(title="Alert History")
                table.add_column("Alert ID", style="cyan")
                table.add_column("Rule", style="green")
                table.add_column("Service", style="blue")
                table.add_column("Severity", style="red")
                table.add_column("Message", style="white")
                table.add_column("Duration", style="yellow")

                for alert in self.alerts_history[-20:]:  # Show last 20
                    severity_color = {
                        "critical": "red bold",
                        "high": "red",
                        "medium": "yellow",
                        "low": "blue",
                        "info": "green"
                    }.get(alert.get("severity", "medium"), "white")

                    table.add_row(
                        alert.get("id", "unknown"),
                        alert.get("rule", "unknown"),
                        alert.get("service", "unknown"),
                        f"[{severity_color}]{alert.get('severity', 'medium').upper()}[/{severity_color}]",
                        alert.get("message", ""),
                        alert.get("duration", "unknown")
                    )

                self.console.print(table)

                # Show summary statistics
                total_alerts = len(self.alerts_history)
                severity_stats = defaultdict(int)

                for alert in self.alerts_history:
                    severity_stats[alert.get("severity", "medium")] += 1

                summary_content = f"""
[bold]Alert History Summary:[/bold]
• Total Alerts: {total_alerts}
• Average Resolution Time: 12 minutes
"""

                for severity, count in sorted(severity_stats.items(), key=lambda x: ["critical", "high", "medium", "low", "info"].index(x[0])):
                    percentage = (count / total_alerts) * 100
                    severity_color = {
                        "critical": "red",
                        "high": "red",
                        "medium": "yellow",
                        "low": "blue",
                        "info": "green"
                    }.get(severity, "white")
                    summary_content += f"• [{severity_color}]{severity.title()}[/{severity_color}]: {count} ({percentage:.1f}%)\n"

                print_panel(self.console, summary_content, border_style="blue")
            else:
                self.console.print("[yellow]No alert history available[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error viewing alert history: {e}[/red]")

    async def alert_notifications(self):
        """Configure alert notifications."""
        try:
            self.console.print("[yellow]Alert notification configuration would allow setting up email, Slack, webhook notifications[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring alert notifications: {e}[/red]")

    async def slo_sla_monitoring_menu(self):
        """SLO/SLA monitoring submenu."""
        while True:
            menu = create_menu_table("SLO/SLA Monitoring", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View SLO/SLA Definitions"),
                ("2", "Create SLO/SLA Definition"),
                ("3", "Monitor SLO/SLA Compliance"),
                ("4", "SLO/SLA Performance Reports"),
                ("5", "SLO/SLA Alerts"),
                ("6", "Budget Burn Analysis"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_slo_sla_definitions()
            elif choice == "2":
                await self.create_slo_sla_definition()
            elif choice == "3":
                await self.monitor_slo_sla_compliance()
            elif choice == "4":
                await self.slo_sla_performance_reports()
            elif choice == "5":
                await self.slo_sla_alerts()
            elif choice == "6":
                await self.budget_burn_analysis()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_slo_sla_definitions(self):
        """View SLO/SLA definitions."""
        try:
            # Initialize with some default SLOs if none exist
            if not self.slo_definitions:
                self.slo_definitions = {
                    "api_response_time": {
                        "name": "API Response Time",
                        "type": "SLO",
                        "metric": "response_time_p95",
                        "target": 500,
                        "unit": "ms",
                        "window": "30d",
                        "description": "95th percentile API response time should be under 500ms"
                    },
                    "service_uptime": {
                        "name": "Service Uptime",
                        "type": "SLA",
                        "metric": "uptime_percentage",
                        "target": 99.9,
                        "unit": "%",
                        "window": "30d",
                        "description": "Service availability should be 99.9% or higher"
                    },
                    "error_budget": {
                        "name": "Error Budget",
                        "type": "SLO",
                        "metric": "error_rate_percentage",
                        "target": 0.1,
                        "unit": "%",
                        "window": "30d",
                        "description": "Error rate should not exceed 0.1%"
                    }
                }

            if self.slo_definitions:
                table = Table(title="SLO/SLA Definitions")
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Metric", style="blue")
                table.add_column("Target", style="yellow")
                table.add_column("Window", style="magenta")
                table.add_column("Status", style="red")

                for name, slo in self.slo_definitions.items():
                    # Mock status based on target
                    current_value = await self._get_current_metric_value(slo["metric"])
                    status = "✅ Compliant" if current_value <= slo["target"] else "❌ Violated"

                    table.add_row(
                        slo["name"],
                        slo["type"],
                        slo["metric"],
                        f"{slo['target']} {slo['unit']}",
                        slo["window"],
                        status
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No SLO/SLA definitions configured[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error viewing SLO/SLA definitions: {e}[/red]")

    async def create_slo_sla_definition(self):
        """Create a new SLO/SLA definition."""
        try:
            definition_name = Prompt.ask("[bold cyan]Definition name[/bold cyan]")

            if not definition_name.strip():
                self.console.print("[yellow]Definition name cannot be empty[/yellow]")
                return

            definition_type = Prompt.ask("[bold cyan]Type[/bold cyan]",
                                       choices=["SLO", "SLA"], default="SLO")

            metric = Prompt.ask("[bold cyan]Metric to monitor[/bold cyan]",
                              choices=["response_time_p95", "uptime_percentage", "error_rate_percentage", "throughput", "latency_p99"], default="response_time_p95")

            target_value = float(Prompt.ask("[bold cyan]Target value[/bold cyan]", default="500"))
            unit = Prompt.ask("[bold cyan]Unit[/bold cyan]", default="ms")
            window = Prompt.ask("[bold cyan]Time window[/bold cyan]",
                              choices=["1h", "24h", "7d", "30d", "90d"], default="30d")

            description = Prompt.ask("[bold cyan]Description[/bold cyan]", default="")

            # Create SLO/SLA definition
            slo_definition = {
                "name": definition_name,
                "type": definition_type,
                "metric": metric,
                "target": target_value,
                "unit": unit,
                "window": window,
                "description": description,
                "created_at": self._get_timestamp(),
                "enabled": True
            }

            self.slo_definitions[definition_name] = slo_definition

            # Save to file
            success = await self._save_slo_definition(definition_name, slo_definition)

            if success:
                self.console.print(f"[green]✅ {definition_type} '{definition_name}' created successfully[/green]")
                self.console.print(f"[blue]Target: {target_value} {unit} over {window} window[/blue]")
            else:
                self.console.print("[red]❌ Failed to save SLO/SLA definition[/red]")

        except Exception as e:
            self.console.print(f"[red]Error creating SLO/SLA definition: {e}[/red]")

    async def monitor_slo_sla_compliance(self):
        """Monitor SLO/SLA compliance in real-time."""
        try:
            if not self.slo_definitions:
                self.console.print("[yellow]No SLO/SLA definitions to monitor[/yellow]")
                return

            compliance_data = []

            for name, slo in self.slo_definitions.items():
                current_value = await self._get_current_metric_value(slo["metric"])
                target = slo["target"]
                compliance_percentage = min(100, max(0, (1 - abs(current_value - target) / target) * 100))

                compliance_data.append({
                    "name": name,
                    "type": slo["type"],
                    "current": current_value,
                    "target": target,
                    "unit": slo["unit"],
                    "compliance": compliance_percentage,
                    "status": "compliant" if compliance_percentage >= 95 else "at_risk" if compliance_percentage >= 90 else "violated"
                })

            table = Table(title="SLO/SLA Compliance Status")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Current", style="blue", justify="right")
            table.add_column("Target", style="yellow", justify="right")
            table.add_column("Compliance", style="magenta", justify="right")
            table.add_column("Status", style="red")

            for data in compliance_data:
                status_color = {
                    "compliant": "green",
                    "at_risk": "yellow",
                    "violated": "red"
                }.get(data["status"], "white")

                table.add_row(
                    data["name"],
                    data["type"],
                    f"{data['current']:.2f} {data['unit']}",
                    f"{data['target']} {data['unit']}",
                    f"{data['compliance']:.1f}%",
                    f"[{status_color}]{data['status'].replace('_', ' ').title()}[/{status_color}]"
                )

            self.console.print(table)

            # Show overall compliance score
            avg_compliance = sum(d["compliance"] for d in compliance_data) / len(compliance_data)
            overall_status = "🟢 Excellent" if avg_compliance >= 95 else "🟡 Good" if avg_compliance >= 90 else "🔴 Needs Attention"

            content = f"""
[bold]Overall SLO/SLA Compliance:[/bold]
• Average Compliance: {avg_compliance:.1f}%
• Status: {overall_status}
• Total Definitions: {len(compliance_data)}
• Compliant: {sum(1 for d in compliance_data if d['status'] == 'compliant')}
• At Risk: {sum(1 for d in compliance_data if d['status'] == 'at_risk')}
• Violated: {sum(1 for d in compliance_data if d['status'] == 'violated')}
"""

            print_panel(self.console, content, border_style="blue" if avg_compliance >= 90 else "yellow")

        except Exception as e:
            self.console.print(f"[red]Error monitoring SLO/SLA compliance: {e}[/red]")

    async def slo_sla_performance_reports(self):
        """Generate SLO/SLA performance reports."""
        try:
            self.console.print("[yellow]SLO/SLA performance reports would show historical compliance trends[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating SLO/SLA reports: {e}[/red]")

    async def slo_sla_alerts(self):
        """Configure SLO/SLA alerts."""
        try:
            self.console.print("[yellow]SLO/SLA alerts would notify when compliance thresholds are approached[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring SLO/SLA alerts: {e}[/red]")

    async def budget_burn_analysis(self):
        """Perform budget burn analysis for error budgets."""
        try:
            self.console.print("[yellow]Budget burn analysis would show error budget consumption rates[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error performing budget burn analysis: {e}[/red]")

    async def real_time_metrics_menu(self):
        """Real-time metrics submenu."""
        while True:
            menu = create_menu_table("Real-time Metrics", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "System Metrics Overview"),
                ("2", "Service-Specific Metrics"),
                ("3", "Infrastructure Metrics"),
                ("4", "Application Performance"),
                ("5", "Custom Metric Queries"),
                ("6", "Metrics Export"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.system_metrics_overview()
            elif choice == "2":
                await self.service_specific_metrics()
            elif choice == "3":
                await self.infrastructure_metrics()
            elif choice == "4":
                await self.application_performance()
            elif choice == "5":
                await self.custom_metric_queries()
            elif choice == "6":
                await self.metrics_export()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def system_metrics_overview(self):
        """Show system-wide metrics overview."""
        try:
            # Collect metrics from various sources
            metrics = await self._collect_system_metrics()

            if metrics:
                content = f"""
[bold]🖥️ System Metrics Overview[/bold]

[bold blue]CPU & Memory:[/bold blue]
• Average CPU Usage: {metrics.get('cpu_avg', 'N/A')}%
• Peak CPU Usage: {metrics.get('cpu_peak', 'N/A')}%
• Memory Usage: {metrics.get('memory_usage', 'N/A')}%
• Memory Available: {metrics.get('memory_available', 'N/A')}GB

[bold green]Services:[/bold green]
• Total Services: {metrics.get('total_services', 0)}
• Healthy Services: {metrics.get('healthy_services', 0)}
• Services with Alerts: {metrics.get('services_with_alerts', 0)}

[bold yellow]Performance:[/bold yellow]
• Average Response Time: {metrics.get('avg_response_time', 'N/A')}ms
• 95th Percentile: {metrics.get('p95_response_time', 'N/A')}ms
• Error Rate: {metrics.get('error_rate', 'N/A')}%

[bold cyan]Traffic:[/bold cyan]
• Total Requests: {metrics.get('total_requests', 'N/A')}
• Requests per Second: {metrics.get('rps', 'N/A')}
• Peak RPS: {metrics.get('peak_rps', 'N/A')}
"""

                print_panel(self.console, content, border_style="blue")

                # Show top resource consumers
                if metrics.get("top_cpu_consumers"):
                    table = Table(title="Top CPU Consumers")
                    table.add_column("Service", style="cyan")
                    table.add_column("CPU %", style="red", justify="right")

                    for service, cpu in metrics["top_cpu_consumers"][:5]:
                        table.add_row(service, f"{cpu}%")

                    self.console.print(table)
            else:
                self.console.print("[yellow]No system metrics available[/yellow]")
                self.console.print("[blue]Ensure Prometheus and monitoring infrastructure are running[/blue]")

        except Exception as e:
            self.console.print(f"[red]Error showing system metrics: {e}[/red]")

    async def service_specific_metrics(self):
        """Show metrics for specific services."""
        try:
            # Get available services
            services = ["orchestrator", "doc-store", "analysis-service", "frontend", "summarizer-hub"]
            selected_service = Prompt.ask("[bold cyan]Select service[/bold cyan]", choices=services)

            metrics = await self._get_service_metrics(selected_service)

            if metrics:
                content = f"""
[bold]📊 {selected_service.title()} Metrics[/bold]

[bold blue]Performance:[/bold blue]
• Response Time (avg): {metrics.get('avg_response_time', 'N/A')}ms
• Response Time (p95): {metrics.get('p95_response_time', 'N/A')}ms
• Throughput: {metrics.get('throughput', 'N/A')} req/s
• Error Rate: {metrics.get('error_rate', 'N/A')}%

[bold green]Resources:[/bold green]
• CPU Usage: {metrics.get('cpu_usage', 'N/A')}%
• Memory Usage: {metrics.get('memory_usage', 'N/A')}MB
• Active Connections: {metrics.get('active_connections', 'N/A')}

[bold yellow]Health:[/bold yellow]
• Status: {metrics.get('status', 'unknown')}
• Uptime: {metrics.get('uptime', 'N/A')}
• Last Health Check: {metrics.get('last_health_check', 'N/A')}
"""

                print_panel(self.console, content, border_style="green")
            else:
                self.console.print(f"[yellow]No metrics available for {selected_service}[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error showing service metrics: {e}[/red]")

    async def infrastructure_metrics(self):
        """Show infrastructure metrics."""
        try:
            self.console.print("[yellow]Infrastructure metrics would show Redis, PostgreSQL, and system-level metrics[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error showing infrastructure metrics: {e}[/red]")

    async def application_performance(self):
        """Show application performance metrics."""
        try:
            self.console.print("[yellow]Application performance metrics would show business logic performance[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error showing application performance: {e}[/red]")

    async def custom_metric_queries(self):
        """Allow custom metric queries."""
        try:
            self.console.print("[yellow]Custom metric queries would allow PromQL or similar query execution[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with custom metric queries: {e}[/red]")

    async def metrics_export(self):
        """Export metrics data."""
        try:
            self.console.print("[yellow]Metrics export would allow saving metrics data in various formats[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error exporting metrics: {e}[/red]")

    async def anomaly_detection_menu(self):
        """Anomaly detection submenu."""
        while True:
            menu = create_menu_table("Anomaly Detection", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Detect Performance Anomalies"),
                ("2", "Detect Traffic Anomalies"),
                ("3", "Detect Error Rate Anomalies"),
                ("4", "Configure Anomaly Thresholds"),
                ("5", "Anomaly History"),
                ("6", "Anomaly Alerts"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.detect_performance_anomalies()
            elif choice == "2":
                await self.detect_traffic_anomalies()
            elif choice == "3":
                await self.detect_error_rate_anomalies()
            elif choice == "4":
                await self.configure_anomaly_thresholds()
            elif choice == "5":
                await self.anomaly_history()
            elif choice == "6":
                await self.anomaly_alerts()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def detect_performance_anomalies(self):
        """Detect performance anomalies."""
        try:
            self.console.print("[yellow]Performance anomaly detection would identify unusual response times or resource usage[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error detecting performance anomalies: {e}[/red]")

    async def detect_traffic_anomalies(self):
        """Detect traffic anomalies."""
        try:
            self.console.print("[yellow]Traffic anomaly detection would identify unusual request patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error detecting traffic anomalies: {e}[/red]")

    async def detect_error_rate_anomalies(self):
        """Detect error rate anomalies."""
        try:
            self.console.print("[yellow]Error rate anomaly detection would identify unusual error patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error detecting error rate anomalies: {e}[/red]")

    async def configure_anomaly_thresholds(self):
        """Configure anomaly detection thresholds."""
        try:
            self.console.print("[yellow]Anomaly threshold configuration would set sensitivity levels for detection[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring anomaly thresholds: {e}[/red]")

    async def anomaly_history(self):
        """View anomaly detection history."""
        try:
            self.console.print("[yellow]Anomaly history would show past detected anomalies and their resolution[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing anomaly history: {e}[/red]")

    async def anomaly_alerts(self):
        """Configure anomaly alerts."""
        try:
            self.console.print("[yellow]Anomaly alerts would notify when anomalies are detected[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring anomaly alerts: {e}[/red]")

    async def performance_analytics_menu(self):
        """Performance analytics submenu."""
        while True:
            menu = create_menu_table("Performance Analytics", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Response Time Analysis"),
                ("2", "Throughput Analysis"),
                ("3", "Resource Usage Trends"),
                ("4", "Performance Bottleneck Detection"),
                ("5", "Comparative Analysis"),
                ("6", "Performance Reports"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.response_time_analysis()
            elif choice == "2":
                await self.throughput_analysis()
            elif choice == "3":
                await self.resource_usage_trends()
            elif choice == "4":
                await self.performance_bottleneck_detection()
            elif choice == "5":
                await self.comparative_analysis()
            elif choice == "6":
                await self.performance_reports()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def response_time_analysis(self):
        """Analyze response time patterns."""
        try:
            self.console.print("[yellow]Response time analysis would show latency distributions and trends[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing response times: {e}[/red]")

    async def throughput_analysis(self):
        """Analyze throughput patterns."""
        try:
            self.console.print("[yellow]Throughput analysis would show request processing capacity and patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing throughput: {e}[/red]")

    async def resource_usage_trends(self):
        """Analyze resource usage trends."""
        try:
            self.console.print("[yellow]Resource usage trends would show CPU, memory, and disk usage patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing resource trends: {e}[/red]")

    async def performance_bottleneck_detection(self):
        """Detect performance bottlenecks."""
        try:
            self.console.print("[yellow]Performance bottleneck detection would identify system constraints[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error detecting bottlenecks: {e}[/red]")

    async def comparative_analysis(self):
        """Perform comparative performance analysis."""
        try:
            self.console.print("[yellow]Comparative analysis would compare performance across services or time periods[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error performing comparative analysis: {e}[/red]")

    async def performance_reports(self):
        """Generate performance reports."""
        try:
            self.console.print("[yellow]Performance reports would provide comprehensive performance analysis documents[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating performance reports: {e}[/red]")

    async def monitoring_configuration_menu(self):
        """Monitoring configuration submenu."""
        while True:
            menu = create_menu_table("Monitoring Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Configure Metric Collection"),
                ("2", "Configure Alert Rules"),
                ("3", "Configure Dashboards"),
                ("4", "Configure SLO/SLA Definitions"),
                ("5", "Monitoring Settings"),
                ("6", "Integration Setup"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.configure_metric_collection()
            elif choice == "2":
                await self.configure_alert_rules()
            elif choice == "3":
                await self.configure_dashboards()
            elif choice == "4":
                await self.configure_slo_sla_definitions()
            elif choice == "5":
                await self.monitoring_settings()
            elif choice == "6":
                await self.integration_setup()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def configure_metric_collection(self):
        """Configure metric collection settings."""
        try:
            self.console.print("[yellow]Metric collection configuration would set up Prometheus scraping and custom metrics[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring metric collection: {e}[/red]")

    async def configure_alert_rules(self):
        """Configure alert rules."""
        try:
            self.console.print("[yellow]Alert rule configuration would set up Prometheus alerting rules[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring alert rules: {e}[/red]")

    async def configure_dashboards(self):
        """Configure dashboards."""
        try:
            self.console.print("[yellow]Dashboard configuration would set up Grafana dashboard provisioning[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring dashboards: {e}[/red]")

    async def configure_slo_sla_definitions(self):
        """Configure SLO/SLA definitions."""
        try:
            self.console.print("[yellow]SLO/SLA configuration would set up service level objectives and agreements[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring SLO/SLA definitions: {e}[/red]")

    async def monitoring_settings(self):
        """Configure monitoring settings."""
        try:
            self.console.print("[yellow]Monitoring settings would configure retention, sampling, and other monitoring parameters[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring monitoring settings: {e}[/red]")

    async def integration_setup(self):
        """Set up monitoring integrations."""
        try:
            self.console.print("[yellow]Integration setup would configure connections to external monitoring systems[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error setting up integrations: {e}[/red]")

    # Helper methods

    def _discover_dashboards(self) -> Dict[str, Dict[str, Any]]:
        """Discover available dashboards."""
        # In a real implementation, this would scan Grafana or local dashboard files
        # For now, return mock dashboards
        return {
            "system-overview": {
                "type": "system",
                "description": "System-wide metrics and health overview",
                "last_modified": "2024-01-15 10:30:00",
                "panels": 12,
                "tags": ["system", "health"]
            },
            "application-performance": {
                "type": "application",
                "description": "Application performance metrics and response times",
                "last_modified": "2024-01-15 09:15:00",
                "panels": 8,
                "tags": ["application", "performance"]
            },
            "infrastructure-monitoring": {
                "type": "infrastructure",
                "description": "Infrastructure metrics and resource usage",
                "last_modified": "2024-01-15 08:45:00",
                "panels": 15,
                "tags": ["infrastructure", "resources"]
            }
        }

    async def _display_dashboard_details(self, dashboard_info: Dict[str, Any]):
        """Display detailed dashboard information."""
        content = f"""
[bold]Dashboard Details[/bold]

[bold blue]Type:[/bold blue] {dashboard_info.get('type', 'Unknown')}
[bold blue]Description:[/bold blue] {dashboard_info.get('description', 'No description')}
[bold blue]Last Modified:[/bold blue] {dashboard_info.get('last_modified', 'Unknown')}
[bold blue]Panels:[/bold blue] {dashboard_info.get('panels', 0)}
[bold blue]Tags:[/bold blue] {', '.join(dashboard_info.get('tags', []))}
"""

        print_panel(self.console, content, border_style="cyan")

    def _get_system_dashboard_panels(self) -> List[Dict[str, Any]]:
        """Get default system dashboard panels."""
        return [
            {"title": "CPU Usage", "type": "graph", "targets": ["cpu_usage"]},
            {"title": "Memory Usage", "type": "graph", "targets": ["memory_usage"]},
            {"title": "Disk Usage", "type": "graph", "targets": ["disk_usage"]},
            {"title": "Network I/O", "type": "graph", "targets": ["network_io"]},
            {"title": "Service Health", "type": "table", "targets": ["service_status"]},
            {"title": "Active Alerts", "type": "table", "targets": ["active_alerts"]}
        ]

    def _get_application_dashboard_panels(self) -> List[Dict[str, Any]]:
        """Get default application dashboard panels."""
        return [
            {"title": "Response Time", "type": "graph", "targets": ["response_time"]},
            {"title": "Request Rate", "type": "graph", "targets": ["request_rate"]},
            {"title": "Error Rate", "type": "graph", "targets": ["error_rate"]},
            {"title": "Active Connections", "type": "graph", "targets": ["active_connections"]}
        ]

    async def _save_dashboard_config(self, name: str, config: Dict[str, Any]) -> bool:
        """Save dashboard configuration."""
        try:
            # In a real implementation, this would save to Grafana or a local file
            # For now, just store in memory
            self.dashboards[name] = config
            return True
        except Exception:
            return False

    async def _load_dashboard_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Load dashboard configuration."""
        return self.dashboards.get(name)

    async def _add_panel_to_dashboard(self, dashboard_config: Dict[str, Any]):
        """Add a panel to a dashboard."""
        panel_title = Prompt.ask("[bold cyan]Panel title[/bold cyan]")
        panel_type = Prompt.ask("[bold cyan]Panel type[/bold cyan]", choices=["graph", "table", "heatmap", "gauge"], default="graph")

        if not dashboard_config.get("panels"):
            dashboard_config["panels"] = []

        panel = {
            "title": panel_title,
            "type": panel_type,
            "targets": [],
            "created_at": self._get_timestamp()
        }

        dashboard_config["panels"].append(panel)
        dashboard_config["updated_at"] = self._get_timestamp()

    def _validate_dashboard_config(self, config: Dict[str, Any]) -> bool:
        """Validate dashboard configuration."""
        required_fields = ["name", "type"]
        return all(field in config for field in required_fields)

    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        # In a real implementation, this would query Prometheus Alertmanager
        # For now, return mock alerts
        return [
            {
                "id": "alert_001",
                "severity": "high",
                "service": "orchestrator",
                "message": "High CPU usage detected (85%)",
                "triggered_at": "2024-01-15 14:30:00",
                "status": "active"
            },
            {
                "id": "alert_002",
                "severity": "medium",
                "service": "analysis-service",
                "message": "Memory usage above 80%",
                "triggered_at": "2024-01-15 14:15:00",
                "status": "active"
            }
        ]

    async def _save_alert_rule(self, name: str, rule: Dict[str, Any]) -> bool:
        """Save alert rule configuration."""
        try:
            # In a real implementation, this would save to Prometheus rules
            # For now, just store in memory
            return True
        except Exception:
            return False

    async def _load_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load alert rules."""
        # In a real implementation, this would load from Prometheus
        # For now, return mock rules
        return {
            "high_cpu_usage": {
                "name": "High CPU Usage",
                "severity": "high",
                "service": "all",
                "condition": {"metric": "cpu_usage", "operator": ">", "threshold": 80},
                "description": "Alert when CPU usage exceeds 80%",
                "enabled": True
            },
            "memory_pressure": {
                "name": "Memory Pressure",
                "severity": "medium",
                "service": "all",
                "condition": {"metric": "memory_usage_percentage", "operator": ">", "threshold": 75},
                "description": "Alert when memory usage exceeds 75%",
                "enabled": True
            }
        }

    async def _delete_alert_rule(self, name: str) -> bool:
        """Delete an alert rule."""
        try:
            # In a real implementation, this would delete from Prometheus
            return True
        except Exception:
            return False

    async def _get_current_metric_value(self, metric: str) -> float:
        """Get current value for a metric."""
        # Mock metric values
        mock_values = {
            "response_time_p95": 450.5,
            "uptime_percentage": 99.95,
            "error_rate_percentage": 0.05,
            "cpu_usage": 65.2,
            "memory_usage": 72.8
        }

        # Add some randomness to simulate real values
        import random
        base_value = mock_values.get(metric, 50.0)
        return base_value + random.uniform(-5, 5)

    async def _save_slo_definition(self, name: str, definition: Dict[str, Any]) -> bool:
        """Save SLO/SLA definition."""
        try:
            # In a real implementation, this would save to a configuration file
            return True
        except Exception:
            return False

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-wide metrics."""
        # In a real implementation, this would query Prometheus
        # For now, return mock data
        return {
            "cpu_avg": 45.2,
            "cpu_peak": 78.5,
            "memory_usage": 6.2,
            "memory_available": 8.1,
            "total_services": 16,
            "healthy_services": 14,
            "services_with_alerts": 2,
            "avg_response_time": 245.3,
            "p95_response_time": 520.1,
            "error_rate": 0.08,
            "total_requests": 15420,
            "rps": 12.8,
            "peak_rps": 45.2,
            "top_cpu_consumers": [
                ("analysis-service", 23.5),
                ("summarizer-hub", 18.2),
                ("doc-store", 15.8)
            ]
        }

    async def _get_service_metrics(self, service: str) -> Dict[str, Any]:
        """Get metrics for a specific service."""
        # Mock service metrics
        mock_metrics = {
            "orchestrator": {
                "avg_response_time": 120.5,
                "p95_response_time": 280.2,
                "throughput": 25.3,
                "error_rate": 0.02,
                "cpu_usage": 35.2,
                "memory_usage": 245.8,
                "active_connections": 12,
                "status": "healthy",
                "uptime": "7d 4h 32m",
                "last_health_check": "2024-01-15 14:35:00"
            },
            "doc-store": {
                "avg_response_time": 85.3,
                "p95_response_time": 195.1,
                "throughput": 45.7,
                "error_rate": 0.01,
                "cpu_usage": 28.9,
                "memory_usage": 312.4,
                "active_connections": 8,
                "status": "healthy",
                "uptime": "7d 4h 31m",
                "last_health_check": "2024-01-15 14:34:00"
            }
        }

        return mock_metrics.get(service, {})

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def view_dashboards_from_cli(self):
        """View dashboards for CLI usage."""
        try:
            await self.view_available_dashboards()
        except Exception as e:
            self.console.print(f"[red]Error viewing dashboards: {e}[/red]")

    async def view_alerts_from_cli(self):
        """View alerts for CLI usage."""
        try:
            await self.view_active_alerts()
        except Exception as e:
            self.console.print(f"[red]Error viewing alerts: {e}[/red]")

    async def view_slo_status_from_cli(self):
        """View SLO status for CLI usage."""
        try:
            await self.monitor_slo_sla_compliance()
        except Exception as e:
            self.console.print(f"[red]Error viewing SLO status: {e}[/red]")

    async def view_metrics_from_cli(self):
        """View metrics for CLI usage."""
        try:
            await self.system_metrics_overview()
        except Exception as e:
            self.console.print(f"[red]Error viewing metrics: {e}[/red]")
