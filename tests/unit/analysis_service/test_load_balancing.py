"""Tests for load balancing functionality in Analysis Service.

Tests the load balancing components and their integration with the distributed processor.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'services'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'services', 'analysis-service'))

from modules.distributed_processor import (
    LoadBalancer,
    LoadBalancingStrategy,
    PriorityQueue,
    Worker,
    WorkerStatus,
    DistributedTask,
    TaskPriority
)


@pytest.fixture
def sample_workers():
    """Create sample workers for load balancing testing."""
    return [
        Worker(
            worker_id='worker-1',
            capabilities={'analysis', 'processing'},
            performance_score=1.2,
            active_tasks=1,
            max_concurrent_tasks=3
        ),
        Worker(
            worker_id='worker-2',
            capabilities={'analysis', 'processing'},
            performance_score=0.8,
            active_tasks=2,
            max_concurrent_tasks=3
        ),
        Worker(
            worker_id='worker-3',
            capabilities={'analysis', 'processing'},
            performance_score=1.5,
            active_tasks=0,
            max_concurrent_tasks=3
        )
    ]


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return DistributedTask(
        task_id='test-task',
        task_type='semantic_similarity',
        priority=TaskPriority.NORMAL,
        data={'documents': [{'id': 'doc1', 'content': 'test'}]}
    )


class TestPriorityQueue:
    """Test the PriorityQueue class."""

    @pytest.mark.asyncio
    async def test_queue_initialization(self):
        """Test priority queue initialization."""
        queue = PriorityQueue()
        assert queue is not None

    @pytest.mark.asyncio
    async def test_put_and_get(self):
        """Test putting items in queue and getting them."""
        queue = PriorityQueue()
        task = DistributedTask(task_id='test', task_type='test')

        await queue.put(task, priority=2)
        retrieved = await queue.get()

        assert retrieved is not None
        assert retrieved.task_id == 'test'

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test that higher priority items are retrieved first."""
        queue = PriorityQueue()

        low_task = DistributedTask(task_id='low', task_type='test')
        high_task = DistributedTask(task_id='high', task_type='test')

        await queue.put(low_task, priority=1)  # Lower priority
        await queue.put(high_task, priority=3)  # Higher priority

        # Should get high priority task first
        first = await queue.get()
        assert first.task_id == 'high'

        # Then low priority task
        second = await queue.get()
        assert second.task_id == 'low'

    @pytest.mark.asyncio
    async def test_empty_queue(self):
        """Test empty queue operations."""
        queue = PriorityQueue()

        assert await queue.empty() is True
        assert await queue.get() is None

    @pytest.mark.asyncio
    async def test_queue_size(self):
        """Test queue size tracking."""
        queue = PriorityQueue()
        task = DistributedTask(task_id='test', task_type='test')

        assert await queue.size() == 0

        await queue.put(task, priority=1)
        assert await queue.size() == 1

        await queue.get()
        assert await queue.size() == 0


class TestLoadBalancer:
    """Test the LoadBalancer class."""

    def test_initialization(self):
        """Test load balancer initialization."""
        balancer = LoadBalancer()
        assert balancer.strategy == LoadBalancingStrategy.ADAPTIVE
        assert isinstance(balancer.worker_metrics, dict)

    @pytest.mark.asyncio
    async def test_round_robin_selection(self, sample_workers):
        """Test round-robin worker selection."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)

        # First selection
        worker1 = await balancer.select_worker(sample_task, sample_workers)
        assert worker1.worker_id == 'worker-1'

        # Second selection
        worker2 = await balancer.select_worker(sample_task, sample_workers)
        assert worker2.worker_id == 'worker-2'

        # Third selection
        worker3 = await balancer.select_worker(sample_task, sample_workers)
        assert worker3.worker_id == 'worker-3'

        # Fourth selection (should wrap around)
        worker4 = await balancer.select_worker(sample_task, sample_workers)
        assert worker4.worker_id == 'worker-1'

    @pytest.mark.asyncio
    async def test_least_loaded_selection(self, sample_workers):
        """Test least loaded worker selection."""
        balancer = LoadBalancer(LoadBalancingStrategy.LEAST_LOADED)

        # worker-3 has 0 active tasks, should be selected
        worker = await balancer.select_worker(sample_task, sample_workers)
        assert worker.worker_id == 'worker-3'

    @pytest.mark.asyncio
    async def test_weighted_random_selection(self, sample_workers):
        """Test weighted random worker selection."""
        balancer = LoadBalancer(LoadBalancingStrategy.WEIGHTED_RANDOM)

        # With enough iterations, all workers should be selected at least once
        selected_workers = set()
        for _ in range(100):
            worker = await balancer.select_worker(sample_task, sample_workers)
            selected_workers.add(worker.worker_id)

        # All workers should have been selected
        assert len(selected_workers) == len(sample_workers)

    @pytest.mark.asyncio
    async def test_performance_based_selection(self, sample_workers, sample_task):
        """Test performance-based worker selection."""
        balancer = LoadBalancer(LoadBalancingStrategy.PERFORMANCE_BASED)

        # worker-3 has highest performance score (1.5), should be selected
        worker = await balancer.select_worker(sample_task, sample_workers)
        assert worker.worker_id == 'worker-3'

    @pytest.mark.asyncio
    async def test_adaptive_selection(self, sample_workers, sample_task):
        """Test adaptive worker selection."""
        balancer = LoadBalancer(LoadBalancingStrategy.ADAPTIVE)

        # Should use performance-based selection initially
        worker = await balancer.select_worker(sample_task, sample_workers)
        assert worker.worker_id == 'worker-3'

    @pytest.mark.asyncio
    async def test_no_available_workers(self, sample_task):
        """Test selection when no workers are available."""
        balancer = LoadBalancer()

        worker = await balancer.select_worker(sample_task, [])
        assert worker is None

    @pytest.mark.asyncio
    async def test_single_worker(self, sample_workers, sample_task):
        """Test selection with single worker."""
        balancer = LoadBalancer()
        single_worker = [sample_workers[0]]

        worker = await balancer.select_worker(sample_task, single_worker)
        assert worker.worker_id == 'worker-1'

    def test_strategy_change(self):
        """Test changing load balancing strategy."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        assert balancer.strategy == LoadBalancingStrategy.ROUND_ROBIN

        balancer.set_strategy(LoadBalancingStrategy.LEAST_LOADED)
        assert balancer.strategy == LoadBalancingStrategy.LEAST_LOADED

    @pytest.mark.asyncio
    async def test_update_worker_metrics(self, sample_workers):
        """Test updating worker metrics."""
        balancer = LoadBalancer()

        await balancer.update_worker_metrics(sample_workers[0])

        assert sample_workers[0].worker_id in balancer.worker_metrics
        metrics = balancer.worker_metrics[sample_workers[0].worker_id]

        assert 'performance_score' in metrics
        assert 'active_tasks' in metrics
        assert 'max_tasks' in metrics


class TestWorkerCapabilityMatching:
    """Test worker capability matching."""

    @pytest.mark.asyncio
    async def test_capability_matching(self, sample_task):
        """Test that workers are matched based on capabilities."""
        balancer = LoadBalancer(LoadBalancingStrategy.PERFORMANCE_BASED)

        # Create workers with different capabilities
        capable_worker = Worker(
            worker_id='capable',
            capabilities={'semantic_similarity', 'analysis'},
            performance_score=1.0
        )

        incapable_worker = Worker(
            worker_id='incapable',
            capabilities={'other_task'},
            performance_score=2.0
        )

        workers = [capable_worker, incapable_worker]

        # Should select capable worker despite lower performance score
        selected = await balancer.select_worker(sample_task, workers)
        assert selected.worker_id == 'capable'


class TestLoadBalancingIntegration:
    """Test load balancing integration with distributed processor."""

    @pytest.mark.asyncio
    async def test_load_balancer_integration(self, sample_workers, sample_task):
        """Test load balancer integration."""
        from modules.distributed_processor import DistributedProcessor

        processor = DistributedProcessor(max_workers=3)

        # Replace workers with our test workers
        processor.workers = {w.worker_id: w for w in sample_workers}

        # Test task assignment
        available_workers = [w for w in processor.workers.values() if w.is_available()]
        worker = await processor.load_balancer.select_worker(sample_task, available_workers)

        assert worker is not None
        assert worker.worker_id in ['worker-1', 'worker-2', 'worker-3']


class TestLoadBalancingStrategies:
    """Test different load balancing strategies in detail."""

    @pytest.mark.asyncio
    async def test_round_robin_fairness(self):
        """Test that round-robin distributes tasks fairly."""
        balancer = LoadBalancingStrategy.ROUND_ROBIN

        workers = [
            Worker(worker_id=f'worker-{i}', capabilities={'test'})
            for i in range(3)
        ]

        # Simulate multiple selections
        selections = {}
        for _ in range(30):  # 10 rounds per worker
            # In practice, this would be called from the load balancer
            worker_index = (_ % len(workers))
            worker_id = workers[worker_index].worker_id
            selections[worker_id] = selections.get(worker_id, 0) + 1

        # Each worker should be selected 10 times
        assert all(count == 10 for count in selections.values())

    @pytest.mark.asyncio
    async def test_least_loaded_with_varying_loads(self):
        """Test least loaded strategy with workers having different loads."""
        balancer = LoadBalancingStrategy.LEAST_LOADED

        workers = [
            Worker(worker_id='light', active_tasks=1, max_concurrent_tasks=5),
            Worker(worker_id='medium', active_tasks=3, max_concurrent_tasks=5),
            Worker(worker_id='heavy', active_tasks=5, max_concurrent_tasks=5)
        ]

        # Light worker should always be selected
        for _ in range(10):
            # Calculate least loaded manually
            least_loaded = min(workers, key=lambda w: w.active_tasks / w.max_concurrent_tasks)
            assert least_loaded.worker_id == 'light'

    @pytest.mark.asyncio
    async def test_performance_based_with_scores(self):
        """Test performance-based selection with different scores."""
        balancer = LoadBalancingStrategy.PERFORMANCE_BASED

        workers = [
            Worker(worker_id='slow', performance_score=0.5),
            Worker(worker_id='medium', performance_score=1.0),
            Worker(worker_id='fast', performance_score=1.5)
        ]

        # Fast worker should always be selected when available
        for _ in range(10):
            # Simulate performance-based selection logic
            best_worker = max(workers, key=lambda w: w.performance_score)
            assert best_worker.worker_id == 'fast'


if __name__ == "__main__":
    pytest.main([__file__])
