"""Service Discovery - Local Development Service Discovery.

Provides automatic service discovery and health checking for local development
environment, with fallback mechanisms and service availability detection.
"""

import asyncio
import socket
import aiohttp
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

from .config_manager import get_config
from services.project_simulation.simulation.infrastructure.logging import get_simulation_logger


class ServiceDiscoveryError(Exception):
    """Service discovery error."""

    def __init__(self, service_name: str, message: str):
        self.service_name = service_name
        self.message = message
        super().__init__(f"Service discovery failed for {service_name}: {message}")


class ServiceHealth:
    """Service health information."""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.is_healthy = False
        self.last_checked = None
        self.response_time = None
        self.error_message = None
        self.version = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "url": self.url,
            "is_healthy": self.is_healthy,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "response_time": self.response_time,
            "error_message": self.error_message,
            "version": self.version
        }


class LocalServiceDiscovery:
    """Local service discovery for development environment."""

    def __init__(self):
        """Initialize service discovery."""
        self.logger = get_simulation_logger()
        self.config = get_config()
        self.services: Dict[str, ServiceHealth] = {}
        self.discovery_interval = 30  # seconds
        self.health_check_timeout = 5  # seconds
        self._running = False
        self._task = None

        # Initialize service registry
        self._initialize_service_registry()

    def _initialize_service_registry(self):
        """Initialize service registry from configuration."""
        service_urls = self.config.ecosystem.__dict__

        for service_name, url in service_urls.items():
            if url and isinstance(url, str):
                self.services[service_name] = ServiceHealth(service_name, url)

        self.logger.info(f"Initialized service registry with {len(self.services)} services")

    async def start_discovery(self):
        """Start service discovery process."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._discovery_loop())
        self.logger.info("Service discovery started")

    async def stop_discovery(self):
        """Stop service discovery process."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self.logger.info("Service discovery stopped")

    async def _discovery_loop(self):
        """Main discovery loop."""
        while self._running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self.discovery_interval)
            except Exception as e:
                self.logger.error("Error in discovery loop", error=str(e))
                await asyncio.sleep(self.discovery_interval)

    async def _check_all_services(self):
        """Check health of all registered services."""
        tasks = []
        for service in self.services.values():
            task = asyncio.create_task(self._check_service_health(service))
            tasks.append(task)

        # Wait for all checks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        # Log summary
        healthy_count = sum(1 for s in self.services.values() if s.is_healthy)
        total_count = len(self.services)
        self.logger.debug(f"Service health check completed: {healthy_count}/{total_count} services healthy")

    async def _check_service_health(self, service: ServiceHealth):
        """Check health of a single service."""
        import time

        try:
            start_time = time.time()

            # Parse URL to get health endpoint
            parsed = urlparse(service.url)
            health_url = f"{parsed.scheme}://{parsed.netloc}/health"

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.health_check_timeout)) as session:
                async with session.get(health_url) as response:
                    response_time = time.time() - start_time

                    if response.status == 200:
                        # Try to get service info
                        try:
                            data = await response.json()
                            service.version = data.get("version")
                        except:
                            pass

                        service.is_healthy = True
                        service.response_time = response_time
                        service.error_message = None
                    else:
                        service.is_healthy = False
                        service.response_time = response_time
                        service.error_message = f"HTTP {response.status}"

        except asyncio.TimeoutError:
            service.is_healthy = False
            service.response_time = self.health_check_timeout
            service.error_message = "Timeout"

        except aiohttp.ClientError as e:
            service.is_healthy = False
            service.response_time = None
            service.error_message = str(e)

        except Exception as e:
            service.is_healthy = False
            service.response_time = None
            service.error_message = f"Unexpected error: {str(e)}"

        service.last_checked = asyncio.get_event_loop().time()

    def get_service_url(self, service_name: str, fallback: Optional[str] = None) -> str:
        """Get URL for a service, with fallback support."""
        if service_name in self.services:
            service = self.services[service_name]
            if service.is_healthy:
                return service.url
            else:
                self.logger.warning(f"Service {service_name} is not healthy, using fallback")
                return fallback or service.url
        else:
            self.logger.warning(f"Service {service_name} not found in registry")
            return fallback or ""

    def get_healthy_services(self) -> List[str]:
        """Get list of healthy services."""
        return [name for name, service in self.services.items() if service.is_healthy]

    def get_unhealthy_services(self) -> List[str]:
        """Get list of unhealthy services."""
        return [name for name, service in self.services.items() if not service.is_healthy]

    def get_service_health(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get health information for a specific service."""
        if service_name in self.services:
            return self.services[service_name].to_dict()
        return None

    def get_all_service_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health information for all services."""
        return {name: service.to_dict() for name, service in self.services.items()}

    def is_service_available(self, service_name: str) -> bool:
        """Check if a service is available."""
        return service_name in self.services and self.services[service_name].is_healthy

    def get_service_discovery_summary(self) -> Dict[str, Any]:
        """Get summary of service discovery status."""
        total_services = len(self.services)
        healthy_services = len(self.get_healthy_services())
        unhealthy_services = len(self.get_unhealthy_services())

        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": unhealthy_services,
            "discovery_running": self._running,
            "discovery_interval": self.discovery_interval,
            "last_check": asyncio.get_event_loop().time() if self._running else None
        }


class FallbackServiceClient:
    """Service client with automatic fallback mechanisms."""

    def __init__(self, service_name: str, discovery: LocalServiceDiscovery):
        """Initialize fallback service client."""
        self.service_name = service_name
        self.discovery = discovery
        self.logger = get_simulation_logger()

    async def make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make request with automatic fallback handling."""
        service_url = self.discovery.get_service_url(self.service_name)

        if not service_url:
            self.logger.warning(f"No URL available for service {self.service_name}")
            return None

        # Check if service is available
        if not self.discovery.is_service_available(self.service_name):
            self.logger.warning(f"Service {self.service_name} is not available, request will fail")
            return None

        # Make the request
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{service_url}{endpoint}"
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.error(f"Request to {self.service_name} failed with status {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Request to {self.service_name} failed", error=str(e))
            return None


class PortScanner:
    """Port scanner for local service discovery."""

    def __init__(self):
        """Initialize port scanner."""
        self.logger = get_simulation_logger()
        self.scan_timeout = 1.0  # seconds

    async def scan_ports(self, host: str, port_range: Tuple[int, int]) -> List[int]:
        """Scan range of ports on a host."""
        open_ports = []

        async def check_port(port: int) -> bool:
            try:
                reader, writer = await asyncio.open_connection(host, port)
                writer.close()
                await writer.wait_closed()
                return True
            except:
                return False

        tasks = []
        for port in range(port_range[0], port_range[1] + 1):
            task = asyncio.create_task(check_port(port))
            tasks.append((port, task))

        for port, task in tasks:
            try:
                is_open = await asyncio.wait_for(task, timeout=self.scan_timeout)
                if is_open:
                    open_ports.append(port)
            except asyncio.TimeoutError:
                pass

        return open_ports

    def detect_common_services(self, host: str = "localhost") -> Dict[str, int]:
        """Detect common service ports."""
        common_ports = {
            "redis": 6379,
            "postgresql": 5432,
            "mysql": 3306,
            "mongodb": 27017,
            "elasticsearch": 9200,
            "rabbitmq": 5672,
            "ollama": 11434,
            "mailhog_smtp": 1025,
            "mailhog_web": 8025
        }

        # This would need to be implemented asynchronously
        # For now, return the known port mappings
        return common_ports


# Global service discovery instance
_service_discovery: Optional[LocalServiceDiscovery] = None


def get_service_discovery() -> LocalServiceDiscovery:
    """Get the global service discovery instance."""
    global _service_discovery
    if _service_discovery is None:
        _service_discovery = LocalServiceDiscovery()
    return _service_discovery


async def start_service_discovery():
    """Start the global service discovery."""
    discovery = get_service_discovery()
    await discovery.start_discovery()


async def stop_service_discovery():
    """Stop the global service discovery."""
    discovery = get_service_discovery()
    await discovery.stop_discovery()


def get_service_url(service_name: str, fallback: Optional[str] = None) -> str:
    """Get URL for a service."""
    discovery = get_service_discovery()
    return discovery.get_service_url(service_name, fallback)


def is_service_available(service_name: str) -> bool:
    """Check if a service is available."""
    discovery = get_service_discovery()
    return discovery.is_service_available(service_name)


def get_service_health_summary() -> Dict[str, Any]:
    """Get service health summary."""
    discovery = get_service_discovery()
    return discovery.get_service_discovery_summary()


__all__ = [
    'LocalServiceDiscovery',
    'FallbackServiceClient',
    'PortScanner',
    'ServiceDiscoveryError',
    'get_service_discovery',
    'start_service_discovery',
    'stop_service_discovery',
    'get_service_url',
    'is_service_available',
    'get_service_health_summary'
]
