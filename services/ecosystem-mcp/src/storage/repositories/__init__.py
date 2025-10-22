"""
Repository pattern implementations for Ecosystem MCP Service.

Provides abstraction layer between business logic and database.
"""

from .base import BaseRepository
from .document_repository import DocumentRepository
from .embedding_repository import EmbeddingRepository
from .ingestion_job_repository import IngestionJobRepository
from .timeline_repository import (
    TimelineRepository,
    TimePeriodRepository,
    DocumentPlacementRepository
)

__all__ = [
    "BaseRepository",
    "DocumentRepository",
    "EmbeddingRepository",
    "IngestionJobRepository",
    "TimelineRepository",
    "TimePeriodRepository",
    "DocumentPlacementRepository",
]

