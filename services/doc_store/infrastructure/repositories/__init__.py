"""Infrastructure repositories for Doc Store service.

Repositories provide data access abstractions using adapters.
"""

from .base_repository import BaseRepository
from .document_repository import DocumentRepository

__all__ = [
    "BaseRepository",
    "DocumentRepository",
]
