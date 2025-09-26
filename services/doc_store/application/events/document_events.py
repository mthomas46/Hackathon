"""Document events for Doc Store application layer.

Domain events representing document-related business occurrences.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import time


@dataclass
class DocumentEvent:
    """Base class for document events."""

    document_id: str
    timestamp: float
    event_id: str

    def __post_init__(self):
        """Set default timestamp if not provided."""
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class DocumentCreatedEvent(DocumentEvent):
    """Event fired when a document is created."""

    content: str
    metadata: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None

    def __post_init__(self):
        """Initialize event with defaults."""
        super().__post_init__()
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []


@dataclass
class DocumentUpdatedEvent(DocumentEvent):
    """Event fired when a document is updated."""

    old_content: Optional[str] = None
    new_content: Optional[str] = None
    metadata_changes: Optional[Dict[str, str]] = None

    def __post_init__(self):
        """Initialize event with defaults."""
        super().__post_init__()
        if self.metadata_changes is None:
            self.metadata_changes = {}


@dataclass
class DocumentDeletedEvent(DocumentEvent):
    """Event fired when a document is deleted."""

    # No additional fields needed for deletion events
    pass


@dataclass
class DocumentTaggedEvent(DocumentEvent):
    """Event fired when tags are added to a document."""

    added_tags: List[str]
    existing_tags: List[str]

    def __post_init__(self):
        """Initialize event with defaults."""
        super().__post_init__()
        if not self.added_tags:
            self.added_tags = []
        if not self.existing_tags:
            self.existing_tags = []
