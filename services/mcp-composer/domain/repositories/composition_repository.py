"""Composition Repository Interface - Domain Layer.

Defines the contract for persisting and retrieving Composition entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from services.mcp_composer.domain.entities.composition import Composition


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""
    pass


class DuplicateEntityError(RepositoryError):
    """Raised when trying to create a duplicate entity."""
    pass


class CompositionRepository(ABC):
    """
    Abstract base class for Composition repositories.
    
    Defines the interface that all concrete composition repositories must implement.
    This follows the Repository pattern from Domain-Driven Design.
    """
    
    @abstractmethod
    async def save(self, composition: Composition) -> None:
        """
        Save a composition.
        
        Args:
            composition: The composition to save
            
        Raises:
            RepositoryError: If save fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, composition_id: str) -> Optional[Composition]:
        """
        Retrieve a composition by ID.
        
        Args:
            composition_id: The composition ID
            
        Returns:
            The composition if found, None otherwise
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_all(self) -> List[Composition]:
        """
        Retrieve all compositions.
        
        Returns:
            List of all compositions
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_active(self) -> List[Composition]:
        """
        Retrieve all active compositions.
        
        Returns:
            List of active compositions
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def update(self, composition: Composition) -> None:
        """
        Update an existing composition.
        
        Args:
            composition: The composition to update
            
        Raises:
            EntityNotFoundError: If composition doesn't exist
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def delete(self, composition_id: str) -> None:
        """
        Delete a composition by ID.
        
        Args:
            composition_id: The composition ID
            
        Raises:
            EntityNotFoundError: If composition doesn't exist
            RepositoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def exists(self, composition_id: str) -> bool:
        """
        Check if a composition exists.
        
        Args:
            composition_id: The composition ID
            
        Returns:
            True if composition exists, False otherwise
            
        Raises:
            RepositoryError: If check fails
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        Get the total number of compositions.
        
        Returns:
            The count of compositions
            
        Raises:
            RepositoryError: If count fails
        """
        pass
    
    @abstractmethod
    async def get_by_tag(self, tag: str) -> List[Composition]:
        """
        Retrieve compositions by tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of compositions with the given tag
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
