"""Event Processor Service."""

import logging
from typing import Optional, Any
import httpx

from ...domain.entities.document_event import DocumentEvent
from ...domain.value_objects.event_status import EventStatus
from ...domain.repositories.event_repository import EventRepository
from ...domain.events.ingestion_events import EventProcessed, EventFailed

logger = logging.getLogger(__name__)


class EventProcessorService:
    """
    Service for processing document events.
    
    Coordinates event processing and updates event status.
    """
    
    def __init__(
        self,
        event_repository: EventRepository,
        doc_store_url: str = "http://doc_store:5087",
        doc_store_client: Optional[Any] = None  # Will be injected
    ):
        """
        Initialize service.
        
        Args:
            event_repository: Event repository
            doc_store_url: URL for doc_store service
            doc_store_client: Optional doc_store client
        """
        self.event_repository = event_repository
        self.doc_store_url = doc_store_url
        self.doc_store_client = doc_store_client
    
    async def process_event(self, event: DocumentEvent) -> bool:
        """
        Process a document event.
        
        Args:
            event: Event to process
            
        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            # Mark as processing
            event.mark_as_processing()
            await self.event_repository.update(event)
            
            logger.info(f"Processing event {event.event_id} for document {event.document_id}")
            
            # Process based on event type
            if event.event_type.requires_content:
                await self._process_content_event(event)
            else:
                await self._process_metadata_event(event)
            
            # Mark as processed
            event.mark_as_processed()
            await self.event_repository.update(event)
            
            # Get processing time
            processing_time = event.get_processing_duration() or 0.0
            
            logger.info(
                f"Event {event.event_id} processed successfully in {processing_time:.2f}s"
            )
            
            # Publish domain event
            # TODO: Integrate with event bus
            processed_event = EventProcessed.create(
                event_id=event.event_id,
                document_id=event.document_id,
                processing_time_seconds=processing_time,
                correlation_id=event.correlation_id,
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {str(e)}")
            
            # Mark as failed
            event.mark_as_failed(str(e))
            await self.event_repository.update(event)
            
            # Check if can retry
            can_retry = event.can_retry()
            
            # Publish domain event
            # TODO: Integrate with event bus
            failed_event = EventFailed.create(
                event_id=event.event_id,
                document_id=event.document_id,
                error_message=str(e),
                retry_count=event.retry_count,
                can_retry=can_retry,
                correlation_id=event.correlation_id,
            )
            
            return False
    
    async def _process_content_event(self, event: DocumentEvent) -> None:
        """
        Process content event (create/update).
        
        Args:
            event: Event to process
        """
        # Validate content
        if not event.content:
            raise ValueError("Content is required for content event")
        
        # Send to doc_store
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Prepare document payload
                doc_payload = {
                    "id": event.document_id,
                    "content": event.content,
                    "metadata": {
                        "title": event.title or event.document_id,
                        "source_url": event.source_url or "",
                        "tags": event.tags or [],
                        "categories": event.categories or [],
                        "correlation_id": event.correlation_id,
                        "event_id": event.event_id,
                        "content_type": event.content_type,
                        **(event.metadata or {})
                    }
                }
                
                logger.info(f"Sending document {event.document_id} to doc_store at {self.doc_store_url}")
                
                response = await client.post(
                    f"{self.doc_store_url}/api/v1/documents",
                    json=doc_payload
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Successfully sent document {event.document_id} to doc_store")
                else:
                    error_msg = f"doc_store returned {response.status_code}: {response.text[:200]}"
                    logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)
                    
        except httpx.ConnectError as e:
            logger.error(f"❌ Cannot connect to doc_store at {self.doc_store_url}: {e}")
            raise Exception(f"doc_store connection failed: {e}")
        except httpx.TimeoutException as e:
            logger.error(f"❌ Timeout connecting to doc_store: {e}")
            raise Exception(f"doc_store timeout: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to send to doc_store: {e}")
            raise
    
    async def _process_metadata_event(self, event: DocumentEvent) -> None:
        """
        Process metadata event (delete/move/rename).
        
        Args:
            event: Event to process
        """
        if self.doc_store_client:
            # Send to doc_store
            # TODO: Implement doc_store client integration
            logger.info(f"Would send metadata event {event.event_id} to doc_store")
        else:
            logger.warning("doc_store client not configured")
    
    async def retry_failed_event(self, event_id: str) -> bool:
        """
        Retry a failed event.
        
        Args:
            event_id: Event ID
            
        Returns:
            True if retry initiated, False otherwise
        """
        # Get event
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            logger.error(f"Event {event_id} not found")
            return False
        
        # Check if can retry
        if not event.can_retry():
            logger.error(f"Event {event_id} cannot be retried")
            return False
        
        # Increment retry count
        if not event.increment_retry():
            logger.error(f"Event {event_id} exceeded max retries")
            event.status = EventStatus.DEAD_LETTER
            await self.event_repository.update(event)
            return False
        
        # Reset status to pending
        event.status = EventStatus.RETRYING
        await self.event_repository.update(event)
        
        # Process event
        return await self.process_event(event)

