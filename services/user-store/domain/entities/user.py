"""User domain entity for the User Store service.

This module defines the User entity and related domain logic for managing
user information, relationships, and preferences within the ecosystem.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

from services.shared.domain import BaseEntity


class UserRole(Enum):
    """Enumeration of user roles in the system."""
    ADMIN = "admin"
    ANALYST = "analyst"
    DEVELOPER = "developer"
    MANAGER = "manager"
    VIEWER = "viewer"


class UserStatus(Enum):
    """Enumeration of user account statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


@dataclass
class UserPreferences(BaseEntity):
    """User notification and display preferences."""

    user_id: str
    email_notifications: bool = True
    webhook_notifications: bool = False
    notification_channels: List[str] = field(default_factory=lambda: ["email"])
    theme: str = "light"
    timezone: str = "UTC"
    language: str = "en"

    def __post_init__(self):
        """Validate preferences after initialization."""
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        if not self.notification_channels:
            self.notification_channels = ["email"]


@dataclass
class User(BaseEntity):
    """Domain entity representing a user in the system.

    The User entity encapsulates all user-related information including
    profile data, relationships to documents, and system preferences.
    """

    id: str = field(default_factory=lambda: f"user_{datetime.now(timezone.utc).timestamp()}")
    email: str = ""
    username: str = ""
    display_name: str = ""
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.ACTIVE

    # Profile information
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)

    # Relationship tracking
    document_relationships: List[str] = field(default_factory=list)  # Document IDs
    service_subscriptions: List[str] = field(default_factory=list)   # Service names
    topic_interests: List[str] = field(default_factory=list)         # Topic tags

    # Expertise tracking (inferred from document relationships)
    user_tags: List[str] = field(default_factory=list)  # Inferred expertise tags

    # Notification contact information
    contact_email: Optional[str] = None      # Alternative contact email
    contact_webhook: Optional[str] = None    # Webhook URL for notifications
    contact_slack: Optional[str] = None      # Slack webhook or user ID
    notification_preferences: Dict[str, any] = field(default_factory=dict)  # Custom notification settings

    # System tracking
    last_login_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate user after initialization."""
        if not self.email.strip():
            raise ValueError("Email cannot be empty")
        if not self.username.strip():
            raise ValueError("Username cannot be empty")
        if "@" not in self.email:
            raise ValueError("Invalid email format")
        if not self.display_name.strip():
            self.display_name = self.username

    def add_document_relationship(self, document_id: str) -> None:
        """Add a relationship to a document."""
        if document_id not in self.document_relationships:
            self.document_relationships.append(document_id)
            self.updated_at = datetime.now(timezone.utc)

    def remove_document_relationship(self, document_id: str) -> None:
        """Remove a relationship to a document."""
        if document_id in self.document_relationships:
            self.document_relationships.remove(document_id)
            self.updated_at = datetime.now(timezone.utc)

    def add_topic_interest(self, topic: str) -> None:
        """Add a topic of interest."""
        if topic not in self.topic_interests:
            self.topic_interests.append(topic)
            self.updated_at = datetime.now(timezone.utc)

    def subscribe_to_service(self, service_name: str) -> None:
        """Subscribe to a service for notifications."""
        if service_name not in self.service_subscriptions:
            self.service_subscriptions.append(service_name)
            self.updated_at = datetime.now(timezone.utc)

    def record_login(self) -> None:
        """Record a user login event."""
        self.last_login_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def update_profile(self, **kwargs) -> None:
        """Update user profile information."""
        allowed_fields = {
            'display_name', 'avatar_url', 'bio', 'metadata',
            'role', 'status', 'topic_interests', 'service_subscriptions',
            'user_tags', 'contact_email', 'contact_webhook', 'contact_slack',
            'notification_preferences'
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(self, key, value)

        self.updated_at = datetime.now(timezone.utc)

    def add_expertise_tag(self, tag: str) -> None:
        """Add an expertise tag to the user."""
        if tag not in self.user_tags:
            self.user_tags.append(tag)
            self.updated_at = datetime.now(timezone.utc)

    def remove_expertise_tag(self, tag: str) -> None:
        """Remove an expertise tag from the user."""
        if tag in self.user_tags:
            self.user_tags.remove(tag)
            self.updated_at = datetime.now(timezone.utc)

    def infer_expertise_from_documents(self, document_tags: List[str]) -> None:
        """Infer user expertise from document tags.

        This method analyzes the tags from documents the user has worked on
        and adds relevant expertise tags to the user's profile.
        """
        # Simple inference: add document tags as expertise if user has worked on multiple docs with same tag
        tag_counts = {}
        for tag in document_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Add tags that appear in multiple documents (shows consistent expertise)
        for tag, count in tag_counts.items():
            if count >= 2 and tag not in self.user_tags:
                self.add_expertise_tag(tag)

    def update_contact_info(self, **contact_info) -> None:
        """Update contact information for notifications."""
        contact_fields = {'contact_email', 'contact_webhook', 'contact_slack'}

        for field, value in contact_info.items():
            if field in contact_fields:
                setattr(self, field, value)

        self.updated_at = datetime.now(timezone.utc)

    def get_notification_contacts(self) -> Dict[str, Optional[str]]:
        """Get all notification contact methods."""
        return {
            'email': self.contact_email or self.email,
            'webhook': self.contact_webhook,
            'slack': self.contact_slack
        }

    def has_expertise_in(self, topic: str) -> bool:
        """Check if user has expertise in a specific topic."""
        return topic in self.user_tags or topic in self.topic_interests

    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE

    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role."""
        return self.role == role

    def can_access_service(self, service_name: str) -> bool:
        """Check if user can access a specific service."""
        # Admin and analyst roles have full access
        if self.role in [UserRole.ADMIN, UserRole.ANALYST]:
            return True

        # Developers have access to development-related services
        if self.role == UserRole.DEVELOPER and service_name in [
            'code-analyzer', 'source-agent', 'github-mcp'
        ]:
            return True

        # Managers have access to analysis and reporting services
        if self.role == UserRole.MANAGER and service_name in [
            'analysis-service', 'summarizer-hub', 'unified-api-dashboard'
        ]:
            return True

        # All active users can access basic services
        return service_name in [
            'notification-service', 'user-store', 'interpreter'
        ]
