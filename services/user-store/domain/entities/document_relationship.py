"""Document relationship domain entity for the User Store service.

This module defines entities for managing relationships between users and
documents, including access permissions and interaction tracking.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

from services.shared.domain import BaseEntity


class RelationshipType(Enum):
    """Types of relationships between users and documents."""
    OWNER = "owner"           # User owns/created the document
    CONTRIBUTOR = "contributor"  # User contributed to the document
    REVIEWER = "reviewer"     # User reviews the document
    SUBSCRIBER = "subscriber" # User is subscribed to document updates
    VIEWER = "viewer"         # User can view the document


class AccessLevel(Enum):
    """Access levels for document relationships."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class DocumentRelationship(BaseEntity):
    """Domain entity representing a relationship between a user and a document.

    This entity tracks how users are related to documents in the system,
    including their access levels, interaction history, and relationship types.
    """

    id: str = field(default_factory=lambda: f"rel_{datetime.now(timezone.utc).timestamp()}")
    user_id: str = ""
    document_id: str = ""
    relationship_type: RelationshipType = RelationshipType.VIEWER
    access_level: AccessLevel = AccessLevel.READ

    # Relationship metadata
    tags: List[str] = field(default_factory=list)  # Document tags for expertise inference
    services: List[str] = field(default_factory=list)  # Services that process this document

    # Interaction tracking
    first_accessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0

    # Notification preferences for this document
    notify_on_updates: bool = True
    notify_on_comments: bool = False

    # System tracking
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate relationship after initialization."""
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        if not self.document_id:
            raise ValueError("Document ID cannot be empty")

    def record_access(self) -> None:
        """Record that the user accessed this document."""
        self.last_accessed_at = datetime.now(timezone.utc)
        self.access_count += 1
        self.updated_at = datetime.now(timezone.utc)

    def update_relationship(self, relationship_type: RelationshipType = None,
                          access_level: AccessLevel = None) -> None:
        """Update the relationship type and/or access level."""
        if relationship_type is not None:
            self.relationship_type = relationship_type
        if access_level is not None:
            self.access_level = access_level
        self.updated_at = datetime.now(timezone.utc)

    def add_tag(self, tag: str) -> None:
        """Add a tag to this relationship."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now(timezone.utc)

    def add_service(self, service_name: str) -> None:
        """Add a service that processes this document."""
        if service_name not in self.services:
            self.services.append(service_name)
            self.updated_at = datetime.now(timezone.utc)

    def can_write(self) -> bool:
        """Check if user has write access to the document."""
        return self.access_level in [AccessLevel.WRITE, AccessLevel.ADMIN]

    def can_admin(self) -> bool:
        """Check if user has admin access to the document."""
        return self.access_level == AccessLevel.ADMIN

    def should_notify(self, event_type: str) -> bool:
        """Check if user should be notified for a specific event type."""
        if event_type == "update":
            return self.notify_on_updates
        elif event_type == "comment":
            return self.notify_on_comments
        return False

    def update_notification_preferences(self, notify_updates: bool = None,
                                      notify_comments: bool = None) -> None:
        """Update notification preferences for this document."""
        if notify_updates is not None:
            self.notify_on_updates = notify_updates
        if notify_comments is not None:
            self.notify_on_comments = notify_comments
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert document relationship to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "relationship_type": self.relationship_type.value,
            "access_level": self.access_level.value,
            "tags": self.tags,
            "services": self.services,
            "notify_on_updates": self.notify_on_updates,
            "notify_on_comments": self.notify_on_comments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
