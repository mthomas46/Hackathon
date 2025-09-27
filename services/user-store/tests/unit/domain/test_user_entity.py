"""Unit tests for User domain entity."""

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from domain.entities.user import User, UserRole, UserStatus


class TestUser:
    """Test cases for User entity."""

    def test_user_creation_valid(self):
        """Test creating a valid user."""
        user = User(
            id="user_123",
            username="johndoe",
            display_name="John Doe",
            email="john@example.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )

        assert user.id == "user_123"
        assert user.username == "johndoe"
        assert user.display_name == "John Doe"
        assert user.email == "john@example.com"
        assert user.role == UserRole.DEVELOPER
        assert user.status == UserStatus.ACTIVE

    def test_user_creation_invalid_email(self):
        """Test creating user with invalid email."""
        with pytest.raises(ValueError, match="Invalid email format"):
            User(
                id="user_123",
                username="johndoe",
                display_name="John Doe",
                email="invalid-email",
                role=UserRole.DEVELOPER,
                status=UserStatus.ACTIVE
            )

    def test_user_add_expertise_tag(self):
        """Test adding expertise tags."""
        user = User(
            id="user_123",
            username="johndoe",
            display_name="John Doe",
            email="john@example.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )

        user.add_expertise_tag("python")
        user.add_expertise_tag("testing")

        assert "python" in user.user_tags
        assert "testing" in user.user_tags

    def test_user_remove_expertise_tag(self):
        """Test removing expertise tags."""
        user = User(
            id="user_123",
            username="johndoe",
            display_name="John Doe",
            email="john@example.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )
        user.user_tags.extend(["python", "testing", "api"])

        user.remove_expertise_tag("testing")

        assert "python" in user.user_tags
        assert "api" in user.user_tags
        assert "testing" not in user.user_tags

    def test_user_has_expertise_in(self):
        """Test checking user expertise."""
        user = User(
            id="user_123",
            username="johndoe",
            display_name="John Doe",
            email="john@example.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE,
        )
        user.user_tags.extend(["python", "testing"])

        assert user.has_expertise_in("python") is True
        assert user.has_expertise_in("javascript") is False

    def test_user_update_contact_info(self):
        """Test updating contact information."""
        user = User(
            id="user_123",
            username="johndoe",
            display_name="John Doe",
            email="john@example.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )

        user.update_contact_info(
            contact_email="new@example.com",
            contact_slack="john_doe",
            contact_webhook="https://hooks.slack.com/..."
        )

        assert user.contact_email == "new@example.com"
        assert user.contact_slack == "john_doe"
        assert user.contact_webhook == "https://hooks.slack.com/..."

    def test_user_get_notification_contacts(self):
        """Test getting notification contacts."""
        user = User(
            id="user_123",
            username="johndoe",
            display_name="John Doe",
            email="john@example.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE,
            contact_email="notify@example.com",
            contact_slack="john_doe",
            contact_webhook="https://hooks.slack.com/...",
            notification_preferences={"email": True, "slack": False}
        )

        contacts = user.get_notification_contacts()

        expected_contacts = {
            "email": "notify@example.com",
            "slack": "john_doe",
            "webhook": "https://hooks.slack.com/..."
        }

        assert contacts == expected_contacts

    def test_user_infer_expertise_from_documents(self):
        """Test inferring expertise from document tags."""
        user = User(
            id="user_123",
            username="johndoe",
            display_name="John Doe",
            email="john@example.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )

        # Simulate documents with tags (flattened)
        document_tags = ["python", "api", "testing", "javascript", "api", "python", "database"]

        user.infer_expertise_from_documents(document_tags)

        # Python and api appear multiple times, so should be added as expertise
        assert "python" in user.user_tags
        assert "api" in user.user_tags
        # Testing appears only once, so should not be added
        assert "testing" not in user.user_tags

    def test_user_to_dict(self):
        """Test converting user to dictionary."""
        user = User(
            id="user_123",
            username="johndoe",
            display_name="John Doe",
            email="john@example.com",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE,
        )
        user.user_tags.extend(["python", "testing"])

        user_dict = user.to_dict()

        assert user_dict["id"] == "user_123"
        assert user_dict["username"] == "johndoe"
        assert user_dict["display_name"] == "John Doe"
        assert user_dict["email"] == "john@example.com"
        assert user_dict["role"] == "developer"
        assert user_dict["status"] == "active"
        assert user_dict["user_tags"] == ["python", "testing"]
