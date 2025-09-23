"""Kubernetes Probes Service for container orchestration health checks.

Provides standard Kubernetes probe endpoints that integrate with the comprehensive
health check infrastructure:
- Liveness Probe: Is the application alive?
- Readiness Probe: Can the application accept traffic?
- Startup Probe: Has the application started successfully?

These probes leverage the existing health check service for comprehensive validation.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProbeConfig:
    """Configuration for Kubernetes probes."""

    enabled: bool = True
    timeout_seconds: float = 5.0
    initial_delay_seconds: float = 0.0
    period_seconds: float = 10.0
    failure_threshold: int = 3
    success_threshold: int = 1

    # Readiness-specific config
    readiness_check_dependencies: bool = True
    readiness_check_resources: bool = True

    # Startup-specific config
    startup_timeout_seconds: float = 60.0


@dataclass
class ProbeResult:
    """Result of a probe check."""

    healthy: bool
    status_code: int  # HTTP status code
    message: str
    details: Dict[str, Any]
    response_time: float
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class KubernetesProbesService:
    """Service for providing Kubernetes probe endpoints."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.startup_time = time.time()

        # Default probe configurations
        self.liveness_config = ProbeConfig(timeout_seconds=3.0, period_seconds=30.0, failure_threshold=3)

        self.readiness_config = ProbeConfig(
            timeout_seconds=5.0,
            period_seconds=10.0,
            failure_threshold=3,
            readiness_check_dependencies=True,
            readiness_check_resources=True,
        )

        self.startup_config = ProbeConfig(timeout_seconds=10.0, startup_timeout_seconds=60.0)

        # Probe state
        self._last_liveness_check = 0.0
        self._last_readiness_check = 0.0
        self._startup_complete = False
        self._startup_completed_at = None

        # Integration with existing services
        self._health_check_service = None
        self._circuit_breaker_service = None
        self._process_monitor_service = None

        # Custom probe functions
        self._custom_liveness_checks: list = []
        self._custom_readiness_checks: list = []
        self._custom_startup_checks: list = []

        # Initialize integrations
        self._initialize_integrations()

    def _initialize_integrations(self):
        """Initialize integrations with existing services."""
        try:
            from .health_check_service import get_health_check_service

            self._health_check_service = get_health_check_service()
        except ImportError:
            logger.warning("Health check service not available for Kubernetes probes")

        try:
            from .circuit_breaker_service import get_circuit_breaker_service

            self._circuit_breaker_service = get_circuit_breaker_service()
        except ImportError:
            logger.warning("Circuit breaker service not available for Kubernetes probes")

        try:
            from .process_monitor_service import get_process_monitor_service

            self._process_monitor_service = get_process_monitor_service()
        except ImportError:
            logger.warning("Process monitor service not available for Kubernetes probes")

    def add_custom_liveness_check(self, check_func: Callable[[], bool], description: str = ""):
        """Add a custom liveness check function."""
        self._custom_liveness_checks.append((check_func, description))

    def add_custom_readiness_check(self, check_func: Callable[[], bool], description: str = ""):
        """Add a custom readiness check function."""
        self._custom_readiness_checks.append((check_func, description))

    def add_custom_startup_check(self, check_func: Callable[[], bool], description: str = ""):
        """Add a custom startup check function."""
        self._custom_startup_checks.append((check_func, description))

    def configure_liveness_probe(self, config: ProbeConfig):
        """Configure the liveness probe."""
        self.liveness_config = config

    def configure_readiness_probe(self, config: ProbeConfig):
        """Configure the readiness probe."""
        self.readiness_config = config

    def configure_startup_probe(self, config: ProbeConfig):
        """Configure the startup probe."""
        self.startup_config = config

    async def liveness_probe(self) -> ProbeResult:
        """Kubernetes liveness probe endpoint.

        Liveness probes determine if the application is alive.
        If this fails, Kubernetes will restart the container.
        """
        start_time = time.time()

        try:
            # Basic liveness checks
            issues = []

            # Check if process is responsive (basic health)
            if not await self._check_basic_health():
                issues.append("Basic health check failed")

            # Check for critical resource exhaustion
            if not await self._check_critical_resources():
                issues.append("Critical resource exhaustion detected")

            # Run custom liveness checks
            for check_func, description in self._custom_liveness_checks:
                try:
                    if not check_func():
                        issues.append(f"Custom liveness check failed: {description}")
                except Exception as e:
                    issues.append(f"Custom liveness check error ({description}): {str(e)}")

            self._last_liveness_check = time.time()
            response_time = time.time() - start_time

            if issues:
                return ProbeResult(
                    healthy=False,
                    status_code=503,  # Service Unavailable
                    message="Liveness check failed",
                    details={"issues": issues},
                    response_time=response_time,
                )
            else:
                return ProbeResult(
                    healthy=True,
                    status_code=200,  # OK
                    message="Application is alive",
                    details={"checks_passed": len(self._custom_liveness_checks) + 2},
                    response_time=response_time,
                )

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Liveness probe error: {e}")
            return ProbeResult(
                healthy=False,
                status_code=500,  # Internal Server Error
                message=f"Liveness probe error: {str(e)}",
                details={"error": str(e)},
                response_time=response_time,
            )

    async def readiness_probe(self) -> ProbeResult:
        """Kubernetes readiness probe endpoint.

        Readiness probes determine if the application can accept traffic.
        If this fails, Kubernetes will remove the pod from service endpoints.
        """
        start_time = time.time()

        try:
            issues = []

            # Check if application has completed startup
            if not self._startup_complete:
                issues.append("Application startup not complete")

            # Check dependencies if configured
            if self.readiness_config.readiness_check_dependencies:
                if not await self._check_dependencies():
                    issues.append("Service dependencies not healthy")

            # Check resource availability if configured
            if self.readiness_config.readiness_check_resources:
                if not await self._check_resource_availability():
                    issues.append("Insufficient resources available")

            # Check circuit breaker state
            if not await self._check_circuit_breaker_state():
                issues.append("Circuit breaker in open state")

            # Run custom readiness checks
            for check_func, description in self._custom_readiness_checks:
                try:
                    if not check_func():
                        issues.append(f"Custom readiness check failed: {description}")
                except Exception as e:
                    issues.append(f"Custom readiness check error ({description}): {str(e)}")

            self._last_readiness_check = time.time()
            response_time = time.time() - start_time

            if issues:
                return ProbeResult(
                    healthy=False,
                    status_code=503,  # Service Unavailable
                    message="Application not ready to accept traffic",
                    details={"issues": issues},
                    response_time=response_time,
                )
            else:
                return ProbeResult(
                    healthy=True,
                    status_code=200,  # OK
                    message="Application is ready to accept traffic",
                    details={"checks_passed": len(self._custom_readiness_checks) + 4},
                    response_time=response_time,
                )

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Readiness probe error: {e}")
            return ProbeResult(
                healthy=False,
                status_code=500,  # Internal Server Error
                message=f"Readiness probe error: {str(e)}",
                details={"error": str(e)},
                response_time=response_time,
            )

    async def startup_probe(self) -> ProbeResult:
        """Kubernetes startup probe endpoint.

        Startup probes determine if the application has started successfully.
        Used during the initial startup period before readiness probes begin.
        """
        start_time = time.time()

        try:
            # Check startup timeout
            elapsed_time = time.time() - self.startup_time
            if elapsed_time > self.startup_config.startup_timeout_seconds:
                return ProbeResult(
                    healthy=False,
                    status_code=500,  # Internal Server Error
                    message=f"Startup timeout exceeded ({elapsed_time:.1f}s > {self.startup_config.startup_timeout_seconds}s)",
                    details={"elapsed_time": elapsed_time, "timeout": self.startup_config.startup_timeout_seconds},
                    response_time=time.time() - start_time,
                )

            issues = []

            # Basic startup checks
            if not await self._check_basic_health():
                issues.append("Basic health check failed during startup")

            # Run custom startup checks
            for check_func, description in self._custom_startup_checks:
                try:
                    if not check_func():
                        issues.append(f"Custom startup check failed: {description}")
                except Exception as e:
                    issues.append(f"Custom startup check error ({description}): {str(e)}")

            response_time = time.time() - start_time

            if issues:
                return ProbeResult(
                    healthy=False,
                    status_code=503,  # Service Unavailable
                    message="Application startup not complete",
                    details={"issues": issues},
                    response_time=response_time,
                )
            else:
                # Mark startup as complete
                if not self._startup_complete:
                    self._startup_complete = True
                    self._startup_completed_at = time.time()
                    logger.info(f"Application {self.service_name} startup completed successfully")

                return ProbeResult(
                    healthy=True,
                    status_code=200,  # OK
                    message="Application startup completed successfully",
                    details={"checks_passed": len(self._custom_startup_checks) + 1},
                    response_time=response_time,
                )

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Startup probe error: {e}")
            return ProbeResult(
                healthy=False,
                status_code=500,  # Internal Server Error
                message=f"Startup probe error: {str(e)}",
                details={"error": str(e)},
                response_time=response_time,
            )

    async def _check_basic_health(self) -> bool:
        """Check basic application health."""
        try:
            # Simple health check - ensure we can respond
            return True
        except Exception:
            return False

    async def _check_critical_resources(self) -> bool:
        """Check for critical resource exhaustion."""
        if not self._process_monitor_service:
            return True  # Assume healthy if no monitoring available

        try:
            summary = self._process_monitor_service.get_resource_summary()

            # Check memory usage (critical threshold)
            memory_usage = summary.get("memory", {}).get("current_value", 0)
            memory_threshold = self._process_monitor_service.resource_thresholds.get("memory")
            if memory_threshold and memory_usage >= memory_threshold.emergency_threshold:
                return False

            # Check if there are any critical alerts
            alerts = self._process_monitor_service.check_thresholds()
            critical_alerts = [a for a in alerts if a.severity.value == "critical"]
            if critical_alerts:
                return False

            return True
        except Exception as e:
            logger.debug(f"Resource check failed: {e}")
            return True  # Don't fail probe due to monitoring issues

    async def _check_dependencies(self) -> bool:
        """Check if service dependencies are healthy."""
        if not self._health_check_service:
            return True  # Assume healthy if no health service available

        try:
            ecosystem_health = self._health_check_service.get_ecosystem_health()

            # Check if our service is healthy
            our_health = ecosystem_health.get("services", {}).get(self.service_name, {})
            if our_health.get("status") != "healthy":
                return False

            # Check if most services are healthy (allow some degradation)
            total_services = ecosystem_health.get("total_services", 0)
            healthy_services = ecosystem_health.get("healthy_services", 0)
            health_ratio = healthy_services / max(total_services, 1)

            # Require at least 80% of services to be healthy
            return health_ratio >= 0.8
        except Exception as e:
            logger.debug(f"Dependency check failed: {e}")
            return True  # Don't fail probe due to health check issues

    async def _check_resource_availability(self) -> bool:
        """Check if sufficient resources are available."""
        if not self._process_monitor_service:
            return True

        try:
            summary = self._process_monitor_service.get_resource_summary()

            # Check various resource levels
            for resource_name, resource_data in summary.items():
                if resource_name == "memory":
                    current = resource_data.get("current_value", 0)
                    warning = resource_data.get("thresholds", {}).get("warning", float("inf"))
                    if current >= warning * 0.9:  # 90% of warning threshold
                        return False

            return True
        except Exception as e:
            logger.debug(f"Resource availability check failed: {e}")
            return True

    async def _check_circuit_breaker_state(self) -> bool:
        """Check if circuit breaker is in a good state."""
        if not self._circuit_breaker_service:
            return True

        try:
            status = self._circuit_breaker_service.get_ecosystem_health()

            # Check if circuit breaker is open (too many failures)
            total_open = status.get("total_circuits_open", 0)
            total_half_open = status.get("total_circuits_half_open", 0)

            # Allow some circuit breakers to be open/half-open, but not too many
            total_circuits = status.get("total_services", 0)
            if total_circuits > 0:
                open_ratio = (total_open + total_half_open) / total_circuits
                return open_ratio < 0.5  # Less than 50% of circuits open/half-open

            return True
        except Exception as e:
            logger.debug(f"Circuit breaker check failed: {e}")
            return True

    def get_probe_status(self) -> Dict[str, Any]:
        """Get comprehensive probe status."""
        return {
            "service_name": self.service_name,
            "startup_complete": self._startup_complete,
            "startup_completed_at": self._startup_completed_at,
            "last_liveness_check": self._last_liveness_check,
            "last_readiness_check": self._last_readiness_check,
            "uptime_seconds": time.time() - self.startup_time,
            "liveness_config": {
                "enabled": self.liveness_config.enabled,
                "timeout_seconds": self.liveness_config.timeout_seconds,
                "period_seconds": self.liveness_config.period_seconds,
                "failure_threshold": self.liveness_config.failure_threshold,
            },
            "readiness_config": {
                "enabled": self.readiness_config.enabled,
                "timeout_seconds": self.readiness_config.timeout_seconds,
                "period_seconds": self.readiness_config.period_seconds,
                "failure_threshold": self.readiness_config.failure_threshold,
                "check_dependencies": self.readiness_config.readiness_check_dependencies,
                "check_resources": self.readiness_config.readiness_check_resources,
            },
            "startup_config": {
                "enabled": self.startup_config.enabled,
                "timeout_seconds": self.startup_config.startup_timeout_seconds,
            },
            "integrations": {
                "health_check_service": self._health_check_service is not None,
                "circuit_breaker_service": self._circuit_breaker_service is not None,
                "process_monitor_service": self._process_monitor_service is not None,
            },
        }

    def create_fastapi_routes(self):
        """Create FastAPI route functions for the probes.

        Returns a dictionary of route functions that can be added to a FastAPI app.
        """

        async def liveness():
            result = await self.liveness_probe()
            return {
                "status": "alive" if result.healthy else "dead",
                "message": result.message,
                "details": result.details,
                "response_time": f"{result.response_time:.3f}s",
            }

        async def readiness():
            result = await self.readiness_probe()
            return {
                "status": "ready" if result.healthy else "not_ready",
                "message": result.message,
                "details": result.details,
                "response_time": f"{result.response_time:.3f}s",
            }

        async def startup():
            result = await self.startup_probe()
            return {
                "status": "started" if result.healthy else "starting",
                "message": result.message,
                "details": result.details,
                "response_time": f"{result.response_time:.3f}s",
            }

        return {"/health/liveness": liveness, "/health/readiness": readiness, "/health/startup": startup}


# Global instance function
def create_kubernetes_probes_service(service_name: str) -> KubernetesProbesService:
    """Create a Kubernetes probes service for a given service."""
    return KubernetesProbesService(service_name)


# Convenience functions for common configurations
def create_standard_probes(service_name: str) -> KubernetesProbesService:
    """Create probes with standard Kubernetes configurations."""
    probes = KubernetesProbesService(service_name)

    # Configure standard timeouts and intervals
    probes.configure_liveness_probe(ProbeConfig(timeout_seconds=3.0, period_seconds=30.0, failure_threshold=3))

    probes.configure_readiness_probe(
        ProbeConfig(
            timeout_seconds=5.0,
            period_seconds=10.0,
            failure_threshold=3,
            readiness_check_dependencies=True,
            readiness_check_resources=True,
        )
    )

    probes.configure_startup_probe(ProbeConfig(timeout_seconds=10.0, startup_timeout_seconds=60.0))

    return probes


def create_fast_startup_probes(service_name: str) -> KubernetesProbesService:
    """Create probes optimized for fast startup applications."""
    probes = KubernetesProbesService(service_name)

    # Faster checks for applications that start quickly
    probes.configure_liveness_probe(ProbeConfig(timeout_seconds=1.0, period_seconds=10.0, failure_threshold=3))

    probes.configure_readiness_probe(
        ProbeConfig(
            timeout_seconds=2.0,
            period_seconds=5.0,
            failure_threshold=2,
            readiness_check_dependencies=False,  # Skip dependency checks for speed
            readiness_check_resources=False,
        )
    )

    probes.configure_startup_probe(ProbeConfig(timeout_seconds=5.0, startup_timeout_seconds=30.0))

    return probes


def create_resilient_probes(service_name: str) -> KubernetesProbesService:
    """Create probes optimized for resilient, slow-starting applications."""
    probes = KubernetesProbesService(service_name)

    # More lenient checks for applications that need time to stabilize
    probes.configure_liveness_probe(
        ProbeConfig(
            timeout_seconds=5.0,
            period_seconds=60.0,  # Check less frequently
            failure_threshold=5,  # Allow more failures before restart
        )
    )

    probes.configure_readiness_probe(
        ProbeConfig(
            timeout_seconds=10.0,
            period_seconds=30.0,  # Check less frequently during stabilization
            failure_threshold=5,
            readiness_check_dependencies=True,
            readiness_check_resources=True,
        )
    )

    probes.configure_startup_probe(
        ProbeConfig(timeout_seconds=15.0, startup_timeout_seconds=300.0)  # 5 minutes for slow startups
    )

    return probes
