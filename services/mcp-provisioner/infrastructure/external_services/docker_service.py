"""Docker Service Implementation - Infrastructure Layer.

Handles Docker container lifecycle operations using Docker SDK.
"""

import logging
from typing import Dict, Any, Optional
import docker
from docker.errors import DockerException, NotFound, APIError

from services.mcp_provisioner.domain.entities.mcp_instance import MCPInstance
from services.mcp_provisioner.infrastructure.config.settings import Settings
from services.mcp_provisioner.infrastructure.external_services.port_allocator import PortAllocator


logger = logging.getLogger(__name__)


class DockerServiceError(Exception):
    """Base exception for Docker service errors."""
    pass


class ContainerStartError(DockerServiceError):
    """Raised when container fails to start."""
    pass


class ContainerStopError(DockerServiceError):
    """Raised when container fails to stop."""
    pass


class DockerServiceImpl:
    """
    Docker service implementation using Docker SDK.
    
    Manages MCP container lifecycle: create, start, stop, remove.
    """
    
    def __init__(self, settings: Settings, port_allocator: PortAllocator):
        """
        Initialize Docker service.
        
        Args:
            settings: Application settings
            port_allocator: Port allocation service
        """
        self.settings = settings
        self.port_allocator = port_allocator
        
        try:
            self.client = docker.DockerClient(base_url=settings.docker_socket)
            logger.info(f"Docker client initialized: {settings.docker_socket}")
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise DockerServiceError(f"Docker initialization failed: {e}")
    
    async def start_container(self, instance: MCPInstance) -> Dict[str, Any]:
        """
        Start a Docker container for an MCP instance.
        
        Args:
            instance: MCP instance to start
        
        Returns:
            Dict with container_id, ip_address, external_port
        
        Raises:
            ContainerStartError: If container fails to start
        """
        try:
            logger.info(f"Starting container for MCP: {instance.id}")
            
            # Allocate external port
            external_port = self.port_allocator.allocate_port()
            
            # Build container configuration
            container_config = self._build_container_config(instance, external_port)
            
            # Create and start container
            container = self.client.containers.run(
                image=instance.mcp_config.image_name,
                name=f"mcp-{instance.client_id}-{instance.id[:8]}",
                detach=True,
                network=self.settings.docker_network,
                ports={f"{instance.mcp_config.api_port}/tcp": external_port},
                environment=container_config["environment"],
                volumes=container_config["volumes"],
                **container_config["resource_limits"]
            )
            
            # Get container info
            container.reload()
            network_settings = container.attrs["NetworkSettings"]
            ip_address = network_settings["Networks"][self.settings.docker_network]["IPAddress"]
            
            logger.info(
                f"Container started: {container.id[:12]} "
                f"(IP: {ip_address}, Port: {external_port})"
            )
            
            return {
                "container_id": container.id,
                "ip_address": ip_address,
                "external_port": external_port,
            }
            
        except docker.errors.ImageNotFound as e:
            logger.error(f"Docker image not found: {instance.mcp_config.image_name}")
            raise ContainerStartError(f"Image not found: {instance.mcp_config.image_name}")
        
        except docker.errors.APIError as e:
            logger.error(f"Docker API error starting container: {e}")
            raise ContainerStartError(f"Failed to start container: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error starting container: {e}", exc_info=True)
            raise ContainerStartError(f"Container start failed: {e}")
    
    async def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """
        Stop a running Docker container.
        
        Args:
            container_id: Container ID to stop
            timeout: Timeout in seconds before forceful kill
        
        Raises:
            ContainerStopError: If container fails to stop
        """
        try:
            logger.info(f"Stopping container: {container_id[:12]}")
            
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            
            logger.info(f"Container stopped: {container_id[:12]}")
            
        except docker.errors.NotFound:
            logger.warning(f"Container not found: {container_id[:12]}")
            # Not an error - container may have already been removed
        
        except docker.errors.APIError as e:
            logger.error(f"Docker API error stopping container: {e}")
            raise ContainerStopError(f"Failed to stop container: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error stopping container: {e}", exc_info=True)
            raise ContainerStopError(f"Container stop failed: {e}")
    
    async def remove_container(self, container_id: str, force: bool = True) -> None:
        """
        Remove a Docker container.
        
        Args:
            container_id: Container ID to remove
            force: Force removal even if running
        
        Raises:
            DockerServiceError: If container fails to be removed
        """
        try:
            logger.info(f"Removing container: {container_id[:12]}")
            
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            
            logger.info(f"Container removed: {container_id[:12]}")
            
        except docker.errors.NotFound:
            logger.warning(f"Container not found: {container_id[:12]}")
            # Not an error - already removed
        
        except docker.errors.APIError as e:
            logger.error(f"Docker API error removing container: {e}")
            raise DockerServiceError(f"Failed to remove container: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error removing container: {e}", exc_info=True)
            raise DockerServiceError(f"Container removal failed: {e}")
    
    async def get_container_status(self, container_id: str) -> Optional[str]:
        """
        Get container status.
        
        Args:
            container_id: Container ID
        
        Returns:
            Status string or None if not found
        """
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except docker.errors.NotFound:
            return None
        except Exception as e:
            logger.error(f"Error getting container status: {e}")
            return None
    
    def _build_container_config(
        self, 
        instance: MCPInstance, 
        external_port: int
    ) -> Dict[str, Any]:
        """
        Build container configuration from MCP instance.
        
        Args:
            instance: MCP instance
            external_port: Allocated external port
        
        Returns:
            Container configuration dict
        """
        # Base environment variables
        environment = {
            "MCP_CLIENT_ID": instance.client_id,
            "MCP_INSTANCE_ID": instance.id,
            "MCP_API_PORT": str(instance.mcp_config.api_port),
            "CHROMADB_PATH": instance.mcp_config.chromadb_path,
            "NEO4J_URI": instance.mcp_config.neo4j_uri,
            **instance.mcp_config.environment_vars,
        }
        
        # Volumes (if specified)
        volumes = instance.mcp_config.volumes or {}
        
        # Resource limits
        resource_limits = instance.mcp_config.resource_limits or {}
        
        return {
            "environment": environment,
            "volumes": volumes,
            "resource_limits": resource_limits,
        }
    
    def close(self) -> None:
        """Close Docker client connection."""
        try:
            self.client.close()
            logger.info("Docker client closed")
        except Exception as e:
            logger.error(f"Error closing Docker client: {e}")

