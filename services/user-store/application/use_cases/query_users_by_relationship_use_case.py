"""Query Users by Relationship Use Case for the User Store service.

This module implements the use case for querying users based on their
relationships to documents, services, and topics, supporting the
interpreter and analysis service requirements.
"""

from typing import List, Optional

from domain.services.user_service import UserService
from application.dto.user_dto import UserResponse


class QueryUsersByRelationshipUseCase:
    """Use case for querying users based on relationships and interests."""

    def __init__(self, user_service: UserService):
        """Initialize the use case with required services."""
        self._user_service = user_service

    async def execute(
        self,
        document_id: Optional[str] = None,
        service_name: Optional[str] = None,
        topic: Optional[str] = None,
        relationship_type: Optional[str] = None,
        limit: int = 50
    ) -> List[UserResponse]:
        """Execute the query users by relationship use case.

        Query users based on various relationship criteria. Supports finding:
        - Users related to specific documents
        - Users subscribed to specific services
        - Users interested in specific topics
        - Users with combined service + topic interests

        Args:
            document_id: Filter by users related to this document
            service_name: Filter by users subscribed to this service
            topic: Filter by users interested in this topic
            relationship_type: Filter by relationship type (not implemented yet)
            limit: Maximum number of users to return

        Returns:
            List of UserResponse objects matching the criteria
        """
        users = []

        # Query based on primary criteria
        if document_id and topic:
            # Users related to document AND interested in topic
            document_users = await self._user_service.get_users_by_document(document_id)
            topic_users = await self._user_service.get_users_by_topic(topic)

            # Find intersection
            document_user_ids = {user.id for user in document_users}
            users = [user for user in topic_users if user.id in document_user_ids]

        elif service_name and topic:
            # Users subscribed to service AND interested in topic
            users = await self._user_service.get_users_by_service_and_topic(service_name, topic)

        elif document_id:
            # Users related to specific document
            users = await self._user_service.get_users_by_document(document_id)

        elif service_name:
            # Users subscribed to specific service
            users = await self._user_service.get_users_by_service(service_name)

        elif topic:
            # Users interested in specific topic
            users = await self._user_service.get_users_by_topic(topic)

        else:
            # No criteria specified, return empty list
            return []

        # Apply limit
        users = users[:limit]

        # Convert to response DTOs
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

    async def get_users_for_notification(
        self,
        document_id: Optional[str] = None,
        service_name: Optional[str] = None,
        topic: Optional[str] = None,
        event_type: str = "update"
    ) -> List[UserResponse]:
        """Get users who should be notified for a specific event.

        This method finds users who should receive notifications based on
        their relationships and preferences. Used by the notification service.

        Args:
            document_id: Document related to the event
            service_name: Service related to the event
            topic: Topic related to the event
            event_type: Type of event (update, comment, etc.)

        Returns:
            List of users who should be notified
        """
        # Get users based on relationships
        users = await self.execute(
            document_id=document_id,
            service_name=service_name,
            topic=topic
        )

        # Filter by notification preferences (simplified - in real implementation,
        # this would check individual user preferences for the specific document)
        return users
