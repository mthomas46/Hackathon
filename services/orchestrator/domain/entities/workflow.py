"""Workflow domain entity."""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from ..value_objects.workflow_id import WorkflowId
from ..value_objects.workflow_status import WorkflowStatus
from ..value_objects.workflow_type import WorkflowType


@dataclass
class Workflow:
    """Domain entity representing a workflow orchestration."""

    id: WorkflowId
    name: str
    type: WorkflowType
    status: WorkflowStatus
    parameters: Dict[str, Any]
    steps: List[Dict[str, Any]]  # Workflow step definitions
    dependencies: List[str]  # IDs of dependent workflows
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    updated_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.parameters is None:
            self.parameters = {}
        if self.steps is None:
            self.steps = []
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}

    def validate(self) -> None:
        """Validate the workflow according to domain rules."""
        if not self.name or not self.name.strip():
            raise ValueError("Workflow name cannot be empty")

        if len(self.name) > 200:
            raise ValueError("Workflow name too long (max 200 characters)")

        if not self.steps:
            raise ValueError("Workflow must have at least one step")

        if len(self.steps) > 100:
            raise ValueError("Workflow cannot have more than 100 steps")

        # Validate dependencies don't create cycles
        if str(self.id) in self.dependencies:
            raise ValueError("Workflow cannot depend on itself")

    def can_start(self) -> bool:
        """Check if workflow can be started."""
        return self.status == WorkflowStatus.PENDING

    def can_cancel(self) -> bool:
        """Check if workflow can be cancelled."""
        return self.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]

    def start(self) -> None:
        """Start the workflow execution."""
        if not self.can_start():
            raise ValueError(f"Cannot start workflow in status: {self.status}")

        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.now()
        self.updated_at = self.started_at

    def complete(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark workflow as completed."""
        if self.status != WorkflowStatus.RUNNING:
            raise ValueError(f"Cannot complete workflow in status: {self.status}")

        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = self.completed_at

        if result:
            self.metadata.update(result)

    def fail(self, error: str) -> None:
        """Mark workflow as failed."""
        if self.status not in [WorkflowStatus.RUNNING, WorkflowStatus.PENDING]:
            raise ValueError(f"Cannot fail workflow in status: {self.status}")

        self.status = WorkflowStatus.FAILED
        self.completed_at = datetime.now()
        self.updated_at = self.completed_at
        self.metadata['error'] = error

    def cancel(self) -> None:
        """Cancel the workflow."""
        if not self.can_cancel():
            raise ValueError(f"Cannot cancel workflow in status: {self.status}")

        self.status = WorkflowStatus.CANCELLED
        self.updated_at = datetime.now()

    def is_completed(self) -> bool:
        """Check if workflow is in a terminal state."""
        return self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]

    def get_execution_time(self) -> Optional[float]:
        """Get execution time in seconds."""
        if not self.started_at or not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': str(self.id),
            'name': self.name,
            'type': str(self.type),
            'status': str(self.status),
            'parameters': self.parameters,
            'steps': self.steps,
            'dependencies': self.dependencies,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """Create from dictionary representation."""
        return cls(
            id=WorkflowId(data['id']),
            name=data['name'],
            type=WorkflowType(data['type']),
            status=WorkflowStatus(data['status']),
            parameters=data.get('parameters', {}),
            steps=data.get('steps', []),
            dependencies=data.get('dependencies', []),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        )
