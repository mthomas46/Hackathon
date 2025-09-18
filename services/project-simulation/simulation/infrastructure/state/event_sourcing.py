"""Event Sourcing - Simulation State Management with Event Sourcing.

This module implements event sourcing patterns for simulation state management,
providing complete audit trails, temporal queries, and reliable state reconstruction
following Domain-Driven Design principles and leveraging existing ecosystem patterns.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Type, TypeVar, Generic, Union
from datetime import datetime
from uuid import uuid4
import json
import weakref

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.utilities.simulation_utilities import get_simulation_cache

# Import simulation domain
from simulation.domain.value_objects import SimulationStatus
from simulation.domain.events import DomainEvent

T = TypeVar('T')


class EventEnvelope:
    """Envelope for domain events with metadata."""

    def __init__(self,
                 event: DomainEvent,
                 aggregate_id: str,
                 aggregate_type: str,
                 sequence_number: int,
                 timestamp: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize event envelope."""
        self.event = event
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.sequence_number = sequence_number
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        self.event_id = str(uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "event_id": self.event_id,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event.event_type,
            "event_data": self.event.dict(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventEnvelope':
        """Create from dictionary."""
        event_data = data["event_data"]
        event_type = data["event_type"]

        # Reconstruct the domain event
        if event_type == "SimulationStarted":
            from simulation.domain.events import SimulationStarted
            event = SimulationStarted(**event_data)
        elif event_type == "SimulationFinished":
            from simulation.domain.events import SimulationFinished
            event = SimulationFinished(**event_data)
        elif event_type == "PhaseCompleted":
            from simulation.domain.events import PhaseCompleted
            event = PhaseCompleted(**event_data)
        elif event_type == "DocumentGenerated":
            from simulation.domain.events import DocumentGenerated
            event = DocumentGenerated(**event_data)
        elif event_type == "WorkflowExecuted":
            from simulation.domain.events import WorkflowExecuted
            event = WorkflowExecuted(**event_data)
        else:
            # Generic domain event for unknown types
            event = DomainEvent(
                event_type=event_type,
                payload=event_data,
                event_id=event_data.get("event_id", str(uuid4())),
                timestamp=datetime.fromisoformat(data["timestamp"])
            )

        return cls(
            event=event,
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            sequence_number=data["sequence_number"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


class EventStore:
    """Event store for persisting domain events."""

    def __init__(self):
        """Initialize event store."""
        self.logger = get_simulation_logger()
        self.cache = get_simulation_cache()
        self._events: Dict[str, List[EventEnvelope]] = {}
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    async def save_events(self, aggregate_id: str, events: List[EventEnvelope]) -> None:
        """Save events to the store."""
        if aggregate_id not in self._events:
            self._events[aggregate_id] = []

        self._events[aggregate_id].extend(events)

        # Invalidate cache for this aggregate
        cache_key = f"aggregate:{aggregate_id}"
        self.cache.delete(cache_key)

        self.logger.info(
            "Events saved",
            aggregate_id=aggregate_id,
            event_count=len(events),
            last_sequence=events[-1].sequence_number if events else 0
        )

    async def get_events(self, aggregate_id: str, from_sequence: int = 0) -> List[EventEnvelope]:
        """Get events for an aggregate."""
        if aggregate_id not in self._events:
            return []

        all_events = self._events[aggregate_id]
        return [e for e in all_events if e.sequence_number >= from_sequence]

    async def get_all_events(self, aggregate_id: str) -> List[EventEnvelope]:
        """Get all events for an aggregate."""
        return self._events.get(aggregate_id, [])

    async def save_snapshot(self, aggregate_id: str, snapshot: Dict[str, Any], version: int) -> None:
        """Save a snapshot of aggregate state."""
        self._snapshots[aggregate_id] = {
            "data": snapshot,
            "version": version,
            "timestamp": datetime.now()
        }

        self.logger.info("Snapshot saved", aggregate_id=aggregate_id, version=version)

    async def get_snapshot(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest snapshot for an aggregate."""
        return self._snapshots.get(aggregate_id)

    def get_aggregate_ids(self) -> List[str]:
        """Get all aggregate IDs."""
        return list(self._events.keys())


class AggregateRoot(Generic[T]):
    """Base class for aggregate roots with event sourcing."""

    def __init__(self, aggregate_id: str):
        """Initialize aggregate root."""
        self.aggregate_id = aggregate_id
        self._version = 0
        self._changes: List[DomainEvent] = []

    def get_uncommitted_changes(self) -> List[DomainEvent]:
        """Get uncommitted changes."""
        return self._changes.copy()

    def mark_changes_as_committed(self) -> None:
        """Mark changes as committed."""
        self._changes.clear()

    def load_from_history(self, events: List[EventEnvelope]) -> None:
        """Load aggregate state from event history."""
        for envelope in events:
            self.apply_event(envelope.event, False)
            self._version = envelope.sequence_number

    def apply_event(self, event: DomainEvent, is_new: bool = True) -> None:
        """Apply an event to the aggregate."""
        self._apply_event(event)

        if is_new:
            self._changes.append(event)
            self._version += 1

    def _apply_event(self, event: DomainEvent) -> None:
        """Apply event to aggregate state - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _apply_event")

    @property
    def version(self) -> int:
        """Get current version."""
        return self._version


class SimulationAggregate(AggregateRoot):
    """Aggregate root for simulation state management."""

    def __init__(self, simulation_id: str):
        """Initialize simulation aggregate."""
        super().__init__(simulation_id)
        self.status = SimulationStatus.INITIALIZED
        self.project_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.phase_progress: Dict[str, float] = {}
        self.generated_documents: List[str] = []
        self.service_calls: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}

    def start_simulation(self, project_id: str, config: Dict[str, Any]) -> None:
        """Start the simulation."""
        from simulation.domain.events import SimulationStarted

        event = SimulationStarted(
            simulation_id=self.aggregate_id,
            project_id=project_id,
            config=config
        )

        self.apply_event(event)

    def complete_phase(self, phase_name: str, progress: float, results: Dict[str, Any]) -> None:
        """Complete a simulation phase."""
        from simulation.domain.events import PhaseCompleted

        event = PhaseCompleted(
            simulation_id=self.aggregate_id,
            phase_name=phase_name,
            progress=progress,
            results=results
        )

        self.apply_event(event)

    def generate_document(self, document_id: str, document_type: str, metadata: Dict[str, Any]) -> None:
        """Record document generation."""
        from simulation.domain.events import DocumentGenerated

        event = DocumentGenerated(
            simulation_id=self.aggregate_id,
            document_id=document_id,
            document_type=document_type,
            metadata=metadata
        )

        self.apply_event(event)

    def execute_workflow(self, workflow_id: str, workflow_name: str, status: str, results: Dict[str, Any]) -> None:
        """Record workflow execution."""
        from simulation.domain.events import WorkflowExecuted

        event = WorkflowExecuted(
            simulation_id=self.aggregate_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            status=status,
            results=results
        )

        self.apply_event(event)

    def finish_simulation(self, final_status: str, summary: Dict[str, Any]) -> None:
        """Finish the simulation."""
        from simulation.domain.events import SimulationFinished

        event = SimulationFinished(
            simulation_id=self.aggregate_id,
            final_status=final_status,
            summary=summary
        )

        self.apply_event(event)

    def _apply_event(self, event: DomainEvent) -> None:
        """Apply event to simulation state."""
        if event.event_type == "SimulationStarted":
            self.status = SimulationStatus.RUNNING
            self.project_id = event.project_id
            self.start_time = event.timestamp
            self.metrics.update(event.config.get("initial_metrics", {}))

        elif event.event_type == "PhaseCompleted":
            self.phase_progress[event.phase_name] = event.progress
            self.metrics.update(event.results.get("metrics", {}))

        elif event.event_type == "DocumentGenerated":
            self.generated_documents.append(event.document_id)

        elif event.event_type == "WorkflowExecuted":
            self.service_calls.append({
                "workflow_id": event.workflow_id,
                "workflow_name": event.workflow_name,
                "status": event.status,
                "timestamp": event.timestamp,
                "results": event.results
            })

        elif event.event_type == "SimulationFinished":
            self.status = SimulationStatus(event.final_status)
            self.end_time = event.timestamp
            self.metrics.update(event.summary.get("final_metrics", {}))


class EventSourcedRepository(Generic[T]):
    """Repository for event-sourced aggregates."""

    def __init__(self, event_store: EventStore, aggregate_class: Type[T]):
        """Initialize repository."""
        self.event_store = event_store
        self.aggregate_class = aggregate_class
        self.cache = get_simulation_cache()
        self.logger = get_simulation_logger()

    async def save(self, aggregate: T) -> None:
        """Save aggregate changes to event store."""
        changes = aggregate.get_uncommitted_changes()

        if not changes:
            return

        # Convert domain events to event envelopes
        envelopes = []
        for i, event in enumerate(changes):
            envelope = EventEnvelope(
                event=event,
                aggregate_id=aggregate.aggregate_id,
                aggregate_type=aggregate.__class__.__name__,
                sequence_number=aggregate.version - len(changes) + i + 1
            )
            envelopes.append(envelope)

        # Save events
        await self.event_store.save_events(aggregate.aggregate_id, envelopes)

        # Mark changes as committed
        aggregate.mark_changes_as_committed()

        # Invalidate cache
        cache_key = f"aggregate:{aggregate.aggregate_id}"
        self.cache.delete(cache_key)

        self.logger.info(
            "Aggregate saved",
            aggregate_id=aggregate.aggregate_id,
            event_count=len(envelopes)
        )

    async def get_by_id(self, aggregate_id: str) -> Optional[T]:
        """Get aggregate by ID."""
        # Check cache first
        cache_key = f"aggregate:{aggregate_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Try snapshot first for performance
        snapshot = await self.event_store.get_snapshot(aggregate_id)
        if snapshot:
            aggregate = self.aggregate_class(aggregate_id)
            # Load from snapshot
            aggregate.__dict__.update(snapshot["data"])
            aggregate._version = snapshot["version"]

            # Apply events after snapshot
            events = await self.event_store.get_events(aggregate_id, snapshot["version"] + 1)
        else:
            # Load from all events
            events = await self.event_store.get_all_events(aggregate_id)
            if not events:
                return None

            aggregate = self.aggregate_class(aggregate_id)

        # Apply events
        aggregate.load_from_history(events)

        # Cache the aggregate
        self.cache.set(cache_key, aggregate, ttl=300)  # 5 minutes

        return aggregate

    async def get_all_ids(self) -> List[str]:
        """Get all aggregate IDs."""
        return self.event_store.get_aggregate_ids()

    async def create_snapshot(self, aggregate_id: str) -> None:
        """Create a snapshot for an aggregate."""
        aggregate = await self.get_by_id(aggregate_id)
        if aggregate:
            snapshot_data = {
                k: v for k, v in aggregate.__dict__.items()
                if not k.startswith('_')
            }
            await self.event_store.save_snapshot(aggregate_id, snapshot_data, aggregate.version)


class EventSourcingService:
    """Service for managing event-sourced aggregates and temporal queries."""

    def __init__(self):
        """Initialize event sourcing service."""
        self.logger = get_simulation_logger()
        self.event_store = EventStore()
        self.repositories: Dict[str, EventSourcedRepository] = {}

    def get_repository(self, aggregate_class: Type[T]) -> EventSourcedRepository[T]:
        """Get repository for aggregate type."""
        class_name = aggregate_class.__name__

        if class_name not in self.repositories:
            self.repositories[class_name] = EventSourcedRepository(
                self.event_store,
                aggregate_class
            )

        return self.repositories[class_name]

    async def replay_events(self, aggregate_id: str, to_sequence: Optional[int] = None) -> List[EventEnvelope]:
        """Replay events for an aggregate up to a specific sequence."""
        events = await self.event_store.get_all_events(aggregate_id)

        if to_sequence is not None:
            events = [e for e in events if e.sequence_number <= to_sequence]

        return events

    async def get_event_history(self, aggregate_id: str, from_date: Optional[datetime] = None,
                               to_date: Optional[datetime] = None) -> List[EventEnvelope]:
        """Get event history for an aggregate within date range."""
        events = await self.event_store.get_all_events(aggregate_id)

        if from_date:
            events = [e for e in events if e.timestamp >= from_date]
        if to_date:
            events = [e for e in events if e.timestamp <= to_date]

        return sorted(events, key=lambda e: e.timestamp)

    async def get_aggregate_at_time(self, aggregate_id: str, timestamp: datetime) -> Optional[SimulationAggregate]:
        """Get aggregate state at a specific point in time."""
        events = await self.event_store.get_all_events(aggregate_id)
        events_before_time = [e for e in events if e.timestamp <= timestamp]

        if not events_before_time:
            return None

        # Create aggregate and apply historical events
        aggregate = SimulationAggregate(aggregate_id)
        aggregate.load_from_history(events_before_time)

        return aggregate

    async def get_aggregates_modified_since(self, since: datetime) -> List[str]:
        """Get aggregate IDs that were modified since a specific time."""
        modified_aggregates = set()

        for aggregate_id in self.event_store.get_aggregate_ids():
            events = await self.event_store.get_all_events(aggregate_id)
            recent_events = [e for e in events if e.timestamp >= since]

            if recent_events:
                modified_aggregates.add(aggregate_id)

        return list(modified_aggregates)

    async def get_event_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored events."""
        total_events = 0
        event_types = {}
        aggregates_with_events = 0
        oldest_event = None
        newest_event = None

        for aggregate_id in self.event_store.get_aggregate_ids():
            events = await self.event_store.get_all_events(aggregate_id)

            if events:
                aggregates_with_events += 1
                total_events += len(events)

                for event in events:
                    event_type = event.event.event_type
                    event_types[event_type] = event_types.get(event_type, 0) + 1

                    if oldest_event is None or event.timestamp < oldest_event:
                        oldest_event = event.timestamp
                    if newest_event is None or event.timestamp > newest_event:
                        newest_event = event.timestamp

        return {
            "total_events": total_events,
            "event_types": event_types,
            "aggregates_with_events": aggregates_with_events,
            "total_aggregates": len(self.event_store.get_aggregate_ids()),
            "oldest_event": oldest_event.isoformat() if oldest_event else None,
            "newest_event": newest_event.isoformat() if newest_event else None,
            "average_events_per_aggregate": total_events / aggregates_with_events if aggregates_with_events > 0 else 0
        }


# Global event sourcing service instance
_event_sourcing_service: Optional[EventSourcingService] = None


def get_event_sourcing_service() -> EventSourcingService:
    """Get the global event sourcing service instance."""
    global _event_sourcing_service
    if _event_sourcing_service is None:
        _event_sourcing_service = EventSourcingService()
    return _event_sourcing_service


# Convenience functions
async def save_aggregate(aggregate: AggregateRoot) -> None:
    """Save an aggregate using the event sourcing service."""
    service = get_event_sourcing_service()
    repository = service.get_repository(aggregate.__class__)
    await repository.save(aggregate)


async def get_aggregate(aggregate_class: Type[T], aggregate_id: str) -> Optional[T]:
    """Get an aggregate using the event sourcing service."""
    service = get_event_sourcing_service()
    repository = service.get_repository(aggregate_class)
    return await repository.get_by_id(aggregate_id)


async def create_snapshot(aggregate_id: str) -> None:
    """Create a snapshot for an aggregate."""
    service = get_event_sourcing_service()
    repository = service.get_repository(SimulationAggregate)
    await repository.create_snapshot(aggregate_id)


__all__ = [
    'EventEnvelope',
    'EventStore',
    'AggregateRoot',
    'SimulationAggregate',
    'EventSourcedRepository',
    'EventSourcingService',
    'get_event_sourcing_service',
    'save_aggregate',
    'get_aggregate',
    'create_snapshot'
]
