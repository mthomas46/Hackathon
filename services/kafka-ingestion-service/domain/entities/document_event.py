"""Document Event Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from uuid import uuid4

from ..value_objects.event_type import EventType
from ..value_objects.event_status import EventStatus
from ..value_objects.source_metadata import SourceMetadata


@dataclass
class DocumentEvent:
    """
    Document event entity.
    
    Represents a document-related event (creation, update, deletion)
    that flows through the ingestion pipeline.
    
    Aggregate root for event processing operations.
    """
    
    # Identity
    event_id: str = field(default_factory=lambda: str(uuid4()))
    document_id: str = ""
    
    # Event type and status
    event_type: EventType = EventType.DOCUMENT_CREATED
    status: EventStatus = EventStatus.PENDING
    
    # Source information
    source_metadata: SourceMetadata = field(default_factory=lambda: SourceMetadata())
    
    # Document content
    title: str = ""
    content: str = ""
    content_type: str = "text/markdown"
    
    # URLs
    source_url: Optional[str] = None
    normalized_url: Optional[str] = None
    
    # Metadata
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing tracking
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    
    # Timestamps
    event_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ingested_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    # Correlation
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate event."""
        if not self.event_id:
            self.event_id = str(uuid4())
        if not self.document_id:
            raise ValueError("Document ID is required")
        if not self.title:
            raise ValueError("Document title is required")
        if not self.content:
            raise ValueError("Document content is required")
    
    def mark_as_ingested(self) -> None:
        """Mark event as ingested."""
        self.status = EventStatus.INGESTED
        self.ingested_at = datetime.now(timezone.utc)
    
    def mark_as_processing(self) -> None:
        """Mark event as currently processing."""
        if not self.status.can_transition_to(EventStatus.PROCESSING):
            raise ValueError(f"Cannot transition from {self.status} to PROCESSING")
        self.status = EventStatus.PROCESSING
    
    def mark_as_processed(self) -> None:
        """Mark event as successfully processed."""
        if not self.status.can_transition_to(EventStatus.PROCESSED):
            raise ValueError(f"Cannot transition from {self.status} to PROCESSED")
        self.status = EventStatus.PROCESSED
        self.processed_at = datetime.now(timezone.utc)
    
    def mark_as_failed(self, error: str) -> None:
        """
        Mark event as failed.
        
        Args:
            error: Error message
        """
        self.status = EventStatus.FAILED
        self.error_message = error
        self.processed_at = datetime.now(timezone.utc)
    
    def increment_retry(self) -> bool:
        """
        Increment retry count.
        
        Returns:
            True if can retry, False if max retries exceeded
        """
        self.retry_count += 1
        return self.retry_count <= self.max_retries
    
    def can_retry(self) -> bool:
        """Check if event can be retried."""
        return (
            self.status == EventStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    def is_terminal(self) -> bool:
        """Check if event is in terminal state."""
        return self.status.is_terminal
    
    def get_processing_duration(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if not self.ingested_at or not self.processed_at:
            return None
        return (self.processed_at - self.ingested_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "document_id": self.document_id,
            "event_type": self.event_type.value,
            "status": self.status.value,
            "source_metadata": self.source_metadata.to_dict(),
            "title": self.title,
            "content": self.content,
            "content_type": self.content_type,
            "source_url": self.source_url,
            "normalized_url": self.normalized_url,
            "tags": self.tags,
            "categories": self.categories,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "event_timestamp": self.event_timestamp.isoformat(),
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "correlation_id": self.correlation_id,
            "parent_event_id": self.parent_event_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentEvent":
        """
        Create event from dictionary.
        
        Args:
            data: Event data
            
        Returns:
            DocumentEvent instance
        """
        # Parse timestamps
        event_timestamp = datetime.fromisoformat(data["event_timestamp"])
        ingested_at = datetime.fromisoformat(data["ingested_at"]) if data.get("ingested_at") else None
        processed_at = datetime.fromisoformat(data["processed_at"]) if data.get("processed_at") else None
        
        return cls(
            event_id=data["event_id"],
            document_id=data["document_id"],
            event_type=EventType(data["event_type"]),
            status=EventStatus(data["status"]),
            source_metadata=SourceMetadata.from_dict(data["source_metadata"]),
            title=data["title"],
            content=data["content"],
            content_type=data.get("content_type", "text/markdown"),
            source_url=data.get("source_url"),
            normalized_url=data.get("normalized_url"),
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            metadata=data.get("metadata", {}),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            error_message=data.get("error_message"),
            event_timestamp=event_timestamp,
            ingested_at=ingested_at,
            processed_at=processed_at,
            correlation_id=data.get("correlation_id"),
            parent_event_id=data.get("parent_event_id"),
        )

