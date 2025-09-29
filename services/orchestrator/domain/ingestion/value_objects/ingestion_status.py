"""Ingestion Status Value Object"""

from enum import Enum


class IngestionStatus(Enum):
    """Enumeration of ingestion process statuses."""

    PENDING = "pending"           # Ingestion request received, waiting to start
    QUEUED = "queued"            # Ingestion queued for processing
    INITIALIZING = "initializing" # Setting up ingestion process
    CONNECTING = "connecting"     # Connecting to source system
    DISCOVERING = "discovering"   # Discovering content to ingest
    DOWNLOADING = "downloading"   # Downloading content from source
    PROCESSING = "processing"     # Processing downloaded content
    INDEXING = "indexing"         # Indexing content for search
    VALIDATING = "validating"     # Validating ingested content
    COMPLETED = "completed"       # Ingestion completed successfully
    FAILED = "failed"            # Ingestion failed with error
    CANCELLED = "cancelled"      # Ingestion was cancelled
    PARTIAL_SUCCESS = "partial_success"  # Some content ingested, some failed

    @property
    def is_active(self) -> bool:
        """Check if ingestion is currently active."""
        active_statuses = {
            IngestionStatus.INITIALIZING,
            IngestionStatus.CONNECTING,
            IngestionStatus.DISCOVERING,
            IngestionStatus.DOWNLOADING,
            IngestionStatus.PROCESSING,
            IngestionStatus.INDEXING,
            IngestionStatus.VALIDATING
        }
        return self in active_statuses

    @property
    def is_final(self) -> bool:
        """Check if this is a final status."""
        final_statuses = {
            IngestionStatus.COMPLETED,
            IngestionStatus.FAILED,
            IngestionStatus.CANCELLED,
            IngestionStatus.PARTIAL_SUCCESS
        }
        return self in final_statuses

    @property
    def is_successful(self) -> bool:
        """Check if ingestion was successful."""
        return self in (IngestionStatus.COMPLETED, IngestionStatus.PARTIAL_SUCCESS)

    @property
    def can_retry(self) -> bool:
        """Check if this status allows retry."""
        return self in (IngestionStatus.FAILED, IngestionStatus.PARTIAL_SUCCESS)

    @property
    def progress_percentage(self) -> int:
        """Get approximate progress percentage for this status."""
        progress_map = {
            IngestionStatus.PENDING: 0,
            IngestionStatus.QUEUED: 5,
            IngestionStatus.INITIALIZING: 10,
            IngestionStatus.CONNECTING: 20,
            IngestionStatus.DISCOVERING: 30,
            IngestionStatus.DOWNLOADING: 50,
            IngestionStatus.PROCESSING: 70,
            IngestionStatus.INDEXING: 85,
            IngestionStatus.VALIDATING: 95,
            IngestionStatus.COMPLETED: 100,
            IngestionStatus.FAILED: 0,
            IngestionStatus.CANCELLED: 0,
            IngestionStatus.PARTIAL_SUCCESS: 100
        }
        return progress_map.get(self, 0)

    def __str__(self) -> str:
        return self.value.replace('_', ' ').title()
