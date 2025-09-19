"""Circuit Breaker Pattern - Service Resilience Infrastructure.

This module implements the circuit breaker pattern for resilient service
communication and graceful failure handling.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import time

# Import from shared infrastructure
shared_path = Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"
sys.path.insert(0, str(shared_path))

try:
    from utilities.resilience import CircuitBreaker as BaseCircuitBreaker
except ImportError:
    # Create a simple mock CircuitBreaker for testing
    class BaseCircuitBreaker:
        async def __call__(self, func, *args, **kwargs):
            return await func(*args, **kwargs)

        def __init__(self, *args, **kwargs):
            pass

from ..logging import get_simulation_logger


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


class ServiceCircuitBreaker:
    """Circuit breaker for individual service calls."""

    def __init__(self,
                 service_name: str,
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 success_threshold: int = 3):
        """Initialize circuit breaker.

        Args:
            service_name: Name of the service
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying to recover (seconds)
            success_threshold: Number of successes needed to close circuit
        """
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.logger = get_simulation_logger()

    async def call(self, func: Callable[[], Awaitable[Any]]) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info(
                    "Circuit breaker transitioning to half-open",
                    service=self.service_name
                )
            else:
                raise CircuitBreakerOpenException(
                    f"Circuit breaker is OPEN for service {self.service_name}"
                )

        try:
            result = await func()
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.last_failure_time is None:
            return False

        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._reset()
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset success count for closed state
            self.success_count = 0

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0

        if self.failure_count >= self.failure_threshold:
            self._trip()

    def _trip(self) -> None:
        """Trip the circuit breaker to open state."""
        if self.state != CircuitBreakerState.OPEN:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(
                "Circuit breaker tripped to OPEN",
                service=self.service_name,
                failure_count=self.failure_count
            )

    def _reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.logger.info(
            "Circuit breaker reset to CLOSED",
            service=self.service_name
        )

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "service_name": self.service_name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "success_threshold": self.success_threshold
        }


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class EcosystemCircuitBreakerRegistry:
    """Registry for managing circuit breakers for all ecosystem services."""

    def __init__(self):
        """Initialize circuit breaker registry."""
        self.breakers: Dict[str, ServiceCircuitBreaker] = {}
        self.logger = get_simulation_logger()
        self._initialize_breakers()

    def _initialize_breakers(self):
        """Initialize circuit breakers for all ecosystem services."""
        # Import ecosystem services
        from ...domain.value_objects import ECOSYSTEM_SERVICES

        for service in ECOSYSTEM_SERVICES:
            # Configure different thresholds based on service criticality
            if service.name in ["doc_store", "mock_data_generator", "orchestrator"]:
                # Critical services - more lenient thresholds
                breaker = ServiceCircuitBreaker(
                    service_name=service.name,
                    failure_threshold=3,  # Fail after 3 attempts
                    recovery_timeout=30.0,  # Try again after 30 seconds
                    success_threshold=2  # Need 2 successes to close
                )
            else:
                # Other services - stricter thresholds
                breaker = ServiceCircuitBreaker(
                    service_name=service.name,
                    failure_threshold=5,  # Fail after 5 attempts
                    recovery_timeout=60.0,  # Try again after 1 minute
                    success_threshold=3  # Need 3 successes to close
                )

            self.breakers[service.name] = breaker

    def get_breaker(self, service_name: str) -> Optional[ServiceCircuitBreaker]:
        """Get circuit breaker for a service."""
        return self.breakers.get(service_name)

    async def execute_with_breaker(self, service_name: str, func: Callable[[], Awaitable[Any]]) -> Any:
        """Execute function with circuit breaker protection."""
        breaker = self.get_breaker(service_name)
        if breaker:
            return await breaker.call(func)
        else:
            # If no breaker configured, execute directly
            return await func()

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        return {
            service_name: breaker.get_status()
            for service_name, breaker in self.breakers.items()
        }

    def reset_breaker(self, service_name: str) -> bool:
        """Reset a circuit breaker to closed state."""
        breaker = self.get_breaker(service_name)
        if breaker and breaker.state != CircuitBreakerState.CLOSED:
            breaker._reset()
            self.logger.info(
                "Circuit breaker manually reset",
                service=service_name
            )
            return True
        return False

    def reset_all_breakers(self) -> Dict[str, bool]:
        """Reset all circuit breakers."""
        results = {}
        for service_name in self.breakers:
            results[service_name] = self.reset_breaker(service_name)
        return results


class ResilientServiceClient:
    """Wrapper for service clients with circuit breaker protection."""

    def __init__(self, service_name: str):
        """Initialize resilient service client."""
        from ..clients.ecosystem_clients import get_ecosystem_client
        self.service_name = service_name
        self.client = get_ecosystem_client(service_name)
        self.circuit_breaker = EcosystemCircuitBreakerRegistry().get_breaker(service_name)
        self.logger = get_simulation_logger()

    async def execute_request(self, method_name: str, *args, **kwargs) -> Any:
        """Execute a service request with circuit breaker protection."""
        if not self.client:
            raise ValueError(f"No client available for service {self.service_name}")

        # Get the method from the client
        method = getattr(self.client, method_name, None)
        if not method:
            raise ValueError(f"Method {method_name} not found on {self.service_name} client")

        async def _execute():
            start_time = time.time()
            try:
                result = await method(*args, **kwargs)
                execution_time = time.time() - start_time

                self.logger.debug(
                    "Service request successful",
                    service=self.service_name,
                    method=method_name,
                    execution_time_seconds=execution_time
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                self.logger.warning(
                    "Service request failed",
                    service=self.service_name,
                    method=method_name,
                    execution_time_seconds=execution_time,
                    error=str(e)
                )
                raise e

        # Execute with circuit breaker protection
        if self.circuit_breaker:
            return await self.circuit_breaker.call(_execute)
        else:
            return await _execute()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check with circuit breaker protection."""
        try:
            result = await self.execute_request("health_check")
            return {
                "service": self.service_name,
                "healthy": True,
                "circuit_breaker_state": self.circuit_breaker.state.value if self.circuit_breaker else "none"
            }
        except Exception as e:
            return {
                "service": self.service_name,
                "healthy": False,
                "error": str(e),
                "circuit_breaker_state": self.circuit_breaker.state.value if self.circuit_breaker else "none"
            }


# Global circuit breaker registry instance
_circuit_breaker_registry: Optional[EcosystemCircuitBreakerRegistry] = None


def get_circuit_breaker_registry() -> EcosystemCircuitBreakerRegistry:
    """Get the global circuit breaker registry instance."""
    global _circuit_breaker_registry
    if _circuit_breaker_registry is None:
        _circuit_breaker_registry = EcosystemCircuitBreakerRegistry()
    return _circuit_breaker_registry


def create_resilient_client(service_name: str) -> ResilientServiceClient:
    """Create a resilient client for a service."""
    return ResilientServiceClient(service_name)


async def execute_with_resilience(service_name: str, method_name: str, *args, **kwargs) -> Any:
    """Execute a service method with full resilience features."""
    client = create_resilient_client(service_name)
    return await client.execute_request(method_name, *args, **kwargs)


__all__ = [
    'CircuitBreakerState',
    'ServiceCircuitBreaker',
    'CircuitBreakerOpenException',
    'EcosystemCircuitBreakerRegistry',
    'ResilientServiceClient',
    'get_circuit_breaker_registry',
    'create_resilient_client',
    'execute_with_resilience'
]
