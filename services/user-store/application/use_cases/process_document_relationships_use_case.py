"""Process Document Relationships Use Case for the User Store service.

This use case handles automatic creation of user-document relationships when
documents are processed by the source agent. It integrates with the document
processing pipeline to automatically extract and create relationships.
"""

from typing import Dict, List, Optional

from ...domain.services.user_service import UserService
from ..dto.user_dto import UserResponse


class ProcessDocumentRelationshipsUseCase:
    """Use case for processing document relationships and creating user associations."""

    def __init__(self, user_service: UserService):
        """Initialize the use case with required services."""
        self._user_service = user_service

    async def execute(
        self,
        document_id: str,
        document_content: str,
        document_metadata: Dict[str, any],
        source_type: str,
        document_tags: Optional[List[str]] = None,
        auto_create_users: bool = True
    ) -> Dict[str, any]:
        """Execute the document relationship processing use case.

        This method analyzes a document's content and metadata to automatically
        create user-document relationships. It's designed to be called by the
        source agent when documents are processed and stored.

        Args:
            document_id: Unique identifier of the processed document
            document_content: Full text content of the document
            document_metadata: Document metadata from the source system
            source_type: Source system type (github, jira, confluence)
            auto_create_users: Whether to auto-create placeholder users for unknown identifiers

        Returns:
            Dictionary containing processing results and created relationships
        """
        # Create relationships automatically
        relationships = await self._user_service.create_relationships_from_document(
            document_id=document_id,
            document_content=document_content,
            document_metadata=document_metadata,
            source_type=source_type,
            document_tags=document_tags
        )

        # Get summary of created relationships
        relationship_summary = self._summarize_relationships(relationships)

        # Get all users now related to this document
        document_users = await self._user_service.get_document_user_relationships(document_id)

        return {
            "document_id": document_id,
            "source_type": source_type,
            "relationships_created": len(relationships),
            "relationship_summary": relationship_summary,
            "total_related_users": sum(len(users) for users in document_users.values()),
            "user_relationships": {
                rel_type: [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "display_name": user.display_name
                    }
                    for user in users
                ]
                for rel_type, users in document_users.items()
            }
        }

    def _summarize_relationships(self, relationships: List) -> Dict[str, int]:
        """Summarize relationships by type."""
        summary = {}
        for rel in relationships:
            rel_type = rel.relationship_type.value
            summary[rel_type] = summary.get(rel_type, 0) + 1
        return summary

    async def get_document_users(
        self,
        document_id: str,
        relationship_type: Optional[str] = None
    ) -> List[UserResponse]:
        """Get all users related to a document, optionally filtered by relationship type.

        Args:
            document_id: Document identifier
            relationship_type: Optional filter by relationship type

        Returns:
            List of users related to the document
        """
        if relationship_type:
            # Get users by specific relationship type
            if relationship_type == "owner":
                users = await self._user_service.get_users_by_document(document_id)
                # Filter for owners only (this is a simplification)
                return [
                    UserResponse(
                        id=user.id,
                        email=user.email,
                        username=user.username,
                        display_name=user.display_name,
                        role=user.role.value,
                        status=user.status.value,
                        avatar_url=user.avatar_url,
                        bio=user.bio,
                        document_relationships=user.document_relationships,
                        service_subscriptions=user.service_subscriptions,
                        topic_interests=user.topic_interests,
                        last_login_at=user.last_login_at,
                        created_at=user.created_at,
                        updated_at=user.updated_at
                    )
                    for user in users
                    if any("owner" in rel.lower() for rel in user.document_relationships)
                ]
            else:
                # For other types, return all users (simplified implementation)
                users = await self._user_service.get_users_by_document(document_id)
        else:
            users = await self._user_service.get_users_by_document(document_id)

        return [
            UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                display_name=user.display_name,
                role=user.role.value,
                status=user.status.value,
                avatar_url=user.avatar_url,
                bio=user.bio,
                document_relationships=user.document_relationships,
                service_subscriptions=user.service_subscriptions,
                topic_interests=user.topic_interests,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]

    async def get_user_documents(
        self,
        user_id: str,
        relationship_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Get all documents related to a user, optionally filtered by relationship type.

        Args:
            user_id: User identifier
            relationship_type: Optional filter by relationship type

        Returns:
            Dictionary mapping relationship types to document ID lists
        """
        relationships = await self._user_service.get_user_document_relationships(user_id)

        if relationship_type:
            return {relationship_type: relationships.get(relationship_type, [])}
        else:
            return relationships
