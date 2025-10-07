"""Ingest Document Command."""

from dataclasses import dataclass
from typing import Dict, Optional, Any

from ...domain.entities.document_event import DocumentEvent
from ...domain.value_objects.event_type import EventType
from ...domain.value_objects.source_metadata import SourceMetadata
from ...domain.repositories.event_repository import EventRepository


@dataclass
class IngestDocumentCommand:
    """
    Command to ingest a document.
    
    Represents the intent to ingest a document event into the system.
    """
    
    document_id: str
    title: str
    content: str
    event_type: EventType
    source_metadata: Dict[str, Any]
    content_type: str = "text/markdown"
    source_url: Optional[str] = None
    tags: list[str] = None
    categories: list[str] = None
    metadata: Dict[str, Any] = None
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = []
        if self.categories is None:
            self.categories = []
        if self.metadata is None:
            self.metadata = {}


class IngestDocumentHandler:
    """
    Handler for ingest document command.
    
    Creates document event and persists it for processing.
    """
    
    def __init__(self, event_repository: EventRepository):
        """
        Initialize handler.
        
        Args:
            event_repository: Event repository
        """
        self.event_repository = event_repository
    
    async def handle(self, command: IngestDocumentCommand) -> DocumentEvent:
        """
        Handle ingest document command.
        
        Args:
            command: Ingest command
            
        Returns:
            Created document event
            
        Raises:
            ValueError: If command is invalid
        """
        # Validate command
        if not command.document_id:
            raise ValueError("Document ID is required")
        if not command.title:
            raise ValueError("Document title is required")
        if not command.content:
            raise ValueError("Document content is required")
        
        # Create source metadata
        source_metadata = SourceMetadata.from_dict(command.source_metadata)
        if not source_metadata.is_valid:
            raise ValueError("Invalid source metadata")
        
        # Create document event
        event = DocumentEvent(
            document_id=command.document_id,
            title=command.title,
            content=command.content,
            event_type=command.event_type,
            content_type=command.content_type,
            source_metadata=source_metadata,
            source_url=command.source_url,
            tags=command.tags,
            categories=command.categories,
            metadata=command.metadata,
            correlation_id=command.correlation_id,
        )
        
        # Mark as ingested
        event.mark_as_ingested()
        
        # Save event
        await self.event_repository.save(event)
        
        return event

