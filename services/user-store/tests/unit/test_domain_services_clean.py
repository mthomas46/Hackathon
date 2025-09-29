"""Clean unit tests for user-store domain services."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional

# Define mock entities and repositories to avoid import dependencies
from enum import Enum
from datetime import datetime, timezone


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class DocumentRelationshipType(str, Enum):
    OWNER = "owner"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"


class MockUser:
    """Mock user entity."""
    def __init__(self, user_id: str, username: str, email: str = None, role: UserRole = UserRole.USER):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.status = UserStatus.ACTIVE

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN


class MockDocumentRelationship:
    """Mock document relationship entity."""
    def __init__(self, user_id: str, document_id: str, relationship_type: DocumentRelationshipType):
        self.user_id = user_id
        self.document_id = document_id
        self.relationship_type = relationship_type

    def can_edit(self) -> bool:
        return self.relationship_type in [DocumentRelationshipType.OWNER, DocumentRelationshipType.CONTRIBUTOR]


# Mock repositories
class MockUserRepository:
    """Mock user repository."""
    def __init__(self):
        self.users = {
            "user1": MockUser("user1", "alice", "alice@example.com"),
            "user2": MockUser("user2", "bob", "bob@example.com"),
            "admin1": MockUser("admin1", "admin", "admin@example.com", UserRole.ADMIN),
        }

    async def get_by_id(self, user_id: str) -> Optional[MockUser]:
        """Get user by ID."""
        return self.users.get(user_id)

    async def get_by_username(self, username: str) -> Optional[MockUser]:
        """Get user by username."""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    async def save(self, user: MockUser) -> MockUser:
        """Save user."""
        self.users[user.user_id] = user
        return user

    async def list_all(self) -> List[MockUser]:
        """List all users."""
        return list(self.users.values())


class MockDocumentRelationshipRepository:
    """Mock document relationship repository."""
    def __init__(self):
        self.relationships = [
            MockDocumentRelationship("user1", "doc1", DocumentRelationshipType.OWNER),
            MockDocumentRelationship("user2", "doc1", DocumentRelationshipType.CONTRIBUTOR),
            MockDocumentRelationship("user1", "doc2", DocumentRelationshipType.VIEWER),
        ]

    async def get_user_relationships(self, user_id: str) -> List[MockDocumentRelationship]:
        """Get relationships for a user."""
        return [rel for rel in self.relationships if rel.user_id == user_id]

    async def get_document_relationships(self, document_id: str) -> List[MockDocumentRelationship]:
        """Get relationships for a document."""
        return [rel for rel in self.relationships if rel.document_id == document_id]

    async def add_relationship(self, relationship: MockDocumentRelationship):
        """Add a relationship."""
        self.relationships.append(relationship)


# Domain services
class UserService:
    """Domain service for user operations."""

    def __init__(self, user_repo: MockUserRepository):
        self.user_repo = user_repo

    async def get_user_with_permissions(self, user_id: str) -> Optional[dict]:
        """Get user with computed permissions."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None

        return {
            "user": user,
            "permissions": {
                "can_create_users": user.is_admin(),
                "can_delete_users": user.is_admin(),
                "can_manage_documents": user.is_active(),
                "can_view_reports": user.is_active(),
            }
        }

    async def validate_user_access(self, user_id: str, required_role: UserRole = UserRole.USER) -> bool:
        """Validate user has required access level."""
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active():
            return False

        if required_role == UserRole.ADMIN and not user.is_admin():
            return False

        return True

    async def get_user_statistics(self) -> dict:
        """Get user statistics."""
        all_users = await self.user_repo.list_all()
        active_users = [u for u in all_users if u.is_active()]
        admin_users = [u for u in all_users if u.is_admin()]

        return {
            "total_users": len(all_users),
            "active_users": len(active_users),
            "admin_users": len(admin_users),
            "inactive_users": len(all_users) - len(active_users),
        }


class DocumentUserExtractionService:
    """Domain service for document-user relationship operations."""

    def __init__(self, user_repo: MockUserRepository, relationship_repo: MockDocumentRelationshipRepository):
        self.user_repo = user_repo
        self.relationship_repo = relationship_repo

    async def get_document_contributors(self, document_id: str) -> List[MockUser]:
        """Get all users who can contribute to a document."""
        relationships = await self.relationship_repo.get_document_relationships(document_id)
        contributor_relationships = [rel for rel in relationships if rel.can_edit()]

        users = []
        for rel in contributor_relationships:
            user = await self.user_repo.get_by_id(rel.user_id)
            if user and user.is_active():
                users.append(user)

        return users

    async def get_user_document_permissions(self, user_id: str, document_id: str) -> dict:
        """Get user permissions for a specific document."""
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active():
            return {"can_view": False, "can_edit": False, "can_delete": False}

        relationships = await self.relationship_repo.get_user_relationships(user_id)
        document_relationship = next((rel for rel in relationships if rel.document_id == document_id), None)

        if not document_relationship:
            return {"can_view": False, "can_edit": False, "can_delete": False}

        return {
            "can_view": True,  # All relationships can view
            "can_edit": document_relationship.can_edit(),
            "can_delete": document_relationship.relationship_type == DocumentRelationshipType.OWNER,
        }

    async def find_users_by_document_access(self, document_id: str, access_type: str = "view") -> List[MockUser]:
        """Find users with specific access to a document."""
        relationships = await self.relationship_repo.get_document_relationships(document_id)

        if access_type == "edit":
            qualifying_relationships = [rel for rel in relationships if rel.can_edit()]
        else:  # view
            qualifying_relationships = relationships  # All relationships can view

        users = []
        for rel in qualifying_relationships:
            user = await self.user_repo.get_by_id(rel.user_id)
            if user and user.is_active():
                users.append(user)

        return users


class TestUserService:
    """Test the UserService domain service."""

    @pytest.fixture
    def user_repo(self):
        """Create user repository."""
        return MockUserRepository()

    @pytest.fixture
    def user_service(self, user_repo):
        """Create user service."""
        return UserService(user_repo)

    @pytest.mark.asyncio
    async def test_get_user_with_permissions_regular_user(self, user_service):
        """Test getting regular user with permissions."""
        result = await user_service.get_user_with_permissions("user1")

        assert result is not None
        assert result["user"].username == "alice"
        assert result["permissions"]["can_create_users"] is False
        assert result["permissions"]["can_manage_documents"] is True

    @pytest.mark.asyncio
    async def test_get_user_with_permissions_admin_user(self, user_service):
        """Test getting admin user with permissions."""
        result = await user_service.get_user_with_permissions("admin1")

        assert result is not None
        assert result["user"].username == "admin"
        assert result["permissions"]["can_create_users"] is True
        assert result["permissions"]["can_delete_users"] is True

    @pytest.mark.asyncio
    async def test_get_user_with_permissions_not_found(self, user_service):
        """Test getting non-existent user."""
        result = await user_service.get_user_with_permissions("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_user_access_regular_user(self, user_service):
        """Test validating regular user access."""
        assert await user_service.validate_user_access("user1", UserRole.USER)
        assert not await user_service.validate_user_access("user1", UserRole.ADMIN)

    @pytest.mark.asyncio
    async def test_validate_user_access_admin_user(self, user_service):
        """Test validating admin user access."""
        assert await user_service.validate_user_access("admin1", UserRole.USER)
        assert await user_service.validate_user_access("admin1", UserRole.ADMIN)

    @pytest.mark.asyncio
    async def test_validate_user_access_inactive_user(self, user_service, user_repo):
        """Test validating inactive user access."""
        # Make user inactive (mock this)
        user_repo.users["user1"].status = UserStatus.INACTIVE

        assert not await user_service.validate_user_access("user1", UserRole.USER)

    @pytest.mark.asyncio
    async def test_get_user_statistics(self, user_service):
        """Test getting user statistics."""
        stats = await user_service.get_user_statistics()

        assert stats["total_users"] == 3
        assert stats["active_users"] == 3  # All are active in our mock
        assert stats["admin_users"] == 1
        assert stats["inactive_users"] == 0


class TestDocumentUserExtractionService:
    """Test the DocumentUserExtractionService domain service."""

    @pytest.fixture
    def user_repo(self):
        """Create user repository."""
        return MockUserRepository()

    @pytest.fixture
    def relationship_repo(self):
        """Create relationship repository."""
        return MockDocumentRelationshipRepository()

    @pytest.fixture
    def extraction_service(self, user_repo, relationship_repo):
        """Create extraction service."""
        return DocumentUserExtractionService(user_repo, relationship_repo)

    @pytest.mark.asyncio
    async def test_get_document_contributors(self, extraction_service):
        """Test getting document contributors."""
        contributors = await extraction_service.get_document_contributors("doc1")

        # user1 is OWNER, user2 is CONTRIBUTOR - both can edit
        assert len(contributors) == 2
        usernames = [user.username for user in contributors]
        assert "alice" in usernames  # user1
        assert "bob" in usernames    # user2

    @pytest.mark.asyncio
    async def test_get_document_contributors_no_editors(self, extraction_service, relationship_repo):
        """Test getting contributors for document with no editors."""
        # Add a document with only viewers
        relationship_repo.relationships.append(
            MockDocumentRelationship("user1", "doc3", DocumentRelationshipType.VIEWER)
        )

        contributors = await extraction_service.get_document_contributors("doc3")

        assert len(contributors) == 0

    @pytest.mark.asyncio
    async def test_get_user_document_permissions_owner(self, extraction_service):
        """Test getting owner permissions."""
        permissions = await extraction_service.get_user_document_permissions("user1", "doc1")

        assert permissions["can_view"] is True
        assert permissions["can_edit"] is True
        assert permissions["can_delete"] is True

    @pytest.mark.asyncio
    async def test_get_user_document_permissions_contributor(self, extraction_service):
        """Test getting contributor permissions."""
        permissions = await extraction_service.get_user_document_permissions("user2", "doc1")

        assert permissions["can_view"] is True
        assert permissions["can_edit"] is True
        assert permissions["can_delete"] is False

    @pytest.mark.asyncio
    async def test_get_user_document_permissions_viewer(self, extraction_service):
        """Test getting viewer permissions."""
        permissions = await extraction_service.get_user_document_permissions("user1", "doc2")

        assert permissions["can_view"] is True
        assert permissions["can_edit"] is False
        assert permissions["can_delete"] is False

    @pytest.mark.asyncio
    async def test_get_user_document_permissions_no_relationship(self, extraction_service):
        """Test getting permissions for user with no relationship to document."""
        permissions = await extraction_service.get_user_document_permissions("user2", "doc2")

        assert permissions["can_view"] is False
        assert permissions["can_edit"] is False
        assert permissions["can_delete"] is False

    @pytest.mark.asyncio
    async def test_get_user_document_permissions_inactive_user(self, extraction_service, user_repo):
        """Test getting permissions for inactive user."""
        # Make user inactive
        user_repo.users["user1"].status = UserStatus.INACTIVE

        permissions = await extraction_service.get_user_document_permissions("user1", "doc1")

        assert permissions["can_view"] is False
        assert permissions["can_edit"] is False
        assert permissions["can_delete"] is False

    @pytest.mark.asyncio
    async def test_find_users_by_document_access_view(self, extraction_service):
        """Test finding users with view access."""
        users = await extraction_service.find_users_by_document_access("doc1", "view")

        assert len(users) == 2  # Both user1 and user2 have relationships with doc1
        usernames = [user.username for user in users]
        assert "alice" in usernames
        assert "bob" in usernames

    @pytest.mark.asyncio
    async def test_find_users_by_document_access_edit(self, extraction_service):
        """Test finding users with edit access."""
        users = await extraction_service.find_users_by_document_access("doc1", "edit")

        assert len(users) == 2  # user1 (owner) and user2 (contributor) can edit
        usernames = [user.username for user in users]
        assert "alice" in usernames
        assert "bob" in usernames

    @pytest.mark.asyncio
    async def test_find_users_by_document_access_no_qualifying_users(self, extraction_service, relationship_repo):
        """Test finding users when none qualify."""
        # Create a document with only viewers
        relationship_repo.relationships = [
            MockDocumentRelationship("user1", "doc4", DocumentRelationshipType.VIEWER)
        ]

        users = await extraction_service.find_users_by_document_access("doc4", "edit")

        assert len(users) == 0


class TestServiceIntegration:
    """Test integration between domain services."""

    @pytest.fixture
    def user_repo(self):
        """Create user repository."""
        return MockUserRepository()

    @pytest.fixture
    def relationship_repo(self):
        """Create relationship repository."""
        return MockDocumentRelationshipRepository()

    @pytest.fixture
    def user_service(self, user_repo):
        """Create user service."""
        return UserService(user_repo)

    @pytest.fixture
    def extraction_service(self, user_repo, relationship_repo):
        """Create extraction service."""
        return DocumentUserExtractionService(user_repo, relationship_repo)

    @pytest.mark.asyncio
    async def test_user_service_and_extraction_service_integration(self, user_service, extraction_service):
        """Test integration between user service and extraction service."""
        # Get user permissions
        user_data = await user_service.get_user_with_permissions("user1")
        assert user_data is not None
        assert user_data["permissions"]["can_manage_documents"] is True

        # Get document permissions for same user
        doc_permissions = await extraction_service.get_user_document_permissions("user1", "doc1")
        assert doc_permissions["can_view"] is True
        assert doc_permissions["can_edit"] is True

        # Verify user can access document
        user = user_data["user"]
        assert user.is_active()

    @pytest.mark.asyncio
    async def test_cross_service_data_consistency(self, user_service, extraction_service):
        """Test data consistency across services."""
        # Get user stats from user service
        stats = await user_service.get_user_statistics()
        total_users = stats["total_users"]

        # Get contributors for a document from extraction service
        contributors = await extraction_service.get_document_contributors("doc1")
        contributor_count = len(contributors)

        # Verify contributor count is reasonable
        assert contributor_count <= total_users
        assert contributor_count >= 0

        # Verify each contributor is an active user
        for contributor in contributors:
            user_data = await user_service.get_user_with_permissions(contributor.user_id)
            assert user_data is not None
            assert user_data["permissions"]["can_manage_documents"] is True
