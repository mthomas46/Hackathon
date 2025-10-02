"""Core Meta-Orchestrator implementation"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import yaml
import json

from config.settings import Settings
from pathlib import Path
from models.service import ServiceStatus, ServiceInfo, ServiceAction
from docker.manager import DockerManager
from utils.exceptions import OrchestrationError

logger = logging.getLogger(__name__)


class MetaOrchestrator:
    """Manages the lifecycle and configuration of services in the ecosystem"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.docker_manager = DockerManager(settings.docker)
        self.services: Dict[str, ServiceInfo] = {}
        self.compose_config: Optional[Dict[str, Any]] = None

    async def initialize(self) -> None:
        """Initialize the meta-orchestrator"""
        try:
            logger.info("🔧 Initializing Meta-Orchestrator")

            # Load Docker Compose configuration
            await self._load_compose_config()

            # Initialize Docker manager
            await self.docker_manager.initialize()

            # Discover existing services
            await self._discover_services()

            logger.info(f"✅ Meta-Orchestrator initialized with {len(self.services)} services")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Meta-Orchestrator: {e}")
            raise

    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            await self.docker_manager.cleanup()
            logger.info("🧹 Meta-Orchestrator cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

    async def _load_compose_config(self) -> None:
        """Load Docker Compose configuration"""
        try:
            workspace_path = Path(self.settings.workspace_path)
            compose_file = workspace_path / self.settings.compose_file
            print(f"🔍 Looking for compose file at: {compose_file}")
            print(f"📂 Workspace path: {workspace_path}")
            print(f"📄 Compose file setting: {self.settings.compose_file}")

            if compose_file.exists():
                print(f"✅ Compose file exists at {compose_file}")
                with open(compose_file, 'r') as f:
                    self.compose_config = yaml.safe_load(f)
                print(f"📄 Loaded compose config with {len(self.compose_config.get('services', {}))} services")
                # Log first few service names for debugging
                services = list(self.compose_config.get('services', {}).keys())[:5]
                print(f"🔧 Found services: {services}")
            else:
                print(f"❌ Compose file not found: {compose_file}")
                print(f"📂 Current directory contents: {list(workspace_path.iterdir()) if workspace_path.exists() else 'workspace path does not exist'}")
        except Exception as e:
            print(f"❌ Failed to load compose config: {e}")
            print(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            raise

    async def _discover_services(self) -> None:
        """Discover existing services from Docker and compose config"""
        try:
            print("🔍 Starting service discovery...")
            # Get running containers
            running_containers = await self.docker_manager.list_containers()
            print(f"🐳 Found {len(running_containers)} running containers")

            # Create service info for each service in compose config
            if self.compose_config and 'services' in self.compose_config:
                print(f"📋 Processing {len(self.compose_config['services'])} services from compose config")
                for service_name, service_config in self.compose_config['services'].items():
                    # Find corresponding container
                    container = next(
                        (c for c in running_containers if c.name.startswith(service_name)),
                        None
                    )

                    # Parse environment variables
                    env_vars = service_config.get('environment', {})
                    if isinstance(env_vars, list):
                        # Convert list format ['KEY=value', ...] to dict
                        env_dict = {}
                        for env_item in env_vars:
                            if isinstance(env_item, str) and '=' in env_item:
                                key, value = env_item.split('=', 1)
                                env_dict[key] = value
                        env_vars = env_dict

                    # Parse depends_on
                    depends = service_config.get('depends_on', [])
                    if isinstance(depends, dict):
                        # Convert dict format to list
                        depends = list(depends.keys())

                    service_info = ServiceInfo(
                        name=service_name,
                        status=ServiceStatus.RUNNING if container else ServiceStatus.STOPPED,
                        config=service_config,
                        container_id=container.id if container else None,
                        ports=service_config.get('ports', []),
                        environment=env_vars,
                        depends_on=depends
                    )

                    self.services[service_name] = service_info
                    print(f"✅ Added service: {service_name} (status: {service_info.status})")

            print(f"🔍 Service discovery complete. Found {len(self.services)} services")
            if self.services:
                service_names = list(self.services.keys())[:10]  # Show first 10
                print(f"📋 Discovered services: {service_names}")

        except Exception as e:
            print(f"❌ Failed to discover services: {e}")
            print(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            raise

    async def start_service(self, service_name: str, profile: str = "all") -> ServiceAction:
        """Start a specific service"""
        try:
            if service_name not in self.services:
                raise OrchestrationError(f"Service '{service_name}' not found")

            service = self.services[service_name]

            # Check dependencies
            await self._check_dependencies(service_name)

            # Start the service using Docker Compose
            result = await self.docker_manager.compose_up([service_name], profile=profile)

            if result.success:
                service.status = ServiceStatus.RUNNING
                # Update container ID
                containers = await self.docker_manager.list_containers()
                container = next((c for c in containers if c.name.startswith(service_name)), None)
                if container:
                    service.container_id = container.id

            return ServiceAction(
                service_name=service_name,
                action="start",
                success=result.success,
                message=result.message,
                timestamp=asyncio.get_event_loop().time()
            )

        except Exception as e:
            logger.error(f"❌ Failed to start service {service_name}: {e}")
            return ServiceAction(
                service_name=service_name,
                action="start",
                success=False,
                message=str(e),
                timestamp=asyncio.get_event_loop().time()
            )

    async def stop_service(self, service_name: str) -> ServiceAction:
        """Stop a specific service"""
        try:
            if service_name not in self.services:
                raise OrchestrationError(f"Service '{service_name}' not found")

            service = self.services[service_name]

            # Stop the service using Docker Compose
            result = await self.docker_manager.compose_down([service_name])

            if result.success:
                service.status = ServiceStatus.STOPPED
                service.container_id = None

            return ServiceAction(
                service_name=service_name,
                action="stop",
                success=result.success,
                message=result.message,
                timestamp=asyncio.get_event_loop().time()
            )

        except Exception as e:
            logger.error(f"❌ Failed to stop service {service_name}: {e}")
            return ServiceAction(
                service_name=service_name,
                action="stop",
                success=False,
                message=str(e),
                timestamp=asyncio.get_event_loop().time()
            )

    async def restart_service(self, service_name: str) -> ServiceAction:
        """Restart a specific service"""
        try:
            stop_result = await self.stop_service(service_name)
            if not stop_result.success:
                return ServiceAction(
                    service_name=service_name,
                    action="restart",
                    success=False,
                    message=f"Failed to stop service: {stop_result.message}",
                    timestamp=asyncio.get_event_loop().time()
                )

            start_result = await self.start_service(service_name)
            return ServiceAction(
                service_name=service_name,
                action="restart",
                success=start_result.success,
                message=f"Restart completed: {start_result.message}",
                timestamp=asyncio.get_event_loop().time()
            )

        except Exception as e:
            logger.error(f"❌ Failed to restart service {service_name}: {e}")
            return ServiceAction(
                service_name=service_name,
                action="restart",
                success=False,
                message=str(e),
                timestamp=asyncio.get_event_loop().time()
            )

    async def update_service_config(self, service_name: str, config_updates: Dict[str, Any]) -> ServiceAction:
        """Update configuration for a service"""
        try:
            if service_name not in self.services:
                raise OrchestrationError(f"Service '{service_name}' not found")

            service = self.services[service_name]

            # Validate config updates (basic validation)
            await self._validate_config_updates(service_name, config_updates)

            # Update the service configuration
            # This is a simplified implementation - in practice, you'd need to:
            # 1. Update the compose file
            # 2. Recreate the container with new config
            # 3. Handle environment variables, volumes, etc.

            # For now, just update our in-memory config
            service.config.update(config_updates)

            return ServiceAction(
                service_name=service_name,
                action="update_config",
                success=True,
                message=f"Configuration updated for {service_name}",
                timestamp=asyncio.get_event_loop().time()
            )

        except Exception as e:
            logger.error(f"❌ Failed to update config for {service_name}: {e}")
            return ServiceAction(
                service_name=service_name,
                action="update_config",
                success=False,
                message=str(e),
                timestamp=asyncio.get_event_loop().time()
            )

    async def _check_dependencies(self, service_name: str) -> None:
        """Check if service dependencies are running"""
        service = self.services[service_name]

        for dep in service.depends_on:
            if isinstance(dep, str):
                dep_name = dep
            elif isinstance(dep, dict):
                dep_name = list(dep.keys())[0]
            else:
                continue

            if dep_name in self.services:
                dep_service = self.services[dep_name]
                if dep_service.status != ServiceStatus.RUNNING:
                    logger.warning(f"⚠️ Dependency {dep_name} is not running for {service_name}")
                    # Could auto-start dependencies here

    async def _validate_config_updates(self, service_name: str, updates: Dict[str, Any]) -> None:
        """Validate configuration updates"""
        # Basic validation - ensure no critical config is removed
        service = self.services[service_name]
        current_config = service.config

        # Check for required fields
        required_fields = ['image', 'ports']  # Add more as needed
        for field in required_fields:
            if field in current_config and field not in updates:
                continue  # Field exists and not being removed
            elif field in updates:
                continue  # Field being added
            else:
                raise OrchestrationError(f"Cannot remove required field '{field}' from {service_name}")

    async def get_service_status(self, service_name: Optional[str] = None) -> List[ServiceInfo]:
        """Get status of services"""
        if service_name:
            service = self.services.get(service_name)
            return [service] if service else []

        # Refresh status from Docker
        await self._discover_services()
        return list(self.services.values())

    async def get_service_logs(self, service_name: str, lines: int = 100) -> str:
        """Get logs for a service"""
        try:
            return await self.docker_manager.get_container_logs(service_name, lines)
        except Exception as e:
            logger.error(f"❌ Failed to get logs for {service_name}: {e}")
            return f"Error retrieving logs: {e}"
