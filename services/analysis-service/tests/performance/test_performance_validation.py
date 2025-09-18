"""Performance Tests - Validate system performance and scalability."""

import pytest
import asyncio
import time
import statistics
from unittest.mock import Mock, AsyncMock, patch
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Tuple
import psutil
import os

from ...main import app
from ...presentation.models.analysis import (
    SemanticSimilarityRequest, SemanticSimilarityResponse
)
from ..fixtures.test_data import TestDataFactory
from ..fixtures.test_utilities import PerformanceMonitor, AsyncMockHelper


class TestPerformanceValidation:
    """Test system performance and scalability."""

    @pytest.fixture
    def performance_monitor(self):
        """Create performance monitor fixture."""
        return PerformanceMonitor()

    @pytest.fixture
    def large_document_set(self):
        """Create large set of documents for performance testing."""
        return TestDataFactory.create_sample_documents(50)

    @pytest.fixture
    def concurrent_users_config(self):
        """Configuration for concurrent user testing."""
        return {
            'user_count': 20,
            'requests_per_user': 5,
            'max_concurrent': 10,
            'timeout_seconds': 30
        }

    def test_single_semantic_similarity_performance(self):
        """Test performance of single semantic similarity analysis."""
        monitor = PerformanceMonitor()

        # Create test request
        request = SemanticSimilarityRequest(
            targets=['doc-1', 'doc-2', 'doc-3'],
            threshold=0.8,
            embedding_model='sentence-transformers/all-MiniLM-L6-v2',
            options={'batch_size': 32}
        )

        # Mock the handler
        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_handler:
            mock_response = SemanticSimilarityResponse(
                analysis_id='perf-test-001',
                analysis_type='semantic_similarity',
                targets=request.targets,
                status='completed',
                execution_time_seconds=1.2,
                similarity_matrix=[[1.0, 0.85, 0.65], [0.85, 1.0, 0.72], [0.65, 0.72, 1.0]]
            )
            mock_handler.return_value = mock_response

            # Measure performance
            monitor.start()
            # Simulate API call processing
            time.sleep(0.1)  # Simulate network/API overhead
            elapsed = monitor.stop()

            # Validate performance
            assert elapsed < 2.0, f"Single analysis too slow: {elapsed:.2f}s"
            assert mock_handler.call_count == 1

    def test_concurrent_semantic_similarity_performance(self):
        """Test performance under concurrent semantic similarity requests."""
        monitor = PerformanceMonitor()

        async def make_concurrent_request(request_id: int):
            """Make a single concurrent request."""
            request = SemanticSimilarityRequest(
                targets=[f'doc-{request_id}-1', f'doc-{request_id}-2'],
                threshold=0.8
            )

            with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_handler:
                mock_response = SemanticSimilarityResponse(
                    analysis_id=f'concurrent-{request_id}',
                    analysis_type='semantic_similarity',
                    targets=request.targets,
                    status='completed',
                    execution_time_seconds=1.0
                )
                mock_handler.return_value = mock_response

                # Simulate request processing
                await asyncio.sleep(0.05)  # Simulate processing time
                return request_id, mock_handler.call_count

        # Execute concurrent requests
        monitor.start()

        async def run_concurrent_test():
            tasks = [make_concurrent_request(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            return results

        # Run the test
        results = asyncio.run(run_concurrent_test())
        total_time = monitor.stop()

        # Validate results
        assert len(results) == 10, "Not all concurrent requests completed"
        assert total_time < 5.0, f"Concurrent requests too slow: {total_time:.2f}s"

        # Verify all requests were processed
        successful_requests = sum(1 for _, call_count in results if call_count == 1)
        assert successful_requests == 10, f"Only {successful_requests}/10 requests succeeded"

    def test_memory_usage_under_load(self):
        """Test memory usage during high load scenarios."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        async def simulate_load():
            """Simulate high load scenario."""
            tasks = []

            for i in range(50):  # Simulate 50 concurrent operations
                task = asyncio.create_task(self._simulate_memory_intensive_operation(i))
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            return results

        # Run load simulation
        results = asyncio.run(simulate_load())

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Validate memory usage
        assert memory_increase < 100, f"Memory usage too high: +{memory_increase:.1f}MB"
        assert len(results) == 50, "Not all operations completed"

    async def _simulate_memory_intensive_operation(self, operation_id: int):
        """Simulate memory-intensive operation."""
        # Create some data structures to simulate memory usage
        data = [f"data-{operation_id}-{i}" * 100 for i in range(100)]

        # Simulate processing time
        await asyncio.sleep(0.01)

        return len(data)

    def test_database_connection_pooling_performance(self):
        """Test database connection pooling under load."""
        monitor = PerformanceMonitor()

        async def simulate_db_operations():
            """Simulate multiple database operations."""
            tasks = []

            for i in range(20):
                task = asyncio.create_task(self._simulate_db_operation(i))
                tasks.append(task)

            start_time = time.time()
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time

            return results, total_time

        # Run database simulation
        results, total_time = asyncio.run(simulate_db_operations())

        # Validate performance
        assert total_time < 10.0, f"Database operations too slow: {total_time:.2f}s"
        assert len(results) == 20, "Not all database operations completed"

        # Check individual operation times
        operation_times = [result for result, _ in results]
        avg_time = statistics.mean(operation_times)
        max_time = max(operation_times)

        assert avg_time < 0.5, f"Average DB operation too slow: {avg_time:.2f}s"
        assert max_time < 2.0, f"Max DB operation too slow: {max_time:.2f}s"

    async def _simulate_db_operation(self, operation_id: int):
        """Simulate database operation."""
        start_time = time.time()

        # Simulate database query time
        await asyncio.sleep(0.05 + (operation_id % 10) * 0.01)

        # Simulate result processing
        result = f"result-{operation_id}"
        processing_time = len(result) * 0.001
        await asyncio.sleep(processing_time)

        total_time = time.time() - start_time
        return total_time, result

    def test_cache_performance_under_load(self):
        """Test caching performance under load."""
        monitor = PerformanceMonitor()

        async def simulate_cache_operations():
            """Simulate cache operations under load."""
            cache_hits = []
            cache_misses = []

            for i in range(100):
                if i % 3 == 0:  # 33% cache misses
                    cache_misses.append(await self._simulate_cache_miss(i))
                else:  # 67% cache hits
                    cache_hits.append(await self._simulate_cache_hit(i))

            return cache_hits, cache_misses

        # Run cache simulation
        monitor.start()
        cache_hits, cache_misses = asyncio.run(simulate_cache_operations())
        total_time = monitor.stop()

        # Validate performance
        assert total_time < 5.0, f"Cache operations too slow: {total_time:.2f}s"

        # Calculate cache hit ratio
        total_operations = len(cache_hits) + len(cache_misses)
        hit_ratio = len(cache_hits) / total_operations if total_operations > 0 else 0

        assert hit_ratio > 0.6, f"Cache hit ratio too low: {hit_ratio:.2f}"

        # Check average response times
        if cache_hits:
            avg_hit_time = statistics.mean(cache_hits)
            assert avg_hit_time < 0.01, f"Average cache hit too slow: {avg_hit_time:.3f}s"

        if cache_misses:
            avg_miss_time = statistics.mean(cache_misses)
            assert avg_miss_time < 0.1, f"Average cache miss too slow: {avg_miss_time:.3f}s"

    async def _simulate_cache_hit(self, operation_id: int) -> float:
        """Simulate cache hit."""
        start_time = time.time()
        await asyncio.sleep(0.005)  # Fast cache hit
        return time.time() - start_time

    async def _simulate_cache_miss(self, operation_id: int) -> float:
        """Simulate cache miss."""
        start_time = time.time()
        await asyncio.sleep(0.05)  # Slower cache miss (includes computation)
        return time.time() - start_time

    def test_api_response_time_distribution(self):
        """Test API response time distribution under various loads."""
        monitor = PerformanceMonitor()

        response_times = []

        # Simulate different load scenarios
        load_scenarios = [
            {'concurrent_requests': 1, 'expected_max_time': 0.5},
            {'concurrent_requests': 5, 'expected_max_time': 1.0},
            {'concurrent_requests': 10, 'expected_max_time': 2.0}
        ]

        for scenario in load_scenarios:
            scenario_times = []

            async def run_scenario():
                tasks = []
                for i in range(scenario['concurrent_requests']):
                    task = asyncio.create_task(self._simulate_api_request(i))
                    tasks.append(task)

                start_time = time.time()
                results = await asyncio.gather(*tasks)
                total_time = time.time() - start_time

                return [result for result, _ in results], total_time

            # Run scenario
            monitor.start()
            times, total_time = asyncio.run(run_scenario())
            monitor.stop()

            scenario_times.extend(times)
            response_times.extend(times)

            # Validate scenario performance
            max_time = max(times) if times else 0
            assert max_time < scenario['expected_max_time'], \
                f"Scenario {scenario['concurrent_requests']} req failed: max {max_time:.2f}s > {scenario['expected_max_time']}s"

            # Check for outliers (responses taking > 2x median)
            if len(times) > 1:
                median_time = statistics.median(times)
                outliers = [t for t in times if t > median_time * 2]
                assert len(outliers) / len(times) < 0.1, \
                    f"Too many outliers in scenario {scenario['concurrent_requests']}: {len(outliers)}/{len(times)}"

        # Overall validation
        if response_times:
            avg_time = statistics.mean(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

            assert avg_time < 0.5, f"Average response time too slow: {avg_time:.2f}s"
            assert p95_time < 2.0, f"95th percentile too slow: {p95_time:.2f}s"

    async def _simulate_api_request(self, request_id: int) -> Tuple[float, str]:
        """Simulate API request with variable processing time."""
        start_time = time.time()

        # Simulate variable processing time based on request complexity
        base_time = 0.1
        complexity_factor = (request_id % 5 + 1) * 0.05  # 0.05 to 0.25
        processing_time = base_time + complexity_factor

        await asyncio.sleep(processing_time)

        total_time = time.time() - start_time
        return total_time, f"response-{request_id}"

    def test_resource_utilization_scaling(self):
        """Test how resource utilization scales with load."""
        monitor = PerformanceMonitor()

        # Test different load levels
        load_levels = [10, 25, 50, 100]

        scaling_results = {}

        for load_level in load_levels:
            monitor.start()

            async def run_load_level():
                tasks = []
                for i in range(load_level):
                    task = asyncio.create_task(self._simulate_load_operation(i))
                    tasks.append(task)

                start_time = time.time()
                results = await asyncio.gather(*tasks)
                total_time = time.time() - start_time

                return results, total_time

            results, total_time = asyncio.run(run_load_level())
            monitor.stop()

            # Measure resource usage
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            cpu_percent = psutil.cpu_percent(interval=0.1)

            scaling_results[load_level] = {
                'total_time': total_time,
                'avg_time_per_operation': total_time / load_level if load_level > 0 else 0,
                'memory_usage_mb': memory_usage,
                'cpu_percent': cpu_percent,
                'operations_completed': len(results)
            }

        # Validate scaling behavior
        for load_level, results in scaling_results.items():
            # Each operation should complete within reasonable time
            assert results['avg_time_per_operation'] < 1.0, \
                f"Load {load_level}: avg operation time too slow: {results['avg_time_per_operation']:.2f}s"

            # Memory usage should be reasonable
            assert results['memory_usage_mb'] < 500, \
                f"Load {load_level}: memory usage too high: {results['memory_usage_mb']:.1f}MB"

            # All operations should complete
            assert results['operations_completed'] == load_level, \
                f"Load {load_level}: only {results['operations_completed']}/{load_level} operations completed"

        # Check scaling efficiency (should not degrade linearly)
        if len(scaling_results) >= 2:
            low_load = scaling_results[load_levels[0]]
            high_load = scaling_results[load_levels[-1]]

            efficiency_ratio = high_load['avg_time_per_operation'] / low_load['avg_time_per_operation']

            # Efficiency ratio should be less than 2 (allowing for some overhead)
            assert efficiency_ratio < 2.0, \
                f"Poor scaling efficiency: {efficiency_ratio:.2f}x slower at high load"

    async def _simulate_load_operation(self, operation_id: int) -> str:
        """Simulate load operation with variable complexity."""
        # Simulate I/O bound operation
        await asyncio.sleep(0.02 + (operation_id % 10) * 0.01)

        # Simulate some CPU work
        result = sum(i * i for i in range(operation_id % 100 + 1))

        return f"operation-{operation_id}-result-{result}"

    def test_error_rate_under_load(self):
        """Test error rates under various load conditions."""
        monitor = PerformanceMonitor()

        # Test different error injection rates
        error_rates = [0.0, 0.05, 0.10, 0.20]  # 0%, 5%, 10%, 20%

        error_results = {}

        for target_error_rate in error_rates:
            monitor.start()

            async def run_with_errors():
                tasks = []
                for i in range(100):  # 100 operations
                    should_error = (i % (1 / target_error_rate)) < 1 if target_error_rate > 0 else False
                    task = asyncio.create_task(self._simulate_operation_with_error(i, should_error))
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                successful = sum(1 for r in results if not isinstance(r, Exception))
                failed = sum(1 for r in results if isinstance(r, Exception))
                actual_error_rate = failed / len(results) if results else 0

                return successful, failed, actual_error_rate

            successful, failed, actual_error_rate = asyncio.run(run_with_errors())
            total_time = monitor.stop()

            error_results[target_error_rate] = {
                'successful': successful,
                'failed': failed,
                'actual_error_rate': actual_error_rate,
                'total_time': total_time,
                'avg_time_per_operation': total_time / 100 if successful + failed > 0 else 0
            }

            # Validate error rate is within acceptable range
            error_tolerance = 0.02  # 2% tolerance
            assert abs(actual_error_rate - target_error_rate) < error_tolerance, \
                f"Error rate mismatch for target {target_error_rate}: actual {actual_error_rate}"

        # Check that error handling doesn't significantly impact performance
        no_error_time = error_results[0.0]['avg_time_per_operation']
        for error_rate, results in error_results.items():
            if error_rate > 0:
                slowdown_ratio = results['avg_time_per_operation'] / no_error_time
                # Error handling should not slow down operations by more than 50%
                assert slowdown_ratio < 1.5, \
                    f"Error handling too slow at {error_rate} error rate: {slowdown_ratio:.2f}x slower"

    async def _simulate_operation_with_error(self, operation_id: int, should_error: bool) -> str:
        """Simulate operation that may raise an error."""
        await asyncio.sleep(0.01)  # Base processing time

        if should_error:
            raise Exception(f"Simulated error in operation {operation_id}")

        return f"success-{operation_id}"

    def test_throughput_stability(self):
        """Test throughput stability over extended period."""
        monitor = PerformanceMonitor()

        # Test throughput over 30 second window
        test_duration = 30
        measurement_interval = 5

        throughput_measurements = []

        async def continuous_operations():
            """Run continuous operations for the test duration."""
            start_time = time.time()
            operations_completed = 0

            while time.time() - start_time < test_duration:
                # Run batch of operations
                batch_start = time.time()
                tasks = [self._simulate_quick_operation(i) for i in range(10)]
                await asyncio.gather(*tasks)
                batch_time = time.time() - batch_start

                operations_completed += 10

                # Record throughput every measurement interval
                if operations_completed % 50 == 0:  # Every 5 batches
                    throughput = 50 / (time.time() - start_time) * measurement_interval
                    throughput_measurements.append(throughput)

            return operations_completed

        # Run continuous test
        monitor.start()
        total_operations = asyncio.run(continuous_operations())
        total_time = monitor.stop()

        # Validate throughput stability
        if throughput_measurements:
            avg_throughput = statistics.mean(throughput_measurements)
            throughput_stddev = statistics.stdev(throughput_measurements) if len(throughput_measurements) > 1 else 0
            throughput_variation = throughput_stddev / avg_throughput if avg_throughput > 0 else 0

            # Throughput variation should be less than 20%
            assert throughput_variation < 0.2, \
                f"Throughput too unstable: {throughput_variation:.2f} variation"

            # Average throughput should be reasonable
            assert avg_throughput > 5, \
                f"Throughput too low: {avg_throughput:.1f} ops/5sec"

        # Validate total operations completed
        expected_min_operations = 100  # At least 100 operations in 30 seconds
        assert total_operations >= expected_min_operations, \
            f"Too few operations completed: {total_operations} < {expected_min_operations}"

    async def _simulate_quick_operation(self, operation_id: int) -> str:
        """Simulate quick operation for throughput testing."""
        await asyncio.sleep(0.005)  # 5ms operation
        return f"quick-op-{operation_id}"

    def test_memory_leak_detection(self):
        """Test for memory leaks during extended operation."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        async def extended_operation():
            """Run extended operation to check for memory leaks."""
            data_structures = []

            for i in range(1000):
                # Create some data structures
                data = [f"memory-test-{i}-{j}" for j in range(100)]
                data_structures.append(data)

                # Process data
                processed = [item.upper() for item in data]
                data_structures[-1] = processed

                # Periodic cleanup (simulate garbage collection)
                if i % 100 == 0:
                    # Remove some old data
                    if len(data_structures) > 50:
                        data_structures = data_structures[-50:]

                await asyncio.sleep(0.001)  # Small delay

            return len(data_structures)

        # Run extended operation
        result = asyncio.run(extended_operation())

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Validate memory usage
        assert result > 0, "Extended operation did not complete properly"

        # Memory increase should be reasonable (less than 50MB for this test)
        assert memory_increase < 50, f"Potential memory leak: +{memory_increase:.1f}MB"

        # Force garbage collection check
        import gc
        gc.collect()

        post_gc_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_after_gc = post_gc_memory - initial_memory

        # After GC, memory should be closer to initial
        assert memory_after_gc < memory_increase, "Memory not properly cleaned up after GC"

    def test_cpu_utilization_under_load(self):
        """Test CPU utilization patterns under load."""
        monitor = PerformanceMonitor()

        # Test different CPU-intensive scenarios
        scenarios = [
            {'name': 'light_cpu', 'intensity': 10, 'expected_max_cpu': 30},
            {'name': 'medium_cpu', 'intensity': 50, 'expected_max_cpu': 60},
            {'name': 'heavy_cpu', 'intensity': 100, 'expected_max_cpu': 90}
        ]

        cpu_results = {}

        for scenario in scenarios:
            monitor.start()

            async def run_cpu_scenario():
                """Run CPU-intensive operations."""
                tasks = []

                def cpu_work(intensity):
                    """CPU-intensive work."""
                    result = 0
                    for i in range(intensity * 1000):
                        result += i ** 2
                    return result

                # Run CPU work in thread pool to avoid blocking event loop
                with ThreadPoolExecutor(max_workers=4) as executor:
                    loop = asyncio.get_event_loop()
                    cpu_tasks = [
                        loop.run_in_executor(executor, cpu_work, scenario['intensity'])
                        for _ in range(4)
                    ]
                    results = await asyncio.gather(*cpu_tasks)

                return results

            # Run scenario and monitor CPU
            results = asyncio.run(run_cpu_scenario())

            # Measure CPU usage during operation
            cpu_percent = psutil.cpu_percent(interval=1.0)

            monitor.stop()

            cpu_results[scenario['name']] = {
                'cpu_percent': cpu_percent,
                'expected_max': scenario['expected_max_cpu'],
                'results_computed': len(results),
                'status': 'pass' if cpu_percent <= scenario['expected_max_cpu'] else 'fail'
            }

            # Validate CPU usage
            assert cpu_percent <= scenario['expected_max_cpu'], \
                f"CPU usage too high for {scenario['name']}: {cpu_percent}% > {scenario['expected_max_cpu']}%"

        # Verify CPU utilization scales appropriately
        light_cpu = cpu_results['light_cpu']['cpu_percent']
        heavy_cpu = cpu_results['heavy_cpu']['cpu_percent']

        # Heavy CPU should use more CPU than light (allowing for system variance)
        assert heavy_cpu > light_cpu * 0.8, \
            f"CPU scaling not working: heavy {heavy_cpu}% vs light {light_cpu}%"

    def test_network_simulation_performance(self):
        """Test performance with simulated network conditions."""
        monitor = PerformanceMonitor()

        # Simulate different network conditions
        network_conditions = [
            {'name': 'fast_network', 'latency': 0.01, 'jitter': 0.005, 'packet_loss': 0.0},
            {'name': 'slow_network', 'latency': 0.1, 'jitter': 0.02, 'packet_loss': 0.02},
            {'name': 'unstable_network', 'latency': 0.05, 'jitter': 0.1, 'packet_loss': 0.1}
        ]

        network_results = {}

        for condition in network_conditions:
            monitor.start()

            async def simulate_network_operations():
                """Simulate operations under network conditions."""
                successful_operations = 0
                failed_operations = 0

                for i in range(50):
                    try:
                        await self._simulate_network_request(
                            i, condition['latency'], condition['jitter'], condition['packet_loss']
                        )
                        successful_operations += 1
                    except Exception:
                        failed_operations += 1

                return successful_operations, failed_operations

            successful, failed = asyncio.run(simulate_network_operations())
            total_time = monitor.stop()

            success_rate = successful / (successful + failed) if (successful + failed) > 0 else 0

            network_results[condition['name']] = {
                'successful': successful,
                'failed': failed,
                'success_rate': success_rate,
                'total_time': total_time,
                'avg_time_per_operation': total_time / (successful + failed) if (successful + failed) > 0 else 0
            }

            # Validate performance under network conditions
            expected_success_rate = 1.0 - condition['packet_loss'] - 0.05  # Allow some tolerance
            assert success_rate >= expected_success_rate, \
                f"Success rate too low for {condition['name']}: {success_rate:.2f} < {expected_success_rate:.2f}"

        # Fast network should be fastest
        fast_time = network_results['fast_network']['avg_time_per_operation']
        slow_time = network_results['slow_network']['avg_time_per_operation']

        assert fast_time < slow_time * 0.5, \
            f"Fast network not faster: {fast_time:.3f}s vs {slow_time:.3f}s"

    async def _simulate_network_request(self, request_id: int, latency: float, jitter: float, packet_loss: float):
        """Simulate network request with specified conditions."""
        import random

        # Simulate packet loss
        if random.random() < packet_loss:
            raise Exception(f"Simulated packet loss for request {request_id}")

        # Simulate latency with jitter
        actual_latency = latency + random.uniform(-jitter, jitter)
        actual_latency = max(0.001, actual_latency)  # Minimum 1ms

        await asyncio.sleep(actual_latency)

        return f"network-response-{request_id}"
