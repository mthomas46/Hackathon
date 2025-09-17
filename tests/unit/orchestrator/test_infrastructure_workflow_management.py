#!/usr/bin/env python3
"""
Infrastructure Layer Tests for Workflow Management

Tests the infrastructure layer including repositories and external service adapters.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from services.orchestrator.infrastructure.persistence.in_memory import (
    InMemoryWorkflowRepository, InMemoryWorkflowExecutionRepository
)
from services.orchestrator.infrastructure.external_services.service_client import (
    OrchestratorServiceClient
)
from services.orchestrator.domain.workflow_management.entities import (
    Workflow, WorkflowExecution, WorkflowParameter, WorkflowAction, WorkflowStatus, ActionType
)
from services.orchestrator.domain.workflow_management.value_objects import (
    WorkflowId, ExecutionId, ParameterType
)


class TestInMemoryWorkflowRepository:
    """Test InMemoryWorkflowRepository."""

    def setup_method(self):
        """Setup test fixtures."""
        self.repo = InMemoryWorkflowRepository()

    def test_save_and_get_workflow(self):
        """Test saving and retrieving a workflow."""
        workflow = Workflow(name="Test Workflow", created_by="user")
        param = WorkflowParameter("param1", ParameterType.STRING)
        action = WorkflowAction("action1", ActionType.SERVICE_CALL)

        workflow.add_parameter(param)
        workflow.add_action(action)

        # Save workflow
        result = self.repo.save_workflow(workflow)
        assert result is True

        # Retrieve workflow
        retrieved = self.repo.get_workflow(workflow.workflow_id)
        assert retrieved is not None
        assert retrieved.workflow_id == workflow.workflow_id
        assert retrieved.name == "Test Workflow"
        assert len(retrieved.parameters) == 1
        assert len(retrieved.actions) == 1

    def test_get_nonexistent_workflow(self):
        """Test retrieving non-existent workflow."""
        workflow_id = WorkflowId.generate()
        result = self.repo.get_workflow(workflow_id)

        assert result is None

    def test_list_workflows_no_filters(self):
        """Test listing all workflows without filters."""
        workflow1 = Workflow(name="Workflow 1", created_by="user1")
        workflow2 = Workflow(name="Workflow 2", created_by="user2")

        self.repo.save_workflow(workflow1)
        self.repo.save_workflow(workflow2)

        results = self.repo.list_workflows()

        assert len(results) == 2

    def test_list_workflows_with_name_filter(self):
        """Test listing workflows with name filter."""
        workflow1 = Workflow(name="Test Workflow", created_by="user")
        workflow2 = Workflow(name="Other Workflow", created_by="user")

        self.repo.save_workflow(workflow1)
        self.repo.save_workflow(workflow2)

        results = self.repo.list_workflows(name_filter="Test")

        assert len(results) == 1
        assert results[0].name == "Test Workflow"

    def test_list_workflows_with_tag_filter(self):
        """Test listing workflows with tag filter."""
        workflow1 = Workflow(name="Workflow 1", created_by="user", tags=["tag1"])
        workflow2 = Workflow(name="Workflow 2", created_by="user", tags=["tag2"])

        self.repo.save_workflow(workflow1)
        self.repo.save_workflow(workflow2)

        results = self.repo.list_workflows(tag_filter="tag1")

        assert len(results) == 1
        assert results[0].name == "Workflow 1"

    def test_list_workflows_with_pagination(self):
        """Test workflow listing with pagination."""
        for i in range(5):
            workflow = Workflow(name=f"Workflow {i}", created_by="user")
            self.repo.save_workflow(workflow)

        results = self.repo.list_workflows(limit=2, offset=2)

        assert len(results) == 2
        assert results[0].name == "Workflow 2"
        assert results[1].name == "Workflow 3"

    def test_delete_workflow(self):
        """Test deleting a workflow."""
        workflow = Workflow(name="Test Workflow", created_by="user")
        self.repo.save_workflow(workflow)

        # Delete workflow
        result = self.repo.delete_workflow(workflow.workflow_id)
        assert result is True

        # Verify deletion
        retrieved = self.repo.get_workflow(workflow.workflow_id)
        assert retrieved is None

    def test_delete_nonexistent_workflow(self):
        """Test deleting non-existent workflow."""
        workflow_id = WorkflowId.generate()
        result = self.repo.delete_workflow(workflow_id)

        assert result is False

    def test_update_workflow(self):
        """Test updating a workflow."""
        workflow = Workflow(name="Original Name", created_by="user")
        self.repo.save_workflow(workflow)

        # Update workflow
        workflow.name = "Updated Name"
        result = self.repo.update_workflow(workflow)
        assert result is True

        # Verify update
        retrieved = self.repo.get_workflow(workflow.workflow_id)
        assert retrieved.name == "Updated Name"


class TestInMemoryWorkflowExecutionRepository:
    """Test InMemoryWorkflowExecutionRepository."""

    def setup_method(self):
        """Setup test fixtures."""
        self.repo = InMemoryWorkflowExecutionRepository()

    def test_save_and_get_execution(self):
        """Test saving and retrieving a workflow execution."""
        workflow = Workflow(name="Test", created_by="user")
        execution = WorkflowExecution(workflow_id=workflow.workflow_id)

        # Save execution
        result = self.repo.save_execution(execution)
        assert result is True

        # Retrieve execution
        retrieved = self.repo.get_execution(execution.execution_id)
        assert retrieved is not None
        assert retrieved.execution_id == execution.execution_id
        assert retrieved.workflow_id == workflow.workflow_id

    def test_list_executions_by_workflow_id(self):
        """Test listing executions filtered by workflow ID."""
        workflow1 = Workflow(name="Workflow 1", created_by="user")
        workflow2 = Workflow(name="Workflow 2", created_by="user")

        execution1 = WorkflowExecution(workflow_id=workflow1.workflow_id)
        execution2 = WorkflowExecution(workflow_id=workflow1.workflow_id)
        execution3 = WorkflowExecution(workflow_id=workflow2.workflow_id)

        self.repo.save_execution(execution1)
        self.repo.save_execution(execution2)
        self.repo.save_execution(execution3)

        results = self.repo.list_executions(workflow_id_filter=workflow1.workflow_id)

        assert len(results) == 2
        assert all(e.workflow_id == workflow1.workflow_id for e in results)

    def test_list_executions_by_status(self):
        """Test listing executions filtered by status."""
        workflow = Workflow(name="Test", created_by="user")

        execution1 = WorkflowExecution(workflow_id=workflow.workflow_id)
        execution2 = WorkflowExecution(workflow_id=workflow.workflow_id)

        execution1.start({})
        execution2.fail("Error")

        self.repo.save_execution(execution1)
        self.repo.save_execution(execution2)

        results = self.repo.list_executions(status_filter="running")

        assert len(results) == 1
        assert results[0].status.value == "running"

    def test_update_execution(self):
        """Test updating an execution."""
        workflow = Workflow(name="Test", created_by="user")
        execution = WorkflowExecution(workflow_id=workflow.workflow_id)

        self.repo.save_execution(execution)

        # Update execution
        execution.start({"param": "value"})
        result = self.repo.update_execution(execution)
        assert result is True

        # Verify update
        retrieved = self.repo.get_execution(execution.execution_id)
        assert retrieved.status.value == "running"
        assert retrieved.parameters["param"] == "value"

    def test_delete_execution(self):
        """Test deleting an execution."""
        workflow = Workflow(name="Test", created_by="user")
        execution = WorkflowExecution(workflow_id=workflow.workflow_id)

        self.repo.save_execution(execution)

        # Delete execution
        result = self.repo.delete_execution(execution.execution_id)
        assert result is True

        # Verify deletion
        retrieved = self.repo.get_execution(execution.execution_id)
        assert retrieved is None


class TestOrchestratorServiceClient:
    """Test OrchestratorServiceClient."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = OrchestratorServiceClient()

    @pytest.mark.asyncio
    async def test_call_service_success(self):
        """Test successful service call."""
        # This test would require mocking HTTP calls
        # For now, we'll just test the interface
        assert hasattr(self.client, 'call_service')
        assert callable(self.client.call_service)

    def test_client_initialization(self):
        """Test client initialization."""
        assert self.client is not None
        assert hasattr(self.client, 'client')
