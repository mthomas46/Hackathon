"""Context session repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from ..entities import ContextSession


class ContextRepository(ABC):
    """Repository interface for ContextSession entity persistence."""
    
    @abstractmethod
    async def get(self, context_id: UUID) -> Optional[ContextSession]:
        """Get context session by ID."""
        pass
    
    @abstractmethod
    async def save(self, context: ContextSession) -> ContextSession:
        """Save or update context session."""
        pass
    
    @abstractmethod
    async def delete(self, context_id: UUID) -> bool:
        """Delete context session."""
        pass
    
    @abstractmethod
    async def list_by_model(self, model_name: str) -> List[ContextSession]:
        """List all contexts for a specific model."""
        pass
    
    @abstractmethod
    async def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """
        Cleanup expired context sessions.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of contexts deleted
        """
        pass

