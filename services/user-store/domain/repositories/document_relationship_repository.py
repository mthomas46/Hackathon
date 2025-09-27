"""Document relationship repository interface for the User Store service.

This module defines the abstract interface for document relationship data
persistence and retrieval operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.document_relationship import DocumentRelationship, RelationshipType, AccessLevel


class DocumentRelationshipRepository(ABC):
    """Abstract base class for document relationship repository implementations."""

    @abstractmethod
    async def save(self, relationship: DocumentRelationship) -> None:
        """Save a document relationship to the repository."""
        pass

    @abstractmethod
    async def find_by_id(self, relationship_id: str) -> Optional[DocumentRelationship]:
        """Find a relationship by its ID."""
        pass

    @abstractmethod
    async def find_by_user_and_document(self, user_id: str, document_id: str) -> Optional[DocumentRelationship]:
        """Find relationship between a specific user and document."""
        pass

    @abstractmethod
    async def find_relationships_by_user(self, user_id: str) -> List[DocumentRelationship]:
        """Find all relationships for a specific user."""
        pass

    @abstractmethod
    async def find_relationships_by_document(self, document_id: str) -> List[DocumentRelationship]:
        """Find all relationships for a specific document."""
        pass

    @abstractmethod
    async def find_by_relationship_type(self, relationship_type: RelationshipType) -> List[DocumentRelationship]:
        """Find all relationships of a specific type."""
        pass

    @abstractmethod
    async def find_by_access_level(self, access_level: AccessLevel) -> List[DocumentRelationship]:
        """Find all relationships with a specific access level."""
        pass

    @abstractmethod
    async def find_users_by_document_and_topic(self, document_id: str, topic: str) -> List[str]:
        """Find user IDs related to a document with a specific topic."""
        pass

    @abstractmethod
    async def find_users_by_service_and_topic(self, service_name: str, topic: str) -> List[str]:
        """Find user IDs subscribed to a service with interest in a topic."""
        pass

    @abstractmethod
    async def find_documents_by_user_and_service(self, user_id: str, service_name: str) -> List[str]:
        """Find document IDs related to a user through a specific service."""
        pass

    @abstractmethod
    async def update(self, relationship: DocumentRelationship) -> None:
        """Update an existing relationship."""
        pass

    @abstractmethod
    async def delete(self, relationship_id: str) -> bool:
        """Delete a relationship by ID."""
        pass

    @abstractmethod
    async def delete_by_user_and_document(self, user_id: str, document_id: str) -> bool:
        """Delete relationship between a specific user and document."""
        pass

    @abstractmethod
    async def exists(self, user_id: str, document_id: str) -> bool:
        """Check if a relationship exists between user and document."""
        pass

    @abstractmethod
    async def count_relationships_by_user(self, user_id: str) -> int:
        """Count total relationships for a user."""
        pass

    @abstractmethod
    async def count_relationships_by_document(self, document_id: str) -> int:
        """Count total relationships for a document."""
        pass
