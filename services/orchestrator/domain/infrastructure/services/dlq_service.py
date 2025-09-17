"""DLQ Service Domain Service"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..value_objects.dlq_event import DLQEvent


class DLQService:
    """Domain service for managing Dead Letter Queue operations."""

    def __init__(self):
        """Initialize DLQ service."""
        self._dlq_events: Dict[str, DLQEvent] = {}

    def add_to_dlq(
        self,
        event_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        failure_reason: str,
        correlation_id: Optional[str] = None,
        service_name: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> DLQEvent:
        """Add an event to the DLQ."""
        dlq_event = DLQEvent(
            event_id=event_id,
            event_type=event_type,
            event_data=event_data,
            failure_reason=failure_reason,
            original_timestamp=datetime.utcnow(),  # Could be passed in
            correlation_id=correlation_id,
            service_name=service_name,
            error_details=error_details
        )

        self._dlq_events[dlq_event.dlq_id] = dlq_event
        return dlq_event

    def get_dlq_event(self, dlq_id: str) -> Optional[DLQEvent]:
        """Get a DLQ event by its DLQ ID."""
        return self._dlq_events.get(dlq_id)

    def get_event_by_original_id(self, event_id: str) -> Optional[DLQEvent]:
        """Get a DLQ event by its original event ID."""
        for dlq_event in self._dlq_events.values():
            if dlq_event.event_id == event_id:
                return dlq_event
        return None

    def list_dlq_events(
        self,
        event_type_filter: Optional[str] = None,
        service_filter: Optional[str] = None,
        correlation_id_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DLQEvent]:
        """List DLQ events with optional filters."""
        events = list(self._dlq_events.values())

        # Apply filters
        if event_type_filter:
            events = [e for e in events if e.event_type == event_type_filter]

        if service_filter:
            events = [e for e in events if e.service_name == service_filter]

        if correlation_id_filter:
            events = [e for e in events if e.correlation_id == correlation_id_filter]

        # Sort by DLQ timestamp (newest first)
        events.sort(key=lambda e: e.dlq_timestamp, reverse=True)

        # Apply pagination
        start_idx = offset
        end_idx = start_idx + limit
        return events[start_idx:end_idx]

    def retry_dlq_events(self, dlq_ids: List[str]) -> Dict[str, Any]:
        """Retry DLQ events. Returns retry results."""
        results = {
            "total_requested": len(dlq_ids),
            "retried": [],
            "failed": [],
            "exhausted": []
        }

        for dlq_id in dlq_ids:
            dlq_event = self._dlq_events.get(dlq_id)
            if not dlq_event:
                results["failed"].append({
                    "dlq_id": dlq_id,
                    "reason": "DLQ event not found"
                })
                continue

            if dlq_event.increment_retry_count():
                results["retried"].append(dlq_event.dlq_id)
                # In a real implementation, this would re-queue the event
            else:
                results["exhausted"].append({
                    "dlq_id": dlq_event.dlq_id,
                    "max_retries": dlq_event.max_retries,
                    "current_retries": dlq_event.retry_count
                })

        return results

    def remove_from_dlq(self, dlq_ids: List[str]) -> Dict[str, Any]:
        """Remove events from DLQ."""
        results = {
            "total_requested": len(dlq_ids),
            "removed": [],
            "not_found": []
        }

        for dlq_id in dlq_ids:
            if dlq_id in self._dlq_events:
                del self._dlq_events[dlq_id]
                results["removed"].append(dlq_id)
            else:
                results["not_found"].append(dlq_id)

        return results

    def get_dlq_stats(self) -> Dict[str, Any]:
        """Get DLQ statistics."""
        events = list(self._dlq_events.values())

        if not events:
            return {
                "total_events": 0,
                "events_by_type": {},
                "events_by_service": {},
                "retryable_events": 0,
                "oldest_event": None,
                "newest_event": None
            }

        # Calculate statistics
        events_by_type = {}
        events_by_service = {}

        for event in events:
            events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1
            if event.service_name:
                events_by_service[event.service_name] = events_by_service.get(event.service_name, 0) + 1

        retryable_count = len([e for e in events if e.can_retry])

        sorted_events = sorted(events, key=lambda e: e.dlq_timestamp)

        return {
            "total_events": len(events),
            "events_by_type": events_by_type,
            "events_by_service": events_by_service,
            "retryable_events": retryable_count,
            "oldest_event": sorted_events[0].dlq_timestamp.isoformat(),
            "newest_event": sorted_events[-1].dlq_timestamp.isoformat()
        }

    def cleanup_old_events(self, max_age_hours: int = 24) -> int:
        """Remove events older than specified hours. Returns count removed."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        events_to_remove = []

        for dlq_id, event in self._dlq_events.items():
            if event.dlq_timestamp < cutoff_time:
                events_to_remove.append(dlq_id)

        for dlq_id in events_to_remove:
            del self._dlq_events[dlq_id]

        return len(events_to_remove)
