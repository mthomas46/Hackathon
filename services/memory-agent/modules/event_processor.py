"""Event processing for Memory Agent service.

Handles Redis pub/sub event subscription and processing.
"""
import json
from typing import Dict, Any, List
import asyncio

try:
    import redis.asyncio as aioredis  # type: ignore
except Exception:
    aioredis = None

from .shared_utils import (
    get_memory_max_items,
    get_memory_ttl_seconds,
    create_memory_item,
    extract_endpoint_from_text
)
from .memory_state import _memory


class EventProcessor:
    """Handles Redis event subscription and processing."""

    def __init__(self):
        self.endpoint_index: Dict[str, int] = {}
        self.redis_url = None
        self.client = None
        self.pubsub = None

    async def initialize_redis(self):
        """Initialize Redis connection."""
        if not aioredis:
            return False

        try:
            from .shared_utils import get_redis_url
            self.redis_url = get_redis_url()
            self.client = aioredis.from_url(self.redis_url)
            self.pubsub = self.client.pubsub()
            return True
        except Exception:
            return False

    async def subscribe_to_channels(self):
        """Subscribe to Redis channels for memory context collection."""
        if not self.pubsub:
            return

        # Subscribe to key ecosystem topics for memory context
        await self.pubsub.subscribe(
            "ingestion.requested",
            "docs.ingested.github",
            "docs.ingested.jira",
            "docs.ingested.confluence",
            "apis.ingested.swagger",
            "findings.created",
        )

    async def process_events(self):
        """Process incoming Redis events."""
        if not self.pubsub:
            return

        try:
            async for message in self.pubsub.listen():
                if message.get("type") != "message":
                    continue

                channel = message.get("channel", b"").decode()
                data = message.get("data")

                try:
                    payload = json.loads(data) if isinstance(data, (bytes, str)) else {"raw": str(data)}
                except Exception:
                    payload = {"raw": str(data)}

                # Create memory item from event
                memory_item = await self._create_memory_item_from_event(channel, payload)
                _memory.append(memory_item)

                # Maintain memory size limits
                max_items = get_memory_max_items()
                if len(_memory) > max_items:
                    del _memory[: len(_memory) - max_items]

                # Update endpoint index from document events
                if channel.startswith("docs.ingested"):
                    self._update_endpoint_index_from_payload(payload)

        finally:
            if self.pubsub:
                await self.pubsub.close()
            if self.client:
                await self.client.aclose()

    async def _create_memory_item_from_event(self, channel: str, payload: Dict[str, Any]):
        """Create a memory item from a Redis event."""
        # Determine memory item type and summary
        if channel == "ingestion.requested":
            kind = "operation"
            summary = f"{channel} event received"
        elif channel.startswith("docs.ingested"):
            kind = "doc_summary"
            summary = f"Document ingested from {channel.split('.')[-1]}"
        elif channel == "apis.ingested.swagger":
            kind = "api_summary"
            summary = "API specification ingested"
        elif channel == "findings.created":
            kind = "finding"
            cnt = payload.get("count", 0)
            sev = payload.get("severity_counts", {})
            summary = f"findings.created: {cnt} findings (severity: {sev})"
        else:
            kind = "event"
            summary = f"{channel} event received"

        # Create memory item
        return create_memory_item(
            key=payload.get("correlation_id") or f"{channel}:{len(_memory) + 1}",
            value={"channel": channel, "payload": payload},
            item_type=kind,
            ttl_seconds=get_memory_ttl_seconds(),
            metadata={
                "source": "redis_event",
                "channel": channel,
                "summary": summary
            }
        )

    def _update_endpoint_index_from_payload(self, payload: Dict[str, Any]) -> None:
        """Update endpoint index from document payload."""
        if not isinstance(payload, dict):
            return

        doc_payload = payload.get("document") or {}
        text = doc_payload.get("content") or doc_payload.get("title") or ""

        endpoints = extract_endpoint_from_text(text)
        for endpoint in endpoints:
            self.endpoint_index[endpoint] = self.endpoint_index.get(endpoint, 0) + 1

    def get_endpoint_index(self) -> Dict[str, int]:
        """Get the current endpoint index."""
        return self.endpoint_index.copy()


# Create singleton instance
event_processor = EventProcessor()
