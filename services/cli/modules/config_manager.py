"""Configuration Management Manager module for CLI service.

Provides comprehensive configuration management including
service configs, environment variables, validation, and deployment configs.
"""

from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
import json
import os
import yaml
import re
from pathlib import Path
from collections import defaultdict
import subprocess

from .shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class ConfigManager:
    """Manager for comprehensive configuration management."""

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients
        self.config_cache = {}
        self.env_cache = {}

    async def config_management_menu(self):
        """Main configuration management menu."""
        while True:
            menu = create_menu_table("Configuration Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Service Configuration (View/edit service YAML configs)"),
                ("2", "Environment Variables (Manage env vars and overrides)"),
                ("3", "Configuration Validation (Validate configs against schemas)"),
                ("4", "Configuration Comparison (Diff configs across environments)"),
                ("5", "Docker Compose Management (Manage deployment configs)"),
                ("6", "Configuration Export/Import (Backup and restore configs)"),
                ("7", "Configuration Audit (Track config changes and history)"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.service_configuration_menu()
            elif choice == "2":
                await self.environment_variables_menu()
            elif choice == "3":
                await self.configuration_validation_menu()
            elif choice == "4":
                await self.configuration_comparison_menu()
            elif choice == "5":
                await self.docker_compose_menu()
            elif choice == "6":
                await self.config_export_import_menu()
            elif choice == "7":
                await self.configuration_audit_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def service_configuration_menu(self):
        """Service configuration submenu."""
        while True:
            menu = create_menu_table("Service Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Service Configuration"),
                ("2", "Edit Service Configuration"),
                ("3", "List Service Config Files"),
                ("4", "Show Configuration Hierarchy"),
                ("5", "Service-Specific Settings"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_service_configuration()
            elif choice == "2":
                await self.edit_service_configuration()
            elif choice == "3":
                await self.list_service_config_files()
            elif choice == "4":
                await self.show_configuration_hierarchy()
            elif choice == "5":
                await self.service_specific_settings()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_service_configuration(self):
        """View service configuration."""
        try:
            service = Prompt.ask("[bold cyan]Service name[/bold cyan]", default="shared")

            config_files = self._find_service_config_files(service)

            if not config_files:
                self.console.print(f"[yellow]No configuration files found for service '{service}'[/yellow]")
                return

            table = Table(title=f"Configuration Files for {service}")
            table.add_column("File", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Size", style="yellow", justify="right")

            for config_file in config_files:
                file_path = Path(config_file)
                file_type = self._get_config_file_type(config_file)
                size = f"{file_path.stat().st_size} bytes"

                table.add_row(str(file_path), file_type, size)

            self.console.print(table)

            # Show detailed view of a specific file
            show_details = Confirm.ask("[bold cyan]Show detailed view of a configuration file?[/bold cyan]", default=False)

            if show_details:
                file_choices = [str(f) for f in config_files]
                selected_file = Prompt.ask("[bold cyan]Select file to view[/bold cyan]", choices=file_choices)

                await self._display_config_file(selected_file)

        except Exception as e:
            self.console.print(f"[red]Error viewing service configuration: {e}[/red]")

    async def edit_service_configuration(self):
        """Edit service configuration."""
        try:
            service = Prompt.ask("[bold cyan]Service name[/bold cyan]", default="shared")

            config_files = self._find_service_config_files(service)

            if not config_files:
                self.console.print(f"[yellow]No configuration files found for service '{service}'[/yellow]")
                return

            file_choices = [str(f) for f in config_files]
            selected_file = Prompt.ask("[bold cyan]Select file to edit[/bold cyan]", choices=file_choices)

            # For safety, we'll show the current content and allow editing
            current_content = await self._read_config_file(selected_file)

            if current_content:
                self.console.print(f"\n[bold]Current content of {selected_file}:[/bold]")
                self.console.print("[dim]" + "="*50 + "[/dim]")
                self.console.print(current_content)
                self.console.print("[dim]" + "="*50 + "[/dim]")

                edit_choice = Prompt.ask("[bold cyan]Edit option[/bold cyan]",
                                       choices=["key-value", "full-edit", "cancel"], default="cancel")

                if edit_choice == "key-value":
                    await self._edit_config_key_value(selected_file, current_content)
                elif edit_choice == "full-edit":
                    await self._edit_config_full(selected_file, current_content)
                else:
                    self.console.print("[yellow]Edit cancelled[/yellow]")
            else:
                self.console.print(f"[red]Could not read configuration file {selected_file}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error editing service configuration: {e}[/red]")

    async def list_service_config_files(self):
        """List all service configuration files."""
        try:
            # Scan all service directories for config files
            services_dir = Path("services")
            config_files = []

            for service_dir in services_dir.iterdir():
                if service_dir.is_dir():
                    service_name = service_dir.name

                    # Look for config files
                    for config_file in service_dir.glob("config*.yaml"):
                        config_files.append((service_name, config_file))

                    for config_file in service_dir.glob("*.yaml"):
                        if "config" in config_file.name:
                            config_files.append((service_name, config_file))

            # Add global config files
            config_dir = Path("config")
            if config_dir.exists():
                for config_file in config_dir.glob("*.yaml"):
                    config_files.append(("global", config_file))

            if config_files:
                table = Table(title="All Service Configuration Files")
                table.add_column("Service", style="cyan")
                table.add_column("File Path", style="white")
                table.add_column("Size", style="yellow", justify="right")

                for service, config_file in config_files:
                    size = f"{config_file.stat().st_size} bytes"
                    table.add_row(service, str(config_file), size)

                self.console.print(table)
            else:
                self.console.print("[yellow]No configuration files found[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error listing service config files: {e}[/red]")

    async def show_configuration_hierarchy(self):
        """Show configuration hierarchy."""
        try:
            service = Prompt.ask("[bold cyan]Service name[/bold cyan]", default="shared")

            hierarchy = self._build_config_hierarchy(service)

            if hierarchy:
                content = f"""
[bold]Configuration Hierarchy for {service}[/bold]

[bold blue]Priority Order (highest to lowest):[/bold blue]
"""

                for i, (level, configs) in enumerate(hierarchy.items(), 1):
                    content += f"{i}. {level.title()}\n"
                    for config in configs:
                        content += f"   • {config}\n"

                # Show merged configuration
                merged_config = self._merge_config_hierarchy(hierarchy)
                if merged_config:
                    content += f"\n[bold green]Merged Configuration Preview:[/bold green]\n"
                    content += self._format_config_preview(merged_config, max_lines=20)

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print(f"[yellow]No configuration hierarchy found for service '{service}'[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error showing configuration hierarchy: {e}[/red]")

    async def service_specific_settings(self):
        """Show service-specific settings."""
        try:
            service = Prompt.ask("[bold cyan]Service name[/bold cyan]")

            service_configs = self._get_service_specific_configs(service)

            if service_configs:
                content = f"""
[bold]Service-Specific Settings for {service}[/bold]

[bold blue]Configuration Sections:[/bold blue]
"""

                for section, settings in service_configs.items():
                    content += f"\n[bold cyan]{section.title()}:[/bold cyan]\n"
                    if isinstance(settings, dict):
                        for key, value in settings.items():
                            content += f"• {key}: {value}\n"
                    else:
                        content += f"• {settings}\n"

                print_panel(self.console, content, border_style="green")
            else:
                self.console.print(f"[yellow]No service-specific settings found for '{service}'[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error showing service-specific settings: {e}[/red]")

    async def environment_variables_menu(self):
        """Environment variables submenu."""
        while True:
            menu = create_menu_table("Environment Variables", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Current Environment"),
                ("2", "Set Environment Variable"),
                ("3", "Unset Environment Variable"),
                ("4", "Environment Variable Validation"),
                ("5", "Environment Templates"),
                ("6", "Export Environment Variables"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_current_environment()
            elif choice == "2":
                await self.set_environment_variable()
            elif choice == "3":
                await self.unset_environment_variable()
            elif choice == "4":
                await self.environment_variable_validation()
            elif choice == "5":
                await self.environment_templates()
            elif choice == "6":
                await self.export_environment_variables()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_current_environment(self):
        """View current environment variables."""
        try:
            # Get environment variables related to the system
            relevant_env_vars = self._get_relevant_env_vars()

            if relevant_env_vars:
                table = Table(title="Relevant Environment Variables")
                table.add_column("Variable", style="cyan")
                table.add_column("Value", style="green")
                table.add_column("Source", style="yellow")

                for var, (value, source) in relevant_env_vars.items():
                    # Mask sensitive values
                    display_value = self._mask_sensitive_value(var, value)
                    table.add_row(var, display_value, source)

                self.console.print(table)

                # Show environment file status
                env_files = self._find_env_files()
                if env_files:
                    self.console.print(f"\n[bold blue]Environment Files:[/bold blue]")
                    for env_file in env_files:
                        self.console.print(f"• {env_file}")
            else:
                self.console.print("[yellow]No relevant environment variables found[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error viewing current environment: {e}[/red]")

    async def set_environment_variable(self):
        """Set an environment variable."""
        try:
            var_name = Prompt.ask("[bold cyan]Environment variable name[/bold cyan]")
            var_value = Prompt.ask("[bold cyan]Environment variable value[/bold cyan]")

            if not var_name or not var_value:
                self.console.print("[yellow]Both variable name and value are required[/yellow]")
                return

            # Validate variable name
            if not re.match(r'^[A-Z][A-Z0-9_]*$', var_name):
                self.console.print("[red]Invalid environment variable name. Must start with letter and contain only uppercase letters, numbers, and underscores.[/red]")
                return

            # Set in current session
            os.environ[var_name] = var_value

            # Ask if they want to persist to file
            persist = Confirm.ask(f"[bold cyan]Persist {var_name} to .env file?[/bold cyan]", default=True)

            if persist:
                env_file = Path(".env")
                env_content = ""

                if env_file.exists():
                    env_content = env_file.read_text()

                # Check if variable already exists
                var_pattern = re.compile(f'^{re.escape(var_name)}=.*$', re.MULTILINE)
                if var_pattern.search(env_content):
                    # Replace existing
                    env_content = var_pattern.sub(f"{var_name}={var_value}", env_content)
                else:
                    # Add new
                    if env_content and not env_content.endswith('\n'):
                        env_content += '\n'
                    env_content += f"{var_name}={var_value}\n"

                env_file.write_text(env_content)
                self.console.print(f"[green]✅ Environment variable {var_name} set and persisted to .env file[/green]")
            else:
                self.console.print(f"[green]✅ Environment variable {var_name} set for current session[/green]")

        except Exception as e:
            self.console.print(f"[red]Error setting environment variable: {e}[/red]")

    async def unset_environment_variable(self):
        """Unset an environment variable."""
        try:
            var_name = Prompt.ask("[bold cyan]Environment variable name to unset[/bold cyan]")

            if not var_name:
                self.console.print("[yellow]Variable name is required[/yellow]")
                return

            # Unset from current session
            if var_name in os.environ:
                del os.environ[var_name]
                self.console.print(f"[green]✅ Environment variable {var_name} unset from current session[/green]")
            else:
                self.console.print(f"[yellow]Environment variable {var_name} was not set[/yellow]")

            # Remove from .env file if it exists
            env_file = Path(".env")
            if env_file.exists():
                env_content = env_file.read_text()
                var_pattern = re.compile(f'^{re.escape(var_name)}=.*$\n?', re.MULTILINE)

                if var_pattern.search(env_content):
                    env_content = var_pattern.sub('', env_content)
                    env_file.write_text(env_content)
                    self.console.print(f"[green]✅ Environment variable {var_name} removed from .env file[/green]")

        except Exception as e:
            self.console.print(f"[red]Error unsetting environment variable: {e}[/red]")

    async def environment_variable_validation(self):
        """Validate environment variables."""
        try:
            validation_results = self._validate_environment_variables()

            if validation_results:
                table = Table(title="Environment Variable Validation Results")
                table.add_column("Variable", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Message", style="white")

                for var, (status, message) in validation_results.items():
                    status_color = "green" if status == "valid" else "red" if status == "invalid" else "yellow"
                    table.add_row(var, f"[{status_color}]{status.upper()}[/{status_color}]", message)

                self.console.print(table)

                # Show summary
                valid_count = sum(1 for status, _ in validation_results.values() if status == "valid")
                invalid_count = sum(1 for status, _ in validation_results.values() if status == "invalid")
                warning_count = sum(1 for status, _ in validation_results.values() if status == "warning")

                content = f"""
[bold]Validation Summary:[/bold]
• Valid: {valid_count}
• Invalid: {invalid_count}
• Warnings: {warning_count}
"""

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]No environment variables to validate[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error validating environment variables: {e}[/red]")

    async def environment_templates(self):
        """Manage environment templates."""
        try:
            templates = self._get_environment_templates()

            if templates:
                table = Table(title="Environment Templates")
                table.add_column("Template", style="cyan")
                table.add_column("Description", style="white")
                table.add_column("Variables", style="green", justify="right")

                for name, template in templates.items():
                    var_count = len(template.get("variables", []))
                    table.add_row(name, template.get("description", ""), str(var_count))

                self.console.print(table)

                # Option to apply a template
                apply_template = Confirm.ask("[bold cyan]Apply an environment template?[/bold cyan]", default=False)

                if apply_template:
                    template_names = list(templates.keys())
                    selected_template = Prompt.ask("[bold cyan]Select template to apply[/bold cyan]", choices=template_names)

                    await self._apply_environment_template(templates[selected_template])
            else:
                self.console.print("[yellow]No environment templates available[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error managing environment templates: {e}[/red]")

    async def export_environment_variables(self):
        """Export environment variables."""
        try:
            format_choice = Prompt.ask("[bold cyan]Export format[/bold cyan]", choices=["env", "json", "yaml"], default="env")

            relevant_env_vars = self._get_relevant_env_vars()
            export_data = {var: value for var, (value, _) in relevant_env_vars.items()}

            if not export_data:
                self.console.print("[yellow]No environment variables to export[/yellow]")
                return

            filename = f"env_export.{format_choice}"
            file_path = Prompt.ask("[bold cyan]Export file path[/bold cyan]", default=filename)

            if format_choice == "env":
                content = "\n".join(f"{k}={v}" for k, v in export_data.items())
            elif format_choice == "json":
                content = json.dumps(export_data, indent=2)
            elif format_choice == "yaml":
                content = yaml.dump(export_data, default_flow_style=False)

            with open(file_path, 'w') as f:
                f.write(content)

            self.console.print(f"[green]✅ Environment variables exported to {file_path}[/green]")

        except Exception as e:
            self.console.print(f"[red]Error exporting environment variables: {e}[/red]")

    async def configuration_validation_menu(self):
        """Configuration validation submenu."""
        while True:
            menu = create_menu_table("Configuration Validation", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Validate YAML Syntax"),
                ("2", "Validate Configuration Schema"),
                ("3", "Check Configuration Consistency"),
                ("4", "Validate Environment Variable References"),
                ("5", "Configuration Health Check"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.validate_yaml_syntax()
            elif choice == "2":
                await self.validate_configuration_schema()
            elif choice == "3":
                await self.check_configuration_consistency()
            elif choice == "4":
                await self.validate_environment_references()
            elif choice == "5":
                await self.configuration_health_check()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def validate_yaml_syntax(self):
        """Validate YAML syntax."""
        try:
            config_files = self._find_all_config_files()

            if not config_files:
                self.console.print("[yellow]No configuration files found[/yellow]")
                return

            validation_results = []

            for config_file in config_files:
                try:
                    with open(config_file, 'r') as f:
                        yaml.safe_load(f)
                    validation_results.append((config_file, "valid", "YAML syntax is valid"))
                except yaml.YAMLError as e:
                    validation_results.append((config_file, "invalid", f"YAML syntax error: {str(e)}"))
                except Exception as e:
                    validation_results.append((config_file, "error", f"Error reading file: {str(e)}"))

            # Display results
            table = Table(title="YAML Syntax Validation Results")
            table.add_column("File", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Message", style="white")

            for file_path, status, message in validation_results:
                status_color = "green" if status == "valid" else "red"
                table.add_row(str(file_path), f"[{status_color}]{status.upper()}[/{status_color}]", message)

            self.console.print(table)

            # Summary
            valid_count = sum(1 for _, status, _ in validation_results if status == "valid")
            invalid_count = sum(1 for _, status, _ in validation_results if status == "invalid")
            error_count = sum(1 for _, status, _ in validation_results if status == "error")

            content = f"""
[bold]YAML Validation Summary:[/bold]
• Valid: {valid_count}
• Invalid: {invalid_count}
• Errors: {error_count}
"""

            print_panel(self.console, content, border_style="blue")

        except Exception as e:
            self.console.print(f"[red]Error validating YAML syntax: {e}[/red]")

    async def validate_configuration_schema(self):
        """Validate configuration against schema."""
        try:
            self.console.print("[yellow]Configuration schema validation would validate configs against defined schemas[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error validating configuration schema: {e}[/red]")

    async def check_configuration_consistency(self):
        """Check configuration consistency."""
        try:
            consistency_issues = self._check_configuration_consistency()

            if consistency_issues:
                table = Table(title="Configuration Consistency Issues")
                table.add_column("Issue", style="cyan")
                table.add_column("Severity", style="yellow")
                table.add_column("Description", style="white")

                for issue in consistency_issues:
                    severity_color = "red" if issue["severity"] == "high" else "yellow" if issue["severity"] == "medium" else "blue"
                    table.add_row(issue["issue"], f"[{severity_color}]{issue['severity'].upper()}[/{severity_color}]", issue["description"])

                self.console.print(table)
            else:
                self.console.print("[green]✅ No configuration consistency issues found[/green]")

        except Exception as e:
            self.console.print(f"[red]Error checking configuration consistency: {e}[/red]")

    async def validate_environment_references(self):
        """Validate environment variable references."""
        try:
            config_files = self._find_all_config_files()
            validation_results = []

            for config_file in config_files:
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()

                    # Find environment variable references
                    env_refs = re.findall(r'\$\{([^}]+)\}', content)

                    for env_ref in env_refs:
                        var_name = env_ref.split(':')[0]  # Handle default values like ${VAR:-default}
                        if var_name not in os.environ:
                            validation_results.append({
                                "file": config_file,
                                "variable": var_name,
                                "status": "missing",
                                "message": f"Environment variable {var_name} is referenced but not set"
                            })
                        else:
                            validation_results.append({
                                "file": config_file,
                                "variable": var_name,
                                "status": "valid",
                                "message": f"Environment variable {var_name} is set"
                            })

                except Exception as e:
                    validation_results.append({
                        "file": config_file,
                        "variable": "N/A",
                        "status": "error",
                        "message": f"Error processing file: {str(e)}"
                    })

            if validation_results:
                table = Table(title="Environment Variable Reference Validation")
                table.add_column("File", style="cyan")
                table.add_column("Variable", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Message", style="white")

                for result in validation_results:
                    status_color = "green" if result["status"] == "valid" else "red" if result["status"] == "missing" else "blue"
                    table.add_row(
                        str(result["file"]),
                        result["variable"],
                        f"[{status_color}]{result['status'].upper()}[/{status_color}]",
                        result["message"]
                    )

                self.console.print(table)
            else:
                self.console.print("[green]✅ No environment variable references found to validate[/green]")

        except Exception as e:
            self.console.print(f"[red]Error validating environment references: {e}[/red]")

    async def configuration_health_check(self):
        """Perform configuration health check."""
        try:
            health_results = self._perform_configuration_health_check()

            if health_results:
                table = Table(title="Configuration Health Check Results")
                table.add_column("Check", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Details", style="white")

                for check, (status, details) in health_results.items():
                    status_color = "green" if status == "healthy" else "red" if status == "unhealthy" else "yellow"
                    table.add_row(check, f"[{status_color}]{status.upper()}[/{status_color}]", details)

                self.console.print(table)

                # Overall health score
                healthy_count = sum(1 for status, _ in health_results.values() if status == "healthy")
                total_count = len(health_results)
                health_score = (healthy_count / total_count) * 100

                status = "🟢 Excellent" if health_score >= 90 else "🟡 Good" if health_score >= 70 else "🔴 Needs Attention"

                content = f"""
[bold]Configuration Health Score: {health_score:.1f}%[/bold]
[bold blue]Overall Status: {status}[/bold blue]
"""

                print_panel(self.console, content, border_style="green" if health_score >= 70 else "yellow")
            else:
                self.console.print("[yellow]No health checks performed[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error performing configuration health check: {e}[/red]")

    async def configuration_comparison_menu(self):
        """Configuration comparison submenu."""
        while True:
            menu = create_menu_table("Configuration Comparison", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Compare Service Configurations"),
                ("2", "Compare Environment Configurations"),
                ("3", "Compare with Baseline"),
                ("4", "Configuration Drift Detection"),
                ("5", "Generate Configuration Diff"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.compare_service_configurations()
            elif choice == "2":
                await self.compare_environment_configurations()
            elif choice == "3":
                await self.compare_with_baseline()
            elif choice == "4":
                await self.configuration_drift_detection()
            elif choice == "5":
                await self.generate_configuration_diff()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def compare_service_configurations(self):
        """Compare configurations between services."""
        try:
            service1 = Prompt.ask("[bold cyan]First service to compare[/bold cyan]")
            service2 = Prompt.ask("[bold cyan]Second service to compare[/bold cyan]")

            config1 = self._load_service_config(service1)
            config2 = self._load_service_config(service2)

            if config1 and config2:
                differences = self._compare_configurations(config1, config2)

                if differences:
                    content = f"""
[bold]Configuration Differences: {service1} vs {service2}[/bold]

[bold green]Shared Settings:[/bold green]
"""

                    for key in differences.get("shared", []):
                        content += f"• {key}\n"

                    if differences.get("only_in_first"):
                        content += f"\n[bold blue]Only in {service1}:[/bold blue]\n"
                        for key in differences["only_in_first"]:
                            content += f"• {key}\n"

                    if differences.get("only_in_second"):
                        content += f"\n[bold yellow]Only in {service2}:[/bold yellow]\n"
                        for key in differences["only_in_second"]:
                            content += f"• {key}\n"

                    if differences.get("different_values"):
                        content += f"\n[bold red]Different Values:[/bold red]\n"
                        for key, (val1, val2) in differences["different_values"].items():
                            content += f"• {key}: {service1}={val1}, {service2}={val2}\n"

                    print_panel(self.console, content, border_style="blue")
                else:
                    self.console.print(f"[green]✅ Configurations for {service1} and {service2} are identical[/green]")
            else:
                self.console.print(f"[red]Could not load configurations for comparison[/red]")

        except Exception as e:
            self.console.print(f"[red]Error comparing service configurations: {e}[/red]")

    async def compare_environment_configurations(self):
        """Compare configurations across environments."""
        try:
            self.console.print("[yellow]Environment configuration comparison would compare configs across dev/staging/prod[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error comparing environment configurations: {e}[/red]")

    async def compare_with_baseline(self):
        """Compare with baseline configuration."""
        try:
            self.console.print("[yellow]Baseline configuration comparison would compare with known good configs[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error comparing with baseline: {e}[/red]")

    async def configuration_drift_detection(self):
        """Detect configuration drift."""
        try:
            self.console.print("[yellow]Configuration drift detection would identify unauthorized config changes[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error detecting configuration drift: {e}[/red]")

    async def generate_configuration_diff(self):
        """Generate configuration diff."""
        try:
            self.console.print("[yellow]Configuration diff generation would create detailed config change reports[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating configuration diff: {e}[/red]")

    async def docker_compose_menu(self):
        """Docker Compose management submenu."""
        while True:
            menu = create_menu_table("Docker Compose Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Docker Compose Configuration"),
                ("2", "Validate Docker Compose Files"),
                ("3", "Service Dependencies Analysis"),
                ("4", "Environment Variable Substitution"),
                ("5", "Generate Deployment Config"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_docker_compose_configuration()
            elif choice == "2":
                await self.validate_docker_compose_files()
            elif choice == "3":
                await self.service_dependencies_analysis()
            elif choice == "4":
                await self.environment_variable_substitution()
            elif choice == "5":
                await self.generate_deployment_config()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_docker_compose_configuration(self):
        """View Docker Compose configuration."""
        try:
            compose_files = self._find_docker_compose_files()

            if not compose_files:
                self.console.print("[yellow]No Docker Compose files found[/yellow]")
                return

            table = Table(title="Docker Compose Files")
            table.add_column("File", style="cyan")
            table.add_column("Services", style="green", justify="right")
            table.add_column("Size", style="yellow", justify="right")

            for compose_file in compose_files:
                try:
                    with open(compose_file, 'r') as f:
                        compose_data = yaml.safe_load(f)

                    services_count = len(compose_data.get("services", {}))
                    size = f"{Path(compose_file).stat().st_size} bytes"

                    table.add_row(str(compose_file), str(services_count), size)
                except Exception:
                    table.add_row(str(compose_file), "error", "error")

            self.console.print(table)

            # Show detailed view of a specific file
            show_details = Confirm.ask("[bold cyan]Show detailed view of a Docker Compose file?[/bold cyan]", default=False)

            if show_details:
                file_choices = [str(f) for f in compose_files]
                selected_file = Prompt.ask("[bold cyan]Select file to view[/bold cyan]", choices=file_choices)

                await self._display_compose_file(selected_file)

        except Exception as e:
            self.console.print(f"[red]Error viewing Docker Compose configuration: {e}[/red]")

    async def validate_docker_compose_files(self):
        """Validate Docker Compose files."""
        try:
            compose_files = self._find_docker_compose_files()

            if not compose_files:
                self.console.print("[yellow]No Docker Compose files found[/yellow]")
                return

            validation_results = []

            for compose_file in compose_files:
                try:
                    # Use docker-compose config to validate
                    result = subprocess.run(
                        ["docker-compose", "-f", str(compose_file), "config", "--quiet"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        validation_results.append((compose_file, "valid", "Docker Compose syntax is valid"))
                    else:
                        validation_results.append((compose_file, "invalid", result.stderr.strip()))
                except FileNotFoundError:
                    validation_results.append((compose_file, "error", "docker-compose command not found"))
                except subprocess.TimeoutExpired:
                    validation_results.append((compose_file, "error", "Validation timeout"))
                except Exception as e:
                    validation_results.append((compose_file, "error", f"Error: {str(e)}"))

            # Display results
            table = Table(title="Docker Compose Validation Results")
            table.add_column("File", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Message", style="white")

            for file_path, status, message in validation_results:
                status_color = "green" if status == "valid" else "red"
                table.add_row(str(file_path), f"[{status_color}]{status.upper()}[/{status_color}]", message)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error validating Docker Compose files: {e}[/red]")

    async def service_dependencies_analysis(self):
        """Analyze service dependencies."""
        try:
            compose_files = self._find_docker_compose_files()

            if not compose_files:
                self.console.print("[yellow]No Docker Compose files found[/yellow]")
                return

            dependencies = self._analyze_service_dependencies(compose_files)

            if dependencies:
                table = Table(title="Service Dependencies Analysis")
                table.add_column("Service", style="cyan")
                table.add_column("Depends On", style="green")
                table.add_column("Dependency Count", style="yellow", justify="right")

                for service, deps in dependencies.items():
                    deps_list = ", ".join(deps) if deps else "None"
                    table.add_row(service, deps_list, str(len(deps)))

                self.console.print(table)

                # Show dependency graph
                show_graph = Confirm.ask("[bold cyan]Show dependency graph?[/bold cyan]", default=False)

                if show_graph:
                    await self._display_dependency_graph(dependencies)
            else:
                self.console.print("[yellow]No service dependencies found[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing service dependencies: {e}[/red]")

    async def environment_variable_substitution(self):
        """Check environment variable substitution in Docker Compose."""
        try:
            compose_files = self._find_docker_compose_files()

            if not compose_files:
                self.console.print("[yellow]No Docker Compose files found[/yellow]")
                return

            substitution_results = []

            for compose_file in compose_files:
                try:
                    with open(compose_file, 'r') as f:
                        content = f.read()

                    # Find environment variable references
                    env_refs = re.findall(r'\$\{([^}]+)\}', content)

                    for env_ref in env_refs:
                        var_name = env_ref.split(':')[0]  # Handle default values
                        is_set = var_name in os.environ

                        substitution_results.append({
                            "file": compose_file,
                            "variable": var_name,
                            "status": "substituted" if is_set else "not_substituted",
                            "current_value": os.environ.get(var_name, "N/A") if is_set else "Not set"
                        })

                except Exception as e:
                    substitution_results.append({
                        "file": compose_file,
                        "variable": "N/A",
                        "status": "error",
                        "current_value": f"Error: {str(e)}"
                    })

            if substitution_results:
                table = Table(title="Environment Variable Substitution in Docker Compose")
                table.add_column("File", style="cyan")
                table.add_column("Variable", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Current Value", style="white")

                for result in substitution_results:
                    status_color = "green" if result["status"] == "substituted" else "red"
                    table.add_row(
                        str(result["file"]),
                        result["variable"],
                        f"[{status_color}]{result['status'].replace('_', ' ').title()}[/{status_color}]",
                        result["current_value"]
                    )

                self.console.print(table)
            else:
                self.console.print("[green]✅ No environment variable references found in Docker Compose files[/green]")

        except Exception as e:
            self.console.print(f"[red]Error checking environment variable substitution: {e}[/red]")

    async def generate_deployment_config(self):
        """Generate deployment configuration."""
        try:
            self.console.print("[yellow]Deployment configuration generation would create optimized deployment configs[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating deployment config: {e}[/red]")

    async def config_export_import_menu(self):
        """Configuration export/import submenu."""
        while True:
            menu = create_menu_table("Configuration Export/Import", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Export Configuration Set"),
                ("2", "Import Configuration Set"),
                ("3", "Create Configuration Backup"),
                ("4", "Restore from Backup"),
                ("5", "Configuration Templates"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.export_configuration_set()
            elif choice == "2":
                await self.import_configuration_set()
            elif choice == "3":
                await self.create_configuration_backup()
            elif choice == "4":
                await self.restore_from_backup()
            elif choice == "5":
                await self.configuration_templates()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def export_configuration_set(self):
        """Export a set of configurations."""
        try:
            export_name = Prompt.ask("[bold cyan]Export name[/bold cyan]", default="config_export")

            # Gather all configurations
            export_data = {
                "name": export_name,
                "timestamp": datetime.now().isoformat(),
                "configurations": {},
                "environment": {},
                "docker_compose": {}
            }

            # Export service configurations
            config_files = self._find_all_config_files()
            for config_file in config_files:
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                    export_data["configurations"][str(config_file)] = content
                except Exception as e:
                    self.console.print(f"[yellow]Warning: Could not export {config_file}: {e}[/yellow]")

            # Export environment variables
            relevant_env_vars = self._get_relevant_env_vars()
            export_data["environment"] = {var: value for var, (value, _) in relevant_env_vars.items()}

            # Export Docker Compose files
            compose_files = self._find_docker_compose_files()
            for compose_file in compose_files:
                try:
                    with open(compose_file, 'r') as f:
                        content = f.read()
                    export_data["docker_compose"][str(compose_file)] = content
                except Exception as e:
                    self.console.print(f"[yellow]Warning: Could not export {compose_file}: {e}[/yellow]")

            # Save export
            export_file = f"{export_name}.json"
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)

            self.console.print(f"[green]✅ Configuration set exported to {export_file}[/green]")
            self.console.print(f"[blue]Exported {len(export_data['configurations'])} config files, {len(export_data['environment'])} env vars, {len(export_data['docker_compose'])} compose files[/blue]")

        except Exception as e:
            self.console.print(f"[red]Error exporting configuration set: {e}[/red]")

    async def import_configuration_set(self):
        """Import a configuration set."""
        try:
            import_file = Prompt.ask("[bold cyan]Import file path[/bold cyan]")

            if not Path(import_file).exists():
                self.console.print(f"[red]Import file {import_file} does not exist[/red]")
                return

            with open(import_file, 'r') as f:
                import_data = json.load(f)

            self.console.print(f"[yellow]Importing configuration set: {import_data.get('name', 'Unknown')}[/yellow]")
            self.console.print(f"[blue]Created: {import_data.get('timestamp', 'Unknown')}[/blue]")

            # Preview what will be imported
            configs_count = len(import_data.get("configurations", {}))
            env_count = len(import_data.get("environment", {}))
            compose_count = len(import_data.get("docker_compose", {}))

            self.console.print(f"[blue]Will import: {configs_count} config files, {env_count} env vars, {compose_count} compose files[/blue]")

            confirm = Confirm.ask("[bold red]Proceed with import? This may overwrite existing files.[/bold red]", default=False)

            if confirm:
                # Import configurations
                imported_configs = 0
                for file_path, content in import_data.get("configurations", {}).items():
                    try:
                        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(file_path, 'w') as f:
                            f.write(content)
                        imported_configs += 1
                    except Exception as e:
                        self.console.print(f"[red]Error importing {file_path}: {e}[/red]")

                # Import environment variables
                for var_name, var_value in import_data.get("environment", {}).items():
                    os.environ[var_name] = var_value

                # Import Docker Compose files
                imported_compose = 0
                for file_path, content in import_data.get("docker_compose", {}).items():
                    try:
                        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(file_path, 'w') as f:
                            f.write(content)
                        imported_compose += 1
                    except Exception as e:
                        self.console.print(f"[red]Error importing {file_path}: {e}[/red]")

                self.console.print(f"[green]✅ Import completed: {imported_configs} config files, {env_count} env vars, {imported_compose} compose files[/green]")
            else:
                self.console.print("[yellow]Import cancelled[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error importing configuration set: {e}[/red]")

    async def create_configuration_backup(self):
        """Create a configuration backup."""
        try:
            backup_name = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await self.export_configuration_set()
            self.console.print(f"[green]✅ Configuration backup created: {backup_name}[/green]")

        except Exception as e:
            self.console.print(f"[red]Error creating configuration backup: {e}[/red]")

    async def restore_from_backup(self):
        """Restore from a configuration backup."""
        try:
            # Find backup files
            backup_files = list(Path(".").glob("config_backup_*.json"))

            if not backup_files:
                self.console.print("[yellow]No configuration backups found[/yellow]")
                return

            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            table = Table(title="Available Configuration Backups")
            table.add_column("Backup File", style="cyan")
            table.add_column("Created", style="green")
            table.add_column("Size", style="yellow", justify="right")

            for backup_file in backup_files[:10]:  # Show latest 10
                created = datetime.fromtimestamp(backup_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                size = f"{backup_file.stat().st_size} bytes"
                table.add_row(str(backup_file), created, size)

            self.console.print(table)

            if backup_files:
                selected_backup = Prompt.ask("[bold cyan]Select backup to restore[/bold cyan]",
                                           choices=[str(f) for f in backup_files[:10]])

                # Set the import file and call import
                self.console.print(f"[yellow]Restoring from backup: {selected_backup}[/yellow]")
                # Note: This would need to be implemented to avoid recursion
                self.console.print("[yellow]Restore functionality would import the selected backup[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error restoring from backup: {e}[/red]")

    async def configuration_templates(self):
        """Manage configuration templates."""
        try:
            self.console.print("[yellow]Configuration templates would provide reusable config patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error managing configuration templates: {e}[/red]")

    async def configuration_audit_menu(self):
        """Configuration audit submenu."""
        while True:
            menu = create_menu_table("Configuration Audit", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Configuration Changes"),
                ("2", "Configuration Change History"),
                ("3", "Audit Configuration Access"),
                ("4", "Configuration Compliance Check"),
                ("5", "Generate Audit Report"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_configuration_changes()
            elif choice == "2":
                await self.configuration_change_history()
            elif choice == "3":
                await self.audit_configuration_access()
            elif choice == "4":
                await self.configuration_compliance_check()
            elif choice == "5":
                await self.generate_audit_report()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_configuration_changes(self):
        """View recent configuration changes."""
        try:
            self.console.print("[yellow]Configuration change tracking would show recent config modifications[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing configuration changes: {e}[/red]")

    async def configuration_change_history(self):
        """Show configuration change history."""
        try:
            self.console.print("[yellow]Configuration change history would track all config modifications over time[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error showing configuration change history: {e}[/red]")

    async def audit_configuration_access(self):
        """Audit configuration access."""
        try:
            self.console.print("[yellow]Configuration access auditing would track who accesses configuration files[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error auditing configuration access: {e}[/red]")

    async def configuration_compliance_check(self):
        """Check configuration compliance."""
        try:
            self.console.print("[yellow]Configuration compliance checking would validate configs against policies[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error checking configuration compliance: {e}[/red]")

    async def generate_audit_report(self):
        """Generate configuration audit report."""
        try:
            self.console.print("[yellow]Configuration audit report generation would create detailed compliance reports[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating audit report: {e}[/red]")

    # Helper methods

    def _find_service_config_files(self, service: str) -> List[Path]:
        """Find configuration files for a specific service."""
        config_files = []

        # Check service-specific config directory
        service_config_dir = Path("services") / service
        if service_config_dir.exists():
            for yaml_file in service_config_dir.glob("*.yaml"):
                config_files.append(yaml_file)

        # Check for config.yaml in service directory
        config_yaml = service_config_dir / "config.yaml"
        if config_yaml.exists():
            config_files.append(config_yaml)

        # Check shared config for service-specific sections
        shared_config = Path("services/shared/base_config.yaml")
        if shared_config.exists():
            config_files.append(shared_config)

        return config_files

    def _get_config_file_type(self, config_file: Path) -> str:
        """Get the type of configuration file."""
        if "base_config" in str(config_file):
            return "Base Config"
        elif "app.yaml" in str(config_file):
            return "Global Config"
        elif "config.yaml" in str(config_file):
            return "Service Config"
        else:
            return "Custom Config"

    async def _read_config_file(self, file_path: str) -> Optional[str]:
        """Read a configuration file."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception:
            return None

    async def _display_config_file(self, file_path: str):
        """Display the contents of a configuration file."""
        try:
            content = await self._read_config_file(file_path)
            if content:
                # Show first 50 lines or so
                lines = content.split('\n')
                display_content = '\n'.join(lines[:50])

                if len(lines) > 50:
                    display_content += f"\n... and {len(lines) - 50} more lines"

                content_panel = f"[dim]File: {file_path}[/dim]\n\n{display_content}"
                print_panel(self.console, content_panel, border_style="blue")
            else:
                self.console.print(f"[red]Could not read configuration file {file_path}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error displaying config file: {e}[/red]")

    async def _edit_config_key_value(self, file_path: str, current_content: str):
        """Edit configuration using key-value pairs."""
        try:
            # Parse current YAML
            config_data = yaml.safe_load(current_content)

            if not isinstance(config_data, dict):
                self.console.print("[red]Configuration file is not a key-value structure[/red]")
                return

            # Flatten the config for editing
            flat_config = self._flatten_config(config_data)

            table = Table(title=f"Current Configuration ({file_path})")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")

            for key, value in list(flat_config.items())[:20]:  # Show first 20
                table.add_row(key, str(value))

            self.console.print(table)

            if len(flat_config) > 20:
                self.console.print(f"[yellow]... and {len(flat_config) - 20} more configuration keys[/yellow]")

            # Allow editing specific keys
            edit_key = Prompt.ask("[bold cyan]Enter key to edit (or 'done' to finish)[/bold cyan]")

            while edit_key.lower() != 'done':
                if edit_key in flat_config:
                    current_value = flat_config[edit_key]
                    new_value = Prompt.ask(f"[bold cyan]New value for {edit_key}[/bold cyan]", default=str(current_value))

                    # Update the flat config
                    flat_config[edit_key] = new_value

                    # Unflatten and save
                    updated_config = self._unflatten_config(flat_config)

                    with open(file_path, 'w') as f:
                        yaml.dump(updated_config, f, default_flow_style=False)

                    self.console.print(f"[green]✅ Updated {edit_key} = {new_value}[/green]")
                else:
                    self.console.print(f"[red]Key '{edit_key}' not found in configuration[/red]")

                edit_key = Prompt.ask("[bold cyan]Enter key to edit (or 'done' to finish)[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in key-value editing: {e}[/red]")

    async def _edit_config_full(self, file_path: str, current_content: str):
        """Allow full configuration editing."""
        try:
            self.console.print("[yellow]Full configuration editing requires external editor support[/yellow]")
            self.console.print("[yellow]For now, please edit the file directly using your preferred editor[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in full config editing: {e}[/red]")

    def _flatten_config(self, config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten a nested configuration dictionary."""
        flat_config = {}

        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                flat_config.update(self._flatten_config(value, full_key))
            else:
                flat_config[full_key] = value

        return flat_config

    def _unflatten_config(self, flat_config: Dict[str, Any]) -> Dict[str, Any]:
        """Unflatten a flat configuration dictionary."""
        config = {}

        for key, value in flat_config.items():
            keys = key.split('.')
            current = config

            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            current[keys[-1]] = value

        return config

    def _build_config_hierarchy(self, service: str) -> Dict[str, List[str]]:
        """Build configuration hierarchy for a service."""
        hierarchy = {
            "Global Config": [],
            "Base Config": [],
            "Service Config": [],
            "Environment Override": []
        }

        # Global config
        global_config = Path("config/app.yaml")
        if global_config.exists():
            hierarchy["Global Config"].append(str(global_config))

        # Base config
        base_config = Path("services/shared/base_config.yaml")
        if base_config.exists():
            hierarchy["Base Config"].append(str(base_config))

        # Service-specific config
        service_config_files = self._find_service_config_files(service)
        for config_file in service_config_files:
            if "base_config" not in str(config_file):
                hierarchy["Service Config"].append(str(config_file))

        # Environment variables (placeholder)
        hierarchy["Environment Override"].append("Environment variables")

        return hierarchy

    def _merge_config_hierarchy(self, hierarchy: Dict[str, List[str]]) -> Optional[Dict[str, Any]]:
        """Merge configuration from hierarchy."""
        merged_config = {}

        for level, config_files in hierarchy.items():
            for config_file in config_files:
                if config_file != "Environment variables":
                    try:
                        with open(config_file, 'r') as f:
                            config_data = yaml.safe_load(f)
                        if isinstance(config_data, dict):
                            merged_config.update(config_data)
                    except Exception:
                        pass

        return merged_config if merged_config else None

    def _format_config_preview(self, config: Dict[str, Any], max_lines: int = 20) -> str:
        """Format configuration preview."""
        lines = []

        def format_dict(d, indent=0):
            for key, value in d.items():
                if len(lines) >= max_lines:
                    lines.append("...")
                    return

                prefix = "  " * indent
                if isinstance(value, dict):
                    lines.append(f"{prefix}{key}:")
                    format_dict(value, indent + 1)
                else:
                    lines.append(f"{prefix}{key}: {value}")

        format_dict(config)
        return "\n".join(lines)

    def _get_service_specific_configs(self, service: str) -> Dict[str, Any]:
        """Get service-specific configuration sections."""
        # This would analyze the configuration and extract service-specific settings
        service_configs = {}

        # Placeholder implementation
        if service == "shared":
            service_configs = {
                "server": {"host": "0.0.0.0", "port": 8080},
                "redis": {"host": "redis", "port": 6379},
                "logging": {"level": "INFO", "format": "json"}
            }

        return service_configs

    def _get_relevant_env_vars(self) -> Dict[str, Tuple[str, str]]:
        """Get relevant environment variables for the system."""
        relevant_patterns = [
            r'^[A-Z_]*URL$',
            r'^[A-Z_]*HOST$',
            r'^[A-Z_]*PORT$',
            r'^LOG_',
            r'^REDIS_',
            r'^DB_',
            r'^AWS_',
            r'^OLLAMA_',
            r'^SECURE_',
            r'^NOTIFICATION_',
            r'^HTTP_'
        ]

        relevant_vars = {}

        for var_name, var_value in os.environ.items():
            for pattern in relevant_patterns:
                if re.match(pattern, var_name):
                    source = "Environment" if var_name in os.environ else ".env file"
                    relevant_vars[var_name] = (var_value, source)
                    break

        return relevant_vars

    def _mask_sensitive_value(self, var_name: str, value: str) -> str:
        """Mask sensitive values in environment variables."""
        sensitive_patterns = [
            r'.*_KEY.*',
            r'.*_SECRET.*',
            r'.*_TOKEN.*',
            r'.*_PASSWORD.*',
            r'AWS_SECRET_ACCESS_KEY'
        ]

        for pattern in sensitive_patterns:
            if re.match(pattern, var_name, re.IGNORECASE):
                return "*" * len(value)

        return value

    def _find_env_files(self) -> List[str]:
        """Find environment files in the project."""
        env_files = []

        for env_file in [".env", ".env.local", ".env.dev", ".env.prod"]:
            if Path(env_file).exists():
                env_files.append(env_file)

        return env_files

    def _validate_environment_variables(self) -> Dict[str, Tuple[str, str]]:
        """Validate environment variables."""
        validation_results = {}

        # Check required variables
        required_vars = [
            "REDIS_HOST",
            "ORCHESTRATOR_URL",
            "DOC_STORE_URL"
        ]

        for var in required_vars:
            if var in os.environ:
                validation_results[var] = ("valid", "Required variable is set")
            else:
                validation_results[var] = ("invalid", "Required variable is missing")

        # Check URL format variables
        url_vars = [var for var in os.environ.keys() if var.endswith('_URL')]

        for var in url_vars:
            value = os.environ[var]
            if value.startswith(('http://', 'https://')):
                validation_results[var] = ("valid", "Valid URL format")
            else:
                validation_results[var] = ("warning", "URL may not be properly formatted")

        return validation_results

    def _get_environment_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available environment templates."""
        # Placeholder for environment templates
        templates = {
            "development": {
                "description": "Development environment with debug settings",
                "variables": [
                    {"name": "LOG_LEVEL", "value": "DEBUG", "description": "Detailed logging"},
                    {"name": "REDIS_HOST", "value": "localhost", "description": "Local Redis"},
                    {"name": "HTTP_CLIENT_TIMEOUT", "value": "60", "description": "Extended timeout"}
                ]
            },
            "production": {
                "description": "Production environment with optimized settings",
                "variables": [
                    {"name": "LOG_LEVEL", "value": "INFO", "description": "Standard logging"},
                    {"name": "HTTP_CLIENT_TIMEOUT", "value": "30", "description": "Standard timeout"},
                    {"name": "REDIS_HOST", "value": "redis", "description": "Production Redis"}
                ]
            }
        }

        return templates

    async def _apply_environment_template(self, template: Dict[str, Any]):
        """Apply an environment template."""
        try:
            variables = template.get("variables", [])

            self.console.print(f"[yellow]Applying template with {len(variables)} variables...[/yellow]")

            for var in variables:
                var_name = var["name"]
                var_value = var["value"]
                description = var.get("description", "")

                # Set in environment
                os.environ[var_name] = var_value

                self.console.print(f"[green]✅ Set {var_name} = {var_value} ({description})[/green]")

            # Ask to persist
            persist = Confirm.ask("[bold cyan]Persist template variables to .env file?[/bold cyan]", default=True)

            if persist:
                env_content = ""
                env_file = Path(".env")

                if env_file.exists():
                    env_content = env_file.read_text()

                for var in variables:
                    var_name = var["name"]
                    var_value = var["value"]

                    # Check if already exists
                    var_pattern = re.compile(f'^{re.escape(var_name)}=.*$', re.MULTILINE)
                    if var_pattern.search(env_content):
                        env_content = var_pattern.sub(f"{var_name}={var_value}", env_content)
                    else:
                        if env_content and not env_content.endswith('\n'):
                            env_content += '\n'
                        env_content += f"{var_name}={var_value}\n"

                env_file.write_text(env_content)
                self.console.print("[green]✅ Template variables persisted to .env file[/green]")

        except Exception as e:
            self.console.print(f"[red]Error applying environment template: {e}[/red]")

    def _find_all_config_files(self) -> List[Path]:
        """Find all configuration files in the project."""
        config_files = []

        # YAML files in config directory
        config_dir = Path("config")
        if config_dir.exists():
            config_files.extend(config_dir.glob("*.yaml"))

        # Service config files
        services_dir = Path("services")
        if services_dir.exists():
            for service_dir in services_dir.iterdir():
                if service_dir.is_dir():
                    config_files.extend(service_dir.glob("*.yaml"))

        return config_files

    def _check_configuration_consistency(self) -> List[Dict[str, Any]]:
        """Check configuration consistency across services."""
        issues = []

        # Check for duplicate service URLs
        service_urls = {}
        config_files = self._find_all_config_files()

        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)

                if isinstance(config_data, dict):
                    # Look for service URL patterns
                    for key, value in config_data.items():
                        if key.endswith('_URL') and isinstance(value, str):
                            if value in service_urls and service_urls[value] != config_file:
                                issues.append({
                                    "issue": "Duplicate service URL",
                                    "severity": "medium",
                                    "description": f"URL '{value}' is used in both {service_urls[value]} and {config_file}"
                                })
                            else:
                                service_urls[value] = config_file
            except Exception:
                pass

        # Check for missing required configurations
        required_configs = ["redis.host", "server.port"]
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)

                flat_config = self._flatten_config(config_data)
                for required in required_configs:
                    if required not in flat_config:
                        issues.append({
                            "issue": "Missing required configuration",
                            "severity": "high",
                            "description": f"Required config '{required}' not found in {config_file}"
                        })
            except Exception:
                pass

        return issues

    def _perform_configuration_health_check(self) -> Dict[str, Tuple[str, str]]:
        """Perform comprehensive configuration health check."""
        health_checks = {}

        # Check YAML syntax
        config_files = self._find_all_config_files()
        valid_yaml = 0
        total_yaml = len(config_files)

        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    yaml.safe_load(f)
                valid_yaml += 1
            except Exception:
                pass

        yaml_health = "healthy" if valid_yaml == total_yaml else "unhealthy"
        health_checks["YAML Syntax"] = (yaml_health, f"{valid_yaml}/{total_yaml} files valid")

        # Check environment variables
        env_validation = self._validate_environment_variables()
        valid_env = sum(1 for status, _ in env_validation.values() if status == "valid")
        total_env = len(env_validation)

        env_health = "healthy" if valid_env == total_env else "warning" if valid_env > total_env * 0.8 else "unhealthy"
        health_checks["Environment Variables"] = (env_health, f"{valid_env}/{total_env} variables valid")

        # Check service connectivity (placeholder)
        health_checks["Service Connectivity"] = ("unknown", "Connectivity check not implemented")

        # Check configuration consistency
        consistency_issues = self._check_configuration_consistency()
        high_issues = sum(1 for issue in consistency_issues if issue["severity"] == "high")

        consistency_health = "healthy" if high_issues == 0 else "unhealthy"
        health_checks["Configuration Consistency"] = (consistency_health, f"{high_issues} high-severity issues")

        return health_checks

    def _load_service_config(self, service: str) -> Optional[Dict[str, Any]]:
        """Load configuration for a specific service."""
        config_files = self._find_service_config_files(service)

        merged_config = {}

        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                if isinstance(config_data, dict):
                    merged_config.update(config_data)
            except Exception:
                pass

        return merged_config if merged_config else None

    def _compare_configurations(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two configurations."""
        flat1 = self._flatten_config(config1)
        flat2 = self._flatten_config(config2)

        shared = set(flat1.keys()) & set(flat2.keys())
        only_in_first = set(flat1.keys()) - set(flat2.keys())
        only_in_second = set(flat2.keys()) - set(flat1.keys())

        different_values = {}
        for key in shared:
            if flat1[key] != flat2[key]:
                different_values[key] = (flat1[key], flat2[key])

        return {
            "shared": list(shared),
            "only_in_first": list(only_in_first),
            "only_in_second": list(only_in_second),
            "different_values": different_values
        }

    def _find_docker_compose_files(self) -> List[Path]:
        """Find Docker Compose files in the project."""
        compose_files = []

        # Common Docker Compose file names
        compose_names = [
            "docker-compose.yml",
            "docker-compose.yaml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml",
            "docker-compose.override.yml"
        ]

        for name in compose_names:
            compose_file = Path(name)
            if compose_file.exists():
                compose_files.append(compose_file)

        return compose_files

    async def _display_compose_file(self, file_path: str):
        """Display the contents of a Docker Compose file."""
        try:
            with open(file_path, 'r') as f:
                compose_data = yaml.safe_load(f)

            # Show services overview
            services = compose_data.get("services", {})

            table = Table(title=f"Docker Compose Services ({file_path})")
            table.add_column("Service", style="cyan")
            table.add_column("Image", style="green")
            table.add_column("Ports", style="yellow")

            for service_name, service_config in services.items():
                image = service_config.get("image", "N/A")
                ports = service_config.get("ports", [])
                ports_str = ", ".join(str(p) for p in ports) if ports else "None"

                table.add_row(service_name, image, ports_str)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error displaying Docker Compose file: {e}[/red]")

    def _analyze_service_dependencies(self, compose_files: List[Path]) -> Dict[str, List[str]]:
        """Analyze service dependencies in Docker Compose files."""
        dependencies = {}

        for compose_file in compose_files:
            try:
                with open(compose_file, 'r') as f:
                    compose_data = yaml.safe_load(f)

                services = compose_data.get("services", {})

                for service_name, service_config in services.items():
                    deps = service_config.get("depends_on", [])
                    if isinstance(deps, list):
                        dependencies[service_name] = deps
                    elif isinstance(deps, dict):
                        dependencies[service_name] = list(deps.keys())
                    else:
                        dependencies[service_name] = []

            except Exception:
                pass

        return dependencies

    async def _display_dependency_graph(self, dependencies: Dict[str, List[str]]):
        """Display a dependency graph."""
        try:
            # Simple text-based dependency display
            content = "[bold]Service Dependency Graph:[/bold]\n\n"

            for service, deps in dependencies.items():
                if deps:
                    content += f"[cyan]{service}[/cyan] depends on: {', '.join(deps)}\n"
                else:
                    content += f"[cyan]{service}[/cyan] (no dependencies)\n"

            print_panel(self.console, content, border_style="blue")

        except Exception as e:
            self.console.print(f"[red]Error displaying dependency graph: {e}[/red]")
