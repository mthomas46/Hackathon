"""
Docker Service Manager with Caching and Auto-Start Capabilities.

Provides infrastructure to:
- Detect Docker daemon status
- Cache container information
- Start/restart/redeploy services
- Handle unreachable services
"""

import subprocess
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class DockerService:
    """Docker service information."""
    name: str
    status: str  # running, stopped, not_found
    container_id: Optional[str] = None
    image: str = ""
    ports: Dict[str, str] = None
    healthy: bool = False
    last_checked: datetime = None
    
    def __post_init__(self):
        if self.ports is None:
            self.ports = {}
        if self.last_checked is None:
            self.last_checked = datetime.now()


class DockerManager:
    """Manages Docker services with caching and auto-start capabilities."""
    
    def __init__(self, cache_ttl_seconds: int = 30):
        """
        Initialize Docker manager.
        
        Args:
            cache_ttl_seconds: How long to cache container info before refreshing
        """
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self.service_cache: Dict[str, DockerService] = {}
        self.docker_available: Optional[bool] = None
        self.last_docker_check: Optional[datetime] = None
        
    def is_docker_running(self, force_check: bool = False) -> bool:
        """
        Check if Docker daemon is running.
        
        Args:
            force_check: Force check even if cached
            
        Returns:
            True if Docker daemon is accessible
        """
        # Use cache if available and recent
        if not force_check and self.last_docker_check:
            if datetime.now() - self.last_docker_check < timedelta(seconds=10):
                return self.docker_available
        
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5,
                text=True
            )
            self.docker_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.docker_available = False
        except Exception as e:
            logger.error(f"Error checking Docker status: {e}")
            self.docker_available = False
        
        self.last_docker_check = datetime.now()
        return self.docker_available
    
    def get_service_status(self, service_name: str, force_refresh: bool = False) -> DockerService:
        """
        Get status of a specific service.
        
        Args:
            service_name: Name of the Docker service/container
            force_refresh: Force refresh cache
            
        Returns:
            DockerService object with current status
        """
        # Check cache first
        if not force_refresh and service_name in self.service_cache:
            cached = self.service_cache[service_name]
            if datetime.now() - cached.last_checked < self.cache_ttl:
                return cached
        
        # Check if Docker is running
        if not self.is_docker_running():
            return DockerService(
                name=service_name,
                status="docker_unavailable"
            )
        
        # Get container status
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={service_name}", "--format", "json"],
                capture_output=True,
                timeout=10,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse first line (container found)
                container_info = json.loads(result.stdout.strip().split('\n')[0])
                
                service = DockerService(
                    name=service_name,
                    status="running" if container_info.get("State") == "running" else "stopped",
                    container_id=container_info.get("ID"),
                    image=container_info.get("Image", ""),
                    ports=self._parse_ports(container_info.get("Ports", "")),
                    healthy=container_info.get("State") == "running",
                    last_checked=datetime.now()
                )
            else:
                # Container not found
                service = DockerService(
                    name=service_name,
                    status="not_found",
                    last_checked=datetime.now()
                )
            
            # Update cache
            self.service_cache[service_name] = service
            return service
            
        except Exception as e:
            logger.error(f"Error getting service status for {service_name}: {e}")
            return DockerService(
                name=service_name,
                status="error",
                last_checked=datetime.now()
            )
    
    def start_service(self, service_name: str, compose_file: Optional[str] = None) -> Tuple[bool, str]:
        """
        Start a Docker service.
        
        Args:
            service_name: Name of the service
            compose_file: Optional docker-compose file path
            
        Returns:
            (success: bool, message: str)
        """
        if not self.is_docker_running():
            return False, "Docker daemon is not running. Please start Docker Desktop."
        
        try:
            # Try docker-compose first if file provided
            if compose_file:
                result = subprocess.run(
                    ["docker-compose", "-f", compose_file, "up", "-d", service_name],
                    capture_output=True,
                    timeout=120,
                    text=True
                )
            else:
                # Try to start existing container
                result = subprocess.run(
                    ["docker", "start", service_name],
                    capture_output=True,
                    timeout=30,
                    text=True
                )
            
            if result.returncode == 0:
                # Clear cache to force refresh
                if service_name in self.service_cache:
                    del self.service_cache[service_name]
                return True, f"Service {service_name} started successfully"
            else:
                error_msg = result.stderr or result.stdout
                return False, f"Failed to start {service_name}: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, f"Timeout while starting {service_name}"
        except Exception as e:
            return False, f"Error starting {service_name}: {str(e)}"
    
    def restart_service(self, service_name: str) -> Tuple[bool, str]:
        """
        Restart a Docker service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            (success: bool, message: str)
        """
        if not self.is_docker_running():
            return False, "Docker daemon is not running"
        
        try:
            result = subprocess.run(
                ["docker", "restart", service_name],
                capture_output=True,
                timeout=60,
                text=True
            )
            
            if result.returncode == 0:
                # Clear cache
                if service_name in self.service_cache:
                    del self.service_cache[service_name]
                return True, f"Service {service_name} restarted successfully"
            else:
                return False, f"Failed to restart: {result.stderr}"
                
        except Exception as e:
            return False, f"Error restarting: {str(e)}"
    
    def get_all_services(self, filter_prefix: Optional[str] = None) -> List[DockerService]:
        """
        Get status of all Docker services.
        
        Args:
            filter_prefix: Optional prefix to filter services (e.g., "ecosystem-")
            
        Returns:
            List of DockerService objects
        """
        if not self.is_docker_running():
            return []
        
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "json"],
                capture_output=True,
                timeout=10,
                text=True
            )
            
            if result.returncode != 0:
                return []
            
            services = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                try:
                    container = json.loads(line)
                    name = container.get("Names", "")
                    
                    # Apply filter if provided
                    if filter_prefix and not name.startswith(filter_prefix):
                        continue
                    
                    service = DockerService(
                        name=name,
                        status="running" if container.get("State") == "running" else "stopped",
                        container_id=container.get("ID"),
                        image=container.get("Image", ""),
                        ports=self._parse_ports(container.get("Ports", "")),
                        healthy=container.get("State") == "running",
                        last_checked=datetime.now()
                    )
                    services.append(service)
                    
                    # Update cache
                    self.service_cache[name] = service
                    
                except json.JSONDecodeError:
                    continue
            
            return services
            
        except Exception as e:
            logger.error(f"Error getting all services: {e}")
            return []
    
    def auto_start_service(self, service_name: str, compose_file: str) -> Tuple[bool, str]:
        """
        Automatically attempt to start a service if it's not running.
        
        Args:
            service_name: Name of the service
            compose_file: Path to docker-compose file
            
        Returns:
            (success: bool, message: str)
        """
        # Check current status
        status = self.get_service_status(service_name, force_refresh=True)
        
        if status.status == "docker_unavailable":
            return False, "Docker daemon is not running. Please start Docker Desktop and try again."
        
        if status.status == "running":
            return True, f"Service {service_name} is already running"
        
        if status.status == "stopped":
            # Try to start the stopped container
            return self.start_service(service_name)
        
        if status.status == "not_found":
            # Try to deploy using docker-compose
            return self.start_service(service_name, compose_file)
        
        return False, f"Unknown service status: {status.status}"
    
    def _parse_ports(self, ports_str: str) -> Dict[str, str]:
        """Parse Docker ports string into dict."""
        ports = {}
        if not ports_str:
            return ports
        
        # Format: "0.0.0.0:8000->8000/tcp"
        for mapping in ports_str.split(", "):
            if "->" in mapping:
                external, internal = mapping.split("->")
                if ":" in external:
                    external = external.split(":")[-1]
                ports[internal.split("/")[0]] = external
        
        return ports
    
    def get_compose_services(self, compose_file: str) -> List[str]:
        """
        Get list of services defined in docker-compose file.
        
        Args:
            compose_file: Path to docker-compose file
            
        Returns:
            List of service names
        """
        try:
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "config", "--services"],
                capture_output=True,
                timeout=10,
                text=True
            )
            
            if result.returncode == 0:
                return [s.strip() for s in result.stdout.strip().split('\n') if s.strip()]
            
        except Exception as e:
            logger.error(f"Error getting compose services: {e}")
        
        return []


# Global instance for caching
_docker_manager = None


def get_docker_manager(cache_ttl_seconds: int = 30) -> DockerManager:
    """Get or create global Docker manager instance."""
    global _docker_manager
    if _docker_manager is None:
        _docker_manager = DockerManager(cache_ttl_seconds)
    return _docker_manager

