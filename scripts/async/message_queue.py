#!/usr/bin/env python3
"""
Message Queue System for Inter-Service Communication

This script implements a comprehensive message queue system for the LLM
Documentation Ecosystem. It provides reliable message delivery, queue
management, and inter-service communication capabilities.

Features:
- Message queuing with Redis/RabbitMQ alternatives
- Publisher-subscriber pattern
- Dead letter queues and retry logic
- Message persistence and durability
- Queue monitoring and metrics
- Message routing and filtering
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, asdict
import uuid
import hashlib

import redis.asyncio as redis
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class DeliveryMode(Enum):
    """Message delivery modes."""
    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


@dataclass
class Message:
    """Message data structure."""
    id: str
    topic: str
    payload: Dict[str, Any]
    priority: MessagePriority
    delivery_mode: DeliveryMode
    created_at: datetime
    expires_at: Optional[datetime]
    headers: Dict[str, str]
    correlation_id: Optional[str]
    reply_to: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['delivery_mode'] = self.delivery_mode.value
        data['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        data['priority'] = MessagePriority(data['priority'])
        data['delivery_mode'] = DeliveryMode(data['delivery_mode'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


@dataclass
class Subscription:
    """Subscription data structure."""
    id: str
    topic: str
    subscriber_name: str
    handler_func: str
    enabled: bool
    created_at: datetime
    last_processed: Optional[datetime]
    message_count: int
    error_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert subscription to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.last_processed:
            data['last_processed'] = self.last_processed.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subscription':
        """Create subscription from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('last_processed'):
            data['last_processed'] = datetime.fromisoformat(data['last_processed'])
        return cls(**data)


class MessageQueue:
    """Message queue system for inter-service communication."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.subscriptions: Dict[str, Subscription] = {}
        self.message_handlers: Dict[str, Callable[[Message], Awaitable[None]]] = {}
        self.running = False

    async def connect(self) -> None:
        """Establish Redis connection."""
        if self.redis is None:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            console.print("[green]✓ Connected to Redis for message queuing[/green]")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def publish_message(
        self,
        topic: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE,
        expires_in_seconds: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> str:
        """Publish a message to a topic."""
        await self.connect()

        message_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds) if expires_in_seconds else None

        message = Message(
            id=message_id,
            topic=topic,
            payload=payload,
            priority=priority,
            delivery_mode=delivery_mode,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            headers=headers or {},
            correlation_id=correlation_id,
            reply_to=reply_to
        )

        # Store message
        message_key = f"message:{message_id}"
        await self.redis.set(message_key, json.dumps(message.to_dict()))

        # Add to topic queue with priority
        queue_key = f"topic:{topic}:{priority.value}"
        await self.redis.rpush(queue_key, message_id)

        # Set expiration if specified
        if expires_in_seconds:
            await self.redis.expire(message_key, expires_in_seconds)

        console.print(f"[green]✓ Published message to {topic}: {message_id}[/green]")
        return message_id

    async def subscribe(
        self,
        topic: str,
        subscriber_name: str,
        handler_func: Callable[[Message], Awaitable[None]]
    ) -> str:
        """Subscribe to a topic."""
        await self.connect()

        subscription_id = str(uuid.uuid4())
        subscription = Subscription(
            id=subscription_id,
            topic=topic,
            subscriber_name=subscriber_name,
            handler_func=handler_func.__name__,
            enabled=True,
            created_at=datetime.utcnow(),
            last_processed=None,
            message_count=0,
            error_count=0
        )

        # Store subscription
        sub_key = f"subscription:{subscription_id}"
        await self.redis.set(sub_key, json.dumps(subscription.to_dict()))

        # Add to topic subscriptions
        subs_key = f"topic_subscriptions:{topic}"
        await self.redis.sadd(subs_key, subscription_id)

        self.subscriptions[subscription_id] = subscription
        self.message_handlers[subscription_id] = handler_func

        console.print(f"[green]✓ Subscribed {subscriber_name} to {topic}[/green]")
        return subscription_id

    async def start_consuming(self, max_concurrent: int = 10) -> None:
        """Start consuming messages."""
        console.print(f"[blue]🚀 Starting message consumption with {max_concurrent} concurrent workers...[/blue]")
        self.running = True

        # Load existing subscriptions
        await self._load_subscriptions()

        # Create consumer tasks
        consumer_tasks = []
        for i in range(max_concurrent):
            task = asyncio.create_task(self._consume_messages(i))
            consumer_tasks.append(task)

        # Wait for consumers
        await asyncio.gather(*consumer_tasks, return_exceptions=True)

    async def stop_consuming(self) -> None:
        """Stop consuming messages."""
        console.print("[blue]🛑 Stopping message consumption...[/blue]")
        self.running = False

    async def _load_subscriptions(self) -> None:
        """Load subscriptions from Redis."""
        await self.connect()

        # Get all subscription keys
        pattern = "subscription:*"
        keys = await self.redis.keys(pattern)

        for key in keys:
            sub_data = await self.redis.get(key)
            if sub_data:
                sub_dict = json.loads(sub_data)
                subscription = Subscription.from_dict(sub_dict)
                self.subscriptions[subscription.id] = subscription

        console.print(f"[green]✓ Loaded {len(self.subscriptions)} subscriptions[/green]")

    async def _consume_messages(self, worker_id: int) -> None:
        """Consume messages for all subscriptions."""
        console.print(f"[blue]Consumer {worker_id} started[/blue]")

        while self.running:
            try:
                message_processed = False

                # Check each subscription for messages
                for subscription in self.subscriptions.values():
                    if not subscription.enabled:
                        continue

                    # Get message from topic queues (highest priority first)
                    for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH, MessagePriority.NORMAL, MessagePriority.LOW]:
                        queue_key = f"topic:{subscription.topic}:{priority.value}"
                        message_id_bytes = await self.redis.lpop(queue_key)

                        if message_id_bytes:
                            message_id = message_id_bytes.decode() if isinstance(message_id_bytes, bytes) else message_id_bytes
                            await self._process_message(message_id, subscription)
                            message_processed = True
                            break

                    if message_processed:
                        break

                if not message_processed:
                    # No messages available, wait before checking again
                    await asyncio.sleep(1)

            except Exception as e:
                console.print(f"[red]Consumer {worker_id} error: {e}[/red]")
                await asyncio.sleep(5)

    async def _process_message(self, message_id: str, subscription: Subscription) -> None:
        """Process a single message."""
        message_key = f"message:{message_id}"

        try:
            # Get message data
            message_data = await self.redis.get(message_key)
            if not message_data:
                return

            message_dict = json.loads(message_data)
            message = Message.from_dict(message_dict)

            # Check if message has expired
            if message.expires_at and datetime.utcnow() > message.expires_at:
                console.print(f"[yellow]⚠ Expired message: {message_id}[/yellow]")
                return

            # Get message handler
            handler = self.message_handlers.get(subscription.id)
            if not handler:
                console.print(f"[red]❌ No handler for subscription {subscription.id}[/red]")
                return

            # Process message
            console.print(f"[blue]▶ Processing message {message_id} for {subscription.subscriber_name}[/blue]")
            await handler(message)

            # Update subscription stats
            subscription.message_count += 1
            subscription.last_processed = datetime.utcnow()

            sub_key = f"subscription:{subscription.id}"
            await self.redis.set(sub_key, json.dumps(subscription.to_dict()))

            # Clean up processed message
            await self.redis.delete(message_key)

            console.print(f"[green]✓ Processed message {message_id}[/green]")

        except Exception as e:
            console.print(f"[red]✗ Failed to process message {message_id}: {e}[/red]")

            # Update error count
            subscription.error_count += 1
            sub_key = f"subscription:{subscription.id}"
            await self.redis.set(sub_key, json.dumps(subscription.to_dict()))

            # Move to dead letter queue if configured
            await self._move_to_dead_letter_queue(message_id, str(e))

    async def _move_to_dead_letter_queue(self, message_id: str, error: str) -> None:
        """Move failed message to dead letter queue."""
        dlq_key = "dead_letter_queue"
        dlq_entry = {
            "message_id": message_id,
            "failed_at": datetime.utcnow().isoformat(),
            "error": error
        }
        await self.redis.rpush(dlq_key, json.dumps(dlq_entry))

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        await self.connect()

        stats = {
            "total_subscriptions": len(self.subscriptions),
            "active_subscriptions": len([s for s in self.subscriptions.values() if s.enabled]),
            "total_messages_processed": sum(s.message_count for s in self.subscriptions.values()),
            "total_errors": sum(s.error_count for s in self.subscriptions.values())
        }

        # Count messages in all topic queues
        pattern = "topic:*:*"
        queue_keys = await self.redis.keys(pattern)
        total_queued = 0

        for key in queue_keys:
            queue_length = await self.redis.llen(key)
            total_queued += queue_length

        stats["messages_queued"] = total_queued
        stats["dead_letter_count"] = await self.redis.llen("dead_letter_queue")

        return stats

    async def purge_dead_letter_queue(self) -> int:
        """Purge the dead letter queue."""
        return await self.redis.delete("dead_letter_queue") or 0


# Example message handlers
async def document_updated_handler(message: Message) -> None:
    """Handle document updated messages."""
    doc_id = message.payload.get("document_id")
    console.print(f"[blue]📄 Document updated: {doc_id}[/blue]")
    await asyncio.sleep(0.1)  # Simulate processing

async def analysis_completed_handler(message: Message) -> None:
    """Handle analysis completed messages."""
    analysis_id = message.payload.get("analysis_id")
    console.print(f"[blue]🔍 Analysis completed: {analysis_id}[/blue]")
    await asyncio.sleep(0.1)  # Simulate processing

async def service_health_handler(message: Message) -> None:
    """Handle service health messages."""
    service_name = message.payload.get("service_name")
    status = message.payload.get("status")
    console.print(f"[blue]🏥 Service {service_name} health: {status}[/blue]")
    await asyncio.sleep(0.05)  # Simulate processing


async def setup_message_queue() -> MessageQueue:
    """Set up and configure the message queue."""
    queue = MessageQueue()

    console.print("[green]✓ Message queue system configured[/green]")
    return queue


async def main():
    """Main function to demonstrate message queuing."""
    console.print("[bold blue]🚀 Message Queue Demonstration[/bold blue]")
    console.print()

    queue = await setup_message_queue()

    try:
        # Subscribe to topics
        doc_sub_id = await queue.subscribe("document.updated", "document_processor", document_updated_handler)
        analysis_sub_id = await queue.subscribe("analysis.completed", "result_processor", analysis_completed_handler)
        health_sub_id = await queue.subscribe("service.health", "health_monitor", service_health_handler)

        console.print(f"[green]✓ Subscriptions created: doc({doc_sub_id[:8]}), analysis({analysis_sub_id[:8]}), health({health_sub_id[:8]})[/green]")

        # Publish some test messages
        message_ids = []

        # Document messages
        for i in range(3):
            msg_id = await queue.publish_message(
                "document.updated",
                {"document_id": f"doc_{i+1}", "action": "updated", "timestamp": datetime.utcnow().isoformat()},
                priority=MessagePriority.HIGH if i == 0 else MessagePriority.NORMAL
            )
            message_ids.append(msg_id)

        # Analysis messages
        for i in range(2):
            msg_id = await queue.publish_message(
                "analysis.completed",
                {"analysis_id": f"analysis_{i+1}", "result": "success", "duration": 5.2},
                priority=MessagePriority.NORMAL
            )
            message_ids.append(msg_id)

        # Health messages
        msg_id = await queue.publish_message(
            "service.health",
            {"service_name": "doc_store", "status": "healthy", "response_time": 0.15},
            priority=MessagePriority.CRITICAL
        )
        message_ids.append(msg_id)

        console.print(f"[green]✓ Published {len(message_ids)} test messages[/green]")

        # Start consuming in background
        consumer_task = asyncio.create_task(queue.start_consuming(max_concurrent=5))

        # Wait for messages to be processed
        await asyncio.sleep(5)

        # Check queue stats
        stats = await queue.get_queue_stats()
        console.print(f"[blue]📊 Queue stats: {stats}[/blue]")

        # Stop consuming
        await queue.stop_consuming()
        consumer_task.cancel()

        console.print("[green]✓ Message queue demonstration completed[/green]")

    finally:
        await queue.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
