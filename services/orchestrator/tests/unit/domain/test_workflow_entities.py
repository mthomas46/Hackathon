"""Comprehensive tests for Workflow Management Domain Entities"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from services.orchestrator.domain.workflow_management.entities.workflow import (
    Workflow, WorkflowStatus
)
from services.orchestrator.domain.workflow_management.entities.workflow_execution import (
    WorkflowExecution, WorkflowExecutionStatus
)
from services.orchestrator.domain.workflow_management.entities.workflow_action import (
    WorkflowAction, ActionType
)
from services.orchestrator.domain.workflow_management.entities.workflow_parameter import (
    WorkflowParameter, ParameterType
)
from services.orchestrator.domain.workflow_management.value_objects.workflow_id import WorkflowId
from services.orchestrator.domain.workflow_management.value_objects.execution_id import ExecutionId
from services.orchestrator.domain.workflow_management.value_objects.action_result import ActionResult
from services.orchestrator.domain.workflow_management.value_objects.parameter_value import ParameterValue


class TestWorkflowEntity:
    """Test cases for Workflow entity."""

    def test_workflow_creation_minimal(self):
        """Test creating a workflow with minimal required fields."""
        workflow = Workflow()

        assert isinstance(workflow.workflow_id, WorkflowId)
        assert workflow.name == ""
        assert workflow.description == ""
        assert workflow.status == WorkflowStatus.DRAFT
        assert workflow.tags == []
        assert workflow.parameters == []
        assert workflow.actions == []

    def test_workflow_creation_full(self):
        """Test creating a workflow with all fields."""
        workflow_id = WorkflowId("test-workflow")
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()

        workflow = Workflow(
            workflow_id=workflow_id,
            name="Test Workflow",
            description="A test workflow",
            created_by="test-user",
            created_at=created_at,
            updated_at=updated_at,
            status=WorkflowStatus.ACTIVE,
            tags=["test", "automation"]
        )

        assert workflow.workflow_id == workflow_id
        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert workflow.created_by == "test-user"
        assert workflow.created_at == created_at
        assert workflow.updated_at == updated_at
        assert workflow.status == WorkflowStatus.ACTIVE
        assert workflow.tags == ["test", "automation"]

    def test_workflow_parameter_validation_unique_names(self):
        """Test that parameter names must be unique."""
        param1 = WorkflowParameter(
            name="param1",
            type=ParameterType.STRING,
            description="First parameter"
        )
        param2 = WorkflowParameter(
            name="param1",  # Duplicate name
            type=ParameterType.INTEGER,
            description="Second parameter"
        )

        with pytest.raises(ValueError, match="Parameter names must be unique"):
            Workflow(
                name="Test Workflow",
                parameters=[param1, param2]
            )

    def test_workflow_action_validation_unique_ids(self):
        """Test that action IDs must be unique."""
        action1 = WorkflowAction(
            action_id="action1",
            name="Action 1",
            type=ActionType.TASK,
            description="First action"
        )
        action2 = WorkflowAction(
            action_id="action1",  # Duplicate ID
            name="Action 2",
            type=ActionType.DECISION,
            description="Second action"
        )

        with pytest.raises(ValueError, match="Action IDs must be unique"):
            Workflow(
                name="Test Workflow",
                actions=[action1, action2]
            )

    def test_workflow_add_parameter(self):
        """Test adding a parameter to workflow."""
        workflow = Workflow(name="Test Workflow")
        parameter = WorkflowParameter(
            name="test_param",
            type=ParameterType.STRING,
            description="Test parameter"
        )

        workflow.add_parameter(parameter)

        assert len(workflow.parameters) == 1
        assert workflow.parameters[0] == parameter

    def test_workflow_add_action(self):
        """Test adding an action to workflow."""
        workflow = Workflow(name="Test Workflow")
        action = WorkflowAction(
            action_id="test_action",
            name="Test Action",
            type=ActionType.TASK,
            description="Test action"
        )

        workflow.add_action(action)

        assert len(workflow.actions) == 1
        assert workflow.actions[0] == action

    def test_workflow_get_parameter_by_name(self):
        """Test getting parameter by name."""
        workflow = Workflow(name="Test Workflow")
        param1 = WorkflowParameter(
            name="param1",
            type=ParameterType.STRING,
            description="Parameter 1"
        )
        param2 = WorkflowParameter(
            name="param2",
            type=ParameterType.INTEGER,
            description="Parameter 2"
        )

        workflow.add_parameter(param1)
        workflow.add_parameter(param2)

        found = workflow.get_parameter_by_name("param1")
        assert found == param1

        not_found = workflow.get_parameter_by_name("nonexistent")
        assert not_found is None

    def test_workflow_get_action_by_id(self):
        """Test getting action by ID."""
        workflow = Workflow(name="Test Workflow")
        action1 = WorkflowAction(
            action_id="action1",
            name="Action 1",
            type=ActionType.TASK,
            description="Action 1"
        )
        action2 = WorkflowAction(
            action_id="action2",
            name="Action 2",
            type=ActionType.DECISION,
            description="Action 2"
        )

        workflow.add_action(action1)
        workflow.add_action(action2)

        found = workflow.get_action_by_id("action1")
        assert found == action1

        not_found = workflow.get_action_by_id("nonexistent")
        assert not_found is None

    def test_workflow_to_dict(self):
        """Test converting workflow to dictionary."""
        workflow_id = WorkflowId("test-workflow")
        workflow = Workflow(
            workflow_id=workflow_id,
            name="Test Workflow",
            description="Test description",
            created_by="test-user",
            status=WorkflowStatus.ACTIVE,
            tags=["test", "workflow"]
        )

        data = workflow.to_dict()

        assert data["workflow_id"] == "test-workflow"
        assert data["name"] == "Test Workflow"
        assert data["description"] == "Test description"
        assert data["created_by"] == "test-user"
        assert data["status"] == "active"
        assert data["tags"] == ["test", "workflow"]
        assert "created_at" in data
        assert "updated_at" in data

    def test_workflow_from_dict(self):
        """Test creating workflow from dictionary."""
        data = {
            "workflow_id": "test-workflow",
            "name": "Test Workflow",
            "description": "Test description",
            "created_by": "test-user",
            "status": "active",
            "tags": ["test", "workflow"],
            "parameters": [],
            "actions": []
        }

        workflow = Workflow.from_dict(data)

        assert workflow.workflow_id.value == "test-workflow"
        assert workflow.name == "Test Workflow"
        assert workflow.description == "Test description"
        assert workflow.created_by == "test-user"
        assert workflow.status == WorkflowStatus.ACTIVE
        assert workflow.tags == ["test", "workflow"]


class TestWorkflowExecutionEntity:
    """Test cases for WorkflowExecution entity."""

    def test_execution_creation_minimal(self):
        """Test creating execution with minimal fields."""
        execution = WorkflowExecution()

        assert isinstance(execution.execution_id, ExecutionId)
        assert isinstance(execution.workflow_id, WorkflowId)
        assert execution.status == WorkflowExecutionStatus.PENDING
        assert execution.parameters == {}
        assert execution.action_results == []
        assert execution.metadata == {}

    def test_execution_creation_full(self):
        """Test creating execution with all fields."""
        execution_id = ExecutionId("test-execution")
        workflow_id = WorkflowId("test-workflow")
        started_at = datetime.utcnow()

        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowExecutionStatus.RUNNING,
            correlation_id="test-correlation",
            started_at=started_at,
            parameters={"param1": "value1"},
            action_results=[],
            metadata={"key": "value"}
        )

        assert execution.execution_id == execution_id
        assert execution.workflow_id == workflow_id
        assert execution.status == WorkflowExecutionStatus.RUNNING
        assert execution.correlation_id == "test-correlation"
        assert execution.started_at == started_at
        assert execution.parameters == {"param1": "value1"}
        assert execution.metadata == {"key": "value"}

    def test_execution_add_action_result(self):
        """Test adding action result to execution."""
        execution = WorkflowExecution()
        result = ActionResult(
            action_id="test_action",
            status="completed",
            output={"result": "success"}
        )

        execution.add_action_result(result)

        assert len(execution.action_results) == 1
        assert execution.action_results[0] == result

    def test_execution_get_action_result(self):
        """Test getting action result by action ID."""
        execution = WorkflowExecution()
        result1 = ActionResult(
            action_id="action1",
            status="completed",
            output={"result": "success1"}
        )
        result2 = ActionResult(
            action_id="action2",
            status="failed",
            output={"error": "failure"}
        )

        execution.add_action_result(result1)
        execution.add_action_result(result2)

        found = execution.get_action_result("action1")
        assert found == result1

        not_found = execution.get_action_result("nonexistent")
        assert not_found is None

    def test_execution_complete(self):
        """Test completing execution."""
        execution = WorkflowExecution(status=WorkflowExecutionStatus.RUNNING)
        completed_at = datetime.utcnow()

        execution.complete(completed_at)

        assert execution.status == WorkflowExecutionStatus.COMPLETED
        assert execution.completed_at == completed_at

    def test_execution_fail(self):
        """Test failing execution."""
        execution = WorkflowExecution(status=WorkflowExecutionStatus.RUNNING)
        failed_at = datetime.utcnow()

        execution.fail("Test error", failed_at)

        assert execution.status == WorkflowExecutionStatus.FAILED
        assert execution.error_message == "Test error"
        assert execution.completed_at == failed_at

    def test_execution_to_dict(self):
        """Test converting execution to dictionary."""
        execution_id = ExecutionId("test-execution")
        workflow_id = WorkflowId("test-workflow")

        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowExecutionStatus.COMPLETED,
            correlation_id="test-correlation",
            parameters={"param": "value"},
            metadata={"meta": "data"}
        )

        data = execution.to_dict()

        assert data["execution_id"] == "test-execution"
        assert data["workflow_id"] == "test-workflow"
        assert data["status"] == "completed"
        assert data["correlation_id"] == "test-correlation"
        assert data["parameters"] == {"param": "value"}
        assert data["metadata"] == {"meta": "data"}


class TestWorkflowActionEntity:
    """Test cases for WorkflowAction entity."""

    def test_action_creation_minimal(self):
        """Test creating action with minimal fields."""
        action = WorkflowAction(
            action_id="test_action",
            name="Test Action",
            type=ActionType.TASK
        )

        assert action.action_id == "test_action"
        assert action.name == "Test Action"
        assert action.type == ActionType.TASK
        assert action.description == ""
        assert action.config == {}
        assert action.dependencies == []

    def test_action_creation_full(self):
        """Test creating action with all fields."""
        action = WorkflowAction(
            action_id="test_action",
            name="Test Action",
            type=ActionType.TASK,
            description="Test description",
            config={"key": "value"},
            dependencies=["dep1", "dep2"]
        )

        assert action.action_id == "test_action"
        assert action.name == "Test Action"
        assert action.type == ActionType.TASK
        assert action.description == "Test description"
        assert action.config == {"key": "value"}
        assert action.dependencies == ["dep1", "dep2"]

    def test_action_add_dependency(self):
        """Test adding dependency to action."""
        action = WorkflowAction(
            action_id="test_action",
            name="Test Action",
            type=ActionType.TASK
        )

        action.add_dependency("new_dep")

        assert "new_dep" in action.dependencies

    def test_action_has_dependency(self):
        """Test checking if action has dependency."""
        action = WorkflowAction(
            action_id="test_action",
            name="Test Action",
            type=ActionType.TASK,
            dependencies=["dep1", "dep2"]
        )

        assert action.has_dependency("dep1")
        assert not action.has_dependency("nonexistent")

    def test_action_to_dict(self):
        """Test converting action to dictionary."""
        action = WorkflowAction(
            action_id="test_action",
            name="Test Action",
            type=ActionType.DECISION,
            description="Test description",
            config={"config": "value"},
            dependencies=["dep1"]
        )

        data = action.to_dict()

        assert data["action_id"] == "test_action"
        assert data["name"] == "Test Action"
        assert data["type"] == "decision"
        assert data["description"] == "Test description"
        assert data["config"] == {"config": "value"}
        assert data["dependencies"] == ["dep1"]


class TestWorkflowParameterEntity:
    """Test cases for WorkflowParameter entity."""

    def test_parameter_creation_minimal(self):
        """Test creating parameter with minimal fields."""
        param = WorkflowParameter(
            name="test_param",
            type=ParameterType.STRING
        )

        assert param.name == "test_param"
        assert param.type == ParameterType.STRING
        assert param.description == ""
        assert param.required == True
        assert param.default_value is None
        assert param.validation_rules == {}

    def test_parameter_creation_full(self):
        """Test creating parameter with all fields."""
        param = WorkflowParameter(
            name="test_param",
            type=ParameterType.INTEGER,
            description="Test parameter",
            required=False,
            default_value=42,
            validation_rules={"min": 0, "max": 100}
        )

        assert param.name == "test_param"
        assert param.type == ParameterType.INTEGER
        assert param.description == "Test parameter"
        assert param.required == False
        assert param.default_value == 42
        assert param.validation_rules == {"min": 0, "max": 100}

    def test_parameter_validate_value_string(self):
        """Test validating string parameter value."""
        param = WorkflowParameter(
            name="test_param",
            type=ParameterType.STRING,
            validation_rules={"min_length": 3, "max_length": 10}
        )

        # Valid values
        assert param.validate_value("hello")
        assert param.validate_value("hi")

        # Invalid values
        assert not param.validate_value("hi")  # Too short
        assert not param.validate_value("this_is_too_long")  # Too long
        assert not param.validate_value(123)  # Wrong type

    def test_parameter_validate_value_integer(self):
        """Test validating integer parameter value."""
        param = WorkflowParameter(
            name="test_param",
            type=ParameterType.INTEGER,
            validation_rules={"min": 0, "max": 100}
        )

        # Valid values
        assert param.validate_value(50)
        assert param.validate_value(0)
        assert param.validate_value(100)

        # Invalid values
        assert not param.validate_value(-1)  # Too small
        assert not param.validate_value(101)  # Too large
        assert not param.validate_value("50")  # Wrong type

    def test_parameter_to_dict(self):
        """Test converting parameter to dictionary."""
        param = WorkflowParameter(
            name="test_param",
            type=ParameterType.BOOLEAN,
            description="Test parameter",
            required=False,
            default_value=True,
            validation_rules={"required": True}
        )

        data = param.to_dict()

        assert data["name"] == "test_param"
        assert data["type"] == "boolean"
        assert data["description"] == "Test parameter"
        assert data["required"] == False
        assert data["default_value"] == True
        assert data["validation_rules"] == {"required": True}
