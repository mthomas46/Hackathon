"""User domain service for the User Store service.

This module provides business logic for user management, including
user creation, updates, relationship management, and query operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from ..entities.user import User, UserPreferences, UserRole, UserStatus
from ..entities.document_relationship import DocumentRelationship
from ..repositories.user_repository import UserRepository, UserPreferencesRepository
from ..repositories.document_relationship_repository import DocumentRelationshipRepository
from .document_user_extraction_service import DocumentUserExtractionService, UserRelationship


class UserService:
    """Domain service for user-related business logic."""

    def __init__(
        self,
        user_repository: UserRepository,
        preferences_repository: UserPreferencesRepository,
        relationship_repository: DocumentRelationshipRepository
    ):
        """Initialize the user service with required repositories."""
        self._user_repository = user_repository
        self._preferences_repository = preferences_repository
        self._relationship_repository = relationship_repository
        self._extraction_service = DocumentUserExtractionService()

    async def create_user(
        self,
        email: str,
        username: str,
        display_name: str = "",
        role: UserRole = UserRole.VIEWER
    ) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = await self._user_repository.find_by_email(email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        existing_username = await self._user_repository.find_by_username(username)
        if existing_username:
            raise ValueError(f"Username {username} is already taken")

        # Create new user
        user = User(
            email=email,
            username=username,
            display_name=display_name or username,
            role=role
        )

        await self._user_repository.save(user)

        # Create default preferences
        preferences = UserPreferences(user_id=user.id)
        await self._preferences_repository.save(preferences)

        return user

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return await self._user_repository.find_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return await self._user_repository.find_by_email(email)

    async def update_user(self, user_id: str, **updates) -> Optional[User]:
        """Update user information."""
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            return None

        user.update_profile(**updates)
        await self._user_repository.update(user)
        return user

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        # Remove all relationships
        relationships = await self._relationship_repository.find_relationships_by_user(user_id)
        for relationship in relationships:
            await self._relationship_repository.delete(relationship.id)

        # Remove preferences
        await self._preferences_repository.delete(user_id)

        # Delete user
        return await self._user_repository.delete(user_id)

    async def list_users(
        self,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[User]:
        """List users with optional filtering."""
        if role:
            return await self._user_repository.find_by_role(role)
        elif status:
            return await self._user_repository.find_by_status(status)
        else:
            return await self._user_repository.list_all_users(limit, offset)

    async def search_users(self, query: str, limit: int = 50) -> List[User]:
        """Search users by name, email, or username."""
        return await self._user_repository.search_users(query, limit)

    async def get_users_by_document(self, document_id: str) -> List[User]:
        """Get all users related to a document."""
        return await self._user_repository.find_users_by_document(document_id)

    async def get_users_by_topic(self, topic: str) -> List[User]:
        """Get all users interested in a topic."""
        return await self._user_repository.find_users_by_topic(topic)

    async def get_users_by_service(self, service_name: str) -> List[User]:
        """Get all users subscribed to a service."""
        return await self._user_repository.find_users_by_service(service_name)

    async def get_users_by_service_and_topic(self, service_name: str, topic: str) -> List[User]:
        """Get users subscribed to a service and interested in a topic."""
        user_ids = await self._relationship_repository.find_users_by_service_and_topic(service_name, topic)

        users = []
        for user_id in user_ids:
            user = await self._user_repository.find_by_id(user_id)
            if user:
                users.append(user)

        return users

    async def add_user_document_relationship(
        self,
        user_id: str,
        document_id: str,
        relationship_type: str = "viewer",
        access_level: str = "read"
    ) -> DocumentRelationship:
        """Add a relationship between a user and a document."""
        # Check if relationship already exists
        existing = await self._relationship_repository.find_by_user_and_document(user_id, document_id)
        if existing:
            raise ValueError(f"Relationship between user {user_id} and document {document_id} already exists")

        # Create new relationship
        relationship = DocumentRelationship(
            user_id=user_id,
            document_id=document_id,
            relationship_type=getattr(DocumentRelationship.RelationshipType, relationship_type.upper()),
            access_level=getattr(DocumentRelationship.AccessLevel, access_level.upper())
        )

        await self._relationship_repository.save(relationship)

        # Update user's document relationships
        user = await self._user_repository.find_by_id(user_id)
        if user:
            user.add_document_relationship(document_id)
            await self._user_repository.update(user)

        return relationship

    async def update_user_preferences(self, user_id: str, **preferences) -> Optional[UserPreferences]:
        """Update user notification preferences."""
        existing_prefs = await self._preferences_repository.find_by_user_id(user_id)
        if not existing_prefs:
            existing_prefs = UserPreferences(user_id=user_id)

        # Update preferences
        for key, value in preferences.items():
            if hasattr(existing_prefs, key):
                setattr(existing_prefs, key, value)

        await self._preferences_repository.update(existing_prefs)
        return existing_prefs

    async def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences."""
        return await self._preferences_repository.find_by_user_id(user_id)

    async def record_user_login(self, user_id: str) -> Optional[User]:
        """Record a user login event."""
        user = await self._user_repository.find_by_id(user_id)
        if user:
            user.record_login()
            await self._user_repository.update(user)
            return user
        return None

    async def get_user_stats(self) -> dict:
        """Get user statistics."""
        total_users = await self._user_repository.count()
        active_users = len(await self._user_repository.find_by_status(UserStatus.ACTIVE))
        admin_users = len(await self._user_repository.find_by_role(UserRole.ADMIN))

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "admin_users": admin_users,
            "analyst_users": len(await self._user_repository.find_by_role(UserRole.ANALYST)),
            "developer_users": len(await self._user_repository.find_by_role(UserRole.DEVELOPER)),
            "manager_users": len(await self._user_repository.find_by_role(UserRole.MANAGER)),
            "viewer_users": len(await self._user_repository.find_by_role(UserRole.VIEWER)),
        }

    async def create_relationships_from_document(
        self,
        document_id: str,
        document_content: str,
        document_metadata: Dict[str, Any],
        source_type: str,
        document_tags: Optional[List[str]] = None
    ) -> List[DocumentRelationship]:
        """Automatically create user-document relationships by analyzing document content.

        This method extracts user identifiers from document metadata and content,
        then creates relationships between identified users and the document.
        Supports GitHub PRs, Jira issues, and Confluence pages.

        Args:
            document_id: Unique identifier of the document
            document_content: Full text content of the document
            document_metadata: Document metadata dictionary
            source_type: Source system (github, jira, confluence)

        Returns:
            List of DocumentRelationship objects created
        """
        # Extract user relationships from the document
        user_relationships = self._extraction_service.extract_user_relationships(
            document_content, document_metadata, source_type
        )

        # Use provided document tags or extract from metadata
        if document_tags is None:
            document_tags = self._extract_tags_from_metadata(document_metadata)

        created_relationships = []

        for user_rel in user_relationships:
            # Try to find existing user by email, username, or create placeholder
            user = await self._find_or_create_user_from_identifier(user_rel.user_identifier)

            if user:
                try:
                    # Create the relationship
                    relationship = await self.add_user_document_relationship(
                        user_id=user.id,
                        document_id=document_id,
                        relationship_type=user_rel.relationship_type.value.lower(),
                        access_level="read"  # Default access level
                    )

                    # Add document tags to relationship for expertise inference
                    if document_tags:
                        relationship.tags.extend(document_tags)

                    await self._relationship_repository.update(relationship)
                    created_relationships.append(relationship)

                    # Update user's expertise based on document tags
                    await self._update_user_expertise(user.id, document_tags)

                except ValueError:
                    # Relationship already exists, skip
                    continue

        return created_relationships

    async def _find_or_create_user_from_identifier(self, identifier: str) -> Optional[User]:
        """Find existing user or create placeholder user from identifier.

        Args:
            identifier: User identifier (email, username, or display name)

        Returns:
            User object if found or created, None if invalid identifier
        """
        # Clean the identifier
        identifier = identifier.strip()
        if not identifier:
            return None

        # Try to find by email first
        if '@' in identifier and '.' in identifier:
            user = await self._user_repository.find_by_email(identifier)
            if user:
                return user

        # Try to find by username
        user = await self._user_repository.find_by_username(identifier)
        if user:
            return user

        # Try to find by display name (partial match)
        users = await self._user_repository.search_users(identifier, limit=1)
        if users:
            return users[0]

        # If not found and looks like an email, create placeholder user
        if '@' in identifier and '.' in identifier:
            try:
                # Generate username from email
                username = identifier.split('@')[0].lower()
                # Make sure username is unique
                counter = 1
                base_username = username
                while await self._user_repository.find_by_username(username):
                    username = f"{base_username}_{counter}"
                    counter += 1

                # Create placeholder user
                user = await self.create_user(
                    email=identifier,
                    username=username,
                    display_name=username.title(),
                    role=UserRole.VIEWER
                )
                return user
            except Exception:
                # If creation fails, return None
                return None

        # If not found and doesn't look like email, create placeholder with generated email
        try:
            username = identifier.lower().replace(' ', '_').replace('-', '_')
            # Make sure username is unique
            counter = 1
            base_username = username
            while await self._user_repository.find_by_username(username):
                username = f"{base_username}_{counter}"
                counter += 1

            # Generate placeholder email
            email = f"{username}@placeholder.local"

            user = await self.create_user(
                email=email,
                username=username,
                display_name=identifier,
                role=UserRole.VIEWER
            )
            return user
        except Exception:
            return None

    async def get_document_user_relationships(self, document_id: str) -> Dict[str, List[User]]:
        """Get all user relationships for a document, grouped by relationship type.

        Args:
            document_id: Document identifier

        Returns:
            Dictionary mapping relationship types to lists of users
        """
        relationships = await self._relationship_repository.find_relationships_by_document(document_id)

        result = {}
        for rel in relationships:
            rel_type = rel.relationship_type.value
            if rel_type not in result:
                result[rel_type] = []

            user = await self._user_repository.find_by_id(rel.user_id)
            if user:
                result[rel_type].append(user)

        return result

    async def get_user_document_relationships(self, user_id: str) -> Dict[str, List[str]]:
        """Get all document relationships for a user, grouped by relationship type.

        Args:
            user_id: User identifier

        Returns:
            Dictionary mapping relationship types to lists of document IDs
        """
        relationships = await self._relationship_repository.find_relationships_by_user(user_id)

        result = {}
        for rel in relationships:
            rel_type = rel.relationship_type.value
            if rel_type not in result:
                result[rel_type] = []

            result[rel_type].append(rel.document_id)

        return result

    def _extract_tags_from_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract tags from document metadata."""
        tags = []

        # Look for common tag fields in metadata
        tag_fields = ['tags', 'labels', 'topics', 'categories', 'keywords']

        for field in tag_fields:
            if field in metadata:
                field_value = metadata[field]
                if isinstance(field_value, list):
                    tags.extend(field_value)
                elif isinstance(field_value, str):
                    # Split comma-separated tags
                    tags.extend([tag.strip() for tag in field_value.split(',')])

        # Extract from GitHub labels
        if 'labels' in metadata and metadata['labels']:
            for label in metadata['labels']:
                if isinstance(label, dict) and 'name' in label:
                    tags.append(label['name'])
                elif isinstance(label, str):
                    tags.append(label)

        # Extract from Jira labels
        if 'fields' in metadata and 'labels' in metadata['fields']:
            tags.extend(metadata['fields']['labels'])

        return list(set(tags))  # Remove duplicates

    async def _update_user_expertise(self, user_id: str, document_tags: List[str]) -> None:
        """Update user expertise based on document tags."""
        if not document_tags:
            return

        user = await self._user_repository.find_by_id(user_id)
        if not user:
            return

        # Get all document tags user has worked with
        relationships = await self._relationship_repository.find_relationships_by_user(user_id)
        all_tags = []
        for rel in relationships:
            all_tags.extend(rel.tags)

        # Infer expertise - tags that appear in multiple documents
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Add expertise tags (tags that appear in 2+ documents)
        for tag, count in tag_counts.items():
            if count >= 2 and tag not in user.user_tags:
                user.add_expertise_tag(tag)

        await self._user_repository.update(user)

    async def find_users_by_expertise(self, topic: str, min_relationships: int = 1) -> List[User]:
        """Find users with expertise in a specific topic.

        Args:
            topic: Topic/expertise area to search for
            min_relationships: Minimum number of document relationships required

        Returns:
            List of users with expertise in the topic
        """
        users = await self._user_repository.find_users_by_expertise(topic)

        # Filter by minimum relationships if specified
        if min_relationships > 1:
            filtered_users = []
            for user in users:
                relationship_count = await self._relationship_repository.count_relationships_by_user(user.id)
                if relationship_count >= min_relationships:
                    filtered_users.append(user)
            return filtered_users

        return users

    async def get_user_expertise_profile(self, user_id: str) -> Dict[str, Any]:
        """Get a comprehensive expertise profile for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with expertise analysis
        """
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            return {}

        relationships = await self._relationship_repository.find_relationships_by_user(user_id)

        # Analyze expertise by tag frequency
        tag_counts = {}
        document_types = {}
        services_worked_with = set()

        for rel in relationships:
            # Count tags
            for tag in rel.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Track document types and services
            doc_type = rel.document_id.split(':')[0] if ':' in rel.document_id else 'unknown'
            document_types[doc_type] = document_types.get(doc_type, 0) + 1
            services_worked_with.update(rel.services)

        # Calculate expertise scores (tags with high frequency)
        expertise_scores = {}
        for tag, count in tag_counts.items():
            # Score based on frequency and relationship diversity
            expertise_scores[tag] = min(count * 10, 100)  # Cap at 100

        return {
            'user_id': user_id,
            'expertise_tags': user.user_tags,
            'tag_frequencies': tag_counts,
            'expertise_scores': expertise_scores,
            'document_types': document_types,
            'services_experience': list(services_worked_with),
            'total_relationships': len(relationships),
            'top_expertise': sorted(expertise_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    async def add_user_document_relationship(
        self,
        user_id: str,
        document_id: str,
        relationship_type: str,
        access_level: str = "read"
    ) -> DocumentRelationship:
        """Add a document relationship for a user."""
        # Check if user exists
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check if relationship already exists
        existing = await self._relationship_repository.find_by_user_and_document(user_id, document_id)
        if existing:
            raise ValueError(f"Relationship already exists between user {user_id} and document {document_id}")

        # Create new relationship
        from ..entities.document_relationship import DocumentRelationship, RelationshipType, AccessLevel

        relationship = DocumentRelationship(
            user_id=user_id,
            document_id=document_id,
            relationship_type=getattr(RelationshipType, relationship_type.upper()),
            access_level=getattr(AccessLevel, access_level.upper())
        )

        await self._relationship_repository.save(relationship)
        return relationship

    async def remove_user_document_relationship(self, user_id: str, document_id: str) -> bool:
        """Remove a document relationship from a user."""
        return await self._relationship_repository.delete_by_user_and_document(user_id, document_id)

    async def update_user_document_relationship(
        self, user_id: str, document_id: str, **updates
    ) -> bool:
        """Update a user's document relationship properties."""
        relationship = await self._relationship_repository.find_by_user_and_document(user_id, document_id)
        if not relationship:
            return False

        # Update relationship properties
        if 'relationship_type' in updates:
            from ..entities.document_relationship import RelationshipType
            relationship.relationship_type = getattr(RelationshipType, updates['relationship_type'].upper())

        if 'access_level' in updates:
            from ..entities.document_relationship import AccessLevel
            relationship.access_level = getattr(AccessLevel, updates['access_level'].upper())

        await self._relationship_repository.update(relationship)
        return True

    async def add_user_topic_interest(self, user_id: str, topic: str) -> User:
        """Add a topic interest to a user."""
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        if topic in user.topic_interests:
            raise ValueError(f"Topic '{topic}' already in user interests")

        user.topic_interests.append(topic)
        user.updated_at = datetime.now(timezone.utc)
        await self._user_repository.update(user)
        return user

    async def remove_user_topic_interest(self, user_id: str, topic: str) -> bool:
        """Remove a topic interest from a user."""
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            return False

        if topic not in user.topic_interests:
            return False

        user.topic_interests.remove(topic)
        user.updated_at = datetime.now(timezone.utc)
        await self._user_repository.update(user)
        return True

    async def add_user_service_subscription(self, user_id: str, service_name: str) -> User:
        """Add a service subscription for a user."""
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        if service_name in user.service_subscriptions:
            raise ValueError(f"Already subscribed to service '{service_name}'")

        user.service_subscriptions.append(service_name)
        user.updated_at = datetime.now(timezone.utc)
        await self._user_repository.update(user)
        return user

    async def remove_user_service_subscription(self, user_id: str, service_name: str) -> bool:
        """Remove a service subscription from a user."""
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            return False

        if service_name not in user.service_subscriptions:
            return False

        user.service_subscriptions.remove(service_name)
        user.updated_at = datetime.now(timezone.utc)
        await self._user_repository.update(user)
        return True

    async def list_users(
        self,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[User]:
        """List users with optional filtering."""
        if role:
            return await self._user_repository.find_by_role(role)
        elif status:
            return await self._user_repository.find_by_status(status)
        else:
            return await self._user_repository.list_all_users(limit=limit, offset=offset)
