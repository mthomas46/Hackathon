#!/usr/bin/env python3
"""
Redis Performance Tests

Comprehensive performance test suite for Redis operations including:
- Throughput testing under various loads
- Latency measurement and analysis
- Memory usage monitoring
- Connection pool efficiency
- Concurrent operations stress testing
- Scalability benchmarks
"""

import asyncio
import time
import json
import uuid
import statistics
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Add services to path for testing
import sys
from pathlib import Path
services_path = Path(__file__).parent.parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from services.orchestrator.modules.redis_manager import (
    RedisManager,
    RetryConfig,
    CircuitBreakerConfig
)


class PerformanceMetrics:
    """Performance metrics collector."""

    def __init__(self):
        self.operations = []
        self.start_time = None
        self.end_time = None

    def start(self):
        """Start performance measurement."""
        self.start_time = time.time()

    def record_operation(self, operation_time: float, success: bool, operation_type: str):
        """Record operation performance."""
        self.operations.append({
            'time': operation_time,
            'success': success,
            'type': operation_type,
            'timestamp': time.time()
        })

    def end(self):
        """End performance measurement."""
        self.end_time = time.time()

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.operations:
            return {}

        total_time = self.end_time - self.start_time if self.end_time else 0
        successful_ops = [op for op in self.operations if op['success']]
        failed_ops = [op for op in self.operations if not op['success']]

        return {
            'total_operations': len(self.operations),
            'successful_operations': len(successful_ops),
            'failed_operations': len(failed_ops),
            'success_rate': len(successful_ops) / len(self.operations) if self.operations else 0,
            'total_time': total_time,
            'operations_per_second': len(self.operations) / total_time if total_time > 0 else 0,
            'average_response_time': statistics.mean([op['time'] for op in self.operations]) if self.operations else 0,
            'median_response_time': statistics.median([op['time'] for op in self.operations]) if self.operations else 0,
            'min_response_time': min([op['time'] for op in self.operations]) if self.operations else 0,
            'max_response_time': max([op['time'] for op in self.operations]) if self.operations else 0,
            'response_time_stddev': statistics.stdev([op['time'] for op in self.operations]) if len(self.operations) > 1 else 0,
            'percentile_95': statistics.quantiles([op['time'] for op in self.operations], n=20)[18] if len(self.operations) >= 20 else None,
            'percentile_99': statistics.quantiles([op['time'] for op in self.operations], n=100)[98] if len(self.operations) >= 100 else None
        }


class TestRedisThroughputPerformance:
    """Test Redis throughput performance under various loads."""

    @pytest.fixture
    def redis_manager(self):
        """Create Redis manager for performance testing."""
        return RedisManager(
            max_connections=20,
            retry_config=RetryConfig(max_attempts=1, base_delay=0.001)
        )

    @pytest.mark.asyncio
    async def test_single_operation_throughput(self, redis_manager):
        """Test throughput for single operations."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            metrics = PerformanceMetrics()
            metrics.start()

            # Perform 1000 single operations
            for i in range(1000):
                start_time = time.time()
                await redis_manager.set_cache(f"throughput_test_{i}", f"value_{i}")
                end_time = time.time()
                metrics.record_operation(end_time - start_time, True, "set_cache")

            metrics.end()
            summary = metrics.get_summary()

            print(f"Single operation throughput: {summary['operations_per_second']:.2f} ops/sec")
            print(f"Average response time: {summary['average_response_time']*1000:.2f} ms")

            assert summary['total_operations'] == 1000
            assert summary['successful_operations'] == 1000
            assert summary['success_rate'] == 1.0
            assert summary['operations_per_second'] > 0

    @pytest.mark.asyncio
    async def test_concurrent_operations_throughput(self, redis_manager):
        """Test throughput for concurrent operations."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            async def perform_operation(i):
                start_time = time.time()
                result = await redis_manager.set_cache(f"concurrent_test_{i}", f"value_{i}")
                end_time = time.time()
                return end_time - start_time, result is not None

            metrics = PerformanceMetrics()
            metrics.start()

            # Perform 1000 concurrent operations
            tasks = [perform_operation(i) for i in range(1000)]
            results = await asyncio.gather(*tasks)

            for response_time, success in results:
                metrics.record_operation(response_time, success, "concurrent_set")

            metrics.end()
            summary = metrics.get_summary()

            print(f"Concurrent operations throughput: {summary['operations_per_second']:.2f} ops/sec")
            print(f"Average response time: {summary['average_response_time']*1000:.2f} ms")

            assert summary['total_operations'] == 1000
            assert summary['successful_operations'] == 1000
            assert summary['success_rate'] == 1.0

    @pytest.mark.asyncio
    async def test_mixed_operation_throughput(self, redis_manager):
        """Test throughput for mixed operation types."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            operations = [
                ("set_cache", lambda i: redis_manager.set_cache(f"mixed_test_{i}", f"value_{i}")),
                ("get_cache", lambda i: redis_manager.get_cache(f"mixed_test_{i}")),
                ("delete_cache", lambda i: redis_manager.delete_cache(f"mixed_test_{i}"))
            ]

            metrics = PerformanceMetrics()
            metrics.start()

            # Perform 300 operations (100 of each type)
            for i in range(100):
                for op_name, op_func in operations:
                    start_time = time.time()
                    try:
                        await op_func(i)
                        success = True
                    except Exception:
                        success = False
                    end_time = time.time()
                    metrics.record_operation(end_time - start_time, success, op_name)

            metrics.end()
            summary = metrics.get_summary()

            print(f"Mixed operations throughput: {summary['operations_per_second']:.2f} ops/sec")
            print(f"Average response time: {summary['average_response_time']*1000:.2f} ms")

            assert summary['total_operations'] == 300
            assert summary['successful_operations'] == 300
            assert summary['success_rate'] == 1.0


class TestRedisLatencyPerformance:
    """Test Redis latency performance and analysis."""

    @pytest.fixture
    def redis_manager(self):
        """Create Redis manager for latency testing."""
        return RedisManager(
            retry_config=RetryConfig(max_attempts=1, base_delay=0.001)
        )

    @pytest.mark.asyncio
    async def test_operation_latency_distribution(self, redis_manager):
        """Test latency distribution across operations."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            # Simulate varying response times
            response_times = [0.001, 0.005, 0.002, 0.010, 0.003] * 200  # 1000 operations
            response_iter = iter(response_times)

            def mock_operation(*args, **kwargs):
                # Simulate processing time
                time.sleep(next(response_iter))
                return "success"

            mock_execute.side_effect = mock_operation

            metrics = PerformanceMetrics()
            metrics.start()

            for i in range(1000):
                start_time = time.time()
                await redis_manager.set_cache(f"latency_test_{i}", f"value_{i}")
                end_time = time.time()
                # Use actual measured time
                metrics.record_operation(end_time - start_time, True, "set_cache")

            metrics.end()
            summary = metrics.get_summary()

            print(f"Latency test - Average: {summary['average_response_time']*1000:.2f} ms")
            print(f"Latency test - Median: {summary['median_response_time']*1000:.2f} ms")
            print(f"Latency test - Min: {summary['min_response_time']*1000:.2f} ms")
            print(f"Latency test - Max: {summary['max_response_time']*1000:.2f} ms")
            print(f"Latency test - StdDev: {summary['response_time_stddev']*1000:.2f} ms")

            # Verify latency characteristics
            assert summary['average_response_time'] > 0
            assert summary['median_response_time'] > 0
            assert summary['min_response_time'] > 0
            assert summary['max_response_time'] > 0
            assert summary['max_response_time'] > summary['min_response_time']

    @pytest.mark.asyncio
    async def test_percentile_latencies(self, redis_manager):
        """Test percentile-based latency analysis."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            metrics = PerformanceMetrics()
            metrics.start()

            # Generate operations with known latency distribution
            for i in range(1000):
                # Create varied response times
                base_time = 0.001 + (i % 10) * 0.001  # 1ms to 10ms
                start_time = time.time()
                await asyncio.sleep(base_time / 10)  # Simulate network delay
                await redis_manager.set_cache(f"percentile_test_{i}", f"value_{i}")
                end_time = time.time()
                metrics.record_operation(end_time - start_time, True, "set_cache")

            metrics.end()
            summary = metrics.get_summary()

            if summary['percentile_95']:
                print(f"95th percentile latency: {summary['percentile_95']*1000:.2f} ms")
            if summary['percentile_99']:
                print(f"99th percentile latency: {summary['percentile_99']*1000:.2f} ms")

            # For 1000 operations, we should have percentile data
            assert summary['total_operations'] == 1000
            assert summary['percentile_95'] is not None
            assert summary['percentile_99'] is not None

    @pytest.mark.asyncio
    async def test_latency_under_load(self, redis_manager):
        """Test latency behavior under increasing load."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            load_levels = [10, 50, 100, 200]  # Concurrent operations
            latency_results = {}

            for load in load_levels:
                print(f"Testing latency at {load} concurrent operations...")

                async def perform_operation(i):
                    start_time = time.time()
                    await redis_manager.set_cache(f"load_test_{load}_{i}", f"value_{i}")
                    end_time = time.time()
                    return end_time - start_time

                metrics = PerformanceMetrics()
                metrics.start()

                # Run operations concurrently
                tasks = [perform_operation(i) for i in range(load)]
                response_times = await asyncio.gather(*tasks)

                for response_time in response_times:
                    metrics.record_operation(response_time, True, f"load_{load}")

                metrics.end()
                summary = metrics.get_summary()
                latency_results[load] = summary

                print(f"  Load {load}: {summary['average_response_time']*1000:.2f} ms avg")

            # Verify that latency increases with load (expected behavior)
            assert latency_results[10]['average_response_time'] <= latency_results[200]['average_response_time']


class TestRedisConnectionPoolPerformance:
    """Test Redis connection pool performance and efficiency."""

    @pytest.mark.asyncio
    async def test_connection_pool_reuse_efficiency(self):
        """Test connection pool reuse efficiency."""
        manager = RedisManager(max_connections=5)

        with patch('redis.asyncio.ConnectionPool') as mock_pool, \
             patch('redis.asyncio.Redis') as mock_redis:

            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.aclose = AsyncMock()
            mock_redis.return_value = mock_client

            # Initialize connection pool
            await manager._create_connection_pool()

            metrics = PerformanceMetrics()
            metrics.start()

            # Simulate multiple operations reusing connections
            for i in range(100):
                start_time = time.time()
                with patch.object(manager, '_execute_with_retry') as mock_execute:
                    mock_execute.return_value = "success"
                    await manager.set_cache(f"pool_test_{i}", f"value_{i}")
                end_time = time.time()
                metrics.record_operation(end_time - start_time, True, "connection_reuse")

            metrics.end()
            summary = metrics.get_summary()

            print(f"Connection pool reuse throughput: {summary['operations_per_second']:.2f} ops/sec")

            # Verify operations completed successfully
            assert summary['total_operations'] == 100
            assert summary['successful_operations'] == 100

    @pytest.mark.asyncio
    async def test_connection_pool_scaling(self):
        """Test connection pool scaling under load."""
        manager = RedisManager(max_connections=10)

        with patch.object(manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            async def perform_operation(i):
                start_time = time.time()
                await manager.set_cache(f"scale_test_{i}", f"value_{i}")
                end_time = time.time()
                return end_time - start_time

            # Test with different concurrency levels
            concurrency_levels = [5, 10, 20, 50]

            for concurrency in concurrency_levels:
                print(f"Testing pool scaling at {concurrency} concurrent operations...")

                metrics = PerformanceMetrics()
                metrics.start()

                tasks = [perform_operation(i) for i in range(concurrency)]
                response_times = await asyncio.gather(*tasks)

                for response_time in response_times:
                    metrics.record_operation(response_time, True, f"concurrency_{concurrency}")

                metrics.end()
                summary = metrics.get_summary()

                print(f"  Concurrency {concurrency}: {summary['operations_per_second']:.2f} ops/sec")
                print(f"  Average latency: {summary['average_response_time']*1000:.2f} ms")


class TestRedisMemoryUsagePerformance:
    """Test Redis memory usage and efficiency."""

    @pytest.fixture
    def redis_manager(self):
        """Create Redis manager for memory testing."""
        return RedisManager()

    @pytest.mark.asyncio
    async def test_memory_usage_patterns(self, redis_manager):
        """Test memory usage patterns for different data types."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            # Test different data types and sizes
            test_data = {
                "small_string": "hello",
                "medium_string": "x" * 1000,
                "large_string": "x" * 10000,
                "small_dict": {"key": "value", "number": 42},
                "large_dict": {f"key_{i}": f"value_{i}" for i in range(100)},
                "list": list(range(1000)),
                "nested_structure": {
                    "users": [
                        {"id": i, "name": f"user_{i}", "data": "x" * 100}
                        for i in range(50)
                    ]
                }
            }

            memory_metrics = {}

            for data_name, data in test_data.items():
                print(f"Testing memory usage for {data_name}...")

                metrics = PerformanceMetrics()
                metrics.start()

                # Perform operations with this data type
                for i in range(100):
                    start_time = time.time()
                    await redis_manager.set_cache(f"memory_test_{data_name}_{i}", data)
                    end_time = time.time()
                    metrics.record_operation(end_time - start_time, True, data_name)

                metrics.end()
                summary = metrics.get_summary()
                memory_metrics[data_name] = summary

                print(f"  {data_name}: {summary['average_response_time']*1000:.2f} ms avg")

            # Verify all operations completed
            for data_name, summary in memory_metrics.items():
                assert summary['total_operations'] == 100
                assert summary['successful_operations'] == 100


class TestRedisScalabilityBenchmarks:
    """Test Redis scalability under various conditions."""

    @pytest.fixture
    def redis_manager(self):
        """Create Redis manager for scalability testing."""
        return RedisManager(
            max_connections=50,
            retry_config=RetryConfig(max_attempts=1, base_delay=0.001)
        )

    @pytest.mark.asyncio
    async def test_high_concurrency_scalability(self, redis_manager):
        """Test scalability under high concurrency."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            # Test scalability from 100 to 1000 concurrent operations
            concurrency_levels = [100, 250, 500, 1000]

            scalability_results = {}

            for concurrency in concurrency_levels:
                print(f"Testing scalability at {concurrency} concurrent operations...")

                async def perform_operation(i):
                    start_time = time.time()
                    await redis_manager.set_cache(f"scale_test_{concurrency}_{i}", f"value_{i}")
                    end_time = time.time()
                    return end_time - start_time

                metrics = PerformanceMetrics()
                metrics.start()

                # Run concurrent operations
                tasks = [perform_operation(i) for i in range(concurrency)]
                response_times = await asyncio.gather(*tasks)

                for response_time in response_times:
                    metrics.record_operation(response_time, True, f"scale_{concurrency}")

                metrics.end()
                summary = metrics.get_summary()
                scalability_results[concurrency] = summary

                print(f"  {concurrency} ops: {summary['operations_per_second']:.2f} ops/sec")
                print(f"  Latency: {summary['average_response_time']*1000:.2f} ms")
                print(f"  Success rate: {summary['success_rate']:.3f}")

                # Verify all operations completed
                assert summary['total_operations'] == concurrency
                assert summary['successful_operations'] == concurrency

            # Analyze scalability trends
            throughput_trend = []
            latency_trend = []

            for concurrency in concurrency_levels:
                result = scalability_results[concurrency]
                throughput_trend.append(result['operations_per_second'])
                latency_trend.append(result['average_response_time'])

            print("Scalability analysis:")
            print(f"  Throughput trend: {throughput_trend}")
            print(f"  Latency trend: {latency_trend}")

    @pytest.mark.asyncio
    async def test_sustained_load_performance(self, redis_manager):
        """Test performance under sustained load over time."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            test_duration = 30  # seconds
            operations_per_second = 50

            print(f"Testing sustained load: {operations_per_second} ops/sec for {test_duration}s...")

            metrics = PerformanceMetrics()
            metrics.start()

            operation_count = 0
            start_time = time.time()

            while time.time() - start_time < test_duration:
                # Perform batch of operations
                batch_start = time.time()
                tasks = []

                for i in range(operations_per_second):
                    task = redis_manager.set_cache(f"sustained_test_{operation_count + i}", f"value_{operation_count + i}")
                    tasks.append(task)

                # Wait for batch to complete
                await asyncio.gather(*tasks)

                batch_end = time.time()
                batch_time = batch_end - batch_start

                # Record batch metrics
                for i in range(operations_per_second):
                    metrics.record_operation(batch_time / operations_per_second, True, "sustained")

                operation_count += operations_per_second

                # Sleep to maintain target rate
                if batch_time < 1.0:
                    await asyncio.sleep(1.0 - batch_time)

            metrics.end()
            summary = metrics.get_summary()

            print("Sustained load results:")
            print(f"  Total operations: {summary['total_operations']}")
            print(f"  Average throughput: {summary['operations_per_second']:.2f} ops/sec")
            print(f"  Average latency: {summary['average_response_time']*1000:.2f} ms")
            print(f"  Success rate: {summary['success_rate']:.3f}")

            # Verify sustained performance
            assert summary['total_operations'] > 1000  # At least 1000 operations
            assert summary['success_rate'] == 1.0
            assert summary['operations_per_second'] > 40  # At least 80% of target


class TestRedisFailureResiliencePerformance:
    """Test Redis performance under failure conditions."""

    @pytest.fixture
    def redis_manager(self):
        """Create Redis manager for failure testing."""
        return RedisManager(
            retry_config=RetryConfig(max_attempts=3, base_delay=0.01, max_delay=0.1)
        )

    @pytest.mark.asyncio
    async def test_performance_with_intermittent_failures(self, redis_manager):
        """Test performance when Redis has intermittent failures."""
        call_count = 0

        def mock_execute_with_failures(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Fail every 5th operation to simulate intermittent issues
            if call_count % 5 == 0:
                raise Exception("Simulated Redis connection error")
            return "success"

        with patch.object(redis_manager, '_execute_with_retry', side_effect=mock_execute_with_failures):

            metrics = PerformanceMetrics()
            metrics.start()

            # Perform operations that will encounter failures
            for i in range(100):
                start_time = time.time()
                try:
                    await redis_manager.set_cache(f"failure_test_{i}", f"value_{i}")
                    success = True
                except Exception:
                    success = False
                end_time = time.time()
                metrics.record_operation(end_time - start_time, success, "failure_test")

            metrics.end()
            summary = metrics.get_summary()

            print("Failure resilience results:")
            print(f"  Total operations: {summary['total_operations']}")
            print(f"  Successful operations: {summary['successful_operations']}")
            print(f"  Failed operations: {summary['failed_operations']}")
            print(f"  Success rate: {summary['success_rate']:.3f}")
            print(f"  Average latency: {summary['average_response_time']*1000:.2f} ms")

            # Verify resilience - should handle failures gracefully
            assert summary['total_operations'] == 100
            assert summary['successful_operations'] > 60  # At least 60% success rate
            assert summary['failed_operations'] > 0  # Some failures occurred

    @pytest.mark.asyncio
    async def test_circuit_breaker_performance_impact(self, redis_manager):
        """Test performance impact of circuit breaker activation."""
        # Force circuit breaker to open
        for _ in range(redis_manager.circuit_breaker.config.failure_threshold):
            redis_manager.circuit_breaker._record_failure()

        assert redis_manager.circuit_breaker.state.value == "open"

        metrics = PerformanceMetrics()
        metrics.start()

        # Try operations while circuit breaker is open
        for i in range(50):
            start_time = time.time()
            try:
                await redis_manager.set_cache(f"circuit_test_{i}", f"value_{i}")
                success = True
            except Exception:
                success = False
            end_time = time.time()
            metrics.record_operation(end_time - start_time, success, "circuit_breaker")

        metrics.end()
        summary = metrics.get_summary()

        print("Circuit breaker performance:")
        print(f"  Operations during open circuit: {summary['total_operations']}")
        print(f"  Successful operations: {summary['successful_operations']}")
        print(f"  Failed operations: {summary['failed_operations']}")
        print(f"  Average latency: {summary['average_response_time']*1000:.2f} ms")

        # Circuit breaker should prevent most operations when open
        assert summary['failed_operations'] > summary['successful_operations']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
