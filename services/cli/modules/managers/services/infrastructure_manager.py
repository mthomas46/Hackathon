"""Infrastructure Manager module for CLI service.

Provides power-user operations for infrastructure monitoring including
Redis, DLQ, sagas, tracing, and system infrastructure management.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from ...base.base_manager import BaseManager


class InfrastructureManager(BaseManager):
    """Manager for infrastructure power-user operations."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

    async def infrastructure_menu(self):
        """Main infrastructure management menu with enhanced interactive experience."""
        await self.run_menu_loop("Infrastructure Management", use_interactive=True)

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return the main menu items for infrastructure operations."""
        return [
            ("1", "Redis Operations (Pub/Sub, Keys, Performance)"),
            ("2", "Dead Letter Queue (DLQ) Management"),
            ("3", "Saga Orchestration Monitoring"),
            ("4", "Distributed Tracing"),
            ("5", "Event History & Replay"),
            ("6", "Infrastructure Health Dashboard")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle a menu choice. Return True to continue, False to exit."""
        if choice == "1":
            await self.redis_operations_menu()
        elif choice == "2":
            await self.dlq_management_menu()
        elif choice == "3":
            await self.saga_monitoring_menu()
        elif choice == "4":
            await self.tracing_menu()
        elif choice == "5":
            await self.event_history_menu()
        elif choice == "6":
            await self.infrastructure_health_dashboard()
        else:
            self.display.show_error("Invalid option. Please try again.")
        return True

    async def redis_operations_menu(self):
        """Redis operations submenu."""
        while True:
            menu = create_menu_table("Redis Operations", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Redis Info"),
                ("2", "Monitor Pub/Sub Channels"),
                ("3", "Key Space Analysis"),
                ("4", "Redis Performance Metrics"),
                ("5", "Clear Redis Keys"),
                ("6", "Redis Configuration"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.redis_info()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.monitor_pubsub()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.key_space_analysis()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                await self.redis_performance()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "5":
                await self.clear_redis_keys()
            elif choice == "6":
                await self.redis_configuration()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def redis_info(self):
        """View Redis info."""
        try:
            with self.console.status("[bold green]Fetching Redis info...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/redis/info")

            if response.get("redis_info"):
                info = response["redis_info"]
                content = f"""
[bold]Redis Information[/bold]

Server Version: {info.get('redis_version', 'unknown')}
Uptime: {info.get('uptime_in_days', 0)} days
Connected Clients: {info.get('connected_clients', 0)}
Used Memory: {info.get('used_memory_human', 'unknown')}
Total Connections: {info.get('total_connections_received', 0)}

Key Statistics:
  Total Keys: {info.get('total_keys', 0)}
  Keys with Expiry: {info.get('keys_with_expiry', 0)}
  Expired Keys: {info.get('expired_keys', 0)}

Memory:
  Used: {info.get('used_memory_human', 'unknown')}
  Peak: {info.get('used_memory_peak_human', 'unknown')}
  Fragmentation: {info.get('mem_fragmentation_ratio', 0):.2f}

Connections:
  Connected: {info.get('connected_clients', 0)}
  Blocked: {info.get('blocked_clients', 0)}
  Tracking: {info.get('tracking_clients', 0)}
"""
                print_panel(self.console, content, border_style="red")
            else:
                self.console.print("[yellow]Redis info not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching Redis info: {e}[/red]")

    async def monitor_pubsub(self):
        """Monitor Pub/Sub channels."""
        try:
            with self.console.status("[bold green]Monitoring Pub/Sub channels...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/redis/pubsub")

            if response.get("pubsub_info"):
                pubsub = response["pubsub_info"]
                content = f"""
[bold]Redis Pub/Sub Status[/bold]

Active Channels: {pubsub.get('active_channels', 0)}
Active Patterns: {pubsub.get('active_patterns', 0)}
Subscriptions: {pubsub.get('subscriptions', 0)}

Channel Activity (last 5 minutes):
"""
                if pubsub.get("recent_activity"):
                    for activity in pubsub["recent_activity"]:
                        content += f"  {activity.get('channel', 'unknown')}: {activity.get('message_count', 0)} messages\n"

                content += f"\nActive Channels:\n"
                if pubsub.get("channels"):
                    for channel in pubsub["channels"][:10]:  # Show first 10
                        content += f"  • {channel.get('name', 'unknown')}: {channel.get('subscriber_count', 0)} subscribers\n"
                    if len(pubsub["channels"]) > 10:
                        content += f"  ... and {len(pubsub['channels']) - 10} more channels\n"

                print_panel(self.console, content, border_style="cyan")
            else:
                self.console.print("[yellow]Pub/Sub info not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring Pub/Sub: {e}[/red]")

    async def key_space_analysis(self):
        """Key space analysis."""
        try:
            pattern = Prompt.ask("[bold cyan]Key pattern (e.g., 'doc:*', 'wf:*')[/bold cyan]", default="*")
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="100")

            with self.console.status(f"[bold green]Analyzing keys matching '{pattern}'...") as status:
                response = await self.clients.get_json(f"orchestrator/infrastructure/redis/keys?pattern={pattern}&limit={limit}")

            if response.get("key_analysis"):
                analysis = response["key_analysis"]
                content = f"""
[bold]Redis Key Space Analysis[/bold]

Pattern: {pattern}
Total Keys Found: {analysis.get('total_keys', 0)}
Sample Size: {min(int(limit), analysis.get('total_keys', 0))}

Key Types:
"""
                if analysis.get("key_types"):
                    for key_type, count in analysis["key_types"].items():
                        content += f"  {key_type}: {count} keys\n"

                content += f"""
Memory Usage:
  Total: {analysis.get('total_memory_bytes', 0)} bytes
  Average per Key: {analysis.get('avg_memory_per_key', 0):.2f} bytes

Sample Keys:
"""
                if analysis.get("sample_keys"):
                    for key_info in analysis["sample_keys"][:10]:  # Show first 10
                        content += f"  • {key_info.get('key', 'unknown')}: {key_info.get('type', 'unknown')}, {key_info.get('size_bytes', 0)} bytes\n"

                print_panel(self.console, content, border_style="yellow")
            else:
                self.console.print("[yellow]Key space analysis not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing key space: {e}[/red]")

    async def redis_performance(self):
        """Redis performance metrics."""
        try:
            with self.console.status("[bold green]Fetching Redis performance metrics...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/redis/performance")

            if response.get("performance"):
                perf = response["performance"]
                content = f"""
[bold]Redis Performance Metrics[/bold]

Commands Processed: {perf.get('total_commands_processed', 0)}
Commands per Second: {perf.get('instantaneous_ops_per_sec', 0)}

Network:
  Bytes Received: {perf.get('total_net_input_bytes', 0)} bytes
  Bytes Sent: {perf.get('total_net_output_bytes', 0)} bytes
  Connections: {perf.get('total_connections_received', 0)}

Cache Performance:
  Keyspace Hits: {perf.get('keyspace_hits', 0)}
  Keyspace Misses: {perf.get('keyspace_misses', 0)}
  Hit Rate: {perf.get('hit_rate_percent', 0):.2f}%

Latency:
  Average: {perf.get('avg_latency_ms', 0):.2f} ms
  Max: {perf.get('max_latency_ms', 0):.2f} ms

Evictions: {perf.get('evicted_keys', 0)}
Expired Keys: {perf.get('expired_keys', 0)}
"""
                print_panel(self.console, content, border_style="magenta")
            else:
                self.console.print("[yellow]Performance metrics not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching performance metrics: {e}[/red]")

    async def clear_redis_keys(self):
        """Clear Redis keys."""
        try:
            pattern = Prompt.ask("[bold cyan]Key pattern to delete[/bold cyan]", default="")
            confirm = Confirm.ask(f"[bold red]This will delete ALL keys matching '{pattern}'. Continue?[/bold red]")

            if confirm:
                with self.console.status(f"[bold green]Deleting keys matching '{pattern}'...") as status:
                    response = await self.clients.post_json("orchestrator/infrastructure/redis/clear", {
                        "pattern": pattern
                    })

                if response.get("deleted_count"):
                    self.console.print(f"[green]✅ Deleted {response['deleted_count']} keys[/green]")
                else:
                    self.console.print("[yellow]No keys matched the pattern.[/yellow]")
            else:
                self.console.print("[yellow]Key deletion cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error clearing Redis keys: {e}[/red]")

    async def redis_configuration(self):
        """Redis configuration."""
        try:
            with self.console.status("[bold green]Fetching Redis configuration...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/redis/config")

            if response.get("config"):
                config = response["config"]
                content = "[bold]Redis Configuration[/bold]\n\n"

                # Group config by category
                categories = {}
                for key, value in config.items():
                    category = key.split('_')[0] if '_' in key else 'general'
                    if category not in categories:
                        categories[category] = []
                    categories[category].append((key, value))

                for category, settings in categories.items():
                    content += f"[bold]{category.upper()}:[/bold]\n"
                    for key, value in settings[:10]:  # Show first 10 per category
                        content += f"  {key}: {value}\n"
                    if len(settings) > 10:
                        content += f"  ... and {len(settings) - 10} more settings\n"
                    content += "\n"

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]Redis configuration not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching Redis configuration: {e}[/red]")

    async def dlq_management_menu(self):
        """DLQ management submenu."""
        while True:
            menu = create_menu_table("Dead Letter Queue Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View DLQ Statistics"),
                ("2", "Browse DLQ Messages"),
                ("3", "Retry Failed Messages"),
                ("4", "Clear DLQ Messages"),
                ("5", "DLQ Configuration"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.dlq_statistics()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.browse_dlq_messages()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.retry_failed_messages()
            elif choice == "4":
                await self.clear_dlq_messages()
            elif choice == "5":
                await self.dlq_configuration()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def dlq_statistics(self):
        """View DLQ statistics."""
        try:
            with self.console.status("[bold green]Fetching DLQ statistics...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/dlq/stats")

            if response.get("dlq_stats"):
                stats = response["dlq_stats"]
                content = f"""
[bold]Dead Letter Queue Statistics[/bold]

Total Messages: {stats.get('total_messages', 0)}
Processed Today: {stats.get('processed_today', 0)}
Oldest Message: {stats.get('oldest_message_age_hours', 0):.1f} hours

Failure Reasons:
"""
                if stats.get("failure_reasons"):
                    for reason, count in stats["failure_reasons"].items():
                        content += f"  {reason}: {count} messages\n"

                content += f"""
Queues:
"""
                if stats.get("queues"):
                    for queue_name, queue_stats in stats["queues"].items():
                        content += f"  {queue_name}: {queue_stats.get('message_count', 0)} messages\n"

                content += f"""
Retry Statistics:
  Successful Retries: {stats.get('successful_retries', 0)}
  Failed Retries: {stats.get('failed_retries', 0)}
  Success Rate: {stats.get('retry_success_rate', 0):.1f}%
"""
                print_panel(self.console, content, border_style="red")
            else:
                self.console.print("[yellow]DLQ statistics not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching DLQ statistics: {e}[/red]")

    async def browse_dlq_messages(self):
        """Browse DLQ messages."""
        try:
            queue_name = Prompt.ask("[bold cyan]Queue name[/bold cyan]", default="")
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="20")

            endpoint = f"orchestrator/infrastructure/dlq/messages?limit={limit}"
            if queue_name:
                endpoint += f"&queue={queue_name}"

            with self.console.status("[bold green]Fetching DLQ messages...") as status:
                response = await self.clients.get_json(endpoint)

            if response.get("messages"):
                table = Table(title="DLQ Messages")
                table.add_column("ID", style="cyan")
                table.add_column("Queue", style="green")
                table.add_column("Failure Reason", style="red")
                table.add_column("Retry Count", style="yellow")
                table.add_column("Age (hours)", style="magenta")

                for msg in response["messages"]:
                    table.add_row(
                        msg.get("id", "N/A")[:8],
                        msg.get("queue", "unknown"),
                        msg.get("failure_reason", "unknown")[:30],
                        str(msg.get("retry_count", 0)),
                        f"{msg.get('age_hours', 0):.1f}"
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No DLQ messages found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error browsing DLQ messages: {e}[/red]")

    async def retry_failed_messages(self):
        """Retry failed messages."""
        try:
            queue_name = Prompt.ask("[bold cyan]Queue name[/bold cyan]", default="")
            message_ids = Prompt.ask("[bold cyan]Message IDs (comma-separated, or 'all')[/bold cyan]", default="")

            retry_config = {}
            if queue_name:
                retry_config["queue"] = queue_name
            if message_ids and message_ids != "all":
                retry_config["message_ids"] = [id.strip() for id in message_ids.split(",")]

            confirm = Confirm.ask(f"[bold yellow]This will retry {'all' if message_ids == 'all' else len(retry_config.get('message_ids', []))} failed messages. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Retrying failed messages...") as status:
                    response = await self.clients.post_json("orchestrator/infrastructure/dlq/retry", retry_config)

                if response.get("retry_result"):
                    result = response["retry_result"]
                    content = f"""
[bold]Retry Results[/bold]

Total Attempted: {result.get('attempted', 0)}
Successful: {result.get('successful', 0)}
Failed: {result.get('failed', 0)}
Success Rate: {result.get('success_rate', 0):.1f}%

Details:
"""
                    if result.get("details"):
                        for detail in result["details"][:10]:  # Show first 10
                            status_icon = "✅" if detail.get("success") else "❌"
                            content += f"  {status_icon} {detail.get('message_id', 'unknown')[:8]}: {detail.get('result', 'unknown')}\n"

                    print_panel(self.console, content, border_style="green" if result.get('success_rate', 0) > 50 else "red")
                else:
                    self.console.print("[red]❌ Retry operation failed[/red]")
            else:
                self.console.print("[yellow]Retry operation cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error retrying failed messages: {e}[/red]")

    async def clear_dlq_messages(self):
        """Clear DLQ messages."""
        try:
            queue_name = Prompt.ask("[bold cyan]Queue name[/bold cyan]", default="")
            criteria = Prompt.ask("[bold cyan]Clear criteria (JSON)[/bold cyan]", default='{"age_hours": {"$gt": 24}}')

            import json
            clear_criteria = json.loads(criteria)

            confirm = Confirm.ask(f"[bold red]This will permanently delete DLQ messages matching the criteria. Continue?[/bold red]")

            if confirm:
                clear_config = {"criteria": clear_criteria}
                if queue_name:
                    clear_config["queue"] = queue_name

                with self.console.status("[bold green]Clearing DLQ messages...") as status:
                    response = await self.clients.post_json("orchestrator/infrastructure/dlq/clear", clear_config)

                if response.get("cleared_count"):
                    self.console.print(f"[green]✅ Cleared {response['cleared_count']} DLQ messages[/green]")
                else:
                    self.console.print("[yellow]No messages matched the clear criteria.[/yellow]")
            else:
                self.console.print("[yellow]DLQ clear operation cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error clearing DLQ messages: {e}[/red]")

    async def dlq_configuration(self):
        """DLQ configuration."""
        try:
            with self.console.status("[bold green]Fetching DLQ configuration...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/dlq/config")

            if response.get("dlq_config"):
                config = response["dlq_config"]
                content = f"""
[bold]DLQ Configuration[/bold]

Max Retry Attempts: {config.get('max_retry_attempts', 0)}
Retry Delay: {config.get('retry_delay_seconds', 0)} seconds
Max Message Age: {config.get('max_message_age_hours', 0)} hours

Queues:
"""
                if config.get("queues"):
                    for queue_name, queue_config in config["queues"].items():
                        content += f"  {queue_name}:\n"
                        content += f"    Max retries: {queue_config.get('max_retries', 0)}\n"
                        content += f"    TTL: {queue_config.get('ttl_hours', 0)} hours\n"

                content += f"""
Monitoring:
  Alert threshold: {config.get('alert_threshold', 0)} messages
  Auto-cleanup: {'Enabled' if config.get('auto_cleanup') else 'Disabled'}
"""
                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]DLQ configuration not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching DLQ configuration: {e}[/red]")

    async def saga_monitoring_menu(self):
        """Saga orchestration monitoring submenu."""
        while True:
            menu = create_menu_table("Saga Orchestration Monitoring", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Active Sagas"),
                ("2", "Saga Statistics"),
                ("3", "Failed Saga Recovery"),
                ("4", "Saga Configuration"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_active_sagas()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.saga_statistics()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.failed_saga_recovery()
            elif choice == "4":
                await self.saga_configuration()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_active_sagas(self):
        """View active sagas."""
        try:
            with self.console.status("[bold green]Fetching active sagas...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/saga/active")

            if response.get("sagas"):
                table = Table(title="Active Sagas")
                table.add_column("Saga ID", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Steps", style="magenta")
                table.add_column("Progress", style="blue")

                for saga in response["sagas"]:
                    progress = f"{saga.get('completed_steps', 0)}/{saga.get('total_steps', 0)}"
                    status_color = {
                        "running": "yellow",
                        "waiting": "blue",
                        "compensating": "red",
                        "completed": "green"
                    }.get(saga.get("status", "unknown"), "white")

                    table.add_row(
                        saga.get("id", "N/A")[:8],
                        saga.get("type", "unknown"),
                        f"[{status_color}]{saga.get('status', 'unknown')}[/{status_color}]",
                        str(saga.get("total_steps", 0)),
                        progress
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No active sagas found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching active sagas: {e}[/red]")

    async def saga_statistics(self):
        """Saga statistics."""
        try:
            with self.console.status("[bold green]Fetching saga statistics...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/saga/stats")

            if response.get("saga_stats"):
                stats = response["saga_stats"]
                content = f"""
[bold]Saga Orchestration Statistics[/bold]

Active Sagas: {stats.get('active_sagas', 0)}
Completed Today: {stats.get('completed_today', 0)}
Failed Today: {stats.get('failed_today', 0)}

Success Rate: {stats.get('success_rate_percent', 0):.1f}%

Saga Types:
"""
                if stats.get("saga_types"):
                    for saga_type, count in stats["saga_types"].items():
                        content += f"  {saga_type}: {count} sagas\n"

                content += f"""
Failure Reasons:
"""
                if stats.get("failure_reasons"):
                    for reason, count in stats["failure_reasons"].items():
                        content += f"  {reason}: {count} failures\n"

                content += f"""
Average Completion Time: {stats.get('avg_completion_time_minutes', 0):.1f} minutes
Longest Running Saga: {stats.get('longest_running_saga_age_minutes', 0)} minutes
"""
                print_panel(self.console, content, border_style="cyan")
            else:
                self.console.print("[yellow]Saga statistics not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching saga statistics: {e}[/red]")

    async def failed_saga_recovery(self):
        """Failed saga recovery."""
        try:
            saga_id = Prompt.ask("[bold cyan]Failed saga ID[/bold cyan]")

            with self.console.status(f"[bold green]Attempting recovery for saga {saga_id}...") as status:
                response = await self.clients.post_json(f"orchestrator/infrastructure/saga/{saga_id}/recover", {})

            if response.get("recovery_result"):
                result = response["recovery_result"]
                content = f"""
[bold]Saga Recovery Result[/bold]

Saga ID: {saga_id}
Recovery Status: {'✅ SUCCESS' if result.get('successful') else '❌ FAILED'}

Steps Recovered: {result.get('steps_recovered', 0)}
Steps Failed: {result.get('steps_failed', 0)}

Details:
"""
                if result.get("details"):
                    for detail in result["details"]:
                        status_icon = "✅" if detail.get("success") else "❌"
                        content += f"  {status_icon} {detail.get('step', 'unknown')}: {detail.get('result', 'unknown')}\n"

                print_panel(self.console, content, border_style="green" if result.get('successful') else "red")
            else:
                self.console.print("[red]❌ Saga recovery failed[/red]")

        except Exception as e:
            self.console.print(f"[red]Error attempting saga recovery: {e}[/red]")

    async def saga_configuration(self):
        """Saga configuration."""
        try:
            with self.console.status("[bold green]Fetching saga configuration...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/saga/config")

            if response.get("saga_config"):
                config = response["saga_config"]
                content = f"""
[bold]Saga Configuration[/bold]

Timeout Settings:
  Default timeout: {config.get('default_timeout_minutes', 0)} minutes
  Max timeout: {config.get('max_timeout_minutes', 0)} minutes

Retry Settings:
  Max retries: {config.get('max_retries', 0)}
  Retry delay: {config.get('retry_delay_seconds', 0)} seconds

Compensation:
  Auto-compensation: {'Enabled' if config.get('auto_compensation') else 'Disabled'}
  Compensation timeout: {config.get('compensation_timeout_minutes', 0)} minutes

Monitoring:
  Alert threshold: {config.get('alert_threshold_failures', 0)} failures
  Metrics collection: {'Enabled' if config.get('metrics_enabled') else 'Disabled'}
"""
                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]Saga configuration not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching saga configuration: {e}[/red]")

    async def tracing_menu(self):
        """Distributed tracing submenu."""
        while True:
            menu = create_menu_table("Distributed Tracing", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Tracing Statistics"),
                ("2", "View Trace Details"),
                ("3", "Search Traces"),
                ("4", "Tracing Configuration"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.tracing_statistics()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.view_trace_details()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.search_traces()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                await self.tracing_configuration()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def tracing_statistics(self):
        """Tracing statistics."""
        try:
            with self.console.status("[bold green]Fetching tracing statistics...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/tracing/stats")

            if response.get("tracing_stats"):
                stats = response["tracing_stats"]
                content = f"""
[bold]Distributed Tracing Statistics[/bold]

Total Traces: {stats.get('total_traces', 0)}
Active Traces: {stats.get('active_traces', 0)}
Completed Today: {stats.get('completed_today', 0)}

Performance:
  Average Trace Duration: {stats.get('avg_trace_duration_ms', 0):.2f} ms
  95th Percentile: {stats.get('p95_duration_ms', 0):.2f} ms
  99th Percentile: {stats.get('p99_duration_ms', 0):.2f} ms

Services Involved:
"""
                if stats.get("services_involved"):
                    for service, count in stats["services_involved"].items():
                        content += f"  {service}: {count} traces\n"

                content += f"""
Error Traces:
  Total: {stats.get('error_traces', 0)}
  Error Rate: {stats.get('error_rate_percent', 0):.2f}%

Sampling:
  Sample Rate: {stats.get('sample_rate_percent', 0):.2f}%
  Traces Sampled: {stats.get('sampled_traces', 0)}
"""
                print_panel(self.console, content, border_style="purple")
            else:
                self.console.print("[yellow]Tracing statistics not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching tracing statistics: {e}[/red]")

    async def view_trace_details(self):
        """View trace details."""
        try:
            trace_id = Prompt.ask("[bold cyan]Trace ID[/bold cyan]")

            with self.console.status(f"[bold green]Fetching trace {trace_id}...") as status:
                response = await self.clients.get_json(f"orchestrator/infrastructure/tracing/trace/{trace_id}")

            if response.get("trace"):
                trace = response["trace"]
                content = f"""
[bold]Trace Details[/bold]

Trace ID: {trace.get('id', 'N/A')}
Status: {trace.get('status', 'unknown')}
Duration: {trace.get('duration_ms', 0):.2f} ms
Started: {trace.get('start_time', 'unknown')}

Services Involved: {len(trace.get('services', []))}

Service Timeline:
"""
                if trace.get("spans"):
                    for span in trace["spans"]:
                        content += f"  {span.get('service', 'unknown')}.{span.get('operation', 'unknown')}: {span.get('duration_ms', 0):.2f} ms\n"

                if trace.get("errors"):
                    content += f"\nErrors:\n"
                    for error in trace["errors"]:
                        content += f"  {error.get('service', 'unknown')}: {error.get('message', 'Unknown error')}\n"

                print_panel(self.console, content, border_style="cyan")
            else:
                self.console.print("[red]Trace not found.[/red]")

        except Exception as e:
            self.console.print(f"[red]Error fetching trace details: {e}[/red]")

    async def search_traces(self):
        """Search traces."""
        try:
            search_criteria = Prompt.ask("[bold cyan]Search criteria (JSON)[/bold cyan]",
                                       default='{"status": "error", "duration_ms": {"$gt": 1000}}')
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="20")

            import json
            criteria = json.loads(search_criteria)

            with self.console.status("[bold green]Searching traces...") as status:
                response = await self.clients.get_json(f"orchestrator/infrastructure/tracing/search?criteria={json.dumps(criteria)}&limit={limit}")

            if response.get("traces"):
                table = Table(title="Trace Search Results")
                table.add_column("Trace ID", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Duration", style="yellow")
                table.add_column("Services", style="magenta")
                table.add_column("Started", style="blue")

                for trace in response["traces"]:
                    status_color = "green" if trace.get("status") == "completed" else "red" if trace.get("status") == "error" else "yellow"
                    table.add_row(
                        trace.get("id", "N/A")[:8],
                        f"[{status_color}]{trace.get('status', 'unknown')}[/{status_color}]",
                        f"{trace.get('duration_ms', 0):.2f}ms",
                        str(len(trace.get('services', []))),
                        trace.get("start_time", "unknown")[:19]
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No traces found matching criteria.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error searching traces: {e}[/red]")

    async def tracing_configuration(self):
        """Tracing configuration."""
        try:
            with self.console.status("[bold green]Fetching tracing configuration...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/tracing/config")

            if response.get("tracing_config"):
                config = response["tracing_config"]
                content = f"""
[bold]Tracing Configuration[/bold]

Enabled: {'Yes' if config.get('enabled') else 'No'}
Sample Rate: {config.get('sample_rate', 0):.2f}%

Exporters:
"""
                if config.get("exporters"):
                    for exporter in config["exporters"]:
                        content += f"  • {exporter.get('type', 'unknown')}: {exporter.get('endpoint', 'unknown')}\n"

                content += f"""
Settings:
  Max spans per trace: {config.get('max_spans_per_trace', 0)}
  Max trace duration: {config.get('max_trace_duration_minutes', 0)} minutes
  Retention period: {config.get('retention_days', 0)} days

Tags:
"""
                if config.get("default_tags"):
                    for key, value in config["default_tags"].items():
                        content += f"  {key}: {value}\n"

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]Tracing configuration not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching tracing configuration: {e}[/red]")

    async def event_history_menu(self):
        """Event history and replay submenu."""
        while True:
            menu = create_menu_table("Event History & Replay", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Event History"),
                ("2", "Search Events"),
                ("3", "Replay Events"),
                ("4", "Event Statistics"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_event_history()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.search_events()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.replay_events()
            elif choice == "4":
                await self.event_statistics()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_event_history(self):
        """View event history."""
        try:
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="50")

            with self.console.status("[bold green]Fetching event history...") as status:
                response = await self.clients.get_json(f"orchestrator/infrastructure/events/history?limit={limit}")

            if response.get("events"):
                table = Table(title="Event History")
                table.add_column("Event ID", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Aggregate", style="yellow")
                table.add_column("Timestamp", style="blue")

                for event in response["events"]:
                    table.add_row(
                        event.get("id", "N/A")[:8],
                        event.get("event_type", "unknown"),
                        event.get("aggregate_id", "N/A")[:8],
                        event.get("timestamp", "unknown")[:19]
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No events found in history.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching event history: {e}[/red]")

    async def search_events(self):
        """Search events."""
        try:
            event_type = Prompt.ask("[bold cyan]Event type[/bold cyan]", default="")
            aggregate_id = Prompt.ask("[bold cyan]Aggregate ID[/bold cyan]", default="")
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="20")

            search_params = f"?limit={limit}"
            if event_type:
                search_params += f"&event_type={event_type}"
            if aggregate_id:
                search_params += f"&aggregate_id={aggregate_id}"

            with self.console.status("[bold green]Searching events...") as status:
                response = await self.clients.get_json(f"orchestrator/infrastructure/events/search{search_params}")

            if response.get("events"):
                self.display_event_results(response["events"], f"Event Search Results")
            else:
                self.console.print("[yellow]No events found matching criteria.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error searching events: {e}[/red]")

    def display_event_results(self, events, title):
        """Display event search results."""
        table = Table(title=title)
        table.add_column("Event ID", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Aggregate", style="yellow")
        table.add_column("Data", style="white")
        table.add_column("Timestamp", style="blue")

        for event in events[:20]:  # Show first 20
            # Truncate event data for display
            event_data = str(event.get("data", {}))
            if len(event_data) > 50:
                event_data = event_data[:47] + "..."

            table.add_row(
                event.get("id", "N/A")[:8],
                event.get("event_type", "unknown"),
                event.get("aggregate_id", "N/A")[:8],
                event_data,
                event.get("timestamp", "unknown")[:19]
            )

        self.console.print(table)

    async def replay_events(self):
        """Replay events."""
        try:
            event_ids = Prompt.ask("[bold cyan]Event IDs to replay (comma-separated)[/bold cyan]")

            event_id_list = [id.strip() for id in event_ids.split(",")]

            confirm = Confirm.ask(f"[bold yellow]This will replay {len(event_id_list)} events. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Replaying events...") as status:
                    response = await self.clients.post_json("orchestrator/infrastructure/events/replay", {
                        "event_ids": event_id_list
                    })

                if response.get("replay_result"):
                    result = response["replay_result"]
                    content = f"""
[bold]Event Replay Results[/bold]

Total Events: {result.get('total_events', 0)}
Successful: {result.get('successful', 0)}
Failed: {result.get('failed', 0)}

Details:
"""
                    if result.get("details"):
                        for detail in result["details"]:
                            status_icon = "✅" if detail.get("success") else "❌"
                            content += f"  {status_icon} {detail.get('event_id', 'unknown')[:8]}: {detail.get('result', 'unknown')}\n"

                    print_panel(self.console, content, border_style="green" if result.get('failed', 0) == 0 else "red")
                else:
                    self.console.print("[red]❌ Event replay failed[/red]")
            else:
                self.console.print("[yellow]Event replay cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error replaying events: {e}[/red]")

    async def event_statistics(self):
        """Event statistics."""
        try:
            with self.console.status("[bold green]Fetching event statistics...") as status:
                response = await self.clients.get_json("orchestrator/infrastructure/events/stats")

            if response.get("event_stats"):
                stats = response["event_stats"]
                content = f"""
[bold]Event Statistics[/bold]

Total Events: {stats.get('total_events', 0)}
Events Today: {stats.get('events_today', 0)}
Average Events/Hour: {stats.get('avg_events_per_hour', 0):.1f}

Event Types:
"""
                if stats.get("event_types"):
                    for event_type, count in stats["event_types"].items():
                        content += f"  {event_type}: {count} events\n"

                content += f"""
Processing:
  Average Processing Time: {stats.get('avg_processing_time_ms', 0):.2f} ms
  Failed Events: {stats.get('failed_events', 0)}
  Retry Rate: {stats.get('retry_rate_percent', 0):.2f}%

Storage:
  Events Stored: {stats.get('events_stored', 0)}
  Storage Size: {stats.get('storage_size_mb', 0):.2f} MB
  Retention Days: {stats.get('retention_days', 0)}
"""
                print_panel(self.console, content, border_style="cyan")
            else:
                self.console.print("[yellow]Event statistics not available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching event statistics: {e}[/red]")

    async def infrastructure_health_dashboard(self):
        """Infrastructure health dashboard."""
        try:
            with self.console.status("[bold green]Generating infrastructure health dashboard...") as status:
                # Fetch all infrastructure health data
                redis_response = await self.clients.get_json("orchestrator/infrastructure/redis/info")
                dlq_response = await self.clients.get_json("orchestrator/infrastructure/dlq/stats")
                saga_response = await self.clients.get_json("orchestrator/infrastructure/saga/stats")
                tracing_response = await self.clients.get_json("orchestrator/infrastructure/tracing/stats")

            content = "[bold]Infrastructure Health Dashboard[/bold]\n\n"

            # Redis Health
            content += "[bold red]Redis:[/bold red]\n"
            if redis_response.get("redis_info"):
                redis = redis_response["redis_info"]
                content += f"  Status: ✅ Connected ({redis.get('connected_clients', 0)} clients)\n"
                content += f"  Memory: {redis.get('used_memory_human', 'unknown')}\n"
                content += f"  Uptime: {redis.get('uptime_in_days', 0)} days\n"
            else:
                content += "  Status: ❌ Disconnected\n"
            content += "\n"

            # DLQ Health
            content += "[bold red]Dead Letter Queue:[/bold red]\n"
            if dlq_response.get("dlq_stats"):
                dlq = dlq_response["dlq_stats"]
                total_msgs = dlq.get('total_messages', 0)
                status = "✅ Healthy" if total_msgs < 100 else "⚠️ High" if total_msgs < 1000 else "❌ Critical"
                content += f"  Status: {status} ({total_msgs} messages)\n"
                content += f"  Processed Today: {dlq.get('processed_today', 0)}\n"
            else:
                content += "  Status: ❓ Unknown\n"
            content += "\n"

            # Saga Health
            content += "[bold cyan]Saga Orchestration:[/bold cyan]\n"
            if saga_response.get("saga_stats"):
                saga = saga_response["saga_stats"]
                success_rate = saga.get('success_rate_percent', 0)
                status = "✅ Healthy" if success_rate > 95 else "⚠️ Degraded" if success_rate > 80 else "❌ Critical"
                content += f"  Status: {status} ({success_rate:.1f}% success rate)\n"
                content += f"  Active Sagas: {saga.get('active_sagas', 0)}\n"
                content += f"  Failed Today: {saga.get('failed_today', 0)}\n"
            else:
                content += "  Status: ❓ Unknown\n"
            content += "\n"

            # Tracing Health
            content += "[bold purple]Distributed Tracing:[/bold purple]\n"
            if tracing_response.get("tracing_stats"):
                tracing = tracing_response["tracing_stats"]
                error_rate = tracing.get('error_rate_percent', 0)
                status = "✅ Healthy" if error_rate < 5 else "⚠️ Issues" if error_rate < 15 else "❌ Problems"
                content += f"  Status: {status} ({error_rate:.1f}% error rate)\n"
                content += f"  Active Traces: {tracing.get('active_traces', 0)}\n"
                content += f"  Average Duration: {tracing.get('avg_trace_duration_ms', 0):.2f} ms\n"
            else:
                content += "  Status: ❓ Unknown\n"

            print_panel(self.console, content, border_style="green")

        except Exception as e:
            self.console.print(f"[red]Error generating infrastructure health dashboard: {e}[/red]")
