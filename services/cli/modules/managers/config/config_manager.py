"""Main Configuration Manager for CLI operations."""

from typing import Dict, Any, List, Optional
from rich.table import Table
from rich.prompt import Prompt, Confirm

from ...base.base_manager import BaseManager
from .service_config_manager import ServiceConfigManager
from .environment_manager import EnvironmentManager
from .validation_manager import ValidationManager
from .docker_manager import DockerManager


class ConfigManager(BaseManager):
    """Main configuration manager coordinating all config operations."""

    def __init__(self, console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

        # Initialize specialized managers
        self.service_manager = ServiceConfigManager(console, clients, cache)
        self.environment_manager = EnvironmentManager(console, clients, cache)
        self.validation_manager = ValidationManager(console, clients, cache)
        self.docker_manager = DockerManager(console, clients, cache)

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return the main configuration management menu."""
        return [
            ("1", "Service Configuration (View/edit service YAML configs)"),
            ("2", "Environment Variables (Manage env vars and overrides)"),
            ("3", "Configuration Validation (Validate configs against schemas)"),
            ("4", "Configuration Comparison (Diff configs across environments)"),
            ("5", "Docker Compose Management (Manage deployment configs)"),
            ("6", "Configuration Export/Import (Backup and restore configs)"),
            ("7", "Configuration Audit (Track config changes and history)"),
            ("b", "Back to Main Menu")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle menu choice."""
        if choice == "1":
            await self.service_configuration_menu()
        elif choice == "2":
            await self.environment_variables_menu()
        elif choice == "3":
            await self.validation_menu()
        elif choice == "4":
            await self.comparison_menu()
        elif choice == "5":
            await self.docker_menu()
        elif choice == "6":
            await self.export_import_menu()
        elif choice == "7":
            await self.audit_menu()
        else:
            return False
        return True

    async def service_configuration_menu(self):
        """Service configuration submenu."""
        while True:
            menu_items = [
                ("1", "List Service Configuration Files"),
                ("2", "View Service Configuration"),
                ("3", "Edit Service Configuration"),
                ("4", "Show Configuration Hierarchy"),
                ("b", "Back")
            ]
            self.display.show_menu("Service Configuration", menu_items)

            choice = await self.get_user_input("Select option")

            if choice == "1":
                services = await self._get_available_services()
                if services:
                    selected_service = await self.select_from_list(services, "Select service")
                    if selected_service:
                        config_files = await self.service_manager.list_service_config_files(selected_service)
                        if config_files:
                            table_data = [[str(f), f.stat().st_size] for f in config_files]
                            self.display.show_table(
                                f"Configuration Files for {selected_service}",
                                ["File Path", "Size (bytes)"],
                                table_data
                            )
                        else:
                            self.display.show_warning(f"No configuration files found for {selected_service}")
                await self._pause_continue()

            elif choice == "2":
                services = await self._get_available_services()
                if services:
                    selected_service = await self.select_from_list(services, "Select service to view config")
                    if selected_service:
                        await self.service_manager.view_service_configuration(selected_service)
                await self._pause_continue()

            elif choice == "3":
                services = await self._get_available_services()
                if services:
                    selected_service = await self.select_from_list(services, "Select service to edit config")
                    if selected_service:
                        await self.service_manager.edit_service_configuration(selected_service)
                await self._pause_continue()

            elif choice == "4":
                services = await self._get_available_services()
                if services:
                    selected_service = await self.select_from_list(services, "Select service to show hierarchy")
                    if selected_service:
                        await self.service_manager.show_configuration_hierarchy(selected_service)
                await self._pause_continue()

            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.display.show_error("Invalid option")

    async def environment_variables_menu(self):
        """Environment variables submenu."""
        while True:
            menu_items = [
                ("1", "View Current Environment Variables"),
                ("2", "Set Environment Variable"),
                ("3", "Unset Environment Variable"),
                ("4", "Environment Variable Validation"),
                ("5", "Environment Templates"),
                ("6", "Export Environment Variables"),
                ("b", "Back")
            ]
            self.display.show_menu("Environment Variables", menu_items)

            choice = await self.get_user_input("Select option")

            if choice == "1":
                await self.environment_manager.view_current_environment()
                await self._pause_continue()
            elif choice == "2":
                await self.environment_manager.set_environment_variable()
                await self._pause_continue()
            elif choice == "3":
                await self.environment_manager.unset_environment_variable()
                await self._pause_continue()
            elif choice == "4":
                await self.environment_manager.environment_variable_validation()
                await self._pause_continue()
            elif choice == "5":
                await self.environment_manager.environment_templates()
                await self._pause_continue()
            elif choice == "6":
                await self.environment_manager.export_environment_variables()
                await self._pause_continue()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.display.show_error("Invalid option")

    async def validation_menu(self):
        """Configuration validation submenu."""
        while True:
            menu_items = [
                ("1", "Validate YAML Syntax"),
                ("2", "Validate Configuration Schema"),
                ("3", "Check Configuration Consistency"),
                ("4", "Validate Environment References"),
                ("5", "Configuration Health Check"),
                ("b", "Back")
            ]
            self.display.show_menu("Configuration Validation", menu_items)

            choice = await self.get_user_input("Select option")

            if choice == "1":
                await self.validation_manager.validate_yaml_syntax()
                await self._pause_continue()
            elif choice == "2":
                await self.validation_manager.validate_configuration_schema()
                await self._pause_continue()
            elif choice == "3":
                await self.validation_manager.check_configuration_consistency()
                await self._pause_continue()
            elif choice == "4":
                await self.validation_manager.validate_environment_references()
                await self._pause_continue()
            elif choice == "5":
                await self.validation_manager.configuration_health_check()
                await self._pause_continue()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.display.show_error("Invalid option")

    async def comparison_menu(self):
        """Configuration comparison submenu."""
        self.display.show_info("Configuration comparison feature coming soon!")
        await self._pause_continue()

    async def docker_menu(self):
        """Docker Compose management submenu."""
        while True:
            menu_items = [
                ("1", "View Docker Compose Configuration"),
                ("2", "Validate Docker Compose Files"),
                ("3", "Service Dependencies Analysis"),
                ("4", "Environment Variable Substitution"),
                ("5", "Generate Deployment Config"),
                ("b", "Back")
            ]
            self.display.show_menu("Docker Compose Management", menu_items)

            choice = await self.get_user_input("Select option")

            if choice == "1":
                await self.docker_manager.view_docker_compose_configuration()
                await self._pause_continue()
            elif choice == "2":
                await self.docker_manager.validate_docker_compose_files()
                await self._pause_continue()
            elif choice == "3":
                await self.docker_manager.service_dependencies_analysis()
                await self._pause_continue()
            elif choice == "4":
                await self.docker_manager.environment_variable_substitution()
                await self._pause_continue()
            elif choice == "5":
                await self.docker_manager.generate_deployment_config()
                await self._pause_continue()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.display.show_error("Invalid option")

    async def export_import_menu(self):
        """Configuration export/import submenu."""
        self.display.show_info("Configuration export/import feature coming soon!")
        await self._pause_continue()

    async def audit_menu(self):
        """Configuration audit submenu."""
        self.display.show_info("Configuration audit feature coming soon!")
        await self._pause_continue()

    async def _get_available_services(self) -> List[str]:
        """Get list of available services."""
        try:
            from pathlib import Path
            services_dir = Path("services")
            if services_dir.exists():
                return [d.name for d in services_dir.iterdir() if d.is_dir()]
            return []
        except Exception:
            return []

    async def _pause_continue(self):
        """Pause and wait for user to continue."""
        await self.get_user_input("Press Enter to continue", default="")
