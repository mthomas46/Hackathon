"""Document status value object."""

from enum import Enum
from typing import Optional, List


class DocumentStatus(Enum):
    """Enumeration of document processing statuses."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PROCESSING = "processing"
    FAILED = "failed"
    VALIDATING = "validating"
    INDEXING = "indexing"

    @classmethod
    def from_string(cls, value: str) -> Optional['DocumentStatus']:
        """Create document status from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def get_display_name(self) -> str:
        """Get human-readable display name."""
        display_names = {
            "active": "Active",
            "archived": "Archived",
            "deleted": "Deleted",
            "processing": "Processing",
            "failed": "Failed",
            "validating": "Validating",
            "indexing": "Indexing",
        }
        return display_names.get(self.value, self.value.title())

    def is_terminal(self) -> bool:
        """Check if this is a terminal status (no further processing)."""
        return self in [self.ACTIVE, self.ARCHIVED, self.DELETED, self.FAILED]

    def is_transient(self) -> bool:
        """Check if this is a transient status (processing in progress)."""
        return self in [self.PROCESSING, self.VALIDATING, self.INDEXING]

    def allows_modification(self) -> bool:
        """Check if document can be modified in this status."""
        return self in [self.ACTIVE, self.PROCESSING]

    def requires_cleanup(self) -> bool:
        """Check if this status requires cleanup operations."""
        return self in [self.FAILED, self.DELETED]

    @classmethod
    def get_active_statuses(cls) -> List['DocumentStatus']:
        """Get all statuses that indicate active/available documents."""
        return [cls.ACTIVE, cls.PROCESSING, cls.VALIDATING, cls.INDEXING]

    @classmethod
    def get_inactive_statuses(cls) -> List['DocumentStatus']:
        """Get all statuses that indicate inactive/unavailable documents."""
        return [cls.ARCHIVED, cls.DELETED, cls.FAILED]

    def can_transition_to(self, new_status: 'DocumentStatus') -> bool:
        """Check if transition to new status is allowed."""
        # Define valid transitions
        valid_transitions = {
            self.ACTIVE: [self.ARCHIVED, self.DELETED, self.PROCESSING],
            self.ARCHIVED: [self.ACTIVE, self.DELETED],
            self.DELETED: [],  # Terminal state
            self.PROCESSING: [self.ACTIVE, self.FAILED],
            self.FAILED: [self.PROCESSING],  # Can retry
            self.VALIDATING: [self.ACTIVE, self.FAILED],
            self.INDEXING: [self.ACTIVE, self.FAILED],
        }

        return new_status in valid_transitions.get(self, [])
