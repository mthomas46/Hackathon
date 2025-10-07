"""Event DTOs."""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class EventDTO:
    """Data transfer object for document event."""
    
    event_id: str
    document_id: str
    event_type: str
    status: str
    title: str
    source_type: str
    source_url: Optional[str]
    tags: List[str]
    categories: List[str]
    retry_count: int
    error_message: Optional[str]
    event_timestamp: str
    ingested_at: Optional[str]
    processed_at: Optional[str]
    correlation_id: Optional[str]
    
    @classmethod
    def from_entity(cls, event: Any) -> "EventDTO":
        """
        Create DTO from entity.
        
        Args:
            event: DocumentEvent entity
            
        Returns:
            EventDTO
        """
        return cls(
            event_id=event.event_id,
            document_id=event.document_id,
            event_type=event.event_type.value,
            status=event.status.value,
            title=event.title,
            source_type=event.source_metadata.source_type,
            source_url=event.source_url,
            tags=event.tags,
            categories=event.categories,
            retry_count=event.retry_count,
            error_message=event.error_message,
            event_timestamp=event.event_timestamp.isoformat(),
            ingested_at=event.ingested_at.isoformat() if event.ingested_at else None,
            processed_at=event.processed_at.isoformat() if event.processed_at else None,
            correlation_id=event.correlation_id,
        )


@dataclass
class EventListDTO:
    """Data transfer object for list of events."""
    
    events: List[EventDTO]
    total: int
    page: int
    page_size: int

