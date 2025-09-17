from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt
import json
from datetime import datetime, timedelta

from services.shared.integrations.clients.clients import ServiceClients
from ...utils.display_helpers import print_kv, print_list


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    # ============================================================================
    # LOG SUBMISSION ENDPOINTS
    # ============================================================================

    async def submit_log():
        """Submit a single log entry."""
        console.print("[bold blue]📝 Submit Log Entry[/bold blue]")

        service = Prompt.ask("Service name", default="cli")
        level = Prompt.ask("Log level", default="info")
        message = Prompt.ask("Log message")

        if not message.strip():
            console.print("[red]❌ Log message is required[/red]")
            return

        # Optional context
        context_input = Prompt.ask("Context JSON (optional)", default="")
        context = None
        if context_input.strip():
            try:
                context = json.loads(context_input)
            except:
                console.print("[yellow]⚠️  Invalid JSON context, ignoring[/yellow]")

        payload = {
            "service": service,
            "level": level,
            "message": message
        }
        if context:
            payload["context"] = context

        url = f"{clients.log_collector_url()}/logs"
        rx = await clients.post_json(url, payload)

        if rx.get("status") == "ok":
            console.print("[green]✅ Log entry submitted successfully[/green]")
            print_kv(console, "Total log count", rx.get("count", "unknown"))
        else:
            console.print(f"[red]❌ Failed to submit log: {rx}[/red]")

    async def submit_batch_logs():
        """Submit multiple log entries at once."""
        count = Prompt.ask("Number of log entries to submit", default="3")
        count = int(count)

        service = Prompt.ask("Service name for all logs", default="cli")
        default_level = Prompt.ask("Default log level", default="info")

        logs = []
        for i in range(count):
            console.print(f"\n[bold cyan]Log Entry {i+1}/{count}[/bold cyan]")
            level = Prompt.ask(f"Level (default: {default_level})", default=default_level)
            message = Prompt.ask(f"Message {i+1}")

            if not message.strip():
                console.print(f"[yellow]⚠️  Skipping empty message {i+1}[/yellow]")
                continue

            logs.append({
                "service": service,
                "level": level,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })

        if not logs:
            console.print("[red]❌ No valid log entries to submit[/red]")
            return

        console.print(f"\n[bold blue]📤 Submitting {len(logs)} log entries...[/bold blue]")

        url = f"{clients.log_collector_url()}/logs/batch"
        rx = await clients.post_json(url, {"logs": logs})

        if rx.get("status") == "ok":
            console.print("[green]✅ Batch log submission successful[/green]")
            print_kv(console, "Submitted", len(logs))
            print_kv(console, "Total log count", rx.get("total_count", "unknown"))
        else:
            console.print(f"[red]❌ Batch submission failed: {rx}[/red]")

    async def generate_test_logs():
        """Generate test log entries for testing purposes."""
        console.print("[bold purple]🧪 Generate Test Logs[/bold purple]")

        service = Prompt.ask("Service name", default="test-service")
        count = Prompt.ask("Number of test logs to generate", default="10")
        count = int(count)

        log_levels = ["debug", "info", "warning", "error"]
        test_messages = [
            "Application started successfully",
            "Processing user request",
            "Database connection established",
            "Cache miss for key: user_123",
            "Authentication successful for user@example.com",
            "File upload completed: document.pdf",
            "API call to external service succeeded",
            "Background job completed",
            "Memory usage is within normal limits",
            "Scheduled maintenance task executed",
            "Invalid input received from client",
            "Rate limit exceeded for IP 192.168.1.100",
            "Database query took longer than expected",
            "External API returned error response",
            "Configuration file reloaded",
            "New user registration completed",
            "Email notification sent successfully",
            "Cache cleared for performance optimization",
            "SSL certificate renewed automatically",
            "Backup process completed successfully"
        ]

        import random

        logs = []
        for i in range(count):
            level = random.choice(log_levels)
            message = random.choice(test_messages)
            timestamp = datetime.now().isoformat()

            logs.append({
                "service": service,
                "level": level,
                "message": f"[{i+1}] {message}",
                "timestamp": timestamp,
                "context": {
                    "test_id": f"test_{i+1}",
                    "generated": True
                }
            })

        console.print(f"📝 Generated {len(logs)} test log entries")

        url = f"{clients.log_collector_url()}/logs/batch"
        rx = await clients.post_json(url, {"logs": logs})

        if rx.get("status") == "ok":
            console.print("[green]✅ Test logs submitted successfully[/green]")
            print_kv(console, "Service", service)
            print_kv(console, "Generated", count)
            print_kv(console, "Total log count", rx.get("total_count", "unknown"))
        else:
            console.print(f"[red]❌ Test log submission failed: {rx}[/red]")

    # ============================================================================
    # LOG RETRIEVAL ENDPOINTS
    # ============================================================================

    async def view_logs():
        """View logs with optional filtering."""
        console.print("[bold green]📋 View Log Entries[/bold green]")

        # Filtering options
        service_filter = Prompt.ask("Service filter (optional)", default="")
        level_filter = Prompt.ask("Level filter (optional)", default="")
        limit = Prompt.ask("Maximum entries to retrieve", default="50")

        params = {"limit": int(limit)}
        if service_filter.strip():
            params["service"] = service_filter
        if level_filter.strip():
            params["level"] = level_filter

        url = f"{clients.log_collector_url()}/logs"
        rx = await clients.get_json(url, params=params)

        if rx.get("logs"):
            logs = rx["logs"]
            console.print(f"\n[bold green]📝 Retrieved {len(logs)} log entries[/bold green]")

            from rich.table import Table
            table = Table(title="Log Entries")
            table.add_column("Timestamp", style="cyan", max_width=20)
            table.add_column("Service", style="white", max_width=15)
            table.add_column("Level", style="yellow", max_width=8)
            table.add_column("Message", style="white", max_width=50)

            for log in logs:
                timestamp = log.get("timestamp", "")[:19]  # Truncate to fit
                service = log.get("service", "")[:15]
                level = log.get("level", "").upper()[:8]

                # Color code log levels
                if level == "ERROR":
                    level_style = "red"
                elif level == "WARNING":
                    level_style = "yellow"
                elif level == "INFO":
                    level_style = "green"
                else:
                    level_style = "white"

                table.add_column("Level", style=level_style, max_width=8)
                message = log.get("message", "")[:50]

                table.add_row(timestamp, service, level, message)

            console.print(table)

            # Show summary
            level_counts = {}
            for log in logs:
                level = log.get("level", "unknown")
                level_counts[level] = level_counts.get(level, 0) + 1

            console.print("
[bold blue]📊 Summary by Level:[/bold blue]"            for level, count in level_counts.items():
                console.print(f"  {level.upper()}: {count}")

        else:
            console.print("[yellow]⚠️  No logs found matching criteria[/yellow]")

    async def view_log_stats():
        """View log statistics and analytics."""
        console.print("[bold purple]📊 Log Statistics[/bold purple]")

        url = f"{clients.log_collector_url()}/stats"
        rx = await clients.get_json(url)

        if rx.get("stats"):
            stats = rx["stats"]
            console.print("[green]✅ Log statistics retrieved[/green]")

            print_kv(console, "Total logs", stats.get("total_logs", 0))
            print_kv(console, "Unique services", stats.get("unique_services", 0))
            print_kv(console, "Log levels", stats.get("log_levels", 0))

            # Level distribution
            if stats.get("level_distribution"):
                console.print("
[bold blue]📈 Level Distribution:[/bold blue]"                level_dist = stats["level_distribution"]
                for level, count in level_dist.items():
                    percentage = (count / stats["total_logs"]) * 100 if stats["total_logs"] > 0 else 0
                    console.print(f"  {level.upper()}: {count} ({percentage:.1f}%)")

            # Service distribution
            if stats.get("service_distribution"):
                console.print("
[bold blue]🏢 Service Distribution:[/bold blue]"                service_dist = stats["service_distribution"]
                for service, count in list(service_dist.items())[:10]:  # Show top 10
                    percentage = (count / stats["total_logs"]) * 100 if stats["total_logs"] > 0 else 0
                    console.print(f"  {service}: {count} ({percentage:.1f}%)")

                if len(service_dist) > 10:
                    console.print(f"  ... and {len(service_dist) - 10} more services")

            # Time-based stats
            if stats.get("time_range"):
                time_range = stats["time_range"]
                console.print("
[bold blue]⏰ Time Range:[/bold blue]"                print_kv(console, "Earliest", time_range.get("earliest", "unknown"))
                print_kv(console, "Latest", time_range.get("latest", "unknown"))

            # Recent activity
            if stats.get("recent_activity"):
                recent = stats["recent_activity"]
                console.print("
[bold blue]📅 Recent Activity:[/bold blue]"                print_kv(console, "Last hour", recent.get("last_hour", 0))
                print_kv(console, "Last 24 hours", recent.get("last_24_hours", 0))
                print_kv(console, "Last 7 days", recent.get("last_7_days", 0))

        else:
            console.print("[yellow]⚠️  No statistics available[/yellow]")

    # ============================================================================
    # MONITORING AND ALERTS
    # ============================================================================

    async def monitor_logs():
        """Monitor logs in real-time."""
        console.print("[bold cyan]👀 Real-time Log Monitoring[/bold cyan]")
        console.print("Press Ctrl+C to stop monitoring")

        service_filter = Prompt.ask("Service filter (optional)", default="")
        level_filter = Prompt.ask("Level filter (optional)", default="")

        last_count = 0

        try:
            while True:
                params = {"limit": 10}
                if service_filter.strip():
                    params["service"] = service_filter
                if level_filter.strip():
                    params["level"] = level_filter

                url = f"{clients.log_collector_url()}/logs"
                rx = await clients.get_json(url, params=params)

                if rx.get("logs"):
                    logs = rx["logs"]
                    new_logs = logs[:10]  # Show latest 10

                    if len(new_logs) > last_count or last_count == 0:
                        console.print(f"\n[bold green]📝 Latest {len(new_logs)} log entries:[/bold green]")

                        for log in new_logs:
                            timestamp = log.get("timestamp", "")[:19]
                            service = log.get("service", "")
                            level = log.get("level", "").upper()
                            message = log.get("message", "")

                            # Color code by level
                            if level == "ERROR":
                                level_color = "[red]"
                            elif level == "WARNING":
                                level_color = "[yellow]"
                            elif level == "INFO":
                                level_color = "[green]"
                            else:
                                level_color = "[white]"

                            console.print(f"{timestamp} {level_color}{level}[/{level_color}] [{service}] {message}")

                        last_count = len(new_logs)

                import asyncio
                await asyncio.sleep(5)  # Check every 5 seconds

        except KeyboardInterrupt:
            console.print("\n[blue]🛑 Monitoring stopped[/blue]")

    async def setup_log_alerts():
        """Set up log-based alerts (conceptual - would need backend support)."""
        console.print("[bold orange]🚨 Log Alert Configuration[/bold orange]")
        console.print("This is a conceptual feature for setting up alerts based on log patterns")

        alert_name = Prompt.ask("Alert name")
        service_pattern = Prompt.ask("Service pattern (regex)", default=".*")
        level_pattern = Prompt.ask("Level pattern", default="ERROR|WARNING")
        message_pattern = Prompt.ask("Message pattern (regex)", default=".*")
        threshold = Prompt.ask("Alert threshold (count per minute)", default="5")

        alert_config = {
            "name": alert_name,
            "service_pattern": service_pattern,
            "level_pattern": level_pattern,
            "message_pattern": message_pattern,
            "threshold": int(threshold),
            "time_window_minutes": 1
        }

        console.print("[green]✅ Alert configuration created (would be saved to backend)[/green]")
        print_kv(console, "Alert Name", alert_config["name"])
        print_kv(console, "Service Pattern", alert_config["service_pattern"])
        print_kv(console, "Level Pattern", alert_config["level_pattern"])
        print_kv(console, "Threshold", f"{alert_config['threshold']} per minute")

    # ============================================================================
    # TESTING AND DIAGNOSTICS
    # ============================================================================

    async def test_log_collector_health():
        """Test log collector service health."""
        url = f"{clients.log_collector_url()}/health"
        rx = await clients.get_json(url)

        if rx.get("status") == "healthy":
            console.print("[green]✅ Log Collector is healthy[/green]")
            print_kv(console, "Service", rx.get("service", "unknown"))
            print_kv(console, "Version", rx.get("version", "unknown"))
            print_kv(console, "Current log count", rx.get("count", 0))
        else:
            console.print("[red]❌ Log Collector health check failed[/red]")
            print_kv(console, "Response", rx)

    async def benchmark_log_operations():
        """Benchmark log submission and retrieval performance."""
        console.print("[bold blue]⚡ Log Operations Benchmark[/bold blue]")

        # Test data
        test_logs = [
            {"service": "benchmark", "level": "info", "message": f"Benchmark log {i}"}
            for i in range(10)
        ]

        import time

        # Benchmark submission
        console.print("📤 Testing log submission performance...")
        submit_times = []

        for log in test_logs:
            start_time = time.time()
            url = f"{clients.log_collector_url()}/logs"
            await clients.post_json(url, log)
            end_time = time.time()
            submit_times.append(end_time - start_time)

        submit_avg = sum(submit_times) / len(submit_times) if submit_times else 0

        # Benchmark retrieval
        console.print("📥 Testing log retrieval performance...")
        retrieve_times = []

        for _ in range(5):
            start_time = time.time()
            url = f"{clients.log_collector_url()}/logs"
            await clients.get_json(url, params={"limit": 50})
            end_time = time.time()
            retrieve_times.append(end_time - start_time)

        retrieve_avg = sum(retrieve_times) / len(retrieve_times) if retrieve_times else 0

        # Display results
        console.print("
[bold green]📊 Benchmark Results[/bold green]"        console.print("Submission Performance:"        console.print(f"  Average time: {submit_avg:.3f}s per log")
        console.print(f"  Total logs submitted: {len(test_logs)}")
        console.print(f"  Throughput: {len(test_logs)/sum(submit_times):.1f} logs/second")

        console.print("
Retrieval Performance:"        console.print(f"  Average time: {retrieve_avg:.3f}s per query")
        console.print(f"  Records per query: 50")
        console.print(f"  Throughput: {50/retrieve_avg:.1f} records/second")

    # ============================================================================
    # ORGANIZE ACTIONS BY CATEGORY
    # ============================================================================

    return [
        # Log Submission
        ("📝 Submit single log", submit_log),
        ("📦 Submit batch logs", submit_batch_logs),
        ("🧪 Generate test logs", generate_test_logs),

        # Log Retrieval
        ("📋 View logs", view_logs),
        ("📊 View statistics", view_log_stats),

        # Monitoring
        ("👀 Monitor logs real-time", monitor_logs),
        ("🚨 Setup alerts (conceptual)", setup_log_alerts),

        # Testing & Diagnostics
        ("🩺 Service health check", test_log_collector_health),
        ("⚡ Benchmark operations", benchmark_log_operations),
    ]
