"""Consolidated resilience utilities for fault tolerance and reliability.

Combines retry, circuit breaker, and rate limiting functionality.
"""
import asyncio
import random
import time
from typing import Callable, Awaitable, Optional, TypeVar, Dict

T = TypeVar("T")


class CircuitBreaker:
    """Tracks consecutive failures and gates calls for a cooldown window.

    State transitions:
    - closed: calls pass, failures increment counter
    - open: calls blocked until reset_timeout passes
    - half-open: first call allowed after timeout, success closes circuit
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._state = "closed"  # closed|open|half-open
        self._failures = 0
        self._last_failure_time: float = 0.0

    def allow(self) -> bool:
        if self._state == "open":
            if time.time() - self._last_failure_time >= self.reset_timeout:
                self._state = "half-open"
                return True
            return False
        return True

    def on_success(self) -> None:
        self._state = "closed"
        self._failures = 0

    def on_failure(self) -> None:
        self._failures += 1
        self._last_failure_time = time.time()
        if self._failures >= self.failure_threshold:
            self._state = "open"


async def with_circuit(cb: CircuitBreaker, func: Callable[[], Awaitable[T]]) -> T:
    """Execute function under circuit protection."""
    if not cb.allow():
        raise RuntimeError("circuit_open")
    try:
        result = await func()
        cb.on_success()
        return result
    except Exception:
        cb.on_failure()
        raise


async def with_retries(
    operation: Callable[[], Awaitable[T]],
    attempts: int = 3,
    base_delay_ms: int = 100
) -> T:
    """Execute operation with exponential backoff retry logic."""
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return await operation()
        except Exception as e:
            last_exc = e
            if i == attempts - 1:
                break
            jitter = random.randint(0, base_delay_ms)
            await asyncio.sleep((base_delay_ms + jitter) / 1000.0)
    assert last_exc is not None
    raise last_exc


class TokenBucket:
    """Token bucket for rate limiting."""

    def __init__(self, rate_per_sec: float, burst: int):
        self.rate = rate_per_sec
        self.capacity = burst
        self.tokens = burst
        self.last = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class ResilienceManager:
    """Unified resilience management for services."""

    def __init__(
        self,
        circuit_failure_threshold: int = 3,
        circuit_reset_timeout: float = 30.0,
        retry_attempts: int = 3,
        retry_base_delay_ms: int = 150,
        rate_limits: Optional[Dict[str, tuple[float, int]]] = None
    ):
        self.circuit_breaker = CircuitBreaker(circuit_failure_threshold, circuit_reset_timeout)
        self.retry_attempts = retry_attempts
        self.retry_base_delay_ms = retry_base_delay_ms
        self.rate_buckets: Dict[str, TokenBucket] = {}

        if rate_limits:
            for path, (rate, burst) in rate_limits.items():
                self.rate_buckets[path] = TokenBucket(rate, burst)

    async def execute_with_resilience(self, operation: Callable[[], Awaitable[T]]) -> T:
        """Execute operation with full resilience (circuit + retry)."""
        async def _circuit_operation():
            return await with_retries(operation, self.retry_attempts, self.retry_base_delay_ms)

        return await with_circuit(self.circuit_breaker, _circuit_operation)

    def check_rate_limit(self, path: str) -> bool:
        """Check if request should be rate limited."""
        bucket = self.rate_buckets.get(path)
        if bucket:
            return bucket.allow()
        return True
