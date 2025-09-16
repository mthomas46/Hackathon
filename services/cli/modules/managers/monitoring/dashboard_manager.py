"""Dashboard Manager for CLI monitoring operations."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import yaml
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from ...base.base_manager import BaseManager
from ...formatters.display_utils import DisplayManager


class DashboardManager(BaseManager):
    """Manager for dashboard operations."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)
        self.dashboards = {}

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return dashboard management menu."""
        return [
            ("1", "View Available Dashboards"),
            ("2", "Create New Dashboard"),
            ("3", "Edit Dashboard Configuration"),
            ("4", "Import Dashboard"),
            ("5", "Export Dashboard"),
            ("6", "Dashboard Performance"),
            ("b", "Back to Advanced Monitoring")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle menu choice."""
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
        else:
            return False

        if choice in ["1", "3", "4", "5", "6"]:  # Choices that show results
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        return True

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
                self.display.show_warning("No dashboards found. Grafana integration may not be available.")
                self.display.show_info("To enable dashboards, ensure Grafana is running with dashboard provisioning.")

        except Exception as e:
            self.display.show_error(f"Error viewing dashboards: {e}")

    async def create_new_dashboard(self):
        """Create a new monitoring dashboard."""
        try:
            dashboard_name = await self.get_user_input("Dashboard name")

            if not dashboard_name.strip():
                self.display.show_warning("Dashboard name cannot be empty")
                return

            dashboard_type = await self.select_from_list(
                ["system", "application", "business", "custom"],
                "Dashboard type"
            )
            if not dashboard_type:
                dashboard_type = "custom"

            description = await self.get_user_input("Description", default="")

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
                self.display.show_success(f"Dashboard '{dashboard_name}' created successfully")
                self.display.show_info(f"Dashboard includes {len(dashboard_config['panels'])} default panels")
            else:
                self.display.show_error("Failed to create dashboard")

        except Exception as e:
            self.display.show_error(f"Error creating dashboard: {e}")

    async def edit_dashboard_configuration(self):
        """Edit dashboard configuration."""
        try:
            dashboards = self._discover_dashboards()

            if not dashboards:
                self.display.show_warning("No dashboards available to edit")
                return

            dashboard_names = list(dashboards.keys())
            selected_dashboard = await self.select_from_list(dashboard_names, "Select dashboard to edit")

            if not selected_dashboard:
                return

            dashboard_config = await self._load_dashboard_config(selected_dashboard)

            if dashboard_config:
                self.display.show_info(f"Editing dashboard: {selected_dashboard}")

                # Allow editing basic properties
                new_description = await self.get_user_input(
                    "New description",
                    default=dashboard_config.get("description", "")
                )

                if new_description != dashboard_config.get("description", ""):
                    dashboard_config["description"] = new_description
                    dashboard_config["updated_at"] = self._get_timestamp()

                    success = await self._save_dashboard_config(selected_dashboard, dashboard_config)
                    if success:
                        self.display.show_success("Dashboard description updated")
                    else:
                        self.display.show_error("Failed to update dashboard")

                # Option to add panels
                add_panel = await self.confirm_action("Add a new panel to the dashboard?")

                if add_panel:
                    await self._add_panel_to_dashboard(dashboard_config)
                    success = await self._save_dashboard_config(selected_dashboard, dashboard_config)
                    if success:
                        self.display.show_success("Panel added to dashboard")
            else:
                self.display.show_error(f"Could not load dashboard configuration for {selected_dashboard}")

        except Exception as e:
            self.display.show_error(f"Error editing dashboard: {e}")

    async def import_dashboard(self):
        """Import a dashboard from file."""
        try:
            file_path = await self.get_user_input("Dashboard file path to import")

            if not Path(file_path).exists():
                self.display.show_error(f"File not found: {file_path}")
                return

            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    dashboard_config = json.load(f)
                elif file_path.endswith(('.yaml', '.yml')):
                    dashboard_config = yaml.safe_load(f)
                else:
                    self.display.show_error("Unsupported file format. Use .json or .yaml/.yml")
                    return

            dashboard_name = dashboard_config.get("name", Path(file_path).stem)

            # Validate dashboard structure
            if not self._validate_dashboard_config(dashboard_config):
                self.display.show_error("Invalid dashboard configuration")
                return

            success = await self._save_dashboard_config(dashboard_name, dashboard_config)

            if success:
                self.dashboards[dashboard_name] = dashboard_config
                self.display.show_success(f"Dashboard '{dashboard_name}' imported successfully")
                self.display.show_info(f"Imported {len(dashboard_config.get('panels', []))} panels")
            else:
                self.display.show_error("Failed to import dashboard")

        except Exception as e:
            self.display.show_error(f"Error importing dashboard: {e}")

    async def export_dashboard(self):
        """Export a dashboard to file."""
        try:
            dashboards = self._discover_dashboards()

            if not dashboards:
                self.display.show_warning("No dashboards available to export")
                return

            dashboard_names = list(dashboards.keys())
            selected_dashboard = await self.select_from_list(dashboard_names, "Select dashboard to export")

            if not selected_dashboard:
                return

            dashboard_config = await self._load_dashboard_config(selected_dashboard)

            if dashboard_config:
                format_choice = await self.select_from_list(["json", "yaml"], "Export format")
                if not format_choice:
                    format_choice = "json"

                file_path = await self.get_user_input(
                    "Export file path",
                    default=f"{selected_dashboard}.{format_choice}"
                )

                if format_choice == "json":
                    content = json.dumps(dashboard_config, indent=2, default=str)
                else:
                    content = yaml.dump(dashboard_config, default_flow_style=False)

                with open(file_path, 'w') as f:
                    f.write(content)

                self.display.show_success(f"Dashboard exported to {file_path}")
            else:
                self.display.show_error(f"Could not load dashboard configuration for {selected_dashboard}")

        except Exception as e:
            self.display.show_error(f"Error exporting dashboard: {e}")

    async def dashboard_performance(self):
        """Show dashboard performance metrics."""
        try:
            dashboards = self._discover_dashboards()

            if not dashboards:
                self.display.show_warning("No dashboards available for performance analysis")
                return

            # Generate mock performance metrics
            performance_data = {}

            for name in dashboards.keys():
                performance_data[name] = {
                    "load_time": f"{0.5 + 0.1 * len(name):.2f}s",
                    "query_count": len(name) * 2,
                    "data_points": len(name) * 100,
                    "refresh_rate": "30s"
                }

            table = Table(title="Dashboard Performance Metrics")
            table.add_column("Dashboard", style="cyan")
            table.add_column("Load Time", style="green")
            table.add_column("Queries", style="yellow")
            table.add_column("Data Points", style="blue")
            table.add_column("Refresh Rate", style="magenta")

            for name, metrics in performance_data.items():
                table.add_row(
                    name,
                    metrics["load_time"],
                    str(metrics["query_count"]),
                    str(metrics["data_points"]),
                    metrics["refresh_rate"]
                )

            self.console.print(table)

        except Exception as e:
            self.display.show_error(f"Error analyzing dashboard performance: {e}")

    def _discover_dashboards(self) -> Dict[str, Dict[str, Any]]:
        """Discover available dashboards."""
        # In a real implementation, this would query Grafana or other dashboard systems
        # For now, return mock dashboards
        return {
            "system-overview": {
                "type": "system",
                "description": "System-wide metrics and health overview",
                "last_modified": "2024-01-15",
                "panels": 8
            },
            "application-metrics": {
                "type": "application",
                "description": "Application performance and throughput metrics",
                "last_modified": "2024-01-14",
                "panels": 6
            },
            "business-kpis": {
                "type": "business",
                "description": "Business-level KPIs and service level indicators",
                "last_modified": "2024-01-13",
                "panels": 4
            }
        }

    async def _display_dashboard_details(self, dashboard_info: Dict[str, Any]):
        """Display detailed dashboard information."""
        details = f"""
[bold]Dashboard Details:[/bold]
Name: {dashboard_info.get('name', 'Unknown')}
Type: {dashboard_info.get('type', 'Unknown')}
Description: {dashboard_info.get('description', 'No description')}
Last Modified: {dashboard_info.get('last_modified', 'Unknown')}
Panels: {dashboard_info.get('panels', 0)}
"""
        self.display.show_panel(details.strip())

    def _get_system_dashboard_panels(self) -> List[Dict[str, Any]]:
        """Get default system dashboard panels."""
        return [
            {"type": "graph", "title": "CPU Usage", "targets": ["cpu_usage"]},
            {"type": "graph", "title": "Memory Usage", "targets": ["memory_usage"]},
            {"type": "graph", "title": "Disk I/O", "targets": ["disk_io"]},
            {"type": "graph", "title": "Network Traffic", "targets": ["network_traffic"]}
        ]

    def _get_application_dashboard_panels(self) -> List[Dict[str, Any]]:
        """Get default application dashboard panels."""
        return [
            {"type": "graph", "title": "Response Time", "targets": ["response_time"]},
            {"type": "graph", "title": "Request Rate", "targets": ["request_rate"]},
            {"type": "graph", "title": "Error Rate", "targets": ["error_rate"]},
            {"type": "table", "title": "Top Endpoints", "targets": ["endpoint_stats"]}
        ]

    async def _save_dashboard_config(self, name: str, config: Dict[str, Any]) -> bool:
        """Save dashboard configuration."""
        # In a real implementation, this would save to Grafana or a database
        # For now, just store in memory
        try:
            self.dashboards[name] = config
            return True
        except Exception:
            return False

    async def _load_dashboard_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Load dashboard configuration."""
        return self.dashboards.get(name)

    async def _add_panel_to_dashboard(self, dashboard_config: Dict[str, Any]):
        """Add a new panel to dashboard configuration."""
        panel_title = await self.get_user_input("Panel title")
        panel_type = await self.select_from_list(
            ["graph", "table", "singlestat", "heatmap"],
            "Panel type"
        )

        if panel_title and panel_type:
            new_panel = {
                "type": panel_type,
                "title": panel_title,
                "targets": [],
                "added_at": self._get_timestamp()
            }
            dashboard_config["panels"].append(new_panel)

    def _validate_dashboard_config(self, config: Dict[str, Any]) -> bool:
        """Validate dashboard configuration."""
        required_fields = ["name", "type"]
        return all(field in config for field in required_fields)

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
