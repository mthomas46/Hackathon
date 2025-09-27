"""In-memory implementation of User Repository for the User Store service.

This module provides an in-memory repository implementation for development
and testing purposes. In production, this would be replaced with a database-backed
implementation.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone

from ...domain.entities.user import User, UserPreferences, UserRole, UserStatus
from ...domain.repositories.user_repository import UserRepository, UserPreferencesRepository


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of UserRepository."""

    def __init__(self):
        """Initialize the repository with empty storage."""
        self._users: Dict[str, User] = {}
        self._email_index: Dict[str, str] = {}  # email -> user_id
        self._username_index: Dict[str, str] = {}  # username -> user_id
        self._document_index: Dict[str, List[str]] = {}  # document_id -> [user_ids]
        self._topic_index: Dict[str, List[str]] = {}  # topic -> [user_ids]
        self._service_index: Dict[str, List[str]] = {}  # service -> [user_ids]

    async def save(self, user: User) -> None:
        """Save a user to the repository."""
        self._users[user.id] = user
        self._email_index[user.email] = user.id
        self._username_index[user.username] = user.id

        # Update indexes
        self._update_indexes(user)

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by their ID."""
        return self._users.get(user_id)

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by their email address."""
        user_id = self._email_index.get(email)
        return self._users.get(user_id) if user_id else None

    async def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by their username."""
        user_id = self._username_index.get(username)
        return self._users.get(user_id) if user_id else None

    async def find_by_role(self, role: UserRole) -> List[User]:
        """Find all users with a specific role."""
        return [user for user in self._users.values() if user.role == role]

    async def find_by_status(self, status: UserStatus) -> List[User]:
        """Find all users with a specific status."""
        return [user for user in self._users.values() if user.status == status]

    async def find_users_by_document(self, document_id: str) -> List[User]:
        """Find all users related to a specific document."""
        user_ids = self._document_index.get(document_id, [])
        return [self._users[user_id] for user_id in user_ids if user_id in self._users]

    async def find_users_by_topic(self, topic: str) -> List[User]:
        """Find all users interested in a specific topic."""
        user_ids = self._topic_index.get(topic, [])
        return [self._users[user_id] for user_id in user_ids if user_id in self._users]

    async def find_users_by_service(self, service_name: str) -> List[User]:
        """Find all users subscribed to a specific service."""
        user_ids = self._service_index.get(service_name, [])
        return [self._users[user_id] for user_id in user_ids if user_id in self._users]

    async def search_users(self, query: str, limit: int = 50) -> List[User]:
        """Search users by name, email, or username."""
        query_lower = query.lower()
        matching_users = []

        for user in self._users.values():
            if (query_lower in user.email.lower() or
                query_lower in user.username.lower() or
                query_lower in user.display_name.lower()):
                matching_users.append(user)

        return matching_users[:limit]

    async def list_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users with pagination."""
        all_users = list(self._users.values())
        return all_users[offset:offset + limit]

    async def update(self, user: User) -> None:
        """Update an existing user."""
        if user.id in self._users:
            self._users[user.id] = user
            self._update_indexes(user)

    async def delete(self, user_id: str) -> bool:
        """Delete a user by ID."""
        if user_id in self._users:
            user = self._users[user_id]
            del self._users[user_id]

            # Remove from indexes
            if user.email in self._email_index:
                del self._email_index[user.email]
            if user.username in self._username_index:
                del self._username_index[user.username]

            # Remove from relationship indexes
            self._remove_from_indexes(user)

            return True
        return False

    async def exists(self, user_id: str) -> bool:
        """Check if a user exists."""
        return user_id in self._users

    async def count(self) -> int:
        """Count total number of users."""
        return len(self._users)

    def _update_indexes(self, user: User) -> None:
        """Update the relationship indexes for a user."""
        # Document relationships
        for doc_id in user.document_relationships:
            if doc_id not in self._document_index:
                self._document_index[doc_id] = []
            if user.id not in self._document_index[doc_id]:
                self._document_index[doc_id].append(user.id)

        # Topic interests
        for topic in user.topic_interests:
            if topic not in self._topic_index:
                self._topic_index[topic] = []
            if user.id not in self._topic_index[topic]:
                self._topic_index[topic].append(user.id)

        # Service subscriptions
        for service in user.service_subscriptions:
            if service not in self._service_index:
                self._service_index[service] = []
            if user.id not in self._service_index[service]:
                self._service_index[service].append(user.id)

    def _remove_from_indexes(self, user: User) -> None:
        """Remove a user from all relationship indexes."""
        # Remove from document index
        for doc_id in user.document_relationships:
            if doc_id in self._document_index and user.id in self._document_index[doc_id]:
                self._document_index[doc_id].remove(user.id)
                if not self._document_index[doc_id]:
                    del self._document_index[doc_id]

        # Remove from topic index
        for topic in user.topic_interests:
            if topic in self._topic_index and user.id in self._topic_index[topic]:
                self._topic_index[topic].remove(user.id)
                if not self._topic_index[topic]:
                    del self._topic_index[topic]

        # Remove from service index
        for service in user.service_subscriptions:
            if service in self._service_index and user.id in self._service_index[service]:
                self._service_index[service].remove(user.id)
                if not self._service_index[service]:
                    del self._service_index[service]


class InMemoryUserPreferencesRepository(UserPreferencesRepository):
    """In-memory implementation of UserPreferencesRepository."""

    def __init__(self):
        """Initialize the repository with empty storage."""
        self._preferences: Dict[str, UserPreferences] = {}

    async def save(self, preferences: UserPreferences) -> None:
        """Save user preferences."""
        self._preferences[preferences.user_id] = preferences

    async def find_by_user_id(self, user_id: str) -> Optional[UserPreferences]:
        """Find preferences for a specific user."""
        return self._preferences.get(user_id)

    async def update(self, preferences: UserPreferences) -> None:
        """Update user preferences."""
        self._preferences[preferences.user_id] = preferences

    async def delete(self, user_id: str) -> bool:
        """Delete preferences for a user."""
        if user_id in self._preferences:
            del self._preferences[user_id]
            return True
        return False
