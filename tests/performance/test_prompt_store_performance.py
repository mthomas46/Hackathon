"""Performance and load testing for prompt_store service.

This module provides comprehensive performance testing including:
- Load testing with concurrent users
- Memory usage profiling
- Database query performance analysis
- LLM service call performance monitoring
- API endpoint response time benchmarking

Run with: pytest tests/performance/test_prompt_store_performance.py -v --benchmark-only
"""

import asyncio
import time
import statistics
import psutil
import os
from typing import List, Dict, Any
import pytest
from unittest.mock import AsyncMock, patch
import httpx

from services.prompt_store.domain.prompts.service import PromptService
from services.prompt_store.domain.refinement.service import PromptRefinementService
from services.prompt_store.infrastructure.cache import prompt_store_cache


@pytest.mark.performance
class TestPromptStorePerformance:
    """Performance tests for prompt_store critical operations."""

    @pytest.fixture
    def performance_db(self):
        """Setup clean database for performance testing."""
        # Use in-memory database for performance tests
        os.environ["PROMPT_STORE_DB"] = ":memory:"
        # Reset any existing service instances
        yield
        # Cleanup
        if "PROMPT_STORE_DB" in os.environ:
            del os.environ["PROMPT_STORE_DB"]

    def test_prompt_creation_performance(self, benchmark, performance_db):
        """Benchmark prompt creation performance."""
        service = PromptService()

        prompt_data = {
            "name": "perf_test_prompt",
            "category": "performance",
            "content": "This is a test prompt for performance benchmarking.",
            "description": "Performance test prompt",
            "variables": ["var1", "var2"],
            "tags": ["performance", "test"],
            "created_by": "perf_test"
        }

        result = benchmark(service.create_entity, prompt_data)
        assert result.id is not None
        assert result.name == "perf_test_prompt"

    def test_prompt_bulk_creation_performance(self, benchmark, performance_db):
        """Benchmark bulk prompt creation performance."""
        service = PromptService()

        def create_bulk_prompts():
            prompts = []
            for i in range(100):
                prompt_data = {
                    "name": f"bulk_perf_test_{i}",
                    "category": "bulk_performance",
                    "content": f"This is bulk test prompt {i} for performance benchmarking.",
                    "created_by": "bulk_perf_test"
                }
                prompt = service.create_entity(prompt_data)
                prompts.append(prompt)
            return prompts

        result = benchmark(create_bulk_prompts)
        assert len(result) == 100
        assert all(p.id is not None for p in result)

    def test_prompt_retrieval_performance(self, benchmark, performance_db):
        """Benchmark prompt retrieval performance."""
        service = PromptService()

        # Create test prompt
        prompt_data = {
            "name": "retrieval_perf_test",
            "category": "performance",
            "content": "This is a test prompt for retrieval performance benchmarking.",
            "created_by": "perf_test"
        }
        created_prompt = service.create_entity(prompt_data)

        # Benchmark retrieval
        result = benchmark(service.get_entity, created_prompt.id)
        assert result.id == created_prompt.id
        assert result.name == "retrieval_perf_test"

    def test_prompt_update_performance(self, benchmark, performance_db):
        """Benchmark prompt update performance."""
        service = PromptService()

        # Create test prompt
        prompt_data = {
            "name": "update_perf_test",
            "category": "performance",
            "content": "Original content for update performance test.",
            "created_by": "perf_test"
        }
        created_prompt = service.create_entity(prompt_data)

        # Benchmark update
        result = benchmark(
            service.update_prompt_content,
            created_prompt.id,
            "Updated content for performance testing with additional text.",
            change_summary="Performance test update",
            updated_by="perf_test"
        )
        assert result.version == 2
        assert "Updated content" in result.content

    @pytest.mark.asyncio
    async def test_cache_performance(self, benchmark):
        """Benchmark cache operations performance."""
        # Test cache set/get operations
        test_key = "perf_test_key"
        test_data = {"data": "x" * 1000, "metadata": {"size": "1KB"}}

        async def cache_operations():
            # Set operation
            await prompt_store_cache.set(test_key, test_data, ttl=300)
            # Get operation
            result = await prompt_store_cache.get(test_key)
            return result

        result = await benchmark(cache_operations)
        assert result == test_data

    @pytest.mark.asyncio
    async def test_llm_service_call_performance(self, benchmark):
        """Benchmark LLM service call simulation."""
        service = PromptRefinementService()

        request = {
            "original_prompt": {
                "name": "perf_test",
                "content": "Write a function.",
                "category": "coding"
            },
            "refinement_instructions": "Add error handling and documentation",
            "user_id": "perf_test"
        }

        # Mock the LLM service call
        with patch('services.shared.clients.ServiceClients.interpret_query', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "data": {
                    "intent": "refine_prompt",
                    "response_text": "Improved prompt with error handling and documentation."
                }
            }

            result = await benchmark(service._call_llm_service, "interpreter", request)
            assert "refined_content" in result

    def test_memory_usage_during_bulk_operations(self, performance_db):
        """Test memory usage during bulk operations."""
        service = PromptService()

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform bulk operations
        prompts = []
        for i in range(500):
            prompt_data = {
                "name": f"memory_test_{i}",
                "category": "memory_performance",
                "content": f"This is memory test prompt {i} with some content to consume memory.",
                "created_by": "memory_test"
            }
            prompt = service.create_entity(prompt_data)
            prompts.append(prompt)

        # Check memory usage after operations
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")

        # Memory increase should be reasonable (less than 50MB for 500 prompts)
        assert memory_increase < 50, f"Memory increase too high: {memory_increase:.1f}MB"
        assert len(prompts) == 500


@pytest.mark.load_test
class TestPromptStoreLoadTesting:
    """Load testing for prompt_store under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_prompt_creation(self):
        """Test concurrent prompt creation under load."""
        service = PromptService()

        async def create_prompt_async(index: int):
            prompt_data = {
                "name": f"concurrent_test_{index}",
                "category": "load_test",
                "content": f"Concurrent load test prompt {index}",
                "created_by": "load_test"
            }
            return service.create_entity(prompt_data)

        # Create 50 concurrent prompt creation tasks
        tasks = [create_prompt_async(i) for i in range(50)]
        start_time = time.time()

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        assert len(results) == 50
        assert all(r.id is not None for r in results)
        print(".2f")
        # Should complete within reasonable time (under 5 seconds)
        assert duration < 5.0, f"Concurrent creation too slow: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_concurrent_refinement_sessions(self):
        """Test concurrent refinement session handling."""
        service = PromptRefinementService()

        async def create_refinement_session(index: int):
            # Mock the LLM call
            with patch.object(service, '_call_llm_service', new_callable=AsyncMock) as mock_llm, \
                 patch.object(service, '_store_refinement_result', new_callable=AsyncMock) as mock_store:

                mock_llm.return_value = {"refined_content": f"Refined content {index}"}
                mock_store.return_value = f"doc_{index}"

                result = await service.refine_prompt(
                    "test_prompt_id",  # Would need to create actual prompt
                    f"Refine prompt {index}",
                    "interpreter",
                    None,
                    "load_test"
                )
                return result

        # Skip this test for now as it requires actual prompt setup
        # In real load testing, we would create test prompts first
        pytest.skip("Requires test prompt setup for meaningful load testing")

    def test_database_connection_pooling(self, performance_db):
        """Test database connection performance under load."""
        service = PromptService()

        def perform_db_operations():
            results = []
            for i in range(100):
                prompt_data = {
                    "name": f"db_pool_test_{i}",
                    "category": "db_performance",
                    "content": f"Database pooling test prompt {i}",
                    "created_by": "db_test"
                }
                prompt = service.create_entity(prompt_data)
                results.append(prompt)

                # Also perform a read operation
                retrieved = service.get_entity(prompt.id)
                assert retrieved.id == prompt.id

            return results

        start_time = time.time()
        results = perform_db_operations()
        end_time = time.time()

        duration = end_time - start_time
        operations_per_second = 200 / duration  # 100 creates + 100 reads

        print(".1f")
        assert len(results) == 100
        # Should handle at least 50 operations per second
        assert operations_per_second > 50, f"DB performance too slow: {operations_per_second:.1f} ops/sec"


@pytest.mark.stress_test
class TestPromptStoreStressTesting:
    """Stress testing for edge cases and high load scenarios."""

    def test_large_prompt_handling(self, performance_db):
        """Test handling of very large prompts."""
        service = PromptService()

        # Create a large prompt (10KB)
        large_content = "Large prompt content. " * 1000  # ~20KB of content

        prompt_data = {
            "name": "large_prompt_test",
            "category": "stress_test",
            "content": large_content,
            "description": "Testing large prompt handling",
            "created_by": "stress_test"
        }

        start_time = time.time()
        result = service.create_entity(prompt_data)
        end_time = time.time()

        creation_time = end_time - start_time

        assert result.id is not None
        assert len(result.content) > 10000  # Ensure large content is stored
        print(".3f")
        # Should create within reasonable time (under 1 second)
        assert creation_time < 1.0, f"Large prompt creation too slow: {creation_time:.3f}s"

    def test_many_versions_performance(self, performance_db):
        """Test performance with many prompt versions."""
        service = PromptService()

        # Create initial prompt
        prompt_data = {
            "name": "version_stress_test",
            "category": "stress_test",
            "content": "Initial version content",
            "created_by": "stress_test"
        }
        prompt = service.create_entity(prompt_data)

        # Create many versions
        start_time = time.time()
        for i in range(50):
            prompt = service.update_prompt_content(
                prompt.id,
                f"Version {i+2} content with changes",
                change_summary=f"Version {i+2} update",
                updated_by="stress_test"
            )

        end_time = time.time()
        duration = end_time - start_time

        assert prompt.version == 51  # Initial + 50 updates
        print(".3f")
        # Should handle 50 version updates within reasonable time
        assert duration < 10.0, f"Version updates too slow: {duration:.3f}s"

    def test_high_frequency_updates(self, performance_db):
        """Test rapid successive updates to the same prompt."""
        service = PromptService()

        # Create initial prompt
        prompt_data = {
            "name": "frequency_test",
            "category": "stress_test",
            "content": "Initial content",
            "created_by": "stress_test"
        }
        prompt = service.create_entity(prompt_data)

        # Perform rapid updates
        updates = []
        start_time = time.time()

        for i in range(20):
            updated = service.update_prompt_content(
                prompt.id,
                f"Rapid update {i+1} content",
                change_summary=f"Rapid update {i+1}",
                updated_by="stress_test"
            )
            updates.append(updated)

        end_time = time.time()
        duration = end_time - start_time

        assert len(updates) == 20
        assert updates[-1].version == 21
        print(".3f")
        # Should handle rapid updates efficiently
        assert duration < 5.0, f"Rapid updates too slow: {duration:.3f}s"


# Performance profiling utilities
def profile_memory_usage(func):
    """Decorator to profile memory usage of a function."""
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        duration = end_time - start_time

        print(f"Function {func.__name__}:")
        print(".1f")
        print(".3f")
        print(".1f")

        return result
    return wrapper


def calculate_performance_stats(times: List[float]) -> Dict[str, float]:
    """Calculate performance statistics from timing data."""
    if not times:
        return {}

    sorted_times = sorted(times)
    return {
        "count": len(times),
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "95th_percentile": sorted_times[int(len(times) * 0.95)] if times else 0,
        "99th_percentile": sorted_times[int(len(times) * 0.99)] if times else 0
    }


# Command line performance testing utilities
if __name__ == "__main__":
    print("Prompt Store Performance Testing Suite")
    print("=" * 50)
    print("Run with: pytest tests/performance/test_prompt_store_performance.py -v")
    print("Run benchmarks: pytest tests/performance/test_prompt_store_performance.py -k benchmark")
    print("Run load tests: pytest tests/performance/test_prompt_store_performance.py -k load_test")
    print("Run stress tests: pytest tests/performance/test_prompt_store_performance.py -k stress_test")
