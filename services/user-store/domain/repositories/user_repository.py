"""User repository interface for the User Store service.

This module defines the abstract interface for user data persistence
and retrieval operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.user import User, UserPreferences, UserRole, UserStatus


class UserRepository(ABC):
    """Abstract base class for user repository implementations."""

    @abstractmethod
    async def save(self, user: User) -> None:
        """Save a user to the repository."""
        pass

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by their ID."""
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by their email address."""
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by their username."""
        pass

    @abstractmethod
    async def find_by_role(self, role: UserRole) -> List[User]:
        """Find all users with a specific role."""
        pass

    @abstractmethod
    async def find_by_status(self, status: UserStatus) -> List[User]:
        """Find all users with a specific status."""
        pass

    @abstractmethod
    async def find_users_by_document(self, document_id: str) -> List[User]:
        """Find all users related to a specific document."""
        pass

    @abstractmethod
    async def find_users_by_topic(self, topic: str) -> List[User]:
        """Find all users interested in a specific topic."""
        pass

    @abstractmethod
    async def find_users_by_service(self, service_name: str) -> List[User]:
        """Find all users subscribed to a specific service."""
        pass

    @abstractmethod
    async def search_users(self, query: str, limit: int = 50) -> List[User]:
        """Search users by name, email, or username."""
        pass

    @abstractmethod
    async def list_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users with pagination."""
        pass

    @abstractmethod
    async def update(self, user: User) -> None:
        """Update an existing user."""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a user by ID."""
        pass

    @abstractmethod
    async def exists(self, user_id: str) -> bool:
        """Check if a user exists."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total number of users."""
        pass


class UserPreferencesRepository(ABC):
    """Abstract base class for user preferences repository implementations."""

    @abstractmethod
    async def save(self, preferences: UserPreferences) -> None:
        """Save user preferences."""
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> Optional[UserPreferences]:
        """Find preferences for a specific user."""
        pass

    @abstractmethod
    async def update(self, preferences: UserPreferences) -> None:
        """Update user preferences."""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete preferences for a user."""
        pass
