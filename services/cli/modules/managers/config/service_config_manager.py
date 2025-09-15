"""Service Configuration Manager for CLI operations."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import yaml
import os

from ...base.base_manager import BaseManager
from ...utils.api_utils import APIClient
from ...formatters.display_utils import DisplayManager


class ServiceConfigManager(BaseManager):
    """Manager for service configuration operations."""

    async def list_service_config_files(self, service: str) -> List[Path]:
        """List all configuration files for a service."""
        config_files = []

        # Common config locations
        search_paths = [
            Path("services") / service,
            Path("services") / service / "config",
            Path("config"),
            Path("infrastructure"),
        ]

        patterns = [
            f"{service}.yaml",
            f"{service}.yml",
            f"{service}.json",
            "config.yaml",
            "config.yml",
            "application.yaml",
            "application.yml",
        ]

        for search_path in search_paths:
            if search_path.exists():
                for pattern in patterns:
                    config_files.extend(search_path.glob(f"**/{pattern}"))

        return list(set(config_files))  # Remove duplicates

    async def show_configuration_hierarchy(self, service: str):
        """Show the configuration hierarchy for a service."""
        try:
            hierarchy = await self._build_config_hierarchy(service)
            merged_config = await self._merge_config_hierarchy(hierarchy)

            if merged_config:
                self.display.show_dict(merged_config, f"Configuration Hierarchy for {service}")
            else:
                self.display.show_warning(f"No configuration found for service: {service}")

        except Exception as e:
            self.display.show_error(f"Error showing configuration hierarchy: {e}")

    async def view_service_configuration(self, service: str):
        """View configuration for a specific service."""
        try:
            config_files = await self.list_service_config_files(service)

            if not config_files:
                self.display.show_warning(f"No configuration files found for service: {service}")
                return

            # Show available config files
            file_options = []
            for i, config_file in enumerate(config_files, 1):
                file_options.append((str(i), f"{config_file.name} ({config_file.parent})"))

            choice = await self.get_user_input("Select configuration file to view")
            if choice and choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(config_files):
                    await self._display_config_file(str(config_files[index]))

        except Exception as e:
            self.display.show_error(f"Error viewing service configuration: {e}")

    async def edit_service_configuration(self, service: str):
        """Edit configuration for a specific service."""
        try:
            config_files = await self.list_service_config_files(service)

            if not config_files:
                self.display.show_warning(f"No configuration files found for service: {service}")
                return

            # Show available config files
            file_options = []
            for i, config_file in enumerate(config_files, 1):
                file_options.append((str(i), f"{config_file.name} ({config_file.parent})"))

            choice = await self.get_user_input("Select configuration file to edit")
            if choice and choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(config_files):
                    await self._edit_config_file(str(config_files[index]))

        except Exception as e:
            self.display.show_error(f"Error editing service configuration: {e}")

    async def _display_config_file(self, file_path: str):
        """Display the contents of a configuration file."""
        try:
            content = await self._read_config_file(file_path)
            if content:
                file_name = Path(file_path).name
                self.display.show_panel(content, f"Configuration File: {file_name}")
            else:
                self.display.show_warning(f"Could not read file: {file_path}")

        except Exception as e:
            self.display.show_error(f"Error displaying config file: {e}")

    async def _edit_config_file(self, file_path: str):
        """Edit a configuration file."""
        try:
            current_content = await self._read_config_file(file_path)
            if not current_content:
                self.display.show_warning(f"Could not read file: {file_path}")
                return

            file_name = Path(file_path).name
            self.display.show_panel(current_content, f"Current Content: {file_name}")

            if await self.confirm_action("Do you want to edit this file?"):
                # For now, just show a message about editing
                # In a real implementation, this would open an editor
                self.display.show_info("File editing would open in your default editor")
                self.display.show_info(f"File path: {file_path}")

        except Exception as e:
            self.display.show_error(f"Error editing config file: {e}")

    def _find_service_config_files(self, service: str) -> List[Path]:
        """Find configuration files for a service."""
        config_files = []

        # Service-specific config
        service_config = Path("services") / service / "config.yaml"
        if service_config.exists():
            config_files.append(service_config)

        # Service config file
        service_file = Path("services") / service / f"{service}.yaml"
        if service_file.exists():
            config_files.append(service_file)

        # Global config files
        global_configs = [
            Path("config") / "app.yaml",
            Path("config") / "config.yaml",
            Path("config") / f"{service}.yaml"
        ]

        for config_file in global_configs:
            if config_file.exists():
                config_files.append(config_file)

        return config_files

    async def _read_config_file(self, file_path: str) -> Optional[str]:
        """Read and format a configuration file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Try to format as YAML/JSON if possible
            try:
                if file_path.endswith(('.yaml', '.yml')):
                    data = yaml.safe_load(content)
                    return yaml.dump(data, default_flow_style=False, indent=2)
                elif file_path.endswith('.json'):
                    data = json.loads(content)
                    return json.dumps(data, indent=2)
            except:
                pass  # Fall back to raw content

            return content

        except Exception as e:
            self.display.show_error(f"Error reading file {file_path}: {e}")
            return None

    async def _build_config_hierarchy(self, service: str) -> Dict[str, List[str]]:
        """Build the configuration hierarchy for a service."""
        hierarchy = {
            "service_specific": [],
            "service_level": [],
            "global_level": [],
            "environment_overrides": []
        }

        # Service-specific configs
        service_dir = Path("services") / service
        if service_dir.exists():
            for config_file in service_dir.glob("*.yaml"):
                hierarchy["service_specific"].append(str(config_file))

        # Service-level configs
        service_config = Path("services") / service / "config.yaml"
        if service_config.exists():
            hierarchy["service_level"].append(str(service_config))

        # Global configs
        global_configs = [
            Path("config") / "app.yaml",
            Path("config") / "config.yaml"
        ]
        for config_file in global_configs:
            if config_file.exists():
                hierarchy["global_level"].append(str(config_file))

        # Environment overrides
        env_file = Path("config") / ".env"
        if env_file.exists():
            hierarchy["environment_overrides"].append(str(env_file))

        return hierarchy

    async def _merge_config_hierarchy(self, hierarchy: Dict[str, List[str]]) -> Optional[Dict[str, Any]]:
        """Merge configuration from hierarchy."""
        merged_config = {}

        # Process in order: service-specific -> service-level -> global -> env overrides
        for level in ["service_specific", "service_level", "global_level"]:
            for config_file in hierarchy[level]:
                try:
                    config_data = await self._load_config_file(config_file)
                    if config_data:
                        merged_config.update(config_data)
                except Exception:
                    continue  # Skip files that can't be loaded

        return merged_config if merged_config else None

    async def _load_config_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load configuration from file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            if file_path.endswith(('.yaml', '.yml')):
                return yaml.safe_load(content)
            elif file_path.endswith('.json'):
                return json.loads(content)
            else:
                return None

        except Exception:
            return None
