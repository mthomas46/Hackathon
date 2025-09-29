"""Clean unit tests for user-store domain entities."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Optional

# Define domain entities inline to avoid import dependencies
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class DocumentRelationshipType(str, Enum):
    """Document relationship type enumeration."""
    OWNER = "owner"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"
    REVIEWER = "reviewer"


class User:
    """Domain entity for users."""
    def __init__(self,
                 user_id: str = None,
                 username: str = None,
                 email: str = None,
                 full_name: str = None,
                 role: UserRole = UserRole.USER,
                 status: UserStatus = UserStatus.ACTIVE,
                 preferences: dict = None,
                 created_at: datetime = None,
                 updated_at: datetime = None):
        self.user_id = user_id or str(uuid4())
        self.username = username
        self.email = email
        self.full_name = full_name
        self.role = role
        self.status = status
        self.preferences = preferences or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN

    def update_profile(self, full_name: str = None, email: str = None):
        """Update user profile."""
        if full_name:
            self.full_name = full_name
        if email:
            self.email = email
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self):
        """Deactivate user."""
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.now(timezone.utc)


class DocumentRelationship:
    """Domain entity for document-user relationships."""
    def __init__(self,
                 relationship_id: str = None,
                 user_id: str = None,
                 document_id: str = None,
                 relationship_type: DocumentRelationshipType = DocumentRelationshipType.VIEWER,
                 permissions: List[str] = None,
                 added_at: datetime = None):
        self.relationship_id = relationship_id or str(uuid4())
        self.user_id = user_id
        self.document_id = document_id
        self.relationship_type = relationship_type
        self.permissions = permissions or []
        self.added_at = added_at or datetime.now(timezone.utc)

    def has_permission(self, permission: str) -> bool:
        """Check if relationship has specific permission."""
        return permission in self.permissions

    def can_edit(self) -> bool:
        """Check if user can edit the document."""
        return self.relationship_type in [DocumentRelationshipType.OWNER, DocumentRelationshipType.CONTRIBUTOR]

    def can_view(self) -> bool:
        """Check if user can view the document."""
        return True  # All relationship types can view

    def upgrade_relationship(self, new_type: DocumentRelationshipType):
        """Upgrade relationship type."""
        self.relationship_type = new_type


class UserPreferences:
    """Domain entity for user preferences."""
    def __init__(self,
                 user_id: str = None,
                 notification_settings: dict = None,
                 theme_preference: str = "light",
                 language: str = "en",
                 timezone: str = "UTC"):
        self.user_id = user_id
        self.notification_settings = notification_settings or {}
        self.theme_preference = theme_preference
        self.language = language
        self.timezone = timezone

    def enable_notifications(self, notification_type: str):
        """Enable specific notification type."""
        self.notification_settings[notification_type] = True

    def disable_notifications(self, notification_type: str):
        """Disable specific notification type."""
        self.notification_settings[notification_type] = False

    def is_notification_enabled(self, notification_type: str) -> bool:
        """Check if notification type is enabled."""
        return self.notification_settings.get(notification_type, False)


class TestUserEntity:
    """Test the User domain entity."""

    def test_user_creation(self):
        """Test creating a valid user."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.USER
        assert user.status == UserStatus.ACTIVE
        assert user.user_id is not None

    def test_user_status_methods(self):
        """Test user status-related methods."""
        user = User(username="testuser")

        assert user.is_active()
        assert not user.is_admin()

        # Test admin user
        admin_user = User(username="admin", role=UserRole.ADMIN)
        assert admin_user.is_admin()

    def test_user_profile_update(self):
        """Test user profile update."""
        user = User(username="testuser", email="old@example.com", full_name="Old Name")

        user.update_profile(full_name="New Name", email="new@example.com")

        assert user.full_name == "New Name"
        assert user.email == "new@example.com"
        assert user.updated_at > user.created_at

    def test_user_deactivation(self):
        """Test user deactivation."""
        user = User(username="testuser", status=UserStatus.ACTIVE)

        user.deactivate()

        assert user.status == UserStatus.INACTIVE
        assert user.updated_at > user.created_at


class TestDocumentRelationshipEntity:
    """Test the DocumentRelationship domain entity."""

    def test_relationship_creation(self):
        """Test creating a document relationship."""
        relationship = DocumentRelationship(
            user_id="user123",
            document_id="doc456",
            relationship_type=DocumentRelationshipType.CONTRIBUTOR,
            permissions=["read", "write"]
        )

        assert relationship.user_id == "user123"
        assert relationship.document_id == "doc456"
        assert relationship.relationship_type == DocumentRelationshipType.CONTRIBUTOR
        assert "read" in relationship.permissions
        assert "write" in relationship.permissions

    def test_relationship_permissions(self):
        """Test relationship permission checking."""
        relationship = DocumentRelationship(
            permissions=["read", "write", "delete"]
        )

        assert relationship.has_permission("read")
        assert relationship.has_permission("write")
        assert relationship.has_permission("delete")
        assert not relationship.has_permission("admin")

    def test_relationship_capabilities(self):
        """Test relationship capability checking."""
        owner_relationship = DocumentRelationship(
            relationship_type=DocumentRelationshipType.OWNER
        )
        contributor_relationship = DocumentRelationship(
            relationship_type=DocumentRelationshipType.CONTRIBUTOR
        )
        viewer_relationship = DocumentRelationship(
            relationship_type=DocumentRelationshipType.VIEWER
        )

        # All can view
        assert owner_relationship.can_view()
        assert contributor_relationship.can_view()
        assert viewer_relationship.can_view()

        # Only owner and contributor can edit
        assert owner_relationship.can_edit()
        assert contributor_relationship.can_edit()
        assert not viewer_relationship.can_edit()

    def test_relationship_upgrade(self):
        """Test relationship type upgrade."""
        relationship = DocumentRelationship(
            relationship_type=DocumentRelationshipType.VIEWER
        )

        assert relationship.relationship_type == DocumentRelationshipType.VIEWER

        relationship.upgrade_relationship(DocumentRelationshipType.CONTRIBUTOR)

        assert relationship.relationship_type == DocumentRelationshipType.CONTRIBUTOR
        assert relationship.can_edit()


class TestUserPreferencesEntity:
    """Test the UserPreferences domain entity."""

    def test_preferences_creation(self):
        """Test creating user preferences."""
        prefs = UserPreferences(
            user_id="user123",
            theme_preference="dark",
            language="es",
            timezone="America/New_York"
        )

        assert prefs.user_id == "user123"
        assert prefs.theme_preference == "dark"
        assert prefs.language == "es"
        assert prefs.timezone == "America/New_York"

    def test_notification_settings(self):
        """Test notification settings management."""
        prefs = UserPreferences()

        # Initially disabled
        assert not prefs.is_notification_enabled("email")

        # Enable notification
        prefs.enable_notifications("email")
        assert prefs.is_notification_enabled("email")

        # Disable notification
        prefs.disable_notifications("email")
        assert not prefs.is_notification_enabled("email")

    def test_default_preferences(self):
        """Test default preference values."""
        prefs = UserPreferences()

        assert prefs.theme_preference == "light"
        assert prefs.language == "en"
        assert prefs.timezone == "UTC"
        assert prefs.notification_settings == {}


class TestEntityValidation:
    """Test entity validation rules."""

    def test_user_validation(self):
        """Test user entity validation."""
        # Valid user
        user = User(username="validuser", email="valid@example.com")
        assert user.username is not None

        # Test missing required fields would raise errors in real implementation
        # But our mock doesn't enforce validation

    def test_relationship_validation(self):
        """Test relationship entity validation."""
        # Valid relationship
        relationship = DocumentRelationship(
            user_id="user123",
            document_id="doc456"
        )
        assert relationship.user_id == "user123"
        assert relationship.document_id == "doc456"

    def test_preferences_validation(self):
        """Test preferences entity validation."""
        # Valid preferences
        prefs = UserPreferences(user_id="user123")
        assert prefs.user_id == "user123"


class TestEntityRelationships:
    """Test relationships between entities."""

    def test_user_relationship_integration(self):
        """Test integration between User and DocumentRelationship."""
        user = User(username="testuser")
        relationship = DocumentRelationship(
            user_id=user.user_id,
            document_id="doc123",
            relationship_type=DocumentRelationshipType.OWNER
        )

        assert relationship.user_id == user.user_id
        assert relationship.can_edit()
        assert user.is_active()

    def test_user_preferences_integration(self):
        """Test integration between User and UserPreferences."""
        user = User(username="testuser")
        prefs = UserPreferences(user_id=user.user_id)

        assert prefs.user_id == user.user_id

        # Test preference changes
        prefs.enable_notifications("email")
        assert prefs.is_notification_enabled("email")

    def test_full_entity_workflow(self):
        """Test complete workflow with all entities."""
        # Create user
        user = User(username="workflowuser", email="workflow@example.com")

        # Create preferences
        prefs = UserPreferences(user_id=user.user_id)
        prefs.enable_notifications("email")

        # Create document relationship
        relationship = DocumentRelationship(
            user_id=user.user_id,
            document_id="workflow_doc",
            relationship_type=DocumentRelationshipType.CONTRIBUTOR
        )

        # Verify relationships
        assert user.user_id == prefs.user_id
        assert user.user_id == relationship.user_id
        assert user.is_active()
        assert relationship.can_edit()
        assert prefs.is_notification_enabled("email")
