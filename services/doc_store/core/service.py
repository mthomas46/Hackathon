"""Base service for business logic operations.

Provides common validation, error handling, and business rule patterns.
"""
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypeVar, Generic
from services.shared.responses import create_success_response, create_error_response
from services.shared.error_handling import ServiceException
from .entities import BaseEntity

T = TypeVar('T', bound=BaseEntity)


class BaseService(Generic[T], ABC):
    """Base service with common business logic patterns."""

    def __init__(self, repository):
        self.repository = repository

    @abstractmethod
    def _validate_entity(self, entity: T) -> None:
        """Validate entity before saving."""
        pass

    def create_entity(self, entity_data: Dict[str, Any], entity_id: Optional[str] = None) -> T:
        """Create a new entity with validation."""
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
        """Get entity by ID."""
        return self.repository.get_by_id(entity_id)

    def update_entity(self, entity_id: str, updates: Dict[str, Any]) -> T:
        """Update entity with validation."""
        # Get existing entity
        entity = self.repository.get_by_id(entity_id)
        if not entity:
            raise ServiceException(f"Entity {entity_id} not found", "NOT_FOUND")

        # Apply updates
        self._apply_updates(entity, updates)

        # Validate updated entity
        self._validate_entity(entity)

        # Save changes
        self.repository.update(entity)

        return entity

    def delete_entity(self, entity_id: str) -> None:
        """Delete entity by ID."""
        if not self.repository.exists(entity_id):
            raise ServiceException(f"Entity {entity_id} not found", "NOT_FOUND")

        self.repository.delete_by_id(entity_id)

    def list_entities(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List entities with pagination."""
        entities = self.repository.get_all(limit, offset)

        return {
            "items": [entity.to_dict() for entity in entities],
            "total": len(entities),
            "has_more": len(entities) == limit,
            "limit": limit,
            "offset": offset
        }

    @abstractmethod
    def _create_entity_from_data(self, entity_id: str, data: Dict[str, Any]) -> T:
        """Create entity instance from data dictionary."""
        pass

    def _apply_updates(self, entity: T, updates: Dict[str, Any]) -> None:
        """Apply updates to entity."""
        for key, value in updates.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate required fields are present."""
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            raise ServiceException(f"Missing required fields: {', '.join(missing_fields)}", "VALIDATION_ERROR")

    def _validate_field_type(self, value: Any, field_name: str, expected_type: type) -> None:
        """Validate field type."""
        if not isinstance(value, expected_type):
            raise ServiceException(f"Field '{field_name}' must be of type {expected_type.__name__}", "VALIDATION_ERROR")
