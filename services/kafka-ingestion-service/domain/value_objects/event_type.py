"""Event Type Value Object."""

from enum import Enum


class EventType(str, Enum):
    """
    Document event types.
    
    Represents the type of change that occurred to a document.
    """
    
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_MOVED = "document_moved"
    DOCUMENT_RENAMED = "document_renamed"
    
    @property
    def is_mutation(self) -> bool:
        """Check if event represents a mutation (create/update)."""
        return self in (self.DOCUMENT_CREATED, self.DOCUMENT_UPDATED)
    
    @property
    def requires_content(self) -> bool:
        """Check if event requires document content."""
        return self in (self.DOCUMENT_CREATED, self.DOCUMENT_UPDATED)

