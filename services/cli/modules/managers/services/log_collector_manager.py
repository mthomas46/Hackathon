"""Log Collector Manager module for CLI service.

Provides power-user operations for log collector including
log aggregation, streaming, pattern analysis, and stats.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
import json
import os
import asyncio
from datetime import datetime

from ...shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class LogCollectorManager:
    """Manager for log collector power-user operations."""

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients

    async def log_collector_menu(self):
        """Main log collector menu."""
        while True:
            menu = create_menu_table("Log Collector Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Log Submission (Store individual and batch logs)"),
                ("2", "Log Querying (Search, filter, and retrieve logs)"),
                ("3", "Log Statistics & Analytics"),
                ("4", "Log Monitoring & Alerting"),
                ("5", "Log Export & Archiving"),
                ("6", "Log Pattern Analysis"),
                ("7", "Log Collector Health & Configuration"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.log_submission_menu()
            elif choice == "2":
                await self.log_querying_menu()
            elif choice == "3":
                await self.log_statistics_menu()
            elif choice == "4":
                await self.log_monitoring_menu()
            elif choice == "5":
                await self.log_export_menu()
            elif choice == "6":
                await self.log_pattern_analysis_menu()
            elif choice == "7":
                await self.log_collector_health_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def log_submission_menu(self):
        """Log submission submenu."""
        while True:
            menu = create_menu_table("Log Submission", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Submit Individual Log Entry"),
                ("2", "Submit Batch Log Entries"),
                ("3", "Import Logs from File"),
                ("4", "Generate Test Logs"),
                ("5", "Log Submission Templates"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.submit_individual_log()
            elif choice == "2":
                await self.submit_batch_logs()
            elif choice == "3":
                await self.import_logs_from_file()
            elif choice == "4":
                await self.generate_test_logs()
            elif choice == "5":
                await self.log_submission_templates()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def submit_individual_log(self):
        """Submit a single log entry."""
        try:
            service = Prompt.ask("[bold cyan]Service name[/bold cyan]")
            level = Prompt.ask("[bold cyan]Log level[/bold cyan]", default="info")
            message = Prompt.ask("[bold cyan]Log message[/bold cyan]")

            if not service or not message:
                self.console.print("[red]Service name and message are required[/red]")
                return

            # Optional context
            add_context = Confirm.ask("[bold cyan]Add context data?[/bold cyan]", default=False)
            context = None
            if add_context:
                context_input = Prompt.ask("[bold cyan]Context (JSON)[/bold cyan]", default="{}")
                try:
                    context = json.loads(context_input)
                except json.JSONDecodeError:
                    self.console.print("[yellow]Invalid JSON, using empty context[/yellow]")

            log_entry = {
                "service": service,
                "level": level,
                "message": message,
                "context": context
            }

            with self.console.status("[bold green]Submitting log entry...[/bold green]") as status:
                response = await self.clients.post_json("log-collector/logs", log_entry)

            if response:
                self.console.print("[green]✅ Log entry submitted successfully[/green]")
                if response.get("count"):
                    self.console.print(f"[green]Total logs stored: {response['count']}[/green]")
            else:
                self.console.print("[red]❌ Failed to submit log entry[/red]")

        except Exception as e:
            self.console.print(f"[red]Error submitting log: {e}[/red]")

    async def submit_batch_logs(self):
        """Submit multiple log entries in batch."""
        try:
            batch_size = int(Prompt.ask("[bold cyan]Number of log entries to create[/bold cyan]", default="5"))

            batch_entries = []
            for i in range(batch_size):
                service = Prompt.ask(f"[bold cyan]Service name for entry {i+1}[/bold cyan]", default=f"test-service-{i+1}")
                level = Prompt.ask(f"[bold cyan]Log level for entry {i+1}[/bold cyan]", default="info")
                message = Prompt.ask(f"[bold cyan]Message for entry {i+1}[/bold cyan]", default=f"Test log message {i+1}")

                batch_entries.append({
                    "service": service,
                    "level": level,
                    "message": message
                })

            self.console.print(f"[yellow]Created {len(batch_entries)} log entries for batch submission[/yellow]")

            confirm = Confirm.ask("[bold cyan]Submit batch?[/bold cyan]", default=True)

            if confirm:
                batch_request = {"items": batch_entries}

                with self.console.status("[bold green]Submitting batch logs...[/bold green]") as status:
                    response = await self.clients.post_json("log-collector/logs/batch", batch_request)

                if response:
                    self.console.print("[green]✅ Batch logs submitted successfully[/green]")
                    if response.get("count") and response.get("added"):
                        self.console.print(f"[green]Added {response['added']} logs, total stored: {response['count']}[/green]")
                else:
                    self.console.print("[red]❌ Failed to submit batch logs[/red]")

        except Exception as e:
            self.console.print(f"[red]Error submitting batch logs: {e}[/red]")

    async def import_logs_from_file(self):
        """Import logs from a JSON file."""
        try:
            file_path = Prompt.ask("[bold cyan]JSON file path containing log entries[/bold cyan]")

            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return

            with open(file_path, 'r') as f:
                log_data = json.load(f)

            # Handle both single log and array of logs
            if isinstance(log_data, dict):
                log_entries = [log_data]
            elif isinstance(log_data, list):
                log_entries = log_data
            else:
                self.console.print("[red]Invalid JSON format. Expected object or array[/red]")
                return

            self.console.print(f"[yellow]Found {len(log_entries)} log entries to import[/yellow]")

            confirm = Confirm.ask("[bold cyan]Import logs?[/bold cyan]", default=True)

            if confirm:
                batch_request = {"items": log_entries}

                with self.console.status("[bold green]Importing logs from file...[/bold green]") as status:
                    response = await self.clients.post_json("log-collector/logs/batch", batch_request)

                if response:
                    self.console.print("[green]✅ Logs imported successfully[/green]")
                    if response.get("count") and response.get("added"):
                        self.console.print(f"[green]Added {response['added']} logs, total stored: {response['count']}[/green]")
                else:
                    self.console.print("[red]❌ Failed to import logs[/red]")

        except Exception as e:
            self.console.print(f"[red]Error importing logs: {e}[/red]")

    async def generate_test_logs(self):
        """Generate test log entries for testing purposes."""
        try:
            count = int(Prompt.ask("[bold cyan]Number of test logs to generate[/bold cyan]", default="10"))
            service = Prompt.ask("[bold cyan]Service name for test logs[/bold cyan]", default="test-service")

            test_logs = []
            levels = ["debug", "info", "warning", "error"]

            for i in range(count):
                test_logs.append({
                    "service": service,
                    "level": levels[i % len(levels)],
                    "message": f"Test log message {i+1} - {datetime.now().isoformat()}",
                    "context": {
                        "test_id": i + 1,
                        "generated_by": "cli_test_generator"
                    }
                })

            batch_request = {"items": test_logs}

            with self.console.status(f"[bold green]Generating {count} test logs...[/bold green]") as status:
                response = await self.clients.post_json("log-collector/logs/batch", batch_request)

            if response:
                self.console.print("[green]✅ Test logs generated successfully[/green]")
                if response.get("count") and response.get("added"):
                    self.console.print(f"[green]Added {response['added']} test logs, total stored: {response['count']}[/green]")
            else:
                self.console.print("[red]❌ Failed to generate test logs[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating test logs: {e}[/red]")

    async def log_submission_templates(self):
        """Manage log submission templates."""
        try:
            self.console.print("[yellow]Log submission templates would provide reusable log formats[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with log templates: {e}[/red]")

    async def log_querying_menu(self):
        """Log querying submenu."""
        while True:
            menu = create_menu_table("Log Querying", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Query All Logs"),
                ("2", "Filter by Service"),
                ("3", "Filter by Log Level"),
                ("4", "Advanced Filtering"),
                ("5", "Search Log Messages"),
                ("6", "Real-time Log Streaming"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.query_all_logs()
            elif choice == "2":
                await self.filter_by_service()
            elif choice == "3":
                await self.filter_by_level()
            elif choice == "4":
                await self.advanced_filtering()
            elif choice == "5":
                await self.search_log_messages()
            elif choice == "6":
                await self.real_time_log_streaming()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def query_all_logs(self):
        """Query all logs with optional limit."""
        try:
            limit = int(Prompt.ask("[bold cyan]Maximum logs to retrieve[/bold cyan]", default="50"))

            params = {"limit": limit}

            response = await self.clients.get_json("log-collector/logs", params=params)

            if response and "items" in response:
                logs = response["items"]
                await self.display_logs(logs, f"All Logs (showing {len(logs)} of {limit} requested)")
            else:
                self.console.print("[yellow]No logs found[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error querying logs: {e}[/red]")

    async def filter_by_service(self):
        """Filter logs by service name."""
        try:
            service = Prompt.ask("[bold cyan]Service name to filter by[/bold cyan]")
            limit = int(Prompt.ask("[bold cyan]Maximum logs to retrieve[/bold cyan]", default="50"))

            params = {"service": service, "limit": limit}

            response = await self.clients.get_json("log-collector/logs", params=params)

            if response and "items" in response:
                logs = response["items"]
                await self.display_logs(logs, f"Logs for service '{service}' ({len(logs)} found)")
            else:
                self.console.print(f"[yellow]No logs found for service '{service}'[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error filtering by service: {e}[/red]")

    async def filter_by_level(self):
        """Filter logs by log level."""
        try:
            level = Prompt.ask("[bold cyan]Log level to filter by[/bold cyan]")
            limit = int(Prompt.ask("[bold cyan]Maximum logs to retrieve[/bold cyan]", default="50"))

            params = {"level": level, "limit": limit}

            response = await self.clients.get_json("log-collector/logs", params=params)

            if response and "items" in response:
                logs = response["items"]
                await self.display_logs(logs, f"Logs with level '{level}' ({len(logs)} found)")
            else:
                self.console.print(f"[yellow]No logs found with level '{level}'[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error filtering by level: {e}[/red]")

    async def advanced_filtering(self):
        """Advanced log filtering with multiple criteria."""
        try:
            service = Prompt.ask("[bold cyan]Service filter (optional)[/bold cyan]", default="")
            level = Prompt.ask("[bold cyan]Level filter (optional)[/bold cyan]", default="")
            limit = int(Prompt.ask("[bold cyan]Maximum logs to retrieve[/bold cyan]", default="50"))

            params = {"limit": limit}
            if service:
                params["service"] = service
            if level:
                params["level"] = level

            filter_desc = []
            if service:
                filter_desc.append(f"service='{service}'")
            if level:
                filter_desc.append(f"level='{level}'")
            filter_str = " and ".join(filter_desc) if filter_desc else "no filters"

            response = await self.clients.get_json("log-collector/logs", params=params)

            if response and "items" in response:
                logs = response["items"]
                await self.display_logs(logs, f"Advanced filtered logs ({filter_str}) - {len(logs)} found")
            else:
                self.console.print(f"[yellow]No logs found with filters: {filter_str}[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error in advanced filtering: {e}[/red]")

    async def search_log_messages(self):
        """Search log messages for specific text."""
        try:
            search_term = Prompt.ask("[bold cyan]Text to search for in log messages[/bold cyan]")
            limit = int(Prompt.ask("[bold cyan]Maximum logs to retrieve[/bold cyan]", default="50"))

            # Get all logs and filter client-side
            params = {"limit": min(limit * 2, 1000)}  # Get more to filter
            response = await self.clients.get_json("log-collector/logs", params=params)

            if response and "items" in response:
                all_logs = response["items"]
                matching_logs = []

                for log in all_logs:
                    if search_term.lower() in log.get("message", "").lower():
                        matching_logs.append(log)
                        if len(matching_logs) >= limit:
                            break

                await self.display_logs(matching_logs, f"Logs containing '{search_term}' ({len(matching_logs)} found)")
            else:
                self.console.print(f"[yellow]No logs found containing '{search_term}'[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error searching log messages: {e}[/red]")

    async def real_time_log_streaming(self):
        """Real-time log streaming (placeholder for future implementation)."""
        try:
            self.console.print("[yellow]Real-time log streaming would show live log entries[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with real-time streaming: {e}[/red]")

    async def display_logs(self, logs: List[Dict[str, Any]], title: str):
        """Display logs in a formatted table."""
        if not logs:
            self.console.print(f"[yellow]{title}: No logs found[/yellow]")
            return

        table = Table(title=title)
        table.add_column("Service", style="cyan")
        table.add_column("Level", style="green")
        table.add_column("Message", style="white")
        table.add_column("Timestamp", style="blue")

        for log in logs[:50]:  # Limit display to 50 logs
            level = log.get("level", "unknown")
            level_color = {
                "debug": "dim",
                "info": "green",
                "warning": "yellow",
                "error": "red",
                "fatal": "red bold"
            }.get(level, "white")

            message = log.get("message", "")
            if len(message) > 60:
                message = message[:57] + "..."

            timestamp = log.get("timestamp", "")
            if timestamp and len(timestamp) > 19:
                timestamp = timestamp[:19]  # Truncate to fit

            table.add_row(
                log.get("service", "unknown"),
                f"[{level_color}]{level.upper()}[/{level_color}]",
                message,
                timestamp
            )

        self.console.print(table)

        if len(logs) > 50:
            self.console.print(f"[yellow]... and {len(logs) - 50} more logs[/yellow]")

    async def log_statistics_menu(self):
        """Log statistics and analytics submenu."""
        while True:
            menu = create_menu_table("Log Statistics & Analytics", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Overall Statistics"),
                ("2", "Service-wise Statistics"),
                ("3", "Level Distribution Analysis"),
                ("4", "Error Rate Analysis"),
                ("5", "Time-based Analytics"),
                ("6", "Log Volume Trends"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_overall_statistics()
            elif choice == "2":
                await self.service_wise_statistics()
            elif choice == "3":
                await self.level_distribution_analysis()
            elif choice == "4":
                await self.error_rate_analysis()
            elif choice == "5":
                await self.time_based_analytics()
            elif choice == "6":
                await self.log_volume_trends()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_overall_statistics(self):
        """View comprehensive log statistics."""
        try:
            response = await self.clients.get_json("log-collector/stats")

            if response:
                await self.display_log_statistics(response, "Overall Log Statistics")
            else:
                self.console.print("[red]Failed to retrieve log statistics[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing statistics: {e}[/red]")

    async def display_log_statistics(self, stats: Dict[str, Any], title: str):
        """Display log statistics in a formatted way."""
        content = f"""
[bold]📊 {title}[/bold]

[bold blue]Total Logs:[/bold blue] {stats.get('total_logs', 0)}
[bold blue]Time Range:[/bold blue] {stats.get('time_range', 'N/A')}
"""

        # Level distribution
        level_distribution = stats.get("level_distribution", {})
        if level_distribution:
            content += "\n[bold green]Log Levels:[/bold green]\n"
            for level, count in sorted(level_distribution.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / stats.get('total_logs', 1)) * 100
                level_color = {
                    "debug": "dim",
                    "info": "green",
                    "warning": "yellow",
                    "error": "red",
                    "fatal": "red bold"
                }.get(level, "white")
                content += f"• [{level_color}]{level}[/{level_color}]: {count} ({percentage:.1f}%)\n"

        # Service distribution (top 5)
        service_distribution = stats.get("service_distribution", {})
        if service_distribution:
            content += "\n[bold cyan]Top Services:[/bold cyan]\n"
            top_services = sorted(service_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
            for service, count in top_services:
                percentage = (count / stats.get('total_logs', 1)) * 100
                content += f"• {service}: {count} ({percentage:.1f}%)\n"

        # Error metrics
        error_rate = stats.get("error_rate", 0)
        if error_rate > 0:
            content += f"\n[bold red]Error Rate:[/bold red] {error_rate:.2f}%\n"

        # Recent activity
        recent_activity = stats.get("recent_activity", {})
        if recent_activity:
            content += "\n[bold yellow]Recent Activity:[/bold yellow]\n"
            content += f"• Last hour: {recent_activity.get('last_hour', 0)} logs\n"
            content += f"• Last 24h: {recent_activity.get('last_24h', 0)} logs\n"

        print_panel(self.console, content, border_style="blue")

        # Show additional metrics if available
        if stats.get("performance_metrics"):
            perf_table = Table(title="Performance Metrics")
            perf_table.add_column("Metric", style="cyan")
            perf_table.add_column("Value", style="green")

            perf_metrics = stats["performance_metrics"]
            for metric, value in perf_metrics.items():
                perf_table.add_row(metric, str(value))

            self.console.print(perf_table)

    async def service_wise_statistics(self):
        """Show statistics broken down by service."""
        try:
            response = await self.clients.get_json("log-collector/stats")

            if response:
                service_stats = response.get("service_distribution", {})
                if service_stats:
                    table = Table(title="Service-wise Log Statistics")
                    table.add_column("Service", style="cyan")
                    table.add_column("Log Count", style="green", justify="right")
                    table.add_column("Percentage", style="yellow", justify="right")

                    total_logs = response.get("total_logs", 1)
                    for service, count in sorted(service_stats.items(), key=lambda x: x[1], reverse=True):
                        percentage = (count / total_logs) * 100
                        table.add_row(service, str(count), f"{percentage:.1f}%")

                    self.console.print(table)
                else:
                    self.console.print("[yellow]No service statistics available[/yellow]")
            else:
                self.console.print("[red]Failed to retrieve service statistics[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing service statistics: {e}[/red]")

    async def level_distribution_analysis(self):
        """Analyze log level distribution."""
        try:
            response = await self.clients.get_json("log-collector/stats")

            if response:
                level_stats = response.get("level_distribution", {})
                if level_stats:
                    # Create a visual representation
                    total = sum(level_stats.values())

                    content = f"""
[bold]🔍 Log Level Distribution Analysis[/bold]

[bold blue]Total Logs Analyzed:[/bold blue] {total}
"""

                    for level, count in sorted(level_stats.items(), key=lambda x: x[1], reverse=True):
                        percentage = (count / total) * 100
                        bar_length = int((count / total) * 40)  # 40 chars max bar
                        bar = "█" * bar_length

                        level_color = {
                            "debug": "dim",
                            "info": "green",
                            "warning": "yellow",
                            "error": "red",
                            "fatal": "red bold"
                        }.get(level, "white")

                        content += f"[{level_color}]{level.upper():<8}[/{level_color}] {bar} {count:>4} ({percentage:>5.1f}%)\n"

                    print_panel(self.console, content, border_style="green")
                else:
                    self.console.print("[yellow]No level distribution data available[/yellow]")
            else:
                self.console.print("[red]Failed to retrieve level analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing level distribution: {e}[/red]")

    async def error_rate_analysis(self):
        """Analyze error rates and patterns."""
        try:
            response = await self.clients.get_json("log-collector/stats")

            if response:
                error_rate = response.get("error_rate", 0)
                error_trends = response.get("error_trends", {})

                content = f"""
[bold]🚨 Error Rate Analysis[/bold]

[bold blue]Current Error Rate:[/bold blue] {error_rate:.2f}%

[bold red]Error Assessment:[/bold red] {'High' if error_rate > 10 else 'Moderate' if error_rate > 5 else 'Low'}
"""

                if error_trends:
                    content += "\n[bold yellow]Error Trends:[/bold yellow]\n"
                    for period, rate in error_trends.items():
                        content += f"• {period}: {rate:.2f}%\n"

                # Show error pattern analysis if available
                error_patterns = response.get("error_patterns", {})
                if error_patterns:
                    content += "\n[bold magenta]Common Error Patterns:[/bold magenta]\n"
                    for pattern, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
                        content += f"• {pattern}: {count} occurrences\n"

                print_panel(self.console, content, border_style="red" if error_rate > 5 else "yellow")
            else:
                self.console.print("[red]Failed to retrieve error analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing error rates: {e}[/red]")

    async def time_based_analytics(self):
        """Show time-based log analytics."""
        try:
            self.console.print("[yellow]Time-based analytics would show log patterns over time[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in time-based analytics: {e}[/red]")

    async def log_volume_trends(self):
        """Show log volume trends."""
        try:
            self.console.print("[yellow]Log volume trends would show log ingestion patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error showing volume trends: {e}[/red]")

    async def log_monitoring_menu(self):
        """Log monitoring and alerting submenu."""
        while True:
            menu = create_menu_table("Log Monitoring & Alerting", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Set up Log Alerts"),
                ("2", "Monitor Error Rates"),
                ("3", "Service Health Monitoring"),
                ("4", "Anomaly Detection"),
                ("5", "Alert History"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.setup_log_alerts()
            elif choice == "2":
                await self.monitor_error_rates()
            elif choice == "3":
                await self.service_health_monitoring()
            elif choice == "4":
                await self.anomaly_detection()
            elif choice == "5":
                await self.alert_history()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def setup_log_alerts(self):
        """Set up log-based alerts."""
        try:
            self.console.print("[yellow]Log alert setup would configure notifications for log patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error setting up alerts: {e}[/red]")

    async def monitor_error_rates(self):
        """Monitor error rates in real-time."""
        try:
            self.console.print("[yellow]Error rate monitoring would track error percentages[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring rates: {e}[/red]")

    async def service_health_monitoring(self):
        """Monitor service health through logs."""
        try:
            self.console.print("[yellow]Service health monitoring would analyze logs for health indicators[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in health monitoring: {e}[/red]")

    async def anomaly_detection(self):
        """Detect anomalous log patterns."""
        try:
            self.console.print("[yellow]Anomaly detection would identify unusual log patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in anomaly detection: {e}[/red]")

    async def alert_history(self):
        """View alert history."""
        try:
            self.console.print("[yellow]Alert history would show past alert notifications[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing alert history: {e}[/red]")

    async def log_export_menu(self):
        """Log export and archiving submenu."""
        while True:
            menu = create_menu_table("Log Export & Archiving", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Export Logs to JSON"),
                ("2", "Export Logs to CSV"),
                ("3", "Filtered Log Export"),
                ("4", "Log Archiving"),
                ("5", "Bulk Log Operations"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.export_logs_json()
            elif choice == "2":
                await self.export_logs_csv()
            elif choice == "3":
                await self.filtered_log_export()
            elif choice == "4":
                await self.log_archiving()
            elif choice == "5":
                await self.bulk_log_operations()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def export_logs_json(self):
        """Export logs to JSON format."""
        try:
            file_path = Prompt.ask("[bold cyan]Export file path[/bold cyan]", default="logs_export.json")
            limit = int(Prompt.ask("[bold cyan]Maximum logs to export[/bold cyan]", default="1000"))

            params = {"limit": limit}
            response = await self.clients.get_json("log-collector/logs", params=params)

            if response and "items" in response:
                logs = response["items"]

                with open(file_path, 'w') as f:
                    json.dump(logs, f, indent=2, default=str)

                self.console.print(f"[green]✅ Exported {len(logs)} logs to {file_path}[/green]")
            else:
                self.console.print("[red]❌ Failed to retrieve logs for export[/red]")

        except Exception as e:
            self.console.print(f"[red]Error exporting logs: {e}[/red]")

    async def export_logs_csv(self):
        """Export logs to CSV format."""
        try:
            file_path = Prompt.ask("[bold cyan]Export file path[/bold cyan]", default="logs_export.csv")
            limit = int(Prompt.ask("[bold cyan]Maximum logs to export[/bold cyan]", default="1000"))

            params = {"limit": limit}
            response = await self.clients.get_json("log-collector/logs", params=params)

            if response and "items" in response:
                logs = response["items"]

                if logs:
                    import csv
                    fieldnames = ["service", "level", "message", "timestamp"]
                    # Add context fields if they exist
                    if any(log.get("context") for log in logs):
                        fieldnames.append("context")

                    with open(file_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()

                        for log in logs:
                            row = {k: v for k, v in log.items() if k in fieldnames}
                            if "context" in row and isinstance(row["context"], dict):
                                row["context"] = json.dumps(row["context"])
                            writer.writerow(row)

                    self.console.print(f"[green]✅ Exported {len(logs)} logs to {file_path}[/green]")
                else:
                    self.console.print("[yellow]No logs to export[/yellow]")
            else:
                self.console.print("[red]❌ Failed to retrieve logs for export[/red]")

        except Exception as e:
            self.console.print(f"[red]Error exporting logs to CSV: {e}[/red]")

    async def filtered_log_export(self):
        """Export filtered logs."""
        try:
            self.console.print("[yellow]Filtered log export would allow exporting with specific criteria[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in filtered export: {e}[/red]")

    async def log_archiving(self):
        """Archive old logs."""
        try:
            self.console.print("[yellow]Log archiving would move old logs to long-term storage[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in log archiving: {e}[/red]")

    async def bulk_log_operations(self):
        """Perform bulk log operations."""
        try:
            self.console.print("[yellow]Bulk log operations would handle large-scale log processing[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in bulk operations: {e}[/red]")

    async def log_pattern_analysis_menu(self):
        """Log pattern analysis submenu."""
        while True:
            menu = create_menu_table("Log Pattern Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Identify Common Patterns"),
                ("2", "Error Pattern Analysis"),
                ("3", "Service Interaction Analysis"),
                ("4", "Performance Pattern Detection"),
                ("5", "Custom Pattern Matching"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.identify_common_patterns()
            elif choice == "2":
                await self.error_pattern_analysis()
            elif choice == "3":
                await self.service_interaction_analysis()
            elif choice == "4":
                await self.performance_pattern_detection()
            elif choice == "5":
                await self.custom_pattern_matching()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def identify_common_patterns(self):
        """Identify common log patterns."""
        try:
            self.console.print("[yellow]Common pattern identification would find recurring log structures[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error identifying patterns: {e}[/red]")

    async def error_pattern_analysis(self):
        """Analyze error patterns in logs."""
        try:
            self.console.print("[yellow]Error pattern analysis would categorize and analyze error logs[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in pattern analysis: {e}[/red]")

    async def service_interaction_analysis(self):
        """Analyze service interactions through logs."""
        try:
            self.console.print("[yellow]Service interaction analysis would map service communication patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in interaction analysis: {e}[/red]")

    async def performance_pattern_detection(self):
        """Detect performance patterns."""
        try:
            self.console.print("[yellow]Performance pattern detection would identify slow operations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in performance detection: {e}[/red]")

    async def custom_pattern_matching(self):
        """Custom pattern matching."""
        try:
            self.console.print("[yellow]Custom pattern matching would allow user-defined log pattern rules[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in custom matching: {e}[/red]")

    async def log_collector_health_menu(self):
        """Log collector health and configuration submenu."""
        while True:
            menu = create_menu_table("Log Collector Health & Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Service Health"),
                ("2", "Storage Capacity Monitoring"),
                ("3", "Performance Metrics"),
                ("4", "Configuration Settings"),
                ("5", "Service Logs"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_service_health()
            elif choice == "2":
                await self.storage_capacity_monitoring()
            elif choice == "3":
                await self.performance_metrics()
            elif choice == "4":
                await self.configuration_settings()
            elif choice == "5":
                await self.service_logs()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_service_health(self):
        """View log collector service health."""
        try:
            response = await self.clients.get_json("log-collector/health")

            if response:
                content = f"""
[bold]Log Collector Health Status[/bold]

[bold blue]Status:[/bold blue] {response.get('status', 'unknown')}
[bold blue]Service:[/bold blue] {response.get('service', 'unknown')}
[bold blue]Version:[/bold blue] {response.get('version', 'unknown')}
[bold blue]Total Logs:[/bold blue] {response.get('count', 0)}

[bold green]Description:[/bold green] {response.get('description', 'N/A')}
"""

                print_panel(self.console, content, border_style="green")
            else:
                self.console.print("[red]Failed to retrieve service health[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing service health: {e}[/red]")

    async def storage_capacity_monitoring(self):
        """Monitor log storage capacity."""
        try:
            response = await self.clients.get_json("log-collector/health")

            if response:
                total_logs = response.get('count', 0)
                capacity = 5000  # Default max logs
                usage_percent = (total_logs / capacity) * 100

                status = "🟢 Normal" if usage_percent < 70 else "🟡 Warning" if usage_percent < 90 else "🔴 Critical"

                content = f"""
[bold]Storage Capacity Monitoring[/bold]

[bold blue]Current Usage:[/bold blue] {total_logs}/{capacity} logs ({usage_percent:.1f}%)
[bold blue]Status:[/bold blue] {status}

[bold green]Capacity Assessment:[/bold green]
"""

                if usage_percent < 70:
                    content += "• Storage utilization is normal\n"
                    content += "• No immediate action required"
                elif usage_percent < 90:
                    content += "• Storage utilization is high\n"
                    content += "• Consider log rotation or cleanup"
                else:
                    content += "• Storage utilization is critical\n"
                    content += "• Immediate log cleanup required"

                print_panel(self.console, content, border_style="red" if usage_percent > 90 else "yellow" if usage_percent > 70 else "green")
            else:
                self.console.print("[red]Failed to retrieve storage information[/red]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring storage: {e}[/red]")

    async def performance_metrics(self):
        """View log collector performance metrics."""
        try:
            self.console.print("[yellow]Performance metrics would show ingestion rates and query performance[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing metrics: {e}[/red]")

    async def configuration_settings(self):
        """View configuration settings."""
        try:
            self.console.print("[yellow]Configuration settings would show current log collector parameters[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing configuration: {e}[/red]")

    async def service_logs(self):
        """View log collector service logs."""
        try:
            self.console.print("[yellow]Service logs would show log collector internal operations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing service logs: {e}[/red]")

    async def submit_log_from_cli(self, log_request: Dict[str, Any]):
        """Submit a single log entry for CLI usage."""
        try:
            with self.console.status(f"[bold green]Submitting log entry...[/bold green]") as status:
                response = await self.clients.post_json("log-collector/logs", log_request)

            if response:
                self.console.print("[green]✅ Log entry submitted successfully[/green]")
            else:
                self.console.print("[red]❌ Failed to submit log entry[/red]")

        except Exception as e:
            self.console.print(f"[red]Error submitting log: {e}[/red]")

    async def submit_batch_logs_from_cli(self, batch_request: Dict[str, Any]):
        """Submit batch log entries for CLI usage."""
        try:
            with self.console.status(f"[bold green]Submitting batch logs...[/bold green]") as status:
                response = await self.clients.post_json("log-collector/logs/batch", batch_request)

            if response:
                added = response.get("added", 0)
                total = response.get("count", 0)
                self.console.print(f"[green]✅ Batch submitted: {added} logs added, {total} total[/green]")
            else:
                self.console.print("[red]❌ Failed to submit batch logs[/red]")

        except Exception as e:
            self.console.print(f"[red]Error submitting batch logs: {e}[/red]")

    async def query_logs_from_cli(self, params: Dict[str, Any]):
        """Query logs for CLI usage."""
        try:
            response = await self.clients.get_json("log-collector/logs", params=params)

            if response and "items" in response:
                logs = response["items"]
                await self.display_logs(logs, f"Query Results ({len(logs)} logs)")
            else:
                self.console.print("[yellow]No logs found matching criteria[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error querying logs: {e}[/red]")

    async def get_log_stats_from_cli(self):
        """Get log statistics for CLI usage."""
        try:
            response = await self.clients.get_json("log-collector/stats")

            if response:
                await self.display_log_statistics(response, "Log Statistics")
            else:
                self.console.print("[red]Failed to retrieve log statistics[/red]")

        except Exception as e:
            self.console.print(f"[red]Error retrieving log statistics: {e}[/red]")
