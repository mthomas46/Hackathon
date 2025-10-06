"""Workflow Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from services.mcp_orchestrator.domain.entities.workflow import Workflow
from services.mcp_orchestrator.domain.value_objects.workflow_state import WorkflowState


class WorkflowRepository(ABC):
    """
    Abstract repository interface for Workflow entities.
    
    Defines persistence operations for workflows without
    specifying implementation details.
    """
    
    @abstractmethod
    async def save(self, workflow: Workflow) -> None:
        """
        Save a workflow (create or update).
        
        Args:
            workflow: Workflow to save
        
        Raises:
            RepositoryError: If save fails
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """
        Find a workflow by ID.
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Workflow if found, None otherwise
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_user_id(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Workflow]:
        """
        Find workflows by user ID.
        
        Args:
            user_id: User ID
            limit: Optional limit on results
        
        Returns:
            List of workflows
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_state(
        self,
        state: WorkflowState,
        limit: Optional[int] = None
    ) -> List[Workflow]:
        """
        Find workflows by state.
        
        Args:
            state: Workflow state
            limit: Optional limit on results
        
        Returns:
            List of workflows
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_active_workflows(self, limit: Optional[int] = None) -> List[Workflow]:
        """
        Find all active workflows (not terminal states).
        
        Args:
            limit: Optional limit on results
        
        Returns:
            List of active workflows
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def delete(self, workflow_id: str) -> bool:
        """
        Delete a workflow.
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            RepositoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def count_by_state(self, state: WorkflowState) -> int:
        """
        Count workflows by state.
        
        Args:
            state: Workflow state
        
        Returns:
            Count of workflows
        
        Raises:
            RepositoryError: If query fails
        """
        pass

