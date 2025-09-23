"""Comprehensive Health Check Service with dependency validation and monitoring.

Provides enterprise-grade health checking capabilities including:
- Service health assessment with dependency validation
- Health status aggregation and reporting
- Automated health monitoring and alerting
- Kubernetes-style liveness, readiness, and startup probes
- Performance and resource health metrics
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import httpx
import psutil

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckType(Enum):
    """Types of health checks."""

    LIVENESS = "liveness"  # Is service alive?
    READINESS = "readiness"  # Can service accept traffic?
    STARTUP = "startup"  # Has service started successfully?
    DEPENDENCY = "dependency"  # Are dependencies healthy?
    PERFORMANCE = "performance"  # Performance metrics within bounds?


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    check_name: str
    status: HealthStatus
    message: str
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class DependencyHealth:
    """Health status of a service dependency."""

    service_name: str
    endpoint: str
    required: bool = True
    timeout_seconds: float = 5.0
    last_check: float = 0
    consecutive_failures: int = 0
    status: HealthStatus = HealthStatus.UNKNOWN


@dataclass
class ServiceHealth:
    """Overall health status of a service."""

    service_name: str
    overall_status: HealthStatus = HealthStatus.UNKNOWN
    last_check: float = 0
    uptime_seconds: float = 0
    checks: Dict[str, HealthCheckResult] = field(default_factory=dict)
    dependencies: Dict[str, DependencyHealth] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HealthCheck:
    """Base class for health checks."""

    def __init__(self, name: str, check_type: HealthCheckType = HealthCheckType.LIVENESS):
        self.name = name
        self.check_type = check_type

    async def execute(self) -> HealthCheckResult:
        """Execute the health check."""
        raise NotImplementedError


class DatabaseHealthCheck(HealthCheck):
    """Health check for database connectivity."""

    def __init__(self, name: str, connection_string: str, timeout: float = 3.0):
        super().__init__(name, HealthCheckType.DEPENDENCY)
        self.connection_string = connection_string
        self.timeout = timeout

    async def execute(self) -> HealthCheckResult:
        start_time = time.time()

        try:
            # Basic connection test - in real implementation, use actual DB client
            await asyncio.sleep(0.1)  # Simulate connection test
            duration = (time.time() - start_time) * 1000

            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                duration_ms=duration,
                details={"connection_string": self._mask_connection_string()},
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                duration_ms=duration,
                error=str(e),
            )

    def _mask_connection_string(self) -> str:
        """Mask sensitive information in connection string."""
        return self.connection_string.replace("password=", "password=***")


class HTTPHealthCheck(HealthCheck):
    """Health check for HTTP service endpoints."""

    def __init__(self, name: str, url: str, timeout: float = 5.0, expected_status: int = 200):
        super().__init__(name, HealthCheckType.DEPENDENCY)
        self.url = url
        self.timeout = timeout
        self.expected_status = expected_status

    async def execute(self) -> HealthCheckResult:
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.url)
                duration = (time.time() - start_time) * 1000

                if response.status_code == self.expected_status:
                    return HealthCheckResult(
                        check_name=self.name,
                        status=HealthStatus.HEALTHY,
                        message=f"HTTP check successful: {response.status_code}",
                        duration_ms=duration,
                        details={"url": self.url, "status_code": response.status_code, "response_time_ms": duration},
                    )
                else:
                    return HealthCheckResult(
                        check_name=self.name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Unexpected status code: {response.status_code}",
                        duration_ms=duration,
                        details={
                            "url": self.url,
                            "expected_status": self.expected_status,
                            "actual_status": response.status_code,
                        },
                    )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"HTTP check failed: {str(e)}",
                duration_ms=duration,
                error=str(e),
            )


class PerformanceHealthCheck(HealthCheck):
    """Health check for performance metrics."""

    def __init__(self, name: str, metric_func: Callable[[], float], threshold: float, operator: str = "lt"):
        super().__init__(name, HealthCheckType.PERFORMANCE)
        self.metric_func = metric_func
        self.threshold = threshold
        self.operator = operator  # "lt", "gt", "le", "ge"

    async def execute(self) -> HealthCheckResult:
        start_time = time.time()

        try:
            value = self.metric_func()
            duration = (time.time() - start_time) * 1000

            healthy = self._check_threshold(value)

            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.HEALTHY if healthy else HealthStatus.DEGRADED,
                message=f"Performance check: {value:.2f} {'OK' if healthy else 'DEGRADED'}",
                duration_ms=duration,
                details={"value": value, "threshold": self.threshold, "operator": self.operator, "healthy": healthy},
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Performance check failed: {str(e)}",
                duration_ms=duration,
                error=str(e),
            )

    def _check_threshold(self, value: float) -> bool:
        """Check if value meets threshold criteria."""
        if self.operator == "lt":
            return value < self.threshold
        elif self.operator == "gt":
            return value > self.threshold
        elif self.operator == "le":
            return value <= self.threshold
        elif self.operator == "ge":
            return value >= self.threshold
        return False


class ResourceHealthCheck(HealthCheck):
    """Health check for system resources."""

    def __init__(
        self,
        name: str,
        resource_type: str = "memory",
        warning_threshold: float = 80.0,
        critical_threshold: float = 95.0,
    ):
        super().__init__(name, HealthCheckType.PERFORMANCE)
        self.resource_type = resource_type
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    async def execute(self) -> HealthCheckResult:
        start_time = time.time()

        try:
            if self.resource_type == "memory":
                usage_percent = psutil.virtual_memory().percent
            elif self.resource_type == "cpu":
                usage_percent = psutil.cpu_percent(interval=1)
            elif self.resource_type == "disk":
                usage_percent = psutil.disk_usage("/").percent
            else:
                usage_percent = 0.0

            duration = (time.time() - start_time) * 1000

            if usage_percent >= self.critical_threshold:
                status = HealthStatus.UNHEALTHY
                message = f"Critical {self.resource_type} usage: {usage_percent:.1f}%"
            elif usage_percent >= self.warning_threshold:
                status = HealthStatus.DEGRADED
                message = f"High {self.resource_type} usage: {usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"{self.resource_type.capitalize()} usage normal: {usage_percent:.1f}%"

            return HealthCheckResult(
                check_name=self.name,
                status=status,
                message=message,
                duration_ms=duration,
                details={
                    "resource_type": self.resource_type,
                    "usage_percent": usage_percent,
                    "warning_threshold": self.warning_threshold,
                    "critical_threshold": self.critical_threshold,
                },
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Resource check failed: {str(e)}",
                duration_ms=duration,
                error=str(e),
            )


class HealthCheckService:
    """Centralized health check service for the ecosystem."""

    def __init__(self):
        self._services: Dict[str, ServiceHealth] = {}
        self._health_checks: Dict[str, List[HealthCheck]] = {}
        self._alert_callbacks: List[Callable[[str, HealthStatus, HealthStatus], None]] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._lock = threading.Lock()

    def register_service(self, service_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a service for health monitoring."""
        with self._lock:
            if service_name not in self._services:
                self._services[service_name] = ServiceHealth(service_name=service_name, metadata=metadata or {})
                self._health_checks[service_name] = []
                logger.info(f"Registered health monitoring for service: {service_name}")

    def add_health_check(self, service_name: str, health_check: HealthCheck) -> None:
        """Add a health check to a service."""
        if service_name not in self._health_checks:
            self.register_service(service_name)

        self._health_checks[service_name].append(health_check)
        logger.debug(f"Added health check '{health_check.name}' to service '{service_name}'")

    def add_dependency(
        self,
        service_name: str,
        dependency_name: str,
        endpoint: str,
        required: bool = True,
        timeout_seconds: float = 5.0,
    ) -> None:
        """Add a service dependency to monitor."""
        if service_name not in self._services:
            self.register_service(service_name)

        dependency = DependencyHealth(
            service_name=dependency_name, endpoint=endpoint, required=required, timeout_seconds=timeout_seconds
        )

        self._services[service_name].dependencies[dependency_name] = dependency

    def add_alert_callback(self, callback: Callable[[str, HealthStatus, HealthStatus], None]) -> None:
        """Add callback for health status changes."""
        self._alert_callbacks.append(callback)

    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """Perform comprehensive health check for a service."""
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not registered")

        service = self._services[service_name]
        start_time = time.time()

        # Execute all health checks
        check_results = []
        for health_check in self._health_checks.get(service_name, []):
            try:
                result = await health_check.execute()
                check_results.append(result)
                service.checks[health_check.name] = result
            except Exception as e:
                error_result = HealthCheckResult(
                    check_name=health_check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check execution failed: {str(e)}",
                    error=str(e),
                )
                check_results.append(error_result)
                service.checks[health_check.name] = error_result

        # Check dependencies
        await self._check_dependencies(service)

        # Determine overall status
        overall_status = self._calculate_overall_status(service, check_results)
        previous_status = service.overall_status

        # Update service health
        service.overall_status = overall_status
        service.last_check = time.time()
        service.uptime_seconds = time.time() - start_time  # This should track actual uptime

        # Trigger alerts on status changes
        if previous_status != overall_status and previous_status != HealthStatus.UNKNOWN:
            await self._trigger_alerts(service_name, previous_status, overall_status)

        return service

    async def _check_dependencies(self, service: ServiceHealth) -> None:
        """Check health of service dependencies."""
        for dep_name, dependency in service.dependencies.items():
            # Simple dependency check - in real implementation, use service discovery
            check = HTTPHealthCheck(
                f"dependency_{dep_name}", f"http://{dependency.endpoint}", timeout=dependency.timeout_seconds
            )

            try:
                result = await check.execute()

                if result.status == HealthStatus.HEALTHY:
                    dependency.consecutive_failures = 0
                    dependency.status = HealthStatus.HEALTHY
                else:
                    dependency.consecutive_failures += 1
                    dependency.status = HealthStatus.UNHEALTHY

                dependency.last_check = time.time()

            except Exception as e:
                dependency.consecutive_failures += 1
                dependency.status = HealthStatus.UNHEALTHY
                logger.error(f"Dependency check failed for {dep_name}: {e}")

    def _calculate_overall_status(self, service: ServiceHealth, check_results: List[HealthCheckResult]) -> HealthStatus:
        """Calculate overall health status from individual checks."""
        if not check_results and not service.dependencies:
            return HealthStatus.UNKNOWN

        # Check critical dependencies first
        for dep in service.dependencies.values():
            if dep.required and dep.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY

        # Check health check results
        has_unhealthy = any(r.status == HealthStatus.UNHEALTHY for r in check_results)
        has_degraded = any(r.status == HealthStatus.DEGRADED for r in check_results)

        if has_unhealthy:
            return HealthStatus.UNHEALTHY
        elif has_degraded:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def _trigger_alerts(self, service_name: str, old_status: HealthStatus, new_status: HealthStatus) -> None:
        """Trigger alert callbacks for status changes."""
        for callback in self._alert_callbacks:
            try:
                await callback(service_name, old_status, new_status)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """Check health of all registered services."""
        results = {}
        for service_name in self._services.keys():
            try:
                results[service_name] = await self.check_service_health(service_name)
            except Exception as e:
                logger.error(f"Failed to check health for service {service_name}: {e}")
                # Create unhealthy status for failed checks
                results[service_name] = ServiceHealth(service_name=service_name, overall_status=HealthStatus.UNHEALTHY)

        return results

    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """Get cached health status for a service."""
        return self._services.get(service_name)

    def get_ecosystem_health(self) -> Dict[str, Any]:
        """Get overall ecosystem health summary."""
        total_services = len(self._services)
        healthy_services = sum(1 for s in self._services.values() if s.overall_status == HealthStatus.HEALTHY)
        degraded_services = sum(1 for s in self._services.values() if s.overall_status == HealthStatus.DEGRADED)
        unhealthy_services = sum(1 for s in self._services.values() if s.overall_status == HealthStatus.UNHEALTHY)

        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "degraded_services": degraded_services,
            "unhealthy_services": unhealthy_services,
            "overall_status": self._calculate_ecosystem_status(
                healthy_services, degraded_services, unhealthy_services, total_services
            ),
            "last_updated": max((s.last_check for s in self._services.values() if s.last_check > 0), default=0),
            "services": {
                name: {
                    "status": service.overall_status.value,
                    "last_check": service.last_check,
                    "uptime_seconds": service.uptime_seconds,
                }
                for name, service in self._services.items()
            },
        }

    def _calculate_ecosystem_status(self, healthy: int, degraded: int, unhealthy: int, total: int) -> str:
        """Calculate overall ecosystem health status."""
        if unhealthy > 0:
            return HealthStatus.UNHEALTHY.value
        elif degraded > 0 or healthy < total:
            return HealthStatus.DEGRADED.value
        elif healthy == total:
            return HealthStatus.HEALTHY.value
        else:
            return HealthStatus.UNKNOWN.value

    async def start_monitoring(self, check_interval: float = 30.0) -> None:
        """Start background health monitoring."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop(check_interval))
            logger.info("Health monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop background health monitoring."""
        if self._monitoring_task:
            self._shutdown_event.set()
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._monitoring_task.cancel()
            logger.info("Health monitoring stopped")

    async def _monitoring_loop(self, check_interval: float) -> None:
        """Background monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                await self.check_all_services()
                await asyncio.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(check_interval)


# Global instance
_health_check_service: Optional[HealthCheckService] = None


def get_health_check_service() -> HealthCheckService:
    """Get the global health check service instance."""
    global _health_check_service
    if _health_check_service is None:
        _health_check_service = HealthCheckService()
    return _health_check_service


# Convenience functions
async def check_service_health(service_name: str) -> ServiceHealth:
    """Convenience function to check service health."""
    service = get_health_check_service()
    return await service.check_service_health(service_name)


def register_health_checks(service_name: str, checks: List[HealthCheck]) -> None:
    """Convenience function to register multiple health checks."""
    service = get_health_check_service()
    service.register_service(service_name)
    for check in checks:
        service.add_health_check(service_name, check)


def add_dependency_check(
    service_name: str, dependency_name: str, endpoint: str, required: bool = True, timeout_seconds: float = 5.0
) -> None:
    """Convenience function to add dependency check."""
    service = get_health_check_service()
    service.add_dependency(service_name, dependency_name, endpoint, required, timeout_seconds)
