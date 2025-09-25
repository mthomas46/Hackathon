"""Domain Repositories - Data Access Layer.

This module contains standardized repository interfaces and implementations
following Domain-Driven Design principles.
"""

from .base_repository import (
    BaseRepository, SqlRepository, InMemoryRepository,
    BaseEntity, RepositoryError, EntityNotFoundError, DuplicateEntityError
)

__all__ = [
    "BaseRepository", "SqlRepository", "InMemoryRepository",
    "BaseEntity", "RepositoryError", "EntityNotFoundError", "DuplicateEntityError"
]
