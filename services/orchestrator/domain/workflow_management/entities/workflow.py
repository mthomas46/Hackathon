"""Workflow Entity"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..value_objects.workflow_id import WorkflowId
from .workflow_parameter import WorkflowParameter
from .workflow_action import WorkflowAction


class WorkflowStatus(Enum):
    """Workflow definition status."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


@dataclass
class Workflow:
    """Entity representing a workflow definition."""

    workflow_id: WorkflowId = field(default_factory=WorkflowId.generate)
    name: str = ""
    description: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    tags: List[str] = field(default_factory=list)

    # Aggregated entities
    parameters: List[WorkflowParameter] = field(default_factory=list)
    actions: List[WorkflowAction] = field(default_factory=list)

    def __post_init__(self):
        """Validate workflow after initialization."""
        # Only validate required fields if they are explicitly set (not defaults)
        # Domain validation will handle comprehensive validation
        pass

        # Validate parameter names are unique
        param_names = [p.name for p in self.parameters]
        if len(param_names) != len(set(param_names)):
            raise ValueError("Parameter names must be unique")

        # Validate action IDs are unique
        action_ids = [a.action_id for a in self.actions]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("Action IDs must be unique")

    def add_parameter(self, parameter: WorkflowParameter):
        """Add a parameter to the workflow."""
        if any(p.name == parameter.name for p in self.parameters):
            raise ValueError(f"Parameter '{parameter.name}' already exists")

        self.parameters.append(parameter)
        self._update_timestamp()

    def remove_parameter(self, param_name: str):
        """Remove a parameter from the workflow."""
        self.parameters = [p for p in self.parameters if p.name != param_name]
        self._update_timestamp()

    def add_action(self, action: WorkflowAction):
        """Add an action to the workflow."""
        if any(a.action_id == action.action_id for a in self.actions):
            raise ValueError(f"Action '{action.action_id}' already exists")

        self.actions.append(action)
        self._update_timestamp()

    def remove_action(self, action_id: str):
        """Remove an action from the workflow."""
        self.actions = [a for a in self.actions if a.action_id != action_id]
        self._update_timestamp()

    def get_parameter(self, name: str) -> Optional[WorkflowParameter]:
        """Get a parameter by name."""
        return next((p for p in self.parameters if p.name == name), None)

    def get_action(self, action_id: str) -> Optional[WorkflowAction]:
        """Get an action by ID."""
        return next((a for a in self.actions if a.action_id == action_id), None)

    def validate_parameters(self, param_values: Dict[str, Any]) -> tuple[bool, str]:
        """Validate parameter values against workflow parameters."""
        for param in self.parameters:
            if param.name not in param_values:
                if param.required:
                    return False, f"Missing required parameter: {param.name}"
                continue

            valid, error = param.validate_value(param_values[param.name])
            if not valid:
                return False, error

        return True, ""

    def get_required_services(self) -> List[str]:
        """Get all services required by this workflow."""
        services = set()
        for action in self.actions:
            services.update(action.get_required_services())
        return list(services)

    def activate(self):
        """Activate the workflow."""
        if self.status != WorkflowStatus.DRAFT:
            raise ValueError(f"Cannot activate workflow in {self.status.value} status")

        # Validate workflow has at least one action
        if not self.actions:
            raise ValueError("Workflow must have at least one action to be activated")

        self.status = WorkflowStatus.ACTIVE
        self._update_timestamp()

    def archive(self):
        """Archive the workflow."""
        if self.status == WorkflowStatus.ARCHIVED:
            return

        self.status = WorkflowStatus.ARCHIVED
        self._update_timestamp()

    def _update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "workflow_id": self.workflow_id.value,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "tags": self.tags,
            "parameters": [p.to_dict() for p in self.parameters],
            "actions": [a.to_dict() for a in self.actions]
        }
