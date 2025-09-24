"""Centralized Circuit Breaker Service for ecosystem-wide resilience management.

Provides a singleton service for managing circuit breakers across all services,
with monitoring, metrics, and automatic recovery capabilities.
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from .resilience import EnhancedCircuitBreaker, ResilienceManager, ResourceLimiter

logger = logging.getLogger(__name__)
T = TypeVar("T")


@dataclass
class ServiceEndpoint:
    """Represents a service endpoint with circuit breaker protection."""

    service_name: str
    endpoint_path: str
    circuit_breaker: EnhancedCircuitBreaker
    resilience_manager: ResilienceManager
    last_health_check: float = 0
    health_check_interval: float = 30.0  # seconds
    is_healthy: bool = True


@dataclass
class EcosystemHealthMetrics:
    """Overall ecosystem health metrics."""

    total_services: int = 0
    healthy_services: int = 0
    degraded_services: int = 0
    failing_services: int = 0
    total_circuits_open: int = 0
    total_circuits_half_open: int = 0
    last_updated: float = field(default_factory=time.time)


class CircuitBreakerService:
    """Centralized service for managing circuit breakers across the ecosystem."""

    _instance: Optional["CircuitBreakerService"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._endpoints: Dict[str, ServiceEndpoint] = {}
        self._global_resource_limiter = ResourceLimiter(
            max_concurrent=50, max_memory_mb=1024.0
        )
        self._health_metrics = EcosystemHealthMetrics()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    @classmethod
    def get_instance(cls) -> "CircuitBreakerService":
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register_endpoint(
        self,
        service_name: str,
        endpoint_path: str,
        failure_threshold: int = 3,
        reset_timeout: float = 30.0,
        max_concurrent: int = 10,
    ) -> ServiceEndpoint:
        """Register a service endpoint with circuit breaker protection."""
        endpoint_key = f"{service_name}:{endpoint_path}"

        if endpoint_key in self._endpoints:
            return self._endpoints[endpoint_key]

        # Create resource limiter for this endpoint
        resource_limiter = ResourceLimiter(max_concurrent=max_concurrent)

        # Create enhanced circuit breaker
        circuit_breaker = EnhancedCircuitBreaker(
            failure_threshold=failure_threshold,
            reset_timeout=reset_timeout,
            resource_limiter=resource_limiter,
        )

        # Create resilience manager
        resilience_manager = ResilienceManager(
            circuit_failure_threshold=failure_threshold,
            circuit_reset_timeout=reset_timeout,
            max_concurrent_operations=max_concurrent,
        )

        endpoint = ServiceEndpoint(
            service_name=service_name,
            endpoint_path=endpoint_path,
            circuit_breaker=circuit_breaker,
            resilience_manager=resilience_manager,
        )

        self._endpoints[endpoint_key] = endpoint
        logger.info(f"Registered circuit breaker for {endpoint_key}")
        return endpoint

    async def execute_with_protection(
        self,
        service_name: str,
        endpoint_path: str,
        operation: Callable[[], Awaitable[T]],
        operation_name: str = "unknown",
        timeout_seconds: Optional[float] = None,
    ) -> T:
        """Execute operation with full circuit breaker and resilience protection."""
        endpoint_key = f"{service_name}:{endpoint_path}"
        endpoint = self._endpoints.get(endpoint_key)

        if not endpoint:
            # Auto-register with defaults
            endpoint = self.register_endpoint(service_name, endpoint_path)

        # Check global resource limits
        if not self._global_resource_limiter.acquire():
            raise RuntimeError("Global resource limit exceeded")

        try:
            return await endpoint.resilience_manager.execute_with_resilience(
                operation=operation,
                operation_name=f"{service_name}:{endpoint_path}:{operation_name}",
                timeout_seconds=timeout_seconds,
            )
        finally:
            self._global_resource_limiter.release()

    def get_endpoint_status(
        self, service_name: str, endpoint_path: str
    ) -> Optional[Dict[str, Any]]:
        """Get status of a specific endpoint."""
        endpoint_key = f"{service_name}:{endpoint_path}"
        endpoint = self._endpoints.get(endpoint_key)

        if not endpoint:
            return None

        return {
            "service_name": endpoint.service_name,
            "endpoint_path": endpoint.endpoint_path,
            "circuit_state": endpoint.circuit_breaker.state,
            "is_healthy": endpoint.is_healthy,
            "last_health_check": endpoint.last_health_check,
            "resource_usage": endpoint.circuit_breaker.resource_usage,
            "metrics": {
                "total_calls": endpoint.circuit_breaker.metrics.total_calls,
                "successful_calls": endpoint.circuit_breaker.metrics.successful_calls,
                "failed_calls": endpoint.circuit_breaker.metrics.failed_calls,
                "rejected_calls": endpoint.circuit_breaker.metrics.rejected_calls,
                "state_changes": endpoint.circuit_breaker.metrics.state_changes,
            },
        }

    def get_ecosystem_health(self) -> Dict[str, Any]:
        """Get overall ecosystem health status."""
        self._update_health_metrics()

        return {
            "total_services": self._health_metrics.total_services,
            "healthy_services": self._health_metrics.healthy_services,
            "degraded_services": self._health_metrics.degraded_services,
            "failing_services": self._health_metrics.failing_services,
            "total_circuits_open": self._health_metrics.total_circuits_open,
            "total_circuits_half_open": self._health_metrics.total_circuits_half_open,
            "last_updated": self._health_metrics.last_updated,
            "global_resource_usage": self._global_resource_limiter.active_operations,
            "services": {
                key: self.get_endpoint_status(ep.service_name, ep.endpoint_path)
                for key, ep in self._endpoints.items()
            },
        }

    def _update_health_metrics(self) -> None:
        """Update ecosystem-wide health metrics."""
        total_services = len(self._endpoints)
        healthy_services = 0
        degraded_services = 0
        failing_services = 0
        circuits_open = 0
        circuits_half_open = 0

        for endpoint in self._endpoints.values():
            state = endpoint.circuit_breaker.state
            metrics = endpoint.circuit_breaker.metrics

            if state == "open":
                circuits_open += 1
                failing_services += 1
            elif state == "half-open":
                circuits_half_open += 1
                degraded_services += 1
            elif state == "closed" and metrics.failed_calls == 0:
                healthy_services += 1
            else:
                degraded_services += 1

        self._health_metrics = EcosystemHealthMetrics(
            total_services=total_services,
            healthy_services=healthy_services,
            degraded_services=degraded_services,
            failing_services=failing_services,
            total_circuits_open=circuits_open,
            total_circuits_half_open=circuits_half_open,
            last_updated=time.time(),
        )

    async def start_monitoring(self) -> None:
        """Start the monitoring task."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Circuit breaker monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop the monitoring task."""
        if self._monitoring_task:
            self._shutdown_event.set()
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._monitoring_task.cancel()
            logger.info("Circuit breaker monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop for health checks and metrics."""
        while not self._shutdown_event.is_set():
            try:
                # Update health metrics
                self._update_health_metrics()

                # Log critical issues
                if self._health_metrics.failing_services > 0:
                    logger.warning(
                        f"Circuit breaker alert: {self._health_metrics.failing_services} "
                        f"services failing, {self._health_metrics.total_circuits_open} circuits open"
                    )

                # Perform health checks for degraded services
                await self._perform_health_checks()

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in circuit breaker monitoring loop: {e}")
                await asyncio.sleep(30)  # Back off on errors

    async def _perform_health_checks(self) -> None:
        """Perform health checks on degraded endpoints."""
        current_time = time.time()

        for endpoint in self._endpoints.values():
            if (
                current_time - endpoint.last_health_check
                > endpoint.health_check_interval
            ):
                # Perform basic health check (circuit not open)
                was_healthy = endpoint.is_healthy
                endpoint.is_healthy = endpoint.circuit_breaker.state != "open"
                endpoint.last_health_check = current_time

                if was_healthy != endpoint.is_healthy:
                    status = "healthy" if endpoint.is_healthy else "unhealthy"
                    logger.info(
                        f"Endpoint {endpoint.service_name}:{endpoint.endpoint_path} status changed to {status}"
                    )


# Global instance
_circuit_breaker_service: Optional[CircuitBreakerService] = None


def get_circuit_breaker_service() -> CircuitBreakerService:
    """Get the global circuit breaker service instance."""
    global _circuit_breaker_service
    if _circuit_breaker_service is None:
        _circuit_breaker_service = CircuitBreakerService.get_instance()
    return _circuit_breaker_service


async def execute_with_circuit_breaker(
    service_name: str,
    endpoint_path: str,
    operation: Callable[[], Awaitable[T]],
    operation_name: str = "unknown",
    timeout_seconds: Optional[float] = None,
) -> T:
    """Convenience function for executing operations with circuit breaker protection."""
    service = get_circuit_breaker_service()
    return await service.execute_with_protection(
        service_name=service_name,
        endpoint_path=endpoint_path,
        operation=operation,
        operation_name=operation_name,
        timeout_seconds=timeout_seconds,
    )
