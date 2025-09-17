#!/usr/bin/env python3
"""
Domain Layer Tests for Workflow Management

Tests the core domain logic including value objects, entities, and domain services.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock

from services.orchestrator.domain.workflow_management.value_objects import (
    WorkflowId, ExecutionId, ParameterValue, ParameterType, ActionResult, ActionStatus
)
from services.orchestrator.domain.workflow_management.entities import (
    Workflow, WorkflowExecution, WorkflowParameter, WorkflowAction, WorkflowStatus, WorkflowExecutionStatus, ActionType
)
from services.orchestrator.domain.workflow_management.services import (
    WorkflowValidator, ParameterResolver, WorkflowExecutor
)


class TestWorkflowId:
    """Test WorkflowId value object."""

    def test_generate_creates_unique_ids(self):
        """Test that generated IDs are unique."""
        id1 = WorkflowId.generate()
        id2 = WorkflowId.generate()

        assert id1 != id2
        assert isinstance(id1.value, str)
        assert isinstance(id2.value, str)

    def test_from_string_creates_valid_id(self):
        """Test creating WorkflowId from string."""
        test_uuid = str(uuid.uuid4())
        workflow_id = WorkflowId(test_uuid)

        assert workflow_id.value == test_uuid
        assert str(workflow_id) == test_uuid

    def test_from_uuid_creates_valid_id(self):
        """Test creating WorkflowId from UUID object."""
        test_uuid = uuid.uuid4()
        workflow_id = WorkflowId(test_uuid)

        assert workflow_id.uuid == test_uuid
        assert workflow_id.value == str(test_uuid)

    def test_invalid_string_raises_error(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError):
            WorkflowId("invalid-uuid")

    def test_equality(self):
        """Test equality comparison."""
        id1 = WorkflowId("12345678-1234-5678-9012-123456789012")
        id2 = WorkflowId("12345678-1234-5678-9012-123456789012")
        id3 = WorkflowId("87654321-4321-8765-2109-876543210987")

        assert id1 == id2
        assert id1 != id3


class TestParameterValue:
    """Test ParameterValue value object."""

    def test_valid_string_parameter(self):
        """Test creating valid string parameter."""
        param = ParameterValue("test_value", ParameterType.STRING)
        assert param.value == "test_value"
        assert param.param_type == ParameterType.STRING

    def test_valid_integer_parameter(self):
        """Test creating valid integer parameter."""
        param = ParameterValue(42, ParameterType.INTEGER)
        assert param.value == 42
        assert param.param_type == ParameterType.INTEGER

    def test_invalid_string_parameter(self):
        """Test that invalid string parameter raises error."""
        with pytest.raises(ValueError):
            ParameterValue(123, ParameterType.STRING)

    def test_invalid_integer_parameter(self):
        """Test that invalid integer parameter raises error."""
        with pytest.raises(ValueError):
            ParameterValue("not_a_number", ParameterType.INTEGER)


class TestWorkflowParameter:
    """Test WorkflowParameter entity."""

    def test_create_valid_parameter(self):
        """Test creating a valid workflow parameter."""
        param = WorkflowParameter(
            name="test_param",
            param_type=ParameterType.STRING,
            description="Test parameter",
            required=True,
            default_value="default"
        )

        assert param.name == "test_param"
        assert param.param_type == ParameterType.STRING
        assert param.required is True
        assert param.default_value == "default"

    def test_validate_string_value(self):
        """Test validating string parameter value."""
        param = WorkflowParameter("test", ParameterType.STRING)

        assert param.validate_value("valid_string") == (True, "")
        assert param.validate_value(123) == (False, "Parameter 'test' must be a string")

    def test_validate_required_parameter(self):
        """Test validating required parameter."""
        param = WorkflowParameter("required", ParameterType.STRING, required=True)

        assert param.validate_value(None) == (False, "Parameter 'required' is required")
        assert param.validate_value("value") == (True, "")

    def test_validate_allowed_values(self):
        """Test validating allowed values."""
        param = WorkflowParameter(
            "choice",
            ParameterType.STRING,
            allowed_values=["option1", "option2"]
        )

        assert param.validate_value("option1") == (True, "")
        assert param.validate_value("invalid") == (False, "Parameter 'choice' must be one of: ['option1', 'option2']")


class TestWorkflowAction:
    """Test WorkflowAction entity."""

    def test_create_valid_action(self):
        """Test creating a valid workflow action."""
        action = WorkflowAction(
            action_id="test_action_id",
            name="test_action",
            action_type=ActionType.SERVICE_CALL,
            config={"service": "test", "endpoint": "/test"}
        )

        assert action.name == "test_action"
        assert action.action_type == ActionType.SERVICE_CALL
        assert action.config["service"] == "test"

    def test_can_execute_without_dependencies(self):
        """Test action execution when no dependencies."""
        action = WorkflowAction(name="test", action_type=ActionType.SERVICE_CALL)

        assert action.can_execute({}) is True

    def test_can_execute_with_satisfied_dependencies(self):
        """Test action execution with satisfied dependencies."""
        action = WorkflowAction(
            name="test",
            action_type=ActionType.SERVICE_CALL,
            depends_on=["dep1", "dep2"]
        )

        previous_results = {
            "dep1": Mock(status="completed"),
            "dep2": Mock(status="completed")
        }

        assert action.can_execute(previous_results) is True

    def test_cannot_execute_with_failed_dependencies(self):
        """Test action cannot execute with failed dependencies."""
        action = WorkflowAction(
            name="test",
            action_type=ActionType.SERVICE_CALL,
            depends_on=["dep1"]
        )

        previous_results = {
            "dep1": Mock(status="failed")
        }

        assert action.can_execute(previous_results) is False


class TestWorkflow:
    """Test Workflow entity."""

    def test_create_valid_workflow(self):
        """Test creating a valid workflow."""
        workflow = Workflow(
            name="Test Workflow",
            description="Test description",
            created_by="test_user",
            status=WorkflowStatus.DRAFT
        )

        assert workflow.name == "Test Workflow"
        assert workflow.status == WorkflowStatus.DRAFT
        assert workflow.created_by == "test_user"

    def test_add_parameter(self):
        """Test adding parameter to workflow."""
        workflow = Workflow(name="Test", created_by="user")
        param = WorkflowParameter("param1", ParameterType.STRING)

        workflow.add_parameter(param)

        assert len(workflow.parameters) == 1
        assert workflow.get_parameter("param1") == param

    def test_add_duplicate_parameter_raises_error(self):
        """Test that adding duplicate parameter raises error."""
        workflow = Workflow(name="Test", created_by="user")
        param1 = WorkflowParameter("param1", ParameterType.STRING)
        param2 = WorkflowParameter("param1", ParameterType.INTEGER)

        workflow.add_parameter(param1)

        with pytest.raises(ValueError):
            workflow.add_parameter(param2)

    def test_validate_parameters(self):
        """Test parameter validation."""
        workflow = Workflow(name="Test", created_by="user")
        param = WorkflowParameter("required", ParameterType.STRING, required=True)
        workflow.add_parameter(param)

        # Valid parameters
        valid, errors = workflow.validate_parameters({"required": "value"})
        assert valid is True
        assert errors == ""

        # Missing required parameter
        valid, errors = workflow.validate_parameters({})
        assert valid is False
        assert "required" in errors

    def test_activate_workflow(self):
        """Test workflow activation."""
        workflow = Workflow(name="Test", created_by="user")
        action = WorkflowAction(name="action1", action_type=ActionType.SERVICE_CALL)
        workflow.add_action(action)

        workflow.activate()

        assert workflow.status == WorkflowStatus.ACTIVE


class TestWorkflowValidator:
    """Test WorkflowValidator domain service."""

    def test_validate_valid_workflow(self):
        """Test validating a valid workflow."""
        workflow = Workflow(name="Test Workflow", created_by="user")
        param = WorkflowParameter("param1", ParameterType.STRING)
        action = WorkflowAction(
            name="action1",
            action_type=ActionType.SERVICE_CALL,
            config={"service": "test_service", "endpoint": "/test"}
        )

        workflow.add_parameter(param)
        workflow.add_action(action)

        is_valid, errors = WorkflowValidator.validate_workflow(workflow)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_workflow_without_name(self):
        """Test validation fails for workflow without name."""
        workflow = Workflow(name="", created_by="user")

        is_valid, errors = WorkflowValidator.validate_workflow(workflow)

        assert is_valid is False
        assert any("name" in error.lower() for error in errors)

    def test_validate_workflow_with_circular_dependencies(self):
        """Test validation fails for circular dependencies."""
        workflow = Workflow(name="Test", created_by="user")

        action1 = WorkflowAction(
            action_id="action1",
            name="action1",
            action_type=ActionType.SERVICE_CALL,
            config={"service": "test", "endpoint": "/test"},
            depends_on=["action2"]
        )
        action2 = WorkflowAction(
            action_id="action2",
            name="action2",
            action_type=ActionType.SERVICE_CALL,
            config={"service": "test", "endpoint": "/test"},
            depends_on=["action1"]
        )

        workflow.add_action(action1)
        workflow.add_action(action2)

        is_valid, errors = WorkflowValidator.validate_workflow(workflow)

        assert is_valid is False
        assert any("circular" in error.lower() for error in errors)


class TestParameterResolver:
    """Test ParameterResolver domain service."""

    def test_resolve_parameters_with_provided_values(self):
        """Test resolving parameters with provided values."""
        workflow = Workflow(name="Test", created_by="user")
        param = WorkflowParameter("param1", ParameterType.STRING, required=True)
        workflow.add_parameter(param)

        provided = {"param1": "test_value"}
        resolved = ParameterResolver.resolve_parameters(workflow, provided)

        assert resolved["param1"] == "test_value"

    def test_resolve_parameters_with_defaults(self):
        """Test resolving parameters using defaults."""
        workflow = Workflow(name="Test", created_by="user")
        param = WorkflowParameter(
            "param1",
            ParameterType.STRING,
            default_value="default_value"
        )
        workflow.add_parameter(param)

        resolved = ParameterResolver.resolve_parameters(workflow, {})

        assert resolved["param1"] == "default_value"

    def test_resolve_missing_required_parameter_raises_error(self):
        """Test that missing required parameter raises error."""
        workflow = Workflow(name="Test", created_by="user")
        param = WorkflowParameter("required", ParameterType.STRING, required=True)
        workflow.add_parameter(param)

        with pytest.raises(ValueError):
            ParameterResolver.resolve_parameters(workflow, {})


class TestActionResult:
    """Test ActionResult value object."""

    def test_success_result(self):
        """Test creating success result."""
        result = ActionResult.success("action1", {"data": "value"}, 1500)

        assert result.action_id == "action1"
        assert result.status == ActionStatus.COMPLETED
        assert result.is_successful is True
        assert result.execution_time_ms == 1500

    def test_failure_result(self):
        """Test creating failure result."""
        result = ActionResult.failure("action1", "Error occurred", 500)

        assert result.action_id == "action1"
        assert result.status == ActionStatus.FAILED
        assert result.has_error is True
        assert result.error_message == "Error occurred"
