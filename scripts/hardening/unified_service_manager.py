#!/usr/bin/env python3
"""
Unified Service Management Framework
====================================

Consolidated service lifecycle management combining:
- Auto-healing capabilities
- Dependency validation
- Service connectivity testing
- Production readiness validation

PURPOSE: Unified service lifecycle management and monitoring
DEPENDENCIES: requests, docker, psutil, yaml, kubernetes (optional)
OVERLAPS: auto_healer.py, dependency_validator.py, service_connectivity_validator.py, production_readiness_validator.py
CONSOLIDATION_TARGET: unified_service_manager.py (THIS FILE)
MAINTENANCE_LEVEL: HIGH (core service management)
LLM_PROCESSING_HINTS:
- Use async patterns for concurrent service checks
- Implement circuit breaker pattern for failing services
- Cache service discovery results to reduce overhead
- Provide graceful degradation for optional dependencies
"""

import asyncio
import aiohttp
import docker
import json
import yaml
import time
import psutil
import socket
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import subprocess
import sys

# Optional imports with fallbacks
try:
    import kubernetes as k8s
    from kubernetes import client, config
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STOPPED = "stopped"


class ServiceType(Enum):
    """Types of services in the ecosystem"""
    API_SERVICE = "api_service"
    DATASTORE = "datastore"
    MESSAGE_QUEUE = "message_queue"
    LOAD_BALANCER = "load_balancer"
    MONITORING = "monitoring"
    BACKGROUND_WORKER = "background_worker"


@dataclass
class ServiceDefinition:
    """Complete service definition with dependencies and requirements"""
    name: str
    service_type: ServiceType
    host: str
    port: int
    health_endpoint: str = "/health"
    dependencies: List[str] = field(default_factory=list)
    startup_timeout: int = 60
    health_check_interval: int = 30
    max_restart_attempts: int = 3
    critical_for_system: bool = False
    environment_specific: bool = False
    docker_container: Optional[str] = None
    kubernetes_deployment: Optional[str] = None
    resource_limits: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceHealth:
    """Real-time service health information"""
    service_name: str
    status: ServiceStatus
    last_check: datetime
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    last_successful_check: Optional[datetime] = None
    dependency_status: Dict[str, ServiceStatus] = field(default_factory=dict)


@dataclass
class ServiceManagerConfig:
    """Configuration for the unified service manager"""
    workspace_path: Path
    docker_compose_file: str = "docker-compose.dev.yml"
    kubernetes_namespace: str = "default"
    health_check_timeout: int = 10
    service_discovery_interval: int = 60
    max_concurrent_checks: int = 10
    enable_auto_healing: bool = True
    enable_dependency_validation: bool = True
    enable_resource_monitoring: bool = True
    alert_thresholds: Dict[str, Any] = field(default_factory=dict)


class UnifiedServiceManager:
    """
    Unified Service Management Framework

    LLM_PROCESSING_HINTS:
    - This class consolidates service lifecycle management from 4 separate files
    - Use async methods for concurrent service operations
    - Implement exponential backoff for retry logic
    - Cache service discovery to reduce overhead
    - Provide both sync and async interfaces
    """

    def __init__(self, config: Optional[ServiceManagerConfig] = None):
        """Initialize the unified service manager"""
        self.config = config or ServiceManagerConfig(workspace_path=Path.cwd())
        self.services: Dict[str, ServiceDefinition] = {}
        self.health_status: Dict[str, ServiceHealth] = {}
        self.docker_client: Optional[docker.DockerClient] = None
        self.kubernetes_client: Optional[Any] = None
        self.redis_client: Optional[redis.Redis] = None

        # Initialize clients
        self._init_docker_client()
        self._init_kubernetes_client()
        self._init_redis_client()

        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.service_discovery_cache: Dict[str, datetime] = {}
        self.last_discovery_time: Optional[datetime] = None

        # Performance metrics
        self.operation_metrics = {
            "health_checks": 0,
            "failed_checks": 0,
            "auto_heals": 0,
            "dependency_checks": 0,
            "resource_checks": 0
        }

        self.logger = logging.getLogger("unified_service_manager")
        self.logger.info("🔧 Unified Service Manager initialized")

    def _init_docker_client(self):
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
            self.logger.info("🐳 Docker client initialized")
        except Exception as e:
            self.logger.warning(f"🐳 Docker client initialization failed: {e}")
            self.docker_client = None

    def _init_kubernetes_client(self):
        """Initialize Kubernetes client"""
        if not KUBERNETES_AVAILABLE:
            self.logger.info("☸️ Kubernetes not available")
            return

        try:
            config.load_incluster_config()
            self.kubernetes_client = client.CoreV1Api()
            self.logger.info("☸️ Kubernetes client initialized")
        except Exception as e:
            self.logger.warning(f"☸️ Kubernetes client initialization failed: {e}")
            self.kubernetes_client = None

    def _init_redis_client(self):
        """Initialize Redis client for caching"""
        if not REDIS_AVAILABLE:
            self.logger.info("🔴 Redis not available for caching")
            return

        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.redis_client.ping()
            self.logger.info("🔴 Redis client initialized")
        except Exception as e:
            self.logger.warning(f"🔴 Redis client initialization failed: {e}")
            self.redis_client = None

    def discover_services(self) -> Dict[str, ServiceDefinition]:
        """
        Discover all services from configuration files

        LLM_PROCESSING_HINTS:
        - This method replaces functionality from dependency_validator.py
        - Use caching to avoid repeated file reads
        - Support multiple configuration formats (YAML, JSON, Kubernetes)
        - Validate service definitions against schema
        """
        # Check cache validity
        if (self.last_discovery_time and
            datetime.now() - self.last_discovery_time < timedelta(seconds=self.config.service_discovery_interval)):
            return self.services

        self.logger.info("🔍 Discovering services...")

        services = {}

        # Discover from Docker Compose
        services.update(self._discover_from_docker_compose())

        # Discover from Kubernetes (if available)
        if self.kubernetes_client:
            services.update(self._discover_from_kubernetes())

        # Discover from manual configuration
        services.update(self._discover_from_manual_config())

        self.services = services
        self.last_discovery_time = datetime.now()

        self.logger.info(f"🔍 Discovered {len(services)} services")
        return services

    def _discover_from_docker_compose(self) -> Dict[str, ServiceDefinition]:
        """Discover services from Docker Compose configuration"""
        compose_file = self.config.workspace_path / self.config.docker_compose_file

        if not compose_file.exists():
            return {}

        try:
            with open(compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)

            services = {}
            if 'services' in compose_config:
                for service_name, service_config in compose_config['services'].items():
                    service_def = self._parse_docker_service(service_name, service_config)
                    if service_def:
                        services[service_name] = service_def

            return services

        except Exception as e:
            self.logger.error(f"Failed to parse Docker Compose: {e}")
            return {}

    def _parse_docker_service(self, name: str, config: Dict[str, Any]) -> Optional[ServiceDefinition]:
        """Parse Docker service configuration"""
        try:
            # Extract port mapping
            ports = config.get('ports', [])
            if not ports:
                return None

            # Get first port mapping
            port_mapping = ports[0]
            if isinstance(port_mapping, str):
                external_port = int(port_mapping.split(':')[0])
            elif isinstance(port_mapping, dict):
                external_port = port_mapping.get('published', port_mapping.get('target'))
            else:
                external_port = port_mapping

            # Determine service type
            service_type = self._infer_service_type(name, config)

            # Extract dependencies
            depends_on = config.get('depends_on', [])
            if isinstance(depends_on, dict):
                dependencies = list(depends_on.keys())
            elif isinstance(depends_on, list):
                dependencies = depends_on
            else:
                dependencies = []

            return ServiceDefinition(
                name=name,
                service_type=service_type,
                host="localhost",
                port=int(external_port),
                dependencies=dependencies,
                docker_container=config.get('container_name', f"hackathon-{name}-1"),
                resource_limits=config.get('deploy', {}).get('resources', {})
            )

        except Exception as e:
            self.logger.warning(f"Failed to parse service {name}: {e}")
            return None

    def _infer_service_type(self, name: str, config: Dict[str, Any]) -> ServiceType:
        """Infer service type from name and configuration"""
        name_lower = name.lower()

        if any(keyword in name_lower for keyword in ['redis', 'postgres', 'mysql', 'mongo']):
            return ServiceType.DATASTORE
        elif any(keyword in name_lower for keyword in ['rabbit', 'kafka', 'queue']):
            return ServiceType.MESSAGE_QUEUE
        elif any(keyword in name_lower for keyword in ['nginx', 'traefik', 'haproxy']):
            return ServiceType.LOAD_BALANCER
        elif any(keyword in name_lower for keyword in ['prometheus', 'grafana', 'monitor']):
            return ServiceType.MONITORING
        elif any(keyword in name_lower for keyword in ['worker', 'processor', 'task']):
            return ServiceType.BACKGROUND_WORKER
        else:
            return ServiceType.API_SERVICE

    def _discover_from_kubernetes(self) -> Dict[str, ServiceDefinition]:
        """Discover services from Kubernetes"""
        if not self.kubernetes_client:
            return {}

        try:
            services = {}
            # Implementation for Kubernetes service discovery
            # This would query Kubernetes API for services
            return services
        except Exception as e:
            self.logger.error(f"Failed to discover from Kubernetes: {e}")
            return {}

    def _discover_from_manual_config(self) -> Dict[str, ServiceDefinition]:
        """Discover services from manual configuration files"""
        # Implementation for manual service configuration
        return {}

    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """
        Check health of a specific service

        LLM_PROCESSING_HINTS:
        - This consolidates health checking from multiple files
        - Use async HTTP requests for concurrent checks
        - Implement retry logic with exponential backoff
        - Cache results to reduce load on services
        """
        if service_name not in self.services:
            return ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.UNKNOWN,
                last_check=datetime.now(),
                error_message="Service not found in registry"
            )

        service = self.services[service_name]

        try:
            # Check service connectivity
            connectivity_ok = await self._check_connectivity(service)

            if not connectivity_ok:
                return ServiceHealth(
                    service_name=service_name,
                    status=ServiceStatus.UNHEALTHY,
                    last_check=datetime.now(),
                    error_message="Service not reachable"
                )

            # Check health endpoint
            health_url = f"http://{service.host}:{service.port}{service.health_endpoint}"
            start_time = time.time()

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.health_check_timeout)) as session:
                async with session.get(health_url) as response:
                    response_time = time.time() - start_time
                    status_code = response.status

                    if status_code == 200:
                        # Try to parse response
                        try:
                            health_data = await response.json()
                            status = health_data.get("status", "unknown")

                            if status == "healthy":
                                service_status = ServiceStatus.HEALTHY
                            elif status == "degraded":
                                service_status = ServiceStatus.DEGRADED
                            else:
                                service_status = ServiceStatus.UNHEALTHY
                        except:
                            service_status = ServiceStatus.HEALTHY  # Basic connectivity check passed

                        # Update consecutive failures
                        if service_name in self.health_status:
                            current_health = self.health_status[service_name]
                            consecutive_failures = 0 if service_status == ServiceStatus.HEALTHY else current_health.consecutive_failures + 1
                        else:
                            consecutive_failures = 0

                        return ServiceHealth(
                            service_name=service_name,
                            status=service_status,
                            last_check=datetime.now(),
                            response_time=response_time,
                            consecutive_failures=consecutive_failures,
                            last_successful_check=datetime.now() if service_status == ServiceStatus.HEALTHY else None
                        )
                    else:
                        return ServiceHealth(
                            service_name=service_name,
                            status=ServiceStatus.UNHEALTHY,
                            last_check=datetime.now(),
                            response_time=response_time,
                            error_message=f"Health check returned status {status_code}"
                        )

        except Exception as e:
            return ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e)
            )

    async def _check_connectivity(self, service: ServiceDefinition) -> bool:
        """Check basic connectivity to service"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((service.host, service.port))
            sock.close()
            return result == 0
        except:
            return False

    async def check_all_services_health(self) -> Dict[str, ServiceHealth]:
        """
        Check health of all discovered services concurrently

        LLM_PROCESSING_HINTS:
        - Use asyncio.gather for concurrent health checks
        - Limit concurrency to prevent overwhelming services
        - Implement timeout handling for slow services
        """
        if not self.services:
            self.discover_services()

        self.logger.info(f"🏥 Checking health of {len(self.services)} services...")

        # Create semaphore to limit concurrent checks
        semaphore = asyncio.Semaphore(self.config.max_concurrent_checks)

        async def check_with_semaphore(service_name: str):
            async with semaphore:
                return await self.check_service_health(service_name)

        # Run all checks concurrently
        tasks = [check_with_semaphore(name) for name in self.services.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        health_status = {}
        for i, result in enumerate(results):
            service_name = list(self.services.keys())[i]
            if isinstance(result, Exception):
                health_status[service_name] = ServiceHealth(
                    service_name=service_name,
                    status=ServiceStatus.UNKNOWN,
                    last_check=datetime.now(),
                    error_message=str(result)
                )
            else:
                health_status[service_name] = result

        self.health_status.update(health_status)
        self.operation_metrics["health_checks"] += len(health_status)

        self.logger.info(f"🏥 Health check completed for {len(health_status)} services")
        return health_status

    def validate_dependencies(self) -> Dict[str, List[str]]:
        """
        Validate service dependencies

        LLM_PROCESSING_HINTS:
        - This replaces dependency_validator.py functionality
        - Build dependency graph to detect cycles
        - Validate dependency health and availability
        - Provide suggestions for dependency optimization
        """
        if not self.services:
            self.discover_services()

        self.logger.info("🔗 Validating service dependencies...")

        dependency_issues = {}
        dependency_graph = self._build_dependency_graph()

        # Check for circular dependencies
        cycles = self._detect_cycles(dependency_graph)
        if cycles:
            dependency_issues["circular_dependencies"] = cycles

        # Check dependency health
        unhealthy_deps = []
        for service_name, service in self.services.items():
            for dep in service.dependencies:
                if dep in self.health_status:
                    dep_health = self.health_status[dep]
                    if dep_health.status in [ServiceStatus.UNHEALTHY, ServiceStatus.UNKNOWN]:
                        unhealthy_deps.append(f"{service_name} -> {dep} ({dep_health.status.value})")

        if unhealthy_deps:
            dependency_issues["unhealthy_dependencies"] = unhealthy_deps

        # Check missing dependencies
        missing_deps = []
        for service_name, service in self.services.items():
            for dep in service.dependencies:
                if dep not in self.services:
                    missing_deps.append(f"{service_name} -> {dep} (not found)")

        if missing_deps:
            dependency_issues["missing_dependencies"] = missing_deps

        self.operation_metrics["dependency_checks"] += 1
        return dependency_issues

    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph from services"""
        graph = {}
        for service_name, service in self.services.items():
            graph[service_name] = set(service.dependencies)
        return graph

    def _detect_cycles(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Detect circular dependencies in the graph"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def auto_heal_service(self, service_name: str) -> bool:
        """
        Attempt to auto-heal a service

        LLM_PROCESSING_HINTS:
        - This consolidates auto-healing from auto_healer.py
        - Implement multiple healing strategies
        - Track healing success rates
        - Provide escalation paths for failed healing
        """
        if service_name not in self.services:
            self.logger.warning(f"Cannot heal unknown service: {service_name}")
            return False

        service = self.services[service_name]
        self.logger.info(f"🔧 Attempting to heal service: {service_name}")

        # Strategy 1: Restart Docker container
        if service.docker_container and self.docker_client:
            success = self._restart_docker_container(service.docker_container)
            if success:
                self.logger.info(f"✅ Successfully restarted container: {service.docker_container}")
                self.operation_metrics["auto_heals"] += 1
                return True

        # Strategy 2: Restart Kubernetes pod (if available)
        if service.kubernetes_deployment and self.kubernetes_client:
            success = self._restart_kubernetes_pod(service.kubernetes_deployment)
            if success:
                self.logger.info(f"✅ Successfully restarted Kubernetes pod: {service.kubernetes_deployment}")
                self.operation_metrics["auto_heals"] += 1
                return True

        # Strategy 3: Process restart (for local processes)
        success = self._restart_local_process(service_name)
        if success:
            self.logger.info(f"✅ Successfully restarted local process: {service_name}")
            self.operation_metrics["auto_heals"] += 1
            return True

        self.logger.error(f"❌ Failed to heal service: {service_name}")
        return False

    def _restart_docker_container(self, container_name: str) -> bool:
        """Restart a Docker container"""
        try:
            container = self.docker_client.containers.get(container_name)
            container.restart()
            return True
        except Exception as e:
            self.logger.error(f"Failed to restart container {container_name}: {e}")
            return False

    def _restart_kubernetes_pod(self, deployment_name: str) -> bool:
        """Restart a Kubernetes pod"""
        # Implementation for Kubernetes pod restart
        return False

    def _restart_local_process(self, service_name: str) -> bool:
        """Restart a local process"""
        # Implementation for local process restart
        return False

    def validate_production_readiness(self) -> Dict[str, Any]:
        """
        Validate production readiness of all services

        LLM_PROCESSING_HINTS:
        - This consolidates production readiness from production_readiness_validator.py
        - Check multiple readiness criteria
        - Provide detailed readiness reports
        - Suggest improvements for non-ready services
        """
        if not self.services:
            self.discover_services()

        self.logger.info("🚀 Validating production readiness...")

        readiness_report = {
            "overall_ready": True,
            "services_ready": {},
            "issues": [],
            "recommendations": []
        }

        for service_name, service in self.services.items():
            service_ready, issues = self._check_service_readiness(service)

            readiness_report["services_ready"][service_name] = {
                "ready": service_ready,
                "issues": issues
            }

            if not service_ready:
                readiness_report["overall_ready"] = False
                readiness_report["issues"].extend([f"{service_name}: {issue}" for issue in issues])

        # Generate recommendations
        readiness_report["recommendations"] = self._generate_readiness_recommendations(readiness_report)

        return readiness_report

    def _check_service_readiness(self, service: ServiceDefinition) -> Tuple[bool, List[str]]:
        """Check readiness of a single service"""
        issues = []

        # Check health
        if service.name in self.health_status:
            health = self.health_status[service.name]
            if health.status != ServiceStatus.HEALTHY:
                issues.append(f"Service health: {health.status.value}")

        # Check dependencies
        for dep in service.dependencies:
            if dep not in self.services:
                issues.append(f"Missing dependency: {dep}")
            elif dep in self.health_status:
                dep_health = self.health_status[dep]
                if dep_health.status != ServiceStatus.HEALTHY:
                    issues.append(f"Unhealthy dependency {dep}: {dep_health.status.value}")

        # Check resource limits
        if service.resource_limits:
            # Validate resource limits are reasonable
            pass

        # Check critical services
        if service.critical_for_system and issues:
            issues.append("Critical service has issues - immediate attention required")

        return len(issues) == 0, issues

    def _generate_readiness_recommendations(self, readiness_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving production readiness"""
        recommendations = []

        if not readiness_report["overall_ready"]:
            recommendations.append("🔴 Address critical service issues before deployment")

        unhealthy_count = sum(1 for s in readiness_report["services_ready"].values() if not s["ready"])
        if unhealthy_count > 0:
            recommendations.append(f"🟡 Fix {unhealthy_count} unhealthy services")

        missing_deps = [issue for issue in readiness_report["issues"] if "Missing dependency" in issue]
        if missing_deps:
            recommendations.append("🔧 Resolve missing service dependencies")

        return recommendations

    def get_service_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service metrics"""
        return {
            "services_discovered": len(self.services),
            "services_monitored": len(self.health_status),
            "operation_metrics": self.operation_metrics,
            "health_summary": self._get_health_summary(),
            "timestamp": datetime.now().isoformat()
        }

    def _get_health_summary(self) -> Dict[str, int]:
        """Get summary of service health status"""
        summary = {
            "healthy": 0,
            "degraded": 0,
            "unhealthy": 0,
            "unknown": 0,
            "stopped": 0
        }

        for health in self.health_status.values():
            status_key = health.status.value
            if status_key in summary:
                summary[status_key] += 1

        return summary

    def start_monitoring(self):
        """Start continuous monitoring"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="service_monitor"
        )
        self.monitoring_thread.start()
        self.logger.info("📊 Service monitoring started")

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("📊 Service monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Run health checks
                asyncio.run(self.check_all_services_health())

                # Validate dependencies
                if self.config.enable_dependency_validation:
                    self.validate_dependencies()

                # Check production readiness
                if self.config.enable_resource_monitoring:
                    self.validate_production_readiness()

                time.sleep(self.config.service_discovery_interval)

            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(5)


# Global instance for easy access
_service_manager: Optional[UnifiedServiceManager] = None


def get_service_manager(config: Optional[ServiceManagerConfig] = None) -> UnifiedServiceManager:
    """Get the global service manager instance"""
    global _service_manager
    if _service_manager is None:
        _service_manager = UnifiedServiceManager(config)
    return _service_manager


def init_service_manager(workspace_path: Optional[str] = None) -> UnifiedServiceManager:
    """Initialize the service manager with default configuration"""
    config = ServiceManagerConfig(
        workspace_path=Path(workspace_path or Path.cwd()),
        enable_auto_healing=True,
        enable_dependency_validation=True,
        enable_resource_monitoring=True
    )
    return get_service_manager(config)


# Example usage and testing
if __name__ == "__main__":
    # Initialize service manager
    manager = init_service_manager()

    # Discover services
    services = manager.discover_services()
    print(f"Discovered {len(services)} services")

    # Check service health
    async def test_health():
        health_status = await manager.check_all_services_health()
        print(f"Health checked {len(health_status)} services")

        # Print health summary
        for service_name, health in health_status.items():
            print(f"  {service_name}: {health.status.value}")

    # Run async health check
    asyncio.run(test_health())

    # Validate dependencies
    dep_issues = manager.validate_dependencies()
    if dep_issues:
        print(f"Dependency issues found: {dep_issues}")
    else:
        print("No dependency issues found")

    # Check production readiness
    readiness = manager.validate_production_readiness()
    print(f"Production ready: {readiness['overall_ready']}")

    print("Service manager test completed")
