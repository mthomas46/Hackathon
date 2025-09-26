"""Tests for Workflow Domain Entities"""

import pytest
from datetime import datetime

from services.orchestrator.domain.entities.workflow import (
    Workflow
)
from services.orchestrator.domain.value_objects.workflow_status import (
    WorkflowStatus
)
from services.orchestrator.domain.value_objects.workflow_id import (
    WorkflowId
)
from services.orchestrator.domain.value_objects.workflow_type import (
    WorkflowType
)


class TestWorkflowEntity:
    """Test cases for Workflow entity."""

    def test_workflow_creation_minimal(self):
        """Test creating a workflow with minimal required fields."""
        workflow_id = WorkflowId.generate()
        workflow = Workflow(
            id=workflow_id,
            name="Test Workflow",
            type=WorkflowType.CUSTOM,
            status=WorkflowStatus.PENDING,
            parameters={},
            steps=[],
            dependencies=[]
        )

        assert isinstance(workflow.id, WorkflowId)
        assert workflow.name == "Test Workflow"
        assert workflow.type == WorkflowType.CUSTOM
        assert workflow.status == WorkflowStatus.PENDING
        assert workflow.parameters == {}
        assert workflow.steps == []
        assert workflow.dependencies == []

    def test_workflow_creation_full(self):
        """Test creating a workflow with all fields."""
        workflow_id = WorkflowId.generate()
        created_at = datetime.now()

        workflow = Workflow(
            id=workflow_id,
            name="Test Workflow",
            type=WorkflowType.CUSTOM,
            status=WorkflowStatus.PENDING,
            parameters={"param1": "value1"},
            steps=[{"step": "test"}],
            dependencies=["dep1"],
            metadata={"key": "value"},
            created_at=created_at
        )

        assert workflow.id == workflow_id
        assert workflow.name == "Test Workflow"
        assert workflow.type == WorkflowType.CUSTOM
        assert workflow.status == WorkflowStatus.PENDING
        assert workflow.parameters == {"param1": "value1"}
        assert workflow.steps == [{"step": "test"}]
        assert workflow.dependencies == ["dep1"]
        assert workflow.metadata == {"key": "value"}

    def test_workflow_validation(self):
        """Test workflow validation."""
        workflow_id = WorkflowId.generate()
        workflow = Workflow(
            id=workflow_id,
            name="",  # Empty name should fail
            type=WorkflowType.CUSTOM,
            status=WorkflowStatus.PENDING,
            parameters={},
            steps=[],
            dependencies=[]
        )

        with pytest.raises(ValueError):
            workflow.validate()

    def test_workflow_state_transitions(self):
        """Test workflow state transitions."""
        workflow_id = WorkflowId.generate()
        workflow = Workflow(
            id=workflow_id,
            name="Test Workflow",
            type=WorkflowType.CUSTOM,
            status=WorkflowStatus.PENDING,
            parameters={},
            steps=[],
            dependencies=[]
        )

        assert workflow.can_start() is True
        assert workflow.can_cancel() is True
        assert workflow.is_completed() is False

        # Test starting workflow
        workflow.start()
        assert workflow.status == WorkflowStatus.RUNNING
        assert workflow.started_at is not None