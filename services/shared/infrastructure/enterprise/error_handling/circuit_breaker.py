"""Circuit breaker implementation for resilience."""

import time
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, Optional


class CircuitBreakerState(Enum):
    """States of the circuit breaker."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker for service resilience."""

    service_name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    expected_exception: tuple = (Exception,)

    # Internal state
    _state: CircuitBreakerState = CircuitBreakerState.CLOSED
    _failure_count: int = 0
    _last_failure_time: Optional[float] = None
    _lock: Lock = field(default_factory=Lock)

    def __post_init__(self):
        """Initialize the circuit breaker."""
        if isinstance(self.expected_exception, type):
            self.expected_exception = (self.expected_exception,)

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self._state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenException(self.service_name)

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self.recovery_timeout

    def _on_success(self):
        """Handle successful operation."""
        with self._lock:
            self._failure_count = 0
            self._state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """Handle failed operation."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitBreakerState.OPEN

    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    def reset(self):
        """Manually reset the circuit breaker."""
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for monitoring."""
        return {
            "service_name": self.service_name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self._last_failure_time,
        }


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Circuit breaker is open for service: {service_name}")
