"""Event Streaming Service Domain Service"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from ..value_objects.event_status import EventStatus


class EventEntry:
    """Represents an event in the streaming system."""

    def __init__(
        self,
        event_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.event_data = event_data
        self.correlation_id = correlation_id
        self.timestamp = timestamp or datetime.utcnow()
        self.status = EventStatus.PENDING


class EventStreamingService:
    """Domain service for managing event streaming and history."""

    def __init__(self):
        """Initialize event streaming service."""
        self._events: List[EventEntry] = []
        self._event_index: Dict[str, int] = {}  # event_id -> index in _events

    def publish_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        event_id: Optional[str] = None
    ) -> str:
        """Publish an event to the stream."""
        if event_id is None:
            import uuid
            event_id = str(uuid.uuid4())

        event = EventEntry(
            event_id=event_id,
            event_type=event_type,
            event_data=event_data,
            correlation_id=correlation_id
        )

        self._events.append(event)
        self._event_index[event_id] = len(self._events) - 1

        return event_id

    def get_event_history(
        self,
        correlation_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get event history with optional filtering."""
        filtered_events = self._events.copy()

        # Apply filters
        if correlation_id:
            filtered_events = [e for e in filtered_events if e.correlation_id == correlation_id]

        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]

        # Sort by timestamp (newest first)
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        total_count = len(filtered_events)
        start_idx = offset
        end_idx = start_idx + limit
        paginated_events = filtered_events[start_idx:end_idx]

        return {
            "events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "event_data": e.event_data,
                    "correlation_id": e.correlation_id,
                    "timestamp": e.timestamp.isoformat(),
                    "status": e.status.value
                }
                for e in paginated_events
            ],
            "total": total_count,
            "filtered": total_count,
            "limit": limit,
            "offset": offset
        }

    def replay_events(
        self,
        event_types: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Replay events based on filters."""
        filtered_events = self._events.copy()

        # Apply filters
        if correlation_id:
            filtered_events = [e for e in filtered_events if e.correlation_id == correlation_id]

        if event_types:
            filtered_events = [e for e in filtered_events if e.event_type in event_types]

        # Limit the results
        replay_events = filtered_events[:limit]

        # Mark events as being replayed
        replayed_ids = []
        for event in replay_events:
            # In a real implementation, this would re-publish the events
            replayed_ids.append(event.event_id)

        return {
            "status": "replay_started",
            "events_processed": len(replayed_ids),
            "event_types": event_types,
            "correlation_id": correlation_id,
            "limit": limit
        }

    def clear_events(
        self,
        event_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        before_timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Clear events based on filters."""
        if before_timestamp is None:
            before_timestamp = datetime.utcnow()

        events_to_remove = []

        for i, event in enumerate(self._events):
            should_remove = True

            if event.timestamp >= before_timestamp:
                should_remove = False

            if event_type and event.event_type != event_type:
                should_remove = False

            if correlation_id and event.correlation_id != correlation_id:
                should_remove = False

            if should_remove:
                events_to_remove.append(i)

        # Remove events in reverse order to maintain indices
        events_to_remove.reverse()
        removed_count = 0

        for index in events_to_remove:
            event = self._events[index]
            del self._event_index[event.event_id]
            del self._events[index]
            removed_count += 1

            # Update indices for remaining events
            for eid, idx in self._event_index.items():
                if idx > index:
                    self._event_index[eid] = idx - 1

        return {
            "cleared_count": removed_count,
            "event_type": event_type,
            "correlation_id": correlation_id,
            "before_timestamp": before_timestamp.isoformat()
        }

    def get_event_stats(self) -> Dict[str, Any]:
        """Get event streaming statistics."""
        if not self._events:
            return {
                "total_events": 0,
                "events_by_type": {},
                "oldest_event": None,
                "newest_event": None,
                "avg_events_per_minute": 0
            }

        # Calculate statistics
        events_by_type = {}
        timestamps = []

        for event in self._events:
            events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1
            timestamps.append(event.timestamp)

        sorted_timestamps = sorted(timestamps)
        oldest_event = sorted_timestamps[0]
        newest_event = sorted_timestamps[-1]

        # Calculate average events per minute (rough estimate)
        if len(timestamps) > 1:
            time_span_minutes = (newest_event - oldest_event).total_seconds() / 60
            avg_events_per_minute = len(timestamps) / time_span_minutes if time_span_minutes > 0 else 0
        else:
            avg_events_per_minute = 0

        return {
            "total_events": len(self._events),
            "events_by_type": events_by_type,
            "oldest_event": oldest_event.isoformat(),
            "newest_event": newest_event.isoformat(),
            "avg_events_per_minute": round(avg_events_per_minute, 2)
        }

    def cleanup_old_events(self, max_age_hours: int = 24) -> int:
        """Clean up events older than specified hours. Returns count removed."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        return self.clear_events(before_timestamp=cutoff_time)["cleared_count"]
