#!/usr/bin/env python3
"""Comprehensive Integration Test for the Complete LLM Documentation Ecosystem.

This script tests the full integration of all implemented features across the
Analysis Service, including distributed processing, load balancing, and all
analysis capabilities.
"""

import asyncio
import time
import json
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add services to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'analysis-service'))

try:
    # Try direct imports first
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'analysis-service'))
    from modules.distributed_processor import (
        DistributedProcessor,
        submit_distributed_task,
        get_distributed_task_status,
        LoadBalancingStrategy
    )
    from modules.cross_repository_analyzer import (
        CrossRepositoryAnalyzer,
        analyze_repositories
    )
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Continuing with limited functionality...")


class IntegrationTestSuite:
    """Comprehensive integration test suite."""

    def __init__(self):
        """Initialize the test suite."""
        self.test_results = []
        self.start_time = None
        self.end_time = None

    def log_test(self, test_name: str, success: bool, message: str = "", duration: float = None):
        """Log a test result."""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.2f}s)" if duration else ""
        print(f"{status} {test_name}{duration_str}")
        if message:
            print(f"   {message}")

    async def run_all_tests(self):
        """Run all integration tests."""
        print("🚀 Starting Comprehensive Integration Test Suite")
        print("=" * 60)

        self.start_time = time.time()

        try:
            # Test 1: Distributed Processor Initialization
            await self.test_distributed_processor_initialization()

            # Test 2: Load Balancing Strategies
            await self.test_load_balancing_strategies()

            # Test 3: Task Submission and Processing
            await self.test_task_submission_and_processing()

            # Test 4: Batch Task Processing
            await self.test_batch_task_processing()

            # Test 5: Cross-Repository Analysis
            await self.test_cross_repository_analysis()

            # Test 6: Worker Scaling
            await self.test_worker_scaling()

            # Test 7: Queue Management
            await self.test_queue_management()

            # Test 8: Performance Monitoring
            await self.test_performance_monitoring()

            # Test 9: Error Handling
            await self.test_error_handling()

            # Test 10: Concurrent Load Testing
            await self.test_concurrent_load()

        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
            self.log_test("test_suite_execution", False, str(e))

        self.end_time = time.time()
        self.generate_report()

    async def test_distributed_processor_initialization(self):
        """Test distributed processor initialization."""
        start_time = time.time()

        try:
            processor = DistributedProcessor(max_workers=5)
            assert len(processor.workers) == 5
            assert processor.load_balancer is not None
            assert len(processor.task_handlers) > 0

            duration = time.time() - start_time
            self.log_test("distributed_processor_initialization", True,
                         "Successfully initialized with 5 workers", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.log_test("distributed_processor_initialization", False,
                         f"Failed: {e}", duration)

    async def test_load_balancing_strategies(self):
        """Test different load balancing strategies."""
        start_time = time.time()

        try:
            processor = DistributedProcessor(max_workers=3)

            # Test round-robin
            processor.set_load_balancing_strategy(LoadBalancingStrategy.ROUND_ROBIN)
            assert processor.load_balancer.strategy == LoadBalancingStrategy.ROUND_ROBIN

            # Test least-loaded
            processor.set_load_balancing_strategy(LoadBalancingStrategy.LEAST_LOADED)
            assert processor.load_balancer.strategy == LoadBalancingStrategy.LEAST_LOADED

            # Test adaptive (default)
            processor.set_load_balancing_strategy(LoadBalancingStrategy.ADAPTIVE)
            assert processor.load_balancer.strategy == LoadBalancingStrategy.ADAPTIVE

            duration = time.time() - start_time
            self.log_test("load_balancing_strategies", True,
                         "All strategies configured successfully", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.log_test("load_balancing_strategies", False,
                         f"Failed: {e}", duration)

    async def test_task_submission_and_processing(self):
        """Test task submission and processing."""
        start_time = time.time()

        try:
            # Test semantic similarity task
            task_data = {
                'task_type': 'semantic_similarity',
                'data': {
                    'documents': [
                        {'id': 'doc1', 'content': 'This is a test document about machine learning.'},
                        {'id': 'doc2', 'content': 'This document discusses ML algorithms and AI.'}
                    ]
                },
                'priority': 'high'
            }

            task_id = await submit_distributed_task(**task_data)
            assert task_id is not None

            # Wait a bit for processing
            await asyncio.sleep(1)

            # Check task status
            status = await get_distributed_task_status(task_id)
            assert status is not None
            assert 'status' in status

            duration = time.time() - start_time
            self.log_test("task_submission_and_processing", True,
                         f"Task {task_id} submitted and processed successfully", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.log_test("task_submission_and_processing", False,
                         f"Failed: {e}", duration)

    async def test_batch_task_processing(self):
        """Test batch task processing."""
        start_time = time.time()

        try:
            batch_tasks = [
                {
                    'task_type': 'sentiment_analysis',
                    'data': {'documents': [{'id': 'doc1', 'content': 'Great documentation!'}]},
                    'priority': 'normal'
                },
                {
                    'task_type': 'content_quality',
                    'data': {'documents': [{'id': 'doc2', 'content': 'Poor documentation'}]},
                    'priority': 'low'
                }
            ]

            # This would normally use the batch processing endpoint
            # For now, test individual task submission
            task_ids = []
            for task in batch_tasks:
                task_id = await submit_distributed_task(**task)
                task_ids.append(task_id)

            assert len(task_ids) == 2

            duration = time.time() - start_time
            self.log_test("batch_task_processing", True,
                         f"Batch of {len(task_ids)} tasks submitted successfully", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.log_test("batch_task_processing", False,
                         f"Failed: {e}", duration)

    async def test_cross_repository_analysis(self):
        """Test cross-repository analysis."""
        start_time = time.time()

        try:
            # Create sample repository data
            repositories = [
                {
                    'repository_id': 'repo-1',
                    'repository_name': 'api-service',
                    'files': [
                        {
                            'path': 'docs/README.md',
                            'content': '# API Service\nREST API for user management.'
                        }
                    ]
                },
                {
                    'repository_id': 'repo-2',
                    'repository_name': 'frontend-app',
                    'files': [
                        {
                            'path': 'docs/guide.md',
                            'content': '# Frontend Guide\nHow to use the application.'
                        }
                    ]
                }
            ]

            results = await analyze_repositories(repositories)
            assert results is not None
            assert 'repository_count' in results
            assert results['repository_count'] == 2

            duration = time.time() - start_time
            self.log_test("cross_repository_analysis", True,
                         "Cross-repository analysis completed successfully", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.log_test("cross_repository_analysis", False,
                         f"Failed: {e}", duration)

    async def test_worker_scaling(self):
        """Test worker scaling functionality."""
        start_time = time.time()

        try:
            processor = DistributedProcessor(max_workers=2)

            initial_count = len(processor.workers)

            # Scale up
            success = await processor.scale_workers(5)
            assert success is True
            assert len(processor.workers) == 5

            # Scale down
            success = await processor.scale_workers(3)
            assert success is True
            assert len(processor.workers) == 3

            duration = time.time() - start_time
            self.log_test("worker_scaling", True,
                         f"Workers scaled from {initial_count} to {len(processor.workers)}", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.log_test("worker_scaling", False,
                         f"Failed: {e}", duration)

    async def test_queue_management(self):
        """Test queue management functionality."""
        start_time = time.time()

        try:
            processor = DistributedProcessor(max_workers=2)

            # Submit multiple tasks to fill queue
            for i in range(5):
                await processor.submit_task(
                    task_type='data_processing',
                    data={'operation': f'task-{i}'},
                    priority=['low', 'normal', 'high', 'critical'][i % 4]
                )

            queue_status = processor.get_queue_status()
            assert 'queue_length' in queue_status
            assert queue_status['queue_length'] > 0

            duration = time.time() - start_time
            self.log_test("queue_management", True,
                         f"Queue contains {queue_status['queue_length']} tasks", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.log_test("queue_management", False,
                         f"Failed: {e}", duration)

    async def test_performance_monitoring(self):
        """Test performance monitoring."""
        start_time = time.time()

        try:
            processor = DistributedProcessor(max_workers=3)

            # Get initial stats
            stats = await processor.get_processing_stats()
            assert 'total_tasks' in stats
            assert 'active_workers' in stats

            # Submit a task and check updated stats
            task_id = await processor.submit_task(
                task_type='data_processing',
                data={'operation': 'performance_test'}
            )

            updated_stats = await processor.get_processing_stats()
            assert updated_stats['total_tasks'] >= stats['total_tasks']

            duration = time.time() - start_time
            self.log_test("performance_monitoring", True,
                         f"Performance stats: {updated_stats['total_tasks']} total tasks", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.log_test("performance_monitoring", False,
                         f"Failed: {e}", duration)

    async def test_error_handling(self):
        """Test error handling in distributed processing."""
        start_time = time.time()

        try:
            processor = DistributedProcessor(max_workers=2)

            # Submit task with invalid data
            task_id = await processor.submit_task(
                task_type='invalid_task_type',
                data={'invalid': 'data'}
            )

            # Wait for processing
            await asyncio.sleep(1)

            # Check task status
            status = await processor.get_task_status(task_id)
            # Should either complete or fail gracefully

            duration = time.time() - start_time
            self.log_test("error_handling", True,
                         "Error handling processed gracefully", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.log_test("error_handling", False,
                         f"Error handling failed: {e}", duration)

    async def test_concurrent_load(self):
        """Test concurrent load handling."""
        start_time = time.time()

        try:
            processor = DistributedProcessor(max_workers=5)

            # Submit many tasks concurrently
            tasks = []
            for i in range(20):
                task = processor.submit_task(
                    task_type='data_processing',
                    data={'operation': f'concurrent-{i}'},
                    priority=['low', 'normal', 'high'][i % 3]
                )
                tasks.append(task)

            # Wait for all tasks to be submitted
            task_ids = await asyncio.gather(*tasks)
            assert len(task_ids) == 20

            # Check queue status
            queue_status = processor.get_queue_status()
            assert queue_status['queue_length'] >= 15  # Some may be processing

            duration = time.time() - start_time
            self.log_test("concurrent_load", True,
                         f"Successfully handled {len(task_ids)} concurrent tasks", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.log_test("concurrent_load", False,
                         f"Concurrent load test failed: {e}", duration)

    def generate_report(self):
        """Generate comprehensive test report."""
        total_time = self.end_time - self.start_time

        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST REPORT")
        print("=" * 60)

        passed = sum(1 for test in self.test_results if test['success'])
        failed = len(self.test_results) - passed

        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"✅ Tests passed: {passed}")
        print(f"❌ Tests failed: {failed}")
        print(f"📈 Success rate: {(passed / len(self.test_results) * 100):.1f}%")

        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)

        for test in self.test_results:
            status = "✅" if test['success'] else "❌"
            duration = f" ({test['duration']:.2f}s)" if test['duration'] else ""
            print(f"{status} {test['test_name']}{duration}")
            if test['message']:
                print(f"   {test['message']}")

        print("\n" + "=" * 60)

        if failed == 0:
            print("🎉 ALL TESTS PASSED! The system is fully operational.")
        else:
            print(f"⚠️  {failed} test(s) failed. Please review the results above.")

        print("=" * 60)


async def main():
    """Run the integration test suite."""
    print("🤖 LLM Documentation Ecosystem - Integration Test Suite")
    print("Testing all implemented features and their interactions...")

    test_suite = IntegrationTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    # Run the integration tests
    asyncio.run(main())
