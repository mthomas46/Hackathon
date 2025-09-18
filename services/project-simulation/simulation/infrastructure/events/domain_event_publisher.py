"""Domain Event Publisher - Cross-Bounded Context Communication.

This module implements the domain event publishing infrastructure
for communication between bounded contexts.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Awaitable
from datetime import datetime
import asyncio
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))
from streaming.event_streaming import EventPublisher

from ...domain.events import DomainEvent, event_from_dict
from ...domain.value_objects import ServiceHealth
from ..logging import get_simulation_logger
from ..clients.ecosystem_clients import get_ecosystem_client


class DomainEventPublisher:
    """Publisher for domain events across bounded contexts."""

    def __init__(self):
        """Initialize domain event publisher."""
        self.logger = get_simulation_logger()
        self._subscribers: Dict[str, List[Callable[[DomainEvent], Awaitable[None]]]] = {}
        self._event_publisher = EventPublisher("project-simulation")
        self._published_events: List[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all subscribers."""
        try:
            self.logger.info(
                "Publishing domain event",
                event_type=event.event_type,
                event_id=event.event_id,
                aggregate_id=event.get_aggregate_id()
            )

            # Store event for tracking
            self._published_events.append(event)

            # Publish to local subscribers
            if event.event_type in self._subscribers:
                tasks = []
                for subscriber in self._subscribers[event.event_type]:
                    tasks.append(subscriber(event))
                await asyncio.gather(*tasks, return_exceptions=True)

            # Publish to ecosystem event streaming
            await self._publish_to_ecosystem(event)

            self.logger.debug(
                "Domain event published successfully",
                event_type=event.event_type,
                event_id=event.event_id
            )

        except Exception as e:
            self.logger.error(
                "Failed to publish domain event",
                error=str(e),
                event_type=event.event_type,
                event_id=event.event_id
            )
            raise

    async def _publish_to_ecosystem(self, event: DomainEvent) -> None:
        """Publish event to ecosystem event streaming service."""
        try:
            # Try to publish to event streaming service
            event_data = {
                "event_type": event.event_type,
                "event_id": event.event_id,
                "aggregate_id": event.get_aggregate_id(),
                "occurred_at": event.occurred_at.isoformat(),
                "event_data": event.to_dict(),
                "source_service": "project-simulation",
                "event_version": event.event_version
            }

            # This would integrate with the shared event streaming infrastructure
            # For now, we'll log the event
            self.logger.info(
                "Event published to ecosystem",
                event_type=event.event_type,
                event_id=event.event_id,
                aggregate_id=event.get_aggregate_id()
            )

        except Exception as e:
            self.logger.warning(
                "Failed to publish event to ecosystem",
                error=str(e),
                event_type=event.event_type
            )

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], Awaitable[None]]) -> None:
        """Subscribe to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

        self.logger.debug(
            "Subscribed to domain event",
            event_type=event_type,
            handler=str(handler)
        )

    def unsubscribe(self, event_type: str, handler: Callable[[DomainEvent], Awaitable[None]]) -> None:
        """Unsubscribe from a specific event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                self.logger.debug(
                    "Unsubscribed from domain event",
                    event_type=event_type,
                    handler=str(handler)
                )
            except ValueError:
                pass

    def get_published_events(self, event_type: Optional[str] = None) -> List[DomainEvent]:
        """Get published events, optionally filtered by type."""
        if event_type:
            return [e for e in self._published_events if e.event_type == event_type]
        return self._published_events.copy()

    def clear_published_events(self) -> None:
        """Clear the published events history."""
        self._published_events.clear()

    async def replay_events(self, event_type: Optional[str] = None) -> List[DomainEvent]:
        """Replay published events (useful for testing/debugging)."""
        events = self.get_published_events(event_type)
        self.logger.info(
            "Replaying domain events",
            event_type=event_type or "all",
            event_count=len(events)
        )
        return events


class EcosystemEventSubscriber:
    """Subscriber for events from other ecosystem services."""

    def __init__(self, publisher: DomainEventPublisher):
        """Initialize ecosystem event subscriber."""
        self.publisher = publisher
        self.logger = get_simulation_logger()
        self._running = False

    async def start_listening(self) -> None:
        """Start listening for ecosystem events."""
        if self._running:
            return

        self._running = True
        self.logger.info("Starting ecosystem event listener")

        try:
            # This would integrate with the shared event streaming infrastructure
            # For now, we'll simulate listening for events
            while self._running:
                # Simulate receiving events from other services
                await self._process_pending_events()
                await asyncio.sleep(5)  # Check every 5 seconds

        except Exception as e:
            self.logger.error("Error in ecosystem event listener", error=str(e))
        finally:
            self._running = False

    async def stop_listening(self) -> None:
        """Stop listening for ecosystem events."""
        self._running = False
        self.logger.info("Stopped ecosystem event listener")

    async def _process_pending_events(self) -> None:
        """Process any pending events from ecosystem services."""
        # This would check for events from other services
        # For now, we'll simulate some cross-service events

        # Example: React to doc_store events
        doc_store_client = get_ecosystem_client("doc_store")
        if doc_store_client:
            try:
                # Check for recent documents (this is a placeholder)
                # In real implementation, this would listen to event streams
                pass
            except Exception as e:
                self.logger.debug("No new doc_store events", error=str(e))

        # Example: React to orchestrator workflow events
        orchestrator_client = get_ecosystem_client("orchestrator")
        if orchestrator_client:
            try:
                # Check for workflow status updates (placeholder)
                pass
            except Exception as e:
                self.logger.debug("No new orchestrator events", error=str(e))


class DomainEventBus:
    """Central event bus for domain event handling."""

    def __init__(self):
        """Initialize domain event bus."""
        self.publisher = DomainEventPublisher()
        self.subscriber = EcosystemEventSubscriber(self.publisher)
        self.logger = get_simulation_logger()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the event bus."""
        if self._initialized:
            return

        # Register default event handlers
        await self._register_default_handlers()

        # Start ecosystem event subscriber
        asyncio.create_task(self.subscriber.start_listening())

        self._initialized = True
        self.logger.info("Domain event bus initialized")

    async def _register_default_handlers(self) -> None:
        """Register default event handlers."""
        # Import here to avoid circular imports
        from ...domain.events import (
            ProjectCreated, ProjectStatusChanged, ProjectPhaseCompleted,
            SimulationStarted, SimulationCompleted, SimulationFailed,
            DocumentGenerated, WorkflowExecuted
        )

        # Project events
        self.publisher.subscribe("ProjectCreated", self._handle_project_created)
        self.publisher.subscribe("ProjectStatusChanged", self._handle_project_status_changed)
        self.publisher.subscribe("ProjectPhaseCompleted", self._handle_project_phase_completed)

        # Simulation events
        self.publisher.subscribe("SimulationStarted", self._handle_simulation_started)
        self.publisher.subscribe("SimulationCompleted", self._handle_simulation_completed)
        self.publisher.subscribe("SimulationFailed", self._handle_simulation_failed)

        # Document and workflow events
        self.publisher.subscribe("DocumentGenerated", self._handle_document_generated)
        self.publisher.subscribe("WorkflowExecuted", self._handle_workflow_executed)

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        await self.publisher.publish(event)

    async def _handle_project_created(self, event: ProjectCreated) -> None:
        """Handle project created event."""
        self.logger.info(
            "Project created event received",
            project_id=event.project_id,
            project_name=event.project_name
        )

        # Could trigger notifications, analytics, etc.

    async def _handle_project_status_changed(self, event: ProjectStatusChanged) -> None:
        """Handle project status changed event."""
        self.logger.info(
            "Project status changed",
            project_id=event.project_id,
            old_status=event.old_status,
            new_status=event.new_status
        )

        # Could trigger status-based workflows

    async def _handle_project_phase_completed(self, event: ProjectPhaseCompleted) -> None:
        """Handle project phase completed event."""
        self.logger.info(
            "Project phase completed",
            project_id=event.project_id,
            phase_name=event.phase_name
        )

        # Could trigger next phase initialization

    async def _handle_simulation_started(self, event: SimulationStarted) -> None:
        """Handle simulation started event."""
        self.logger.info(
            "Simulation started",
            simulation_id=event.simulation_id,
            project_id=event.project_id
        )

        # Could trigger monitoring, notifications

    async def _handle_simulation_completed(self, event: SimulationCompleted) -> None:
        """Handle simulation completed event."""
        self.logger.info(
            "Simulation completed",
            simulation_id=event.simulation_id,
            project_id=event.project_id,
            success=event.success
        )

        # Could trigger result processing, notifications

    async def _handle_simulation_failed(self, event: SimulationFailed) -> None:
        """Handle simulation failed event."""
        self.logger.error(
            "Simulation failed",
            simulation_id=event.simulation_id,
            project_id=event.project_id,
            failure_reason=event.failure_reason
        )

        # Could trigger error handling, notifications

    async def _handle_document_generated(self, event: DocumentGenerated) -> None:
        """Handle document generated event."""
        self.logger.info(
            "Document generated",
            simulation_id=event.simulation_id,
            document_type=event.document_type,
            word_count=event.word_count
        )

        # Could trigger document analysis workflows

    async def _handle_workflow_executed(self, event: WorkflowExecuted) -> None:
        """Handle workflow executed event."""
        self.logger.info(
            "Workflow executed",
            simulation_id=event.simulation_id,
            workflow_type=event.workflow_type,
            success=event.success,
            execution_time=event.execution_time_seconds
        )

        # Could trigger follow-up workflows or notifications

    async def shutdown(self) -> None:
        """Shutdown the event bus."""
        await self.subscriber.stop_listening()
        self.logger.info("Domain event bus shut down")


# Global event bus instance
_event_bus: Optional[DomainEventBus] = None


def get_domain_event_bus() -> DomainEventBus:
    """Get the global domain event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = DomainEventBus()
    return _event_bus


async def initialize_event_bus() -> None:
    """Initialize the global event bus."""
    bus = get_domain_event_bus()
    await bus.initialize()


async def publish_domain_event(event: DomainEvent) -> None:
    """Publish a domain event using the global event bus."""
    bus = get_domain_event_bus()
    await bus.publish(event)


__all__ = [
    'DomainEventPublisher',
    'EcosystemEventSubscriber',
    'DomainEventBus',
    'get_domain_event_bus',
    'initialize_event_bus',
    'publish_domain_event'
]
