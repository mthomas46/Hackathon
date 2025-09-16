"""Advanced Monitoring Manager for CLI operations."""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.prompt import Prompt

from ...base.base_manager import BaseManager
from .dashboard_manager import DashboardManager
from .alerting_manager import AlertingManager


class AdvancedMonitoringManager(BaseManager):
    """Main advanced monitoring manager coordinating all monitoring operations."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

        # Initialize specialized managers
        self.dashboard_manager = DashboardManager(console, clients, cache)
        self.alerting_manager = AlertingManager(console, clients, cache)

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return advanced monitoring main menu."""
        return [
            ("1", "Custom Metrics Dashboards (Create, Edit, View)"),
            ("2", "Alerting Rule Management (Create, Edit, Monitor)"),
            ("3", "SLO/SLA Monitoring (Definitions, Compliance)"),
            ("4", "Real-Time Metrics (System, Service, Custom)"),
            ("5", "Anomaly Detection (Performance, Traffic, Errors)"),
            ("6", "Performance Analytics (Trends, Bottlenecks)"),
            ("7", "Monitoring Configuration (Settings, Integration)"),
            ("b", "Back to Main Menu")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle menu choice."""
        if choice == "1":
            await self.dashboard_manager.run_menu_loop("Custom Metrics Dashboards")
        elif choice == "2":
            await self.alerting_manager.run_menu_loop("Alerting Rule Management")
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
        else:
            return False

        return True

    async def slo_sla_monitoring_menu(self):
        """SLO/SLA monitoring submenu."""
        self.display.show_info("SLO/SLA monitoring feature coming soon!")
        self.display.show_info("This will include service level objective and agreement monitoring")
        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    async def real_time_metrics_menu(self):
        """Real-time metrics submenu."""
        self.display.show_info("Real-time metrics feature coming soon!")
        self.display.show_info("This will include live system and application metrics")
        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    async def anomaly_detection_menu(self):
        """Anomaly detection submenu."""
        self.display.show_info("Anomaly detection feature coming soon!")
        self.display.show_info("This will include automated anomaly detection for metrics")
        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    async def performance_analytics_menu(self):
        """Performance analytics submenu."""
        self.display.show_info("Performance analytics feature coming soon!")
        self.display.show_info("This will include detailed performance trend analysis")
        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    async def monitoring_configuration_menu(self):
        """Monitoring configuration submenu."""
        self.display.show_info("Monitoring configuration feature coming soon!")
        self.display.show_info("This will include monitoring system settings and integrations")
        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    # CLI integration methods for backward compatibility
    async def view_dashboards_from_cli(self):
        """View dashboards for CLI integration."""
        await self.dashboard_manager.view_available_dashboards()

    async def view_alerts_from_cli(self):
        """View alerts for CLI integration."""
        await self.alerting_manager.view_active_alerts()

    async def view_slo_status_from_cli(self):
        """View SLO status for CLI integration."""
        self.display.show_info("SLO/SLA status viewing coming soon")

    async def view_metrics_from_cli(self):
        """View metrics for CLI integration."""
        self.display.show_info("Real-time metrics viewing coming soon")
