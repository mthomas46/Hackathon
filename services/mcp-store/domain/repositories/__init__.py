"""Repository interfaces for MCP Store."""

from services.mcp_store.domain.repositories.package_repository import (
    PackageRepository,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
)
from services.mcp_store.domain.repositories.storage_repository import (
    StorageRepository,
    StorageError,
)

__all__ = [
    "PackageRepository",
    "StorageRepository",
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "StorageError",
]
