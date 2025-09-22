"""Tests for Orchestrator Workflow Management Routes logging integration with LogCollectorClient."""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from services.shared.utilities.logging_client import LogCollectorClient


class TestOrchestratorWorkflowManagementLoggingIntegration:
    """Test Orchestrator Workflow Management routes logging integration with LogCollectorClient."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_logger_client(self):
        """Mock LogCollectorClient."""
        mock_client = AsyncMock(spec=LogCollectorClient)
        return mock_client

    @pytest.fixture(autouse=True)
    async def setup_logger_client(self, mock_logger_client):
        """Setup mock logger client for all tests."""
        # Patch the get_logger_client function in the workflow management routes
        with patch('services.orchestrator.presentation.api.workflow_management.routes.get_logger_client') as mock_get_client:
            mock_get_client.return_value = mock_logger_client
            yield

    @pytest.mark.asyncio
    async def test_workflow_creation_logging_success(self, client, mock_logger_client):
        """Test workflow creation endpoint logging on success."""
        mock_workflow = type('MockWorkflow', (), {
            'workflow_id': 'workflow_12345',
            'name': 'Test Workflow',
            'description': 'A test workflow',
            'workflow_type': 'data_processing',
            'status': 'created',
            'parameters': {'input_path': '/data', 'output_path': '/results'},
            'actions': [{'type': 'transform', 'config': {}}, {'type': 'validate', 'config': {}}],
            'tags': ['test', 'automation'],
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:00:00Z'
        })()

        mock_result = type('MockResult', (), {
            'success': True,
            'workflow': mock_workflow
        })()

        with patch('services.orchestrator.presentation.api.workflow_management.routes.container') as mock_container:
            mock_container.create_workflow_use_case.execute.return_value = mock_result

            workflow_request = {
                "name": "Test Workflow",
                "description": "A test workflow",
                "workflow_type": "data_processing",
                "parameters": {"input_path": "/data", "output_path": "/results"},
                "actions": [{"type": "transform", "config": {}}, {"type": "validate", "config": {}}],
                "tags": ["test", "automation"]
            }
            response = client.post("/api/v1/workflow-management", json=workflow_request)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and created
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check workflow creation events
            business_calls = mock_logger_client.log_business_event.call_args_list
            creation_started = next((call for call in business_calls
                                   if call[0][0] == 'workflow_creation_started'), None)
            workflow_created = next((call for call in business_calls
                                   if call[0][0] == 'workflow_created'), None)

            assert creation_started is not None
            assert workflow_created is not None

            started_data = creation_started[0][1]
            assert started_data['workflow_type'] == 'data_processing'
            assert started_data['workflow_name'] == 'Test Workflow'
            assert started_data['actions_count'] == 2
            assert started_data['parameters_count'] == 2
            assert started_data['tags_count'] == 2

            created_data = workflow_created[0][1]
            assert created_data['workflow_id'] == 'workflow_12345'
            assert created_data['success'] is True
            assert created_data['workflow_type'] == 'data_processing'
            assert created_data['actions_defined'] == 2

    @pytest.mark.asyncio
    async def test_workflow_execution_logging_success(self, client, mock_logger_client):
        """Test workflow execution endpoint logging on success."""
        workflow_id = "workflow_12345"
        mock_execution = type('MockExecution', (), {
            'execution_id': 'execution_67890',
            'workflow_id': workflow_id,
            'status': type('MockStatus', (), {'value': 'running'})(),
            'parameters': {'input_path': '/data'},
            'results': None,
            'started_at': '2024-01-15T10:05:00Z',
            'completed_at': None,
            'duration_seconds': 0,
            'error_message': None
        })()

        mock_result = type('MockResult', (), {
            'success': True,
            'execution': mock_execution
        })()

        with patch('services.orchestrator.presentation.api.workflow_management.routes.container') as mock_container:
            mock_container.execute_workflow_use_case.execute.return_value = mock_result

            execution_request = {
                "workflow_id": workflow_id,
                "parameters": {"input_path": "/data"},
                "user_id": "user123",
                "correlation_id": "corr_abc123",
                "priority": "normal"
            }
            response = client.post(f"/api/v1/workflow-management/{workflow_id}/execute", json=execution_request)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and initiated
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check workflow execution events
            business_calls = mock_logger_client.log_business_event.call_args_list
            execution_started = next((call for call in business_calls
                                    if call[0][0] == 'workflow_execution_started'), None)
            execution_initiated = next((call for call in business_calls
                                      if call[0][0] == 'workflow_execution_initiated'), None)

            assert execution_started is not None
            assert execution_initiated is not None

            started_data = execution_started[0][1]
            assert started_data['workflow_id'] == workflow_id
            assert started_data['execution_priority'] == 'normal'
            assert started_data['parameters_count'] == 1
            assert started_data['user_initiated'] is True
            assert started_data['correlation_tracking'] is True

            initiated_data = execution_initiated[0][1]
            assert initiated_data['workflow_id'] == workflow_id
            assert initiated_data['execution_id'] == 'execution_67890'
            assert initiated_data['success'] is True
            assert initiated_data['execution_status'] == 'running'

    @pytest.mark.asyncio
    async def test_workflow_retrieval_logging_success(self, client, mock_logger_client):
        """Test workflow retrieval endpoint logging on success."""
        workflow_id = "workflow_12345"
        mock_workflow = type('MockWorkflow', (), {
            'workflow_id': workflow_id,
            'name': 'Test Workflow',
            'description': 'A test workflow',
            'workflow_type': 'data_processing',
            'status': 'active',
            'parameters': {'input_path': '/data'},
            'actions': [{'type': 'transform', 'config': {}}],
            'tags': ['test'],
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:00:00Z'
        })()

        mock_result = type('MockResult', (), {
            'success': True,
            'workflow': mock_workflow
        })()

        with patch('services.orchestrator.presentation.api.workflow_management.routes.container') as mock_container:
            mock_container.get_workflow_use_case.execute.return_value = mock_result

            response = client.get(f"/api/v1/workflow-management/{workflow_id}")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check workflow retrieval events
            business_calls = mock_logger_client.log_business_event.call_args_list
            retrieval_started = next((call for call in business_calls
                                    if call[0][0] == 'workflow_retrieval_started'), None)
            workflow_retrieved = next((call for call in business_calls
                                     if call[0][0] == 'workflow_retrieved'), None)

            assert retrieval_started is not None
            assert workflow_retrieved is not None

            started_data = retrieval_started[0][1]
            assert started_data['workflow_id'] == workflow_id
            assert started_data['data_scope'] == 'workflow_configuration'
            assert started_data['workflow_cache_access'] is True

            retrieved_data = workflow_retrieved[0][1]
            assert retrieved_data['workflow_id'] == workflow_id
            assert retrieved_data['success'] is True
            assert retrieved_data['workflow_type'] == 'data_processing'
            assert retrieved_data['actions_count'] == 1

    @pytest.mark.asyncio
    async def test_workflows_listing_logging_with_filters(self, client, mock_logger_client):
        """Test workflows listing endpoint logging with filters."""
        mock_workflows = [
            type('MockWorkflow', (), {
                'workflow_id': 'wf1',
                'name': 'Workflow 1',
                'description': 'First workflow',
                'workflow_type': 'data_processing',
                'status': 'active',
                'parameters': {},
                'actions': [],
                'tags': ['test'],
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            })(),
            type('MockWorkflow', (), {
                'workflow_id': 'wf2',
                'name': 'Workflow 2',
                'description': 'Second workflow',
                'workflow_type': 'data_processing',
                'status': 'inactive',
                'parameters': {},
                'actions': [],
                'tags': ['prod'],
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            })()
        ]

        with patch('services.orchestrator.presentation.api.workflow_management.routes.container') as mock_container:
            mock_container.list_workflows_use_case.execute.return_value = mock_workflows

            response = client.get("/api/v1/workflow-management?workflow_type=data_processing&limit=10&offset=0")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and listed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check workflows listing events
            business_calls = mock_logger_client.log_business_event.call_args_list
            listing_started = next((call for call in business_calls
                                  if call[0][0] == 'workflows_listing_started'), None)
            workflows_listed = next((call for call in business_calls
                                   if call[0][0] == 'workflows_listed'), None)

            assert listing_started is not None
            assert workflows_listed is not None

            started_data = listing_started[0][1]
            assert started_data['filters_applied'] is True
            assert started_data['workflow_type_filter'] == 'data_processing'
            assert started_data['limit'] == 10
            assert started_data['offset'] == 0

            listed_data = workflows_listed[0][1]
            assert listed_data['workflows_returned'] == 2
            assert listed_data['filters_applied'] is True
            assert listed_data['total_available'] == 2

    @pytest.mark.asyncio
    async def test_executions_listing_logging_with_filters(self, client, mock_logger_client):
        """Test executions listing endpoint logging with workflow filter."""
        workflow_id = "workflow_12345"
        mock_executions = [
            type('MockExecution', (), {
                'execution_id': 'exec1',
                'workflow_id': workflow_id,
                'status': type('MockStatus', (), {'value': 'completed'})(),
                'parameters': {},
                'results': {'output': 'success'},
                'started_at': '2024-01-15T10:05:00Z',
                'completed_at': '2024-01-15T10:15:00Z',
                'duration_seconds': 600,
                'error_message': None
            })()
        ]

        mock_result = type('MockResult', (), {
            'success': True,
            'executions': mock_executions,
            'total': 1
        })()

        with patch('services.orchestrator.presentation.api.workflow_management.routes.container') as mock_container:
            mock_container.list_workflow_executions_use_case.execute.return_value = mock_result

            response = client.get(f"/api/v1/workflow-management/executions?workflow_id={workflow_id}&limit=10")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and listed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check executions listing events
            business_calls = mock_logger_client.log_business_event.call_args_list
            listing_started = next((call for call in business_calls
                                  if call[0][0] == 'executions_listing_started'), None)
            executions_listed = next((call for call in business_calls
                                    if call[0][0] == 'executions_listed'), None)

            assert listing_started is not None
            assert executions_listed is not None

            started_data = listing_started[0][1]
            assert started_data['filters_applied'] is True
            assert started_data['workflow_id_filter'] == workflow_id
            assert started_data['limit'] == 10

            listed_data = executions_listed[0][1]
            assert listed_data['executions_returned'] == 1
            assert listed_data['filters_applied'] is True
            assert listed_data['total_available'] == 1

    @pytest.mark.asyncio
    async def test_execution_detail_retrieval_logging_success(self, client, mock_logger_client):
        """Test execution detail retrieval endpoint logging on success."""
        execution_id = "execution_67890"
        workflow_id = "workflow_12345"

        mock_execution = type('MockExecution', (), {
            'execution_id': execution_id,
            'workflow_id': workflow_id,
            'status': type('MockStatus', (), {'value': 'completed'})(),
            'parameters': {'input_path': '/data'},
            'results': {'output_path': '/results', 'records_processed': 1000},
            'started_at': '2024-01-15T10:05:00Z',
            'completed_at': '2024-01-15T10:15:00Z',
            'duration_seconds': 600,
            'error_message': None
        })()

        mock_result = type('MockResult', (), {
            'success': True,
            'execution': mock_execution
        })()

        with patch('services.orchestrator.presentation.api.workflow_management.routes.container') as mock_container:
            mock_container.get_workflow_execution_use_case.execute.return_value = mock_result

            response = client.get(f"/api/v1/workflow-management/executions/{execution_id}")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check execution detail events
            business_calls = mock_logger_client.log_business_event.call_args_list
            detail_started = next((call for call in business_calls
                                 if call[0][0] == 'execution_detail_started'), None)
            detail_retrieved = next((call for call in business_calls
                                   if call[0][0] == 'execution_detail_retrieved'), None)

            assert detail_started is not None
            assert detail_retrieved is not None

            started_data = detail_started[0][1]
            assert started_data['execution_id'] == execution_id
            assert started_data['data_scope'] == 'single_execution_lifecycle'

            retrieved_data = detail_retrieved[0][1]
            assert retrieved_data['execution_id'] == execution_id
            assert retrieved_data['success'] is True
            assert retrieved_data['workflow_id'] == workflow_id
            assert retrieved_data['execution_status'] == 'completed'
            assert retrieved_data['execution_duration'] == 600
            assert retrieved_data['has_results'] is True

    @pytest.mark.asyncio
    async def test_workflow_creation_logging_failure(self, client, mock_logger_client):
        """Test workflow creation endpoint logging on validation failure."""
        mock_result = type('MockResult', (), {
            'success': False,
            'error_message': 'Invalid workflow configuration: missing required actions'
        })()

        with patch('services.orchestrator.presentation.api.workflow_management.routes.container') as mock_container:
            mock_container.create_workflow_use_case.execute.return_value = mock_result

            workflow_request = {
                "name": "Invalid Workflow",
                "description": "Missing actions",
                "workflow_type": "data_processing",
                "parameters": {},
                "actions": [],  # Empty actions cause validation failure
                "tags": []
            }
            response = client.post("/api/v1/workflow-management", json=workflow_request)
            assert response.status_code == 400

            # Verify error logging
            assert mock_logger_client.log_business_event.call_count >= 2  # started and failed

            # Check failure event
            business_calls = mock_logger_client.log_business_event.call_args_list
            workflow_failed = next((call for call in business_calls
                                  if call[0][0] == 'workflow_creation_failed'), None)
            assert workflow_failed is not None

            failed_data = workflow_failed[0][1]
            assert failed_data['workflow_type'] == 'data_processing'
            assert failed_data['workflow_name'] == 'Invalid Workflow'
            assert failed_data['error_message'] == 'Invalid workflow configuration: missing required actions'
            assert failed_data['validation_failed'] is True

    @pytest.mark.asyncio
    async def test_workflow_execution_logging_id_mismatch(self, client, mock_logger_client):
        """Test workflow execution endpoint logging on ID mismatch."""
        workflow_id = "workflow_12345"

        execution_request = {
            "workflow_id": "different_workflow_id",  # Different from path
            "parameters": {},
            "priority": "normal"
        }
        response = client.post(f"/api/v1/workflow-management/{workflow_id}/execute", json=execution_request)
        assert response.status_code == 400

        # Verify logging calls
        business_calls = mock_logger_client.log_business_event.call_args_list
        execution_rejected = next((call for call in business_calls
                                 if call[0][0] == 'workflow_execution_rejected'), None)
        assert execution_rejected is not None

        rejected_data = execution_rejected[0][1]
        assert rejected_data['workflow_id'] == workflow_id
        assert rejected_data['error_type'] == 'workflow_id_mismatch'
        assert rejected_data['request_workflow_id'] == 'different_workflow_id'
        assert rejected_data['path_workflow_id'] == workflow_id

    @pytest.mark.asyncio
    async def test_request_ids_generated_uniquely(self, client, mock_logger_client):
        """Test that all endpoints generate unique request IDs."""
        request_ids = set()

        with patch('services.orchestrator.presentation.api.workflow_management.routes.container') as mock_container:
            # Mock successful responses
            mock_workflow = type('MockWorkflow', (), {
                'workflow_id': 'test',
                'name': 'Test',
                'description': 'Test workflow',
                'workflow_type': 'test',
                'status': 'active',
                'parameters': {},
                'actions': [],
                'tags': [],
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            })()

            mock_execution = type('MockExecution', (), {
                'execution_id': 'exec_test',
                'workflow_id': 'test',
                'status': type('MockStatus', (), {'value': 'running'})(),
                'parameters': {},
                'results': None,
                'started_at': '2024-01-15T10:05:00Z',
                'completed_at': None,
                'duration_seconds': 0,
                'error_message': None
            })()

            mock_result = type('MockResult', (), {
                'success': True,
                'workflow': mock_workflow,
                'execution': mock_execution,
                'executions': [mock_execution],
                'total': 1
            })()

            # Mock all use cases
            mock_container.create_workflow_use_case.execute.return_value = mock_result
            mock_container.execute_workflow_use_case.execute.return_value = mock_result
            mock_container.get_workflow_use_case.execute.return_value = mock_result
            mock_container.list_workflows_use_case.execute.return_value = [mock_workflow]
            mock_container.list_workflow_executions_use_case.execute.return_value = mock_result
            mock_container.get_workflow_execution_use_case.execute.return_value = mock_result

            # Make requests to different endpoints
            client.post("/api/v1/workflow-management", json={
                "name": "Test", "workflow_type": "test", "actions": []
            })
            client.post("/api/v1/workflow-management/test/execute", json={
                "workflow_id": "test", "parameters": {}
            })
            client.get("/api/v1/workflow-management/test")
            client.get("/api/v1/workflow-management?page=1&page_size=10")
            client.get("/api/v1/workflow-management/executions?page=1&page_size=10")
            client.get("/api/v1/workflow-management/executions/exec_test")

            # Collect request IDs from business events
            business_calls = mock_logger_client.log_business_event.call_args_list
            for call in business_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get('request_id')
                    if request_id:
                        request_ids.add(request_id)

        # Should have collected multiple unique request IDs
        assert len(request_ids) >= 6  # At least one per endpoint

        # All request IDs should follow expected patterns
        for request_id in request_ids:
            assert any(prefix in request_id for prefix in [
                'workflow_creation_', 'workflow_execution_', 'workflow_retrieval_',
                'workflows_listing_', 'executions_listing_', 'execution_detail_'
            ])

    @pytest.mark.asyncio
    async def test_performance_metrics_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        mock_workflow = type('MockWorkflow', (), {
            'workflow_id': 'test',
            'name': 'Test',
            'description': 'Test workflow',
            'workflow_type': 'test',
            'status': 'active',
            'parameters': {},
            'actions': [],
            'tags': [],
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:00:00Z'
        })()

        mock_result = type('MockResult', (), {
            'success': True,
            'workflow': mock_workflow
        })()

        with patch('services.orchestrator.presentation.api.workflow_management.routes.container') as mock_container:
            mock_container.get_workflow_use_case.execute.return_value = mock_result

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            response = client.get("/api/v1/workflow-management/test")
            assert response.status_code == 200

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            retrieval_perf = next((call for call in perf_calls if call[0][0] == 'workflow_retrieval'), None)
            assert retrieval_perf is not None

            processing_time = retrieval_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Patch get_logger_client to return None
        with patch('services.orchestrator.presentation.api.workflow_management.routes.get_logger_client') as mock_get_client:
            mock_get_client.return_value = None

            with patch('services.orchestrator.presentation.api.workflow_management.routes.container') as mock_container:
                mock_workflows = [
                    type('MockWorkflow', (), {
                        'workflow_id': 'wf1',
                        'name': 'Test',
                        'description': 'Test workflow',
                        'workflow_type': 'test',
                        'status': 'active',
                        'parameters': {},
                        'actions': [],
                        'tags': [],
                        'created_at': '2024-01-15T10:00:00Z',
                        'updated_at': '2024-01-15T10:00:00Z'
                    })()
                ]
                mock_container.list_workflows_use_case.execute.return_value = mock_workflows

                # Make request - should still work without logging
                response = client.get("/api/v1/workflow-management?page=1&page_size=10")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_business_events_comprehensive_coverage(self, client, mock_logger_client):
        """Test that all major business events are logged across workflow management endpoints."""
        expected_events = {
            # Workflow lifecycle events
            'workflow_creation_started', 'workflow_created', 'workflow_creation_failed',
            'workflow_creation_error',

            # Workflow execution events
            'workflow_execution_started', 'workflow_execution_initiated', 'workflow_execution_failed',
            'workflow_execution_rejected', 'workflow_execution_error',

            # Workflow retrieval events
            'workflow_retrieval_started', 'workflow_retrieved', 'workflow_not_found',
            'workflow_retrieval_failed', 'workflow_retrieval_error',

            # Workflow inventory events
            'workflows_listing_started', 'workflows_listed', 'workflows_listing_failed',

            # Execution history events
            'executions_listing_started', 'executions_listed', 'executions_listing_failed',

            # Execution monitoring events
            'execution_detail_started', 'execution_detail_retrieved', 'execution_not_found',
            'execution_detail_failed', 'execution_detail_error'
        }

        # Test a representative sample of endpoints to verify event logging
        with patch('services.orchestrator.presentation.api.workflow_management.routes.container') as mock_container:
            # Mock successful responses
            mock_workflow = type('MockWorkflow', (), {
                'workflow_id': 'test',
                'name': 'Test',
                'description': 'Test workflow',
                'workflow_type': 'test',
                'status': 'active',
                'parameters': {},
                'actions': [],
                'tags': [],
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            })()

            mock_execution = type('MockExecution', (), {
                'execution_id': 'exec_test',
                'workflow_id': 'test',
                'status': type('MockStatus', (), {'value': 'running'})(),
                'parameters': {},
                'results': None,
                'started_at': '2024-01-15T10:05:00Z',
                'completed_at': None,
                'duration_seconds': 0,
                'error_message': None
            })()

            mock_result = type('MockResult', (), {
                'success': True,
                'workflow': mock_workflow,
                'execution': mock_execution,
                'executions': [mock_execution],
                'total': 1
            })()

            # Mock all use cases
            mock_container.create_workflow_use_case.execute.return_value = mock_result
            mock_container.execute_workflow_use_case.execute.return_value = mock_result
            mock_container.get_workflow_use_case.execute.return_value = mock_result
            mock_container.list_workflows_use_case.execute.return_value = [mock_workflow]
            mock_container.list_workflow_executions_use_case.execute.return_value = mock_result
            mock_container.get_workflow_execution_use_case.execute.return_value = mock_result

            # Make requests to key endpoints
            client.post("/api/v1/workflow-management", json={
                "name": "Test", "workflow_type": "test", "actions": []
            })
            client.post("/api/v1/workflow-management/test/execute", json={
                "workflow_id": "test", "parameters": {}
            })
            client.get("/api/v1/workflow-management/test")
            client.get("/api/v1/workflow-management?page=1&page_size=10")
            client.get("/api/v1/workflow-management/executions?page=1&page_size=10")
            client.get("/api/v1/workflow-management/executions/exec_test")

            # Check which events were actually logged
            business_calls = mock_logger_client.log_business_event.call_args_list
            logged_events = {call[0][0] for call in business_calls}

            # Verify we logged some key events (not all, as some require specific conditions)
            key_events_logged = logged_events.intersection({
                'workflow_creation_started', 'workflow_created',
                'workflow_execution_started', 'workflow_execution_initiated',
                'workflow_retrieval_started', 'workflow_retrieved',
                'workflows_listing_started', 'workflows_listed',
                'executions_listing_started', 'executions_listed',
                'execution_detail_started', 'execution_detail_retrieved'
            })

            assert len(key_events_logged) >= 12  # Should have logged most key events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
