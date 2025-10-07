"""Pattern Performance Repository Interface - Domain Layer.

Defines the contract for persisting and retrieving PatternPerformance entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from services.mcp_performance_store.domain.entities.pattern_performance import PatternPerformance


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""
    pass


class DuplicateEntityError(RepositoryError):
    """Raised when trying to create a duplicate entity."""
    pass


class PatternPerformanceRepository(ABC):
    """
    Abstract base class for Pattern Performance repositories.
    
    Defines the interface for persisting and querying pattern performance metrics.
    """
    
    @abstractmethod
    async def save(self, performance: PatternPerformance) -> None:
        """
        Save pattern performance metrics.
        
        Args:
            performance: The pattern performance to save
            
        Raises:
            DuplicateEntityError: If pattern already exists
            RepositoryError: If save fails
        """
        pass
    
    @abstractmethod
    async def get_by_pattern(self, pattern_name: str) -> Optional[PatternPerformance]:
        """
        Retrieve performance metrics for a pattern.
        
        Args:
            pattern_name: The pattern name
            
        Returns:
            The pattern performance if found, None otherwise
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_all(self) -> List[PatternPerformance]:
        """
        Retrieve all pattern performance metrics.
        
        Returns:
            List of all pattern performances
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_top_performers(self, limit: int = 10) -> List[PatternPerformance]:
        """
        Retrieve top performing patterns by success rate.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of top performing patterns
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_degrading_patterns(self) -> List[PatternPerformance]:
        """
        Retrieve patterns with degrading performance.
        
        Returns:
            List of patterns showing performance degradation
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def update(self, performance: PatternPerformance) -> None:
        """
        Update existing pattern performance metrics.
        
        Args:
            performance: The pattern performance to update
            
        Raises:
            EntityNotFoundError: If pattern doesn't exist
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def exists(self, pattern_name: str) -> bool:
        """
        Check if pattern performance exists.
        
        Args:
            pattern_name: The pattern name
            
        Returns:
            True if pattern exists, False otherwise
            
        Raises:
            RepositoryError: If check fails
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        Get total number of tracked patterns.
        
        Returns:
            The count of patterns
            
        Raises:
            RepositoryError: If count fails
        """
        pass
    
    @abstractmethod
    async def delete(self, pattern_name: str) -> None:
        """
        Delete pattern performance metrics.
        
        Args:
            pattern_name: The pattern name
            
        Raises:
            EntityNotFoundError: If pattern doesn't exist
            RepositoryError: If deletion fails
        """
        pass
