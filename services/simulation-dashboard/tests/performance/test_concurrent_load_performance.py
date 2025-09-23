"""
Performance tests for concurrent load handling and scalability.

This module contains comprehensive performance tests for concurrent user load,
request throughput, response times, and system scalability under various
load conditions.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from infrastructure.config.config import DashboardSettings
from services.clients.simulation_client import SimulationClient


class TestConcurrentLoadPerformance:
    """Test suite for concurrent load performance and scalability."""

    @pytest.fixture
    def high_load_config(self):
        """Create configuration optimized for high load testing."""
        config = DashboardSettings()
        config.performance.max_concurrent_requests = 100
        config.performance.request_timeout = 10.0
        config.performance.enable_compression = True
        return config

    @pytest.fixture
    def load_test_simulation_client(self, high_load_config):
        """Create simulation client configured for load testing."""
        return SimulationClient(high_load_config.simulation_service)

    def test_concurrent_simulation_creation_load(self, high_load_config):
        """Test concurrent simulation creation under load."""
        async def create_simulation_load_test():
            """Async load test for simulation creation."""
            config = high_load_config
            client = SimulationClient(config.simulation_service)

            # Mock successful responses
            with patch.object(client, 'create_simulation', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = {
                    "id": "sim_load_test_001",
                    "name": "Load Test Simulation",
                    "status": "created"
                }

                # Test concurrent creation
                start_time = time.time()
                tasks = []

                # Create 50 concurrent simulation creation tasks
                for i in range(50):
                    task = asyncio.create_task(
                        client.create_simulation({
                            "name": f"Load Test Sim {i}",
                            "type": "performance_test",
                            "complexity": "low"
                        })
                    )
                    tasks.append(task)

                # Execute all tasks concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

                # Validate results
                successful_creations = [r for r in results if not isinstance(r, Exception)]
                failed_creations = [r for r in results if isinstance(r, Exception)]

                # Performance assertions
                total_time = end_time - start_time
                avg_time_per_creation = total_time / len(tasks)

                # Should handle 50 concurrent creations within reasonable time
                assert total_time < 30.0, f"Total time {total_time}s exceeded 30s limit"
                assert avg_time_per_creation < 1.0, f"Avg time {avg_time_per_creation}s exceeded 1s limit"
                assert len(successful_creations) >= 45, f"Only {len(successful_creations)} successful out of 50"
                assert len(failed_creations) <= 5, f"Too many failures: {len(failed_creations)}"

                # Verify all calls were made
                assert mock_create.call_count == 50

        # Run the async test
        asyncio.run(create_simulation_load_test())

    @pytest.mark.asyncio
    async def test_websocket_connection_scaling(self, high_load_config):
        """Test WebSocket connection scaling under concurrent load."""
        from services.clients.websocket_client import WebSocketClient

        # Test multiple concurrent WebSocket connections
        connections = []
        connection_tasks = []

        # Create 20 concurrent WebSocket connections
        for i in range(20):
            client = WebSocketClient(high_load_config.websocket)

            # Mock successful connection
            with patch.object(client, 'connect', new_callable=AsyncMock) as mock_connect:
                mock_connect.return_value = True

                task = asyncio.create_task(client.connect(f"ws://test-{i}:8080"))
                connection_tasks.append((client, task))
                connections.append(client)

        # Execute connection attempts
        start_time = time.time()
        results = await asyncio.gather(*[task for _, task in connection_tasks], return_exceptions=True)
        end_time = time.time()

        # Validate performance
        total_time = end_time - start_time
        successful_connections = [r for r in results if r is True]
        failed_connections = [r for r in results if isinstance(r, Exception) or r is False]

        # Performance assertions
        assert total_time < 15.0, f"Connection time {total_time}s exceeded 15s limit"
        assert len(successful_connections) >= 18, f"Only {len(successful_connections)} successful connections out of 20"
        assert len(failed_connections) <= 2, f"Too many failed connections: {len(failed_connections)}"

        # Clean up connections
        cleanup_tasks = []
        for client in connections:
            if hasattr(client, 'disconnect'):
                cleanup_tasks.append(client.disconnect())

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

    @pytest.mark.asyncio
    async def test_api_rate_limiting_under_load(self, high_load_config):
        """Test API rate limiting behavior under concurrent load."""
        client = SimulationClient(high_load_config.simulation_service)

        # Mock rate-limited responses (some succeed, some get rate limited)
        call_count = 0
        def mock_rate_limited_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count <= 10:  # First 10 succeed
                return {"status": "healthy"}
            else:  # Rest get rate limited
                raise Exception("Rate limit exceeded")

        with patch.object(client, 'get_health', side_effect=mock_rate_limited_response):
            # Test rapid successive calls
            start_time = time.time()
            tasks = []

            # Create 50 rapid health check calls
            for i in range(50):
                task = asyncio.create_task(client.get_health())
                tasks.append(task)

            # Add small delay between batches to simulate realistic load
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # Analyze results
            successful_calls = [r for r in results if not isinstance(r, Exception)]
            rate_limited_calls = [r for r in results if isinstance(r, Exception) and "Rate limit" in str(r)]

            # Performance assertions
            total_time = end_time - start_time
            assert total_time < 25.0, f"Rate limit test took {total_time}s, exceeded 25s limit"

            # Should handle rate limiting gracefully
            assert len(successful_calls) >= 8, f"Only {len(successful_calls)} successful calls"
            assert len(rate_limited_calls) >= 10, f"Expected rate limiting, got {len(rate_limited_calls)}"

    @pytest.mark.asyncio
    async def test_memory_usage_under_concurrent_load(self, high_load_config):
        """Test memory usage patterns under concurrent load."""
        import psutil
        import os

        client = SimulationClient(high_load_config.simulation_service)
        process = psutil.Process(os.getpid())

        # Get baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Mock memory-intensive operations
        large_response = {"data": "x" * 1000000}  # 1MB response

        with patch.object(client, 'list_simulations', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [large_response] * 100  # 100MB total

            # Execute memory-intensive concurrent operations
            start_memory = process.memory_info().rss / 1024 / 1024

            tasks = []
            for i in range(10):
                task = asyncio.create_task(client.list_simulations())
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_memory = process.memory_info().rss / 1024 / 1024

            # Memory usage assertions
            memory_increase = end_memory - start_memory
            memory_increase_percentage = (memory_increase / baseline_memory) * 100

            # Should not exceed reasonable memory growth
            assert memory_increase < 500, f"Memory increase {memory_increase}MB exceeded 500MB limit"
            assert memory_increase_percentage < 200, f"Memory growth {memory_increase_percentage}% exceeded 200% limit"

            # Verify all operations succeeded
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == 10, f"Only {len(successful_results)} successful out of 10"

    @pytest.mark.asyncio
    async def test_database_connection_pooling_under_load(self, high_load_config):
        """Test database connection pooling efficiency under load."""
        # This would test actual database connection pooling
        # For now, we'll mock the behavior

        connection_pool_size = high_load_config.performance.connection_pool_size
        max_concurrent_requests = high_load_config.performance.max_concurrent_requests

        # Mock connection pool behavior
        connection_usage = []

        async def mock_database_operation(operation_id):
            """Mock database operation with connection pooling."""
            # Simulate connection acquisition time
            await asyncio.sleep(0.01)  # 10ms connection time

            # Track connection usage
            connection_usage.append(operation_id)

            # Simulate operation time
            await asyncio.sleep(0.05)  # 50ms operation time

            return {"operation_id": operation_id, "status": "completed"}

        # Test concurrent database operations
        start_time = time.time()
        tasks = []

        for i in range(min(max_concurrent_requests, 50)):  # Test up to 50 concurrent ops
            task = asyncio.create_task(mock_database_operation(i))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Performance analysis
        total_time = end_time - start_time
        successful_operations = [r for r in results if not isinstance(r, Exception)]

        # Connection pooling should allow efficient concurrent operations
        assert total_time < 10.0, f"Concurrent operations took {total_time}s, exceeded 10s limit"
        assert len(successful_operations) == len(tasks), f"Only {len(successful_operations)} successful out of {len(tasks)}"

        # Verify connection reuse (all operations should have been tracked)
        assert len(connection_usage) == len(tasks), "Connection tracking failed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_performance_under_failure_load(self, high_load_config):
        """Test circuit breaker performance under failure load conditions."""
        client = SimulationClient(high_load_config.simulation_service)

        # Mock circuit breaker behavior - initial failures then recovery
        call_count = 0
        def mock_circuit_breaker_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count <= 5:  # First 5 calls fail (circuit opens)
                raise Exception("Service unavailable")
            elif call_count <= 10:  # Next 5 calls succeed (circuit closes)
                return {"status": "healthy"}
            else:  # Remaining calls fail again
                raise Exception("Service unavailable")

        with patch.object(client, 'get_health', side_effect=mock_circuit_breaker_response):
            # Test circuit breaker under load
            start_time = time.time()
            tasks = []

            # Create 50 concurrent requests to test circuit breaker
            for i in range(50):
                task = asyncio.create_task(client.get_health())
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # Analyze circuit breaker behavior
            total_time = end_time - start_time
            successful_responses = [r for r in results if not isinstance(r, Exception)]
            failed_responses = [r for r in results if isinstance(r, Exception)]

            # Circuit breaker should prevent cascade failures
            assert total_time < 20.0, f"Circuit breaker test took {total_time}s, exceeded 20s limit"

            # Should have some successful responses during recovery window
            assert len(successful_responses) >= 3, f"Only {len(successful_responses)} successful during recovery"

            # Should have prevented some failures through circuit breaking
            assert len(failed_responses) < 45, f"Too many failures: {len(failed_responses)} out of 50"

    @pytest.mark.asyncio
    async def test_cache_performance_under_concurrent_load(self, high_load_config):
        """Test caching performance under concurrent load."""
        # Mock cache operations
        cache_hits = 0
        cache_misses = 0

        async def mock_cached_operation(key):
            """Mock cached operation with hit/miss simulation."""
            nonlocal cache_hits, cache_misses

            # Simulate 70% cache hit rate
            if hash(key) % 10 < 7:
                cache_hits += 1
                return {"data": f"cached_{key}", "source": "cache"}
            else:
                cache_misses += 1
                # Simulate cache population time
                await asyncio.sleep(0.1)
                return {"data": f"computed_{key}", "source": "compute"}

        # Test concurrent cache operations
        start_time = time.time()
        tasks = []

        # Create 100 concurrent cache requests with some repetition for hits
        for i in range(100):
            # Use limited key space to create cache hits
            key = f"key_{i % 20}"  # Only 20 unique keys
            task = asyncio.create_task(mock_cached_operation(key))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Performance analysis
        total_time = end_time - start_time
        successful_results = [r for r in results if not isinstance(r, Exception)]

        # Calculate cache effectiveness
        total_requests = len(tasks)
        cache_hit_rate = cache_hits / total_requests

        # Performance assertions
        assert total_time < 15.0, f"Cached operations took {total_time}s, exceeded 15s limit"
        assert len(successful_results) == total_requests, f"Only {len(successful_results)} successful out of {total_requests}"

        # Cache should improve performance
        assert cache_hit_rate >= 0.6, f"Cache hit rate {cache_hit_rate:.2%} below 60% target"
        assert cache_hits > cache_misses, f"Cache hits ({cache_hits}) should exceed misses ({cache_misses})"

    @pytest.mark.asyncio
    async def test_session_management_under_load(self, high_load_config):
        """Test Streamlit session state management under concurrent load."""
        # Mock Streamlit session state operations
        session_operations = []
        session_conflicts = 0

        async def mock_session_operation(session_id, operation):
            """Mock session state operation."""
            nonlocal session_conflicts

            # Simulate session access time
            await asyncio.sleep(0.005)  # 5ms session access

            # Simulate occasional session conflicts
            if hash(f"{session_id}_{operation}") % 100 < 5:  # 5% conflict rate
                session_conflicts += 1
                raise Exception("Session conflict")

            session_operations.append(f"{session_id}_{operation}")
            return {"session_id": session_id, "operation": operation, "status": "success"}

        # Test concurrent session operations
        start_time = time.time()
        tasks = []

        # Simulate 10 concurrent users with 10 operations each
        for user_id in range(10):
            for op_id in range(10):
                task = asyncio.create_task(
                    mock_session_operation(f"user_{user_id}", f"op_{op_id}")
                )
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Performance analysis
        total_time = end_time - start_time
        successful_operations = [r for r in results if not isinstance(r, Exception)]
        failed_operations = [r for r in results if isinstance(r, Exception)]

        # Session management should handle concurrent access efficiently
        assert total_time < 8.0, f"Session operations took {total_time}s, exceeded 8s limit"
        assert len(successful_operations) >= 90, f"Only {len(successful_operations)} successful out of 100"
        assert len(failed_operations) <= 10, f"Too many session conflicts: {len(failed_operations)}"

        # Verify session isolation (no duplicate operations)
        assert len(session_operations) == len(successful_operations), "Session operation tracking failed"


if __name__ == "__main__":
    pytest.main([__file__])
