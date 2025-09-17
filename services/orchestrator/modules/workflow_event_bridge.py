#!/usr/bin/env python3
"""
Workflow Event Bridge

Connects the workflow management system with the event-driven orchestration framework.
Provides seamless integration between workflow operations and event emission/persistence.
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from .redis_manager import publish_orchestrator_event
from .event_driven_orchestration import (
    event_store,
    WorkflowEvent,
    EventType
)
from services.shared.core.constants_new import ServiceNames
from services.shared.monitoring.logging import fire_and_forget
from services.shared.utilities import generate_id

try:
    from services.shared.event_streaming import event_stream_processor, StreamEvent, EventType as StreamEventType
    EVENT_STREAMING_AVAILABLE = True
except ImportError:
    EVENT_STREAMING_AVAILABLE = False


class WorkflowEventBridge:
    """Bridge between workflow operations and event system."""

    def __init__(self):
        self.event_handlers_registered = False

    async def initialize_bridge(self):
        """Initialize the workflow-event bridge."""
        if not self.event_handlers_registered:
            await self._register_event_handlers()
            self.event_handlers_registered = True
            fire_and_forget("info", "Workflow-event bridge initialized", ServiceNames.ORCHESTRATOR)

    async def _register_event_handlers(self):
        """Register event handlers for workflow events."""
        # Register handlers in event store
        event_store.register_event_handler(EventType.WORKFLOW_STARTED, self._handle_workflow_started_event)
        event_store.register_event_handler(EventType.WORKFLOW_COMPLETED, self._handle_workflow_completed_event)
        event_store.register_event_handler(EventType.WORKFLOW_FAILED, self._handle_workflow_failed_event)

        # Register handlers in event-driven engine
        from .event_driven_orchestration import event_driven_engine
        event_driven_engine.register_event_processor(EventType.WORKFLOW_STARTED, self._process_workflow_started)
        event_driven_engine.register_event_processor(EventType.WORKFLOW_COMPLETED, self._process_workflow_completed)
        event_driven_engine.register_event_processor(EventType.WORKFLOW_FAILED, self._process_workflow_failed)

    async def emit_workflow_event(self,
                                 event_type: str,
                                 workflow_id: str,
                                 workflow_data: Dict[str, Any],
                                 correlation_id: str = None,
                                 user_id: str = None) -> bool:
        """Emit a workflow-related event through multiple channels."""

        correlation_id = correlation_id or generate_id("correlation")
        event_id = generate_id("event")

        # Prepare event payload
        event_payload = {
            "workflow_id": workflow_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": correlation_id,
            "event_id": event_id,
            "user_id": user_id,
            **workflow_data
        }

        success_count = 0

        # 1. Publish to Redis pub/sub
        redis_success = await publish_orchestrator_event(
            f"workflow.{event_type}",
            event_payload,
            correlation_id
        )
        if redis_success:
            success_count += 1
            fire_and_forget("debug", f"Published workflow event to Redis: {event_type}", ServiceNames.ORCHESTRATOR)
        else:
            fire_and_forget("warning", f"Failed to publish workflow event to Redis: {event_type}", ServiceNames.ORCHESTRATOR)

        # 2. Store in event store (for event sourcing)
        try:
            workflow_event = WorkflowEvent(
                event_id=event_id,
                event_type=self._map_event_type(event_type),
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id=correlation_id,
                payload=workflow_data,
                metadata={
                    "source": "workflow_bridge",
                    "event_category": "workflow_lifecycle"
                },
                user_id=user_id
            )

            store_success = await event_store.store_event(workflow_event)
            if store_success:
                success_count += 1
                fire_and_forget("debug", f"Stored workflow event in event store: {event_type}", ServiceNames.ORCHESTRATOR)
            else:
                fire_and_forget("warning", f"Failed to store workflow event: {event_type}", ServiceNames.ORCHESTRATOR)

        except Exception as e:
            fire_and_forget("error", f"Event store error for workflow {workflow_id}: {e}", ServiceNames.ORCHESTRATOR)

        # 3. Publish to event streaming (if available)
        if EVENT_STREAMING_AVAILABLE:
            try:
                stream_event = StreamEvent(
                    source_service="orchestrator",
                    event_name=f"workflow_{event_type}",
                    payload=event_payload,
                    correlation_id=correlation_id,
                    metadata={
                        "workflow_id": workflow_id,
                        "event_category": "workflow_lifecycle"
                    }
                )

                stream_success = await event_stream_processor.publish_event(
                    "workflow_events",
                    stream_event
                )

                if stream_success:
                    success_count += 1
                    fire_and_forget("debug", f"Published workflow event to stream: {event_type}", ServiceNames.ORCHESTRATOR)
                else:
                    fire_and_forget("warning", f"Failed to publish workflow event to stream: {event_type}", ServiceNames.ORCHESTRATOR)

            except Exception as e:
                fire_and_forget("error", f"Event streaming error for workflow {workflow_id}: {e}", ServiceNames.ORCHESTRATOR)

        # Log overall success
        if success_count > 0:
            fire_and_forget("info", f"Workflow event emitted successfully: {event_type} ({success_count} channels)", ServiceNames.ORCHESTRATOR, {
                "workflow_id": workflow_id,
                "event_type": event_type,
                "correlation_id": correlation_id,
                "channels_successful": success_count
            })
        else:
            fire_and_forget("error", f"Workflow event emission failed completely: {event_type}", ServiceNames.ORCHESTRATOR, {
                "workflow_id": workflow_id,
                "correlation_id": correlation_id
            })

        return success_count > 0

    def _map_event_type(self, event_type: str) -> EventType:
        """Map string event type to EventType enum."""
        mapping = {
            "created": EventType.WORKFLOW_STARTED,
            "started": EventType.WORKFLOW_STARTED,
            "completed": EventType.WORKFLOW_COMPLETED,
            "failed": EventType.WORKFLOW_FAILED,
            "error": EventType.ERROR_OCCURRED,
            "step_started": EventType.STEP_STARTED,
            "step_completed": EventType.STEP_COMPLETED,
            "step_failed": EventType.STEP_FAILED
        }
        return mapping.get(event_type, EventType.STATE_CHANGED)

    async def emit_workflow_created(self, workflow_id: str, workflow_data: Dict[str, Any], user_id: str = None) -> bool:
        """Emit workflow creation event."""
        return await self.emit_workflow_event(
            "created",
            workflow_id,
            {
                "action": "created",
                "workflow_name": workflow_data.get("name", "Unknown"),
                "workflow_description": workflow_data.get("description", ""),
                "parameters_count": len(workflow_data.get("parameters", [])),
                "actions_count": len(workflow_data.get("actions", []))
            },
            user_id=user_id
        )

    async def emit_workflow_started(self, workflow_id: str, execution_id: str, parameters: Dict[str, Any], user_id: str = None) -> bool:
        """Emit workflow execution started event."""
        return await self.emit_workflow_event(
            "started",
            workflow_id,
            {
                "action": "started",
                "execution_id": execution_id,
                "parameters": parameters,
                "parameter_count": len(parameters)
            },
            user_id=user_id
        )

    async def emit_workflow_completed(self, workflow_id: str, execution_id: str, result: Dict[str, Any], duration: float, user_id: str = None) -> bool:
        """Emit workflow execution completed event."""
        return await self.emit_workflow_event(
            "completed",
            workflow_id,
            {
                "action": "completed",
                "execution_id": execution_id,
                "result": result,
                "duration_seconds": duration,
                "success": True
            },
            user_id=user_id
        )

    async def emit_workflow_failed(self, workflow_id: str, execution_id: str, error: str, duration: float, user_id: str = None) -> bool:
        """Emit workflow execution failed event."""
        return await self.emit_workflow_event(
            "failed",
            workflow_id,
            {
                "action": "failed",
                "execution_id": execution_id,
                "error": error,
                "duration_seconds": duration,
                "success": False
            },
            user_id=user_id
        )

    async def emit_step_event(self, workflow_id: str, execution_id: str, step_id: str, step_name: str, status: str, data: Dict[str, Any] = None, user_id: str = None) -> bool:
        """Emit workflow step event."""
        event_type = f"step_{status}"

        return await self.emit_workflow_event(
            event_type,
            workflow_id,
            {
                "action": event_type,
                "execution_id": execution_id,
                "step_id": step_id,
                "step_name": step_name,
                "status": status,
                **(data or {})
            },
            user_id=user_id
        )

    # Event handler methods
    async def _handle_workflow_started_event(self, event: WorkflowEvent):
        """Handle workflow started event from event store."""
        fire_and_forget("info", f"Workflow started event received: {event.workflow_id}", ServiceNames.ORCHESTRATOR, {
            "event_id": event.event_id,
            "correlation_id": event.correlation_id
        })

    async def _handle_workflow_completed_event(self, event: WorkflowEvent):
        """Handle workflow completed event from event store."""
        fire_and_forget("info", f"Workflow completed event received: {event.workflow_id}", ServiceNames.ORCHESTRATOR, {
            "event_id": event.event_id,
            "correlation_id": event.correlation_id,
            "duration": event.payload.get("duration_seconds")
        })

    async def _handle_workflow_failed_event(self, event: WorkflowEvent):
        """Handle workflow failed event from event store."""
        fire_and_forget("warning", f"Workflow failed event received: {event.workflow_id}", ServiceNames.ORCHESTRATOR, {
            "event_id": event.event_id,
            "correlation_id": event.correlation_id,
            "error": event.payload.get("error")
        })

    # Event processor methods for event-driven engine
    async def _process_workflow_started(self, event: WorkflowEvent):
        """Process workflow started event in event-driven engine."""
        # Could trigger additional workflows, notifications, etc.
        fire_and_forget("debug", f"Processing workflow started: {event.workflow_id}", ServiceNames.ORCHESTRATOR)

    async def _process_workflow_completed(self, event: WorkflowEvent):
        """Process workflow completed event in event-driven engine."""
        # Could trigger cleanup, notifications, analytics, etc.
        fire_and_forget("debug", f"Processing workflow completed: {event.workflow_id}", ServiceNames.ORCHESTRATOR)

    async def _process_workflow_failed(self, event: WorkflowEvent):
        """Process workflow failed event in event-driven engine."""
        # Could trigger error handling, retries, notifications, etc.
        fire_and_forget("debug", f"Processing workflow failed: {event.workflow_id}", ServiceNames.ORCHESTRATOR)

    async def get_workflow_events(self, workflow_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events for a specific workflow."""
        try:
            events = await event_store.get_aggregate_events(workflow_id, "workflow")

            # Convert to dict format
            event_list = []
            for event in events[-limit:]:  # Get last N events
                event_list.append({
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "correlation_id": event.correlation_id,
                    "payload": event.payload,
                    "metadata": event.metadata
                })

            return event_list

        except Exception as e:
            fire_and_forget("error", f"Failed to get workflow events for {workflow_id}: {e}", ServiceNames.ORCHESTRATOR)
            return []

    async def replay_workflow_events(self, workflow_id: str) -> Dict[str, Any]:
        """Replay events to reconstruct workflow state."""
        try:
            state = await event_store.replay_events(workflow_id, "workflow")
            return state
        except Exception as e:
            fire_and_forget("error", f"Failed to replay workflow events for {workflow_id}: {e}", ServiceNames.ORCHESTRATOR)
            return {"error": str(e)}


# Global workflow event bridge instance
workflow_event_bridge = WorkflowEventBridge()


async def initialize_workflow_event_bridge():
    """Initialize the workflow event bridge."""
    await workflow_event_bridge.initialize_bridge()
    fire_and_forget("info", "Workflow event bridge initialized", ServiceNames.ORCHESTRATOR)


# Convenience functions for easy access
async def emit_workflow_created_event(workflow_id: str, workflow_data: Dict[str, Any], user_id: str = None) -> bool:
    """Emit workflow created event."""
    return await workflow_event_bridge.emit_workflow_created(workflow_id, workflow_data, user_id)


async def emit_workflow_started_event(workflow_id: str, execution_id: str, parameters: Dict[str, Any], user_id: str = None) -> bool:
    """Emit workflow started event."""
    return await workflow_event_bridge.emit_workflow_started(workflow_id, execution_id, parameters, user_id)


async def emit_workflow_completed_event(workflow_id: str, execution_id: str, result: Dict[str, Any], duration: float, user_id: str = None) -> bool:
    """Emit workflow completed event."""
    return await workflow_event_bridge.emit_workflow_completed(workflow_id, execution_id, result, duration, user_id)


async def emit_workflow_failed_event(workflow_id: str, execution_id: str, error: str, duration: float, user_id: str = None) -> bool:
    """Emit workflow failed event."""
    return await workflow_event_bridge.emit_workflow_failed(workflow_id, execution_id, error, duration, user_id)


async def emit_step_event(workflow_id: str, execution_id: str, step_id: str, step_name: str, status: str, data: Dict[str, Any] = None, user_id: str = None) -> bool:
    """Emit workflow step event."""
    return await workflow_event_bridge.emit_step_event(workflow_id, execution_id, step_id, step_name, status, data, user_id)


async def get_workflow_events(workflow_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get events for a workflow."""
    return await workflow_event_bridge.get_workflow_events(workflow_id, limit)


async def replay_workflow_events(workflow_id: str) -> Dict[str, Any]:
    """Replay workflow events to get current state."""
    return await workflow_event_bridge.replay_workflow_events(workflow_id)
