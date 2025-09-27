"""SQLite implementation of User Repository for the User Store service.

This module provides a SQLite-based repository implementation for persistent
user data storage and retrieval operations.
"""

import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone

from ...domain.entities.user import User, UserPreferences, UserRole, UserStatus
from ...domain.repositories.user_repository import UserRepository, UserPreferencesRepository


class SQLiteUserRepository(UserRepository):
    """SQLite implementation of UserRepository."""

    def __init__(self, db_path: str = "user_store.db"):
        """Initialize the repository with database connection."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    avatar_url TEXT,
                    bio TEXT,
                    document_relationships TEXT NOT NULL, -- JSON array
                    service_subscriptions TEXT NOT NULL,    -- JSON array
                    topic_interests TEXT NOT NULL,          -- JSON array
                    user_tags TEXT NOT NULL,                -- JSON array of inferred expertise tags
                    contact_email TEXT,
                    contact_webhook TEXT,
                    contact_slack TEXT,
                    notification_preferences TEXT,          -- JSON object
                    last_login_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def _user_from_row(self, row) -> User:
        """Convert database row to User entity."""
        return User(
            id=row[0],
            email=row[1],
            username=row[2],
            display_name=row[3],
            role=UserRole(row[4]),
            status=UserStatus(row[5]),
            avatar_url=row[6],
            bio=row[7],
            document_relationships=json.loads(row[8]),
            service_subscriptions=json.loads(row[9]),
            topic_interests=json.loads(row[10]),
            user_tags=json.loads(row[11]) if row[11] else [],
            contact_email=row[12],
            contact_webhook=row[13],
            contact_slack=row[14],
            notification_preferences=json.loads(row[15]) if row[15] else {},
            last_login_at=datetime.fromisoformat(row[16]) if row[16] else None,
            created_at=datetime.fromisoformat(row[17]),
            updated_at=datetime.fromisoformat(row[18])
        )

    async def save(self, user: User) -> None:
        """Save a user to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users (
                    id, email, username, display_name, role, status,
                    avatar_url, bio, document_relationships, service_subscriptions,
                    topic_interests, user_tags, contact_email, contact_webhook,
                    contact_slack, notification_preferences, last_login_at,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.id, user.email, user.username, user.display_name, user.role.value, user.status.value,
                user.avatar_url, user.bio,
                json.dumps(user.document_relationships),
                json.dumps(user.service_subscriptions),
                json.dumps(user.topic_interests),
                json.dumps(getattr(user, 'user_tags', [])),
                getattr(user, 'contact_email', None),
                getattr(user, 'contact_webhook', None),
                getattr(user, 'contact_slack', None),
                json.dumps(getattr(user, 'notification_preferences', {})),
                user.last_login_at.isoformat() if user.last_login_at else None,
                user.created_at.isoformat(),
                user.updated_at.isoformat()
            ))
            conn.commit()

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by their ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return self._user_from_row(row) if row else None

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by their email address."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return self._user_from_row(row) if row else None

    async def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by their username."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return self._user_from_row(row) if row else None

    async def find_by_role(self, role: UserRole) -> List[User]:
        """Find all users with a specific role."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users WHERE role = ?", (role.value,))
            return [self._user_from_row(row) for row in cursor.fetchall()]

    async def find_by_status(self, status: UserStatus) -> List[User]:
        """Find all users with a specific status."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users WHERE status = ?", (status.value,))
            return [self._user_from_row(row) for row in cursor.fetchall()]

    async def find_users_by_document(self, document_id: str) -> List[User]:
        """Find all users related to a specific document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users WHERE document_relationships LIKE ?", (f'%{document_id}%',))
            users = []
            for row in cursor.fetchall():
                user = self._user_from_row(row)
                if document_id in user.document_relationships:
                    users.append(user)
            return users

    async def find_users_by_topic(self, topic: str) -> List[User]:
        """Find all users interested in a specific topic."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users WHERE topic_interests LIKE ?", (f'%{topic}%',))
            users = []
            for row in cursor.fetchall():
                user = self._user_from_row(row)
                if topic in user.topic_interests:
                    users.append(user)
            return users

    async def find_users_by_expertise(self, topic: str) -> List[User]:
        """Find all users with expertise in a specific topic (based on document tags)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users WHERE user_tags LIKE ?", (f'%{topic}%',))
            users = []
            for row in cursor.fetchall():
                user = self._user_from_row(row)
                if topic in getattr(user, 'user_tags', []):
                    users.append(user)
            return users

    async def find_users_by_service(self, service_name: str) -> List[User]:
        """Find all users subscribed to a specific service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users WHERE service_subscriptions LIKE ?", (f'%{service_name}%',))
            users = []
            for row in cursor.fetchall():
                user = self._user_from_row(row)
                if service_name in user.service_subscriptions:
                    users.append(user)
            return users

    async def search_users(self, query: str, limit: int = 50) -> List[User]:
        """Search users by name, email, or username."""
        query_lower = f"%{query.lower()}%"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM users
                WHERE LOWER(email) LIKE ? OR LOWER(username) LIKE ? OR LOWER(display_name) LIKE ?
                LIMIT ?
            """, (query_lower, query_lower, query_lower, limit))
            return [self._user_from_row(row) for row in cursor.fetchall()]

    async def list_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users with pagination."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users LIMIT ? OFFSET ?", (limit, offset))
            return [self._user_from_row(row) for row in cursor.fetchall()]

    async def update(self, user: User) -> None:
        """Update an existing user."""
        await self.save(user)  # SQLite INSERT OR REPLACE handles updates

    async def delete(self, user_id: str) -> bool:
        """Delete a user by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    async def exists(self, user_id: str) -> bool:
        """Check if a user exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM users WHERE id = ? LIMIT 1", (user_id,))
            return cursor.fetchone() is not None

    async def count(self) -> int:
        """Count total number of users."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]


class SQLiteUserPreferencesRepository(UserPreferencesRepository):
    """SQLite implementation of UserPreferencesRepository."""

    def __init__(self, db_path: str = "user_store.db"):
        """Initialize the repository with database connection."""
        self.db_path = db_path

    async def save(self, preferences: UserPreferences) -> None:
        """Save user preferences - stored in users table."""
        # Preferences are stored in the users table, so this is a no-op
        # The UserService handles updating preferences through the user entity
        pass

    async def find_by_user_id(self, user_id: str) -> Optional[UserPreferences]:
        """Find preferences for a specific user - retrieved from users table."""
        # Preferences are stored in the users table, so we need to get them from there
        # This is handled by the UserService
        return None

    async def update(self, preferences: UserPreferences) -> None:
        """Update user preferences - handled through user updates."""
        pass

    async def delete(self, user_id: str) -> bool:
        """Delete preferences for a user - handled through user deletion."""
        return True
