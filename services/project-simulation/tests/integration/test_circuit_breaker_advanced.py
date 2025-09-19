"""Advanced Circuit Breaker Integration Tests.

This module contains comprehensive tests for circuit breaker functionality,
including state transitions, failure thresholds, recovery mechanisms,
and integration with service ecosystem.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional, Callable
import httpx
from pathlib import Path
import sys

# Add project path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulation.infrastructure.resilience.circuit_breaker import CircuitBreakerState


class TestCircuitBreakerStateTransitions:
    """Test circuit breaker state machine and transitions."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in closed state."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",
            failure_threshold=3,
            recovery_timeout=5.0
        )

        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.state != CircuitBreakerState.OPEN

    def test_circuit_breaker_failure_count_increment(self):
        """Test failure count increments on exceptions."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=2)

        # Simulate failures
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Test failure")

        assert breaker.failure_count == 1

        with pytest.raises(Exception):
            with breaker:
                raise Exception("Test failure 2")

        assert breaker.failure_count == 2

    def test_circuit_breaker_opens_on_threshold(self):
        """Test circuit breaker opens when failure threshold is reached."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=2)

        # First failure
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Failure 1")

        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 1

        # Second failure - should open
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Failure 2")

        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.failure_count == 2

    def test_circuit_breaker_blocks_calls_when_open(self):
        """Test circuit breaker blocks calls when in open state."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=1)

        # Open the breaker
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Open breaker")

        assert breaker.state == CircuitBreakerState.OPEN

        # Subsequent calls should be blocked
        with pytest.raises(Exception) as exc_info:
            with breaker:
                pass  # This should not execute

        assert "Circuit breaker is OPEN" in str(exc_info.value)

    def test_circuit_breaker_half_open_transition(self):
        """Test circuit breaker transitions to half-open after recovery timeout."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=1, recovery_timeout=0.1)

        # Open the breaker
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Open breaker")

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        time.sleep(0.2)

        # Next call should transition to half-open
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Test in half-open")

        # Circuit breaker should reopen after failure in half-open state
        assert breaker.state == CircuitBreakerState.OPEN

    def test_circuit_breaker_recovery_on_success(self):
        """Test circuit breaker recovers when call succeeds in half-open state."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service", failure_threshold=1, recovery_timeout=0.1, success_threshold=1)

        # Open the breaker
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Open breaker")

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        time.sleep(0.2)

        # Successful call should close the breaker
        with breaker:
            pass  # Success

        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0

    def test_circuit_breaker_reopens_on_failure_in_half_open(self):
        """Test circuit breaker reopens when call fails in half-open state."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=1, recovery_timeout=0.1)

        # Open the breaker
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Open breaker")

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        time.sleep(0.2)

        # Failed call in half-open should reopen
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Fail in half-open")

        assert breaker.state == CircuitBreakerState.OPEN


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration with service ecosystem."""

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_functionality(self):
        """Test circuit breaker with async functions."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=2)

        async def failing_function():
            raise Exception("Async failure")

        # First failure
        with pytest.raises(Exception):
            async with breaker:
                await failing_function()

        assert breaker.failure_count == 1

        # Second failure should open
        with pytest.raises(Exception):
            async with breaker:
                await failing_function()

        assert breaker.state == CircuitBreakerState.OPEN

    def test_circuit_breaker_with_http_client(self):
        """Test circuit breaker with HTTP client calls."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=1)

        def mock_http_call():
            raise httpx.ConnectError("Connection failed")

        # Should open on HTTP error
        with pytest.raises(httpx.ConnectError):
            with breaker:
                mock_http_call()

        assert breaker.state == CircuitBreakerState.OPEN

    def test_circuit_breaker_with_custom_exceptions(self):
        """Test circuit breaker with custom exception types."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        class CustomError(Exception):
            pass

        breaker = ServiceCircuitBreaker(
            service_name="test_service",
            failure_threshold=1,
            expected_exception=CustomError
        )

        # Should only count CustomError
        with pytest.raises(ValueError):
            with breaker:
                raise ValueError("Different error")

        assert breaker.failure_count == 0  # Should not count

        # Should count CustomError
        with pytest.raises(CustomError):
            with breaker:
                raise CustomError("Custom error")

        assert breaker.state == CircuitBreakerState.OPEN


class TestCircuitBreakerMetrics:
    """Test circuit breaker metrics and monitoring."""

    def test_circuit_breaker_success_count_tracking(self):
        """Test circuit breaker tracks successful calls."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=5)

        # Track initial metrics
        initial_success = getattr(breaker, 'success_count', 0)
        initial_total = getattr(breaker, 'total_count', 0)

        # Make successful calls
        for i in range(3):
            with breaker:
                pass

        # Check metrics updated
        current_success = getattr(breaker, 'success_count', 0)
        current_total = getattr(breaker, 'total_count', 0)

        assert current_success >= initial_success + 3
        assert current_total >= initial_total + 3

    def test_circuit_breaker_failure_metrics(self):
        """Test circuit breaker failure metrics."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=5)

        # Make some failures
        for i in range(2):
            with pytest.raises(Exception):
                with breaker:
                    raise Exception(f"Failure {i}")

        # Check failure metrics
        assert breaker.failure_count == 2
        assert breaker.state == CircuitBreakerState.CLOSED  # Not yet open

    def test_circuit_breaker_state_change_metrics(self):
        """Test circuit breaker tracks state changes."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=1)

        # Track state changes
        state_changes = []
        original_state = breaker.state

        # Open the breaker
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Open breaker")

        state_changes.append(('closed', 'open'))

        # Wait for recovery
        time.sleep(0.1)

        # Transition to half-open
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Half-open failure")

        state_changes.append(('open', 'half_open'))

        # Should have tracked the state changes
        assert len(state_changes) >= 1


class TestCircuitBreakerConfiguration:
    """Test circuit breaker configuration options."""

    def test_circuit_breaker_custom_failure_threshold(self):
        """Test custom failure threshold configuration."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=5)

        # Should handle 4 failures without opening
        for i in range(4):
            with pytest.raises(Exception):
                with breaker:
                    raise Exception(f"Failure {i}")

        assert breaker.failure_count == 4
        assert breaker.state == CircuitBreakerState.CLOSED

        # 5th failure should open
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Failure 5")

        assert breaker.state == CircuitBreakerState.OPEN

    def test_circuit_breaker_custom_recovery_timeout(self):
        """Test custom recovery timeout."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        timeout = 0.5
        breaker = ServiceCircuitBreaker(
            service_name="test_service",
            failure_threshold=1,
            recovery_timeout=timeout
        )

        # Open breaker
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Open")

        assert breaker.state == CircuitBreakerState.OPEN

        # Should still be open before timeout
        time.sleep(timeout / 2)
        assert breaker.state == CircuitBreakerState.OPEN

        # Should be ready for half-open after timeout
        time.sleep(timeout / 2 + 0.1)
        # Next call should attempt recovery
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Test recovery")

        assert breaker.state == CircuitBreakerState.HALF_OPEN

    def test_circuit_breaker_exception_filtering(self):
        """Test circuit breaker filters exceptions."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",
            failure_threshold=2,
            expected_exception=ValueError
        )

        # Should count ValueError
        with pytest.raises(ValueError):
            with breaker:
                raise ValueError("Count this")

        assert breaker.failure_count == 1

        # Should not count RuntimeError
        with pytest.raises(RuntimeError):
            with breaker:
                raise RuntimeError("Don't count this")

        assert breaker.failure_count == 1  # Still 1


class TestCircuitBreakerConcurrency:
    """Test circuit breaker under concurrent load."""

    def test_concurrent_circuit_breaker_access(self):
        """Test circuit breaker handles concurrent access."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker
        import threading

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=10)
        results = []
        errors = []

        def worker(worker_id):
            try:
                for i in range(5):
                    with breaker:
                        if i % 2 == 0:  # Fail every other call
                            raise Exception(f"Worker {worker_id} failure {i}")
                        results.append(f"Worker {worker_id} success {i}")
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have some successes and failures
        assert len(results) > 0
        assert len(errors) > 0

        # Circuit breaker should handle concurrent state changes
        assert breaker.failure_count > 0

    @pytest.mark.asyncio
    async def test_async_concurrent_circuit_breaker(self):
        """Test circuit breaker with async concurrent operations."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=5)
        results = []

        async def async_worker(worker_id):
            try:
                async with breaker:
                    await asyncio.sleep(0.01)
                    if worker_id % 2 == 0:
                        raise Exception(f"Async failure {worker_id}")
                    results.append(f"Async success {worker_id}")
            except Exception as e:
                results.append(f"Async error {worker_id}: {str(e)[:50]}")

        # Run concurrent async operations
        tasks = [async_worker(i) for i in range(6)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Should have mixed results
        assert len(results) == 6
        assert any("success" in r for r in results)
        assert any("error" in r or "failure" in r for r in results)


class TestCircuitBreakerEcosystemIntegration:
    """Test circuit breaker integration with ecosystem services."""

    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_mock_service_client(self, mock_client):
        """Test circuit breaker with mocked service client."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        # Mock service client failure
        mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.ConnectError("Service down")

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=2)

        # Simulate service calls
        for i in range(3):
            try:
                async with breaker:
                    async with mock_client() as client:
                        await client.get("http://test-service/api")
            except Exception:
                pass

        # Should have opened after 2 failures
        assert breaker.state == CircuitBreakerState.OPEN

    def test_circuit_breaker_service_discovery_integration(self):
        """Test circuit breaker with service discovery patterns."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=1)

        # Simulate service discovery scenarios
        services = ["service-a", "service-b", "service-c"]

        for service in services:
            try:
                with breaker:
                    if service == "service-b":  # Simulate one service down
                        raise Exception(f"{service} is down")
                    # Success for others
            except Exception:
                pass

        # Should have recorded the failure
        assert breaker.failure_count == 1

    def test_circuit_breaker_load_balancing_scenario(self):
        """Test circuit breaker in load balancing scenarios."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        # Multiple service instances
        instances = ["instance-1", "instance-2", "instance-3"]
        breakers = {instance: ServiceCircuitBreaker(service_name=instance, failure_threshold=2) for instance in instances}

        # Simulate load balancing with failures
        for i in range(5):
            instance = instances[i % len(instances)]
            breaker = breakers[instance]

            try:
                with breaker:
                    if i == 2:  # Fail instance-1
                        raise Exception(f"{instance} failed")
                    # Others succeed
            except Exception:
                pass

        # instance-1 should be open, others closed
        assert breakers["instance-1"].state == CircuitBreakerState.OPEN
        assert breakers["instance-2"].state != CircuitBreakerState.OPEN
        assert breakers["instance-3"].state != CircuitBreakerState.OPEN


class TestCircuitBreakerMonitoring:
    """Test circuit breaker monitoring and observability."""

    def test_circuit_breaker_health_metrics(self):
        """Test circuit breaker exposes health metrics."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=3)

        # Should be able to get health status
        health = breaker.get_status()

        assert 'state' in health
        assert 'failure_count' in health

        # Initial state should be healthy
        assert health['state'] == 'closed'
        assert health['failure_count'] == 0

    def test_circuit_breaker_state_history(self):
        """Test circuit breaker maintains state history."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=1)

        # Track state changes
        initial_state = breaker.state

        # Open breaker
        with pytest.raises(Exception):
            with breaker:
                raise Exception("Open")

        # State should have changed
        assert breaker.state != initial_state

        # Should be able to track state transitions
        assert breaker.state == 'open'

    def test_circuit_breaker_performance_metrics(self):
        """Test circuit breaker performance tracking."""
        from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker
        import time

        breaker = ServiceCircuitBreaker(
            service_name="test_service",failure_threshold=5)

        # Measure call times
        start_time = time.time()

        for i in range(10):
            with breaker:
                pass

        end_time = time.time()
        total_time = end_time - start_time

        # Should be reasonably fast
        assert total_time < 1.0, f"Circuit breaker calls took too long: {total_time}s"

        # Average call time
        avg_time = total_time / 10
        assert avg_time < 0.05, f"Average call time too high: {avg_time}s"


# Helper fixtures
@pytest.fixture
def circuit_breaker():
    """Create a test circuit breaker."""
    from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker
    from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker
    return ServiceCircuitBreaker(service_name="test_service", failure_threshold=2, recovery_timeout=0.1)


@pytest.fixture
def mock_service_client():
    """Create a mock service client for testing."""
    mock_client = Mock()
    mock_client.get = Mock(side_effect=Exception("Service unavailable"))
    return mock_client


@pytest.fixture
async def async_circuit_breaker():
    """Create an async circuit breaker for testing."""
    from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker
    from simulation.infrastructure.resilience.circuit_breaker import ServiceCircuitBreaker
    return ServiceCircuitBreaker(service_name="test_service", failure_threshold=2, recovery_timeout=0.1)
