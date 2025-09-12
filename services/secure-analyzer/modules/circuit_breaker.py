"""Circuit breaker implementation for secure analyzer service."""

import time
import os
from typing import Optional
from contextlib import asynccontextmanager


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""

    def __init__(
        self,
        max_failures: int = 5,
        timeout_seconds: int = 60
    ):
        self.max_failures = max_failures
        self.timeout_seconds = timeout_seconds
        self.failures = 0
        self.last_failure = 0.0
        self.open = False

    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.open:
            # Check if timeout has passed to close circuit
            if time.time() - self.last_failure > self.timeout_seconds:
                self.open = False
                return False
            return True
        return False

    def record_failure(self) -> None:
        """Record a circuit breaker failure."""
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.max_failures:
            self.open = True

    def reset(self) -> None:
        """Reset circuit breaker on successful operation."""
        self.failures = 0
        self.open = False


# Global circuit breaker instance
circuit_breaker = CircuitBreaker(
    max_failures=int(os.environ.get("SECURE_ANALYZER_CIRCUIT_BREAKER_MAX_FAILURES", "5")),
    timeout_seconds=int(os.environ.get("SECURE_ANALYZER_CIRCUIT_BREAKER_TIMEOUT", "60"))
)


@asynccontextmanager
async def operation_timeout_context(operation_name: str, timeout_seconds: int = 30):
    """Context manager for operation timeouts with logging."""
    start_time = time.time()
    print(f"[SECURE_ANALYZER] Starting operation: {operation_name} at {start_time}")

    try:
        yield
        elapsed = time.time() - start_time
        print(f"[SECURE_ANALYZER] Completed operation: {operation_name} in {elapsed:.2f}s")
        circuit_breaker.reset()

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[SECURE_ANALYZER] ERROR in operation {operation_name}: {str(e)} after {elapsed:.2f}s")
        circuit_breaker.record_failure()
        raise
