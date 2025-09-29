"""Repository Interfaces"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ...domain.workflow_management import Workflow, WorkflowExecution, WorkflowId, ExecutionId
from ...domain.service_registry import Service, ServiceId


class WorkflowRepositoryInterface(ABC):
    """Interface for workflow repository."""

    @abstractmethod
    def save_workflow(self, workflow: Workflow) -> bool:
        """Save a workflow."""
        pass

    @abstractmethod
    def get_workflow(self, workflow_id: WorkflowId) -> Optional[Workflow]:
        """Get a workflow by ID."""
        pass

    @abstractmethod
    def list_workflows(
        self,
        name_filter: Optional[str] = None,
        tag_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        created_by_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Workflow]:
        """List workflows with optional filters."""
        pass

    @abstractmethod
    def delete_workflow(self, workflow_id: WorkflowId) -> bool:
        """Delete a workflow."""
        pass

    @abstractmethod
    def update_workflow(self, workflow: Workflow) -> bool:
        """Update a workflow."""
        pass


class WorkflowExecutionRepositoryInterface(ABC):
    """Interface for workflow execution repository."""

    @abstractmethod
    def save_execution(self, execution: WorkflowExecution) -> bool:
        """Save a workflow execution."""
        pass

    @abstractmethod
    def get_execution(self, execution_id: ExecutionId) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        pass

    @abstractmethod
    def list_executions(
        self,
        workflow_id_filter: Optional[WorkflowId] = None,
        status_filter: Optional[str] = None,
        correlation_id_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """List workflow executions with optional filters."""
        pass

    @abstractmethod
    def update_execution(self, execution: WorkflowExecution) -> bool:
        """Update a workflow execution."""
        pass

    @abstractmethod
    def delete_execution(self, execution_id: ExecutionId) -> bool:
        """Delete a workflow execution."""
        pass


class ServiceRepositoryInterface(ABC):
    """Interface for service repository."""

    @abstractmethod
    def save_service(self, service: Service) -> bool:
        """Save a service."""
        pass

    @abstractmethod
    def get_service(self, service_id: ServiceId) -> Optional[Service]:
        """Get a service by ID."""
        pass

    @abstractmethod
    def list_services(self) -> List[Service]:
        """List all services."""
        pass

    @abstractmethod
    def delete_service(self, service_id: ServiceId) -> bool:
        """Delete a service."""
        pass

    @abstractmethod
    def update_service(self, service: Service) -> bool:
        """Update a service."""
        pass
