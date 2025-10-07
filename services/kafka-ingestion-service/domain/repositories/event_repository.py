"""Event Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..entities.document_event import DocumentEvent
from ..value_objects.event_status import EventStatus


class EventRepository(ABC):
    """
    Abstract repository for document events.
    
    Defines the contract for persisting and retrieving events.
    """
    
    @abstractmethod
    async def save(self, event: DocumentEvent) -> None:
        """
        Save event.
        
        Args:
            event: Event to save
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, event_id: str) -> Optional[DocumentEvent]:
        """
        Get event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_document_id(self, document_id: str) -> List[DocumentEvent]:
        """
        Get all events for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of events
        """
        pass
    
    @abstractmethod
    async def get_by_status(
        self,
        status: EventStatus,
        limit: int = 100
    ) -> List[DocumentEvent]:
        """
        Get events by status.
        
        Args:
            status: Event status
            limit: Maximum number of events
            
        Returns:
            List of events
        """
        pass
    
    @abstractmethod
    async def get_by_correlation_id(self, correlation_id: str) -> List[DocumentEvent]:
        """
        Get events by correlation ID.
        
        Args:
            correlation_id: Correlation ID
            
        Returns:
            List of events
        """
        pass
    
    @abstractmethod
    async def get_failed_events(
        self,
        can_retry: bool = True,
        limit: int = 100
    ) -> List[DocumentEvent]:
        """
        Get failed events.
        
        Args:
            can_retry: Only return events that can be retried
            limit: Maximum number of events
            
        Returns:
            List of failed events
        """
        pass
    
    @abstractmethod
    async def get_events_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[DocumentEvent]:
        """
        Get events within time range.
        
        Args:
            start_time: Start time
            end_time: End time
            limit: Maximum number of events
            
        Returns:
            List of events
        """
        pass
    
    @abstractmethod
    async def update(self, event: DocumentEvent) -> None:
        """
        Update event.
        
        Args:
            event: Event to update
        """
        pass
    
    @abstractmethod
    async def delete(self, event_id: str) -> bool:
        """
        Delete event.
        
        Args:
            event_id: Event ID
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def count_by_status(self, status: EventStatus) -> int:
        """
        Count events by status.
        
        Args:
            status: Event status
            
        Returns:
            Number of events with status
        """
        pass

