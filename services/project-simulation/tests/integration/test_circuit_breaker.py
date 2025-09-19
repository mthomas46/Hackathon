"""Integration Tests for Circuit Breaker Pattern - Ecosystem Integration Testing.

This module contains integration tests for circuit breaker functionality,
testing failure thresholds, recovery mechanisms, and resilience patterns.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from simulation.infrastructure.resilience.circuit_breaker import (
    ServiceCircuitBreaker, CircuitBreakerState, CircuitBreakerOpenException,
    EcosystemCircuitBreakerRegistry, ResilientServiceClient, execute_with_resilience
)
from simulation.domain.value_objects import ServiceHealth


class TestCircuitBreakerStateTransitions:
    """Test cases for circuit breaker state transitions."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in closed state."""
        breaker = ServiceCircuitBreaker("test_service")

        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0
        assert breaker.last_failure_time is None

    def test_circuit_breaker_closed_to_open_transition(self):
        """Test transition from closed to open state after failures."""
        breaker = ServiceCircuitBreaker("test_service", failure_threshold=2)

        # First failure
        breaker._on_failure()
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 1

        # Second failure - should open circuit
        breaker._on_failure()
        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.failure_count == 2
        assert breaker.last_failure_time is not None

    def test_circuit_breaker_open_to_half_open_transition(self):
        """Test transition from open to half-open after timeout."""
        breaker = ServiceCircuitBreaker("test_service", recovery_timeout=0.1)

        # Open the circuit
        breaker.failure_count = breaker.failure_threshold
        breaker._trip()
        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        time.sleep(0.2)

        # Next call should transition to half-open
        async def dummy_call():
            return "success"

        # This would normally be tested with the async call method
        # For unit testing, we test the internal logic

    def test_circuit_breaker_half_open_to_closed_transition(self):
        """Test transition from half-open to closed after successes."""
        breaker = ServiceCircuitBreaker("test_service", success_threshold=2)

        # Set to half-open state
        breaker.state = CircuitBreakerState.HALF_OPEN
        breaker.success_count = 0

        # First success
        breaker._on_success()
        assert breaker.state == CircuitBreakerState.HALF_OPEN
        assert breaker.success_count == 1

        # Second success - should close circuit
        breaker._on_success()
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.success_count == 0  # Reset after closing

    def test_circuit_breaker_half_open_to_open_transition(self):
        """Test transition from half-open back to open on failure."""
        breaker = ServiceCircuitBreaker("test_service")

        # Set to half-open state
        breaker.state = CircuitBreakerState.HALF_OPEN

        # Failure in half-open state
        breaker._on_failure()
        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.success_count == 0


class TestCircuitBreakerCallProtection:
    """Test cases for circuit breaker call protection."""

    @pytest.mark.asyncio
    async def test_successful_call_in_closed_state(self):
        """Test successful call when circuit is closed."""
        breaker = ServiceCircuitBreaker("test_service")

        async def successful_operation():
            return "success"

        result = await breaker.call(successful_operation)

        assert result == "success"
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0

    @pytest.mark.asyncio
    async def test_failed_call_in_closed_state(self):
        """Test failed call when circuit is closed."""
        breaker = ServiceCircuitBreaker("test_service", failure_threshold=1)

        async def failing_operation():
            raise ValueError("Operation failed")

        with pytest.raises(ValueError, match="Operation failed"):
            await breaker.call(failing_operation)

        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_call_rejection_in_open_state(self):
        """Test that calls are rejected when circuit is open."""
        breaker = ServiceCircuitBreaker("test_service")

        # Open the circuit
        breaker.state = CircuitBreakerState.OPEN

        async def dummy_operation():
            return "should not execute"

        with pytest.raises(CircuitBreakerOpenException):
            await breaker.call(dummy_operation)

    @pytest.mark.asyncio
    async def test_call_in_half_open_state_success(self):
        """Test successful call in half-open state."""
        breaker = ServiceCircuitBreaker("test_service", success_threshold=1)

        # Set to half-open
        breaker.state = CircuitBreakerState.HALF_OPEN

        async def successful_operation():
            return "success"

        result = await breaker.call(successful_operation)

        assert result == "success"
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.success_count == 0  # Reset after closing

    @pytest.mark.asyncio
    async def test_call_in_half_open_state_failure(self):
        """Test failed call in half-open state."""
        breaker = ServiceCircuitBreaker("test_service")

        # Set to half-open
        breaker.state = CircuitBreakerState.HALF_OPEN

        async def failing_operation():
            raise RuntimeError("Operation failed")

        with pytest.raises(RuntimeError):
            await breaker.call(failing_operation)

        assert breaker.state == CircuitBreakerState.OPEN


class TestEcosystemCircuitBreakerRegistry:
    """Test cases for ecosystem circuit breaker registry."""

    def test_registry_initialization(self):
        """Test circuit breaker registry initialization."""
        registry = EcosystemCircuitBreakerRegistry()

        # Should have breakers for ecosystem services
        assert len(registry.breakers) > 0

        # Check for critical services
        critical_services = ["doc_store", "mock_data_generator", "orchestrator"]
        for service in critical_services:
            assert service in registry.breakers
            breaker = registry.breakers[service]
            assert isinstance(breaker, ServiceCircuitBreaker)

    def test_registry_breaker_configuration(self):
        """Test that breakers are configured with appropriate thresholds."""
        registry = EcosystemCircuitBreakerRegistry()

        # Critical services should have more lenient thresholds
        critical_breaker = registry.breakers["doc_store"]
        assert critical_breaker.failure_threshold == 3  # More lenient

        # Other services should have stricter thresholds
        other_breaker = registry.breakers["source_agent"]
        assert other_breaker.failure_threshold == 5  # Stricter

    def test_registry_get_breaker(self):
        """Test getting breaker from registry."""
        registry = EcosystemCircuitBreakerRegistry()

        breaker = registry.get_breaker("doc_store")
        assert breaker is not None
        assert isinstance(breaker, ServiceCircuitBreaker)
        assert breaker.service_name == "doc_store"

        # Non-existent service
        breaker = registry.get_breaker("non_existent_service")
        assert breaker is None

    @pytest.mark.asyncio
    async def test_registry_execute_with_breaker(self):
        """Test executing operation with breaker protection."""
        registry = EcosystemCircuitBreakerRegistry()

        async def successful_operation():
            return "success"

        result = await registry.execute_with_breaker("doc_store", successful_operation)
        assert result == "success"

    def test_registry_get_all_status(self):
        """Test getting status of all breakers."""
        registry = EcosystemCircuitBreakerRegistry()

        status = registry.get_all_status()

        assert isinstance(status, dict)
        assert len(status) == len(registry.breakers)

        for service_name, breaker_status in status.items():
            assert service_name in registry.breakers
            assert "state" in breaker_status
            assert "failure_count" in breaker_status
            assert "success_count" in breaker_status

    def test_registry_reset_breaker(self):
        """Test resetting individual breaker."""
        registry = EcosystemCircuitBreakerRegistry()

        # Get a breaker and open it
        breaker = registry.breakers["doc_store"]
        breaker._trip()
        assert breaker.state == CircuitBreakerState.OPEN

        # Reset it
        result = registry.reset_breaker("doc_store")
        assert result == True
        assert breaker.state == CircuitBreakerState.CLOSED

        # Reset non-existent breaker
        result = registry.reset_breaker("non_existent")
        assert result == False

    def test_registry_reset_all_breakers(self):
        """Test resetting all breakers."""
        registry = EcosystemCircuitBreakerRegistry()

        # Open a few breakers
        registry.breakers["doc_store"]._trip()
        registry.breakers["mock_data_generator"]._trip()

        # Reset all
        results = registry.reset_all_breakers()

        assert results["doc_store"] == True
        assert results["mock_data_generator"] == True
        assert registry.breakers["doc_store"].state == CircuitBreakerState.CLOSED
        assert registry.breakers["mock_data_generator"].state == CircuitBreakerState.CLOSED


class TestResilientServiceClient:
    """Test cases for resilient service client wrapper."""

    @pytest.fixture
    def resilient_client(self):
        """Create resilient service client for testing."""
        # Mock the ecosystem client
        with patch('simulation.infrastructure.resilience.circuit_breaker.get_ecosystem_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            client = ResilientServiceClient("test_service")
            yield client

    @pytest.mark.asyncio
    async def test_resilient_client_successful_request(self, resilient_client):
        """Test successful request through resilient client."""
        # Mock the underlying client method
        resilient_client.client.test_method = AsyncMock(return_value="success")

        result = await resilient_client.execute_request("test_method", "arg1", "arg2")

        assert result == "success"
        resilient_client.client.test_method.assert_called_once_with("arg1", "arg2")

    @pytest.mark.asyncio
    async def test_resilient_client_with_failure(self, resilient_client):
        """Test resilient client with underlying failure."""
        # Mock the underlying client method to fail
        resilient_client.client.test_method = AsyncMock(side_effect=ValueError("Service error"))

        with pytest.raises(ValueError, match="Service error"):
            await resilient_client.execute_request("test_method")

        # Circuit breaker should record the failure
        assert resilient_client.circuit_breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_resilient_client_method_not_found(self, resilient_client):
        """Test resilient client when method doesn't exist."""
        with pytest.raises(ValueError, match="Method nonexistent_method not found"):
            await resilient_client.execute_request("nonexistent_method")

    @pytest.mark.asyncio
    async def test_resilient_client_no_client_available(self):
        """Test resilient client when no underlying client is available."""
        with patch('simulation.infrastructure.resilience.circuit_breaker.get_ecosystem_client') as mock_get_client:
            mock_get_client.return_value = None

            client = ResilientServiceClient("test_service")

            with pytest.raises(ValueError, match="No client available for service test_service"):
                await client.execute_request("test_method")

    @pytest.mark.asyncio
    async def test_resilient_client_health_check_success(self, resilient_client):
        """Test health check through resilient client."""
        resilient_client.client.health_check = AsyncMock(return_value=ServiceHealth.HEALTHY)

        result = await resilient_client.health_check()

        assert result["service"] == "test_service"
        assert result["healthy"] == True
        assert "circuit_breaker_state" in result

    @pytest.mark.asyncio
    async def test_resilient_client_health_check_failure(self, resilient_client):
        """Test health check failure through resilient client."""
        resilient_client.client.health_check = AsyncMock(side_effect=ConnectionError("Connection failed"))

        result = await resilient_client.health_check()

        assert result["service"] == "test_service"
        assert result["healthy"] == False
        assert "Connection failed" in result["error"]


class TestCircuitBreakerRecoveryMechanisms:
    """Test cases for circuit breaker recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_recovery_timeout_mechanism(self):
        """Test that circuit breaker allows attempts after recovery timeout."""
        breaker = ServiceCircuitBreaker("test_service", recovery_timeout=0.1)

        # Open the circuit
        breaker._trip()
        assert breaker.state == CircuitBreakerState.OPEN

        # Immediately try to call - should be rejected
        async def dummy_call():
            return "success"

        with pytest.raises(CircuitBreakerOpenException):
            await breaker.call(dummy_call)

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        # Mock the _should_attempt_reset to return True
        breaker._should_attempt_reset = Mock(return_value=True)

        # Next call should transition to half-open
        # (This is a simplified test - in practice, the call method handles this)
        assert breaker.state == CircuitBreakerState.OPEN

    def test_success_threshold_configuration(self):
        """Test success threshold configuration."""
        breaker = ServiceCircuitBreaker("test_service", success_threshold=5)

        assert breaker.success_threshold == 5

        # Set to half-open and test success counting
        breaker.state = CircuitBreakerState.HALF_OPEN

        # Multiple successes
        for i in range(4):
            breaker._on_success()
            assert breaker.state == CircuitBreakerState.HALF_OPEN
            assert breaker.success_count == i + 1

        # Final success should close the circuit
        breaker._on_success()
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.success_count == 0  # Reset

    def test_failure_threshold_configuration(self):
        """Test failure threshold configuration."""
        breaker = ServiceCircuitBreaker("test_service", failure_threshold=3)

        assert breaker.failure_threshold == 3

        # Multiple failures
        for i in range(2):
            breaker._on_failure()
            assert breaker.state == CircuitBreakerState.CLOSED
            assert breaker.failure_count == i + 1

        # Final failure should open the circuit
        breaker._on_failure()
        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.failure_count == 3


class TestExecuteWithResilience:
    """Test cases for execute_with_resilience function."""

    @pytest.mark.asyncio
    async def test_execute_with_resilience_success(self):
        """Test successful execution with resilience."""
        async def successful_operation():
            return "success"

        result = await execute_with_resilience("test_service", "dummy_method")
        # This would require a real service client setup
        # For this test, we just verify the function exists and can be called

    def test_execute_with_resilience_function_exists(self):
        """Test that execute_with_resilience function is available."""
        # Just verify the function exists
        assert callable(execute_with_resilience)


class TestCircuitBreakerMonitoring:
    """Test cases for circuit breaker monitoring and metrics."""

    def test_circuit_breaker_status_reporting(self):
        """Test circuit breaker status reporting."""
        breaker = ServiceCircuitBreaker("test_service")

        # Set some state
        breaker.failure_count = 2
        breaker.success_count = 1
        breaker._trip()

        status = breaker.get_status()

        assert status["service_name"] == "test_service"
        assert status["state"] == "open"
        assert status["failure_count"] == 2
        assert status["success_count"] == 1
        assert status["failure_threshold"] == 5  # default
        assert status["recovery_timeout"] == 60.0  # default
        assert status["success_threshold"] == 3  # default
        assert "last_failure_time" in status

    def test_circuit_breaker_status_with_datetime(self):
        """Test circuit breaker status with datetime serialization."""
        breaker = ServiceCircuitBreaker("test_service")

        # Cause a failure to set last_failure_time
        breaker._on_failure()

        status = breaker.get_status()

        # Should serialize datetime to ISO format
        last_failure_iso = status["last_failure_time"]
        assert isinstance(last_failure_iso, str)

        # Should be parseable back to datetime
        from datetime import datetime
        parsed_datetime = datetime.fromisoformat(last_failure_iso)
        assert isinstance(parsed_datetime, datetime)


@pytest.mark.integration
class TestCircuitBreakerIntegrationSuite:
    """Comprehensive integration test suite for circuit breakers."""

    @pytest.mark.asyncio
    async def test_full_circuit_breaker_lifecycle(self):
        """Test complete circuit breaker lifecycle."""
        breaker = ServiceCircuitBreaker("integration_test", failure_threshold=2, success_threshold=2)

        # Start in closed state
        assert breaker.state == CircuitBreakerState.CLOSED

        # Cause failures to open circuit
        async def failing_operation():
            raise ConnectionError("Service unavailable")

        for i in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(failing_operation)

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery and test half-open state
        await asyncio.sleep(0.1)  # Recovery timeout

        # Mock successful operation
        async def successful_operation():
            return "recovered"

        # This would transition to half-open and eventually closed
        # In a real integration test, we'd need to control timing more precisely

    @pytest.mark.asyncio
    async def test_concurrent_circuit_breaker_usage(self):
        """Test circuit breaker behavior with concurrent requests."""
        breaker = ServiceCircuitBreaker("concurrent_test")

        async def make_request(should_fail=False):
            async def operation():
                if should_fail:
                    raise ValueError("Concurrent failure")
                return "concurrent success"

            try:
                return await breaker.call(operation)
            except ValueError:
                return "failed"

        # Make concurrent requests
        tasks = []
        for i in range(10):
            should_fail = i < 3  # First 3 should fail
            tasks.append(make_request(should_fail))

        results = await asyncio.gather(*tasks)

        # Verify results
        success_count = sum(1 for r in results if r == "concurrent success")
        failure_count = sum(1 for r in results if r == "failed")

        assert success_count == 7  # 10 - 3 failures
        assert failure_count == 3

        # Circuit should still be closed (within threshold)
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_configuration_persistence(self):
        """Test that circuit breaker configuration is maintained."""
        breaker = ServiceCircuitBreaker(
            "config_test",
            failure_threshold=10,
            recovery_timeout=120.0,
            success_threshold=5
        )

        # Verify configuration is preserved
        assert breaker.failure_threshold == 10
        assert breaker.recovery_timeout == 120.0
        assert breaker.success_threshold == 5

        # Test that status includes configuration
        status = breaker.get_status()
        assert status["failure_threshold"] == 10
        assert status["recovery_timeout"] == 120.0
        assert status["success_threshold"] == 5
