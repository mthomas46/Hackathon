"""Base service for business logic operations.

Provides common validation, error handling, and business rule patterns.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

# Import domain exceptions - no infrastructure dependencies
from .common.error_utils import DomainException, DomainServiceException
from ..exceptions.domain_exceptions import (
    DocStoreException,
    DocumentNotFoundException,
    DocumentValidationException,
)

from .entities import BaseEntity

T = TypeVar("T", bound=BaseEntity)


class BaseService(Generic[T], ABC):
    """Base service with common business logic patterns."""

    def __init__(self, repository):
        self.repository = repository

    @abstractmethod
    def _validate_entity(self, entity: T) -> None:
        """Validate entity before saving.

        Args:
            entity: Entity to validate

        Raises:
            ValidationError: If entity validation fails
        """

    def create_entity(
        self, entity_data: Dict[str, Any], entity_id: Optional[str] = None
    ) -> T:
        """Create a new entity with validation.

        Args:
            entity_data: Data to create entity from
            entity_id: Optional entity ID, generated if not provided

        Returns:
            Created entity

        Raises:
            ValidationError: If entity data is invalid
            DuplicateError: If entity already exists
        """
        # Generate ID if not provided
        if not entity_id:
            entity_id = str(uuid.uuid4())

        # Create entity instance
        entity = self._create_entity_from_data(entity_id, entity_data)

        # Validate entity
        self._validate_entity(entity)

        # Save to repository
        self.repository.save(entity)

        return entity

    def get_entity(self, entity_id: str) -> Optional[T]:
        """Get entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """
        return self.repository.find_by_id(entity_id)

    def update_entity(self, entity_id: str, updates: Dict[str, Any]) -> T:
        """Update entity with validation.

        Args:
            entity_id: Entity identifier
            updates: Fields to update

        Returns:
            Updated entity

        Raises:
            ServiceException: If entity not found or update fails
        """
        # Get existing entity
        entity = self.repository.find_by_id(entity_id)
        if not entity:
            raise DocumentNotFoundException(entity_id)

        # Apply updates
        self._apply_updates(entity, updates)

        # Validate updated entity
        self._validate_entity(entity)

        # Save changes
        self.repository.update(entity)

        return entity

    def delete_entity(self, entity_id: str) -> None:
        """Delete entity by ID.

        Args:
            entity_id: Entity identifier to delete

        Raises:
            DocumentNotFoundException: If entity not found
        """
        if not self.repository.exists(entity_id):
            raise DocumentNotFoundException(entity_id)

        self.repository.delete_by_id(entity_id)

    def list_entities(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List entities with pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            Dictionary containing items, total count, and pagination info
        """
        entities = self.repository.get_all(limit, offset)
        total_count = self.repository.count()
        has_more = (offset + len(entities)) < total_count

        return {
            "items": [entity.to_dict() for entity in entities],
            "total": total_count,
            "has_more": has_more,
            "limit": limit,
            "offset": offset,
        }

    @abstractmethod
    def _create_entity_from_data(self, entity_id: str, data: Dict[str, Any]) -> T:
        """Create entity instance from data dictionary.

        Args:
            entity_id: Unique identifier for the entity
            data: Dictionary containing entity data

        Returns:
            New entity instance
        """

    def _apply_updates(self, entity: T, updates: Dict[str, Any]) -> None:
        """Apply updates to entity.

        Args:
            entity: Entity to update
            updates: Dictionary of field updates
        """
        for key, value in updates.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

    def _validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """Validate required fields are present."""
        missing_fields = [
            field
            for field in required_fields
            if field not in data or data[field] is None
        ]
        if missing_fields:
            raise DocumentValidationException(
                f"Missing required fields: {', '.join(missing_fields)}",
                missing_fields
            )

    def _validate_field_type(
        self, value: Any, field_name: str, expected_type: type
    ) -> None:
        """Validate field type.

        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            expected_type: Expected type for the field

        Raises:
            DocumentValidationException: If field type is incorrect
        """
        if not isinstance(value, expected_type):
            raise DocumentValidationException(
                f"Field '{field_name}' must be of type {expected_type.__name__}",
                [f"Field '{field_name}' has incorrect type"]
            )
