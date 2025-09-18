"""Environment Detection and Run Profile System

This module provides automatic detection of the runtime environment (local vs Docker)
and creates optimized run profiles for HTTP requests and service discovery.

Features:
- Automatic environment detection
- Optimized HTTP client configurations
- Service discovery profiles
- Performance tuning based on environment
- Network connectivity validation
"""

import os
import sys
import socket
import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class Environment(Enum):
    """Runtime environment types."""
    LOCAL = "local"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    UNKNOWN = "unknown"


class RunProfile(Enum):
    """Performance and connectivity profiles."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"
    DEBUG = "debug"


@dataclass
class HTTPConfig:
    """HTTP client configuration optimized for environment."""
    timeout: float
    retries: int
    pool_connections: int
    pool_maxsize: int
    max_keepalive: int
    tcp_keepalive: bool
    user_agent: str


@dataclass
class ServiceDiscoveryConfig:
    """Service discovery configuration."""
    use_dns: bool
    use_health_checks: bool
    health_check_interval: int
    service_timeout: float
    retry_attempts: int


@dataclass
class EnvironmentProfile:
    """Complete environment profile with all configurations."""
    environment: Environment
    run_profile: RunProfile
    http_config: HTTPConfig
    discovery_config: ServiceDiscoveryConfig
    network_info: Dict[str, Any]
    service_mappings: Dict[str, str]


class EnvironmentDetector:
    """Detects runtime environment and creates optimized profiles."""

    def __init__(self):
        self._detection_cache: Optional[EnvironmentProfile] = None
        self._last_detection = 0
        self._cache_ttl = 300  # 5 minutes

    def detect_environment(self) -> EnvironmentProfile:
        """Detect the current runtime environment and return optimized profile."""

        # Check cache first
        current_time = time.time()
        if (self._detection_cache and
            current_time - self._last_detection < self._cache_ttl):
            return self._detection_cache

        # Perform detection
        environment = self._detect_environment_type()
        run_profile = self._detect_run_profile()
        network_info = self._gather_network_info()

        # Create configurations
        http_config = self._create_http_config(environment, run_profile)
        discovery_config = self._create_discovery_config(environment, run_profile)
        service_mappings = self._create_service_mappings(environment, network_info)

        # Create profile
        profile = EnvironmentProfile(
            environment=environment,
            run_profile=run_profile,
            http_config=http_config,
            discovery_config=discovery_config,
            network_info=network_info,
            service_mappings=service_mappings
        )

        # Cache result
        self._detection_cache = profile
        self._last_detection = current_time

        return profile

    def _detect_environment_type(self) -> Environment:
        """Detect the runtime environment type."""

        # Check for Docker
        if self._is_running_in_docker():
            return Environment.DOCKER

        # Check for Kubernetes
        if self._is_running_in_kubernetes():
            return Environment.KUBERNETES

        # Default to local
        return Environment.LOCAL

    def _detect_run_profile(self) -> RunProfile:
        """Detect the run profile based on environment variables and context."""

        # Check environment variables
        env_profile = os.environ.get('RUN_PROFILE', '').upper()
        if env_profile in RunProfile.__members__:
            return RunProfile[env_profile]

        # Check for development indicators
        if (os.environ.get('ENVIRONMENT') == 'development' or
            'DEBUG' in os.environ or
            os.environ.get('FLASK_ENV') == 'development'):
            return RunProfile.DEVELOPMENT

        # Check for testing
        if ('pytest' in sys.modules or
            'unittest' in sys.modules or
            os.environ.get('PYTEST_CURRENT_TEST')):
            return RunProfile.TESTING

        # Default to production for containerized environments
        if self._is_running_in_docker() or self._is_running_in_kubernetes():
            return RunProfile.PRODUCTION

        return RunProfile.DEVELOPMENT

    def _is_running_in_docker(self) -> bool:
        """Check if running inside a Docker container."""
        try:
            with open('/.dockerenv', 'r') as f:
                return True
        except FileNotFoundError:
            pass

        # Check cgroup
        try:
            with open('/proc/1/cgroup', 'r') as f:
                if 'docker' in f.read():
                    return True
        except FileNotFoundError:
            pass

        # Check environment
        return 'DOCKER_CONTAINER' in os.environ

    def _is_running_in_kubernetes(self) -> bool:
        """Check if running in a Kubernetes cluster."""
        return ('KUBERNETES_SERVICE_HOST' in os.environ or
                os.path.exists('/var/run/secrets/kubernetes.io'))

    def _gather_network_info(self) -> Dict[str, Any]:
        """Gather network connectivity information."""
        info = {
            'hostname': socket.gethostname(),
            'interfaces': {},
            'connectivity': {}
        }

        # Get network interfaces
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                info['interfaces'][interface] = addrs
        except ImportError:
            # Fallback without netifaces
            try:
                info['local_ip'] = socket.gethostbyname(socket.gethostname())
            except:
                info['local_ip'] = 'unknown'

        # Test connectivity to common services
        test_hosts = ['localhost', '127.0.0.1']
        for host in test_hosts:
            try:
                socket.create_connection((host, 80), timeout=1)
                info['connectivity'][host] = True
            except:
                info['connectivity'][host] = False

        return info

    def _create_http_config(self, environment: Environment, run_profile: RunProfile) -> HTTPConfig:
        """Create optimized HTTP configuration."""

        base_config = {
            'timeout': 30.0,
            'retries': 3,
            'pool_connections': 10,
            'pool_maxsize': 10,
            'max_keepalive': 5,
            'tcp_keepalive': True,
            'user_agent': f'hackathon-ecosystem/{environment.value}'
        }

        # Adjust based on environment
        if environment == Environment.DOCKER:
            base_config.update({
                'timeout': 15.0,  # Faster timeouts in containers
                'retries': 2,
                'pool_connections': 20,  # More connections for containerized services
                'pool_maxsize': 20
            })
        elif environment == Environment.LOCAL:
            base_config.update({
                'timeout': 10.0,  # Faster for local development
                'retries': 1
            })

        # Adjust based on run profile
        if run_profile == RunProfile.DEVELOPMENT:
            base_config.update({
                'timeout': 60.0,  # Longer timeouts for debugging
                'retries': 5,
                'user_agent': f'{base_config["user_agent"]}-dev'
            })
        elif run_profile == RunProfile.TESTING:
            base_config.update({
                'timeout': 5.0,  # Short timeouts for tests
                'retries': 1,
                'user_agent': f'{base_config["user_agent"]}-test'
            })

        return HTTPConfig(**base_config)

    def _create_discovery_config(self, environment: Environment, run_profile: RunProfile) -> ServiceDiscoveryConfig:
        """Create service discovery configuration."""

        base_config = {
            'use_dns': True,
            'use_health_checks': True,
            'health_check_interval': 30,
            'service_timeout': 5.0,
            'retry_attempts': 3
        }

        # Adjust for environment
        if environment == Environment.DOCKER:
            base_config.update({
                'use_dns': True,  # Docker uses DNS for service discovery
                'health_check_interval': 15,  # More frequent checks in containers
                'service_timeout': 3.0
            })
        elif environment == Environment.KUBERNETES:
            base_config.update({
                'use_dns': True,
                'health_check_interval': 10,
                'service_timeout': 2.0
            })

        # Adjust for run profile
        if run_profile == RunProfile.DEVELOPMENT:
            base_config.update({
                'health_check_interval': 60,  # Less frequent in development
                'retry_attempts': 5
            })
        elif run_profile == RunProfile.TESTING:
            base_config.update({
                'use_health_checks': False,  # Skip health checks in tests
                'service_timeout': 1.0,
                'retry_attempts': 1
            })

        return ServiceDiscoveryConfig(**base_config)

    def _create_service_mappings(self, environment: Environment, network_info: Dict[str, Any]) -> Dict[str, str]:
        """Create service URL mappings based on environment."""

        mappings = {}

        # Base service configurations
        services = {
            'orchestrator': '5099',
            'doc_store': '5087',
            'analysis-service': '5080',
            'source-agent': '5085',
            'notification-service': '5130',
            'frontend': '3000',
            'llm-gateway': '5055',
            'summarizer-hub': '5160',
            'code-analyzer': '5025',
            'discovery-agent': '5045',
            'prompt_store': '5110',
            'interpreter': '5120'
        }

        # Create mappings based on environment
        base_url = 'localhost' if environment == Environment.LOCAL else 'host.docker.internal'

        for service, port in services.items():
            if environment == Environment.DOCKER:
                # Use Docker service names for inter-container communication
                mappings[service] = f'http://{service.replace("-", "_")}:5000'
            else:
                # Use localhost for local development
                mappings[service] = f'http://localhost:{port}'

        return mappings

    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get the URL for a service based on current environment."""
        profile = self.detect_environment()
        return profile.service_mappings.get(service_name)

    def get_http_config(self) -> HTTPConfig:
        """Get optimized HTTP configuration for current environment."""
        profile = self.detect_environment()
        return profile.http_config

    def get_discovery_config(self) -> ServiceDiscoveryConfig:
        """Get service discovery configuration for current environment."""
        profile = self.detect_environment()
        return profile.discovery_config

    def validate_environment(self) -> Dict[str, Any]:
        """Validate current environment configuration."""
        profile = self.detect_environment()

        validation_results = {
            'environment_detected': profile.environment.value,
            'run_profile': profile.run_profile.value,
            'network_connectivity': {},
            'service_accessibility': {},
            'configuration_valid': True,
            'warnings': [],
            'errors': []
        }

        # Test service connectivity
        for service_name, url in profile.service_mappings.items():
            try:
                import urllib.request
                urllib.request.urlopen(f'{url}/health', timeout=5)
                validation_results['service_accessibility'][service_name] = 'accessible'
            except:
                validation_results['service_accessibility'][service_name] = 'inaccessible'
                validation_results['warnings'].append(f'Service {service_name} not accessible at {url}')

        return validation_results


# Global instance
environment_detector = EnvironmentDetector()


def get_current_environment() -> EnvironmentProfile:
    """Get current environment profile."""
    return environment_detector.detect_environment()


def get_service_url(service_name: str) -> Optional[str]:
    """Get service URL for current environment."""
    return environment_detector.get_service_url(service_name)


def get_http_config() -> HTTPConfig:
    """Get HTTP configuration for current environment."""
    return environment_detector.get_http_config()


def validate_environment() -> Dict[str, Any]:
    """Validate current environment setup."""
    return environment_detector.validate_environment()


if __name__ == '__main__':
    # Test the detector
    print("🔍 Environment Detection Test")
    print("=" * 40)

    profile = get_current_environment()

    print(f"Environment: {profile.environment.value}")
    print(f"Run Profile: {profile.run_profile.value}")
    print(f"HTTP Timeout: {profile.http_config.timeout}s")
    print(f"Service Discovery: {'DNS' if profile.discovery_config.use_dns else 'Direct'}")

    print("\nService Mappings:")
    for service, url in profile.service_mappings.items():
        print(f"  {service}: {url}")

    print("\nValidation:")
    validation = validate_environment()
    accessible = sum(1 for s in validation['service_accessibility'].values() if s == 'accessible')
    total = len(validation['service_accessibility'])
    print(f"Services accessible: {accessible}/{total}")

    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")
