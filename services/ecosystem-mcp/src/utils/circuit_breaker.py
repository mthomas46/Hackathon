"""
Circuit breaker pattern for resilient external service calls.

Prevents cascading failures by detecting when a service is down
and failing fast instead of repeatedly trying to call it.

States:
- CLOSED: Normal operation (all calls allowed)
- OPEN: Service is failing (all calls rejected immediately)
- HALF_OPEN: Testing recovery (limited calls allowed)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Optional, TypeVar, ParamSpec
from functools import wraps

logger = logging.getLogger(__name__)

# Type variables for generic support
P = ParamSpec('P')
R = TypeVar('R')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing, reject calls
    HALF_OPEN = "half_open"    # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    Protects against cascading failures by:
    1. Tracking failure rate
    2. Opening circuit when failures exceed threshold
    3. Periodically testing for recovery
    4. Closing circuit when service recovers
    
    Example:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        
        async def call_service():
            async with breaker:
                return await external_service.call()
    """
    
    def __init__(
        self,
        name: str = "circuit",
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker name (for logging/metrics)
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            half_open_max_calls: Max calls in half-open state
            success_threshold: Successes needed to close circuit
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        
        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        
        # Lock for state transitions
        self._lock = asyncio.Lock()
        
        logger.info(
            f"Circuit breaker '{name}' initialized: "
            f"failure_threshold={failure_threshold}, "
            f"recovery_timeout={recovery_timeout}s"
        )
    
    async def __aenter__(self):
        """Context manager entry."""
        await self._check_state_transition()
        
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN "
                f"(service failing, try again in {self._time_until_recovery():.1f}s)"
            )
        
        if self.state == CircuitState.HALF_OPEN:
            async with self._lock:
                if self.half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is HALF_OPEN "
                        f"(max test calls reached, try again later)"
                    )
                self.half_open_calls += 1
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            # Success
            await self._on_success()
        else:
            # Failure
            await self._on_failure()
        
        # Don't suppress exceptions
        return False
    
    async def call(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function raises
        """
        async with self:
            return await func(*args, **kwargs)
    
    async def _check_state_transition(self):
        """Check if circuit should transition from OPEN to HALF_OPEN."""
        if self.state == CircuitState.OPEN and self.last_failure_time:
            elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
            
            if elapsed >= self.recovery_timeout:
                async with self._lock:
                    # Double-check after acquiring lock
                    if self.state == CircuitState.OPEN:
                        logger.info(
                            f"Circuit breaker '{self.name}': OPEN -> HALF_OPEN "
                            f"(testing recovery after {elapsed:.1f}s)"
                        )
                        self.state = CircuitState.HALF_OPEN
                        self.half_open_calls = 0
                        self.success_count = 0
    
    async def _on_success(self):
        """Handle successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                logger.debug(
                    f"Circuit breaker '{self.name}': success in HALF_OPEN "
                    f"({self.success_count}/{self.success_threshold})"
                )
                
                if self.success_count >= self.success_threshold:
                    logger.info(
                        f"Circuit breaker '{self.name}': HALF_OPEN -> CLOSED "
                        f"(service recovered)"
                    )
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.half_open_calls = 0
            
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                if self.failure_count > 0:
                    self.failure_count = 0
    
    async def _on_failure(self):
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.state == CircuitState.HALF_OPEN:
                logger.warning(
                    f"Circuit breaker '{self.name}': HALF_OPEN -> OPEN "
                    f"(recovery test failed)"
                )
                self.state = CircuitState.OPEN
                self.half_open_calls = 0
                self.success_count = 0
            
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    logger.warning(
                        f"Circuit breaker '{self.name}': CLOSED -> OPEN "
                        f"({self.failure_count} consecutive failures)"
                    )
                    self.state = CircuitState.OPEN
    
    def _time_until_recovery(self) -> float:
        """Calculate seconds until recovery attempt."""
        if not self.last_failure_time:
            return 0.0
        
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return max(0.0, self.recovery_timeout - elapsed)
    
    def get_state(self) -> dict:
        """
        Get current circuit breaker state.
        
        Returns:
            Dict with state information
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "time_until_recovery": self._time_until_recovery() if self.state == CircuitState.OPEN else 0.0
        }


def circuit_breaker(
    name: str = "circuit",
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0
):
    """
    Decorator for circuit breaker protection.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening
        recovery_timeout: Seconds before recovery test
    
    Example:
        @circuit_breaker(name="ollama", failure_threshold=5)
        async def call_ollama():
            return await ollama.generate(...)
    """
    breaker = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout
    )
    
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return await breaker.call(func, *args, **kwargs)
        
        # Attach breaker for inspection
        wrapper.circuit_breaker = breaker  # type: ignore
        
        return wrapper
    
    return decorator

