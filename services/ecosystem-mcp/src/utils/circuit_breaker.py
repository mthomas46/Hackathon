"""
Circuit Breaker pattern for infrastructure resilience.

Prevents cascading failures by tracking error rates and failing fast
when a service is known to be down.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any, Optional, Dict
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast, not trying
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 2          # Successes to close from half-open
    timeout: float = 60.0               # Seconds before trying again (open -> half-open)
    expected_exception: type = Exception  # Which exceptions to count
    

@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    opened_at: Optional[float] = None
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.
    
    States:
    - CLOSED: Normal operation, all calls go through
    - OPEN: Too many failures, failing fast without trying
    - HALF_OPEN: Testing if service recovered
    
    Example:
        breaker = CircuitBreaker(name="database", failure_threshold=5, timeout=60)
        
        @breaker
        async def query_database():
            return await db.query()
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name for logging
            failure_threshold: Consecutive failures before opening
            success_threshold: Successes in half-open to close
            timeout: Seconds to wait before trying again
            expected_exception: Exception type to catch
        """
        self.name = name
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
            expected_exception=expected_exception
        )
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        
        logger.info(
            f"Circuit breaker '{name}' initialized: "
            f"failure_threshold={failure_threshold}, "
            f"timeout={timeout}s"
        )
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker."""
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                return await self._call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                return self._call_sync(func, *args, **kwargs)
            return sync_wrapper
    
    async def _call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection."""
        async with self._lock:
            self.stats.total_calls += 1
            
            # Check state
            if self.stats.state == CircuitState.OPEN:
                # Check if timeout has elapsed
                if self._should_attempt_reset():
                    logger.info(f"Circuit breaker '{self.name}': OPEN -> HALF_OPEN (testing recovery)")
                    self.stats.state = CircuitState.HALF_OPEN
                    self.stats.success_count = 0
                else:
                    # Still open, fail fast
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN "
                        f"(failing fast, last failure: {time.time() - (self.stats.last_failure_time or 0):.1f}s ago)"
                    )
        
        # Try to execute function
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        
        except self.config.expected_exception as e:
            await self._record_failure()
            raise
    
    def _call_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Execute sync function with circuit breaker protection."""
        # Note: For sync, we can't use async lock, so this is best-effort
        self.stats.total_calls += 1
        
        if self.stats.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker '{self.name}': OPEN -> HALF_OPEN (testing recovery)")
                self.stats.state = CircuitState.HALF_OPEN
                self.stats.success_count = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN (failing fast)"
                )
        
        try:
            result = func(*args, **kwargs)
            self._record_success_sync()
            return result
        
        except self.config.expected_exception as e:
            self._record_failure_sync()
            raise
    
    async def _record_success(self):
        """Record successful call."""
        async with self._lock:
            self.stats.success_count += 1
            self.stats.total_successes += 1
            self.stats.failure_count = 0
            self.stats.last_success_time = time.time()
            
            if self.stats.state == CircuitState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    logger.info(
                        f"Circuit breaker '{self.name}': HALF_OPEN -> CLOSED "
                        f"({self.stats.success_count} successes)"
                    )
                    self.stats.state = CircuitState.CLOSED
                    self.stats.success_count = 0
                    self.stats.opened_at = None
    
    async def _record_failure(self):
        """Record failed call."""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.total_failures += 1
            self.stats.last_failure_time = time.time()
            
            if self.stats.state == CircuitState.HALF_OPEN:
                # Failed while testing, back to open
                logger.warning(
                    f"Circuit breaker '{self.name}': HALF_OPEN -> OPEN "
                    f"(recovery test failed)"
                )
                self.stats.state = CircuitState.OPEN
                self.stats.opened_at = time.time()
                self.stats.failure_count = 0
            
            elif self.stats.state == CircuitState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    logger.error(
                        f"Circuit breaker '{self.name}': CLOSED -> OPEN "
                        f"({self.stats.failure_count} consecutive failures)"
                    )
                    self.stats.state = CircuitState.OPEN
                    self.stats.opened_at = time.time()
    
    def _record_success_sync(self):
        """Record successful call (sync)."""
        # Best-effort for sync calls
        self.stats.success_count += 1
        self.stats.total_successes += 1
        self.stats.failure_count = 0
        self.stats.last_success_time = time.time()
        
        if self.stats.state == CircuitState.HALF_OPEN:
            if self.stats.success_count >= self.config.success_threshold:
                logger.info(f"Circuit breaker '{self.name}': HALF_OPEN -> CLOSED")
                self.stats.state = CircuitState.CLOSED
                self.stats.opened_at = None
    
    def _record_failure_sync(self):
        """Record failed call (sync)."""
        self.stats.failure_count += 1
        self.stats.total_failures += 1
        self.stats.last_failure_time = time.time()
        
        if self.stats.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit breaker '{self.name}': HALF_OPEN -> OPEN")
            self.stats.state = CircuitState.OPEN
            self.stats.opened_at = time.time()
        
        elif self.stats.state == CircuitState.CLOSED:
            if self.stats.failure_count >= self.config.failure_threshold:
                logger.error(f"Circuit breaker '{self.name}': CLOSED -> OPEN")
                self.stats.state = CircuitState.OPEN
                self.stats.opened_at = time.time()
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try again."""
        if self.stats.opened_at is None:
            return True
        
        elapsed = time.time() - self.stats.opened_at
        return elapsed >= self.config.timeout
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "total_calls": self.stats.total_calls,
            "total_successes": self.stats.total_successes,
            "total_failures": self.stats.total_failures,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "last_failure": self.stats.last_failure_time,
            "last_success": self.stats.last_success_time,
            "opened_at": self.stats.opened_at,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    async def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        async with self._lock:
            logger.info(f"Circuit breaker '{self.name}': Manually reset to CLOSED")
            self.stats.state = CircuitState.CLOSED
            self.stats.failure_count = 0
            self.stats.success_count = 0
            self.stats.opened_at = None


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Global circuit breakers for common services
_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: float = 60.0
) -> CircuitBreaker:
    """
    Get or create a circuit breaker.
    
    Args:
        name: Name of the service
        failure_threshold: Failures before opening
        timeout: Seconds to wait before retry
    
    Returns:
        Circuit breaker instance
    """
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            timeout=timeout
        )
    
    return _breakers[name]


def get_all_breakers() -> Dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    return _breakers.copy()
