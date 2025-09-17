#!/usr/bin/env python3
"""
Event-Driven Orchestration

This module provides event-driven workflow orchestration capabilities including:
- Event sourcing patterns
- CQRS (Command Query Responsibility Segregation)
- Event streaming and processing
- Reactive workflow management
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Callable, Type, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import aio_pika
import redis.asyncio as redis

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from services.shared.intelligent_caching import get_service_cache


class EventType(Enum):
    """Event types for event-driven orchestration."""
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    SERVICE_CALLED = "service_called"
    SERVICE_RESPONSE = "service_response"
    ERROR_OCCURRED = "error_occurred"
    STATE_CHANGED = "state_changed"
    METRICS_UPDATED = "metrics_updated"


class EventPriority(Enum):
    """Event priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WorkflowEvent:
    """Workflow event for event-driven orchestration."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.WORKFLOW_STARTED
    workflow_id: str = ""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    aggregate_id: str = ""  # For event sourcing
    aggregate_type: str = "workflow"
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.MEDIUM
    causation_id: Optional[str] = None  # ID of event that caused this event
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "workflow_id": self.workflow_id,
            "correlation_id": self.correlation_id,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "causation_id": self.causation_id,
            "user_id": self.user_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowEvent':
        """Create event from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            workflow_id=data["workflow_id"],
            correlation_id=data["correlation_id"],
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            payload=data["payload"],
            metadata=data["metadata"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            priority=EventPriority(data["priority"]),
            causation_id=data.get("causation_id"),
            user_id=data.get("user_id")
        )


class EventStore:
    """Event store for event sourcing pattern."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.event_streams: Dict[str, List[WorkflowEvent]] = {}
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)

    async def connect(self):
        """Connect to Redis for event storage."""
        self.redis = redis.from_url(self.redis_url)

    async def store_event(self, event: WorkflowEvent) -> bool:
        """Store event in event store."""
        try:
            # Store in Redis
            if self.redis:
                event_key = f"event:{event.aggregate_type}:{event.aggregate_id}"
                event_data = json.dumps(event.to_dict())

                # Store individual event
                await self.redis.set(f"event:{event.event_id}", event_data)

                # Add to aggregate stream
                await self.redis.rpush(event_key, event.event_id)

                # Add to event type index
                await self.redis.sadd(f"events:{event.event_type.value}", event.event_id)

            # Store in memory
            if event.aggregate_id not in self.event_streams:
                self.event_streams[event.aggregate_id] = []
            self.event_streams[event.aggregate_id].append(event)

            # Trigger event handlers
            await self._trigger_event_handlers(event)

            return True

        except Exception as e:
            fire_and_forget("error", f"Failed to store event {event.event_id}: {e}", ServiceNames.ORCHESTRATOR)
            return False

    async def get_aggregate_events(self, aggregate_id: str, aggregate_type: str = "workflow") -> List[WorkflowEvent]:
        """Get all events for an aggregate."""
        try:
            events = []

            if self.redis:
                event_key = f"event:{aggregate_type}:{aggregate_id}"
                event_ids = await self.redis.lrange(event_key, 0, -1)

                for event_id_bytes in event_ids:
                    event_id = event_id_bytes.decode('utf-8')
                    event_data = await self.redis.get(f"event:{event_id}")
                    if event_data:
                        event_dict = json.loads(event_data)
                        events.append(WorkflowEvent.from_dict(event_dict))

            # Fallback to memory
            if not events and aggregate_id in self.event_streams:
                events = self.event_streams[aggregate_id]

            return events

        except Exception as e:
            fire_and_forget("error", f"Failed to get aggregate events for {aggregate_id}: {e}", ServiceNames.ORCHESTRATOR)
            return []

    async def get_events_by_type(self, event_type: EventType, limit: int = 100) -> List[WorkflowEvent]:
        """Get events by type."""
        try:
            events = []

            if self.redis:
                event_ids = await self.redis.smembers(f"events:{event_type.value}")
                event_ids = list(event_ids)[:limit]

                for event_id_bytes in event_ids:
                    event_id = event_id_bytes.decode('utf-8')
                    event_data = await self.redis.get(f"event:{event_id}")
                    if event_data:
                        event_dict = json.loads(event_data)
                        events.append(WorkflowEvent.from_dict(event_dict))

            return events

        except Exception as e:
            fire_and_forget("error", f"Failed to get events by type {event_type.value}: {e}", ServiceNames.ORCHESTRATOR)
            return []

    async def replay_events(self, aggregate_id: str, aggregate_type: str = "workflow") -> Dict[str, Any]:
        """Replay events to reconstruct aggregate state."""
        events = await self.get_aggregate_events(aggregate_id, aggregate_type)

        # Sort events by timestamp
        events.sort(key=lambda e: e.timestamp)

        # Reconstruct state
        state = {
            "aggregate_id": aggregate_id,
            "aggregate_type": aggregate_type,
            "current_state": "initialized",
            "event_count": len(events),
            "last_event_timestamp": events[-1].timestamp if events else None
        }

        # Apply events to state
        for event in events:
            state = await self._apply_event_to_state(state, event)

        return state

    async def _apply_event_to_state(self, state: Dict[str, Any], event: WorkflowEvent) -> Dict[str, Any]:
        """Apply event to aggregate state."""
        if event.event_type == EventType.WORKFLOW_STARTED:
            state["current_state"] = "running"
            state["started_at"] = event.timestamp
        elif event.event_type == EventType.WORKFLOW_COMPLETED:
            state["current_state"] = "completed"
            state["completed_at"] = event.timestamp
        elif event.event_type == EventType.WORKFLOW_FAILED:
            state["current_state"] = "failed"
            state["failed_at"] = event.timestamp
            state["failure_reason"] = event.payload.get("error")

        return state

    def register_event_handler(self, event_type: EventType, handler: Callable):
        """Register event handler."""
        self.event_handlers[event_type].append(handler)

    async def _trigger_event_handlers(self, event: WorkflowEvent):
        """Trigger registered event handlers."""
        if event.event_type in self.event_handlers:
            tasks = []
            for handler in self.event_handlers[event.event_type]:
                task = asyncio.create_task(handler(event))
                tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)


class CQRSHandler:
    """CQRS (Command Query Responsibility Segregation) handler."""

    def __init__(self):
        self.command_handlers: Dict[str, Callable] = {}
        self.query_handlers: Dict[str, Callable] = {}
        self.event_store = EventStore()

    def register_command_handler(self, command_type: str, handler: Callable):
        """Register command handler."""
        self.command_handlers[command_type] = handler

    def register_query_handler(self, query_type: str, handler: Callable):
        """Register query handler."""
        self.query_handlers[query_type] = handler

    async def handle_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle command (write operation)."""
        command_type = command.get("type", "")
        if command_type not in self.command_handlers:
            raise ValueError(f"No handler registered for command type: {command_type}")

        handler = self.command_handlers[command_type]

        # Execute command
        result = await handler(command)

        # Store events generated by command
        events = result.get("events", [])
        for event_data in events:
            event = WorkflowEvent(
                event_type=EventType(event_data["type"]),
                workflow_id=command.get("workflow_id", ""),
                aggregate_id=command.get("aggregate_id", ""),
                payload=event_data.get("payload", {}),
                metadata={"command_type": command_type}
            )
            await self.event_store.store_event(event)

        return result

    async def handle_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle query (read operation)."""
        query_type = query.get("type", "")
        if query_type not in self.query_handlers:
            raise ValueError(f"No handler registered for query type: {query_type}")

        handler = self.query_handlers[query_type]
        return await handler(query)


class EventDrivenWorkflowEngine:
    """Event-driven workflow engine."""

    def __init__(self):
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_definitions: Dict[str, Dict[str, Any]] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.event_processors: Dict[EventType, List[Callable]] = defaultdict(list)
        self.event_store = EventStore()
        self.cqrs_handler = CQRSHandler()

    async def start_event_processing(self):
        """Start event processing loop."""
        asyncio.create_task(self._event_processing_loop())
        fire_and_forget("info", "Event-driven workflow engine started", ServiceNames.ORCHESTRATOR)

    async def _event_processing_loop(self):
        """Main event processing loop."""
        while True:
            try:
                event = await self.event_queue.get()

                # Process event
                await self._process_event(event)

                # Mark event as processed
                self.event_queue.task_done()

            except Exception as e:
                fire_and_forget("error", f"Error in event processing loop: {e}", ServiceNames.ORCHESTRATOR)

    async def _process_event(self, event: WorkflowEvent):
        """Process individual event."""
        # Store event
        await self.event_store.store_event(event)

        # Trigger event processors
        if event.event_type in self.event_processors:
            tasks = []
            for processor in self.event_processors[event.event_type]:
                task = asyncio.create_task(processor(event))
                tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        # Handle workflow state changes
        if event.workflow_id:
            await self._handle_workflow_event(event)

    async def _handle_workflow_event(self, event: WorkflowEvent):
        """Handle workflow-specific events."""
        workflow_id = event.workflow_id

        if event.event_type == EventType.WORKFLOW_STARTED:
            # Initialize workflow state
            self.active_workflows[workflow_id] = {
                "status": "running",
                "started_at": event.timestamp,
                "events_processed": 1
            }

        elif event.event_type == EventType.WORKFLOW_COMPLETED:
            # Complete workflow
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = "completed"
                self.active_workflows[workflow_id]["completed_at"] = event.timestamp

        elif event.event_type == EventType.WORKFLOW_FAILED:
            # Fail workflow
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = "failed"
                self.active_workflows[workflow_id]["failed_at"] = event.timestamp
                self.active_workflows[workflow_id]["failure_reason"] = event.payload.get("error")

        # Update event count
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]["events_processed"] += 1

    async def publish_event(self, event: WorkflowEvent):
        """Publish event to processing queue."""
        await self.event_queue.put(event)

    def register_event_processor(self, event_type: EventType, processor: Callable):
        """Register event processor."""
        self.event_processors[event_type].append(processor)

    async def create_event_driven_workflow(self, workflow_definition: Dict[str, Any]) -> str:
        """Create event-driven workflow definition."""
        workflow_id = f"edw_{uuid.uuid4().hex[:8]}"

        self.workflow_definitions[workflow_id] = {
            "definition": workflow_definition,
            "created_at": datetime.now(),
            "status": "active"
        }

        return workflow_id

    async def execute_event_driven_workflow(self, workflow_id: str, initial_payload: Dict[str, Any]) -> str:
        """Execute event-driven workflow."""
        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"Workflow definition {workflow_id} not found")

        execution_id = str(uuid.uuid4())

        # Publish initial event
        initial_event = WorkflowEvent(
            event_type=EventType.WORKFLOW_STARTED,
            workflow_id=execution_id,
            aggregate_id=execution_id,
            payload=initial_payload,
            metadata={"workflow_definition_id": workflow_id}
        )

        await self.publish_event(initial_event)

        return execution_id

    async def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status."""
        return self.active_workflows.get(execution_id)


class ReactiveWorkflowManager:
    """Reactive workflow manager for handling streaming events."""

    def __init__(self):
        self.event_streams: Dict[str, asyncio.Queue] = {}
        self.workflow_reactions: Dict[str, List[Callable]] = defaultdict(list)
        self.stream_processors: Dict[str, asyncio.Task] = {}

    async def create_event_stream(self, stream_id: str) -> str:
        """Create new event stream."""
        if stream_id not in self.event_streams:
            self.event_streams[stream_id] = asyncio.Queue()

            # Start stream processor
            self.stream_processors[stream_id] = asyncio.create_task(
                self._process_event_stream(stream_id)
            )

        return stream_id

    async def publish_to_stream(self, stream_id: str, event: WorkflowEvent):
        """Publish event to stream."""
        if stream_id in self.event_streams:
            await self.event_streams[stream_id].put(event)

    def register_workflow_reaction(self, event_pattern: str, reaction_handler: Callable):
        """Register workflow reaction to event pattern."""
        self.workflow_reactions[event_pattern].append(reaction_handler)

    async def _process_event_stream(self, stream_id: str):
        """Process events from stream."""
        stream_queue = self.event_streams[stream_id]

        while True:
            try:
                event = await stream_queue.get()

                # Find matching reactions
                matching_reactions = []
                for pattern, reactions in self.workflow_reactions.items():
                    if self._matches_event_pattern(event, pattern):
                        matching_reactions.extend(reactions)

                # Execute reactions
                if matching_reactions:
                    tasks = [asyncio.create_task(reaction(event)) for reaction in matching_reactions]
                    await asyncio.gather(*tasks, return_exceptions=True)

                stream_queue.task_done()

            except Exception as e:
                fire_and_forget("error", f"Error processing event stream {stream_id}: {e}", ServiceNames.ORCHESTRATOR)

    def _matches_event_pattern(self, event: WorkflowEvent, pattern: str) -> bool:
        """Check if event matches pattern."""
        # Simple pattern matching - in practice, this could use regex or more sophisticated matching
        if pattern in event.event_type.value:
            return True
        if pattern in str(event.payload):
            return True
        return False

    async def cleanup_stream(self, stream_id: str):
        """Clean up event stream."""
        if stream_id in self.event_streams:
            # Cancel processor task
            if stream_id in self.stream_processors:
                self.stream_processors[stream_id].cancel()

            # Clear stream
            del self.event_streams[stream_id]
            del self.stream_processors[stream_id]


# Global instances
event_store = EventStore()
cqrs_handler = CQRSHandler()
event_driven_engine = EventDrivenWorkflowEngine()
reactive_manager = ReactiveWorkflowManager()


async def initialize_event_driven_orchestration():
    """Initialize event-driven orchestration capabilities."""
    # Connect to event store
    await event_store.connect()

    # Start event-driven workflow engine
    await event_driven_engine.start_event_processing()

    # Register sample event handlers
    event_store.register_event_handler(EventType.WORKFLOW_STARTED, handle_workflow_started)
    event_store.register_event_handler(EventType.WORKFLOW_COMPLETED, handle_workflow_completed)
    event_store.register_event_handler(EventType.ERROR_OCCURRED, handle_error_event)

    # Register CQRS handlers
    cqrs_handler.register_command_handler("start_workflow", handle_start_workflow_command)
    cqrs_handler.register_query_handler("get_workflow_status", handle_get_workflow_status_query)

    fire_and_forget("info", "Event-driven orchestration initialized", ServiceNames.ORCHESTRATOR)


# Sample event handlers
async def handle_workflow_started(event: WorkflowEvent):
    """Handle workflow started event."""
    fire_and_forget("info", f"Workflow {event.workflow_id} started via event", ServiceNames.ORCHESTRATOR)

async def handle_workflow_completed(event: WorkflowEvent):
    """Handle workflow completed event."""
    fire_and_forget("info", f"Workflow {event.workflow_id} completed via event", ServiceNames.ORCHESTRATOR)

async def handle_error_event(event: WorkflowEvent):
    """Handle error event."""
    fire_and_forget("error", f"Error in workflow {event.workflow_id}: {event.payload}", ServiceNames.ORCHESTRATOR)

# Sample CQRS handlers
async def handle_start_workflow_command(command: Dict[str, Any]) -> Dict[str, Any]:
    """Handle start workflow command."""
    workflow_id = command["workflow_id"]

    return {
        "success": True,
        "workflow_id": workflow_id,
        "events": [{
            "type": EventType.WORKFLOW_STARTED.value,
            "payload": {"workflow_id": workflow_id}
        }]
    }

async def handle_get_workflow_status_query(query: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get workflow status query."""
    workflow_id = query["workflow_id"]
    status = await event_driven_engine.get_workflow_status(workflow_id)

    return {
        "workflow_id": workflow_id,
        "status": status or {"error": "Workflow not found"}
    }
