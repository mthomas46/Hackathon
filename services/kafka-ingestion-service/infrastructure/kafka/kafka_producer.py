"""Kafka Producer Client."""

import json
import logging
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer

from ...domain.entities.document_event import DocumentEvent

logger = logging.getLogger(__name__)


class KafkaProducerClient:
    """
    Kafka producer client for publishing document events.
    
    Wraps AIOKafkaProducer with domain-specific methods.
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "document-events"
    ):
        """
        Initialize producer client.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Default topic
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self._producer: Optional[AIOKafkaProducer] = None
    
    async def start(self) -> None:
        """Start producer."""
        logger.info(f"Starting Kafka producer: {self.bootstrap_servers}")
        
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            compression_type="gzip",
            acks="all",  # Wait for all replicas
            retries=3,
        )
        
        await self._producer.start()
        logger.info("Kafka producer started")
    
    async def stop(self) -> None:
        """Stop producer."""
        if self._producer:
            logger.info("Stopping Kafka producer")
            await self._producer.stop()
            self._producer = None
    
    async def publish_event(
        self,
        event: DocumentEvent,
        topic: Optional[str] = None
    ) -> None:
        """
        Publish document event to Kafka.
        
        Args:
            event: Document event to publish
            topic: Optional topic override
            
        Raises:
            RuntimeError: If producer not started
        """
        if not self._producer:
            raise RuntimeError("Producer not started")
        
        target_topic = topic or self.topic
        
        # Convert event to dict
        event_data = event.to_dict()
        
        # Use document_id as key for partitioning
        key = event.document_id
        
        logger.debug(f"Publishing event {event.event_id} to topic {target_topic}")
        
        try:
            # Send message
            await self._producer.send_and_wait(
                target_topic,
                value=event_data,
                key=key
            )
            
            logger.info(
                f"Published event {event.event_id} for document {event.document_id}"
            )
            
        except Exception as e:
            logger.error(f"Error publishing event {event.event_id}: {str(e)}")
            raise
    
    async def publish_raw(
        self,
        data: Dict[str, Any],
        key: Optional[str] = None,
        topic: Optional[str] = None
    ) -> None:
        """
        Publish raw data to Kafka.
        
        Args:
            data: Data to publish
            key: Optional message key
            topic: Optional topic override
            
        Raises:
            RuntimeError: If producer not started
        """
        if not self._producer:
            raise RuntimeError("Producer not started")
        
        target_topic = topic or self.topic
        
        logger.debug(f"Publishing raw data to topic {target_topic}")
        
        try:
            await self._producer.send_and_wait(
                target_topic,
                value=data,
                key=key
            )
            
            logger.info(f"Published raw data to {target_topic}")
            
        except Exception as e:
            logger.error(f"Error publishing raw data: {str(e)}")
            raise

