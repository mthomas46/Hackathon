"""Redis Event Bus - Production-ready event publishing with Redis."""

import asyncio
import json
import pickle
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
import threading

from .event_bus import (
    EventBus, EventPublisher, EventSubscriber,
    DomainEvent, EventEnvelope, EventPriority
)


class RedisEventBus(EventBus):
    """Redis-based event bus for production use."""

    def __init__(
        self,
        redis_client=None,
        serializer=None,
        channel_prefix: str = "event:",
        consumer_group: str = "analysis_service",
        consumer_name: Optional[str] = None,
        max_connections: int = 10
    ):
        """Initialize Redis event bus."""
        self.redis = redis_client
        self.serializer = serializer
        self.channel_prefix = channel_prefix
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name or f"consumer_{threading.current_thread().ident}"
        self.max_connections = max_connections

        # Connection pool for pub/sub
        self._pubsub_connections: Dict[str, Any] = {}
        self._subscriber_tasks: Dict[str, asyncio.Task] = {}
        self._handlers: Dict[str, List[Callable]] = {}

        # Statistics
        self.messages_published = 0
        self.messages_received = 0
        self.errors_count = 0

    async def publish(self, event: Union[DomainEvent, EventEnvelope], topic: Optional[str] = None) -> None:
        """Publish an event to Redis."""
        if not self.redis:
            raise RuntimeError("Redis client not configured")

        try:
            # Convert to envelope if needed
            if isinstance(event, DomainEvent):
                if topic is None:
                    topic = self._get_default_topic(event)
                envelope = EventEnvelope(event=event, topic=topic)
            else:
                envelope = event
                if topic:
                    envelope.topic = topic

            # Serialize envelope
            message_data = self._serialize_envelope(envelope)

            # Publish to Redis channel
            channel = f"{self.channel_prefix}{envelope.topic}"
            await self.redis.publish(channel, message_data)

            # Also store in stream for persistence (optional)
            stream_key = f"stream:{envelope.topic}"
            await self.redis.xadd(stream_key, {
                'event_id': envelope.event.event_id,
                'data': message_data,
                'timestamp': envelope.event.timestamp.isoformat()
            }, maxlen=10000)  # Keep last 10k messages

            self.messages_published += 1

        except Exception as e:
            self.errors_count += 1
            raise RuntimeError(f"Failed to publish event: {e}") from e

    async def publish_batch(self, events: List[Union[DomainEvent, EventEnvelope]], topic: Optional[str] = None) -> None:
        """Publish multiple events in batch."""
        if not self.redis:
            raise RuntimeError("Redis client not configured")

        try:
            # Group events by topic for efficient publishing
            topic_events: Dict[str, List[EventEnvelope]] = {}

            for event in events:
                if isinstance(event, DomainEvent):
                    event_topic = topic or self._get_default_topic(event)
                    envelope = EventEnvelope(event=event, topic=event_topic)
                else:
                    envelope = event
                    event_topic = envelope.topic

                if event_topic not in topic_events:
                    topic_events[event_topic] = []
                topic_events[event_topic].append(envelope)

            # Publish to each topic
            for event_topic, envelopes in topic_events.items():
                channel = f"{self.channel_prefix}{event_topic}"
                stream_key = f"stream:{event_topic}"

                # Publish messages
                for envelope in envelopes:
                    message_data = self._serialize_envelope(envelope)
                    await self.redis.publish(channel, message_data)

                    # Add to stream
                    await self.redis.xadd(stream_key, {
                        'event_id': envelope.event.event_id,
                        'data': message_data,
                        'timestamp': envelope.event.timestamp.isoformat()
                    }, maxlen=10000)

            self.messages_published += len(events)

        except Exception as e:
            self.errors_count += 1
            raise RuntimeError(f"Failed to publish batch events: {e}") from e

    async def subscribe(self, topic: str, handler: Callable, **kwargs) -> None:
        """Subscribe to events on a topic."""
        if topic not in self._handlers:
            self._handlers[topic] = []

        self._handlers[topic].append(handler)

        # Start subscriber task if not already running
        if topic not in self._subscriber_tasks or self._subscriber_tasks[topic].done():
            self._subscriber_tasks[topic] = asyncio.create_task(
                self._subscribe_topic(topic, **kwargs)
            )

    async def unsubscribe(self, topic: str, handler: Callable) -> None:
        """Unsubscribe from events on a topic."""
        if topic in self._handlers:
            try:
                self._handlers[topic].remove(handler)
            except ValueError:
                pass  # Handler not found

            # Stop subscriber task if no more handlers
            if not self._handlers[topic] and topic in self._subscriber_tasks:
                self._subscriber_tasks[topic].cancel()
                try:
                    await self._subscriber_tasks[topic]
                except asyncio.CancelledError:
                    pass
                del self._subscriber_tasks[topic]

    async def _subscribe_topic(self, topic: str, **kwargs) -> None:
        """Subscribe to a topic and handle incoming messages."""
        if not self.redis:
            return

        channel = f"{self.channel_prefix}{topic}"
        pubsub = self.redis.pubsub()

        try:
            await pubsub.subscribe(channel)

            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # Deserialize envelope
                        envelope = self._deserialize_envelope(message['data'])

                        # Handle message
                        await self._handle_message(envelope, topic)

                    except Exception as e:
                        self.errors_count += 1
                        print(f"Error handling message on topic {topic}: {e}")

        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel)
            raise
        except Exception as e:
            print(f"Error in topic subscription {topic}: {e}")

    async def _handle_message(self, envelope: EventEnvelope, topic: str) -> None:
        """Handle incoming message."""
        if topic not in self._handlers:
            return

        self.messages_received += 1

        # Call all handlers for this topic
        for handler in self._handlers[topic]:
            try:
                await handler(envelope)
            except Exception as e:
                self.errors_count += 1
                print(f"Error in event handler: {e}")

    async def get_subscriber_count(self, topic: str) -> int:
        """Get number of subscribers for a topic."""
        return len(self._handlers.get(topic, []))

    async def get_topics(self) -> List[str]:
        """Get all available topics."""
        if not self.redis:
            return []

        try:
            # Get all channels with our prefix
            channels = await self.redis.pubsub_channels(f"{self.channel_prefix}*")
            return [ch.decode('utf-8').replace(self.channel_prefix, '') for ch in channels]
        except Exception:
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        try:
            if not self.redis:
                return {
                    'status': 'unhealthy',
                    'error': 'Redis client not configured'
                }

            # Test Redis connection
            await self.redis.ping()

            return {
                'status': 'healthy',
                'redis_connected': True,
                'active_subscriptions': len(self._subscriber_tasks),
                'registered_handlers': sum(len(handlers) for handlers in self._handlers.values()),
                'messages_published': self.messages_published,
                'messages_received': self.messages_received,
                'errors_count': self.errors_count
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'redis_connected': False
            }

    def _get_default_topic(self, event: DomainEvent) -> str:
        """Get default topic for event type."""
        from .event_bus import EventType

        topic_map = {
            EventType.ANALYSIS_STARTED: 'analysis.events',
            EventType.ANALYSIS_COMPLETED: 'analysis.events',
            EventType.ANALYSIS_FAILED: 'analysis.events',
            EventType.DOCUMENT_CREATED: 'document.events',
            EventType.DOCUMENT_UPDATED: 'document.events',
            EventType.DOCUMENT_DELETED: 'document.events',
            EventType.FINDING_CREATED: 'finding.events',
            EventType.FINDING_UPDATED: 'finding.events',
            EventType.WORKFLOW_TRIGGERED: 'workflow.events',
            EventType.NOTIFICATION_SENT: 'notification.events',
            EventType.CACHE_INVALIDATED: 'cache.events',
            EventType.METRICS_UPDATED: 'metrics.events',
            EventType.SYSTEM_HEALTH_CHECK: 'system.events'
        }

        return topic_map.get(event.event_type, 'general.events')

    def _serialize_envelope(self, envelope: EventEnvelope) -> str:
        """Serialize event envelope."""
        if self.serializer:
            return self.serializer.serialize(envelope)
        else:
            # Default JSON serialization
            data = {
                'event': envelope.event.to_dict(),
                'topic': envelope.topic,
                'partition_key': envelope.partition_key,
                'headers': envelope.headers,
                'retry_count': envelope.retry_count,
                'max_retries': envelope.max_retries
            }
            return json.dumps(data, default=str)

    def _deserialize_envelope(self, data: str) -> EventEnvelope:
        """Deserialize event envelope."""
        if self.serializer:
            return self.serializer.deserialize(data)
        else:
            # Default JSON deserialization
            parsed = json.loads(data)

            # Reconstruct event
            event_data = parsed['event']
            event = DomainEvent.from_dict(event_data)

            return EventEnvelope(
                event=event,
                topic=parsed['topic'],
                partition_key=parsed.get('partition_key'),
                headers=parsed.get('headers', {}),
                retry_count=parsed.get('retry_count', 0),
                max_retries=parsed.get('max_retries', 3)
            )


class RedisEventPublisher(EventPublisher):
    """Redis-based event publisher."""

    def __init__(self, redis_client=None, **kwargs):
        """Initialize Redis event publisher."""
        event_bus = RedisEventBus(redis_client, **kwargs)
        super().__init__(event_bus)


class RedisEventSubscriber(EventSubscriber):
    """Redis-based event subscriber."""

    def __init__(self, redis_client=None, **kwargs):
        """Initialize Redis event subscriber."""
        event_bus = RedisEventBus(redis_client, **kwargs)
        super().__init__(event_bus)


class RedisStreamEventBus(EventBus):
    """Redis Streams-based event bus for guaranteed delivery."""

    def __init__(
        self,
        redis_client=None,
        stream_prefix: str = "event_stream:",
        consumer_group: str = "analysis_service",
        consumer_name: Optional[str] = None,
        batch_size: int = 10,
        block_timeout: int = 5000  # milliseconds
    ):
        """Initialize Redis Streams event bus."""
        self.redis = redis_client
        self.stream_prefix = stream_prefix
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name or f"consumer_{threading.current_thread().ident}"
        self.batch_size = batch_size
        self.block_timeout = block_timeout

        self._handlers: Dict[str, List[Callable]] = {}
        self._subscriber_tasks: Dict[str, asyncio.Task] = {}

        # Statistics
        self.messages_published = 0
        self.messages_processed = 0
        self.errors_count = 0

    async def publish(self, event: Union[DomainEvent, EventEnvelope], topic: Optional[str] = None) -> None:
        """Publish event to Redis Stream."""
        if not self.redis:
            raise RuntimeError("Redis client not configured")

        try:
            # Convert to envelope if needed
            if isinstance(event, DomainEvent):
                if topic is None:
                    topic = self._get_default_topic(event)
                envelope = EventEnvelope(event=event, topic=topic)
            else:
                envelope = event

            # Add to stream
            stream_key = f"{self.stream_prefix}{envelope.topic}"
            message_data = self._serialize_envelope(envelope)

            await self.redis.xadd(stream_key, {
                'event_id': envelope.event.event_id,
                'data': message_data,
                'timestamp': envelope.event.timestamp.isoformat()
            })

            self.messages_published += 1

        except Exception as e:
            self.errors_count += 1
            raise RuntimeError(f"Failed to publish event to stream: {e}") from e

    async def publish_batch(self, events: List[Union[DomainEvent, EventEnvelope]], topic: Optional[str] = None) -> None:
        """Publish multiple events to Redis Stream."""
        if not self.redis:
            raise RuntimeError("Redis client not configured")

        try:
            # Group by topic
            topic_events: Dict[str, List[EventEnvelope]] = {}

            for event in events:
                if isinstance(event, DomainEvent):
                    event_topic = topic or self._get_default_topic(event)
                    envelope = EventEnvelope(event=event, topic=event_topic)
                else:
                    envelope = event
                    event_topic = envelope.topic

                if event_topic not in topic_events:
                    topic_events[event_topic] = []
                topic_events[event_topic].append(envelope)

            # Publish to each stream
            for event_topic, envelopes in topic_events.items():
                stream_key = f"{self.stream_prefix}{event_topic}"

                for envelope in envelopes:
                    message_data = self._serialize_envelope(envelope)
                    await self.redis.xadd(stream_key, {
                        'event_id': envelope.event.event_id,
                        'data': message_data,
                        'timestamp': envelope.event.timestamp.isoformat()
                    })

            self.messages_published += len(events)

        except Exception as e:
            self.errors_count += 1
            raise RuntimeError(f"Failed to publish batch events to stream: {e}") from e

    async def subscribe(self, topic: str, handler: Callable, **kwargs) -> None:
        """Subscribe to Redis Stream."""
        if topic not in self._handlers:
            self._handlers[topic] = []

        self._handlers[topic].append(handler)

        # Start consumer task if not already running
        if topic not in self._subscriber_tasks or self._subscriber_tasks[topic].done():
            self._subscriber_tasks[topic] = asyncio.create_task(
                self._consume_stream(topic, **kwargs)
            )

    async def unsubscribe(self, topic: str, handler: Callable) -> None:
        """Unsubscribe from Redis Stream."""
        if topic in self._handlers:
            try:
                self._handlers[topic].remove(handler)
            except ValueError:
                pass

            if not self._handlers[topic] and topic in self._subscriber_tasks:
                self._subscriber_tasks[topic].cancel()
                try:
                    await self._subscriber_tasks[topic]
                except asyncio.CancelledError:
                    pass
                del self._subscriber_tasks[topic]

    async def _consume_stream(self, topic: str, **kwargs) -> None:
        """Consume messages from Redis Stream."""
        if not self.redis:
            return

        stream_key = f"{self.stream_prefix}{topic}"

        try:
            # Create consumer group if it doesn't exist
            try:
                await self.redis.xgroup_create(
                    stream_key,
                    self.consumer_group,
                    '$',
                    mkstream=True
                )
            except Exception:
                # Group might already exist
                pass

            last_id = '0'  # Start from beginning for new consumers

            while True:
                try:
                    # Read from stream
                    messages = await self.redis.xreadgroup(
                        self.consumer_group,
                        self.consumer_name,
                        {stream_key: last_id},
                        count=self.batch_size,
                        block=self.block_timeout
                    )

                    if not messages:
                        continue

                    for stream_name, message_list in messages:
                        for message_id, message_data in message_list:
                            try:
                                # Deserialize envelope
                                envelope = self._deserialize_envelope(message_data['data'])

                                # Handle message
                                await self._handle_message(envelope, topic)

                                # Acknowledge message
                                await self.redis.xack(stream_key, self.consumer_group, message_id)

                                last_id = message_id

                            except Exception as e:
                                self.errors_count += 1
                                print(f"Error processing stream message {message_id}: {e}")

                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"Error in stream consumption for {topic}: {e}")
                    await asyncio.sleep(1)  # Back off on errors

        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"Fatal error in stream consumer for {topic}: {e}")

    async def _handle_message(self, envelope: EventEnvelope, topic: str) -> None:
        """Handle incoming message."""
        if topic not in self._handlers:
            return

        self.messages_processed += 1

        # Call all handlers
        for handler in self._handlers[topic]:
            try:
                await handler(envelope)
            except Exception as e:
                self.errors_count += 1
                print(f"Error in stream event handler: {e}")

    async def get_subscriber_count(self, topic: str) -> int:
        """Get number of subscribers."""
        return len(self._handlers.get(topic, []))

    async def get_topics(self) -> List[str]:
        """Get all available topics."""
        if not self.redis:
            return []

        try:
            # Get all stream keys
            keys = await self.redis.keys(f"{self.stream_prefix}*")
            return [key.decode('utf-8').replace(self.stream_prefix, '') for key in keys]
        except Exception:
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        try:
            if not self.redis:
                return {
                    'status': 'unhealthy',
                    'error': 'Redis client not configured'
                }

            # Test Redis connection
            await self.redis.ping()

            return {
                'status': 'healthy',
                'redis_connected': True,
                'active_consumers': len(self._subscriber_tasks),
                'registered_handlers': sum(len(handlers) for handlers in self._handlers.values()),
                'messages_published': self.messages_published,
                'messages_processed': self.messages_processed,
                'errors_count': self.errors_count,
                'consumer_group': self.consumer_group,
                'consumer_name': self.consumer_name
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'redis_connected': False
            }

    def _get_default_topic(self, event: DomainEvent) -> str:
        """Get default topic for event type."""
        from .event_bus import EventType

        topic_map = {
            EventType.ANALYSIS_STARTED: 'analysis.events',
            EventType.ANALYSIS_COMPLETED: 'analysis.events',
            EventType.ANALYSIS_FAILED: 'analysis.events',
            EventType.DOCUMENT_CREATED: 'document.events',
            EventType.DOCUMENT_UPDATED: 'document.events',
            EventType.DOCUMENT_DELETED: 'document.events',
            EventType.FINDING_CREATED: 'finding.events',
            EventType.FINDING_UPDATED: 'finding.events',
            EventType.WORKFLOW_TRIGGERED: 'workflow.events',
            EventType.NOTIFICATION_SENT: 'notification.events',
            EventType.CACHE_INVALIDATED: 'cache.events',
            EventType.METRICS_UPDATED: 'metrics.events',
            EventType.SYSTEM_HEALTH_CHECK: 'system.events'
        }

        return topic_map.get(event.event_type, 'general.events')

    def _serialize_envelope(self, envelope: EventEnvelope) -> str:
        """Serialize event envelope."""
        data = {
            'event': envelope.event.to_dict(),
            'topic': envelope.topic,
            'partition_key': envelope.partition_key,
            'headers': envelope.headers,
            'retry_count': envelope.retry_count,
            'max_retries': envelope.max_retries
        }
        return json.dumps(data, default=str)

    def _deserialize_envelope(self, data: str) -> EventEnvelope:
        """Deserialize event envelope."""
        parsed = json.loads(data)

        # Reconstruct event
        event_data = parsed['event']
        event = DomainEvent.from_dict(event_data)

        return EventEnvelope(
            event=event,
            topic=parsed['topic'],
            partition_key=parsed.get('partition_key'),
            headers=parsed.get('headers', {}),
            retry_count=parsed.get('retry_count', 0),
            max_retries=parsed.get('max_retries', 3)
        )
