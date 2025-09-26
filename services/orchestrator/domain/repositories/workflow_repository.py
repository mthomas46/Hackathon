"""Workflow repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.workflow import Workflow
from ..value_objects.workflow_id import WorkflowId
from ..value_objects.workflow_status import WorkflowStatus


class WorkflowRepository(ABC):
    """Abstract repository for workflow persistence."""

    @abstractmethod
    async def save(self, workflow: Workflow) -> None:
        """Save a workflow."""
        pass

    @abstractmethod
    async def find_by_id(self, workflow_id: WorkflowId) -> Optional[Workflow]:
        """Find a workflow by ID."""
        pass

    @abstractmethod
    async def find_by_status(self, status: WorkflowStatus) -> List[Workflow]:
        """Find workflows by status."""
        pass

    @abstractmethod
    async def find_all(self) -> List[Workflow]:
        """Find all workflows."""
        pass

    @abstractmethod
    async def delete(self, workflow_id: WorkflowId) -> None:
        """Delete a workflow by ID."""
        pass

    @abstractmethod
    async def exists(self, workflow_id: WorkflowId) -> bool:
        """Check if a workflow exists."""
        pass
