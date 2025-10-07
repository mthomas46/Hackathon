"""Kafka Consumer Service."""

import logging
import json
import asyncio
from typing import Optional, Callable, Any

from ...domain.entities.document_event import DocumentEvent

logger = logging.getLogger(__name__)


class KafkaConsumerService:
    """
    Service for consuming document events from Kafka.
    
    Listens to Kafka topics and processes incoming document events.
    """
    
    def __init__(
        self,
        kafka_consumer: Any,  # Will be KafkaConsumer from infrastructure
        event_processor: Any,  # EventProcessorService
        topic: str = "document-events"
    ):
        """
        Initialize service.
        
        Args:
            kafka_consumer: Kafka consumer instance
            event_processor: Event processor service
            topic: Kafka topic to consume from
        """
        self.kafka_consumer = kafka_consumer
        self.event_processor = event_processor
        self.topic = topic
        self._running = False
    
    async def start(self) -> None:
        """Start consuming events from Kafka."""
        logger.info(f"Starting Kafka consumer for topic: {self.topic}")
        
        self._running = True
        
        # Subscribe to topic
        await self.kafka_consumer.subscribe([self.topic])
        
        # Start consuming
        while self._running:
            try:
                # Poll for messages
                messages = await self.kafka_consumer.poll(timeout_ms=1000)
                
                for topic_partition, records in messages.items():
                    for record in records:
                        await self._process_message(record)
                
            except Exception as e:
                logger.error(f"Error consuming from Kafka: {str(e)}")
                await asyncio.sleep(5)  # Backoff on error
    
    async def stop(self) -> None:
        """Stop consuming events."""
        logger.info("Stopping Kafka consumer")
        self._running = False
        await self.kafka_consumer.close()
    
    async def _process_message(self, record: Any) -> None:
        """
        Process a Kafka message.
        
        Args:
            record: Kafka record
        """
        try:
            # Parse message
            event_data = json.loads(record.value)
            
            # Create DocumentEvent
            event = DocumentEvent.from_dict(event_data)
            
            logger.info(
                f"Received event {event.event_id} for document {event.document_id}"
            )
            
            # Process event
            success = await self.event_processor.process_event(event)
            
            if success:
                # Commit offset
                await self.kafka_consumer.commit()
            else:
                logger.warning(f"Event {event.event_id} processing failed")
                # Don't commit - will retry on next poll
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Log and continue - don't block consumer

