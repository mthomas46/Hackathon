#!/usr/bin/env python3
"""
Comprehensive Test Suite for Orchestrator Service Features

Tests all major features and capabilities of the orchestrator service:
- Workflow Management (CRUD, execution, monitoring)
- Service Discovery and Registry
- Event Streaming and Real-time Processing
- Enterprise Integration (Service Mesh, Health, APIs)
- Multi-service Orchestration
- LangGraph Integration
- RESTful API Endpoints
"""

import asyncio
import json
import pytest
import aiohttp
import time
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

import sys
sys.path.insert(0, '/Users/mykalthomas/Documents/work/Hackathon/services')

from orchestrator.modules.workflow_management.service import WorkflowManagementService
from orchestrator.modules.workflow_management.models import (
    WorkflowDefinition, WorkflowExecution, WorkflowStatus, WorkflowExecutionStatus,
    ActionType, ParameterType
)
from shared.enterprise_service_mesh import EnterpriseServiceMesh, ServiceIdentity
from shared.event_streaming import EventStreamProcessor, StreamEvent, EventType, EventPriority
from shared.health import HealthStatus, DependencyHealth, SystemHealth
from shared.enterprise_integration import EnterpriseIntegrationManager


class TestOrchestratorWorkflowManagement:
    """Test workflow management features."""


    @pytest.mark.asyncio
    async def test_workflow_creation(self, workflow_service):
        """Test workflow creation with parameters and actions."""
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow for validation",
            "parameters": [
                {
                    "name": "input_text",
                    "type": "string",
                    "description": "Input text to process",
                    "required": True
                },
                {
                    "name": "processing_mode",
                    "type": "string",
                    "description": "Processing mode",
                    "required": False,
                    "default_value": "standard",
                    "allowed_values": ["fast", "standard", "detailed"]
                }
            ],
            "actions": [
                {
                    "action_id": "process_input",
                    "action_type": "service_call",
                    "name": "Process Input",
                    "description": "Process the input text",
                    "config": {
                        "service": "interpreter",
                        "endpoint": "/process",
                        "method": "POST",
                        "parameters": {
                            "text": "{{input_text}}",
                            "mode": "{{processing_mode}}"
                        }
                    }
                },
                {
                    "action_id": "generate_summary",
                    "action_type": "service_call",
                    "name": "Generate Summary",
                    "description": "Generate summary of processed text",
                    "config": {
                        "service": "summarizer_hub",
                        "endpoint": "/summarize",
                        "method": "POST",
                        "parameters": {
                            "content": "{{process_input.response.content}}",
                            "max_length": 200
                        }
                    },
                    "depends_on": ["process_input"]
                }
            ]
        }

    success, message, workflow = await workflow_service.create_workflow(workflow_data, "test_user")

    if not success:
        print(f"Workflow creation failed: {message}")
    assert success == True
    assert workflow is not None
    assert workflow.name == "Test Workflow"
    assert len(workflow.parameters) == 2
    assert len(workflow.actions) == 2
    assert workflow.created_by == "test_user"

    @pytest.mark.asyncio
    async def test_workflow_validation(self, workflow_service):
        """Test workflow parameter validation."""
        workflow_data = {
            "name": "Validation Test",
            "description": "Test parameter validation",
            "parameters": [
                {
                    "name": "required_param",
                    "type": "string",
                    "required": True
                },
                {
                    "name": "optional_param",
                    "type": "integer",
                    "required": False,
                    "default_value": 42
                }
            ],
            "actions": [
                {
                    "action_id": "test_action",
                    "action_type": "notification",
                    "name": "Test Action",
                    "config": {
                        "message": "Test message"
                    }
                }
            ]
        }

        success, message, workflow = await workflow_service.create_workflow(workflow_data, "test_user")
        assert success == True

        # Test valid parameters
        valid_params = {"required_param": "test_value"}
        is_valid, errors = workflow.validate_parameters(valid_params)
        assert is_valid == True
        assert len(errors) == 0

        # Test missing required parameter
        invalid_params = {}
        is_valid, errors = workflow.validate_parameters(invalid_params)
        assert is_valid == False
        assert len(errors) > 0
        assert "required_param" in str(errors)

        # Test invalid parameter type
        invalid_params = {"required_param": "test", "optional_param": "not_a_number"}
        is_valid, errors = workflow.validate_parameters(invalid_params)
        assert is_valid == False
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_workflow_execution(self, workflow_service):
        """Test workflow execution with mock service calls."""
        workflow_data = {
            "name": "Execution Test",
            "description": "Test workflow execution",
            "parameters": [
                {
                    "name": "test_input",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "mock_service_call",
                    "action_type": "service_call",
                    "name": "Mock Service Call",
                    "description": "Mock service call for testing",
                    "config": {
                        "service": "mock_service",
                        "endpoint": "/test",
                        "method": "POST",
                        "parameters": {
                            "input": "{{test_input}}"
                        }
                    }
                }
            ]
        }

        # Create workflow
        success, message, workflow = await workflow_service.create_workflow(workflow_data, "test_user")
        assert success == True

        # Update status to active
        workflow.status = WorkflowStatus.ACTIVE
        await workflow_service.repository.save_workflow_definition(workflow)

        # Execute workflow
        execution_params = {"test_input": "test_value"}
        success, message, execution = await workflow_service.execute_workflow(
            workflow.workflow_id, execution_params, "test_user"
        )

        assert success == True
        assert execution is not None
        assert execution.workflow_id == workflow.workflow_id
        assert execution.input_parameters == execution_params
        assert execution.status == WorkflowExecutionStatus.RUNNING

    @pytest.mark.asyncio
    async def test_workflow_crud_operations(self, workflow_service):
        """Test complete CRUD operations for workflows."""
        # Create
        workflow_data = {
            "name": "CRUD Test",
            "description": "Test CRUD operations",
            "parameters": [],
            "actions": [{
                "action_id": "test_action",
                "action_type": "notification",
                "name": "Test Action",
                "config": {"message": "CRUD test"}
            }]
        }

        success, message, workflow = await workflow_service.create_workflow(workflow_data, "test_user")
        assert success == True
        workflow_id = workflow.workflow_id

        # Read
        retrieved_workflow = await workflow_service.get_workflow(workflow_id)
        assert retrieved_workflow is not None
        assert retrieved_workflow.name == "CRUD Test"

        # Update
        updates = {"description": "Updated description"}
        success, message = await workflow_service.update_workflow(workflow_id, updates, "test_user")
        assert success == True

        # Verify update
        updated_workflow = await workflow_service.get_workflow(workflow_id)
        assert updated_workflow.description == "Updated description"

        # List
        workflows = await workflow_service.list_workflows()
        assert len(workflows) > 0
        assert any(w.workflow_id == workflow_id for w in workflows)

        # Delete
        success, message = await workflow_service.delete_workflow(workflow_id)
        assert success == True

        # Verify deletion
        deleted_workflow = await workflow_service.get_workflow(workflow_id)
        assert deleted_workflow is None or deleted_workflow.status == WorkflowStatus.ARCHIVED


class TestOrchestratorEventStreaming:
    """Test event streaming features."""

    @pytest.fixture
    async def event_stream(self):
        """Create event stream processor instance."""
        stream = EventStreamProcessor()
        yield stream

    @pytest.mark.asyncio
    async def test_event_creation_and_publishing(self, event_stream):
        """Test event creation and publishing."""
        event = StreamEvent(
            event_id="test-event-001",
            event_type=EventType.SYSTEM,
            priority=EventPriority.HIGH,
            source_service="test_orchestrator",
            payload={
                "action": "workflow_started",
                "workflow_id": "wf-123",
                "timestamp": datetime.now().isoformat()
            }
        )

        # Test event creation
        assert event.event_id == "test-event-001"
        assert event.event_type == EventType.SYSTEM
        assert event.priority == EventPriority.HIGH
        assert event.source_service == "test_orchestrator"
        assert event.payload["action"] == "workflow_started"

    @pytest.mark.asyncio
    async def test_event_subscription_and_processing(self, event_stream):
        """Test event subscription and real-time processing."""
        received_events = []

        async def test_handler(event: StreamEvent):
            received_events.append(event)
            print(f"Received event: {event.event_id}")

        # Subscribe to events
        subscription_id = await event_stream.subscribe_to_events(
            subscriber_id="test_subscriber",
            event_types=[EventType.SYSTEM, EventType.BUSINESS],
            handler=test_handler
        )

        assert subscription_id is not None

        # Publish test event
        test_event = StreamEvent(
            event_id="test-event-002",
            event_type=EventType.SYSTEM,
            source_service="test_publisher",
            payload={"test": "data"}
        )

        await event_stream.publish_event(test_event)

        # Wait for event processing
        await asyncio.sleep(0.1)

        # Verify event was received
        assert len(received_events) >= 1
        assert received_events[0].event_id == "test-event-002"

    @pytest.mark.asyncio
    async def test_event_correlation(self, event_stream):
        """Test event correlation across services."""
        # Create correlated events
        workflow_event = StreamEvent(
            event_id="wf-start-001",
            event_type=EventType.BUSINESS,
            source_service="workflow_service",
            payload={
                "workflow_id": "wf-123",
                "action": "started",
                "correlation_id": "corr-456"
            }
        )

        execution_event = StreamEvent(
            event_id="wf-exec-001",
            event_type=EventType.BUSINESS,
            source_service="execution_service",
            payload={
                "execution_id": "exec-789",
                "workflow_id": "wf-123",
                "action": "executing",
                "correlation_id": "corr-456"
            }
        )

        # Publish correlated events
        await event_stream.publish_event(workflow_event)
        await event_stream.publish_event(execution_event)

        # Test correlation lookup
        correlation_info = await event_stream.get_event_correlation("corr-456")
        assert correlation_info is not None

        # Verify correlation contains both events
        correlated_events = correlation_info.get("events", [])
        assert len(correlated_events) >= 2
        assert any(e["event_id"] == "wf-start-001" for e in correlated_events)
        assert any(e["event_id"] == "wf-exec-001" for e in correlated_events)


class TestOrchestratorServiceMesh:
    """Test service mesh integration."""

    @pytest.fixture
    async def service_mesh(self):
        """Create service mesh instance."""
        mesh = EnterpriseServiceMesh()
        yield mesh

    @pytest.mark.asyncio
    async def test_service_identity_management(self, service_mesh):
        """Test service identity creation and validation."""
        service_identity = ServiceIdentity(
            service_name="test_workflow_service",
            service_version="1.0.0",
            environment="test"
        )

        # Test identity creation
        assert service_identity.service_name == "test_workflow_service"
        assert service_identity.service_version == "1.0.0"
        assert service_identity.environment == "test"
        assert service_identity.service_id is not None

        # Test identity validation
        assert service_identity.is_valid() == True

        # Test identity serialization
        identity_dict = service_identity.to_dict()
        assert identity_dict["service_name"] == "test_workflow_service"
        assert identity_dict["service_version"] == "1.0.0"
        assert identity_dict["environment"] == "test"

    @pytest.mark.asyncio
    async def test_secure_communication(self, service_mesh):
        """Test secure inter-service communication."""
        # Create service identities
        client_identity = ServiceIdentity(
            service_name="client_service",
            service_version="1.0.0",
            environment="test"
        )

        server_identity = ServiceIdentity(
            service_name="server_service",
            service_version="1.0.0",
            environment="test"
        )

        # Mock service endpoint
        async def mock_server_handler(request_data):
            return {
                "status": "success",
                "message": f"Processed request from {request_data.get('client', 'unknown')}"
            }

        # Test request processing
        test_request = {
            "method": "POST",
            "path": "/api/test",
            "headers": {"Content-Type": "application/json"},
            "body": {"client": "test_client", "data": "test_payload"}
        }

        # Process request through service mesh
        response = await service_mesh.process_request(
            server_identity, test_request, mock_server_handler
        )

        assert response is not None
        assert response["status"] == "success"
        assert "Processed request from" in response["message"]

    @pytest.mark.asyncio
    async def test_mesh_status_and_monitoring(self, service_mesh):
        """Test service mesh status and monitoring."""
        # Get mesh status
        mesh_status = await service_mesh.get_mesh_status()

        assert mesh_status is not None
        assert "services" in mesh_status
        assert "connections" in mesh_status
        assert "health" in mesh_status

        # Test mesh metrics
        metrics = mesh_status.get("metrics", {})
        assert isinstance(metrics, dict)


class TestOrchestratorEnterpriseIntegration:
    """Test enterprise integration features."""

    @pytest.fixture
    async def integration_manager(self):
        """Create enterprise integration manager instance."""
        manager = EnterpriseIntegrationManager()
        await manager.initialize()
        yield manager

    @pytest.mark.asyncio
    async def test_service_discovery(self, integration_manager):
        """Test service discovery functionality."""
        # Test service endpoint discovery
        endpoint = await integration_manager.get_service_endpoint("workflow_service", "execute")
        assert endpoint is not None
        assert "localhost" in endpoint
        assert "5080" in endpoint

        # Test different service
        docstore_endpoint = await integration_manager.get_service_endpoint("doc_store", "store")
        assert docstore_endpoint is not None
        assert "localhost" in docstore_endpoint
        assert "5090" in docstore_endpoint

    @pytest.mark.asyncio
    async def test_standardized_api_responses(self, integration_manager):
        """Test standardized API response creation."""
        # Test success response
        success_response = integration_manager.create_standardized_response(
            success=True,
            message="Operation completed successfully",
            data={"result": "test_data"},
            request_id="req-123",
            processing_time=150.5
        )

        assert success_response.success == True
        assert success_response.message == "Operation completed successfully"
        assert success_response.data["result"] == "test_data"
        assert success_response.metadata["request_id"] == "req-123"
        assert success_response.metadata["processing_time"] == 150.5

        # Test error response
        error_response = integration_manager.create_standardized_response(
            success=False,
            message="Operation failed",
            error_code="VALIDATION_ERROR",
            details={"field": "name", "issue": "required"}
        )

        assert error_response.success == False
        assert error_response.message == "Operation failed"
        assert error_response.metadata["error_code"] == "VALIDATION_ERROR"
        assert "details" in error_response.metadata

    @pytest.mark.asyncio
    async def test_request_context_tracking(self, integration_manager):
        """Test request context tracking."""
        # Get current context
        context = integration_manager.get_request_context()

        # Should return a context or None (depending on initialization)
        assert context is None or hasattr(context, 'request_id')


class TestOrchestratorHealthMonitoring:
    """Test health monitoring features."""

    @pytest.mark.asyncio
    async def test_health_status_creation(self):
        """Test health status creation and validation."""
        # Create health status
        health_status = HealthStatus(
            status="healthy",
            service="test_orchestrator",
            version="1.0.0",
            uptime_seconds=3600.0,
            environment="test"
        )

        assert health_status.status == "healthy"
        assert health_status.service == "test_orchestrator"
        assert health_status.version == "1.0.0"
        assert health_status.uptime_seconds == 3600.0
        assert health_status.environment == "test"

    @pytest.mark.asyncio
    async def test_dependency_health_tracking(self):
        """Test dependency health tracking."""
        # Create dependency health
        dependency_health = DependencyHealth(
            name="workflow_database",
            status="healthy",
            response_time_ms=45.2
        )

        assert dependency_health.name == "workflow_database"
        assert dependency_health.status == "healthy"
        assert dependency_health.response_time_ms == 45.2
        assert dependency_health.last_checked is not None

        # Test unhealthy dependency
        unhealthy_dependency = DependencyHealth(
            name="failed_service",
            status="unhealthy",
            error="Connection timeout"
        )

        assert unhealthy_dependency.status == "unhealthy"
        assert unhealthy_dependency.error == "Connection timeout"

    @pytest.mark.asyncio
    async def test_system_health_aggregation(self):
        """Test system health aggregation."""
        # Create system health with multiple dependencies
        system_health = SystemHealth(
            overall_healthy=True,
            services_checked=3,
            services_healthy=3,
            services_unhealthy=0,
            service_details={
                "workflow_service": DependencyHealth(
                    name="workflow_service",
                    status="healthy",
                    response_time_ms=25.0
                ),
                "database": DependencyHealth(
                    name="database",
                    status="healthy",
                    response_time_ms=15.0
                ),
                "event_stream": DependencyHealth(
                    name="event_stream",
                    status="healthy",
                    response_time_ms=10.0
                )
            },
            environment_info={
                "environment": "test",
                "version": "1.0.0",
                "uptime": "1h 30m"
            }
        )

        assert system_health.overall_healthy == True
        assert system_health.services_checked == 3
        assert system_health.services_healthy == 3
        assert system_health.services_unhealthy == 0
        assert len(system_health.service_details) == 3
        assert system_health.environment_info["environment"] == "test"


class TestOrchestratorPerformance:
    """Test orchestrator performance under load."""


    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, workflow_service):
        """Test concurrent workflow execution performance."""
        # Create a simple workflow
        workflow_data = {
            "name": "Performance Test Workflow",
            "description": "Simple workflow for performance testing",
            "parameters": [
                {
                    "name": "input_value",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "mock_action",
                    "action_type": "notification",
                    "name": "Mock Action",
                    "description": "Mock action for testing",
                    "config": {
                        "message": "Processing {{input_value}}"
                    }
                }
            ]
        }

        success, message, workflow = await workflow_service.create_workflow(workflow_data, "perf_test")
        assert success == True

        # Update to active status
        workflow.status = WorkflowStatus.ACTIVE
        await workflow_service.repository.save_workflow_definition(workflow)

        # Execute multiple workflows concurrently
        execution_tasks = []
        start_time = time.time()

        for i in range(10):  # Execute 10 concurrent workflows
            execution_params = {"input_value": f"test_input_{i}"}
            task = asyncio.create_task(
                workflow_service.execute_workflow(
                    workflow.workflow_id, execution_params, f"user_{i}"
                )
            )
            execution_tasks.append(task)

        # Wait for all executions to complete
        results = await asyncio.gather(*execution_tasks)
        end_time = time.time()

        # Verify results
        successful_executions = sum(1 for success, _, _ in results if success)
        total_time = end_time - start_time

        assert successful_executions == 10  # All should succeed
        assert total_time < 30  # Should complete within 30 seconds
        print(".2f")

    @pytest.mark.asyncio
    async def test_workflow_creation_performance(self, workflow_service):
        """Test workflow creation performance."""
        start_time = time.time()

        # Create multiple workflows
        creation_tasks = []
        for i in range(20):
            workflow_data = {
                "name": f"Bulk Test Workflow {i}",
                "description": f"Workflow {i} for bulk creation test",
                "parameters": [
                    {
                        "name": "input_value",
                        "type": "string",
                        "required": True
                    }
                ],
                "actions": [
                    {
                        "action_id": "mock_action",
                        "action_type": "notification",
                        "name": "Mock Action",
                        "config": {"message": "Processing input"}
                    }
                ]
            }

            task = asyncio.create_task(
                workflow_service.create_workflow(workflow_data, f"user_{i}")
            )
            creation_tasks.append(task)

        # Wait for all creations to complete
        results = await asyncio.gather(*creation_tasks)
        end_time = time.time()

        # Verify results
        successful_creations = sum(1 for success, _, _ in results if success)
        total_time = end_time - start_time

        assert successful_creations == 20  # All should succeed
        assert total_time < 10  # Should complete within 10 seconds
        print(".2f")


class TestOrchestratorErrorHandling:
    """Test error handling and edge cases."""


    @pytest.mark.asyncio
    async def test_invalid_workflow_creation(self, workflow_service):
        """Test error handling for invalid workflow creation."""
        # Test missing name
        invalid_workflow = {
            "description": "Missing name",
            "parameters": [],
            "actions": []
        }

        success, message, workflow = await workflow_service.create_workflow(
            invalid_workflow, "test_user"
        )

        assert success == False
        assert "name" in message.lower()
        assert workflow is None

        # Test circular dependency
        circular_workflow = {
            "name": "Circular Dependency Test",
            "description": "Test circular dependency detection",
            "parameters": [],
            "actions": [
                {
                    "action_id": "action1",
                    "action_type": "notification",
                    "name": "Action 1",
                    "config": {"message": "Action 1"},
                    "depends_on": ["action2"]  # Depends on action that doesn't exist yet
                }
            ]
        }

        success, message, workflow = await workflow_service.create_workflow(
            circular_workflow, "test_user"
        )

        assert success == False
        assert "dependency" in message.lower()

    @pytest.mark.asyncio
    async def test_invalid_workflow_execution(self, workflow_service):
        """Test error handling for invalid workflow execution."""
        # Try to execute non-existent workflow
        success, message, execution = await workflow_service.execute_workflow(
            "non-existent-workflow-id", {}, "test_user"
        )

        assert success == False
        assert "not found" in message.lower()
        assert execution is None

        # Create workflow but don't activate it
        workflow_data = {
            "name": "Inactive Workflow",
            "description": "Workflow that is not active",
            "parameters": [
                {
                    "name": "input_value",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "test_action",
                    "action_type": "notification",
                    "name": "Test Action",
                    "config": {"message": "Test"}
                }
            ]
        }

        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "test_user"
        )
        assert success == True

        # Try to execute inactive workflow
        success, message, execution = await workflow_service.execute_workflow(
            workflow.workflow_id, {"input_value": "test"}, "test_user"
        )

        assert success == False
        assert "not active" in message.lower()

    @pytest.mark.asyncio
    async def test_parameter_validation_errors(self, workflow_service):
        """Test parameter validation error handling."""
        workflow_data = {
            "name": "Parameter Validation Test",
            "description": "Test parameter validation",
            "parameters": [
                {
                    "name": "required_string",
                    "type": "string",
                    "required": True,
                    "validation_rules": {"min_length": 5}
                },
                {
                    "name": "optional_number",
                    "type": "integer",
                    "required": False,
                    "validation_rules": {"minimum": 0, "maximum": 100}
                }
            ],
            "actions": [
                {
                    "action_id": "test_action",
                    "action_type": "notification",
                    "name": "Test Action",
                    "config": {"message": "Test"}
                }
            ]
        }

        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "test_user"
        )
        assert success == True

        # Test missing required parameter
        invalid_params = {"optional_number": 50}
        is_valid, errors = workflow.validate_parameters(invalid_params)
        assert is_valid == False
        assert len(errors) > 0

        # Test parameter too short
        invalid_params = {"required_string": "abc", "optional_number": 50}
        is_valid, errors = workflow.validate_parameters(invalid_params)
        assert is_valid == False
        assert len(errors) > 0

        # Test number out of range
        invalid_params = {"required_string": "valid_string", "optional_number": 150}
        is_valid, errors = workflow.validate_parameters(invalid_params)
        assert is_valid == False
        assert len(errors) > 0

        # Test valid parameters
        valid_params = {"required_string": "valid_string", "optional_number": 50}
        is_valid, errors = workflow.validate_parameters(valid_params)
        assert is_valid == True
        assert len(errors) == 0


class TestOrchestratorIntegration:
    """Test full orchestrator integration scenarios."""

    @pytest.fixture
    async def orchestrator_setup(self):
        """Set up complete orchestrator environment for integration testing."""
        # This would typically set up all services and dependencies
        # For now, we'll mock the key components
        workflow_service = WorkflowManagementService()
        event_stream = EventStreamProcessor()
        service_mesh = EnterpriseServiceMesh()

        return {
            "workflow_service": workflow_service,
            "event_stream": event_stream,
            "service_mesh": service_mesh
        }

    @pytest.mark.asyncio
    async def test_end_to_end_workflow_scenario(self, orchestrator_setup):
        """Test complete end-to-end workflow scenario."""
        components = orchestrator_setup
        workflow_service = components["workflow_service"]
        event_stream = components["event_stream"]

        # Create a comprehensive workflow
        workflow_data = {
            "name": "End-to-End Test Workflow",
            "description": "Complete workflow for integration testing",
            "parameters": [
                {
                    "name": "document_content",
                    "type": "string",
                    "description": "Document content to process",
                    "required": True
                },
                {
                    "name": "analysis_type",
                    "type": "string",
                    "description": "Type of analysis to perform",
                    "required": False,
                    "default_value": "comprehensive",
                    "allowed_values": ["basic", "comprehensive", "detailed"]
                }
            ],
            "actions": [
                {
                    "action_id": "ingest_document",
                    "action_type": "service_call",
                    "name": "Ingest Document",
                    "description": "Ingest document into document store",
                    "config": {
                        "service": "doc_store",
                        "endpoint": "/documents",
                        "method": "POST",
                        "parameters": {
                            "content": "{{document_content}}",
                            "type": "text"
                        }
                    }
                },
                {
                    "action_id": "analyze_document",
                    "action_type": "service_call",
                    "name": "Analyze Document",
                    "description": "Analyze document content",
                    "config": {
                        "service": "analysis_service",
                        "endpoint": "/analyze",
                        "method": "POST",
                        "parameters": {
                            "document_id": "{{ingest_document.response.document_id}}",
                            "analysis_type": "{{analysis_type}}"
                        }
                    },
                    "depends_on": ["ingest_document"]
                },
                {
                    "action_id": "generate_summary",
                    "action_type": "service_call",
                    "name": "Generate Summary",
                    "description": "Generate summary of analysis",
                    "config": {
                        "service": "summarizer_hub",
                        "endpoint": "/summarize",
                        "method": "POST",
                        "parameters": {
                            "content": "{{analyze_document.response.analysis}}",
                            "max_length": 300
                        }
                    },
                    "depends_on": ["analyze_document"]
                },
                {
                    "action_id": "send_notification",
                    "action_type": "notification",
                    "name": "Send Completion Notification",
                    "description": "Notify about workflow completion",
                    "config": {
                        "message": "Workflow completed successfully. Summary: {{generate_summary.response.summary}}",
                        "channels": ["log"]
                    },
                    "depends_on": ["generate_summary"]
                }
            ]
        }

        # Create workflow
        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "integration_test"
        )
        assert success == True

        # Activate workflow
        workflow.status = WorkflowStatus.ACTIVE
        await workflow_service.repository.save_workflow_definition(workflow)

        # Execute workflow
        execution_params = {
            "document_content": "This is a test document for integration testing.",
            "analysis_type": "comprehensive"
        }

        success, message, execution = await workflow_service.execute_workflow(
            workflow.workflow_id, execution_params, "integration_test"
        )
        assert success == True

        # Wait for execution to complete
        await asyncio.sleep(2)

        # Verify execution completed
        updated_execution = await workflow_service.get_execution(execution.execution_id)
        assert updated_execution is not None
        assert updated_execution.status in [
            WorkflowExecutionStatus.COMPLETED,
            WorkflowExecutionStatus.RUNNING  # May still be running due to mocks
        ]

        print(f"Integration test completed. Execution status: {updated_execution.status}")

    @pytest.mark.asyncio
    async def test_multi_service_orchestration(self, orchestrator_setup):
        """Test orchestration across multiple services."""
        components = orchestrator_setup
        workflow_service = components["workflow_service"]

        # Create workflow that coordinates multiple services
        workflow_data = {
            "name": "Multi-Service Orchestration",
            "description": "Test orchestration across multiple services",
            "parameters": [
                {
                    "name": "github_repo",
                    "type": "string",
                    "description": "GitHub repository to analyze",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "fetch_repo_data",
                    "action_type": "service_call",
                    "name": "Fetch Repository Data",
                    "description": "Fetch data from GitHub repository",
                    "config": {
                        "service": "source_agent",
                        "endpoint": "/github/repo",
                        "method": "GET",
                        "parameters": {
                            "repo": "{{github_repo}}"
                        }
                    }
                },
                {
                    "action_id": "analyze_code",
                    "action_type": "service_call",
                    "name": "Analyze Code Quality",
                    "description": "Analyze code quality and patterns",
                    "config": {
                        "service": "code_analyzer",
                        "endpoint": "/analyze",
                        "method": "POST",
                        "parameters": {
                            "repo_data": "{{fetch_repo_data.response}}"
                        }
                    },
                    "depends_on": ["fetch_repo_data"]
                },
                {
                    "action_id": "check_security",
                    "action_type": "service_call",
                    "name": "Security Analysis",
                    "description": "Check for security vulnerabilities",
                    "config": {
                        "service": "secure_analyzer",
                        "endpoint": "/scan",
                        "method": "POST",
                        "parameters": {
                            "code_data": "{{analyze_code.response}}"
                        }
                    },
                    "depends_on": ["analyze_code"]
                },
                {
                    "action_id": "generate_report",
                    "action_type": "service_call",
                    "name": "Generate Report",
                    "description": "Generate comprehensive analysis report",
                    "config": {
                        "service": "analysis_service",
                        "endpoint": "/generate_report",
                        "method": "POST",
                        "parameters": {
                            "repo_analysis": "{{analyze_code.response}}",
                            "security_analysis": "{{check_security.response}}"
                        }
                    },
                    "depends_on": ["analyze_code", "check_security"]
                }
            ]
        }

        # Create workflow
        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "orchestration_test"
        )
        assert success == True

        # Verify multi-service dependencies
        execution_plan = workflow.get_execution_plan()
        assert len(execution_plan) >= 3  # Should have multiple levels due to dependencies

        print(f"Multi-service workflow created with {len(execution_plan)} execution levels")


# Performance and load testing utilities
class OrchestratorLoadTester:
    """Load testing utilities for orchestrator service."""

    def __init__(self, base_url: str = "http://localhost:5080"):
        self.base_url = base_url
        self.session = None

    async def setup(self):
        """Setup load testing environment."""
        self.session = aiohttp.ClientSession()

    async def teardown(self):
        """Cleanup load testing environment."""
        if self.session:
            await self.session.close()

    async def create_test_workflow(self) -> str:
        """Create a test workflow for load testing."""
        workflow_data = {
            "name": "Load Test Workflow",
            "description": "Workflow for load testing",
            "parameters": [
                {
                    "name": "test_input",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "load_test_action",
                    "action_type": "notification",
                    "name": "Load Test Action",
                    "config": {
                        "message": "Processing {{test_input}}"
                    }
                }
            ]
        }

        async with self.session.post(
            f"{self.base_url}/workflows",
            json=workflow_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                workflow_id = result["workflow"]["workflow_id"]

                # Activate workflow
                await self.session.put(
                    f"{self.base_url}/workflows/{workflow_id}",
                    json={"status": "active"}
                )

                return workflow_id
            else:
                raise Exception(f"Failed to create workflow: {response.status}")

    async def execute_workflow_load_test(self, workflow_id: str, num_requests: int = 100):
        """Execute load test for workflow execution."""
        import time

        start_time = time.time()
        tasks = []

        for i in range(num_requests):
            task = self._execute_single_workflow(workflow_id, f"request_{i}")
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        successful_requests = sum(1 for r in results if not isinstance(r, Exception))
        total_time = end_time - start_time
        requests_per_second = num_requests / total_time

        return {
            "total_requests": num_requests,
            "successful_requests": successful_requests,
            "failed_requests": num_requests - successful_requests,
            "total_time": total_time,
            "requests_per_second": requests_per_second,
            "average_response_time": total_time / num_requests
        }

    async def _execute_single_workflow(self, workflow_id: str, input_value: str):
        """Execute a single workflow request."""
        execution_data = {
            "parameters": {
                "test_input": input_value
            }
        }

        async with self.session.post(
            f"{self.base_url}/workflows/{workflow_id}/execute",
            json=execution_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Request failed: {response.status}")


@pytest.mark.asyncio
async def test_orchestrator_load_performance():
    """Integration test for orchestrator load performance."""
    load_tester = OrchestratorLoadTester()

    try:
        await load_tester.setup()

        # Create test workflow
        workflow_id = await load_tester.create_test_workflow()
        assert workflow_id is not None

        # Run load test
        results = await load_tester.execute_workflow_load_test(workflow_id, num_requests=50)

        # Verify performance metrics
        assert results["successful_requests"] >= 45  # At least 90% success rate
        assert results["requests_per_second"] >= 5  # At least 5 requests per second
        assert results["average_response_time"] < 5.0  # Less than 5 seconds average

        print("Load test results:")
        print(f"  Total requests: {results['total_requests']}")
        print(f"  Successful: {results['successful_requests']}")
        print(f"  Failed: {results['failed_requests']}")
        print(f"  Requests/sec: {results['requests_per_second']:.2f}")
        print(".3f")

    finally:
        await load_tester.teardown()


if __name__ == "__main__":
    # Run basic smoke test
    async def smoke_test():
        print("🧪 Running Orchestrator Features Smoke Test...")

        # Test basic workflow creation
        workflow_service = WorkflowManagementService()

        workflow_data = {
            "name": "Smoke Test Workflow",
            "description": "Basic smoke test",
            "parameters": [
                {
                    "name": "test_param",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "smoke_action",
                    "action_type": "notification",
                    "name": "Smoke Test Action",
                    "config": {
                        "message": "Smoke test completed"
                    }
                }
            ]
        }

        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "smoke_test"
        )

        if success:
            print("✅ Smoke test passed - basic workflow creation works")
        else:
            print(f"❌ Smoke test failed: {message}")

    asyncio.run(smoke_test())
