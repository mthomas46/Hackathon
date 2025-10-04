"""In-memory implementation of Document Relationship Repository.

This module provides an in-memory repository implementation for document
relationship data, supporting user-document relationship management.
"""

from typing import Dict, List, Optional

from domain.entities.document_relationship import (
    DocumentRelationship,
    RelationshipType,
    AccessLevel
)
from domain.repositories.document_relationship_repository import DocumentRelationshipRepository


class InMemoryDocumentRelationshipRepository(DocumentRelationshipRepository):
    """In-memory implementation of DocumentRelationshipRepository."""

    def __init__(self):
        """Initialize the repository with empty storage."""
        self._relationships: Dict[str, DocumentRelationship] = {}
        self._user_document_index: Dict[str, str] = {}  # (user_id, document_id) -> relationship_id
        self._user_relationships: Dict[str, List[str]] = {}  # user_id -> [relationship_ids]
        self._document_relationships: Dict[str, List[str]] = {}  # document_id -> [relationship_ids]
        self._service_topic_users: Dict[str, List[str]] = {}  # (service, topic) -> [user_ids]

    async def save(self, relationship: DocumentRelationship) -> None:
        """Save a document relationship."""
        self._relationships[relationship.id] = relationship

        # Update indexes
        key = f"{relationship.user_id}:{relationship.document_id}"
        self._user_document_index[key] = relationship.id

        # User relationships index
        if relationship.user_id not in self._user_relationships:
            self._user_relationships[relationship.user_id] = []
        if relationship.id not in self._user_relationships[relationship.user_id]:
            self._user_relationships[relationship.user_id].append(relationship.id)

        # Document relationships index
        if relationship.document_id not in self._document_relationships:
            self._document_relationships[relationship.document_id] = []
        if relationship.id not in self._document_relationships[relationship.document_id]:
            self._document_relationships[relationship.document_id].append(relationship.id)

        # Update service-topic index
        self._update_service_topic_index(relationship)

    async def find_by_id(self, relationship_id: str) -> Optional[DocumentRelationship]:
        """Find a relationship by ID."""
        return self._relationships.get(relationship_id)

    async def find_by_user_and_document(self, user_id: str, document_id: str) -> Optional[DocumentRelationship]:
        """Find relationship between user and document."""
        key = f"{user_id}:{document_id}"
        relationship_id = self._user_document_index.get(key)
        return self._relationships.get(relationship_id) if relationship_id else None

    async def find_relationships_by_user(self, user_id: str) -> List[DocumentRelationship]:
        """Find all relationships for a user."""
        relationship_ids = self._user_relationships.get(user_id, [])
        return [self._relationships[rid] for rid in relationship_ids if rid in self._relationships]

    async def find_relationships_by_document(self, document_id: str) -> List[DocumentRelationship]:
        """Find all relationships for a document."""
        relationship_ids = self._document_relationships.get(document_id, [])
        return [self._relationships[rid] for rid in relationship_ids if rid in self._relationships]

    async def find_by_relationship_type(self, relationship_type: RelationshipType) -> List[DocumentRelationship]:
        """Find relationships by type."""
        return [rel for rel in self._relationships.values() if rel.relationship_type == relationship_type]

    async def find_by_access_level(self, access_level: AccessLevel) -> List[DocumentRelationship]:
        """Find relationships by access level."""
        return [rel for rel in self._relationships.values() if rel.access_level == access_level]

    async def find_users_by_document_and_topic(self, document_id: str, topic: str) -> List[str]:
        """Find users related to document with topic interest."""
        relationships = await self.find_relationships_by_document(document_id)
        user_ids = []

        for rel in relationships:
            # Check if user has this topic in their interests
            # This is a simplified implementation - in practice, this would need user data
            if topic in getattr(rel, 'tags', []):
                user_ids.append(rel.user_id)

        return user_ids

    async def find_users_by_service_and_topic(self, service_name: str, topic: str) -> List[str]:
        """Find users subscribed to service with topic interest."""
        key = f"{service_name}:{topic}"
        return self._service_topic_users.get(key, [])

    async def find_documents_by_user_and_service(self, user_id: str, service_name: str) -> List[str]:
        """Find documents related to user through service."""
        relationships = await self.find_relationships_by_user(user_id)
        document_ids = []

        for rel in relationships:
            if service_name in getattr(rel, 'services', []):
                document_ids.append(rel.document_id)

        return document_ids

    async def update(self, relationship: DocumentRelationship) -> None:
        """Update an existing relationship."""
        if relationship.id in self._relationships:
            self._relationships[relationship.id] = relationship
            self._update_service_topic_index(relationship)

    async def delete(self, relationship_id: str) -> bool:
        """Delete a relationship."""
        if relationship_id in self._relationships:
            relationship = self._relationships[relationship_id]

            # Remove from indexes
            key = f"{relationship.user_id}:{relationship.document_id}"
            if key in self._user_document_index:
                del self._user_document_index[key]

            # Remove from user relationships
            if relationship.user_id in self._user_relationships:
                self._user_relationships[relationship.user_id] = [
                    rid for rid in self._user_relationships[relationship.user_id]
                    if rid != relationship_id
                ]

            # Remove from document relationships
            if relationship.document_id in self._document_relationships:
                self._document_relationships[relationship.document_id] = [
                    rid for rid in self._document_relationships[relationship.document_id]
                    if rid != relationship_id
                ]

            del self._relationships[relationship_id]
            return True
        return False

    async def delete_by_user_and_document(self, user_id: str, document_id: str) -> bool:
        """Delete relationship between user and document."""
        key = f"{user_id}:{document_id}"
        relationship_id = self._user_document_index.get(key)
        if relationship_id:
            return await self.delete(relationship_id)
        return False

    async def exists(self, user_id: str, document_id: str) -> bool:
        """Check if relationship exists."""
        key = f"{user_id}:{document_id}"
        return key in self._user_document_index

    async def count_relationships_by_user(self, user_id: str) -> int:
        """Count relationships for a user."""
        return len(self._user_relationships.get(user_id, []))

    async def count_relationships_by_document(self, document_id: str) -> int:
        """Count relationships for a document."""
        return len(self._document_relationships.get(document_id, []))

    def _update_service_topic_index(self, relationship: DocumentRelationship) -> None:
        """Update the service-topic-user index."""
        # This is a simplified implementation
        # In practice, this would need access to user service data
        pass
