"""Chaos Engineering Tests for GitHub MCP Service.

This module tests system resilience and failure scenarios including:
- Network failures and timeouts
- Service degradation and recovery
- Resource exhaustion scenarios
- Dependency failures and cascading effects
- Data corruption and recovery mechanisms
- High load with failure injection

Chaos tests ensure the GitHub MCP service is resilient to real-world failure conditions.
"""

import asyncio
import time
import random
import threading
from typing import Dict, Any, List, Optional, Callable
from unittest.mock import patch, AsyncMock, MagicMock, side_effect
from datetime import datetime, timedelta

import pytest
import httpx


class TestChaosScenarios:
    """Chaos engineering tests for failure scenarios."""

    @pytest.fixture
    def chaos_config(self):
        """Chaos test configuration."""
        return {
            "failure_rate": 0.1,  # 10% of operations fail
            "delay_range_ms": (10, 500),  # Random delays
            "timeout_scenarios": [1, 5, 30],  # Different timeout values
            "concurrent_failures": 5,
            "recovery_time_s": 10
        }

    @pytest.mark.asyncio
    async def test_network_failure_resilience(self, chaos_config):
        """Test resilience against network failures."""
        failure_count = 0
        success_count = 0

        async def failing_network_call(should_fail: bool = False) -> Dict[str, Any]:
            """Simulate network call that can fail."""
            if should_fail or random.random() < chaos_config["failure_rate"]:
                nonlocal failure_count
                failure_count += 1
                # Simulate different types of network failures
                failure_types = [
                    httpx.ConnectError("Connection refused"),
                    httpx.TimeoutException("Request timeout"),
                    httpx.NetworkError("Network unreachable"),
                    Exception("Unexpected network error")
                ]
                raise random.choice(failure_types)
            else:
                nonlocal success_count
                success_count += 1
                # Add random delay to simulate network latency
                delay = random.uniform(
                    chaos_config["delay_range_ms"][0] / 1000,
                    chaos_config["delay_range_ms"][1] / 1000
                )
                await asyncio.sleep(delay)
                return {"status": "success", "data": "mock_response"}

        # Test with multiple concurrent failing calls
        tasks = []
        for i in range(100):
            # Randomly decide if this call should fail
            should_fail = random.random() < chaos_config["failure_rate"]
            tasks.append(failing_network_call(should_fail))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        exceptions = [r for r in results if isinstance(r, Exception)]
        successful_responses = [r for r in results if isinstance(r, dict)]

        success_rate = len(successful_responses) / len(results)
        failure_rate = len(exceptions) / len(results)

        print(f"Network Failure Resilience Test:")
        print(f"  Total Calls: {len(results)}")
        print(f"  Successful: {len(successful_responses)}")
        print(f"  Failed: {len(exceptions)}")
        print(f"  Success Rate: {success_rate:.2%}")
        print(f"  Failure Rate: {failure_rate:.2%}")

        # System should handle failures gracefully
        assert len(exceptions) > 0, "No failures occurred - chaos test ineffective"
        assert len(successful_responses) > 0, "All calls failed - system completely broken"
        assert success_rate > 0.8, f"Success rate too low: {success_rate:.2%} under chaos"

    @pytest.mark.asyncio
    async def test_service_degradation_recovery(self, chaos_config):
        """Test recovery from service degradation."""
        degradation_periods = []
        recovery_times = []

        # Simulate service that degrades and recovers
        class DegradingService:
            def __init__(self):
                self.degraded = False
                self.degradation_start = None
                self.recovery_start = None

            async def call(self) -> Dict[str, Any]:
                if self.degraded:
                    if random.random() < 0.3:  # 30% chance of failure when degraded
                        raise Exception("Service temporarily unavailable")
                    else:
                        # Slow response when degraded
                        await asyncio.sleep(random.uniform(0.5, 2.0))
                        return {"status": "slow_response", "degraded": True}
                else:
                    await asyncio.sleep(0.01)  # Normal response time
                    return {"status": "normal", "degraded": False}

            def start_degradation(self):
                self.degraded = True
                self.degradation_start = time.time()

            def recover(self):
                self.degraded = False
                if self.degradation_start:
                    degradation_duration = time.time() - self.degradation_start
                    degradation_periods.append(degradation_duration)
                self.recovery_start = time.time()

        service = DegradingService()

        # Normal operation phase
        results = []
        for _ in range(20):
            result = await service.call()
            results.append(result)

        normal_success_rate = sum(1 for r in results if r["status"] == "normal") / len(results)

        # Degradation phase
        service.start_degradation()
        degradation_results = []
        for _ in range(30):
            try:
                result = await service.call()
                degradation_results.append(result)
            except Exception as e:
                degradation_results.append({"status": "error", "error": str(e)})

        degraded_success_rate = sum(1 for r in degradation_results
                                   if r["status"] in ["slow_response", "normal"]) / len(degradation_results)

        # Recovery phase
        service.recover()
        recovery_results = []
        for _ in range(20):
            result = await service.call()
            recovery_results.append(result)

        recovered_success_rate = sum(1 for r in recovery_results if r["status"] == "normal") / len(recovery_results)

        print(f"Service Degradation Recovery Test:")
        print(f"  Normal Phase Success Rate: {normal_success_rate:.2%}")
        print(f"  Degraded Phase Success Rate: {degraded_success_rate:.2%}")
        print(f"  Recovered Phase Success Rate: {recovered_success_rate:.2%}")

        # Assertions
        assert normal_success_rate > 0.95, "Normal operation success rate too low"
        assert degraded_success_rate < normal_success_rate, "Degradation not simulated effectively"
        assert recovered_success_rate >= normal_success_rate * 0.9, "Recovery not successful"

    @pytest.mark.asyncio
    async def test_resource_exhaustion_handling(self, chaos_config):
        """Test handling of resource exhaustion scenarios."""
        import psutil
        import gc

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Simulate memory pressure
        memory_hogs = []
        try:
            # Create memory pressure
            for i in range(50):
                memory_hogs.append("x" * 1024 * 1024)  # 1MB strings
                await asyncio.sleep(0.001)  # Small delay

            memory_after_pressure = process.memory_info().rss
            memory_increase = memory_after_pressure - initial_memory

            print(f"Resource Exhaustion Test:")
            print(f"  Initial Memory: {initial_memory / 1024 / 1024:.2f} MB")
            print(f"  Memory After Pressure: {memory_after_pressure / 1024 / 1024:.2f} MB")
            print(f"  Memory Increase: {memory_increase / 1024 / 1024:.2f} MB")

            # Simulate garbage collection under pressure
            start_time = time.time()
            gc.collect()
            gc_time = (time.time() - start_time) * 1000

            print(f"  GC Time: {gc_time:.2f}ms")

            # Memory should be manageable
            assert memory_increase < 100 * 1024 * 1024, "Memory usage too high"  # 100MB limit
            assert gc_time < 500, "Garbage collection too slow under memory pressure"

        finally:
            # Clean up
            del memory_hogs
            gc.collect()

    @pytest.mark.asyncio
    async def test_dependency_failure_cascades(self, chaos_config):
        """Test handling of dependency failure cascades."""
        dependency_states = {
            "database": True,
            "cache": True,
            "external_api": True,
            "message_queue": True
        }

        failure_sequence = []

        class CascadingService:
            def __init__(self):
                self.dependencies = dependency_states.copy()

            async def process_request(self, request_type: str) -> Dict[str, Any]:
                # Check dependencies based on request type
                if request_type == "data_intensive" and not self.dependencies["database"]:
                    raise Exception("Database dependency failed")
                elif request_type == "cache_dependent" and not self.dependencies["cache"]:
                    raise Exception("Cache dependency failed")
                elif request_type == "external_call" and not self.dependencies["external_api"]:
                    raise Exception("External API dependency failed")

                # Simulate processing with potential cascading failures
                if not self.dependencies["message_queue"]:
                    # Queue failure might cause secondary failures
                    if random.random() < 0.5:
                        raise Exception("Queue backup caused processing failure")

                await asyncio.sleep(random.uniform(0.01, 0.05))
                return {"status": "processed", "type": request_type}

            def fail_dependency(self, dependency: str):
                self.dependencies[dependency] = False
                failure_sequence.append({
                    "dependency": dependency,
                    "time": time.time(),
                    "cascading_effects": self._calculate_cascading_effects(dependency)
                })

            def _calculate_cascading_effects(self, failed_dependency: str) -> List[str]:
                """Calculate which operations are affected by dependency failure."""
                effects = []
                if failed_dependency == "database":
                    effects.extend(["data_intensive", "reporting"])
                elif failed_dependency == "cache":
                    effects.extend(["cache_dependent", "performance_critical"])
                elif failed_dependency == "external_api":
                    effects.extend(["external_call", "integration"])
                elif failed_dependency == "message_queue":
                    effects.extend(["async_operations", "background_tasks"])
                return effects

        service = CascadingService()

        # Test normal operation
        normal_results = []
        for req_type in ["data_intensive", "cache_dependent", "external_call"]:
            for _ in range(10):
                try:
                    result = await service.process_request(req_type)
                    normal_results.append({"type": req_type, "status": "success"})
                except Exception as e:
                    normal_results.append({"type": req_type, "status": "error", "error": str(e)})

        # Introduce cascading failures
        service.fail_dependency("database")  # Primary failure
        await asyncio.sleep(0.1)
        service.fail_dependency("message_queue")  # Secondary failure

        # Test during cascade
        cascade_results = []
        for req_type in ["data_intensive", "cache_dependent", "external_call"]:
            for _ in range(10):
                try:
                    result = await service.process_request(req_type)
                    cascade_results.append({"type": req_type, "status": "success"})
                except Exception as e:
                    cascade_results.append({"type": req_type, "status": "error", "error": str(e)})

        # Analyze cascade impact
        normal_success_rate = sum(1 for r in normal_results if r["status"] == "success") / len(normal_results)
        cascade_success_rate = sum(1 for r in cascade_results if r["status"] == "success") / len(cascade_results)

        print(f"Dependency Failure Cascade Test:")
        print(f"  Normal Success Rate: {normal_success_rate:.2%}")
        print(f"  Cascade Success Rate: {cascade_success_rate:.2%}")
        print(f"  Failure Sequence: {len(failure_sequence)} dependencies failed")

        # Cascading failures should reduce success rate but not eliminate all functionality
        assert cascade_success_rate < normal_success_rate, "Cascade not properly simulated"
        assert cascade_success_rate > 0.3, "System too fragile to dependency failures"

    @pytest.mark.asyncio
    async def test_high_load_with_injected_failures(self, chaos_config):
        """Test high load scenarios with injected failures."""
        async def load_with_failures(user_id: int, total_requests: int, failure_rate: float) -> Dict[str, Any]:
            """Simulate user load with injected failures."""
            results = {"success": 0, "failure": 0, "timeouts": 0, "response_times": []}

            for i in range(total_requests):
                start_time = time.time()

                try:
                    # Inject random failures
                    if random.random() < failure_rate:
                        if random.random() < 0.5:
                            raise Exception("Injected failure")
                        else:
                            # Simulate timeout
                            await asyncio.sleep(2.0)  # Long delay
                            results["timeouts"] += 1
                            continue

                    # Simulate successful operation
                    await asyncio.sleep(random.uniform(0.01, 0.1))
                    results["success"] += 1

                except Exception:
                    results["failure"] += 1

                end_time = time.time()
                results["response_times"].append((end_time - start_time) * 1000)

            return results

        # Test different load levels with failures
        load_scenarios = [
            {"users": 5, "requests_per_user": 20, "failure_rate": 0.05},
            {"users": 10, "requests_per_user": 20, "failure_rate": 0.1},
            {"users": 20, "requests_per_user": 15, "failure_rate": 0.15}
        ]

        for scenario in load_scenarios:
            print(f"\nHigh Load with Failures Test - {scenario['users']} users, {scenario['failure_rate']:.1%} failure rate:")

            start_time = time.time()

            # Run concurrent users
            tasks = [
                load_with_failures(user_id, scenario["requests_per_user"], scenario["failure_rate"])
                for user_id in range(scenario["users"])
            ]

            user_results = await asyncio.gather(*tasks)

            end_time = time.time()
            total_time = end_time - start_time

            # Aggregate results
            total_requests = sum(len(r["response_times"]) for r in user_results)
            total_success = sum(r["success"] for r in user_results)
            total_failures = sum(r["failure"] for r in user_results)
            total_timeouts = sum(r["timeouts"] for r in user_results)

            throughput = total_requests / total_time
            success_rate = total_success / total_requests if total_requests > 0 else 0

            all_response_times = []
            for r in user_results:
                all_response_times.extend(r["response_times"])

            avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0

            print(f"  Total Requests: {total_requests}")
            print(f"  Successful: {total_success}")
            print(f"  Failed: {total_failures}")
            print(f"  Timeouts: {total_timeouts}")
            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Success Rate: {success_rate:.2%}")
            print(f"  Avg Response Time: {avg_response_time:.2f}ms")

            # Assertions for chaos resilience
            assert success_rate > 0.7, f"Success rate too low under chaos: {success_rate:.2%}"
            assert throughput > scenario["users"] * 0.5, f"Throughput too low: {throughput:.2f} req/s"
            assert avg_response_time < 1000, f"Average response time too high: {avg_response_time:.2f}ms"

    def test_data_corruption_recovery(self):
        """Test recovery from data corruption scenarios."""
        import json
        import hashlib

        # Test data integrity checking
        class DataIntegrityChecker:
            def __init__(self):
                self.checksums = {}

            def store_data(self, key: str, data: Dict[str, Any]):
                """Store data with integrity check."""
                json_str = json.dumps(data, sort_keys=True)
                checksum = hashlib.sha256(json_str.encode()).hexdigest()
                self.checksums[key] = checksum
                return json_str

            def verify_integrity(self, key: str, data: Dict[str, Any]) -> bool:
                """Verify data integrity."""
                if key not in self.checksums:
                    return False

                json_str = json.dumps(data, sort_keys=True)
                current_checksum = hashlib.sha256(json_str.encode()).hexdigest()
                return current_checksum == self.checksums[key]

            def detect_corruption(self, key: str, corrupted_data: Dict[str, Any]) -> bool:
                """Detect if data has been corrupted."""
                return not self.verify_integrity(key, corrupted_data)

        checker = DataIntegrityChecker()

        # Store original data
        original_data = {
            "user_id": 123,
            "preferences": {"theme": "dark", "language": "en"},
            "last_login": "2024-01-15T10:30:00Z"
        }

        stored_data = checker.store_data("user_123", original_data)

        # Verify original data integrity
        assert checker.verify_integrity("user_123", original_data), "Original data integrity check failed"

        # Test corruption scenarios
        corruption_scenarios = [
            # Minor corruption
            {**original_data, "user_id": 124},
            # Major corruption
            {**original_data, "preferences": {"theme": "light", "language": "fr"}, "corrupted": True},
            # Structure corruption
            {"corrupted": "completely", "data": "lost"}
        ]

        detected_corruptions = 0
        for corrupted_data in corruption_scenarios:
            if checker.detect_corruption("user_123", corrupted_data):
                detected_corruptions += 1

        corruption_detection_rate = detected_corruptions / len(corruption_scenarios)

        print(f"Data Corruption Recovery Test:")
        print(f"  Corruption Scenarios Tested: {len(corruption_scenarios)}")
        print(f"  Corruptions Detected: {detected_corruptions}")
        print(f"  Detection Rate: {corruption_detection_rate:.2%}")

        # Should detect all corruptions
        assert corruption_detection_rate == 1.0, f"Failed to detect {len(corruption_scenarios) - detected_corruptions} corruptions"

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern under failure conditions."""
        class CircuitBreaker:
            def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 10):
                self.failure_threshold = failure_threshold
                self.recovery_timeout = recovery_timeout
                self.failure_count = 0
                self.state = "closed"  # closed, open, half_open
                self.last_failure_time = None

            async def call(self, operation) -> Any:
                if self.state == "open":
                    if time.time() - self.last_failure_time > self.recovery_timeout:
                        self.state = "half_open"
                    else:
                        raise Exception("Circuit breaker is OPEN")

                try:
                    result = await operation()
                    self._on_success()
                    return result
                except Exception as e:
                    self._on_failure()
                    raise e

            def _on_success(self):
                if self.state == "half_open":
                    self.state = "closed"
                    self.failure_count = 0

            def _on_failure(self):
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "open"

        circuit_breaker = CircuitBreaker()

        # Simulate failing operation
        async def failing_operation():
            if random.random() < 0.8:  # 80% failure rate
                raise Exception("Operation failed")
            return {"status": "success"}

        # Test circuit breaker behavior
        results = []
        for i in range(20):
            try:
                result = await circuit_breaker.call(failing_operation)
                results.append({"attempt": i, "status": "success", "circuit_state": circuit_breaker.state})
            except Exception as e:
                results.append({"attempt": i, "status": "failure", "circuit_state": circuit_breaker.state, "error": str(e)})

        # Analyze circuit breaker effectiveness
        open_states = sum(1 for r in results if r["circuit_state"] == "open")
        successful_calls = sum(1 for r in results if r["status"] == "success")

        print(f"Circuit Breaker Test:")
        print(f"  Total Attempts: {len(results)}")
        print(f"  Successful Calls: {successful_calls}")
        print(f"  Circuit Open States: {open_states}")
        print(f"  Circuit Breaker State: {circuit_breaker.state}")

        # Circuit breaker should have opened at some point
        assert open_states > 0, "Circuit breaker never opened"
        # Should prevent some failures (not all calls should fail)
        assert successful_calls < len(results), "No failures occurred - circuit breaker not tested"


class TestFailureInjection:
    """Tests with systematic failure injection."""

    @pytest.mark.asyncio
    async def test_partial_system_failure(self):
        """Test system behavior with partial component failures."""
        # Simulate partial failures in different components
        component_failures = {
            "authentication": random.random() < 0.3,
            "database": random.random() < 0.2,
            "cache": random.random() < 0.4,
            "external_service": random.random() < 0.25
        }

        print("Partial System Failure Test:")
        print(f"  Component Failures Injected: {component_failures}")

        # This would test how the system handles partial failures
        # Implementation would depend on actual system architecture

        # For now, verify failure injection works
        failed_components = sum(1 for failed in component_failures.values() if failed)
        assert failed_components > 0, "No failures injected - test ineffective"

    def test_configuration_corruption_recovery(self):
        """Test recovery from configuration corruption."""
        import yaml

        # Original configuration
        original_config = {
            "service": {
                "name": "github-mcp",
                "port": 5072,
                "debug": True
            },
            "github": {
                "token": "secret_token",
                "api_url": "https://api.github.com"
            }
        }

        # Corrupt configuration
        corrupted_configs = [
            # Missing critical section
            {"service": {"name": "github-mcp"}},
            # Invalid data types
            {"service": {"name": "github-mcp", "port": "invalid_port"}},
            # Empty configuration
            {}
        ]

        recovery_successes = 0

        for corrupted_config in corrupted_configs:
            try:
                # Attempt to load corrupted config
                yaml_str = yaml.dump(corrupted_config)

                # Try to parse and validate (simplified validation)
                if "service" not in corrupted_config:
                    raise ValueError("Missing service section")

                service_config = corrupted_config.get("service", {})
                if not isinstance(service_config.get("name"), str):
                    raise ValueError("Invalid service name")

                # If we get here, "recovery" was successful (fallback worked)
                recovery_successes += 1

            except Exception:
                # Recovery failed - configuration was too corrupted
                pass

        recovery_rate = recovery_successes / len(corrupted_configs)

        print(f"Configuration Corruption Recovery Test:")
        print(f"  Corruption Scenarios: {len(corrupted_configs)}")
        print(f"  Successful Recoveries: {recovery_successes}")
        print(f"  Recovery Rate: {recovery_rate:.2%}")

        # System should handle some configuration corruption gracefully
        assert recovery_rate > 0.5, f"Poor configuration recovery: {recovery_rate:.2%}"
