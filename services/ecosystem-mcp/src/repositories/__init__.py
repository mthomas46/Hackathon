"""
Repositories package (compatibility alias).

This package provides backward compatibility by re-exporting
repositories from src.storage.repositories.
"""

from ..storage.repositories import (
    DocumentRepository,
    IngestionJobRepository,
    DocumentationRunRepository
)

__all__ = [
    "DocumentRepository",
    "IngestionJobRepository",
    "DocumentationRunRepository",
]

