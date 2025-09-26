"""UI State repository interface for DDD compliance."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.ui_state import UIStateEntity


class UIStateRepository(ABC):
    """Abstract repository for UI state operations."""

    @abstractmethod
    async def save(self, ui_state: UIStateEntity) -> None:
        """Save UI state."""
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> Optional[UIStateEntity]:
        """Find UI state by user ID."""
        pass

    @abstractmethod
    async def find_by_session_id(self, session_id: str) -> Optional[UIStateEntity]:
        """Find UI state by session ID."""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete UI state for user."""
        pass
