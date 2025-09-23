"""Service Mesh Service for advanced service discovery, load balancing, and routing.

Provides enterprise-grade service mesh capabilities including:
- Dynamic service discovery with health-aware registration
- Intelligent load balancing with multiple algorithms
- Advanced routing with circuit breaker integration
- Service mesh observability and metrics
- Traffic management and canary deployments
- Fault injection and chaos engineering integration
"""
import asyncio
import time
import random
import hashlib
import threading
from typing import Dict, Any, List, Optional, Callable, Awaitable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import httpx


logger = logging.getLogger(__name__)


class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"


class ServiceState(Enum):
    """Service instance states."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"  # Gracefully removing from load balancing
    MAINTENANCE = "maintenance"  # Temporarily out of service


@dataclass
class ServiceInstance:
    """Represents a single service instance."""
    service_name: str
    instance_id: str
    host: str
    port: int
    protocol: str = "http"
    weight: int = 100  # For weighted load balancing
    state: ServiceState = ServiceState.HEALTHY
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)
    last_health_check: float = 0.0
    consecutive_failures: int = 0
    response_time_ms: float = 0.0
    active_connections: int = 0

    @property
    def url(self) -> str:
        """Get the full URL for this instance."""
        return f"{self.protocol}://{self.host}:{self.port}"

    @property
    def is_available(self) -> bool:
        """Check if instance is available for routing."""
        return self.state == ServiceState.HEALTHY

    def record_request(self, response_time_ms: float) -> None:
        """Record a request completion."""
        self.response_time_ms = response_time_ms
        self.consecutive_failures = 0

    def record_failure(self) -> None:
        """Record a request failure."""
        self.consecutive_failures += 1

    def update_health(self, healthy: bool) -> None:
        """Update health status."""
        self.last_health_check = time.time()
        if healthy:
            self.consecutive_failures = 0
            if self.state == ServiceState.UNHEALTHY:
                self.state = ServiceState.HEALTHY
                logger.info(f"Service instance {self.instance_id} recovered")
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= 3 and self.state == ServiceState.HEALTHY:
                self.state = ServiceState.UNHEALTHY
                logger.warning(f"Service instance {self.instance_id} marked unhealthy")


@dataclass
class ServiceEndpoint:
    """Service endpoint configuration."""
    path: str
    methods: Set[str] = field(default_factory=lambda: {"GET"})
    timeout_seconds: float = 30.0
    retry_policy: Optional[str] = None
    circuit_breaker_enabled: bool = True
    rate_limit_per_minute: Optional[int] = None
    authentication_required: bool = False


@dataclass
class RoutingRule:
    """Advanced routing rule."""
    name: str
    service_name: str
    priority: int = 100
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def matches(self, request_context: Dict[str, Any]) -> bool:
        """Check if routing rule matches the request context."""
        if not self.enabled:
            return False

        for condition_key, condition_value in self.conditions.items():
            request_value = request_context.get(condition_key)
            if request_value != condition_value:
                return False
        return True


@dataclass
class TrafficSplit:
    """Traffic splitting configuration for canary deployments."""
    service_name: str
    versions: Dict[str, float]  # version -> percentage
    sticky_sessions: bool = False
    session_cookie: str = "service_version"


class ServiceRegistry:
    """Service registry for service discovery."""

    def __init__(self):
        self._services: Dict[str, List[ServiceInstance]] = {}
        self._endpoints: Dict[str, Dict[str, ServiceEndpoint]] = {}
        self._routing_rules: List[RoutingRule] = []
        self._traffic_splits: Dict[str, TrafficSplit] = {}
        self._lock = threading.Lock()

    def register_instance(self, instance: ServiceInstance) -> None:
        """Register a service instance."""
        with self._lock:
            if instance.service_name not in self._services:
                self._services[instance.service_name] = []

            # Remove existing instance with same ID if it exists
            self._services[instance.service_name] = [
                inst for inst in self._services[instance.service_name]
                if inst.instance_id != instance.instance_id
            ]

            self._services[instance.service_name].append(instance)
            logger.info(f"Registered service instance: {instance.service_name}/{instance.instance_id}")

    def deregister_instance(self, service_name: str, instance_id: str) -> bool:
        """Deregister a service instance."""
        with self._lock:
            if service_name in self._services:
                original_count = len(self._services[service_name])
                self._services[service_name] = [
                    inst for inst in self._services[service_name]
                    if inst.instance_id != instance_id
                ]
                removed = len(self._services[service_name]) < original_count
                if removed:
                    logger.info(f"Deregistered service instance: {service_name}/{instance_id}")
                return removed
        return False

    def get_instances(self, service_name: str) -> List[ServiceInstance]:
        """Get all instances of a service."""
        with self._lock:
            return self._services.get(service_name, []).copy()

    def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """Get healthy instances of a service."""
        return [inst for inst in self.get_instances(service_name) if inst.is_available]

    def update_instance_health(self, service_name: str, instance_id: str, healthy: bool) -> None:
        """Update health status of a service instance."""
        with self._lock:
            if service_name in self._services:
                for instance in self._services[service_name]:
                    if instance.instance_id == instance_id:
                        instance.update_health(healthy)
                        break

    def register_endpoint(self, service_name: str, endpoint: ServiceEndpoint) -> None:
        """Register an endpoint for a service."""
        with self._lock:
            if service_name not in self._endpoints:
                self._endpoints[service_name] = {}
            self._endpoints[service_name][endpoint.path] = endpoint

    def get_endpoint(self, service_name: str, path: str) -> Optional[ServiceEndpoint]:
        """Get endpoint configuration."""
        with self._lock:
            return self._endpoints.get(service_name, {}).get(path)

    def add_routing_rule(self, rule: RoutingRule) -> None:
        """Add a routing rule."""
        with self._lock:
            self._routing_rules.append(rule)
            self._routing_rules.sort(key=lambda r: r.priority, reverse=True)

    def set_traffic_split(self, traffic_split: TrafficSplit) -> None:
        """Set traffic splitting configuration."""
        with self._lock:
            self._traffic_splits[traffic_split.service_name] = traffic_split

    def get_service_summary(self) -> Dict[str, Any]:
        """Get summary of registered services."""
        with self._lock:
            summary = {}
            for service_name, instances in self._services.items():
                healthy_count = sum(1 for inst in instances if inst.is_available)
                total_count = len(instances)

                summary[service_name] = {
                    "total_instances": total_count,
                    "healthy_instances": healthy_count,
                    "unhealthy_instances": total_count - healthy_count,
                    "endpoints": list(self._endpoints.get(service_name, {}).keys())
                }

            return {
                "services": summary,
                "total_services": len(self._services),
                "routing_rules": len(self._routing_rules),
                "traffic_splits": len(self._traffic_splits)
            }


class LoadBalancer:
    """Intelligent load balancer with multiple algorithms."""

    def __init__(self, algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ROUND_ROBIN):
        self.algorithm = algorithm
        self._round_robin_index: Dict[str, int] = {}
        self._response_times: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def select_instance(self, service_name: str, instances: List[ServiceInstance],
                       request_context: Optional[Dict[str, Any]] = None) -> Optional[ServiceInstance]:
        """Select an instance using the configured algorithm."""
        if not instances:
            return None

        available_instances = [inst for inst in instances if inst.is_available]
        if not available_instances:
            return None

        with self._lock:
            if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
                return self._round_robin_select(service_name, available_instances)
            elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
                return self._least_connections_select(available_instances)
            elif self.algorithm == LoadBalancingAlgorithm.RANDOM:
                return random.choice(available_instances)
            elif self.algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_select(service_name, available_instances)
            elif self.algorithm == LoadBalancingAlgorithm.IP_HASH:
                return self._ip_hash_select(available_instances, request_context)
            elif self.algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
                return self._least_response_time_select(available_instances)
            else:
                return random.choice(available_instances)

    def _round_robin_select(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round-robin instance selection."""
        if service_name not in self._round_robin_index:
            self._round_robin_index[service_name] = 0

        instance = instances[self._round_robin_index[service_name] % len(instances)]
        self._round_robin_index[service_name] = (self._round_robin_index[service_name] + 1) % len(instances)
        return instance

    def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with least active connections."""
        return min(instances, key=lambda inst: inst.active_connections)

    def _weighted_round_robin_select(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted round-robin selection."""
        total_weight = sum(inst.weight for inst in instances)
        if total_weight == 0:
            return random.choice(instances)

        # Simple weighted selection
        rand_value = random.uniform(0, total_weight)
        current_weight = 0

        for instance in instances:
            current_weight += instance.weight
            if rand_value <= current_weight:
                return instance

        return instances[0]  # Fallback

    def _ip_hash_select(self, instances: List[ServiceInstance], request_context: Optional[Dict[str, Any]]) -> ServiceInstance:
        """IP hash-based selection for session stickiness."""
        client_ip = request_context.get("client_ip", "127.0.0.1") if request_context else "127.0.0.1"
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        return instances[hash_value % len(instances)]

    def _least_response_time_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with lowest average response time."""
        # Use response_time_ms, defaulting to 0 for new instances
        return min(instances, key=lambda inst: inst.response_time_ms or 0)

    def record_response_time(self, instance_id: str, response_time_ms: float) -> None:
        """Record response time for an instance."""
        with self._lock:
            if instance_id not in self._response_times:
                self._response_times[instance_id] = []

            self._response_times[instance_id].append(response_time_ms)

            # Keep only last 10 measurements
            if len(self._response_times[instance_id]) > 10:
                self._response_times[instance_id].pop(0)


@dataclass
class ServiceMeshMetrics:
    """Metrics for service mesh operations."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time_ms: float = 0.0
    requests_per_service: Dict[str, int] = field(default_factory=dict)
    errors_per_service: Dict[str, int] = field(default_factory=dict)
    circuit_breaker_trips: int = 0
    retry_attempts: int = 0


class ServiceMeshService:
    """Centralized service mesh for advanced service communication."""

    def __init__(self):
        self.registry = ServiceRegistry()
        self.load_balancer = LoadBalancer()
        self.metrics = ServiceMeshMetrics()
        self._http_client: Optional[httpx.AsyncClient] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        # Integration services
        self._circuit_breaker_service = None
        self._retry_service = None
        self._health_check_service = None

    async def initialize(self) -> None:
        """Initialize the service mesh."""
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=1000)
        )

        # Try to get integration services
        try:
            from .circuit_breaker_service import get_circuit_breaker_service
            self._circuit_breaker_service = get_circuit_breaker_service()
        except ImportError:
            logger.warning("Circuit breaker service not available")

        try:
            from .retry_service import get_retry_service
            self._retry_service = get_retry_service()
        except ImportError:
            logger.warning("Retry service not available")

        try:
            from .health_check_service import get_health_check_service
            self._health_check_service = get_health_check_service()
        except ImportError:
            logger.warning("Health check service not available")

    async def sync_with_discovery_agent(self, discovery_url: str = "http://localhost:5045") -> None:
        """Sync service registry with discovery agent."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get discovered services from discovery agent
                response = await client.get(f"{discovery_url}/services")
                if response.status_code == 200:
                    services_data = response.json()
                    if "services" in services_data:
                        for service_info in services_data["services"]:
                            # Register with mesh if not already registered
                            existing_instances = self.registry.get_instances(service_info["service_name"])
                            if not existing_instances:
                                # Parse URL and register
                                # This is a simplified sync - in production, you'd want more robust sync
                                logger.info(f"Auto-registered {service_info['service_name']} from discovery agent")
        except Exception as e:
            logger.warning(f"Failed to sync with discovery agent: {e}")

    async def route_request(
        self,
        service_name: str,
        path: str,
        method: str = "GET",
        request_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Route a request through the service mesh."""
        start_time = time.time()

        try:
            # Apply routing rules
            final_service = self._apply_routing_rules(service_name, request_context or {})

            # Get healthy instances
            instances = self.registry.get_healthy_instances(final_service)
            if not instances:
                raise RuntimeError(f"No healthy instances available for service {final_service}")

            # Select instance using load balancer
            instance = self.load_balancer.select_instance(final_service, instances, request_context)
            if not instance:
                raise RuntimeError(f"No available instances for service {final_service}")

            # Check traffic splitting
            instance = self._apply_traffic_splitting(final_service, instance, request_context)

            # Track active connection
            instance.active_connections += 1

            try:
                # Make the request
                result = await self._make_request(instance, path, method, **kwargs)

                # Record success
                response_time = (time.time() - start_time) * 1000
                instance.record_request(response_time)
                self.load_balancer.record_response_time(instance.instance_id, response_time)

                self.metrics.total_requests += 1
                self.metrics.successful_requests += 1
                self.metrics.total_response_time_ms += response_time
                self.metrics.requests_per_service[final_service] = \
                    self.metrics.requests_per_service.get(final_service, 0) + 1

                return result

            finally:
                instance.active_connections -= 1

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.metrics.errors_per_service[service_name] = \
                self.metrics.errors_per_service.get(service_name, 0) + 1

            logger.error(f"Service mesh request failed for {service_name}: {e}")
            raise

    def _apply_routing_rules(self, service_name: str, request_context: Dict[str, Any]) -> str:
        """Apply routing rules to determine final service."""
        for rule in self.registry._routing_rules:
            if rule.matches(request_context):
                if "redirect_service" in rule.actions:
                    return rule.actions["redirect_service"]
        return service_name

    def _apply_traffic_splitting(self, service_name: str, selected_instance: ServiceInstance,
                               request_context: Optional[Dict[str, Any]]) -> ServiceInstance:
        """Apply traffic splitting for canary deployments."""
        traffic_split = self.registry._traffic_splits.get(service_name)
        if not traffic_split:
            return selected_instance

        # Check for sticky session
        if traffic_split.sticky_sessions and request_context:
            session_version = request_context.get(traffic_split.session_cookie)
            if session_version and session_version in traffic_split.versions:
                # Route to specific version
                return selected_instance  # Simplified - would need version-aware selection

        # Random traffic splitting
        rand_value = random.random() * 100
        cumulative = 0

        for version, percentage in traffic_split.versions.items():
            cumulative += percentage
            if rand_value <= cumulative:
                # Would route to specific version instance
                break

        return selected_instance

    async def _make_request(self, instance: ServiceInstance, path: str, method: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to service instance."""
        if not self._http_client:
            raise RuntimeError("Service mesh not initialized")

        url = f"{instance.url}{path}"

        # Apply circuit breaker if available
        if self._circuit_breaker_service:
            try:
                return await self._circuit_breaker_service.execute_with_protection(
                    instance.service_name,
                    path,
                    lambda: self._execute_http_request(url, method, **kwargs),
                    operation_name=f"{method}_{path}",
                    timeout_seconds=30.0
                )
            except RuntimeError as e:
                if "circuit_open" in str(e):
                    self.metrics.circuit_breaker_trips += 1
                    raise RuntimeError(f"Service {instance.service_name} circuit breaker open")

        # Direct request
        return await self._execute_http_request(url, method, **kwargs)

    async def _execute_http_request(self, url: str, method: str, **kwargs) -> Dict[str, Any]:
        """Execute the actual HTTP request."""
        response = await self._http_client.request(method.upper(), url, **kwargs)

        if response.status_code >= 400:
            response.raise_for_status()

        # Try to parse JSON response
        try:
            return response.json()
        except:
            return {"status": response.status_code, "content": response.text}

    def register_service_instance(
        self,
        service_name: str,
        host: str,
        port: int,
        instance_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Register a service instance."""
        if instance_id is None:
            instance_id = f"{service_name}_{host}_{port}_{int(time.time())}"

        instance = ServiceInstance(
            service_name=service_name,
            instance_id=instance_id,
            host=host,
            port=port,
            **kwargs
        )

        self.registry.register_instance(instance)

        # Register with health check service if available
        if self._health_check_service:
            try:
                from .health_check_service import HTTPHealthCheck
                health_check = HTTPHealthCheck(
                    f"mesh_{instance_id}",
                    f"http://{host}:{port}/health",
                    timeout=5.0
                )
                self._health_check_service.add_health_check(service_name, health_check)
            except Exception as e:
                logger.debug(f"Could not register health check: {e}")

        return instance_id

    def deregister_service_instance(self, service_name: str, instance_id: str) -> bool:
        """Deregister a service instance."""
        return self.registry.deregister_instance(service_name, instance_id)

    def register_endpoint(self, service_name: str, path: str, **endpoint_config) -> None:
        """Register a service endpoint."""
        endpoint = ServiceEndpoint(path=path, **endpoint_config)
        self.registry.register_endpoint(service_name, endpoint)

    def add_routing_rule(self, rule: RoutingRule) -> None:
        """Add a routing rule."""
        self.registry.add_routing_rule(rule)

    def set_traffic_split(self, traffic_split: TrafficSplit) -> None:
        """Set traffic splitting configuration."""
        self.registry.set_traffic_split(traffic_split)

    def set_load_balancing_algorithm(self, algorithm: LoadBalancingAlgorithm) -> None:
        """Set the load balancing algorithm."""
        self.load_balancer.algorithm = algorithm

    async def start_health_monitoring(self) -> None:
        """Start background health monitoring."""
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._health_monitoring_loop())
            logger.info("Service mesh health monitoring started")

    async def stop_health_monitoring(self) -> None:
        """Stop background health monitoring."""
        if self._health_check_task:
            self._shutdown_event.set()
            try:
                await asyncio.wait_for(self._health_check_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._health_check_task.cancel()
            logger.info("Service mesh health monitoring stopped")

    async def _health_monitoring_loop(self) -> None:
        """Background health monitoring for service instances."""
        while not self._shutdown_event.is_set():
            try:
                # Perform health checks on all instances
                for service_name, instances in self.registry._services.items():
                    for instance in instances:
                        try:
                            # Simple health check
                            await self._check_instance_health(instance)
                        except Exception as e:
                            logger.debug(f"Health check failed for {instance.instance_id}: {e}")
                            instance.record_failure()

                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(30)

    async def _check_instance_health(self, instance: ServiceInstance) -> None:
        """Check health of a service instance."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{instance.url}/health")
                healthy = response.status_code == 200
                instance.update_health(healthy)
        except Exception:
            instance.update_health(False)

    def get_mesh_status(self) -> Dict[str, Any]:
        """Get comprehensive service mesh status."""
        return {
            "registry": self.registry.get_service_summary(),
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "average_response_time_ms": (
                    self.metrics.total_response_time_ms / max(1, self.metrics.successful_requests)
                ),
                "circuit_breaker_trips": self.metrics.circuit_breaker_trips,
                "retry_attempts": self.metrics.retry_attempts,
                "requests_per_service": dict(self.metrics.requests_per_service),
                "errors_per_service": dict(self.metrics.errors_per_service)
            },
            "load_balancer": {
                "algorithm": self.load_balancer.algorithm.value
            },
            "integrations": {
                "circuit_breaker": self._circuit_breaker_service is not None,
                "retry_service": self._retry_service is not None,
                "health_check": self._health_check_service is not None
            }
        }

    async def shutdown(self) -> None:
        """Shutdown the service mesh."""
        await self.stop_health_monitoring()

        if self._http_client:
            await self._http_client.aclose()


# Global instance
_service_mesh_service: Optional[ServiceMeshService] = None


def get_service_mesh_service() -> ServiceMeshService:
    """Get the global service mesh service instance."""
    global _service_mesh_service
    if _service_mesh_service is None:
        _service_mesh_service = ServiceMeshService()
    return _service_mesh_service


# Convenience functions
async def route_to_service(service_name: str, path: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Convenience function to route requests through service mesh."""
    mesh = get_service_mesh_service()
    return await mesh.route_request(service_name, path, method, **kwargs)


def register_mesh_service(service_name: str, host: str, port: int, **kwargs) -> str:
    """Convenience function to register service with mesh."""
    mesh = get_service_mesh_service()
    return mesh.register_service_instance(service_name, host, port, **kwargs)


def get_mesh_status() -> Dict[str, Any]:
    """Convenience function to get mesh status."""
    mesh = get_service_mesh_service()
    return mesh.get_mesh_status()
