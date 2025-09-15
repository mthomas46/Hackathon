"""Discovery Agent Manager module for CLI service.

Provides power-user operations for discovery agent including
API discovery, OpenAPI parsing, service registration, and endpoint management.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
import json
import os

from .shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class DiscoveryAgentManager:
    """Manager for discovery agent power-user operations."""

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients

    async def discovery_agent_menu(self):
        """Main discovery agent menu."""
        while True:
            menu = create_menu_table("Discovery Agent Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Service Discovery (OpenAPI parsing and endpoint extraction)"),
                ("2", "Bulk Discovery Operations"),
                ("3", "Discovery History and Results"),
                ("4", "Service Registration Management"),
                ("5", "Discovery Validation and Testing"),
                ("6", "Discovery Agent Configuration"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.service_discovery_menu()
            elif choice == "2":
                await self.bulk_discovery_menu()
            elif choice == "3":
                await self.discovery_history_menu()
            elif choice == "4":
                await self.service_registration_menu()
            elif choice == "5":
                await self.discovery_validation_menu()
            elif choice == "6":
                await self.discovery_config_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def service_discovery_menu(self):
        """Service discovery submenu."""
        while True:
            menu = create_menu_table("Service Discovery", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Discover from Inline OpenAPI Spec"),
                ("2", "Discover from OpenAPI URL"),
                ("3", "Discover from Local File"),
                ("4", "Discover with Custom Configuration"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.discover_inline_spec()
            elif choice == "2":
                await self.discover_from_url()
            elif choice == "3":
                await self.discover_from_file()
            elif choice == "4":
                await self.discover_custom_config()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def discover_inline_spec(self):
        """Discover service from inline OpenAPI specification."""
        try:
            service_name = Prompt.ask("[bold cyan]Service name[/bold cyan]")
            base_url = Prompt.ask("[bold cyan]Base URL[/bold cyan]", default=f"http://{service_name}:8000")

            # Create a basic OpenAPI spec template
            default_spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": service_name.title(),
                    "version": "1.0.0",
                    "description": f"Auto-generated spec for {service_name}"
                },
                "paths": {
                    "/health": {
                        "get": {
                            "summary": "Health check",
                            "responses": {
                                "200": {"description": "Service is healthy"}
                            }
                        }
                    },
                    "/info": {
                        "get": {
                            "summary": "Service information",
                            "responses": {
                                "200": {"description": "Service info"}
                            }
                        }
                    }
                }
            }

            self.console.print("[yellow]Default OpenAPI spec template:[/yellow]")
            self.console.print(json.dumps(default_spec, indent=2))

            use_default = Confirm.ask("[bold cyan]Use default spec template?[/bold cyan]", default=True)

            if use_default:
                spec = default_spec
            else:
                spec_input = Prompt.ask("[bold cyan]OpenAPI spec (JSON)[/bold cyan]")
                spec = json.loads(spec_input)

            dry_run = Confirm.ask("[bold cyan]Dry run (no registration)?[/bold cyan]", default=True)

            discover_request = {
                "name": service_name,
                "base_url": base_url,
                "spec": spec,
                "dry_run": dry_run
            }

            await self.perform_discovery(discover_request)

        except Exception as e:
            self.console.print(f"[red]Error setting up inline spec discovery: {e}[/red]")

    async def discover_from_url(self):
        """Discover service from OpenAPI URL."""
        try:
            service_name = Prompt.ask("[bold cyan]Service name[/bold cyan]")
            base_url = Prompt.ask("[bold cyan]Base URL[/bold cyan]")
            openapi_url = Prompt.ask("[bold cyan]OpenAPI spec URL[/bold cyan]")

            dry_run = Confirm.ask("[bold cyan]Dry run (no registration)?[/bold cyan]", default=True)

            discover_request = {
                "name": service_name,
                "base_url": base_url,
                "openapi_url": openapi_url,
                "dry_run": dry_run
            }

            await self.perform_discovery(discover_request)

        except Exception as e:
            self.console.print(f"[red]Error setting up URL-based discovery: {e}[/red]")

    async def discover_from_file(self):
        """Discover service from local OpenAPI file."""
        try:
            service_name = Prompt.ask("[bold cyan]Service name[/bold cyan]")
            base_url = Prompt.ask("[bold cyan]Base URL[/bold cyan]")
            file_path = Prompt.ask("[bold cyan]OpenAPI spec file path[/bold cyan]")

            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return

            with open(file_path, 'r') as f:
                spec = json.load(f)

            dry_run = Confirm.ask("[bold cyan]Dry run (no registration)?[/bold cyan]", default=True)

            discover_request = {
                "name": service_name,
                "base_url": base_url,
                "spec": spec,
                "dry_run": dry_run
            }

            await self.perform_discovery(discover_request)

        except Exception as e:
            self.console.print(f"[red]Error reading or processing spec file: {e}[/red]")

    async def discover_custom_config(self):
        """Discover service with custom configuration."""
        try:
            self.console.print("[yellow]Enter discovery configuration as JSON:[/yellow]")
            config_input = Prompt.ask("[bold cyan]Configuration JSON[/bold cyan]")

            discover_request = json.loads(config_input)

            # Validate required fields
            required_fields = ["name", "base_url"]
            missing_fields = [field for field in required_fields if field not in discover_request]

            if missing_fields:
                self.console.print(f"[red]Missing required fields: {', '.join(missing_fields)}[/red]")
                return

            await self.perform_discovery(discover_request)

        except json.JSONDecodeError as e:
            self.console.print(f"[red]Invalid JSON configuration: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error processing custom configuration: {e}[/red]")

    async def perform_discovery(self, discover_request: Dict[str, Any]):
        """Perform the actual discovery operation."""
        try:
            with self.console.status("[bold green]Discovering service endpoints...[/bold green]") as status:
                response = await self.clients.post_json("discovery-agent/discover", discover_request)

            if response.get("data"):
                discovery_data = response["data"]
                await self.display_discovery_results(discovery_data, discover_request)
            else:
                self.console.print("[red]❌ Discovery failed[/red]")
                if response.get("message"):
                    self.console.print(f"[red]Error: {response['message']}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error performing discovery: {e}[/red]")

    async def display_discovery_results(self, discovery_data: Dict[str, Any], request: Dict[str, Any]):
        """Display discovery results in a formatted way."""
        service_name = request.get("name", "unknown")
        dry_run = request.get("dry_run", False)

        endpoints = discovery_data.get("endpoints", [])
        metadata = discovery_data.get("metadata", {})
        count = discovery_data.get("count", 0)

        status_icon = "🔍" if dry_run else "✅"
        status_text = "DISCOVERED (DRY RUN)" if dry_run else "REGISTERED"

        content = f"""
[bold]Service Discovery Results[/bold]

[bold blue]Service:[/bold blue] {service_name}
[bold green]Status:[/bold green] {status_icon} {status_text}
[bold yellow]Endpoints Found:[/bold yellow] {count}

[bold magenta]Metadata:[/bold magenta]
• Base URL: {request.get('base_url', 'N/A')}
• Source: {metadata.get('source', 'inline')}
• Schema Hash: {metadata.get('schema_hash', 'N/A')[:16]}...
"""

        if endpoints:
            content += "\n[bold cyan]Discovered Endpoints:[/bold cyan]\n"
            for i, endpoint in enumerate(endpoints[:10], 1):  # Show first 10
                method = endpoint.get('method', 'GET')
                path = endpoint.get('path', '/')
                summary = endpoint.get('summary', 'No summary')

                method_color = {
                    'GET': 'green',
                    'POST': 'yellow',
                    'PUT': 'blue',
                    'DELETE': 'red'
                }.get(method, 'white')

                content += f"{i:2d}. [{method_color}]{method}[/{method_color}] {path}\n"
                content += f"    {summary}\n"

            if len(endpoints) > 10:
                content += f"    ... and {len(endpoints) - 10} more endpoints\n"

        if not dry_run and discovery_data.get("registration"):
            reg_info = discovery_data["registration"]
            content += f"\n[bold green]Registration Details:[/bold green]\n"
            content += f"• Registered with orchestrator: {reg_info.get('success', False)}\n"
            if reg_info.get('service_id'):
                content += f"• Service ID: {reg_info['service_id']}\n"

        print_panel(self.console, content, border_style="green" if count > 0 else "yellow")

        # Show detailed table if there are endpoints
        if endpoints:
            table = Table(title=f"Endpoint Details - {service_name}")
            table.add_column("Method", style="cyan", justify="center")
            table.add_column("Path", style="white")
            table.add_column("Summary", style="yellow")
            table.add_column("Parameters", style="green")

            for endpoint in endpoints:
                method = endpoint.get('method', 'GET')
                path = endpoint.get('path', '/')
                summary = endpoint.get('summary', 'No summary')
                params = len(endpoint.get('parameters', []))

                method_color = {
                    'GET': 'green',
                    'POST': 'yellow',
                    'PUT': 'blue',
                    'DELETE': 'red'
                }.get(method, 'white')

                table.add_row(
                    f"[{method_color}]{method}[/{method_color}]",
                    path,
                    summary[:40] + "..." if len(summary) > 40 else summary,
                    str(params)
                )

            self.console.print(table)

    async def bulk_discovery_menu(self):
        """Bulk discovery operations submenu."""
        while True:
            menu = create_menu_table("Bulk Discovery Operations", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Discover Multiple Services from Config"),
                ("2", "Batch URL-based Discovery"),
                ("3", "Discover from Directory of Specs"),
                ("4", "Parallel Discovery Execution"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.bulk_discovery_from_config()
            elif choice == "2":
                await self.batch_url_discovery()
            elif choice == "3":
                await self.discovery_from_directory()
            elif choice == "4":
                await self.parallel_discovery()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def bulk_discovery_from_config(self):
        """Perform bulk discovery from configuration file."""
        try:
            config_file = Prompt.ask("[bold cyan]Configuration file path[/bold cyan]")

            if not os.path.exists(config_file):
                self.console.print(f"[red]Configuration file not found: {config_file}[/red]")
                return

            with open(config_file, 'r') as f:
                config = json.load(f)

            services = config.get("services", [])
            if not services:
                self.console.print("[red]No services found in configuration[/red]")
                return

            self.console.print(f"[yellow]Found {len(services)} services in configuration[/yellow]")

            # Preview services
            for i, service in enumerate(services[:5], 1):
                self.console.print(f"  {i}. {service.get('name', 'unknown')} - {service.get('base_url', 'no url')}")

            if len(services) > 5:
                self.console.print(f"  ... and {len(services) - 5} more services")

            proceed = Confirm.ask(f"[bold cyan]Proceed with bulk discovery of {len(services)} services?[/bold cyan]")

            if proceed:
                results = []
                for service in services:
                    try:
                        self.console.print(f"\n[yellow]Discovering {service.get('name', 'unknown')}...[/yellow]")
                        await self.perform_discovery(service)
                        results.append({"service": service["name"], "status": "success"})
                    except Exception as e:
                        self.console.print(f"[red]Failed to discover {service.get('name', 'unknown')}: {e}[/red]")
                        results.append({"service": service["name"], "status": "failed", "error": str(e)})

                # Summary
                successful = sum(1 for r in results if r["status"] == "success")
                failed = len(results) - successful

                self.console.print(f"\n[bold]Bulk Discovery Summary:[/bold]")
                self.console.print(f"✅ Successful: {successful}")
                self.console.print(f"❌ Failed: {failed}")
                self.console.print(f"📊 Total: {len(results)}")

        except Exception as e:
            self.console.print(f"[red]Error in bulk discovery: {e}[/red]")

    async def batch_url_discovery(self):
        """Perform batch discovery from URLs."""
        try:
            urls_input = Prompt.ask("[bold cyan]OpenAPI URLs (comma-separated)[/bold cyan]")
            base_name_pattern = Prompt.ask("[bold cyan]Service name pattern[/bold cyan]", default="service-{index}")
            dry_run = Confirm.ask("[bold cyan]Dry run for all?[/bold cyan]", default=True)

            urls = [url.strip() for url in urls_input.split(",") if url.strip()]

            if not urls:
                self.console.print("[red]No URLs provided[/red]")
                return

            # Generate service configurations
            services = []
            for i, url in enumerate(urls, 1):
                service_name = base_name_pattern.format(index=i)
                # Try to infer base URL from OpenAPI URL
                base_url = url.replace("/openapi.json", "").replace("/swagger.json", "")

                services.append({
                    "name": service_name,
                    "base_url": base_url,
                    "openapi_url": url,
                    "dry_run": dry_run
                })

            self.console.print(f"[yellow]Generated {len(services)} service configurations:[/yellow]")
            for service in services:
                self.console.print(f"  • {service['name']}: {service['base_url']} (from {service['openapi_url']})")

            proceed = Confirm.ask("[bold cyan]Proceed with batch discovery?[/bold cyan]")

            if proceed:
                results = []
                for service in services:
                    try:
                        await self.perform_discovery(service)
                        results.append({"service": service["name"], "status": "success"})
                    except Exception as e:
                        self.console.print(f"[red]Failed: {service['name']} - {e}[/red]")
                        results.append({"service": service["name"], "status": "failed", "error": str(e)})

                # Summary
                successful = sum(1 for r in results if r["status"] == "success")
                self.console.print(f"\n[bold]Batch URL Discovery: {successful}/{len(results)} successful[/bold]")

        except Exception as e:
            self.console.print(f"[red]Error in batch URL discovery: {e}[/red]")

    async def discovery_from_directory(self):
        """Discover services from a directory of OpenAPI specs."""
        try:
            directory = Prompt.ask("[bold cyan]Directory containing OpenAPI specs[/bold cyan]")
            file_pattern = Prompt.ask("[bold cyan]File pattern[/bold cyan]", default="*.json")
            dry_run = Confirm.ask("[bold cyan]Dry run for all?[/bold cyan]", default=True)

            if not os.path.exists(directory):
                self.console.print(f"[red]Directory not found: {directory}[/red]")
                return

            import glob
            spec_files = glob.glob(os.path.join(directory, file_pattern))

            if not spec_files:
                self.console.print(f"[red]No spec files found matching {file_pattern} in {directory}[/red]")
                return

            self.console.print(f"[yellow]Found {len(spec_files)} spec files:[/yellow]")
            for file_path in spec_files[:5]:
                self.console.print(f"  • {os.path.basename(file_path)}")

            if len(spec_files) > 5:
                self.console.print(f"  ... and {len(spec_files) - 5} more files")

            proceed = Confirm.ask(f"[bold cyan]Process {len(spec_files)} spec files?[/bold cyan]")

            if proceed:
                results = []
                for file_path in spec_files:
                    try:
                        service_name = os.path.splitext(os.path.basename(file_path))[0]

                        with open(file_path, 'r') as f:
                            spec = json.load(f)

                        # Infer base URL from spec or use default
                        base_url = f"http://{service_name}:8000"

                        discover_request = {
                            "name": service_name,
                            "base_url": base_url,
                            "spec": spec,
                            "dry_run": dry_run
                        }

                        self.console.print(f"\n[yellow]Processing {os.path.basename(file_path)}...[/yellow]")
                        await self.perform_discovery(discover_request)
                        results.append({"file": os.path.basename(file_path), "status": "success"})

                    except Exception as e:
                        self.console.print(f"[red]Failed to process {os.path.basename(file_path)}: {e}[/red]")
                        results.append({"file": os.path.basename(file_path), "status": "failed", "error": str(e)})

                # Summary
                successful = sum(1 for r in results if r["status"] == "success")
                self.console.print(f"\n[bold]Directory Discovery: {successful}/{len(results)} successful[/bold]")

        except Exception as e:
            self.console.print(f"[red]Error in directory discovery: {e}[/red]")

    async def parallel_discovery(self):
        """Perform parallel discovery operations."""
        try:
            self.console.print("[yellow]Parallel discovery allows processing multiple services simultaneously[/yellow]")
            self.console.print("[yellow]This is a premium feature that would require advanced implementation[/yellow]")
            self.console.print("[yellow]For now, use sequential bulk discovery methods above[/yellow]")

            # Placeholder for future parallel implementation
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in parallel discovery: {e}[/red]")

    async def discovery_history_menu(self):
        """Discovery history and results submenu."""
        while True:
            menu = create_menu_table("Discovery History", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Recent Discovery Operations"),
                ("2", "Search Discovery History"),
                ("3", "View Discovery Statistics"),
                ("4", "Export Discovery Results"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_recent_discoveries()
            elif choice == "2":
                await self.search_discovery_history()
            elif choice == "3":
                await self.view_discovery_statistics()
            elif choice == "4":
                await self.export_discovery_results()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_recent_discoveries(self):
        """View recent discovery operations."""
        try:
            # Since discovery agent doesn't store history, show a placeholder
            self.console.print("[yellow]Discovery history tracking would show recent operations here[/yellow]")
            self.console.print("[yellow]In a full implementation, this would query a discovery history store[/yellow]")
            self.console.print("[yellow]For now, use the orchestrator registry to see registered services[/yellow]")

            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing discovery history: {e}[/red]")

    async def search_discovery_history(self):
        """Search discovery history."""
        try:
            self.console.print("[yellow]Discovery history search would allow filtering by service name, date, etc.[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error searching discovery history: {e}[/red]")

    async def view_discovery_statistics(self):
        """View discovery statistics."""
        try:
            self.console.print("[yellow]Discovery statistics would show metrics like:[/yellow]")
            self.console.print("[yellow]• Total services discovered[/yellow]")
            self.console.print("[yellow]• Total endpoints found[/yellow]")
            self.console.print("[yellow]• Success/failure rates[/yellow]")
            self.console.print("[yellow]• Most common endpoint patterns[/yellow]")

            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing discovery statistics: {e}[/red]")

    async def export_discovery_results(self):
        """Export discovery results."""
        try:
            self.console.print("[yellow]Discovery results export would save endpoint data to various formats[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error exporting discovery results: {e}[/red]")

    async def service_registration_menu(self):
        """Service registration management submenu."""
        while True:
            menu = create_menu_table("Service Registration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Registered Services"),
                ("2", "Register Discovered Service"),
                ("3", "Unregister Service"),
                ("4", "Update Service Registration"),
                ("5", "Validate Registrations"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_registered_services()
            elif choice == "2":
                await self.register_discovered_service()
            elif choice == "3":
                await self.unregister_service()
            elif choice == "4":
                await self.update_service_registration()
            elif choice == "5":
                await self.validate_registrations()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_registered_services(self):
        """View services registered with orchestrator."""
        try:
            # Delegate to orchestrator manager since that's where service registry lives
            self.console.print("[yellow]Service registration is managed by the orchestrator[/yellow]")
            self.console.print("[yellow]Use the Orchestrator Management menu to view registered services[/yellow]")

            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing registered services: {e}[/red]")

    async def register_discovered_service(self):
        """Register a previously discovered service."""
        try:
            self.console.print("[yellow]To register a discovered service:[/yellow]")
            self.console.print("[yellow]1. Run discovery with dry_run=true[/yellow]")
            self.console.print("[yellow]2. Review the discovered endpoints[/yellow]")
            self.console.print("[yellow]3. Run discovery again with dry_run=false[/yellow]")

            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with service registration: {e}[/red]")

    async def unregister_service(self):
        """Unregister a service."""
        try:
            # This would require orchestrator API for unregistration
            self.console.print("[yellow]Service unregistration would remove a service from the orchestrator registry[/yellow]")
            self.console.print("[yellow]This requires orchestrator API support for unregistration[/yellow]")

            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error unregistering service: {e}[/red]")

    async def update_service_registration(self):
        """Update service registration."""
        try:
            self.console.print("[yellow]Service registration updates would modify existing service entries[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error updating service registration: {e}[/red]")

    async def validate_registrations(self):
        """Validate service registrations."""
        try:
            self.console.print("[yellow]Registration validation would check if registered services are still accessible[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error validating registrations: {e}[/red]")

    async def discovery_validation_menu(self):
        """Discovery validation and testing submenu."""
        while True:
            menu = create_menu_table("Discovery Validation", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Validate OpenAPI Spec"),
                ("2", "Test Endpoint Accessibility"),
                ("3", "Compare Discovery Results"),
                ("4", "Generate Discovery Report"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.validate_openapi_spec()
            elif choice == "2":
                await self.test_endpoint_accessibility()
            elif choice == "3":
                await self.compare_discovery_results()
            elif choice == "4":
                await self.generate_discovery_report()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def validate_openapi_spec(self):
        """Validate OpenAPI specification."""
        try:
            spec_input = Prompt.ask("[bold cyan]OpenAPI spec (JSON)[/bold cyan]")

            spec = json.loads(spec_input)

            # Basic validation
            issues = []

            if "openapi" not in spec:
                issues.append("Missing 'openapi' version field")

            if "info" not in spec:
                issues.append("Missing 'info' section")

            if "paths" not in spec:
                issues.append("Missing 'paths' section")
            elif not spec["paths"]:
                issues.append("'paths' section is empty")

            if issues:
                self.console.print("[red]Validation Issues Found:[/red]")
                for issue in issues:
                    self.console.print(f"  ❌ {issue}")
            else:
                path_count = len(spec.get("paths", {}))
                self.console.print("[green]✅ OpenAPI spec is valid[/green]")
                self.console.print(f"[green]• {path_count} paths found[/green]")
                self.console.print("[green]• Basic structure validated[/green]")

        except json.JSONDecodeError:
            self.console.print("[red]❌ Invalid JSON format[/red]")
        except Exception as e:
            self.console.print(f"[red]Error validating OpenAPI spec: {e}[/red]")

    async def test_endpoint_accessibility(self):
        """Test endpoint accessibility."""
        try:
            self.console.print("[yellow]Endpoint accessibility testing would check if discovered endpoints are reachable[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error testing endpoint accessibility: {e}[/red]")

    async def compare_discovery_results(self):
        """Compare discovery results."""
        try:
            self.console.print("[yellow]Discovery result comparison would show differences between discovery runs[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error comparing discovery results: {e}[/red]")

    async def generate_discovery_report(self):
        """Generate discovery report."""
        try:
            self.console.print("[yellow]Discovery report generation would create comprehensive reports of discovery operations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating discovery report: {e}[/red]")

    async def discovery_config_menu(self):
        """Discovery agent configuration submenu."""
        while True:
            menu = create_menu_table("Discovery Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Discovery Agent Config"),
                ("2", "Configure Orchestrator Integration"),
                ("3", "Set Discovery Defaults"),
                ("4", "Configure Validation Rules"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_discovery_config()
            elif choice == "2":
                await self.configure_orchestrator_integration()
            elif choice == "3":
                await self.set_discovery_defaults()
            elif choice == "4":
                await self.configure_validation_rules()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_discovery_config(self):
        """View discovery agent configuration."""
        try:
            self.console.print("[yellow]Discovery agent configuration would show current settings[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing discovery config: {e}[/red]")

    async def configure_orchestrator_integration(self):
        """Configure orchestrator integration."""
        try:
            self.console.print("[yellow]Orchestrator integration config would set registration endpoints and auth[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring orchestrator integration: {e}[/red]")

    async def set_discovery_defaults(self):
        """Set discovery defaults."""
        try:
            self.console.print("[yellow]Discovery defaults would configure default behavior for all discoveries[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error setting discovery defaults: {e}[/red]")

    async def configure_validation_rules(self):
        """Configure validation rules."""
        try:
            self.console.print("[yellow]Validation rules would configure how OpenAPI specs are validated[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring validation rules: {e}[/red]")

    async def discover_service_from_cli(self, discover_request: Dict[str, Any]):
        """Discover service for CLI usage (no interactive prompts)."""
        try:
            with self.console.status(f"[bold green]Discovering service {discover_request.get('name', 'unknown')}...[/bold green]") as status:
                response = await self.clients.post_json("discovery-agent/discover", discover_request)

            if response.get("data"):
                discovery_data = response["data"]
                await self.display_discovery_results(discovery_data, discover_request)
            else:
                self.console.print("[red]❌ Discovery failed[/red]")

        except Exception as e:
            self.console.print(f"[red]Error discovering service: {e}[/red]")
