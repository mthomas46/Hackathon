"""Operation type value object."""

from enum import Enum
from typing import Optional


class OperationType(Enum):
    """Enumeration of supported ingestion operation types."""

    FETCH = "fetch"
    INGEST = "ingest"
    UPDATE = "update"
    DELETE = "delete"
    SYNC = "sync"
    VALIDATE = "validate"
    INDEX = "index"

    @classmethod
    def from_string(cls, value: str) -> Optional['OperationType']:
        """Create operation type from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def get_display_name(self) -> str:
        """Get human-readable display name."""
        display_names = {
            "fetch": "Fetch Documents",
            "ingest": "Ingest Documents",
            "update": "Update Documents",
            "delete": "Delete Documents",
            "sync": "Synchronize",
            "validate": "Validate",
            "index": "Index Documents",
        }
        return display_names.get(self.value, self.value.title())

    def is_write_operation(self) -> bool:
        """Check if this operation modifies data."""
        return self in [self.INGEST, self.UPDATE, self.DELETE, self.SYNC]

    def is_read_operation(self) -> bool:
        """Check if this operation only reads data."""
        return self in [self.FETCH, self.VALIDATE]

    def requires_source_connection(self) -> bool:
        """Check if this operation requires a live source connection."""
        return self in [self.FETCH, self.SYNC, self.VALIDATE]

    def can_be_retried(self) -> bool:
        """Check if this operation can be safely retried."""
        return self in [self.FETCH, self.INGEST, self.UPDATE, self.SYNC, self.INDEX]

    def get_timeout_seconds(self) -> int:
        """Get recommended timeout for this operation type."""
        timeouts = {
            self.FETCH: 300,      # 5 minutes for fetching
            self.INGEST: 600,     # 10 minutes for ingestion
            self.UPDATE: 180,     # 3 minutes for updates
            self.DELETE: 60,      # 1 minute for deletion
            self.SYNC: 1800,      # 30 minutes for sync
            self.VALIDATE: 120,   # 2 minutes for validation
            self.INDEX: 300,      # 5 minutes for indexing
        }
        return timeouts.get(self, 300)

    def get_max_retry_attempts(self) -> int:
        """Get maximum retry attempts for this operation."""
        retry_counts = {
            self.FETCH: 3,
            self.INGEST: 2,
            self.UPDATE: 2,
            self.DELETE: 1,
            self.SYNC: 1,
            self.VALIDATE: 3,
            self.INDEX: 2,
        }
        return retry_counts.get(self, 1)
