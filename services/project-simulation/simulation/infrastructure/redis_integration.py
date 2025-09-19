"""Redis pub/sub integration for real-time communication between simulation services.

This module provides Redis-based publish/subscribe functionality for:
- Real-time simulation progress updates
- Document generation notifications
- Cross-service event broadcasting
- Service health monitoring
"""

import json
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import redis.asyncio as redis
from dataclasses import dataclass

from .logging import SimulationLogger


@dataclass
class RedisConfig:
    """Configuration for Redis connection."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True


class RedisPubSubManager:
    """Manages Redis pub/sub connections and message handling."""

    def __init__(self, config: RedisConfig, logger: SimulationLogger):
        self.config = config
        self.logger = logger
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.is_connected = False

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                decode_responses=self.config.decode_responses
            )

            # Test connection
            await self.redis_client.ping()
            self.is_connected = True

            self.logger.info("Connected to Redis successfully")

        except Exception as e:
            self.logger.error("Failed to connect to Redis", error=str(e))
            self.is_connected = False
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            self.logger.info("Disconnected from Redis")

    async def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a Redis channel."""
        if not self.is_connected:
            self.logger.warning("Cannot publish - Redis not connected")
            return False

        try:
            # Add metadata to message
            enriched_message = {
                **message,
                "timestamp": datetime.now().isoformat(),
                "publisher": "simulation-service"
            }

            # Publish to Redis
            await self.redis_client.publish(channel, json.dumps(enriched_message))

            self.logger.debug(
                "Published message to Redis channel",
                channel=channel,
                message_type=message.get("type", "unknown")
            )

            return True

        except Exception as e:
            self.logger.error("Failed to publish message to Redis", error=str(e), channel=channel)
            return False

    async def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to a Redis channel with a callback function."""
        if not self.is_connected:
            self.logger.warning("Cannot subscribe - Redis not connected")
            return

        try:
            if channel not in self.subscribers:
                self.subscribers[channel] = []

            self.subscribers[channel].append(callback)

            # Subscribe to channel
            if not self.pubsub:
                self.pubsub = self.redis_client.pubsub()

            await self.pubsub.subscribe(channel)

            self.logger.info("Subscribed to Redis channel", channel=channel)

        except Exception as e:
            self.logger.error("Failed to subscribe to Redis channel", error=str(e), channel=channel)

    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a Redis channel."""
        if self.pubsub and channel in self.subscribers:
            await self.pubsub.unsubscribe(channel)
            del self.subscribers[channel]
            self.logger.info("Unsubscribed from Redis channel", channel=channel)

    async def start_listening(self) -> None:
        """Start listening for messages on subscribed channels."""
        if not self.pubsub:
            return

        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data = json.loads(message["data"])

                    # Call all subscribers for this channel
                    if channel in self.subscribers:
                        for callback in self.subscribers[channel]:
                            try:
                                await callback(data)
                            except Exception as e:
                                self.logger.error(
                                    "Error in Redis message callback",
                                    error=str(e),
                                    channel=channel
                                )

        except Exception as e:
            self.logger.error("Error in Redis message listening", error=str(e))


class SimulationRedisClient:
    """High-level client for simulation-related Redis operations."""

    def __init__(self, redis_manager: RedisPubSubManager, logger: SimulationLogger):
        self.redis_manager = redis_manager
        self.logger = logger

    async def publish_simulation_event(self, simulation_id: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Publish a simulation event to Redis."""
        channel = f"simulation:{simulation_id}"
        message = {
            "type": event_type,
            "simulation_id": simulation_id,
            **event_data
        }

        return await self.redis_manager.publish(channel, message)

    async def publish_document_generated(self, simulation_id: str, document_id: str, document_type: str) -> bool:
        """Publish document generation event."""
        channel = "documents:generated"
        message = {
            "type": "document_generated",
            "simulation_id": simulation_id,
            "document_id": document_id,
            "document_type": document_type
        }

        return await self.redis_manager.publish(channel, message)

    async def publish_prompt_used(self, simulation_id: str, prompt_id: str, prompt_type: str) -> bool:
        """Publish prompt usage event."""
        channel = "prompts:used"
        message = {
            "type": "prompt_used",
            "simulation_id": simulation_id,
            "prompt_id": prompt_id,
            "prompt_type": prompt_type
        }

        return await self.redis_manager.publish(channel, message)

    async def subscribe_to_simulation_events(self, simulation_id: str, callback: Callable) -> None:
        """Subscribe to events for a specific simulation."""
        channel = f"simulation:{simulation_id}"
        await self.redis_manager.subscribe(channel, callback)

    async def subscribe_to_document_events(self, callback: Callable) -> None:
        """Subscribe to document generation events."""
        await self.redis_manager.subscribe("documents:generated", callback)

    async def subscribe_to_prompt_events(self, callback: Callable) -> None:
        """Subscribe to prompt usage events."""
        await self.redis_manager.subscribe("prompts:used", callback)


# Global instances
_redis_config = None
_redis_manager = None
_simulation_redis_client = None


async def initialize_redis_integration(logger: SimulationLogger, config: Optional[RedisConfig] = None) -> SimulationRedisClient:
    """Initialize Redis integration with default configuration."""
    global _redis_config, _redis_manager, _simulation_redis_client

    if config is None:
        config = RedisConfig()

    _redis_config = config
    _redis_manager = RedisPubSubManager(config, logger)
    _simulation_redis_client = SimulationRedisClient(_redis_manager, logger)

    # Attempt to connect
    try:
        await _redis_manager.connect()

        # Start listening for messages in background
        asyncio.create_task(_redis_manager.start_listening())

        logger.info("Redis integration initialized successfully")
    except Exception as e:
        logger.warning("Redis connection failed, continuing without Redis", error=str(e))

    return _simulation_redis_client


async def get_simulation_redis_client() -> Optional[SimulationRedisClient]:
    """Get the global simulation Redis client instance."""
    return _simulation_redis_client


async def publish_simulation_update(simulation_id: str, update_type: str, update_data: Dict[str, Any]) -> bool:
    """Convenience function to publish simulation updates."""
    client = await get_simulation_redis_client()
    if client:
        return await client.publish_simulation_event(simulation_id, update_type, update_data)
    return False


async def publish_document_event(simulation_id: str, document_id: str, document_type: str) -> bool:
    """Convenience function to publish document generation events."""
    client = await get_simulation_redis_client()
    if client:
        return await client.publish_document_generated(simulation_id, document_id, document_type)
    return False


async def publish_prompt_event(simulation_id: str, prompt_id: str, prompt_type: str) -> bool:
    """Convenience function to publish prompt usage events."""
    client = await get_simulation_redis_client()
    if client:
        return await client.publish_prompt_used(simulation_id, prompt_id, prompt_type)
    return False
