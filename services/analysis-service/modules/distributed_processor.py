"""Distributed Processing module for Analysis Service.

Provides scalable, parallel processing capabilities for analysis tasks
across multiple workers, enabling high-performance document analysis
at enterprise scale.
"""

import asyncio
import time
import logging
import json
import uuid
import heapq
import random
import statistics
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
import threading
import multiprocessing
import queue
import os

try:
    from services.shared.core.responses import create_success_response, create_error_response
    from services.shared.core.constants_new import ErrorCodes
except ImportError:
    # Fallback for testing or when shared services are not available
    def create_success_response(message, data=None, **kwargs):
        return {"message": message, "data": data, "status": "success"}

    def create_error_response(message, error_code=None, **kwargs):
        return {"message": message, "error": error_code, "status": "error"}

    class ErrorCodes:
        ANALYSIS_FAILED = "ANALYSIS_FAILED"
        PROCESSING_FAILED = "PROCESSING_FAILED"

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of distributed processing tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkerStatus(Enum):
    """Status of distributed processing workers."""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class TaskPriority(Enum):
    """Priority levels for distributed processing tasks."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class LoadBalancingStrategy(Enum):
    """Load balancing strategies for task distribution."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    WEIGHTED_RANDOM = "weighted_random"
    PERFORMANCE_BASED = "performance_based"
    ADAPTIVE = "adaptive"


class QueuePriority(Enum):
    """Queue priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Worker:
    """Represents a distributed processing worker."""
    worker_id: str
    status: WorkerStatus = WorkerStatus.AVAILABLE
    current_task: Optional[str] = None
    capabilities: Set[str] = field(default_factory=set)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    tasks_completed: int = 0
    tasks_failed: int = 0
    performance_score: float = 1.0
    max_concurrent_tasks: int = 5
    active_tasks: int = 0

    def is_available(self) -> bool:
        """Check if worker is available for new tasks."""
        return (self.status == WorkerStatus.AVAILABLE and
                self.active_tasks < self.max_concurrent_tasks)

    def can_handle_task(self, task_type: str) -> bool:
        """Check if worker can handle a specific task type."""
        return task_type in self.capabilities or "general" in self.capabilities


@dataclass
class DistributedTask:
    """Represents a distributed processing task."""
    task_id: str
    task_type: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    data: Dict[str, Any] = field(default_factory=dict)
    assigned_worker: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    estimated_completion: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3

    def is_completed(self) -> bool:
        """Check if task is completed (success or failure)."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]

    def should_retry(self) -> bool:
        """Check if task should be retried."""
        return (self.status == TaskStatus.FAILED and
                self.retry_count < self.max_retries and
                self.error_message is not None)


class PriorityQueue:
    """Priority queue for task management with load balancing."""

    def __init__(self):
        """Initialize the priority queue."""
        self._queue = []
        self._entry_count = 0
        self._lock = asyncio.Lock()

    async def put(self, item: DistributedTask, priority: int = 1) -> None:
        """Add an item to the priority queue."""
        async with self._lock:
            entry = (-priority, self._entry_count, item)  # Negative for max-heap behavior
            heapq.heappush(self._queue, entry)
            self._entry_count += 1

    async def get(self) -> Optional[DistributedTask]:
        """Get the highest priority item from the queue."""
        async with self._lock:
            if not self._queue:
                return None

            priority, count, item = heapq.heappop(self._queue)
            return item

    async def empty(self) -> bool:
        """Check if the queue is empty."""
        async with self._lock:
            return len(self._queue) == 0

    async def size(self) -> int:
        """Get the size of the queue."""
        async with self._lock:
            return len(self._queue)

    async def peek(self) -> Optional[DistributedTask]:
        """Peek at the highest priority item without removing it."""
        async with self._lock:
            if not self._queue:
                return None

            priority, count, item = self._queue[0]
            return item


class LoadBalancer:
    """Intelligent load balancer for task distribution."""

    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE):
        """Initialize the load balancer."""
        self.strategy = strategy
        self.worker_metrics = {}
        self.round_robin_index = 0
        self.performance_history = []
        self._lock = asyncio.Lock()

    async def select_worker(self, task: DistributedTask, available_workers: List[Worker]) -> Optional[Worker]:
        """Select the best worker for a task based on the current strategy."""
        async with self._lock:
            if not available_workers:
                return None

            if len(available_workers) == 1:
                return available_workers[0]

            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return await self._round_robin_selection(available_workers)
            elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
                return await self._least_loaded_selection(available_workers)
            elif self.strategy == LoadBalancingStrategy.WEIGHTED_RANDOM:
                return await self._weighted_random_selection(available_workers)
            elif self.strategy == LoadBalancingStrategy.PERFORMANCE_BASED:
                return await self._performance_based_selection(available_workers, task)
            elif self.strategy == LoadBalancingStrategy.ADAPTIVE:
                return await self._adaptive_selection(available_workers, task)
            else:
                return available_workers[0]  # Fallback to first available

    async def _round_robin_selection(self, workers: List[Worker]) -> Worker:
        """Round-robin worker selection."""
        worker = workers[self.round_robin_index % len(workers)]
        self.round_robin_index += 1
        return worker

    async def _least_loaded_selection(self, workers: List[Worker]) -> Worker:
        """Select the least loaded worker."""
        return min(workers, key=lambda w: w.active_tasks / max(w.max_concurrent_tasks, 1))

    async def _weighted_random_selection(self, workers: List[Worker]) -> Worker:
        """Weighted random selection based on performance scores."""
        weights = [w.performance_score for w in workers]
        total_weight = sum(weights)

        if total_weight == 0:
            return random.choice(workers)

        # Normalize weights
        normalized_weights = [w / total_weight for w in weights]

        # Select based on weights
        r = random.random()
        cumulative = 0
        for i, weight in enumerate(normalized_weights):
            cumulative += weight
            if r <= cumulative:
                return workers[i]

        return workers[-1]  # Fallback

    async def _performance_based_selection(self, workers: List[Worker], task: DistributedTask) -> Worker:
        """Performance-based worker selection."""
        # Score workers based on their performance with similar tasks
        worker_scores = []
        for worker in workers:
            score = worker.performance_score

            # Adjust score based on current load
            load_factor = worker.active_tasks / max(worker.max_concurrent_tasks, 1)
            score *= (1 - load_factor * 0.3)  # Penalize heavily loaded workers

            # Adjust score based on task type compatibility
            if worker.can_handle_task(task.task_type):
                score *= 1.2  # Bonus for compatible workers
            else:
                score *= 0.8  # Penalty for incompatible workers

            worker_scores.append((worker, score))

        # Return worker with highest score
        return max(worker_scores, key=lambda x: x[1])[0]

    async def _adaptive_selection(self, workers: List[Worker], task: DistributedTask) -> Worker:
        """Adaptive selection that learns from past performance."""
        # Start with performance-based selection
        best_worker = await self._performance_based_selection(workers, task)

        # Update performance history
        self._update_performance_history(best_worker, task)

        return best_worker

    def _update_performance_history(self, worker: Worker, task: DistributedTask) -> None:
        """Update performance history for learning."""
        # This would track task completion times, success rates, etc.
        # For now, just maintain a simple history
        history_entry = {
            'worker_id': worker.worker_id,
            'task_type': task.task_type,
            'timestamp': datetime.now(),
            'performance_score': worker.performance_score
        }

        self.performance_history.append(history_entry)

        # Keep only recent history (last 100 entries)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

    async def update_worker_metrics(self, worker: Worker) -> None:
        """Update metrics for a worker."""
        async with self._lock:
            self.worker_metrics[worker.worker_id] = {
                'performance_score': worker.performance_score,
                'active_tasks': worker.active_tasks,
                'max_tasks': worker.max_concurrent_tasks,
                'last_updated': datetime.now()
            }

    def set_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """Change the load balancing strategy."""
        self.strategy = strategy
        logger.info(f"Load balancing strategy changed to: {strategy.value}")

    def set_load_balancing_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """Change the load balancing strategy for the processor."""
        self.load_balancer.set_strategy(strategy)
        logger.info(f"Load balancing strategy changed to: {strategy.value}")

    def get_load_balancing_strategy(self) -> LoadBalancingStrategy:
        """Get the current load balancing strategy."""
        return self.load_balancer.strategy

    def get_queue_status(self) -> Dict[str, Any]:
        """Get detailed queue status information."""
        return {
            'queue_length': self.processing_stats['queue_length'],
            'priority_distribution': self._get_priority_distribution(),
            'oldest_task_age': self._get_oldest_task_age(),
            'queue_efficiency': self._calculate_queue_efficiency()
        }

    def _get_priority_distribution(self) -> Dict[str, int]:
        """Get distribution of tasks by priority level."""
        # This would require tracking priority distribution in the queue
        # For now, return a placeholder
        return {
            'critical': 0,
            'high': 0,
            'normal': 0,
            'low': 0
        }

    def _get_oldest_task_age(self) -> Optional[float]:
        """Get age of the oldest task in the queue."""
        # This would require tracking task ages
        # For now, return None
        return None

    def _calculate_queue_efficiency(self) -> float:
        """Calculate queue processing efficiency."""
        queue_length = self.processing_stats['queue_length']
        active_workers = self.processing_stats['active_workers']

        if active_workers == 0:
            return 0.0

        # Simplified efficiency calculation
        efficiency = min(1.0, active_workers / max(1, active_workers + queue_length))
        return efficiency


class DistributedProcessor:
    """Intelligent distributed processing system for analysis tasks."""

    def __init__(self, max_workers: int = 10, enable_process_pool: bool = True,
                 load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE):
        """Initialize the distributed processor."""
        self.max_workers = max_workers
        self.enable_process_pool = enable_process_pool
        self.workers: Dict[str, Worker] = {}
        self.tasks: Dict[str, DistributedTask] = {}
        self.task_queue: PriorityQueue = PriorityQueue()
        self.result_queue: asyncio.Queue = asyncio.Queue()
        self.task_handlers: Dict[str, Callable] = {}

        # Load balancing components
        self.load_balancer = LoadBalancer(strategy=load_balancing_strategy)
        self.processing_history = []

        # Thread/process pools
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers) if enable_process_pool else None

        # Synchronization
        self.task_lock = asyncio.Lock()
        self.worker_lock = asyncio.Lock()

        # Monitoring
        self.processing_stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'active_workers': 0,
            'avg_processing_time': 0.0,
            'throughput_per_minute': 0.0,
            'queue_length': 0,
            'load_balancing_efficiency': 0.0
        }

        # Initialize default workers
        self._initialize_workers()

        # Register default task handlers
        self._register_default_handlers()

        logger.info(f"Distributed processor initialized with {max_workers} max workers using {load_balancing_strategy.value} strategy")

    def _initialize_workers(self) -> None:
        """Initialize default worker instances."""
        for i in range(self.max_workers):
            worker_id = f"worker-{i+1}"
            worker = Worker(
                worker_id=worker_id,
                capabilities={"general", "analysis", "processing"},
                max_concurrent_tasks=3
            )
            self.workers[worker_id] = worker

        self.processing_stats['active_workers'] = self.max_workers

    def _register_default_handlers(self) -> None:
        """Register default task handlers."""
        self.task_handlers.update({
            'semantic_similarity': self._handle_semantic_similarity_task,
            'sentiment_analysis': self._handle_sentiment_analysis_task,
            'content_quality': self._handle_content_quality_task,
            'trend_analysis': self._handle_trend_analysis_task,
            'risk_assessment': self._handle_risk_assessment_task,
            'cross_repository': self._handle_cross_repository_task,
            'batch_analysis': self._handle_batch_analysis_task,
            'data_processing': self._handle_data_processing_task
        })

    async def submit_task(self, task_type: str, data: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.NORMAL,
                         dependencies: Optional[List[str]] = None) -> str:
        """Submit a task for distributed processing."""
        task_id = str(uuid.uuid4())

        task = DistributedTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            data=data,
            dependencies=dependencies or []
        )

        async with self.task_lock:
            self.tasks[task_id] = task
            self.processing_stats['total_tasks'] += 1

        # Add to priority queue with appropriate priority level
        priority_level = priority.value
        await self.task_queue.put(task, priority_level)

        logger.info(f"Task {task_id} ({task_type}) submitted for processing with priority {priority.name}")
        return task_id

    async def submit_batch_tasks(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Submit multiple tasks for batch processing."""
        task_ids = []

        for task_data in tasks:
            task_id = await self.submit_task(
                task_type=task_data.get('task_type', 'general'),
                data=task_data.get('data', {}),
                priority=task_data.get('priority', TaskPriority.NORMAL),
                dependencies=task_data.get('dependencies', [])
            )
            task_ids.append(task_id)

        logger.info(f"Batch of {len(tasks)} tasks submitted")
        return task_ids

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a distributed task."""
        async with self.task_lock:
            task = self.tasks.get(task_id)
            if not task:
                return None

            return {
                'task_id': task.task_id,
                'task_type': task.task_type,
                'status': task.status.value,
                'priority': task.priority.value,
                'progress': task.progress,
                'created_at': task.created_at.isoformat(),
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'assigned_worker': task.assigned_worker,
                'error_message': task.error_message,
                'estimated_completion': task.estimated_completion.isoformat() if task.estimated_completion else None
            }

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a distributed task."""
        async with self.task_lock:
            task = self.tasks.get(task_id)
            if not task or task.is_completed():
                return False

            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()

            logger.info(f"Task {task_id} cancelled")
            return True

    async def get_worker_status(self) -> Dict[str, Any]:
        """Get status of all workers."""
        async with self.worker_lock:
            workers_status = {}
            for worker_id, worker in self.workers.items():
                workers_status[worker_id] = {
                    'status': worker.status.value,
                    'current_task': worker.current_task,
                    'active_tasks': worker.active_tasks,
                    'tasks_completed': worker.tasks_completed,
                    'tasks_failed': worker.tasks_failed,
                    'performance_score': worker.performance_score,
                    'capabilities': list(worker.capabilities),
                    'last_heartbeat': worker.last_heartbeat.isoformat()
                }

            return {
                'workers': workers_status,
                'total_workers': len(self.workers),
                'available_workers': sum(1 for w in self.workers.values() if w.is_available()),
                'busy_workers': sum(1 for w in self.workers.values() if w.status == WorkerStatus.BUSY)
            }

    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.processing_stats.copy()

    async def process_task_queue(self) -> None:
        """Main task processing loop with load balancing."""
        while True:
            try:
                # Get next task from priority queue
                task = await self.task_queue.get()

                if task:
                    # Process task asynchronously
                    asyncio.create_task(self._process_task(task))

                # Update queue length in stats
                queue_size = await self.task_queue.size()
                self.processing_stats['queue_length'] = queue_size

            except Exception as e:
                logger.error(f"Error in task processing loop: {e}")
                await asyncio.sleep(1)

    async def _process_task(self, task: DistributedTask) -> None:
        """Process a single task with load balancing."""
        task_id = task.task_id

        async with self.task_lock:
            if task.is_completed():
                return

            # Find available worker using load balancer
            available_workers = [w for w in self.workers.values() if w.is_available()]
            worker = await self.load_balancer.select_worker(task, available_workers)

            if not worker:
                # No worker available, re-queue task with same priority
                await asyncio.sleep(5)
                priority_level = task.priority.value
                await self.task_queue.put(task, priority_level)
                return

            # Update task and worker status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.assigned_worker = worker.worker_id
            worker.status = WorkerStatus.BUSY
            worker.current_task = task_id
            worker.active_tasks += 1

        try:
            # Execute task
            result = await self._execute_task(task)

            # Calculate processing time for performance tracking
            processing_time = (datetime.now() - task.started_at).total_seconds()

            # Update task with result
            async with self.task_lock:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = result
                task.progress = 1.0

                # Update worker stats and performance
                worker.tasks_completed += 1
                worker.active_tasks -= 1
                worker.current_task = None
                if worker.active_tasks == 0:
                    worker.status = WorkerStatus.AVAILABLE

                # Update worker performance score based on processing time
                self._update_worker_performance(worker, processing_time, task.task_type)

                # Update processing stats
                self.processing_stats['completed_tasks'] += 1
                self._update_processing_stats(processing_time)

            # Update load balancer with worker metrics
            await self.load_balancer.update_worker_metrics(worker)

            logger.info(f"Task {task_id} completed successfully in {processing_time:.2f}s")

        except Exception as e:
            # Handle task failure
            async with self.task_lock:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now()
                task.retry_count += 1

                # Update worker stats
                worker.tasks_failed += 1
                worker.active_tasks -= 1
                worker.current_task = None
                if worker.active_tasks == 0:
                    worker.status = WorkerStatus.AVAILABLE

                # Penalize worker performance for failure
                worker.performance_score = max(0.1, worker.performance_score * 0.9)

                # Update processing stats
                self.processing_stats['failed_tasks'] += 1

            logger.error(f"Task {task_id} failed: {e}")

            # Retry if appropriate
            if task.should_retry():
                logger.info(f"Retrying task {task_id} (attempt {task.retry_count})")
                await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
                priority_level = task.priority.value
                await self.task_queue.put(task, priority_level)

    def _update_worker_performance(self, worker: Worker, processing_time: float, task_type: str) -> None:
        """Update worker performance score based on task completion."""
        # Calculate expected processing time (this would be learned over time)
        expected_time = self._get_expected_processing_time(task_type)

        if expected_time > 0:
            # Performance ratio (lower is better)
            performance_ratio = processing_time / expected_time

            # Update performance score using exponential moving average
            alpha = 0.1  # Learning rate
            worker.performance_score = (1 - alpha) * worker.performance_score + alpha * (1 / performance_ratio)

            # Clamp performance score between 0.1 and 2.0
            worker.performance_score = max(0.1, min(2.0, worker.performance_score))

    def _get_expected_processing_time(self, task_type: str) -> float:
        """Get expected processing time for a task type based on historical data."""
        # This is a simple implementation - in practice, this would be learned from historical data
        expected_times = {
            'semantic_similarity': 2.0,
            'sentiment_analysis': 1.5,
            'content_quality': 3.0,
            'trend_analysis': 5.0,
            'risk_assessment': 4.0,
            'cross_repository': 10.0,
            'batch_analysis': 8.0,
            'data_processing': 1.0
        }

        return expected_times.get(task_type, 2.0)

    def _update_processing_stats(self, processing_time: float) -> None:
        """Update processing statistics with new task completion."""
        # Update average processing time
        completed_count = self.processing_stats['completed_tasks']
        current_avg = self.processing_stats['avg_processing_time']

        if completed_count == 1:
            self.processing_stats['avg_processing_time'] = processing_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.processing_stats['avg_processing_time'] = (1 - alpha) * current_avg + alpha * processing_time

        # Update throughput (tasks per minute)
        # This is a simplified calculation - in practice, you'd track over time windows
        if completed_count > 0:
            self.processing_stats['throughput_per_minute'] = completed_count / max(1, (time.time() - time.time()) / 60)

        # Update load balancing efficiency (simplified metric)
        total_workers = len(self.workers)
        active_workers = sum(1 for w in self.workers.values() if w.status == WorkerStatus.BUSY)
        if total_workers > 0:
            utilization = active_workers / total_workers
            self.processing_stats['load_balancing_efficiency'] = min(1.0, utilization * 1.2)  # Cap at 1.0

    async def _execute_task(self, task: DistributedTask) -> Dict[str, Any]:
        """Execute a task using appropriate handler."""
        handler = self.task_handlers.get(task.task_type)
        if not handler:
            raise ValueError(f"No handler found for task type: {task.task_type}")

        # Update progress
        task.progress = 0.1

        try:
            # Execute handler
            result = await handler(task.data)

            # Update progress
            task.progress = 0.9

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            raise

    # Task handlers
    async def _handle_semantic_similarity_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle semantic similarity analysis task."""
        # Import here to avoid circular imports
        from .semantic_analyzer import analyze_semantic_similarity

        documents = data.get('documents', [])
        return await analyze_semantic_similarity({
            'documents': documents,
            'threshold': data.get('threshold', 0.8)
        })

    async def _handle_sentiment_analysis_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle sentiment analysis task."""
        from .sentiment_analyzer import analyze_document_sentiment

        documents = data.get('documents', [])
        results = []

        for doc in documents:
            result = await analyze_document_sentiment({
                'content': doc.get('content', ''),
                'document_id': doc.get('id', '')
            })
            results.append(result)

        return {'sentiment_analysis': results}

    async def _handle_content_quality_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content quality assessment task."""
        from .content_quality_scorer import assess_document_quality

        documents = data.get('documents', [])
        results = []

        for doc in documents:
            result = await assess_document_quality({
                'content': doc.get('content', ''),
                'document_id': doc.get('id', '')
            })
            results.append(result)

        return {'quality_assessment': results}

    async def _handle_trend_analysis_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle trend analysis task."""
        from .trend_analyzer import analyze_document_trends

        document_data = data.get('document_data', {})
        return await analyze_document_trends(document_data)

    async def _handle_risk_assessment_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle risk assessment task."""
        from .risk_assessor import assess_document_risk

        document_data = data.get('document_data', {})
        return await assess_document_risk(document_data)

    async def _handle_cross_repository_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cross-repository analysis task."""
        from .cross_repository_analyzer import analyze_repositories

        repositories = data.get('repositories', [])
        return await analyze_repositories(repositories)

    async def _handle_batch_analysis_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle batch analysis task."""
        analysis_types = data.get('analysis_types', [])
        documents = data.get('documents', [])

        results = {}
        for analysis_type in analysis_types:
            if analysis_type == 'semantic_similarity':
                result = await self._handle_semantic_similarity_task({'documents': documents})
                results['semantic_similarity'] = result
            elif analysis_type == 'sentiment':
                result = await self._handle_sentiment_analysis_task({'documents': documents})
                results['sentiment'] = result
            elif analysis_type == 'quality':
                result = await self._handle_content_quality_task({'documents': documents})
                results['quality'] = result

        return results

    async def _handle_data_processing_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general data processing task."""
        operation = data.get('operation', 'process')
        input_data = data.get('input_data', [])

        # Simulate data processing
        processed_data = []
        for item in input_data:
            # Apply processing operation
            if operation == 'transform':
                processed_item = {k: v.upper() if isinstance(v, str) else v
                                for k, v in item.items()}
            elif operation == 'filter':
                condition = data.get('condition', {})
                if all(item.get(k) == v for k, v in condition.items()):
                    processed_item = item
                else:
                    continue
            else:
                processed_item = item

            processed_data.append(processed_item)

        return {
            'operation': operation,
            'input_count': len(input_data),
            'output_count': len(processed_data),
            'processed_data': processed_data
        }

    def register_task_handler(self, task_type: str, handler: Callable) -> None:
        """Register a custom task handler."""
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")

    async def scale_workers(self, target_count: int) -> bool:
        """Scale the number of workers up or down."""
        current_count = len(self.workers)

        if target_count > current_count:
            # Scale up
            for i in range(current_count, target_count):
                worker_id = f"worker-{i+1}"
                worker = Worker(
                    worker_id=worker_id,
                    capabilities={"general", "analysis", "processing"},
                    max_concurrent_tasks=3
                )
                self.workers[worker_id] = worker

        elif target_count < current_count:
            # Scale down (only remove idle workers)
            workers_to_remove = []
            for worker_id, worker in self.workers.items():
                if worker.is_available():
                    workers_to_remove.append(worker_id)
                    if len(workers_to_remove) >= current_count - target_count:
                        break

            for worker_id in workers_to_remove:
                del self.workers[worker_id]

        self.processing_stats['active_workers'] = len(self.workers)
        logger.info(f"Scaled workers from {current_count} to {len(self.workers)}")
        return True

    async def shutdown(self) -> None:
        """Shutdown the distributed processor."""
        logger.info("Shutting down distributed processor...")

        # Cancel all pending tasks
        async with self.task_lock:
            for task in self.tasks.values():
                if not task.is_completed():
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = datetime.now()

        # Shutdown thread/process pools
        self.thread_pool.shutdown(wait=True)
        if self.process_pool:
            self.process_pool.shutdown(wait=True)

        logger.info("Distributed processor shutdown complete")


# Global instance
distributed_processor = DistributedProcessor()


async def submit_distributed_task(task_type: str, data: Dict[str, Any],
                                priority: str = "normal") -> str:
    """Convenience function to submit a task to the distributed processor."""
    priority_map = {
        "low": TaskPriority.LOW,
        "normal": TaskPriority.NORMAL,
        "high": TaskPriority.HIGH,
        "critical": TaskPriority.CRITICAL
    }

    return await distributed_processor.submit_task(
        task_type=task_type,
        data=data,
        priority=priority_map.get(priority, TaskPriority.NORMAL)
    )


async def get_distributed_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get task status."""
    return await distributed_processor.get_task_status(task_id)
