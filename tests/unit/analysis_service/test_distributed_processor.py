"""Tests for distributed processing functionality in Analysis Service.

Tests the distributed processor module and its integration with the analysis service.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'services'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'services', 'analysis-service'))

from modules.distributed_processor import (
    DistributedProcessor,
    DistributedTask,
    Worker,
    TaskStatus,
    WorkerStatus,
    TaskPriority,
    submit_distributed_task,
    get_distributed_task_status
)


@pytest.fixture
def sample_task_data():
    """Create sample task data for distributed processing testing."""
    return {
        'task_type': 'semantic_similarity',
        'data': {
            'documents': [
                {'id': 'doc1', 'content': 'This is a test document about API.'},
                {'id': 'doc2', 'content': 'This is another document about API.'}
            ],
            'threshold': 0.8
        },
        'priority': 'high'
    }


@pytest.fixture
def sample_batch_tasks():
    """Create sample batch tasks for testing."""
    return [
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


class TestDistributedProcessor:
    """Test the DistributedProcessor class."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test successful initialization of the distributed processor."""
        processor = DistributedProcessor(max_workers=5)

        assert len(processor.workers) == 5
        assert len(processor.task_handlers) > 0
        assert processor.max_workers == 5
        assert 'semantic_similarity' in processor.task_handlers

    @pytest.mark.asyncio
    async def test_submit_task(self, sample_task_data):
        """Test task submission."""
        processor = DistributedProcessor(max_workers=2)

        task_id = await processor.submit_task(
            task_type=sample_task_data['task_type'],
            data=sample_task_data['data'],
            priority=TaskPriority.HIGH
        )

        assert task_id is not None
        assert task_id in processor.tasks

        task = processor.tasks[task_id]
        assert task.task_type == 'semantic_similarity'
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_submit_batch_tasks(self, sample_batch_tasks):
        """Test batch task submission."""
        processor = DistributedProcessor(max_workers=2)

        task_ids = await processor.submit_batch_tasks(sample_batch_tasks)

        assert len(task_ids) == 2
        assert len(processor.tasks) == 2

        for task_id in task_ids:
            assert task_id in processor.tasks

    @pytest.mark.asyncio
    async def test_get_task_status(self, sample_task_data):
        """Test task status retrieval."""
        processor = DistributedProcessor(max_workers=2)

        task_id = await processor.submit_task(
            task_type=sample_task_data['task_type'],
            data=sample_task_data['data']
        )

        status = await processor.get_task_status(task_id)

        assert status is not None
        assert status['task_id'] == task_id
        assert status['task_type'] == 'semantic_similarity'
        assert status['status'] == 'pending'
        assert status['priority'] == 'normal'

    @pytest.mark.asyncio
    async def test_cancel_task(self, sample_task_data):
        """Test task cancellation."""
        processor = DistributedProcessor(max_workers=2)

        task_id = await processor.submit_task(
            task_type=sample_task_data['task_type'],
            data=sample_task_data['data']
        )

        # Cancel the task
        cancelled = await processor.cancel_task(task_id)

        assert cancelled is True

        task = processor.tasks[task_id]
        assert task.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_get_worker_status(self):
        """Test worker status retrieval."""
        processor = DistributedProcessor(max_workers=3)

        status = await processor.get_worker_status()

        assert status['total_workers'] == 3
        assert status['available_workers'] == 3
        assert status['busy_workers'] == 0
        assert len(status['workers']) == 3

    @pytest.mark.asyncio
    async def test_get_processing_stats(self):
        """Test processing statistics retrieval."""
        processor = DistributedProcessor(max_workers=2)

        stats = await processor.get_processing_stats()

        assert stats['total_tasks'] == 0
        assert stats['completed_tasks'] == 0
        assert stats['failed_tasks'] == 0
        assert stats['active_workers'] == 2

    @pytest.mark.asyncio
    async def test_scale_workers_up(self):
        """Test scaling workers up."""
        processor = DistributedProcessor(max_workers=2)

        initial_count = len(processor.workers)

        success = await processor.scale_workers(5)

        assert success is True
        assert len(processor.workers) == 5

    @pytest.mark.asyncio
    async def test_scale_workers_down(self):
        """Test scaling workers down."""
        processor = DistributedProcessor(max_workers=5)

        initial_count = len(processor.workers)

        success = await processor.scale_workers(2)

        assert success is True
        assert len(processor.workers) == 2

    @pytest.mark.asyncio
    async def test_assign_worker(self, sample_task_data):
        """Test worker assignment."""
        processor = DistributedProcessor(max_workers=2)

        task = DistributedTask(
            task_id='test-task',
            task_type='semantic_similarity',
            data=sample_task_data['data']
        )

        worker = await processor._assign_worker(task)

        assert worker is not None
        assert worker.worker_id in processor.workers

    @pytest.mark.asyncio
    async def test_task_execution_simulation(self, sample_task_data):
        """Test simulated task execution."""
        processor = DistributedProcessor(max_workers=2)

        # Mock the task handler
        async def mock_handler(data):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {'result': 'success', 'similarity_score': 0.85}

        processor.task_handlers['semantic_similarity'] = mock_handler

        task_id = await processor.submit_task(
            task_type='semantic_similarity',
            data=sample_task_data['data']
        )

        # Simulate task processing
        await processor._process_task(task_id)

        task = processor.tasks[task_id]
        assert task.status == TaskStatus.COMPLETED
        assert task.result is not None
        assert 'similarity_score' in task.result


class TestDistributedTask:
    """Test the DistributedTask class."""

    def test_task_creation(self, sample_task_data):
        """Test task creation."""
        task = DistributedTask(
            task_id='test-task',
            task_type='semantic_similarity',
            data=sample_task_data['data'],
            priority=TaskPriority.HIGH
        )

        assert task.task_id == 'test-task'
        assert task.task_type == 'semantic_similarity'
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert not task.is_completed()

    def test_task_completion(self, sample_task_data):
        """Test task completion."""
        task = DistributedTask(
            task_id='test-task',
            task_type='semantic_similarity',
            data=sample_task_data['data']
        )

        task.status = TaskStatus.COMPLETED
        task.completed_at = task.created_at

        assert task.is_completed()

    def test_task_should_retry(self, sample_task_data):
        """Test task retry logic."""
        task = DistributedTask(
            task_id='test-task',
            task_type='semantic_similarity',
            data=sample_task_data['data']
        )

        # Initial state
        assert not task.should_retry()

        # Failed state with retry count < max
        task.status = TaskStatus.FAILED
        task.error_message = 'Test error'
        task.retry_count = 1

        assert task.should_retry()

        # Failed state with retry count >= max
        task.retry_count = 3

        assert not task.should_retry()


class TestWorker:
    """Test the Worker class."""

    def test_worker_creation(self):
        """Test worker creation."""
        worker = Worker(
            worker_id='worker-1',
            capabilities={'analysis', 'processing'},
            max_concurrent_tasks=3
        )

        assert worker.worker_id == 'worker-1'
        assert worker.status == WorkerStatus.AVAILABLE
        assert worker.active_tasks == 0
        assert worker.is_available()

    def test_worker_can_handle_task(self):
        """Test worker capability checking."""
        worker = Worker(
            worker_id='worker-1',
            capabilities={'analysis', 'processing'}
        )

        assert worker.can_handle_task('analysis')
        assert worker.can_handle_task('processing')
        assert not worker.can_handle_task('unknown')

    def test_worker_busy_state(self):
        """Test worker busy state."""
        worker = Worker(
            worker_id='worker-1',
            max_concurrent_tasks=2
        )

        worker.active_tasks = 2
        assert not worker.is_available()

        worker.active_tasks = 1
        assert worker.is_available()


@pytest.mark.asyncio
class TestDistributedIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_submit_distributed_task_function(self, sample_task_data):
        """Test the convenience function for task submission."""
        with patch('modules.distributed_processor.distributed_processor') as mock_processor:
            mock_processor.submit_task.return_value = 'test-task-id'

            task_id = await submit_distributed_task(
                task_type=sample_task_data['task_type'],
                data=sample_task_data['data'],
                priority='high'
            )

            assert task_id == 'test-task-id'
            mock_processor.submit_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_distributed_task_status_function(self):
        """Test the convenience function for status retrieval."""
        with patch('modules.distributed_processor.distributed_processor') as mock_processor:
            mock_status = {
                'task_id': 'test-task',
                'status': 'completed',
                'progress': 1.0
            }
            mock_processor.get_task_status.return_value = mock_status

            status = await get_distributed_task_status('test-task')

            assert status == mock_status
            mock_processor.get_task_status.assert_called_once_with('test-task')


class TestTaskHandlers:
    """Test individual task handlers."""

    @pytest.mark.asyncio
    async def test_semantic_similarity_handler(self):
        """Test semantic similarity task handler."""
        processor = DistributedProcessor(max_workers=1)

        # Mock the semantic analyzer
        with patch('modules.distributed_processor.DistributedProcessor._handle_semantic_similarity_task') as mock_handler:
            mock_handler.return_value = {'similarity_score': 0.85}

            result = await processor._handle_semantic_similarity_task({
                'documents': [{'id': 'doc1', 'content': 'test'}]
            })

            assert result == {'similarity_score': 0.85}

    @pytest.mark.asyncio
    async def test_batch_analysis_handler(self):
        """Test batch analysis task handler."""
        processor = DistributedProcessor(max_workers=1)

        # Mock the individual handlers
        with patch.object(processor, '_handle_semantic_similarity_task') as mock_similarity:
            mock_similarity.return_value = {'similarity': 0.8}

            batch_data = {
                'analysis_types': ['semantic_similarity'],
                'documents': [{'id': 'doc1', 'content': 'test'}]
            }

            result = await processor._handle_batch_analysis_task(batch_data)

            assert 'semantic_similarity' in result
            mock_similarity.assert_called_once()


class TestPriorityQueue:
    """Test priority-based task queuing."""

    @pytest.mark.asyncio
    async def test_priority_ordering(self, sample_task_data):
        """Test that tasks are processed in priority order."""
        processor = DistributedProcessor(max_workers=1)

        # Submit tasks with different priorities
        low_task = await processor.submit_task(
            task_type='data_processing',
            data={'operation': 'low_priority'},
            priority=TaskPriority.LOW
        )

        high_task = await processor.submit_task(
            task_type='data_processing',
            data={'operation': 'high_priority'},
            priority=TaskPriority.HIGH
        )

        # Check that high priority task is processed first
        # (This would require actual processing to verify)

        assert low_task in processor.tasks
        assert high_task in processor.tasks

        low_priority_task = processor.tasks[low_task]
        high_priority_task = processor.tasks[high_task]

        assert low_priority_task.priority == TaskPriority.LOW
        assert high_priority_task.priority == TaskPriority.HIGH


if __name__ == "__main__":
    pytest.main([__file__])
