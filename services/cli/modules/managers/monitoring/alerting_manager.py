"""Alerting Manager for CLI monitoring operations."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import yaml
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from ...base.base_manager import BaseManager
from ...formatters.display_utils import DisplayManager


class AlertingManager(BaseManager):
    """Manager for alerting operations."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)
        self.alert_rules = {}

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return alerting management menu."""
        return [
            ("1", "View Active Alerts"),
            ("2", "Create Alert Rule"),
            ("3", "Edit Alert Rule"),
            ("4", "Delete Alert Rule"),
            ("5", "Alert History"),
            ("6", "Alert Notifications"),
            ("b", "Back to Advanced Monitoring")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle menu choice."""
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
        else:
            return False

        if choice in ["1", "5"]:  # Choices that show results
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        return True

    async def view_active_alerts(self):
        """View active monitoring alerts."""
        try:
            alerts = await self._get_active_alerts()

            if alerts:
                table = Table(title="Active Monitoring Alerts")
                table.add_column("Alert", style="cyan")
                table.add_column("Severity", style="red")
                table.add_column("Status", style="yellow")
                table.add_column("Description", style="white")
                table.add_column("Triggered", style="green")

                for alert in alerts:
                    severity_color = {
                        "critical": "red",
                        "warning": "yellow",
                        "info": "blue"
                    }.get(alert.get("severity", "info"), "white")

                    status_display = {
                        "firing": "[red]FIRING[/red]",
                        "resolved": "[green]RESOLVED[/green]",
                        "pending": "[yellow]PENDING[/yellow]"
                    }.get(alert.get("status", "unknown"), "[dim]UNKNOWN[/dim]")

                    table.add_row(
                        alert.get("name", "Unknown"),
                        f"[{severity_color}]{alert.get('severity', 'info').upper()}[/{severity_color}]",
                        status_display,
                        alert.get("description", "No description"),
                        alert.get("triggered_at", "Unknown")
                    )

                self.console.print(table)

                # Show alert summary
                firing = sum(1 for a in alerts if a.get("status") == "firing")
                resolved = sum(1 for a in alerts if a.get("status") == "resolved")

                self.display.show_info(f"Active alerts: {firing} firing, {resolved} resolved")

            else:
                self.display.show_success("No active alerts found")

        except Exception as e:
            self.display.show_error(f"Error viewing active alerts: {e}")

    async def create_alert_rule(self):
        """Create a new alert rule."""
        try:
            rule_name = await self.get_user_input("Alert rule name")

            if not rule_name.strip():
                self.display.show_warning("Alert rule name cannot be empty")
                return

            rule_type = await self.select_from_list(
                ["threshold", "rate", "absence", "custom"],
                "Alert rule type"
            )
            if not rule_type:
                return

            severity = await self.select_from_list(
                ["critical", "warning", "info"],
                "Alert severity"
            )
            if not severity:
                severity = "warning"

            description = await self.get_user_input("Alert description")

            # Create rule based on type
            rule_config = {
                "name": rule_name,
                "type": rule_type,
                "severity": severity,
                "description": description,
                "enabled": True,
                "created_at": self._get_timestamp()
            }

            # Add type-specific configuration
            if rule_type == "threshold":
                metric = await self.get_user_input("Metric name (e.g., cpu_usage)")
                threshold = await self.get_user_input("Threshold value")
                operator = await self.select_from_list([">", "<", ">=", "<=", "=="], "Operator")

                if metric and threshold and operator:
                    rule_config.update({
                        "metric": metric,
                        "threshold": float(threshold),
                        "operator": operator,
                        "duration": "5m"  # Default 5 minutes
                    })
            elif rule_type == "rate":
                metric = await self.get_user_input("Metric name")
                rate = await self.get_user_input("Rate threshold (e.g., 10 per minute)")

                if metric and rate:
                    rule_config.update({
                        "metric": metric,
                        "rate_threshold": float(rate),
                        "time_window": "5m"
                    })

            # Save alert rule
            success = await self._save_alert_rule(rule_name, rule_config)

            if success:
                self.alert_rules[rule_name] = rule_config
                self.display.show_success(f"Alert rule '{rule_name}' created successfully")
                self.display.show_info("Rule will be active immediately")
            else:
                self.display.show_error("Failed to create alert rule")

        except Exception as e:
            self.display.show_error(f"Error creating alert rule: {e}")

    async def edit_alert_rule(self):
        """Edit an existing alert rule."""
        try:
            rules = await self._load_alert_rules()

            if not rules:
                self.display.show_warning("No alert rules available to edit")
                return

            rule_names = list(rules.keys())
            selected_rule = await self.select_from_list(rule_names, "Select alert rule to edit")

            if not selected_rule:
                return

            rule_config = rules[selected_rule]
            self.display.show_info(f"Editing alert rule: {selected_rule}")

            # Allow editing basic properties
            new_description = await self.get_user_input(
                "New description",
                default=rule_config.get("description", "")
            )

            new_severity = await self.select_from_list(
                ["critical", "warning", "info"],
                "New severity"
            )

            if new_description != rule_config.get("description", ""):
                rule_config["description"] = new_description
                rule_config["updated_at"] = self._get_timestamp()

            if new_severity and new_severity != rule_config.get("severity"):
                rule_config["severity"] = new_severity
                rule_config["updated_at"] = self._get_timestamp()

            success = await self._save_alert_rule(selected_rule, rule_config)

            if success:
                self.alert_rules[selected_rule] = rule_config
                self.display.show_success("Alert rule updated successfully")
            else:
                self.display.show_error("Failed to update alert rule")

        except Exception as e:
            self.display.show_error(f"Error editing alert rule: {e}")

    async def delete_alert_rule(self):
        """Delete an alert rule."""
        try:
            rules = await self._load_alert_rules()

            if not rules:
                self.display.show_warning("No alert rules available to delete")
                return

            rule_names = list(rules.keys())
            selected_rule = await self.select_from_list(rule_names, "Select alert rule to delete")

            if not selected_rule:
                return

            confirm = await self.confirm_action(f"Are you sure you want to delete alert rule '{selected_rule}'?")

            if confirm:
                success = await self._delete_alert_rule(selected_rule)

                if success:
                    if selected_rule in self.alert_rules:
                        del self.alert_rules[selected_rule]
                    self.display.show_success(f"Alert rule '{selected_rule}' deleted successfully")
                else:
                    self.display.show_error("Failed to delete alert rule")

        except Exception as e:
            self.display.show_error(f"Error deleting alert rule: {e}")

    async def alert_history(self):
        """Show alert history."""
        try:
            # Generate mock alert history
            history = [
                {
                    "alert": "High CPU Usage",
                    "severity": "warning",
                    "status": "resolved",
                    "triggered_at": "2024-01-15 10:30:00",
                    "resolved_at": "2024-01-15 10:45:00",
                    "duration": "15m"
                },
                {
                    "alert": "Memory Usage Spike",
                    "severity": "critical",
                    "status": "resolved",
                    "triggered_at": "2024-01-15 09:15:00",
                    "resolved_at": "2024-01-15 09:30:00",
                    "duration": "15m"
                },
                {
                    "alert": "Disk Space Low",
                    "severity": "warning",
                    "status": "firing",
                    "triggered_at": "2024-01-15 08:00:00",
                    "resolved_at": None,
                    "duration": "2h 30m"
                }
            ]

            table = Table(title="Alert History")
            table.add_column("Alert", style="cyan")
            table.add_column("Severity", style="red")
            table.add_column("Status", style="yellow")
            table.add_column("Triggered", style="white")
            table.add_column("Duration", style="green")

            for alert in history:
                severity_color = {
                    "critical": "red",
                    "warning": "yellow",
                    "info": "blue"
                }.get(alert.get("severity", "info"), "white")

                status_display = {
                    "firing": "[red]FIRING[/red]",
                    "resolved": "[green]RESOLVED[/green]",
                    "pending": "[yellow]PENDING[/yellow]"
                }.get(alert.get("status", "unknown"), "[dim]UNKNOWN[/dim]")

                table.add_row(
                    alert["alert"],
                    f"[{severity_color}]{alert['severity'].upper()}[/{severity_color}]",
                    status_display,
                    alert["triggered_at"],
                    alert["duration"]
                )

            self.console.print(table)

        except Exception as e:
            self.display.show_error(f"Error retrieving alert history: {e}")

    async def alert_notifications(self):
        """Configure alert notifications."""
        try:
            self.display.show_info("Alert notification configuration")
            self.display.show_info("Available channels: email, slack, webhook, pager")

            # In a real implementation, this would configure notification settings
            # For now, show current mock configuration

            notifications_config = {
                "email": {
                    "enabled": True,
                    "recipients": ["admin@example.com", "ops@example.com"],
                    "critical_only": True
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "https://hooks.slack.com/...",
                    "channel": "#alerts"
                },
                "webhook": {
                    "enabled": True,
                    "url": "https://api.example.com/webhooks/alerts",
                    "headers": {"Authorization": "Bearer ***"}
                }
            }

            table = Table(title="Alert Notification Configuration")
            table.add_column("Channel", style="cyan")
            table.add_column("Enabled", style="green")
            table.add_column("Configuration", style="white")

            for channel, config in notifications_config.items():
                enabled = "[green]YES[/green]" if config.get("enabled") else "[red]NO[/red]"
                details = []

                if channel == "email":
                    details.append(f"Recipients: {len(config.get('recipients', []))}")
                    if config.get("critical_only"):
                        details.append("Critical alerts only")
                elif channel == "slack":
                    if config.get("channel"):
                        details.append(f"Channel: {config['channel']}")
                elif channel == "webhook":
                    if config.get("url"):
                        details.append("Configured")

                table.add_row(channel, enabled, ", ".join(details) if details else "Not configured")

            self.console.print(table)

        except Exception as e:
            self.display.show_error(f"Error configuring alert notifications: {e}")

    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts from monitoring system."""
        # In a real implementation, this would query Prometheus Alertmanager or similar
        # For now, return mock alerts
        return [
            {
                "name": "High CPU Usage",
                "severity": "warning",
                "status": "firing",
                "description": "CPU usage above 80% for 5 minutes",
                "triggered_at": "2024-01-15 14:30:00"
            },
            {
                "name": "Memory Usage High",
                "severity": "critical",
                "status": "firing",
                "description": "Memory usage above 90%",
                "triggered_at": "2024-01-15 14:25:00"
            },
            {
                "name": "Disk Space Low",
                "severity": "warning",
                "status": "resolved",
                "description": "Disk space below 10%",
                "triggered_at": "2024-01-15 12:00:00"
            }
        ]

    async def _save_alert_rule(self, name: str, rule: Dict[str, Any]) -> bool:
        """Save alert rule configuration."""
        # In a real implementation, this would save to a database or config file
        try:
            self.alert_rules[name] = rule
            return True
        except Exception:
            return False

    async def _load_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load alert rules configuration."""
        # In a real implementation, this would load from a database or config file
        return self.alert_rules.copy()

    async def _delete_alert_rule(self, name: str) -> bool:
        """Delete an alert rule."""
        try:
            if name in self.alert_rules:
                del self.alert_rules[name]
            return True
        except Exception:
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
