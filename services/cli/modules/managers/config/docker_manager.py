"""Docker Configuration Manager for CLI operations."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import json

from ...base.base_manager import BaseManager
from ...formatters.display_utils import DisplayManager


class DockerManager(BaseManager):
    """Manager for Docker configuration operations."""

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return the main menu items for Docker operations."""
        return [
            ("1", "View Docker Compose Configuration"),
            ("2", "Validate Docker Compose Files"),
            ("3", "Check Docker Service Health"),
            ("4", "Docker Environment Variables")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle a menu choice. Return True to continue, False to exit."""
        if choice == "1":
            await self.view_docker_compose_configuration()
        elif choice == "2":
            await self.validate_docker_compose_files()
        elif choice == "3":
            await self.check_docker_service_health()
        elif choice == "4":
            await self.docker_environment_variables()
        else:
            self.display.show_error("Invalid option. Please try again.")
        return True

    async def view_docker_compose_configuration(self):
        """View Docker Compose configuration."""
        try:
            compose_files = await self._find_docker_compose_files()

            if not compose_files:
                self.display.show_warning("No Docker Compose files found")
                return

            # Show available compose files
            file_options = []
            for i, compose_file in enumerate(compose_files, 1):
                file_options.append((str(i), f"{compose_file.name} ({compose_file.parent})"))

            choice = await self.get_user_input("Select Docker Compose file to view")
            if choice and choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(compose_files):
                    await self._display_compose_file(compose_files[index])

        except Exception as e:
            self.display.show_error(f"Error viewing Docker Compose configuration: {e}")

    async def validate_docker_compose_files(self):
        """Validate Docker Compose file syntax."""
        try:
            compose_files = await self._find_docker_compose_files()
            validation_results = []

            with self.display.show_progress("Validating Docker Compose files") as progress:
                for compose_file in compose_files:
                    result = await self._validate_compose_file(compose_file)
                    validation_results.append(result)

            # Display results
            valid_count = sum(1 for r in validation_results if r['valid'])
            total_count = len(validation_results)

            table_data = []
            for result in validation_results:
                status = "✅ Valid" if result['valid'] else "❌ Invalid"
                message = "OK" if result['valid'] else result.get('error', 'Unknown error')
                table_data.append([result['file'], status, message])

            self.display.show_table(
                f"Docker Compose Validation ({valid_count}/{total_count} valid)",
                ["File", "Status", "Message"],
                table_data
            )

            if valid_count == total_count:
                self.display.show_success("All Docker Compose files are valid!")
            else:
                self.display.show_error(f"{total_count - valid_count} Docker Compose files have validation errors")

        except Exception as e:
            self.display.show_error(f"Error validating Docker Compose files: {e}")

    async def service_dependencies_analysis(self):
        """Analyze service dependencies in Docker Compose files."""
        try:
            compose_files = await self._find_docker_compose_files()
            all_dependencies = {}

            for compose_file in compose_files:
                deps = await self._analyze_service_dependencies(compose_file)
                all_dependencies.update(deps)

            if not all_dependencies:
                self.display.show_warning("No service dependencies found")
                return

            # Display dependency graph
            await self._display_dependency_graph(all_dependencies)

        except Exception as e:
            self.display.show_error(f"Error analyzing service dependencies: {e}")

    async def environment_variable_substitution(self):
        """Analyze environment variable substitution in compose files."""
        try:
            compose_files = await self._find_docker_compose_files()
            substitution_issues = []

            for compose_file in compose_files:
                issues = await self._check_environment_substitution(compose_file)
                substitution_issues.extend(issues)

            if not substitution_issues:
                self.display.show_success("No environment variable substitution issues found!")
                return

            # Display issues
            table_data = []
            for issue in substitution_issues:
                table_data.append([issue['file'], issue['variable'], issue['issue']])

            self.display.show_table(
                "Environment Variable Substitution Issues",
                ["File", "Variable", "Issue"],
                table_data
            )

        except Exception as e:
            self.display.show_error(f"Error analyzing environment substitution: {e}")

    async def generate_deployment_config(self):
        """Generate deployment configuration from compose files."""
        try:
            compose_files = await self._find_docker_compose_files()

            if not compose_files:
                self.display.show_warning("No Docker Compose files found")
                return

            # Generate deployment config
            deployment_config = await self._generate_deployment_configuration(compose_files)

            # Show or save the config
            config_yaml = yaml.dump(deployment_config, default_flow_style=False, indent=2)

            self.display.show_panel(config_yaml, "Generated Deployment Configuration")

            if await self.confirm_action("Save deployment configuration to file?"):
                output_path = await self.get_user_input("Output file path", default="./deployment-config.yaml")
                if output_path:
                    with open(output_path, 'w') as f:
                        f.write(config_yaml)
                    self.display.show_success(f"Deployment configuration saved to {output_path}")

        except Exception as e:
            self.display.show_error(f"Error generating deployment configuration: {e}")

    async def _find_docker_compose_files(self) -> List[Path]:
        """Find Docker Compose files in the project."""
        compose_files = []

        # Common compose file names
        compose_names = [
            'docker-compose.yml',
            'docker-compose.yaml',
            'docker-compose.dev.yml',
            'docker-compose.prod.yml',
            'docker-compose.override.yml'
        ]

        # Search in common locations
        search_paths = [Path('.'), Path('config'), Path('infrastructure')]

        for search_path in search_paths:
            if search_path.exists():
                for compose_name in compose_names:
                    compose_file = search_path / compose_name
                    if compose_file.exists():
                        compose_files.append(compose_file)

        return list(set(compose_files))  # Remove duplicates

    async def _validate_compose_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a Docker Compose file."""
        result = {
            'file': str(file_path),
            'valid': False,
            'error': None
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                compose_data = yaml.safe_load(f)

            # Basic validation - check for required sections
            if not isinstance(compose_data, dict):
                result['error'] = "Invalid YAML structure"
                return result

            # Check for version (though it's now optional in newer versions)
            if 'version' in compose_data:
                version = compose_data['version']
                if not isinstance(version, (str, int, float)):
                    result['error'] = f"Invalid version format: {version}"
                    return result

            # Check for services section
            if 'services' not in compose_data:
                result['error'] = "Missing 'services' section"
                return result

            services = compose_data['services']
            if not isinstance(services, dict):
                result['error'] = "'services' section must be a dictionary"
                return result

            # Validate each service has required fields
            for service_name, service_config in services.items():
                if not isinstance(service_config, dict):
                    result['error'] = f"Service '{service_name}' configuration must be a dictionary"
                    return result

            result['valid'] = True

        except yaml.YAMLError as e:
            result['error'] = f"YAML syntax error: {e}"
        except Exception as e:
            result['error'] = f"Validation error: {e}"

        return result

    async def _display_compose_file(self, file_path: Path):
        """Display Docker Compose file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Try to format as YAML
            try:
                compose_data = yaml.safe_load(content)
                formatted_content = yaml.dump(compose_data, default_flow_style=False, indent=2)
            except:
                formatted_content = content

            self.display.show_panel(formatted_content, f"Docker Compose: {file_path.name}")

        except Exception as e:
            self.display.show_error(f"Error displaying compose file: {e}")

    async def _analyze_service_dependencies(self, compose_file: Path) -> Dict[str, List[str]]:
        """Analyze service dependencies in a compose file."""
        dependencies = {}

        try:
            with open(compose_file, 'r', encoding='utf-8') as f:
                compose_data = yaml.safe_load(f)

            services = compose_data.get('services', {})

            for service_name, service_config in services.items():
                if isinstance(service_config, dict):
                    # Check depends_on
                    depends_on = service_config.get('depends_on', [])
                    if isinstance(depends_on, list):
                        dependencies[service_name] = depends_on
                    elif isinstance(depends_on, dict):
                        dependencies[service_name] = list(depends_on.keys())
                    else:
                        dependencies[service_name] = []

        except Exception as e:
            self.display.show_error(f"Error analyzing dependencies in {compose_file}: {e}")

        return dependencies

    async def _display_dependency_graph(self, dependencies: Dict[str, List[str]]):
        """Display service dependency graph."""
        if not dependencies:
            self.display.show_warning("No dependencies to display")
            return

        table_data = []
        for service, deps in dependencies.items():
            deps_str = ", ".join(deps) if deps else "None"
            table_data.append([service, deps_str])

        self.display.show_table(
            "Service Dependency Graph",
            ["Service", "Dependencies"],
            table_data
        )

    async def _check_environment_substitution(self, compose_file: Path) -> List[Dict[str, Any]]:
        """Check environment variable substitution in compose file."""
        issues = []

        try:
            with open(compose_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find environment variable references
            import re
            env_refs = re.findall(r'\$\{([^}]+)\}', content)

            for env_ref in env_refs:
                var_name = env_ref.split(':')[0]  # Handle ${VAR:default} format
                if var_name not in os.environ:
                    issues.append({
                        'file': str(compose_file),
                        'variable': var_name,
                        'issue': 'Referenced environment variable not set'
                    })

        except Exception as e:
            issues.append({
                'file': str(compose_file),
                'variable': 'unknown',
                'issue': f'Error checking environment substitution: {e}'
            })

        return issues

    async def _generate_deployment_configuration(self, compose_files: List[Path]) -> Dict[str, Any]:
        """Generate deployment configuration from compose files."""
        deployment_config = {
            'version': '1.0',
            'services': {},
            'networks': {},
            'volumes': {}
        }

        for compose_file in compose_files:
            try:
                with open(compose_file, 'r', encoding='utf-8') as f:
                    compose_data = yaml.safe_load(f)

                # Extract services
                services = compose_data.get('services', {})
                for service_name, service_config in services.items():
                    if service_name not in deployment_config['services']:
                        deployment_config['services'][service_name] = {
                            'image': service_config.get('image', ''),
                            'replicas': 1,
                            'environment': service_config.get('environment', {}),
                            'ports': service_config.get('ports', []),
                            'source_file': str(compose_file)
                        }

                # Extract networks and volumes
                networks = compose_data.get('networks', {})
                volumes = compose_data.get('volumes', {})

                deployment_config['networks'].update(networks)
                deployment_config['volumes'].update(volumes)

            except Exception as e:
                self.display.show_warning(f"Skipping {compose_file} due to error: {e}")

        return deployment_config
