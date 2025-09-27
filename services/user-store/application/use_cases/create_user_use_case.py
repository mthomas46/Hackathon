"""Create User Use Case for the User Store service.

This module implements the use case for creating new users in the system,
handling validation, business rules, and persistence.
"""

from typing import Optional

from ...domain.entities.user import User, UserRole
from ...domain.services.user_service import UserService
from ..dto.user_dto import CreateUserRequest, UserResponse


class CreateUserUseCase:
    """Use case for creating new users."""

    def __init__(self, user_service: UserService):
        """Initialize the use case with required services."""
        self._user_service = user_service

    async def execute(self, request: CreateUserRequest) -> UserResponse:
        """Execute the create user use case.

        Args:
            request: CreateUserRequest containing user information

        Returns:
            UserResponse with the created user information

        Raises:
            ValueError: If user creation fails due to validation or conflicts
        """
        # Convert string role to enum
        role = getattr(UserRole, request.role.upper())

        # Create the user
        user = await self._user_service.create_user(
            email=request.email,
            username=request.username,
            display_name=request.display_name,
            role=role
        )

        # Convert to response DTO
        return UserResponse(
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
