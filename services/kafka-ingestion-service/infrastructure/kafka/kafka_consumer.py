"""Kafka Consumer Client."""

import logging
from typing import List, Optional
from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)


class KafkaConsumerClient:
    """
    Kafka consumer client for consuming document events.
    
    Wraps AIOKafkaConsumer with domain-specific configuration.
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "kafka-ingestion-service",
        auto_offset_reset: str = "earliest"
    ):
        """
        Initialize consumer client.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            group_id: Consumer group ID
            auto_offset_reset: Offset reset strategy
        """
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset
        self._consumer: Optional[AIOKafkaConsumer] = None
    
    async def start(self) -> None:
        """Start consumer."""
        logger.info(
            f"Starting Kafka consumer: {self.bootstrap_servers}, "
            f"group: {self.group_id}"
        )
        
        self._consumer = AIOKafkaConsumer(
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset=self.auto_offset_reset,
            enable_auto_commit=False,  # Manual commit for reliability
            value_deserializer=lambda m: m.decode('utf-8') if m else None,
        )
        
        await self._consumer.start()
        logger.info("Kafka consumer started")
    
    async def stop(self) -> None:
        """Stop consumer."""
        if self._consumer:
            logger.info("Stopping Kafka consumer")
            await self._consumer.stop()
            self._consumer = None
    
    async def subscribe(self, topics: List[str]) -> None:
        """
        Subscribe to topics.
        
        Args:
            topics: List of topics to subscribe to
            
        Raises:
            RuntimeError: If consumer not started
        """
        if not self._consumer:
            raise RuntimeError("Consumer not started")
        
        logger.info(f"Subscribing to topics: {topics}")
        self._consumer.subscribe(topics)
    
    async def poll(self, timeout_ms: int = 1000):
        """
        Poll for messages.
        
        Args:
            timeout_ms: Poll timeout in milliseconds
            
        Returns:
            Message batch
            
        Raises:
            RuntimeError: If consumer not started
        """
        if not self._consumer:
            raise RuntimeError("Consumer not started")
        
        return await self._consumer.getmany(timeout_ms=timeout_ms)
    
    async def commit(self) -> None:
        """
        Commit offsets.
        
        Raises:
            RuntimeError: If consumer not started
        """
        if not self._consumer:
            raise RuntimeError("Consumer not started")
        
        await self._consumer.commit()
    
    async def close(self) -> None:
        """Close consumer."""
        await self.stop()

