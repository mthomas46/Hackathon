"""Memory Agent Manager module for CLI service.

Provides power-user operations for memory agent including
operational context storage, event summaries, and memory management.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
import json
import os
from datetime import datetime, timezone

from ...base.base_manager import BaseManager


class MemoryAgentManager(BaseManager):
    """Manager for memory agent power-user operations."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

    async def memory_agent_menu(self):
        """Main memory agent management menu."""
        await self.run_menu_loop("Memory Agent Management")

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return the main menu items for memory agent operations."""
        return [
            ("1", "Memory Item Management (Store, List, Search, Delete)"),
            ("2", "Memory Statistics & Monitoring"),
            ("3", "Memory Cleanup & Maintenance"),
            ("4", "Memory Analytics & Reporting"),
            ("5", "Memory Configuration Management")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle a menu choice. Return True to continue, False to exit."""
        if choice == "1":
            await self.memory_item_management_menu()
        elif choice == "2":
            await self.memory_statistics_menu()
        elif choice == "3":
            await self.memory_cleanup_menu()
        elif choice == "4":
            await self.memory_analytics_menu()
        elif choice == "5":
            await self.memory_config_menu()
        else:
            self.display.show_error("Invalid option. Please try again.")
        return True

    async def memory_item_management_menu(self):
        """Memory item management submenu."""
        while True:
            menu = create_menu_table("Memory Item Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Store Memory Item"),
                ("2", "List Memory Items"),
                ("3", "Search Memory by Key/Type"),
                ("4", "View Memory Item Details"),
                ("5", "Bulk Memory Operations"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.store_memory_item()
            elif choice == "2":
                await self.list_memory_items()
            elif choice == "3":
                await self.search_memory_items()
            elif choice == "4":
                await self.view_memory_item_details()
            elif choice == "5":
                await self.bulk_memory_operations()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def store_memory_item(self):
        """Store a new memory item."""
        try:
            # Get memory item details
            memory_type = Prompt.ask("[bold cyan]Memory type[/bold cyan]", default="operation")
            memory_key = Prompt.ask("[bold cyan]Memory key (correlation ID, doc ID, etc.)[/bold cyan]")
            summary = Prompt.ask("[bold cyan]Summary[/bold cyan]")

            # Get data as JSON
            data_input = Prompt.ask("[bold cyan]Data (JSON)[/bold cyan]", default="{}")
            try:
                data = json.loads(data_input)
            except json.JSONDecodeError:
                self.console.print("[red]Invalid JSON for data. Using empty dict.[/red]")
                data = {}

            # Create memory item
            memory_item = {
                "id": f"cli-memory-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                "type": memory_type,
                "key": memory_key,
                "summary": summary,
                "data": data
            }

            # Confirm and store
            self.console.print("[yellow]Memory Item to Store:[/yellow]")
            self.console.print(json.dumps(memory_item, indent=2))

            confirm = Confirm.ask("[bold cyan]Store this memory item?[/bold cyan]", default=True)

            if confirm:
                request_data = {"item": memory_item}
                response = await self.clients.post_json("memory-agent/memory/put", request_data)

                if response.get("data"):
                    self.console.print("[green]✅ Memory item stored successfully[/green]")
                    if response.get("data", {}).get("count"):
                        self.console.print(f"[green]Total memory items: {response['data']['count']}[/green]")
                else:
                    self.console.print("[red]❌ Failed to store memory item[/red]")

        except Exception as e:
            self.console.print(f"[red]Error storing memory item: {e}[/red]")

    async def list_memory_items(self):
        """List memory items with filtering."""
        try:
            memory_type = Prompt.ask("[bold cyan]Filter by type (optional)[/bold cyan]", default="")
            key_filter = Prompt.ask("[bold cyan]Filter by key (optional)[/bold cyan]", default="")
            limit = int(Prompt.ask("[bold cyan]Limit[/bold cyan]", default="50"))

            params = {}
            if memory_type:
                params["type"] = memory_type
            if key_filter:
                params["key"] = key_filter
            params["limit"] = limit

            response = await self.clients.get_json("memory-agent/memory/list", params=params)

            if response.get("data"):
                items = response["data"].get("items", [])
                await self.display_memory_items(items, f"Memory Items ({len(items)} found)")
            else:
                self.console.print("[yellow]No memory items found or error retrieving items[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error listing memory items: {e}[/red]")

    async def search_memory_items(self):
        """Search memory items by key or type."""
        try:
            search_term = Prompt.ask("[bold cyan]Search term[/bold cyan]")
            search_type = Prompt.ask("[bold cyan]Search in (key/type/both)[/bold cyan]", default="both")

            # Get all items and filter client-side
            response = await self.clients.get_json("memory-agent/memory/list", params={"limit": 1000})

            if response.get("data"):
                all_items = response["data"].get("items", [])
                filtered_items = []

                for item in all_items:
                    match = False
                    if search_type in ["key", "both"] and search_term.lower() in (item.get("key", "") or "").lower():
                        match = True
                    if search_type in ["type", "both"] and search_term.lower() in (item.get("type", "") or "").lower():
                        match = True

                    if match:
                        filtered_items.append(item)

                await self.display_memory_items(filtered_items, f"Search Results for '{search_term}' ({len(filtered_items)} found)")
            else:
                self.console.print("[yellow]No memory items found[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error searching memory items: {e}[/red]")

    async def view_memory_item_details(self):
        """View detailed information about a specific memory item."""
        try:
            # First list items to choose from
            response = await self.clients.get_json("memory-agent/memory/list", params={"limit": 20})

            if not response.get("data") or not response["data"].get("items"):
                self.console.print("[yellow]No memory items available[/yellow]")
                return

            items = response["data"]["items"]

            # Display numbered list
            table = Table(title="Available Memory Items")
            table.add_column("Index", style="cyan", justify="right")
            table.add_column("Type", style="green")
            table.add_column("Key", style="yellow")
            table.add_column("Summary", style="white")
            table.add_column("Created", style="blue")

            for i, item in enumerate(items, 1):
                created = item.get("created_at", "")
                if created and len(created) > 19:
                    created = created[:19]  # Truncate timestamp

                table.add_row(
                    str(i),
                    item.get("type", "unknown"),
                    item.get("key", "N/A")[:30] + "..." if len(item.get("key", "")) > 30 else item.get("key", "N/A"),
                    item.get("summary", "No summary")[:40] + "..." if len(item.get("summary", "")) > 40 else item.get("summary", "No summary"),
                    created
                )

            self.console.print(table)

            if not items:
                return

            choice = Prompt.ask("[bold cyan]Enter item index to view details[/bold cyan]", default="1")

            try:
                index = int(choice) - 1
                if 0 <= index < len(items):
                    item = items[index]
                    await self.display_memory_item_detail(item)
                else:
                    self.console.print("[red]Invalid index[/red]")
            except ValueError:
                self.console.print("[red]Invalid input[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing memory item details: {e}[/red]")

    async def display_memory_item_detail(self, item: Dict[str, Any]):
        """Display detailed view of a memory item."""
        content = f"""
[bold]Memory Item Details[/bold]

[bold blue]ID:[/bold blue] {item.get('id', 'N/A')}
[bold blue]Type:[/bold blue] {item.get('type', 'N/A')}
[bold blue]Key:[/bold blue] {item.get('key', 'N/A')}
[bold blue]Summary:[/bold blue] {item.get('summary', 'N/A')}

[bold blue]Created:[/bold blue] {item.get('created_at', 'N/A')}
[bold blue]Expires:[/bold blue] {item.get('expires_at', 'N/A')}

[bold magenta]Data:[/bold magenta]
{json.dumps(item.get('data', {}), indent=2)}
"""

        print_panel(self.console, content, border_style="blue")

    async def bulk_memory_operations(self):
        """Perform bulk memory operations."""
        while True:
            menu = create_menu_table("Bulk Memory Operations", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Bulk Store from JSON File"),
                ("2", "Bulk Store from CSV"),
                ("3", "Export Memory Items"),
                ("4", "Bulk Delete by Type"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.bulk_store_from_json()
            elif choice == "2":
                await self.bulk_store_from_csv()
            elif choice == "3":
                await self.export_memory_items()
            elif choice == "4":
                await self.bulk_delete_by_type()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def bulk_store_from_json(self):
        """Bulk store memory items from JSON file."""
        try:
            file_path = Prompt.ask("[bold cyan]JSON file path[/bold cyan]")

            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return

            with open(file_path, 'r') as f:
                data = json.load(f)

            # Handle both single item and array of items
            items = data if isinstance(data, list) else [data]

            self.console.print(f"[yellow]Found {len(items)} items to store[/yellow]")

            confirm = Confirm.ask(f"[bold cyan]Store {len(items)} memory items?[/bold cyan]", default=True)

            if confirm:
                stored = 0
                failed = 0

                for item in items:
                    try:
                        # Ensure required fields
                        if "id" not in item:
                            item["id"] = f"bulk-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{stored}"
                        if "type" not in item:
                            item["type"] = "bulk_import"

                        request_data = {"item": item}
                        response = await self.clients.post_json("memory-agent/memory/put", request_data)

                        if response.get("data"):
                            stored += 1
                        else:
                            failed += 1

                    except Exception as e:
                        self.console.print(f"[red]Failed to store item {item.get('id', 'unknown')}: {e}[/red]")
                        failed += 1

                self.console.print(f"[green]✅ Bulk store complete: {stored} stored, {failed} failed[/green]")

        except Exception as e:
            self.console.print(f"[red]Error in bulk JSON store: {e}[/red]")

    async def bulk_store_from_csv(self):
        """Bulk store memory items from CSV file."""
        try:
            file_path = Prompt.ask("[bold cyan]CSV file path[/bold cyan]")
            memory_type = Prompt.ask("[bold cyan]Memory type for all items[/bold cyan]", default="csv_import")

            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return

            import csv
            items = []

            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    item = {
                        "id": f"csv-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{len(items)}",
                        "type": memory_type,
                        "data": dict(row)
                    }
                    # Use first column as key if available
                    if row:
                        first_key = list(row.keys())[0]
                        item["key"] = row[first_key]
                        item["summary"] = f"CSV import: {row.get(first_key, 'unknown')}"

                    items.append(item)

            self.console.print(f"[yellow]Parsed {len(items)} items from CSV[/yellow]")

            confirm = Confirm.ask(f"[bold cyan]Store {len(items)} memory items?[/bold cyan]", default=True)

            if confirm:
                stored = 0
                failed = 0

                for item in items:
                    try:
                        request_data = {"item": item}
                        response = await self.clients.post_json("memory-agent/memory/put", request_data)

                        if response.get("data"):
                            stored += 1
                        else:
                            failed += 1

                    except Exception as e:
                        failed += 1

                self.console.print(f"[green]✅ CSV bulk store complete: {stored} stored, {failed} failed[/green]")

        except Exception as e:
            self.console.print(f"[red]Error in bulk CSV store: {e}[/red]")

    async def export_memory_items(self):
        """Export memory items to file."""
        try:
            export_format = Prompt.ask("[bold cyan]Export format (json/csv)[/bold cyan]", default="json")
            file_path = Prompt.ask("[bold cyan]Export file path[/bold cyan]")
            memory_type = Prompt.ask("[bold cyan]Filter by type (optional)[/bold cyan]", default="")

            # Get items
            params = {"limit": 10000}  # Large limit for export
            if memory_type:
                params["type"] = memory_type

            response = await self.clients.get_json("memory-agent/memory/list", params=params)

            if not response.get("data") or not response["data"].get("items"):
                self.console.print("[yellow]No items to export[/yellow]")
                return

            items = response["data"]["items"]

            if export_format.lower() == "json":
                with open(file_path, 'w') as f:
                    json.dump(items, f, indent=2, default=str)
                self.console.print(f"[green]✅ Exported {len(items)} items to {file_path} (JSON)[/green]")

            elif export_format.lower() == "csv":
                if not items:
                    self.console.print("[yellow]No items to export[/yellow]")
                    return

                # Get all unique keys from data dictionaries
                fieldnames = set()
                for item in items:
                    fieldnames.update(item.keys())
                    fieldnames.update(item.get("data", {}).keys())

                fieldnames = list(fieldnames)

                import csv
                with open(file_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for item in items:
                        row = dict(item)
                        # Flatten data dict
                        data = row.pop("data", {})
                        row.update(data)
                        # Convert complex types to strings
                        for key, value in row.items():
                            if not isinstance(value, (str, int, float, bool)):
                                row[key] = str(value)

                        writer.writerow(row)

                self.console.print(f"[green]✅ Exported {len(items)} items to {file_path} (CSV)[/green]")

            else:
                self.console.print("[red]Unsupported export format. Use 'json' or 'csv'[/red]")

        except Exception as e:
            self.console.print(f"[red]Error exporting memory items: {e}[/red]")

    async def bulk_delete_by_type(self):
        """Bulk delete memory items by type."""
        try:
            memory_type = Prompt.ask("[bold cyan]Memory type to delete[/bold cyan]")

            # This would require a delete endpoint in the memory agent
            # For now, show placeholder
            self.console.print("[yellow]Bulk delete functionality requires memory agent API enhancement[/yellow]")
            self.console.print("[yellow]This would delete all items of type: {memory_type}[/yellow]")

            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in bulk delete: {e}[/red]")

    async def display_memory_items(self, items: List[Dict[str, Any]], title: str):
        """Display memory items in a table format."""
        if not items:
            self.console.print(f"[yellow]{title}: No items found[/yellow]")
            return

        table = Table(title=title)
        table.add_column("Type", style="green")
        table.add_column("Key", style="yellow")
        table.add_column("Summary", style="white")
        table.add_column("Created", style="blue")
        table.add_column("Expires", style="red")

        for item in items[:50]:  # Limit display to 50 items
            created = item.get("created_at", "")
            if created and len(created) > 19:
                created = created[:19]

            expires = item.get("expires_at", "")
            if expires and len(expires) > 19:
                expires = expires[:19]

            table.add_row(
                item.get("type", "unknown"),
                item.get("key", "N/A")[:30] + "..." if len(item.get("key", "")) > 30 else item.get("key", "N/A"),
                item.get("summary", "No summary")[:40] + "..." if len(item.get("summary", "")) > 40 else item.get("summary", "No summary"),
                created,
                expires or "Never"
            )

        self.console.print(table)

        if len(items) > 50:
            self.console.print(f"[yellow]... and {len(items) - 50} more items[/yellow]")

    async def memory_statistics_menu(self):
        """Memory statistics and monitoring submenu."""
        while True:
            menu = create_menu_table("Memory Statistics & Monitoring", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Memory Health & Stats"),
                ("2", "Memory Usage Analysis"),
                ("3", "Memory Type Distribution"),
                ("4", "Memory Expiration Monitoring"),
                ("5", "Memory Performance Metrics"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_memory_health_stats()
            elif choice == "2":
                await self.memory_usage_analysis()
            elif choice == "3":
                await self.memory_type_distribution()
            elif choice == "4":
                await self.memory_expiration_monitoring()
            elif choice == "5":
                await self.memory_performance_metrics()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_memory_health_stats(self):
        """View memory agent health and statistics."""
        try:
            response = await self.clients.get_json("memory-agent/health")

            if response:
                content = f"""
[bold]Memory Agent Health & Statistics[/bold]

[bold blue]Status:[/bold blue] {response.get('status', 'unknown')}
[bold blue]Service:[/bold blue] {response.get('service', 'N/A')}
[bold blue]Version:[/bold blue] {response.get('version', 'N/A')}

[bold green]Memory Metrics:[/bold green]
• Memory Count: {response.get('memory_count', 0)}
• Memory Capacity: {response.get('memory_capacity', 0)}
• Memory Usage: {response.get('memory_usage_percent', 0)}%
• TTL Seconds: {response.get('ttl_seconds', 0)}

[bold cyan]Description:[/bold cyan] {response.get('description', 'N/A')}
"""

                print_panel(self.console, content, border_style="green" if response.get('status') == 'healthy' else "yellow")
            else:
                self.console.print("[red]Failed to retrieve memory health stats[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing memory health stats: {e}[/red]")

    async def memory_usage_analysis(self):
        """Analyze memory usage patterns."""
        try:
            # Get all memory items for analysis
            response = await self.clients.get_json("memory-agent/memory/list", params={"limit": 10000})

            if not response.get("data"):
                self.console.print("[yellow]No memory data available for analysis[/yellow]")
                return

            items = response["data"].get("items", [])

            # Analyze by type
            type_counts = {}
            for item in items:
                item_type = item.get("type", "unknown")
                type_counts[item_type] = type_counts.get(item_type, 0) + 1

            # Analyze data sizes
            data_sizes = [len(json.dumps(item.get("data", {}))) for item in items]

            content = f"""
[bold]Memory Usage Analysis[/bold]

[bold blue]Total Items:[/bold blue] {len(items)}

[bold green]Items by Type:[/bold green]
"""

            for item_type, count in sorted(type_counts.items()):
                percentage = (count / len(items)) * 100 if items else 0
                content += f"• {item_type}: {count} items ({percentage:.1f}%)\n"

            if data_sizes:
                avg_size = sum(data_sizes) / len(data_sizes)
                max_size = max(data_sizes)
                min_size = min(data_sizes)

                content += f"""
[bold yellow]Data Size Statistics:[/bold yellow]
• Average: {avg_size:.0f} bytes
• Maximum: {max_size} bytes
• Minimum: {min_size} bytes
"""

            print_panel(self.console, content, border_style="blue")

        except Exception as e:
            self.console.print(f"[red]Error analyzing memory usage: {e}[/red]")

    async def memory_type_distribution(self):
        """Show memory type distribution chart."""
        try:
            response = await self.clients.get_json("memory-agent/memory/list", params={"limit": 10000})

            if not response.get("data"):
                self.console.print("[yellow]No memory data available[/yellow]")
                return

            items = response["data"].get("items", [])

            type_counts = {}
            for item in items:
                item_type = item.get("type", "unknown")
                type_counts[item_type] = type_counts.get(item_type, 0) + 1

            # Display as table
            table = Table(title="Memory Type Distribution")
            table.add_column("Type", style="green")
            table.add_column("Count", style="yellow", justify="right")
            table.add_column("Percentage", style="cyan", justify="right")

            for item_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(items)) * 100 if items else 0
                table.add_row(item_type, str(count), f"{percentage:.1f}%")

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error showing type distribution: {e}[/red]")

    async def memory_expiration_monitoring(self):
        """Monitor memory item expiration."""
        try:
            response = await self.clients.get_json("memory-agent/memory/list", params={"limit": 10000})

            if not response.get("data"):
                self.console.print("[yellow]No memory data available[/yellow]")
                return

            items = response["data"].get("items", [])
            now = datetime.now(timezone.utc)

            expired = []
            expiring_soon = []
            permanent = []

            for item in items:
                expires_at = item.get("expires_at")
                if expires_at:
                    try:
                        # Parse datetime
                        if isinstance(expires_at, str):
                            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        else:
                            expires_dt = expires_at

                        if expires_dt < now:
                            expired.append(item)
                        elif (expires_dt - now).total_seconds() < 3600:  # Expiring in < 1 hour
                            expiring_soon.append(item)
                    except:
                        pass  # Skip invalid dates
                else:
                    permanent.append(item)

            content = f"""
[bold]Memory Expiration Monitoring[/bold]

[bold red]Expired Items:[/bold red] {len(expired)}
[bold yellow]Expiring Soon (< 1 hour):[/bold yellow] {len(expiring_soon)}
[bold green]Permanent Items:[/bold green] {len(permanent)}
[bold blue]Total Items:[/bold blue] {len(items)}
"""

            if expired:
                content += f"\n[bold red]Expired Items (showing first 5):[/bold red]\n"
                for item in expired[:5]:
                    content += f"• {item.get('type', 'unknown')}: {item.get('key', 'N/A')}\n"

            if expiring_soon:
                content += f"\n[bold yellow]Expiring Soon (showing first 5):[/bold yellow]\n"
                for item in expiring_soon[:5]:
                    expires = item.get("expires_at", "")
                    content += f"• {item.get('type', 'unknown')}: {item.get('key', 'N/A')} (expires: {expires})\n"

            print_panel(self.console, content, border_style="blue")

        except Exception as e:
            self.console.print(f"[red]Error monitoring expiration: {e}[/red]")

    async def memory_performance_metrics(self):
        """Show memory performance metrics."""
        try:
            self.console.print("[yellow]Memory performance metrics would show response times, throughput, etc.[/yellow]")
            self.console.print("[yellow]This requires additional memory agent API endpoints for metrics[/yellow]")

            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error showing performance metrics: {e}[/red]")

    async def memory_cleanup_menu(self):
        """Memory cleanup and maintenance submenu."""
        while True:
            menu = create_menu_table("Memory Cleanup & Maintenance", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Cleanup Expired Items"),
                ("2", "Compact Memory Storage"),
                ("3", "Memory Fragmentation Analysis"),
                ("4", "Memory Backup & Restore"),
                ("5", "Memory Integrity Check"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.cleanup_expired_items()
            elif choice == "2":
                await self.compact_memory_storage()
            elif choice == "3":
                await self.memory_fragmentation_analysis()
            elif choice == "4":
                await self.memory_backup_restore()
            elif choice == "5":
                await self.memory_integrity_check()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def cleanup_expired_items(self):
        """Clean up expired memory items."""
        try:
            # This would require a cleanup endpoint in memory agent
            self.console.print("[yellow]Expired item cleanup would remove all expired memory items[/yellow]")
            self.console.print("[yellow]This requires memory agent API enhancement[/yellow]")

            confirm = Confirm.ask("[bold cyan]Proceed with cleanup simulation?[/bold cyan]", default=False)

            if confirm:
                # Simulate cleanup by showing what would be cleaned
                response = await self.clients.get_json("memory-agent/memory/list", params={"limit": 10000})

                if response.get("data"):
                    items = response["data"].get("items", [])
                    now = datetime.now(timezone.utc)

                    expired_count = 0
                    for item in items:
                        expires_at = item.get("expires_at")
                        if expires_at:
                            try:
                                if isinstance(expires_at, str):
                                    expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                                else:
                                    expires_dt = expires_at

                                if expires_dt < now:
                                    expired_count += 1
                            except:
                                pass

                    self.console.print(f"[green]Cleanup simulation: {expired_count} expired items would be removed[/green]")

        except Exception as e:
            self.console.print(f"[red]Error in cleanup: {e}[/red]")

    async def compact_memory_storage(self):
        """Compact memory storage."""
        try:
            self.console.print("[yellow]Memory compaction would optimize storage efficiency[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in compaction: {e}[/red]")

    async def memory_fragmentation_analysis(self):
        """Analyze memory fragmentation."""
        try:
            self.console.print("[yellow]Fragmentation analysis would show storage efficiency metrics[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in fragmentation analysis: {e}[/red]")

    async def memory_backup_restore(self):
        """Memory backup and restore operations."""
        try:
            self.console.print("[yellow]Memory backup/restore would provide data persistence across restarts[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in backup/restore: {e}[/red]")

    async def memory_integrity_check(self):
        """Check memory integrity."""
        try:
            self.console.print("[yellow]Integrity check would validate memory item consistency[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in integrity check: {e}[/red]")

    async def memory_analytics_menu(self):
        """Memory analytics and reporting submenu."""
        while True:
            menu = create_menu_table("Memory Analytics & Reporting", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Memory Trends Analysis"),
                ("2", "Memory Usage Forecasting"),
                ("3", "Memory Pattern Recognition"),
                ("4", "Memory Correlation Analysis"),
                ("5", "Generate Memory Report"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.memory_trends_analysis()
            elif choice == "2":
                await self.memory_usage_forecasting()
            elif choice == "3":
                await self.memory_pattern_recognition()
            elif choice == "4":
                await self.memory_correlation_analysis()
            elif choice == "5":
                await self.generate_memory_report()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def memory_trends_analysis(self):
        """Analyze memory usage trends."""
        try:
            self.console.print("[yellow]Memory trends analysis would show usage patterns over time[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in trends analysis: {e}[/red]")

    async def memory_usage_forecasting(self):
        """Forecast memory usage."""
        try:
            self.console.print("[yellow]Usage forecasting would predict future memory needs[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in forecasting: {e}[/red]")

    async def memory_pattern_recognition(self):
        """Recognize patterns in memory usage."""
        try:
            self.console.print("[yellow]Pattern recognition would identify usage patterns and anomalies[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in pattern recognition: {e}[/red]")

    async def memory_correlation_analysis(self):
        """Analyze correlations in memory data."""
        try:
            self.console.print("[yellow]Correlation analysis would find relationships between memory items[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in correlation analysis: {e}[/red]")

    async def generate_memory_report(self):
        """Generate comprehensive memory report."""
        try:
            self.console.print("[yellow]Memory report generation would create detailed analytics reports[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating report: {e}[/red]")

    async def memory_config_menu(self):
        """Memory configuration management submenu."""
        while True:
            menu = create_menu_table("Memory Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Memory Configuration"),
                ("2", "Configure TTL Settings"),
                ("3", "Set Memory Capacity Limits"),
                ("4", "Configure Redis Integration"),
                ("5", "Memory Agent Settings"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_memory_config()
            elif choice == "2":
                await self.configure_ttl_settings()
            elif choice == "3":
                await self.set_capacity_limits()
            elif choice == "4":
                await self.configure_redis_integration()
            elif choice == "5":
                await self.memory_agent_settings()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_memory_config(self):
        """View current memory configuration."""
        try:
            self.console.print("[yellow]Memory configuration would show current settings[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing config: {e}[/red]")

    async def configure_ttl_settings(self):
        """Configure TTL settings."""
        try:
            self.console.print("[yellow]TTL configuration would set default expiration times[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring TTL: {e}[/red]")

    async def set_capacity_limits(self):
        """Set memory capacity limits."""
        try:
            self.console.print("[yellow]Capacity limits would configure maximum memory usage[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error setting capacity: {e}[/red]")

    async def configure_redis_integration(self):
        """Configure Redis integration."""
        try:
            self.console.print("[yellow]Redis configuration would set connection and pub/sub settings[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring Redis: {e}[/red]")

    async def memory_agent_settings(self):
        """Configure memory agent settings."""
        try:
            self.console.print("[yellow]Memory agent settings would configure general behavior[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring agent: {e}[/red]")

    async def store_memory_from_cli(self, memory_request: Dict[str, Any]):
        """Store memory item for CLI usage (no interactive prompts)."""
        try:
            with self.console.status(f"[bold green]Storing memory item...[/bold green]") as status:
                response = await self.clients.post_json("memory-agent/memory/put", memory_request)

            if response.get("data"):
                self.console.print("[green]✅ Memory item stored successfully[/green]")
            else:
                self.console.print("[red]❌ Failed to store memory item[/red]")

        except Exception as e:
            self.console.print(f"[red]Error storing memory item: {e}[/red]")
