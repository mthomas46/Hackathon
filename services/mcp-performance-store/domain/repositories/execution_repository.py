"""Execution Repository Interface - Domain Layer.

Defines the contract for persisting and retrieving OrchestrationExecution entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from services.mcp_performance_store.domain.entities.orchestration_execution import OrchestrationExecution
from services.mcp_performance_store.domain.value_objects.execution_status import ExecutionStatus


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""
    pass


class DuplicateEntityError(RepositoryError):
    """Raised when trying to create a duplicate entity."""
    pass


class ExecutionRepository(ABC):
    """
    Abstract base class for Execution repositories.
    
    Defines the interface for persisting and querying orchestration executions.
    """
    
    @abstractmethod
    async def save(self, execution: OrchestrationExecution) -> None:
        """
        Save an execution.
        
        Args:
            execution: The execution to save
            
        Raises:
            DuplicateEntityError: If execution already exists
            RepositoryError: If save fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, execution_id: str) -> Optional[OrchestrationExecution]:
        """
        Retrieve an execution by ID.
        
        Args:
            execution_id: The execution ID
            
        Returns:
            The execution if found, None otherwise
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_by_pattern(
        self,
        pattern_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrchestrationExecution]:
        """
        Retrieve executions for a specific pattern.
        
        Args:
            pattern_name: The pattern name
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of executions for the pattern
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_by_status(
        self,
        status: ExecutionStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrchestrationExecution]:
        """
        Retrieve executions by status.
        
        Args:
            status: The execution status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of executions with the given status
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_by_date_range(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000
    ) -> List[OrchestrationExecution]:
        """
        Retrieve executions within a date range.
        
        Args:
            start: Start datetime (inclusive)
            end: End datetime (inclusive)
            limit: Maximum number of results
            
        Returns:
            List of executions in the date range
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_recent(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrchestrationExecution]:
        """
        Retrieve most recent executions.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of recent executions, newest first
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_by_composition(
        self,
        composition_id: str,
        limit: int = 100
    ) -> List[OrchestrationExecution]:
        """
        Retrieve executions for a specific composition.
        
        Args:
            composition_id: The composition ID
            limit: Maximum number of results
            
        Returns:
            List of executions for the composition
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        Get total number of executions.
        
        Returns:
            The count of executions
            
        Raises:
            RepositoryError: If count fails
        """
        pass
    
    @abstractmethod
    async def count_by_status(self, status: ExecutionStatus) -> int:
        """
        Get count of executions by status.
        
        Args:
            status: The execution status
            
        Returns:
            The count of executions with that status
            
        Raises:
            RepositoryError: If count fails
        """
        pass
    
    @abstractmethod
    async def count_by_pattern(self, pattern_name: str) -> int:
        """
        Get count of executions for a pattern.
        
        Args:
            pattern_name: The pattern name
            
        Returns:
            The count of executions for that pattern
            
        Raises:
            RepositoryError: If count fails
        """
        pass
    
    @abstractmethod
    async def delete(self, execution_id: str) -> None:
        """
        Delete an execution by ID.
        
        Args:
            execution_id: The execution ID
            
        Raises:
            EntityNotFoundError: If execution doesn't exist
            RepositoryError: If deletion fails
        """
        pass
