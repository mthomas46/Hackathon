"""Notification Service Manager module for CLI service.

Provides power-user operations for notification service including
owner resolution, notification delivery, DLQ management, and resolutions.
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

from ...base.base_manager import BaseManager
from ...shared_utils import (
    
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class NotificationServiceManager(BaseManager):
    """Manager for notification service power-user operations."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return the main menu items for notification service operations."""
        return [
            ("1", "Notification Management"),
            ("2", "Template Configuration"),
            ("3", "Delivery Monitoring")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle a menu choice. Return True to continue, False to exit."""
        self.display.show_error("Feature not yet implemented")
        return True

    async def notification_service_menu(self):
        """Main notification service menu."""
        while True:
            menu = create_menu_table("Notification Service Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Owner Management (Update, resolve, and manage ownership)"),
                ("2", "Notification Delivery (Send notifications via various channels)"),
                ("3", "Dead Letter Queue (Manage failed notification delivery)"),
                ("4", "Notification Monitoring (Track delivery status and analytics)"),
                ("5", "Channel Configuration (Configure notification channels)"),
                ("6", "Notification Service Health & Configuration"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.owner_management_menu()
            elif choice == "2":
                await self.notification_delivery_menu()
            elif choice == "3":
                await self.dead_letter_queue_menu()
            elif choice == "4":
                await self.notification_monitoring_menu()
            elif choice == "5":
                await self.channel_configuration_menu()
            elif choice == "6":
                await self.notification_service_health_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def owner_management_menu(self):
        """Owner management submenu."""
        while True:
            menu = create_menu_table("Owner Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Update Owner Information"),
                ("2", "Resolve Owners to Targets"),
                ("3", "Bulk Owner Resolution"),
                ("4", "View Owner Registry"),
                ("5", "Owner Resolution Testing"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.update_owner_information()
            elif choice == "2":
                await self.resolve_owners_to_targets()
            elif choice == "3":
                await self.bulk_owner_resolution()
            elif choice == "4":
                await self.view_owner_registry()
            elif choice == "5":
                await self.owner_resolution_testing()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def update_owner_information(self):
        """Update owner information in the system."""
        try:
            entity_id = Prompt.ask("[bold cyan]Entity ID[/bold cyan]")
            owner_name = Prompt.ask("[bold cyan]Owner name (optional)[/bold cyan]", default="")
            team_name = Prompt.ask("[bold cyan]Team name (optional)[/bold cyan]", default="")

            update_request = {
                "id": entity_id,
                "owner": owner_name if owner_name else None,
                "team": team_name if team_name else None
            }

            response = await self.clients.post_json("notification-service/owners/update", update_request)

            if response:
                self.console.print("[green]✅ Owner information updated successfully[/green]")
                self.console.print(f"[green]Entity: {response.get('id', 'N/A')}[/green]")
                self.console.print(f"[green]Owner: {response.get('owner', 'N/A')}[/green]")
                self.console.print(f"[green]Team: {response.get('team', 'N/A')}[/green]")
            else:
                self.console.print("[red]❌ Failed to update owner information[/red]")

        except Exception as e:
            self.console.print(f"[red]Error updating owner information: {e}[/red]")

    async def resolve_owners_to_targets(self):
        """Resolve owners to their notification targets."""
        try:
            owners_input = Prompt.ask("[bold cyan]Owner names (comma-separated)[/bold cyan]")

            owners = [owner.strip() for owner in owners_input.split(",") if owner.strip()]

            if not owners:
                self.console.print("[red]No owners specified[/red]")
                return

            resolve_request = {"owners": owners}

            with self.console.status("[bold green]Resolving owners to notification targets...[/bold green]") as status:
                response = await self.clients.post_json("notification-service/owners/resolve", resolve_request)

            if response and "resolved" in response:
                await self.display_owner_resolutions(response["resolved"], owners)
            else:
                self.console.print("[red]❌ Failed to resolve owners[/red]")

        except Exception as e:
            self.console.print(f"[red]Error resolving owners: {e}[/red]")

    async def display_owner_resolutions(self, resolved_targets: Dict[str, Any], requested_owners: List[str]):
        """Display owner resolution results."""
        content = f"""
[bold]Owner Resolution Results[/bold]

[bold blue]Requested Owners:[/bold blue] {len(requested_owners)}
[bold blue]Resolved Targets:[/bold blue] {len(resolved_targets)}

[bold green]Resolution Details:[/bold green]
"""

        # Create table for resolution results
        table = Table(title="Owner to Target Resolution")
        table.add_column("Owner", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Targets Found", style="yellow", justify="right")
        table.add_column("Target Types", style="white")

        for owner in requested_owners:
            targets = resolved_targets.get(owner, [])
            if targets:
                target_types = list(set(target.get("channel", "unknown") for target in targets))
                status = "✅ Resolved"
                status_style = "green"
            else:
                target_types = ["None"]
                status = "❌ Not Found"
                status_style = "red"

            table.add_row(
                owner,
                f"[{status_style}]{status}[/{status_style}]",
                str(len(targets)),
                ", ".join(target_types)
            )

        self.console.print(table)

        # Show detailed target information
        for owner in requested_owners:
            targets = resolved_targets.get(owner, [])
            if targets:
                content += f"\n[bold cyan]{owner} targets:[/bold cyan]\n"
                for i, target in enumerate(targets, 1):
                    channel = target.get("channel", "unknown")
                    target_addr = target.get("target", "unknown")
                    content += f"  {i}. [{channel}] {target_addr}\n"

        print_panel(self.console, content, border_style="blue")

    async def bulk_owner_resolution(self):
        """Perform bulk owner resolution."""
        try:
            self.console.print("[yellow]Bulk owner resolution allows processing multiple owners from file[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in bulk owner resolution: {e}[/red]")

    async def view_owner_registry(self):
        """View the owner registry."""
        try:
            self.console.print("[yellow]Owner registry viewing would show current owner-to-entity mappings[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing owner registry: {e}[/red]")

    async def owner_resolution_testing(self):
        """Test owner resolution functionality."""
        try:
            self.console.print("[yellow]Owner resolution testing would validate resolution accuracy[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in resolution testing: {e}[/red]")

    async def notification_delivery_menu(self):
        """Notification delivery submenu."""
        while True:
            menu = create_menu_table("Notification Delivery", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Send Notification"),
                ("2", "Send Bulk Notifications"),
                ("3", "Test Channel Connectivity"),
                ("4", "Preview Notification"),
                ("5", "Notification Templates"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.send_notification()
            elif choice == "2":
                await self.send_bulk_notifications()
            elif choice == "3":
                await self.test_channel_connectivity()
            elif choice == "4":
                await self.preview_notification()
            elif choice == "5":
                await self.notification_templates()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def send_notification(self):
        """Send a notification through various channels."""
        try:
            # Get notification details
            channel = Prompt.ask("[bold cyan]Channel (webhook/email/slack)[/bold cyan]", default="webhook")
            target = Prompt.ask("[bold cyan]Target (URL/email/channel)[/bold cyan]")
            title = Prompt.ask("[bold cyan]Title[/bold cyan]")
            message = Prompt.ask("[bold cyan]Message[/bold cyan]")

            # Optional metadata and labels
            add_metadata = Confirm.ask("[bold cyan]Add metadata?[/bold cyan]", default=False)
            metadata = {}
            if add_metadata:
                metadata_input = Prompt.ask("[bold cyan]Metadata (JSON)[/bold cyan]", default="{}")
                try:
                    metadata = json.loads(metadata_input)
                except json.JSONDecodeError:
                    self.console.print("[yellow]Invalid JSON, using empty metadata[/yellow]")

            labels_input = Prompt.ask("[bold cyan]Labels (comma-separated, optional)[/bold cyan]", default="")
            labels = [label.strip() for label in labels_input.split(",") if label.strip()]

            notification_request = {
                "channel": channel,
                "target": target,
                "title": title,
                "message": message,
                "metadata": metadata,
                "labels": labels
            }

            with self.console.status(f"[bold green]Sending {channel} notification...[/bold green]") as status:
                response = await self.clients.post_json("notification-service/notify", notification_request)

            if response:
                await self.display_notification_result(response, channel, target)
            else:
                self.console.print("[red]❌ Failed to send notification[/red]")

        except Exception as e:
            self.console.print(f"[red]Error sending notification: {e}[/red]")

    async def display_notification_result(self, result: Dict[str, Any], channel: str, target: str):
        """Display notification delivery result."""
        status = result.get("status", "unknown")

        if status == "sent":
            status_icon = "✅"
            status_text = "DELIVERED SUCCESSFULLY"
            border_color = "green"
        elif status == "queued":
            status_icon = "⏳"
            status_text = "QUEUED FOR DELIVERY"
            border_color = "yellow"
        elif status == "duplicate":
            status_icon = "🔄"
            status_text = "DEDUPLICATED (recently sent)"
            border_color = "blue"
        else:
            status_icon = "❌"
            status_text = f"DELIVERY {status.upper()}"
            border_color = "red"

        content = f"""
[bold]Notification Delivery Result[/bold]

[bold blue]Channel:[/bold blue] {channel.upper()}
[bold blue]Target:[/bold blue] {target}
[bold blue]Status:[/bold blue] {status_icon} {status_text}

[bold green]Delivery Details:[/bold green]
"""

        if result.get("deduplication_key"):
            content += f"• Deduplication Key: {result['deduplication_key']}\n"

        if result.get("delivery_time"):
            content += f"• Delivery Time: {result['delivery_time']}\n"

        if result.get("error"):
            content += f"[bold red]• Error: {result['error']}[/bold red]\n"

        if result.get("retry_count"):
            content += f"• Retry Count: {result['retry_count']}\n"

        print_panel(self.console, content, border_style=border_color)

    async def send_bulk_notifications(self):
        """Send bulk notifications."""
        try:
            self.console.print("[yellow]Bulk notification sending would process multiple notifications from file[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in bulk notifications: {e}[/red]")

    async def test_channel_connectivity(self):
        """Test connectivity to notification channels."""
        try:
            channel = Prompt.ask("[bold cyan]Channel to test (webhook/email/slack)[/bold cyan]", default="webhook")
            target = Prompt.ask("[bold cyan]Test target[/bold cyan]")

            # Send a test notification
            test_request = {
                "channel": channel,
                "target": target,
                "title": "Connectivity Test",
                "message": "This is a test notification to verify channel connectivity.",
                "metadata": {"test": True},
                "labels": ["test", "connectivity"]
            }

            with self.console.status(f"[bold green]Testing {channel} connectivity...[/bold green]") as status:
                response = await self.clients.post_json("notification-service/notify", test_request)

            if response:
                status = response.get("status", "unknown")
                if status == "sent":
                    self.console.print(f"[green]✅ {channel.upper()} channel connectivity successful[/green]")
                else:
                    self.console.print(f"[yellow]⚠️  {channel.upper()} channel responded with status: {status}[/yellow]")
            else:
                self.console.print(f"[red]❌ {channel.upper()} channel connectivity failed[/red]")

        except Exception as e:
            self.console.print(f"[red]Error testing channel connectivity: {e}[/red]")

    async def preview_notification(self):
        """Preview notification before sending."""
        try:
            channel = Prompt.ask("[bold cyan]Channel[/bold cyan]", default="webhook")
            target = Prompt.ask("[bold cyan]Target[/bold cyan]")
            title = Prompt.ask("[bold cyan]Title[/bold cyan]")
            message = Prompt.ask("[bold cyan]Message[/bold cyan]")

            content = f"""
[bold]Notification Preview[/bold]

[bold blue]Channel:[/bold blue] {channel.upper()}
[bold blue]Target:[/bold blue] {target}

[bold green]Title:[/bold green] {title}

[bold cyan]Message:[/bold cyan]
{message}

[bold yellow]This is a preview. No notification will be sent.[/bold yellow]
"""

            print_panel(self.console, content, border_style="blue")

            send_now = Confirm.ask("[bold cyan]Send this notification now?[/bold cyan]", default=False)

            if send_now:
                await self.send_notification()

        except Exception as e:
            self.console.print(f"[red]Error previewing notification: {e}[/red]")

    async def notification_templates(self):
        """Manage notification templates."""
        try:
            self.console.print("[yellow]Notification templates would provide reusable message formats[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with notification templates: {e}[/red]")

    async def dead_letter_queue_menu(self):
        """Dead letter queue management submenu."""
        while True:
            menu = create_menu_table("Dead Letter Queue Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Failed Notifications"),
                ("2", "Retry Failed Notifications"),
                ("3", "Clear Dead Letter Queue"),
                ("4", "Analyze Failure Patterns"),
                ("5", "Export DLQ Data"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_failed_notifications()
            elif choice == "2":
                await self.retry_failed_notifications()
            elif choice == "3":
                await self.clear_dead_letter_queue()
            elif choice == "4":
                await self.analyze_failure_patterns()
            elif choice == "5":
                await self.export_dlq_data()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_failed_notifications(self):
        """View failed notifications from DLQ."""
        try:
            limit = int(Prompt.ask("[bold cyan]Number of entries to retrieve[/bold cyan]", default="20"))

            params = {"limit": limit}

            response = await self.clients.get_json("notification-service/dlq", params=params)

            if response and "items" in response:
                failed_items = response["items"]
                await self.display_dlq_entries(failed_items, limit)
            else:
                self.console.print("[green]No failed notifications in dead letter queue[/green]")

        except Exception as e:
            self.console.print(f"[red]Error viewing failed notifications: {e}[/red]")

    async def display_dlq_entries(self, entries: List[Dict[str, Any]], requested_limit: int):
        """Display dead letter queue entries."""
        if not entries:
            self.console.print("[green]✅ Dead letter queue is empty[/green]")
            return

        content = f"""
[bold]Dead Letter Queue Entries[/bold]

[bold blue]Total Entries:[/bold blue] {len(entries)}
[bold blue]Requested Limit:[/bold blue] {requested_limit}

[bold red]Failed Notifications:[/bold red]
"""

        # Create table for DLQ entries
        table = Table(title="Failed Notification Details")
        table.add_column("ID", style="cyan")
        table.add_column("Channel", style="green")
        table.add_column("Title", style="yellow")
        table.add_column("Error", style="red")
        table.add_column("Timestamp", style="blue")

        for entry in entries:
            notification = entry.get("notification", {})
            error_msg = entry.get("error", "Unknown error")

            # Truncate long strings
            title = notification.get("title", "No title")
            if len(title) > 30:
                title = title[:27] + "..."

            error_short = error_msg
            if len(error_short) > 40:
                error_short = error_short[:37] + "..."

            timestamp = entry.get("timestamp", "Unknown")

            table.add_row(
                str(entry.get("id", "N/A")),
                notification.get("channel", "unknown"),
                title,
                error_short,
                timestamp
            )

        self.console.print(table)

        # Show summary statistics
        channel_counts = {}
        for entry in entries:
            channel = entry.get("notification", {}).get("channel", "unknown")
            channel_counts[channel] = channel_counts.get(channel, 0) + 1

        content += f"\n[bold yellow]Failure Summary by Channel:[/bold yellow]\n"
        for channel, count in channel_counts.items():
            content += f"• {channel}: {count} failures\n"

        print_panel(self.console, content, border_style="red")

    async def retry_failed_notifications(self):
        """Retry failed notifications from DLQ."""
        try:
            self.console.print("[yellow]Failed notification retry would attempt redelivery[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error retrying notifications: {e}[/red]")

    async def clear_dead_letter_queue(self):
        """Clear the dead letter queue."""
        try:
            confirm = Confirm.ask("[bold red]Clear all entries from dead letter queue? This cannot be undone.[/bold red]", default=False)

            if confirm:
                self.console.print("[yellow]Dead letter queue clearing would remove all failed notification entries[/yellow]")
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            else:
                self.console.print("[green]Dead letter queue clearing cancelled[/green]")

        except Exception as e:
            self.console.print(f"[red]Error clearing DLQ: {e}[/red]")

    async def analyze_failure_patterns(self):
        """Analyze failure patterns in DLQ."""
        try:
            response = await self.clients.get_json("notification-service/dlq", params={"limit": 1000})

            if response and "items" in response:
                entries = response["items"]

                # Analyze patterns
                channel_failures = {}
                error_patterns = {}
                time_distribution = {}

                for entry in entries:
                    # Channel analysis
                    channel = entry.get("notification", {}).get("channel", "unknown")
                    channel_failures[channel] = channel_failures.get(channel, 0) + 1

                    # Error pattern analysis
                    error = entry.get("error", "Unknown")
                    error_key = error.split(":")[0] if ":" in error else error[:50]
                    error_patterns[error_key] = error_patterns.get(error_key, 0) + 1

                    # Time distribution (simplified)
                    timestamp = entry.get("timestamp", "")
                    hour = timestamp.split("T")[1][:2] if "T" in timestamp else "unknown"
                    time_distribution[hour] = time_distribution.get(hour, 0) + 1

                # Display analysis
                content = f"""
[bold]Dead Letter Queue Failure Analysis[/bold]

[bold blue]Total Failed Notifications:[/bold blue] {len(entries)}

[bold green]Failures by Channel:[/bold green]
"""

                for channel, count in sorted(channel_failures.items(), key=lambda x: x[1], reverse=True):
                    content += f"• {channel}: {count} failures\n"

                content += f"\n[bold yellow]Common Error Patterns:[/bold yellow]\n"
                for error, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
                    content += f"• {error}: {count} occurrences\n"

                print_panel(self.console, content, border_style="yellow")

        except Exception as e:
            self.console.print(f"[red]Error analyzing failure patterns: {e}[/red]")

    async def export_dlq_data(self):
        """Export DLQ data."""
        try:
            self.console.print("[yellow]DLQ data export would save failed notification details to file[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error exporting DLQ data: {e}[/red]")

    async def notification_monitoring_menu(self):
        """Notification monitoring submenu."""
        while True:
            menu = create_menu_table("Notification Monitoring", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Delivery Statistics"),
                ("2", "Monitor Notification Health"),
                ("3", "Track Deduplication Events"),
                ("4", "Notification Performance Metrics"),
                ("5", "Alert Configuration"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_delivery_statistics()
            elif choice == "2":
                await self.monitor_notification_health()
            elif choice == "3":
                await self.track_deduplication_events()
            elif choice == "4":
                await self.notification_performance_metrics()
            elif choice == "5":
                await self.alert_configuration()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_delivery_statistics(self):
        """View notification delivery statistics."""
        try:
            self.console.print("[yellow]Delivery statistics would show success rates, failure rates, and channel performance[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing delivery statistics: {e}[/red]")

    async def monitor_notification_health(self):
        """Monitor notification system health."""
        try:
            self.console.print("[yellow]Notification health monitoring would track system status and performance[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring notification health: {e}[/red]")

    async def track_deduplication_events(self):
        """Track deduplication events."""
        try:
            self.console.print("[yellow]Deduplication tracking would monitor duplicate notification prevention[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error tracking deduplication: {e}[/red]")

    async def notification_performance_metrics(self):
        """View notification performance metrics."""
        try:
            self.console.print("[yellow]Performance metrics would show delivery times, throughput, and latency[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing performance metrics: {e}[/red]")

    async def alert_configuration(self):
        """Configure notification alerts."""
        try:
            self.console.print("[yellow]Alert configuration would set up notifications for system events[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring alerts: {e}[/red]")

    async def channel_configuration_menu(self):
        """Channel configuration submenu."""
        while True:
            menu = create_menu_table("Channel Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Configure Webhook Channels"),
                ("2", "Configure Email Channels"),
                ("3", "Configure Slack Channels"),
                ("4", "Test Channel Configurations"),
                ("5", "Channel Performance Tuning"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.configure_webhook_channels()
            elif choice == "2":
                await self.configure_email_channels()
            elif choice == "3":
                await self.configure_slack_channels()
            elif choice == "4":
                await self.test_channel_configurations()
            elif choice == "5":
                await self.channel_performance_tuning()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def configure_webhook_channels(self):
        """Configure webhook channels."""
        try:
            self.console.print("[yellow]Webhook channel configuration would set up HTTP endpoints for notifications[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring webhooks: {e}[/red]")

    async def configure_email_channels(self):
        """Configure email channels."""
        try:
            self.console.print("[yellow]Email channel configuration would set up SMTP settings and templates[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring email: {e}[/red]")

    async def configure_slack_channels(self):
        """Configure Slack channels."""
        try:
            self.console.print("[yellow]Slack channel configuration would set up webhooks and channel mappings[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring Slack: {e}[/red]")

    async def test_channel_configurations(self):
        """Test channel configurations."""
        try:
            self.console.print("[yellow]Channel configuration testing would validate all notification channels[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error testing configurations: {e}[/red]")

    async def channel_performance_tuning(self):
        """Tune channel performance."""
        try:
            self.console.print("[yellow]Channel performance tuning would optimize delivery rates and reliability[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error tuning performance: {e}[/red]")

    async def notification_service_health_menu(self):
        """Notification service health and configuration submenu."""
        while True:
            menu = create_menu_table("Notification Service Health & Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Service Health"),
                ("2", "Monitor System Status"),
                ("3", "Configuration Management"),
                ("4", "Performance Monitoring"),
                ("5", "Service Logs"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_service_health()
            elif choice == "2":
                await self.monitor_system_status()
            elif choice == "3":
                await self.configuration_management()
            elif choice == "4":
                await self.performance_monitoring()
            elif choice == "5":
                await self.service_logs()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_service_health(self):
        """View notification service health."""
        try:
            response = await self.clients.get_json("notification-service/health")

            if response:
                content = f"""
[bold]Notification Service Health Status[/bold]

[bold blue]Status:[/bold blue] {response.get('status', 'unknown')}
[bold blue]Service:[/bold blue] {response.get('service', 'unknown')}
[bold blue]Version:[/bold blue] {response.get('version', 'unknown')}

[bold green]Description:[/bold green] {response.get('description', 'N/A')}
"""

                print_panel(self.console, content, border_style="green")
            else:
                self.console.print("[red]Failed to retrieve service health[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing service health: {e}[/red]")

    async def monitor_system_status(self):
        """Monitor system status."""
        try:
            self.console.print("[yellow]System status monitoring would show overall notification system health[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring system status: {e}[/red]")

    async def configuration_management(self):
        """Manage notification service configuration."""
        try:
            self.console.print("[yellow]Configuration management would allow editing service settings[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in configuration management: {e}[/red]")

    async def performance_monitoring(self):
        """Monitor notification service performance."""
        try:
            self.console.print("[yellow]Performance monitoring would track delivery metrics and system performance[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring performance: {e}[/red]")

    async def service_logs(self):
        """View notification service logs."""
        try:
            self.console.print("[yellow]Service logs would show recent notification service operations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing service logs: {e}[/red]")

    async def update_owner_from_cli(self, update_request: Dict[str, Any]):
        """Update owner information for CLI usage."""
        try:
            with self.console.status(f"[bold green]Updating owner information...[/bold green]") as status:
                response = await self.clients.post_json("notification-service/owners/update", update_request)

            if response:
                self.console.print("[green]✅ Owner information updated successfully[/green]")
            else:
                self.console.print("[red]❌ Failed to update owner information[/red]")

        except Exception as e:
            self.console.print(f"[red]Error updating owner: {e}[/red]")

    async def resolve_owners_from_cli(self, resolve_request: Dict[str, Any]):
        """Resolve owners for CLI usage."""
        try:
            with self.console.status(f"[bold green]Resolving owners...[/bold green]") as status:
                response = await self.clients.post_json("notification-service/owners/resolve", resolve_request)

            if response and "resolved" in response:
                owners = resolve_request.get("owners", [])
                await self.display_owner_resolutions(response["resolved"], owners)
            else:
                self.console.print("[red]❌ Failed to resolve owners[/red]")

        except Exception as e:
            self.console.print(f"[red]Error resolving owners: {e}[/red]")

    async def send_notification_from_cli(self, notification_request: Dict[str, Any]):
        """Send notification for CLI usage."""
        try:
            channel = notification_request.get("channel", "unknown")
            target = notification_request.get("target", "unknown")

            with self.console.status(f"[bold green]Sending {channel} notification...[/bold green]") as status:
                response = await self.clients.post_json("notification-service/notify", notification_request)

            if response:
                await self.display_notification_result(response, channel, target)
            else:
                self.console.print("[red]❌ Failed to send notification[/red]")

        except Exception as e:
            self.console.print(f"[red]Error sending notification: {e}[/red]")
