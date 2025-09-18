"""Event Publisher - Publishes application events to external systems."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from .application_events import ApplicationEvent


logger = logging.getLogger(__name__)


class EventPublisher(ABC):
    """Abstract base class for event publishers."""

    @abstractmethod
    async def publish(self, event: ApplicationEvent) -> None:
        """Publish a single event."""
        pass

    @abstractmethod
    async def publish_batch(self, events: List[ApplicationEvent]) -> None:
        """Publish multiple events in batch."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the publisher and cleanup resources."""
        pass


class InMemoryEventPublisher(EventPublisher):
    """In-memory event publisher for testing and development."""

    def __init__(self):
        """Initialize in-memory publisher."""
        self.published_events: List[Dict[str, Any]] = []
        self.event_handlers: List[callable] = []

    async def publish(self, event: ApplicationEvent) -> None:
        """Publish event to in-memory store."""
        event_dict = event.to_dict()
        self.published_events.append(event_dict)

        # Notify handlers
        for handler in self.event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}", exc_info=True)

        logger.debug(f"Published event: {event.event_type.value} ({event.event_id})")

    async def publish_batch(self, events: List[ApplicationEvent]) -> None:
        """Publish multiple events."""
        for event in events:
            await self.publish(event)

    async def close(self) -> None:
        """Close publisher."""
        self.published_events.clear()
        self.event_handlers.clear()

    def add_handler(self, handler: callable) -> None:
        """Add event handler."""
        self.event_handlers.append(handler)

    def get_published_events(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get published events, optionally filtered by type."""
        if event_type:
            return [e for e in self.published_events if e['event_type'] == event_type]
        return self.published_events.copy()

    def clear_events(self) -> None:
        """Clear all published events."""
        self.published_events.clear()


class RedisEventPublisher(EventPublisher):
    """Redis-based event publisher for production use."""

    def __init__(self, redis_client=None, channel_prefix: str = "analysis-service:events"):
        """Initialize Redis publisher."""
        self.redis = redis_client
        self.channel_prefix = channel_prefix
        self._publish_queue: asyncio.Queue = asyncio.Queue()
        self._publisher_task: Optional[asyncio.Task] = None

    async def publish(self, event: ApplicationEvent) -> None:
        """Publish event to Redis."""
        if not self.redis:
            logger.warning("Redis client not available, event not published")
            return

        event_dict = event.to_dict()
        channel = f"{self.channel_prefix}:{event.event_type.value}"

        try:
            # Publish to Redis channel
            await self.redis.publish(channel, json.dumps(event_dict))

            # Also store in a list for persistence (optional)
            await self.redis.lpush(f"{channel}:history", json.dumps(event_dict))
            await self.redis.ltrim(f"{channel}:history", 0, 999)  # Keep last 1000 events

            logger.debug(f"Published event to Redis: {event.event_type.value}")

        except Exception as e:
            logger.error(f"Failed to publish event to Redis: {e}", exc_info=True)

    async def publish_batch(self, events: List[ApplicationEvent]) -> None:
        """Publish multiple events."""
        for event in events:
            await self.publish(event)

    async def close(self) -> None:
        """Close publisher."""
        if self._publisher_task:
            self._publisher_task.cancel()
            try:
                await self._publisher_task
            except asyncio.CancelledError:
                pass


class KafkaEventPublisher(EventPublisher):
    """Kafka-based event publisher for high-throughput scenarios."""

    def __init__(self, kafka_producer=None, topic_prefix: str = "analysis-service-events"):
        """Initialize Kafka publisher."""
        self.producer = kafka_producer
        self.topic_prefix = topic_prefix

    async def publish(self, event: ApplicationEvent) -> None:
        """Publish event to Kafka."""
        if not self.producer:
            logger.warning("Kafka producer not available, event not published")
            return

        event_dict = event.to_dict()
        topic = f"{self.topic_prefix}-{event.event_type.value}"

        try:
            # Publish to Kafka topic
            await self.producer.send(topic, value=event_dict)

            logger.debug(f"Published event to Kafka: {event.event_type.value}")

        except Exception as e:
            logger.error(f"Failed to publish event to Kafka: {e}", exc_info=True)

    async def publish_batch(self, events: List[ApplicationEvent]) -> None:
        """Publish multiple events."""
        for event in events:
            await self.publish(event)

    async def close(self) -> None:
        """Close publisher."""
        if self.producer:
            await self.producer.close()


class CompositeEventPublisher(EventPublisher):
    """Composite publisher that publishes to multiple destinations."""

    def __init__(self, publishers: List[EventPublisher]):
        """Initialize composite publisher."""
        self.publishers = publishers

    async def publish(self, event: ApplicationEvent) -> None:
        """Publish to all publishers."""
        tasks = [publisher.publish(event) for publisher in self.publishers]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def publish_batch(self, events: List[ApplicationEvent]) -> None:
        """Publish batch to all publishers."""
        tasks = [publisher.publish_batch(events) for publisher in self.publishers]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def close(self) -> None:
        """Close all publishers."""
        tasks = [publisher.close() for publisher in self.publishers]
        await asyncio.gather(*tasks, return_exceptions=True)


class EventPublisherFactory:
    """Factory for creating event publishers."""

    @staticmethod
    def create_in_memory() -> EventPublisher:
        """Create in-memory publisher for testing."""
        return InMemoryEventPublisher()

    @staticmethod
    def create_redis(redis_client=None) -> EventPublisher:
        """Create Redis publisher."""
        return RedisEventPublisher(redis_client)

    @staticmethod
    def create_kafka(kafka_producer=None) -> EventPublisher:
        """Create Kafka publisher."""
        return KafkaEventPublisher(kafka_producer)

    @staticmethod
    def create_composite(publishers: List[EventPublisher]) -> EventPublisher:
        """Create composite publisher."""
        return CompositeEventPublisher(publishers)

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> EventPublisher:
        """Create publisher from configuration."""
        publisher_type = config.get('type', 'in_memory')
        publishers = []

        if publisher_type == 'in_memory' or not config.get('redis') or not config.get('kafka'):
            publishers.append(EventPublisherFactory.create_in_memory())

        if config.get('redis'):
            publishers.append(EventPublisherFactory.create_redis(config['redis']))

        if config.get('kafka'):
            publishers.append(EventPublisherFactory.create_kafka(config['kafka']))

        if len(publishers) == 1:
            return publishers[0]
        else:
            return EventPublisherFactory.create_composite(publishers)
