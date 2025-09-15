"""Circuit breaker implementation for secure analyzer service.

Provides fault tolerance by temporarily stopping requests to failing services
to prevent cascade failures and allow recovery time.
"""
import time
import os
from typing import Optional
from contextlib import asynccontextmanager

# Default configuration values
DEFAULT_CIRCUIT_BREAKER_MAX_FAILURES = 5
DEFAULT_CIRCUIT_BREAKER_TIMEOUT = 60


class CircuitBreaker:
    """Circuit breaker for fault tolerance and cascade failure prevention.

    Implements the circuit breaker pattern to protect against cascading failures
    by temporarily opening the circuit when failure thresholds are exceeded,
    allowing downstream services time to recover.
    """

    def __init__(
        self,
        max_failures: int = 5,
        timeout_seconds: int = 60
    ):
        """Initialize circuit breaker with configurable thresholds.

        Args:
            max_failures: Number of consecutive failures before opening circuit
            timeout_seconds: Time to wait before attempting to close circuit again
        """
        self.max_failures = max_failures
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_timestamp = 0.0
        self.is_circuit_open = False

    def is_open(self) -> bool:
        """Check if the circuit breaker is currently open.

        Returns:
            True if circuit is open (requests should be rejected)
            False if circuit is closed (requests can proceed)
        """
        if self.is_circuit_open:
            # Check if timeout period has elapsed to attempt closing
            time_since_last_failure = time.time() - self.last_failure_timestamp
            if time_since_last_failure > self.timeout_seconds:
                self.is_circuit_open = False
                return False
            return True
        return False

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_timestamp = time.time()
        if self.failure_count >= self.max_failures:
            self.is_circuit_open = True

    def reset(self) -> None:
        """Reset the circuit breaker after a successful operation."""
        self.failure_count = 0
        self.is_circuit_open = False


# Global circuit breaker instance with environment-configurable settings
circuit_breaker = CircuitBreaker(
    max_failures=int(os.environ.get("SECURE_ANALYZER_CIRCUIT_BREAKER_MAX_FAILURES", str(DEFAULT_CIRCUIT_BREAKER_MAX_FAILURES))),
    timeout_seconds=int(os.environ.get("SECURE_ANALYZER_CIRCUIT_BREAKER_TIMEOUT", str(DEFAULT_CIRCUIT_BREAKER_TIMEOUT)))
)


@asynccontextmanager
async def operation_timeout_context(operation_name: str, timeout_seconds: int = 30):
    """Context manager for operation timeouts with automatic circuit breaker management.

    Provides timing, logging, and circuit breaker state management for operations.
    Automatically records failures and resets circuit breaker on success.

    Args:
        operation_name: Name of the operation for logging purposes
        timeout_seconds: Timeout threshold (currently informational only)

    Yields:
        Control to the wrapped operation code block

    Raises:
        Any exception raised by the wrapped operation code
    """
    operation_start_time = time.time()
    print(f"[SECURE_ANALYZER] Starting operation: {operation_name} at {operation_start_time}")

    try:
        yield
        operation_duration = time.time() - operation_start_time
        print(f"[SECURE_ANALYZER] Completed operation: {operation_name} in {operation_duration:.2f}s")
        circuit_breaker.reset()  # Reset circuit breaker on successful operation

    except Exception as e:
        operation_duration = time.time() - operation_start_time
        print(f"[SECURE_ANALYZER] ERROR in operation {operation_name}: {str(e)} after {operation_duration:.2f}s")
        circuit_breaker.record_failure()  # Record failure for circuit breaker
        raise
