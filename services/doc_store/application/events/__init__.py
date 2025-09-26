"""Application events for Doc Store service.

Domain events that represent business occurrences.
"""

from .document_events import (
    DocumentCreatedEvent,
    DocumentUpdatedEvent,
    DocumentDeletedEvent,
    DocumentTaggedEvent
)

__all__ = [
    "DocumentCreatedEvent",
    "DocumentUpdatedEvent",
    "DocumentDeletedEvent",
    "DocumentTaggedEvent",
]
