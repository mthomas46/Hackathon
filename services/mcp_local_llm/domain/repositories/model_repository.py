"""Model repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from ..entities import Model


class ModelRepository(ABC):
    """
    Repository interface for Model entity persistence.
    
    This interface defines the contract for model storage without
    specifying implementation details (in-memory, database, etc.).
    """
    
    @abstractmethod
    async def get(self, model_id: UUID) -> Optional[Model]:
        """
        Retrieve a model by its ID.
        
        Args:
            model_id: Unique model identifier
            
        Returns:
            Model if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Model]:
        """
        Retrieve a model by its name.
        
        Args:
            name: Model name (e.g., "llama2:7b")
            
        Returns:
            Model if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Model]:
        """
        List all models.
        
        Returns:
            List of all models
        """
        pass
    
    @abstractmethod
    async def list_loaded(self) -> List[Model]:
        """
        List all currently loaded models.
        
        Returns:
            List of models with status READY
        """
        pass
    
    @abstractmethod
    async def save(self, model: Model) -> Model:
        """
        Save or update a model.
        
        Args:
            model: Model entity to save
            
        Returns:
            Saved model with any generated fields populated
        """
        pass
    
    @abstractmethod
    async def delete(self, model_id: UUID) -> bool:
        """
        Delete a model.
        
        Args:
            model_id: ID of model to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, name: str) -> bool:
        """
        Check if a model exists.
        
        Args:
            name: Model name
            
        Returns:
            True if model exists
        """
        pass
    
    @abstractmethod
    async def get_total_memory_usage(self) -> float:
        """
        Get total memory usage of all loaded models.
        
        Returns:
            Total memory usage in MB
        """
        pass

