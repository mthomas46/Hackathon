"""Environment Variables Manager for CLI operations."""

from typing import Dict, Any, List, Optional, Tuple
import os
import json
import re
from pathlib import Path

from ...base.base_manager import BaseManager
from ...formatters.display_utils import DisplayManager


class EnvironmentManager(BaseManager):
    """Manager for environment variable operations."""

    async def view_current_environment(self):
        """View current environment variables."""
        try:
            env_vars = await self._get_relevant_env_vars()
            masked_vars = await self._mask_sensitive_values(env_vars)

            # Display in table format
            table_data = []
            for var_name, (value, source) in masked_vars.items():
                table_data.append([var_name, value, source])

            self.display.show_table(
                "Environment Variables",
                ["Variable", "Value", "Source"],
                table_data
            )

        except Exception as e:
            self.display.show_error(f"Error viewing environment: {e}")

    async def set_environment_variable(self):
        """Set an environment variable."""
        try:
            var_name = await self.get_user_input("Environment variable name")
            if not var_name:
                return

            var_value = await self.get_user_input(f"Value for {var_name}", password=True)
            if var_value is None:
                return

            # Validate variable name
            if not re.match(r'^[A-Z][A-Z0-9_]*$', var_name):
                self.display.show_error("Invalid variable name. Must start with letter and contain only uppercase letters, numbers, and underscores.")
                return

            # Set in current environment
            os.environ[var_name] = var_value

            # Optionally save to .env file
            if await self.confirm_action("Save to .env file for persistence?"):
                await self._save_to_env_file(var_name, var_value)

            self.display.show_success(f"Environment variable {var_name} set successfully")

        except Exception as e:
            self.display.show_error(f"Error setting environment variable: {e}")

    async def unset_environment_variable(self):
        """Unset an environment variable."""
        try:
            var_name = await self.get_user_input("Environment variable name to unset")
            if not var_name:
                return

            if var_name in os.environ:
                del os.environ[var_name]

                # Optionally remove from .env file
                if await self.confirm_action("Remove from .env file?"):
                    await self._remove_from_env_file(var_name)

                self.display.show_success(f"Environment variable {var_name} unset successfully")
            else:
                self.display.show_warning(f"Environment variable {var_name} not found")

        except Exception as e:
            self.display.show_error(f"Error unsetting environment variable: {e}")

    async def environment_variable_validation(self):
        """Validate environment variables."""
        try:
            validation_results = await self._validate_environment_variables()

            # Display results
            table_data = []
            for var_name, (status, message) in validation_results.items():
                status_icon = "✅" if status == "valid" else "❌" if status == "invalid" else "⚠️"
                table_data.append([var_name, f"{status_icon} {status}", message])

            self.display.show_table(
                "Environment Variable Validation",
                ["Variable", "Status", "Message"],
                table_data
            )

        except Exception as e:
            self.display.show_error(f"Error validating environment: {e}")

    async def environment_templates(self):
        """Show available environment templates."""
        try:
            templates = await self._get_environment_templates()

            if not templates:
                self.display.show_warning("No environment templates found")
                return

            # Display templates
            table_data = []
            for template_name, template_data in templates.items():
                description = template_data.get('description', 'No description')
                variables = len(template_data.get('variables', {}))
                table_data.append([template_name, description, str(variables)])

            self.display.show_table(
                "Environment Templates",
                ["Template", "Description", "Variables"],
                table_data
            )

            # Allow template application
            template_choice = await self.get_user_input("Enter template name to apply (or press Enter to skip)")
            if template_choice and template_choice in templates:
                await self._apply_environment_template(templates[template_choice])

        except Exception as e:
            self.display.show_error(f"Error showing environment templates: {e}")

    async def export_environment_variables(self):
        """Export environment variables to file."""
        try:
            export_path = await self.get_user_input("Export file path", default="./env_export.json")
            if not export_path:
                return

            env_vars = await self._get_relevant_env_vars()

            with open(export_path, 'w') as f:
                json.dump(env_vars, f, indent=2)

            self.display.show_success(f"Environment variables exported to {export_path}")

        except Exception as e:
            self.display.show_error(f"Error exporting environment variables: {e}")

    async def _get_relevant_env_vars(self) -> Dict[str, Tuple[str, str]]:
        """Get relevant environment variables with their sources."""
        relevant_patterns = [
            r'^[A-Z_]+_URL$',      # Service URLs
            r'^[A-Z_]+_HOST$',     # Host settings
            r'^[A-Z_]+_PORT$',     # Port settings
            r'^ENVIRONMENT$',      # Environment setting
            r'^DEBUG$',            # Debug settings
            r'^LOG_',              # Logging settings
            r'^REDIS_',            # Redis settings
            r'^DB_',               # Database settings
            r'^AWS_',              # AWS settings
            r'^OPENAI_',           # OpenAI settings
            r'^ANTHROPIC_',        # Anthropic settings
        ]

        env_vars = {}
        for key, value in os.environ.items():
            for pattern in relevant_patterns:
                if re.match(pattern, key):
                    env_vars[key] = (value, "environment")
                    break

        # Also check .env files
        env_files = await self._find_env_files()
        for env_file in env_files:
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                if key not in env_vars:  # Don't override environment variables
                                    env_vars[key] = (value.strip(), f"file: {env_file}")
            except Exception:
                continue

        return dict(sorted(env_vars.items()))

    async def _mask_sensitive_values(self, env_vars: Dict[str, Tuple[str, str]]) -> Dict[str, Tuple[str, str]]:
        """Mask sensitive values in environment variables."""
        sensitive_patterns = [
            r'PASSWORD',
            r'SECRET',
            r'KEY',
            r'TOKEN',
            r'CREDENTIALS'
        ]

        masked_vars = {}
        for var_name, (value, source) in env_vars.items():
            is_sensitive = any(pattern in var_name.upper() for pattern in sensitive_patterns)

            if is_sensitive and len(value) > 8:
                masked_value = value[:4] + "****" + value[-4:]
            else:
                masked_value = value

            masked_vars[var_name] = (masked_value, source)

        return masked_vars

    async def _find_env_files(self) -> List[str]:
        """Find environment files in the project."""
        env_files = []

        # Common env file locations
        search_paths = [
            Path(".env"),
            Path("config/.env"),
            Path("config/.env.local"),
            Path("config/.env.development"),
            Path("config/.env.test"),
            Path("config/.env.production"),
        ]

        for env_file in search_paths:
            if env_file.exists():
                env_files.append(str(env_file))

        return env_files

    async def _validate_environment_variables(self) -> Dict[str, Tuple[str, str]]:
        """Validate environment variables."""
        env_vars = await self._get_relevant_env_vars()
        validation_results = {}

        for var_name, (value, source) in env_vars.items():
            # Basic validation rules
            if not value:
                validation_results[var_name] = ("warning", "Empty value")
            elif var_name.endswith('_URL') and not value.startswith(('http://', 'https://')):
                validation_results[var_name] = ("warning", "URL should start with http:// or https://")
            elif var_name.endswith('_PORT') and not value.isdigit():
                validation_results[var_name] = ("invalid", "Port must be a number")
            elif var_name.endswith('_HOST') and not value:
                validation_results[var_name] = ("warning", "Host should not be empty")
            else:
                validation_results[var_name] = ("valid", "OK")

        return validation_results

    async def _get_environment_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available environment templates."""
        return {
            "development": {
                "description": "Development environment settings",
                "variables": {
                    "ENVIRONMENT": "development",
                    "DEBUG": "true",
                    "LOG_LEVEL": "DEBUG"
                }
            },
            "production": {
                "description": "Production environment settings",
                "variables": {
                    "ENVIRONMENT": "production",
                    "DEBUG": "false",
                    "LOG_LEVEL": "INFO"
                }
            },
            "testing": {
                "description": "Testing environment settings",
                "variables": {
                    "ENVIRONMENT": "testing",
                    "DEBUG": "true",
                    "LOG_LEVEL": "DEBUG"
                }
            }
        }

    async def _apply_environment_template(self, template: Dict[str, Any]):
        """Apply an environment template."""
        variables = template.get('variables', {})

        if not variables:
            self.display.show_warning("No variables in template")
            return

        applied_count = 0
        for var_name, var_value in variables.items():
            if var_name not in os.environ:  # Don't override existing
                os.environ[var_name] = var_value
                applied_count += 1

        self.display.show_success(f"Applied {applied_count} variables from template")

    async def _save_to_env_file(self, var_name: str, var_value: str):
        """Save environment variable to .env file."""
        env_file = Path(".env")

        # Read existing content
        existing_lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                existing_lines = f.readlines()

        # Check if variable already exists
        var_exists = False
        for i, line in enumerate(existing_lines):
            if line.strip().startswith(f"{var_name}="):
                existing_lines[i] = f"{var_name}={var_value}\n"
                var_exists = True
                break

        if not var_exists:
            existing_lines.append(f"{var_name}={var_value}\n")

        # Write back
        with open(env_file, 'w') as f:
            f.writelines(existing_lines)

    async def _remove_from_env_file(self, var_name: str):
        """Remove environment variable from .env file."""
        env_file = Path(".env")

        if not env_file.exists():
            return

        # Read existing content
        with open(env_file, 'r') as f:
            lines = f.readlines()

        # Remove the variable
        filtered_lines = [line for line in lines if not line.strip().startswith(f"{var_name}=")]

        # Write back
        with open(env_file, 'w') as f:
            f.writelines(filtered_lines)
