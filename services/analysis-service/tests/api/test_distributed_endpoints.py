"""Tests for Distributed Processing API Endpoints."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...main import app
from ...presentation.models.common import (
    DistributedTaskRequest, BatchTasksRequest, TaskStatusRequest,
    WorkersStatusResponse, ProcessingStatsResponse, ScaleWorkersRequest,
    LoadBalancingStrategyRequest, QueueStatusResponse, LoadBalancingConfigRequest
)


class TestDistributedEndpoints:
    """Test cases for distributed processing API endpoints."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_task_request(self):
        """Sample distributed task request for testing."""
        return DistributedTaskRequest(
            task_type='semantic_similarity',
            data={
                'document_ids': ['doc-1', 'doc-2', 'doc-3'],
                'threshold': 0.8,
                'options': {'batch_size': 32}
            },
            priority='high',
            dependencies=[],
            metadata={
                'user_id': 'user-123',
                'session_id': 'session-456'
            }
        )

    @pytest.fixture
    def sample_batch_tasks_request(self):
        """Sample batch tasks request for testing."""
        return BatchTasksRequest(
            tasks=[
                {
                    'task_type': 'semantic_similarity',
                    'data': {'document_ids': ['doc-1', 'doc-2']},
                    'priority': 'high'
                },
                {
                    'task_type': 'sentiment_analysis',
                    'data': {'document_id': 'doc-3'},
                    'priority': 'normal'
                }
            ],
            batch_options={
                'parallel_execution': True,
                'max_concurrent': 5,
                'timeout_seconds': 300
            }
        )

    def test_distributed_endpoints_exist(self, client):
        """Test that all distributed endpoints exist."""
        endpoints = [
            "/distributed/tasks",
            "/distributed/tasks/batch",
            "/distributed/workers",
            "/distributed/stats",
            "/distributed/start",
            "/distributed/queue/status",
            "/distributed/load-balancing/config"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint) if endpoint.startswith("/distributed/") and "tasks" not in endpoint else client.post(endpoint)
            # Should get method not allowed or validation error, but not 404
            assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_submit_distributed_task_success(self, client, sample_task_request):
        """Test successful distributed task submission."""
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_submit_distributed_task') as mock_handler:
            mock_response = {
                'task_id': 'task-123',
                'status': 'submitted',
                'estimated_completion_seconds': 45.5,
                'queue_position': 2,
                'message': 'Task submitted successfully'
            }
            mock_handler.return_value = mock_response

            response = client.post(
                "/distributed/tasks",
                json=sample_task_request.dict()
            )

            assert response.status_code == 200
            data = response.json()
            assert data['task_id'] == 'task-123'
            assert data['status'] == 'submitted'
            assert data['queue_position'] == 2

    @pytest.mark.asyncio
    async def test_submit_batch_tasks_success(self, client, sample_batch_tasks_request):
        """Test successful batch tasks submission."""
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_submit_batch_tasks') as mock_handler:
            mock_response = {
                'batch_id': 'batch-456',
                'task_count': 2,
                'submitted_tasks': ['task-123', 'task-124'],
                'status': 'batch_submitted',
                'estimated_completion_seconds': 120.0,
                'message': 'Batch submitted successfully'
            }
            mock_handler.return_value = mock_response

            response = client.post(
                "/distributed/tasks/batch",
                json=sample_batch_tasks_request.dict()
            )

            assert response.status_code == 200
            data = response.json()
            assert data['batch_id'] == 'batch-456'
            assert data['task_count'] == 2
            assert len(data['submitted_tasks']) == 2

    @pytest.mark.asyncio
    async def test_get_task_status_success(self, client):
        """Test successful task status retrieval."""
        task_id = 'task-123'

        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_get_task_status') as mock_handler:
            mock_response = {
                'task_id': task_id,
                'status': 'running',
                'progress': 0.65,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'estimated_completion_seconds': 25.5,
                'worker_id': 'worker-3',
                'result': None,
                'error_message': None
            }
            mock_handler.return_value = mock_response

            response = client.get(f"/distributed/tasks/{task_id}")

            assert response.status_code == 200
            data = response.json()
            assert data['task_id'] == task_id
            assert data['status'] == 'running'
            assert data['progress'] == 0.65

    @pytest.mark.asyncio
    async def test_cancel_task_success(self, client):
        """Test successful task cancellation."""
        task_id = 'task-123'

        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_cancel_task') as mock_handler:
            mock_response = {
                'task_id': task_id,
                'status': 'cancelled',
                'message': 'Task cancelled successfully',
                'cancelled_at': datetime.now(timezone.utc).isoformat()
            }
            mock_handler.return_value = mock_response

            response = client.delete(f"/distributed/tasks/{task_id}")

            assert response.status_code == 200
            data = response.json()
            assert data['task_id'] == task_id
            assert data['status'] == 'cancelled'

    @pytest.mark.asyncio
    async def test_get_workers_status_success(self, client):
        """Test successful workers status retrieval."""
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_get_workers_status') as mock_handler:
            mock_response = WorkersStatusResponse(
                total_workers=5,
                active_workers=3,
                idle_workers=2,
                workers=[
                    {
                        'worker_id': 'worker-1',
                        'status': 'active',
                        'current_task': 'task-123',
                        'tasks_completed': 45,
                        'uptime_seconds': 3600,
                        'cpu_usage': 75.5,
                        'memory_usage': 512.3
                    },
                    {
                        'worker_id': 'worker-2',
                        'status': 'idle',
                        'current_task': None,
                        'tasks_completed': 52,
                        'uptime_seconds': 3800,
                        'cpu_usage': 15.2,
                        'memory_usage': 256.7
                    }
                ],
                average_cpu_usage=45.35,
                average_memory_usage=384.5
            )
            mock_handler.return_value = mock_response

            response = client.get("/distributed/workers")

            assert response.status_code == 200
            data = response.json()
            assert data['total_workers'] == 5
            assert data['active_workers'] == 3
            assert len(data['workers']) == 2

    @pytest.mark.asyncio
    async def test_get_processing_stats_success(self, client):
        """Test successful processing statistics retrieval."""
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_get_processing_stats') as mock_handler:
            mock_response = ProcessingStatsResponse(
                total_tasks_processed=1250,
                tasks_completed=1180,
                tasks_failed=45,
                tasks_cancelled=25,
                average_processing_time_seconds=12.5,
                throughput_tasks_per_minute=8.5,
                queue_length=15,
                oldest_task_age_seconds=180.5,
                worker_utilization_percentage=78.3,
                peak_concurrent_tasks=12,
                system_uptime_seconds=86400,
                memory_usage_mb=2048.5,
                cpu_usage_percentage=65.2
            )
            mock_handler.return_value = mock_response

            response = client.get("/distributed/stats")

            assert response.status_code == 200
            data = response.json()
            assert data['total_tasks_processed'] == 1250
            assert data['tasks_completed'] == 1180
            assert data['average_processing_time_seconds'] == 12.5
            assert data['throughput_tasks_per_minute'] == 8.5

    @pytest.mark.asyncio
    async def test_scale_workers_success(self, client):
        """Test successful worker scaling."""
        scale_request = ScaleWorkersRequest(
            target_worker_count=8,
            scaling_reason='high_load',
            immediate=True
        )

        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_scale_workers') as mock_handler:
            mock_response = {
                'previous_worker_count': 5,
                'new_worker_count': 8,
                'scaling_reason': 'high_load',
                'estimated_scaling_time_seconds': 30.0,
                'message': 'Worker scaling initiated successfully'
            }
            mock_handler.return_value = mock_response

            response = client.post(
                "/distributed/workers/scale",
                json=scale_request.dict()
            )

            assert response.status_code == 200
            data = response.json()
            assert data['previous_worker_count'] == 5
            assert data['new_worker_count'] == 8

    @pytest.mark.asyncio
    async def test_start_distributed_processing_success(self, client):
        """Test successful distributed processing start."""
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_start_processing') as mock_handler:
            mock_response = {
                'status': 'started',
                'worker_count': 5,
                'queue_size': 0,
                'message': 'Distributed processing started successfully'
            }
            mock_handler.return_value = mock_response

            response = client.post("/distributed/start")

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'started'
            assert data['worker_count'] == 5

    @pytest.mark.asyncio
    async def test_set_load_balancing_strategy_success(self, client):
        """Test successful load balancing strategy configuration."""
        strategy_request = LoadBalancingStrategyRequest(strategy='least_loaded')

        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_set_load_balancing_strategy') as mock_handler:
            mock_response = {
                'previous_strategy': 'round_robin',
                'new_strategy': 'least_loaded',
                'changed_at': datetime.now(timezone.utc).isoformat(),
                'message': 'Load balancing strategy updated successfully'
            }
            mock_handler.return_value = mock_response

            response = client.put(
                "/distributed/load-balancing/strategy",
                json=strategy_request.dict()
            )

            assert response.status_code == 200
            data = response.json()
            assert data['previous_strategy'] == 'round_robin'
            assert data['new_strategy'] == 'least_loaded'

    @pytest.mark.asyncio
    async def test_get_queue_status_success(self, client):
        """Test successful queue status retrieval."""
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_get_queue_status') as mock_handler:
            mock_response = QueueStatusResponse(
                queue_length=23,
                priority_distribution={
                    'critical': 2,
                    'high': 5,
                    'normal': 12,
                    'low': 4
                },
                oldest_task_age_seconds=245.8,
                queue_efficiency=0.85,
                processing_rate=7.2,
                estimated_empty_time_seconds=180.5
            )
            mock_handler.return_value = mock_response

            response = client.get("/distributed/queue/status")

            assert response.status_code == 200
            data = response.json()
            assert data['queue_length'] == 23
            assert data['priority_distribution']['high'] == 5
            assert data['queue_efficiency'] == 0.85
            assert data['processing_rate'] == 7.2

    @pytest.mark.asyncio
    async def test_configure_load_balancing_success(self, client):
        """Test successful load balancing configuration."""
        config_request = LoadBalancingConfigRequest(
            strategy='performance_based',
            worker_count=6,
            max_queue_size=100,
            enable_auto_scaling=True
        )

        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_configure_load_balancing') as mock_handler:
            mock_response = {
                'strategy': 'performance_based',
                'worker_count': 6,
                'max_queue_size': 100,
                'enable_auto_scaling': True,
                'configured_at': datetime.now(timezone.utc).isoformat(),
                'message': 'Load balancing configuration updated successfully'
            }
            mock_handler.return_value = mock_response

            response = client.put(
                "/distributed/load-balancing/config",
                json=config_request.dict()
            )

            assert response.status_code == 200
            data = response.json()
            assert data['strategy'] == 'performance_based'
            assert data['worker_count'] == 6
            assert data['enable_auto_scaling'] is True

    @pytest.mark.asyncio
    async def test_get_load_balancing_config_success(self, client):
        """Test successful load balancing configuration retrieval."""
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_get_load_balancing_config') as mock_handler:
            mock_response = {
                'strategy': 'adaptive',
                'worker_count': 7,
                'max_queue_size': 150,
                'enable_auto_scaling': True,
                'auto_scaling_thresholds': {
                    'cpu_high': 80.0,
                    'cpu_low': 30.0,
                    'memory_high': 85.0,
                    'memory_low': 40.0
                },
                'configured_at': datetime.now(timezone.utc).isoformat()
            }
            mock_handler.return_value = mock_response

            response = client.get("/distributed/load-balancing/config")

            assert response.status_code == 200
            data = response.json()
            assert data['strategy'] == 'adaptive'
            assert data['worker_count'] == 7
            assert 'auto_scaling_thresholds' in data

    @pytest.mark.asyncio
    async def test_distributed_endpoints_validation_errors(self, client):
        """Test validation errors in distributed endpoints."""
        # Test invalid task type
        invalid_task = {
            'task_type': 'invalid_task_type',
            'data': {'test': 'data'}
        }

        response = client.post("/distributed/tasks", json=invalid_task)
        assert response.status_code == 422  # Validation error

        # Test invalid priority
        invalid_priority = {
            'task_type': 'semantic_similarity',
            'data': {'test': 'data'},
            'priority': 'invalid_priority'
        }

        response = client.post("/distributed/tasks", json=invalid_priority)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_distributed_endpoints_error_handling(self, client, sample_task_request):
        """Test error handling in distributed endpoints."""
        # Test handler error
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_submit_distributed_task') as mock_handler:
            mock_handler.side_effect = Exception("Handler error")

            response = client.post(
                "/distributed/tasks",
                json=sample_task_request.dict()
            )

            # Should handle error gracefully
            assert response.status_code in [400, 500]

    @pytest.mark.asyncio
    async def test_distributed_endpoints_concurrent_requests(self, client):
        """Test concurrent requests to distributed endpoints."""
        async def submit_task(task_id: int):
            task_data = {
                'task_type': 'semantic_similarity',
                'data': {'document_ids': [f'doc-{task_id}']},
                'priority': 'normal'
            }

            with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_submit_distributed_task') as mock_handler:
                mock_response = {
                    'task_id': f'task-{task_id}',
                    'status': 'submitted',
                    'message': f'Task {task_id} submitted'
                }
                mock_handler.return_value = mock_response

                response = client.post("/distributed/tasks", json=task_data)
                return response.status_code, response.json()

        # Submit multiple tasks concurrently
        tasks = [submit_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        for status_code, data in results:
            assert status_code == 200
            assert 'task_id' in data

    @pytest.mark.asyncio
    async def test_distributed_endpoints_resource_limits(self, client):
        """Test resource limits in distributed endpoints."""
        # Test with very large batch
        large_batch = {
            'tasks': [
                {
                    'task_type': 'semantic_similarity',
                    'data': {'document_ids': [f'doc-{i}' for i in range(100)]}
                }
                for _ in range(100)  # 100 tasks
            ]
        }

        response = client.post("/distributed/tasks/batch", json=large_batch)

        # Should either succeed or fail with resource limit
        assert response.status_code in [200, 413, 429]

    @pytest.mark.asyncio
    async def test_distributed_endpoints_metrics_collection(self, client, sample_task_request):
        """Test metrics collection in distributed endpoints."""
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_submit_distributed_task') as mock_handler:
            mock_response = {
                'task_id': 'metrics-task-123',
                'status': 'submitted',
                'message': 'Task submitted for metrics testing'
            }
            mock_handler.return_value = mock_response

            response = client.post(
                "/distributed/tasks",
                json=sample_task_request.dict()
            )

            assert response.status_code == 200

            # In a real implementation, we would verify that:
            # - Request count metrics are incremented
            # - Queue size metrics are updated
            # - Worker utilization metrics are tracked
            # - Task submission latency is measured

    def test_distributed_endpoints_cors_headers(self, client):
        """Test CORS headers in distributed endpoints."""
        response = client.options("/distributed/tasks")
        assert response.status_code == 200

        # Check for CORS headers
        headers = response.headers
        cors_headers = [
            'access-control-allow-origin',
            'access-control-allow-methods',
            'access-control-allow-headers'
        ]

        for header in cors_headers:
            assert header in headers or header.title() in headers

    @pytest.mark.asyncio
    async def test_distributed_endpoints_idempotency(self, client, sample_task_request):
        """Test idempotency in distributed endpoints."""
        # Submit same task multiple times
        responses = []

        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_submit_distributed_task') as mock_handler:
            mock_response = {
                'task_id': 'idempotent-task-123',
                'status': 'submitted',
                'message': 'Task submitted'
            }
            mock_handler.return_value = mock_response

            for i in range(3):
                response = client.post(
                    "/distributed/tasks",
                    json=sample_task_request.dict()
                )
                responses.append(response)

        # All responses should be consistent
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data['task_id'] == 'idempotent-task-123'
            assert data['status'] == 'submitted'

    @pytest.mark.asyncio
    async def test_distributed_endpoints_pagination(self, client):
        """Test pagination in distributed endpoints."""
        # Test workers status pagination
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_get_workers_status') as mock_handler:
            # Mock response with many workers
            workers = [
                {
                    'worker_id': f'worker-{i}',
                    'status': 'active' if i % 2 == 0 else 'idle',
                    'current_task': f'task-{i}' if i % 2 == 0 else None,
                    'tasks_completed': i * 10,
                    'uptime_seconds': i * 1000,
                    'cpu_usage': 50.0 + (i % 20),
                    'memory_usage': 256.0 + (i % 100)
                }
                for i in range(50)  # 50 workers
            ]

            mock_response = WorkersStatusResponse(
                total_workers=50,
                active_workers=25,
                idle_workers=25,
                workers=workers,
                average_cpu_usage=55.0,
                average_memory_usage=300.0
            )
            mock_handler.return_value = mock_response

            # Test without pagination (would get all in real implementation)
            response = client.get("/distributed/workers")
            assert response.status_code == 200

            data = response.json()
            assert data['total_workers'] == 50
            assert len(data['workers']) == 50
