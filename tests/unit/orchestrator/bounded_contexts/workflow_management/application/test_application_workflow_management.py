#!/usr/bin/env python3
"""
Application Layer Tests for Workflow Management

Tests the application layer including use cases, commands, and queries.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from services.orchestrator.application.workflow_management.commands import (
    CreateWorkflowCommand, ExecuteWorkflowCommand
)
from services.orchestrator.application.workflow_management.queries import (
    GetWorkflowQuery, ListWorkflowsQuery
)
from services.orchestrator.application.workflow_management.use_cases import (
    CreateWorkflowUseCase, ExecuteWorkflowUseCase, GetWorkflowUseCase, ListWorkflowsUseCase
)
from services.orchestrator.domain.workflow_management.entities import (
    Workflow, WorkflowParameter, WorkflowAction, WorkflowExecution, WorkflowStatus, WorkflowExecutionStatus, ActionType
)
from services.orchestrator.domain.workflow_management.value_objects import (
    WorkflowId, ExecutionId, ParameterType
)
from services.orchestrator.infrastructure.persistence.in_memory import (
    InMemoryWorkflowRepository, InMemoryWorkflowExecutionRepository
)


class TestCreateWorkflowUseCase:
    """Test CreateWorkflowUseCase."""

    def setup_method(self):
        """Setup test fixtures."""
        self.repository = InMemoryWorkflowRepository()
        self.use_case = CreateWorkflowUseCase(self.repository)

    @pytest.mark.asyncio
    async def test_create_workflow_success(self):
        """Test successful workflow creation."""
        command = CreateWorkflowCommand(
            name="Test Workflow",
            description="Test description",
            created_by="test_user",
            parameters=[
                {
                    "name": "param1",
                    "type": "string",
                    "description": "Test parameter",
                    "required": True
                }
            ],
            actions=[
                {
                    "name": "action1",
                    "action_type": "service_call",
                    "config": {"service": "test", "endpoint": "/test"}
                }
            ],
            tags=["test", "workflow"]
        )

        success, message, workflow = await self.use_case.execute(command)

        assert success is True
        assert message == "Workflow created successfully"
        assert workflow is not None
        assert workflow.name == "Test Workflow"
        assert workflow.created_by == "test_user"
        assert len(workflow.parameters) == 1
        assert len(workflow.actions) == 1

    @pytest.mark.asyncio
    async def test_create_workflow_validation_failure(self):
        """Test workflow creation with validation failure."""
        command = CreateWorkflowCommand(
            name="",  # Invalid: empty name
            description="Test description",
            created_by="test_user",
            parameters=[],
            actions=[],
            tags=[]
        )

        success, message, workflow = await self.use_case.execute(command)

        assert success is False
        assert "validation failed" in message.lower()
        assert workflow is None


class TestExecuteWorkflowUseCase:
    """Test ExecuteWorkflowUseCase."""

    def setup_method(self):
        """Setup test fixtures."""
        self.workflow_repo = InMemoryWorkflowRepository()
        self.execution_repo = InMemoryWorkflowExecutionRepository()
        self.executor = Mock()

        self.use_case = ExecuteWorkflowUseCase(
            self.workflow_repo, self.execution_repo, self.executor
        )

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self):
        """Test successful workflow execution."""
        # Create and save a workflow
        workflow = Workflow(name="Test Workflow", created_by="user")
        param = WorkflowParameter("param1", ParameterType.STRING, required=True)
        action = WorkflowAction(name="action1", action_type=ActionType.SERVICE_CALL, config={"service": "test", "endpoint": "/test"})
        workflow.add_parameter(param)
        workflow.add_action(action)
        self.workflow_repo.save_workflow(workflow)

        # Create expected execution result
        execution = WorkflowExecution(workflow_id=workflow.workflow_id)
        execution.start({"param1": "test_value"})
        execution.complete()

        # Mock the executor to return the execution as completed
        self.executor.execute_workflow = AsyncMock(return_value=execution)

        # Execute workflow
        command = ExecuteWorkflowCommand(
            workflow_id=workflow.workflow_id,
            parameters={"param1": "test_value"}
        )

        success, message, execution = await self.use_case.execute(command)

        assert success is True
        assert execution is not None
        assert execution.workflow_id == workflow.workflow_id
        assert execution.status == WorkflowExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_nonexistent_workflow(self):
        """Test executing non-existent workflow."""
        command = ExecuteWorkflowCommand(
            workflow_id=WorkflowId.generate(),
            parameters={}
        )

        success, message, execution = await self.use_case.execute(command)

        assert success is False
        assert "not found" in message.lower()
        assert execution is None


class TestGetWorkflowUseCase:
    """Test GetWorkflowUseCase."""

    def setup_method(self):
        """Setup test fixtures."""
        self.repository = InMemoryWorkflowRepository()
        self.use_case = GetWorkflowUseCase(self.repository)

    @pytest.mark.asyncio
    async def test_get_existing_workflow(self):
        """Test getting an existing workflow."""
        workflow = Workflow(name="Test Workflow", created_by="user")
        self.repository.save_workflow(workflow)

        query = GetWorkflowQuery(workflow_id=workflow.workflow_id)

        result = await self.use_case.execute(query)

        assert result is not None
        assert result.workflow_id == workflow.workflow_id
        assert result.name == "Test Workflow"

    @pytest.mark.asyncio
    async def test_get_nonexistent_workflow(self):
        """Test getting a non-existent workflow."""
        query = GetWorkflowQuery(workflow_id=WorkflowId.generate())

        result = await self.use_case.execute(query)

        assert result is None


class TestListWorkflowsUseCase:
    """Test ListWorkflowsUseCase."""

    def setup_method(self):
        """Setup test fixtures."""
        self.repository = InMemoryWorkflowRepository()
        self.use_case = ListWorkflowsUseCase(self.repository)

        # Create test workflows
        workflow1 = Workflow(name="Workflow 1", created_by="user1", tags=["tag1"])
        workflow2 = Workflow(name="Workflow 2", created_by="user2", tags=["tag2"])
        workflow3 = Workflow(name="Another Workflow", created_by="user1", tags=["tag1"])

        self.repository.save_workflow(workflow1)
        self.repository.save_workflow(workflow2)
        self.repository.save_workflow(workflow3)

    @pytest.mark.asyncio
    async def test_list_all_workflows(self):
        """Test listing all workflows."""
        query = ListWorkflowsQuery()

        results = await self.use_case.execute(query)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_list_workflows_by_name_filter(self):
        """Test filtering workflows by name."""
        query = ListWorkflowsQuery(name_filter="Workflow 1")

        results = await self.use_case.execute(query)

        assert len(results) == 1
        assert results[0].name == "Workflow 1"

    @pytest.mark.asyncio
    async def test_list_workflows_by_tag_filter(self):
        """Test filtering workflows by tag."""
        query = ListWorkflowsQuery(tag_filter="tag1")

        results = await self.use_case.execute(query)

        assert len(results) == 2
        assert all("tag1" in w.tags for w in results)

    @pytest.mark.asyncio
    async def test_list_workflows_by_creator(self):
        """Test filtering workflows by creator."""
        query = ListWorkflowsQuery(created_by_filter="user1")

        results = await self.use_case.execute(query)

        assert len(results) == 2
        assert all(w.created_by == "user1" for w in results)

    @pytest.mark.asyncio
    async def test_list_workflows_with_pagination(self):
        """Test workflow listing with pagination."""
        query = ListWorkflowsQuery(limit=2, offset=1)

        results = await self.use_case.execute(query)

        assert len(results) == 2  # Should return 2nd and 3rd workflows


class TestWorkflowExecution:
    """Test WorkflowExecution entity behavior."""

    def test_execution_lifecycle(self):
        """Test the complete execution lifecycle."""
        workflow = Workflow("Test", created_by="user")
        execution = WorkflowExecution(workflow_id=workflow.workflow_id)

        # Initial state
        assert execution.status == WorkflowExecutionStatus.PENDING

        # Start execution
        execution.start({"param1": "value"})
        assert execution.status == WorkflowExecutionStatus.RUNNING
        assert execution.started_at is not None
        assert execution.parameters["param1"] == "value"

        # Complete execution
        execution.complete()
        assert execution.status == WorkflowExecutionStatus.COMPLETED
        assert execution.completed_at is not None

    def test_execution_failure(self):
        """Test execution failure handling."""
        workflow = Workflow("Test", created_by="user")
        execution = WorkflowExecution(workflow_id=workflow.workflow_id)

        execution.start({})
        execution.fail("Test error")

        assert execution.status == WorkflowExecutionStatus.FAILED
        assert execution.error_message == "Test error"
        assert execution.completed_at is not None

    def test_execution_cancellation(self):
        """Test execution cancellation."""
        workflow = Workflow("Test", created_by="user")
        execution = WorkflowExecution(workflow_id=workflow.workflow_id)

        execution.start({})
        execution.cancel()

        assert execution.status == WorkflowExecutionStatus.CANCELLED
        assert execution.completed_at is not None
