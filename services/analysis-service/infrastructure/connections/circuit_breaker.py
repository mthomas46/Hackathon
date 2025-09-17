"""Circuit Breaker - Resilient connection handling with failure protection."""

import asyncio
import time
from typing import Any, Dict, List, Optional, Callable, Type
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Number of failures to open circuit
    recovery_timeout: int = 60  # Seconds to wait before attempting recovery
    success_threshold: int = 3  # Number of successes needed in half-open state
    timeout: float = 30.0  # Request timeout
    expected_exceptions: List[Type[Exception]] = field(default_factory=lambda: [Exception])
    name: str = "circuit_breaker"


class CircuitBreaker:
    """Circuit breaker implementation for resilient service calls."""

    def __init__(self, config: CircuitBreakerConfig):
        """Initialize circuit breaker."""
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.next_attempt_time: Optional[datetime] = None

        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.rejected_requests = 0
        self.state_change_count = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        self.total_requests += 1

        # Check if circuit is open
        if self.state == CircuitBreakerState.OPEN:
            if not self._should_attempt_reset():
                self.rejected_requests += 1
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.config.name}' is OPEN"
                )

            # Attempt reset
            self.state = CircuitBreakerState.HALF_OPEN
            self.success_count = 0
            self._record_state_change()

        try:
            # Execute with timeout
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout
                )
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, func, *args, **kwargs),
                    timeout=self.config.timeout
                )

            # Success
            await self._on_success()
            return result

        except tuple(self.config.expected_exceptions) as e:
            # Expected failure
            await self._on_failure()
            raise e
        except asyncio.TimeoutError as e:
            # Timeout is treated as failure
            await self._on_failure()
            raise e

    async def _on_success(self) -> None:
        """Handle successful call."""
        self.total_successes += 1

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1

            # Check if we've met success threshold
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self._record_state_change()

    async def _on_failure(self) -> None:
        """Handle failed call."""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Failed during recovery attempt
            self.state = CircuitBreakerState.OPEN
            self.next_attempt_time = datetime.utcnow() + timedelta(seconds=self.config.recovery_timeout)
            self._record_state_change()

        elif self.state == CircuitBreakerState.CLOSED:
            # Check if we should open the circuit
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                self.next_attempt_time = datetime.utcnow() + timedelta(seconds=self.config.recovery_timeout)
                self._record_state_change()

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        if self.next_attempt_time is None:
            return False

        return datetime.utcnow() >= self.next_attempt_time

    def _record_state_change(self) -> None:
        """Record state change."""
        self.state_change_count += 1

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            'name': self.config.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'next_attempt_time': self.next_attempt_time.isoformat() if self.next_attempt_time else None,
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'success_threshold': self.config.success_threshold,
                'timeout': self.config.timeout
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            'name': self.config.name,
            'total_requests': self.total_requests,
            'total_successes': self.total_successes,
            'total_failures': self.total_failures,
            'rejected_requests': self.rejected_requests,
            'state_changes': self.state_change_count,
            'success_rate': self.total_successes / max(1, self.total_requests),
            'current_state': self.state.value,
            'failure_rate': self.failure_count / max(1, self.failure_count + self.success_count)
        }

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.next_attempt_time = None
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.rejected_requests = 0
        self.state_change_count = 0

    def force_open(self) -> None:
        """Force circuit breaker to open state."""
        if self.state != CircuitBreakerState.OPEN:
            self.state = CircuitBreakerState.OPEN
            self.next_attempt_time = datetime.utcnow() + timedelta(seconds=self.config.recovery_timeout)
            self._record_state_change()

    def force_close(self) -> None:
        """Force circuit breaker to closed state."""
        if self.state != CircuitBreakerState.CLOSED:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self._record_state_change()


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        """Initialize circuit breaker registry."""
        self.breakers: Dict[str, CircuitBreaker] = {}

    def register(self, name: str, breaker: CircuitBreaker) -> None:
        """Register a circuit breaker."""
        self.breakers[name] = breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name."""
        return self.breakers.get(name)

    def list_breakers(self) -> List[str]:
        """List all registered circuit breaker names."""
        return list(self.breakers.keys())

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers."""
        return {name: breaker.get_state() for name, breaker in self.breakers.items()}

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics of all circuit breakers."""
        return {name: breaker.get_stats() for name, breaker in self.breakers.items()}

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self.breakers.values():
            breaker.reset()


# Global circuit breaker registry
circuit_breaker_registry = CircuitBreakerRegistry()


class CircuitBreakerDecorator:
    """Decorator for applying circuit breaker to functions."""

    def __init__(self, config: CircuitBreakerConfig):
        """Initialize circuit breaker decorator."""
        self.breaker = CircuitBreaker(config)
        circuit_breaker_registry.register(config.name, self.breaker)

    def __call__(self, func: Callable) -> Callable:
        """Apply circuit breaker to function."""
        async def async_wrapper(*args, **kwargs):
            return await self.breaker.call(func, *args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to create an async wrapper
            async def async_func():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return await self.breaker.call(func, *args, **kwargs)
                finally:
                    loop.close()

            return asyncio.run(async_func())

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    success_threshold: int = 3,
    timeout: float = 30.0,
    name: Optional[str] = None
):
    """Decorator to apply circuit breaker to a function."""
    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            timeout=timeout,
            name=breaker_name
        )
        return CircuitBreakerDecorator(config)(func)

    return decorator


class AdaptiveCircuitBreaker(CircuitBreaker):
    """Adaptive circuit breaker that adjusts thresholds based on performance."""

    def __init__(self, config: CircuitBreakerConfig, adaptation_interval: int = 300):
        """Initialize adaptive circuit breaker."""
        super().__init__(config)
        self.adaptation_interval = adaptation_interval
        self.last_adaptation = datetime.utcnow()
        self.performance_history: List[Dict[str, Any]] = []

        # Adaptation parameters
        self.min_failure_threshold = 3
        self.max_failure_threshold = 20
        self.failure_rate_threshold = 0.1  # 10% failure rate

    async def _on_success(self) -> None:
        """Handle successful call with adaptation."""
        await super()._on_success()
        await self._record_performance(success=True)

    async def _on_failure(self) -> None:
        """Handle failed call with adaptation."""
        await super()._on_failure()
        await self._record_performance(success=False)

    async def _record_performance(self, success: bool) -> None:
        """Record performance data for adaptation."""
        self.performance_history.append({
            'timestamp': datetime.utcnow(),
            'success': success,
            'state': self.state.value
        })

        # Keep only recent history (last adaptation_interval * 2)
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.adaptation_interval * 2)
        self.performance_history = [
            entry for entry in self.performance_history
            if entry['timestamp'] > cutoff_time
        ]

        # Check if we should adapt
        if (datetime.utcnow() - self.last_adaptation).total_seconds() >= self.adaptation_interval:
            await self._adapt_thresholds()

    async def _adapt_thresholds(self) -> None:
        """Adapt failure threshold based on performance history."""
        if len(self.performance_history) < 10:  # Need minimum data
            return

        # Calculate failure rate
        recent_entries = [
            entry for entry in self.performance_history
            if (datetime.utcnow() - entry['timestamp']).total_seconds() <= self.adaptation_interval
        ]

        if not recent_entries:
            return

        failure_count = sum(1 for entry in recent_entries if not entry['success'])
        total_count = len(recent_entries)
        failure_rate = failure_count / total_count

        # Adapt threshold based on failure rate
        if failure_rate > self.failure_rate_threshold:
            # Increase threshold to be more tolerant
            new_threshold = min(
                self.config.failure_threshold + 1,
                self.max_failure_threshold
            )
            if new_threshold != self.config.failure_threshold:
                self.config.failure_threshold = new_threshold
        elif failure_rate < self.failure_rate_threshold * 0.5:
            # Decrease threshold to be more sensitive
            new_threshold = max(
                self.config.failure_threshold - 1,
                self.min_failure_threshold
            )
            if new_threshold != self.config.failure_threshold:
                self.config.failure_threshold = new_threshold

        self.last_adaptation = datetime.utcnow()

    def get_adaptation_stats(self) -> Dict[str, Any]:
        """Get adaptation statistics."""
        base_stats = self.get_stats()
        base_stats.update({
            'adaptation_interval': self.adaptation_interval,
            'last_adaptation': self.last_adaptation.isoformat(),
            'performance_history_size': len(self.performance_history),
            'adaptive_failure_threshold': self.config.failure_threshold,
            'min_failure_threshold': self.min_failure_threshold,
            'max_failure_threshold': self.max_failure_threshold
        })
        return base_stats


class CircuitBreakerPool:
    """Pool of circuit breakers for different services."""

    def __init__(self):
        """Initialize circuit breaker pool."""
        self.breakers: Dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        service_name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if service_name not in self.breakers:
            if config is None:
                config = CircuitBreakerConfig(name=service_name)
            self.breakers[service_name] = CircuitBreaker(config)

        return self.breakers[service_name]

    def get_breaker(self, service_name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker for service."""
        return self.breakers.get(service_name)

    def reset_service(self, service_name: str) -> bool:
        """Reset circuit breaker for service."""
        breaker = self.get_breaker(service_name)
        if breaker:
            breaker.reset()
            return True
        return False

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get statistics for all breakers in pool."""
        return {
            service: breaker.get_stats()
            for service, breaker in self.breakers.items()
        }


# Global circuit breaker pool
circuit_breaker_pool = CircuitBreakerPool()
