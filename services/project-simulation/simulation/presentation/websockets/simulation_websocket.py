"""WebSocket Support - Real-time Simulation Updates.

This module implements WebSocket support for real-time simulation updates,
allowing clients to receive live progress updates and event notifications.
"""

import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ...infrastructure.logging import get_simulation_logger
from ...infrastructure.di_container import get_simulation_container
from ...domain.events import DomainEvent


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str = Field(..., description="Message type")
    simulation_id: Optional[str] = Field(None, description="Simulation ID")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(),
                          description="Message timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")


class SimulationProgressUpdate(WebSocketMessage):
    """Simulation progress update message."""
    type: str = "simulation_progress"
    progress_percentage: float = Field(..., description="Progress percentage (0-100)")
    current_phase: Optional[str] = Field(None, description="Current phase name")
    status: str = Field(..., description="Simulation status")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")


class SimulationEventNotification(WebSocketMessage):
    """Simulation event notification message."""
    type: str = "simulation_event"
    event_type: str = Field(..., description="Domain event type")
    event_description: str = Field(..., description="Human-readable event description")


class EcosystemServiceStatus(WebSocketMessage):
    """Ecosystem service status update message."""
    type: str = "ecosystem_status"
    service_name: str = Field(..., description="Service name")
    service_status: str = Field(..., description="Service status (healthy/unhealthy)")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")


class WebSocketConnectionManager:
    """WebSocket connection manager for simulation updates."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.logger = get_simulation_logger()

    async def connect(self, websocket: WebSocket, simulation_id: Optional[str] = None) -> None:
        """Connect a WebSocket client."""
        await websocket.accept()

        # Use simulation_id as key, or "general" for general updates
        key = simulation_id or "general"

        if key not in self.active_connections:
            self.active_connections[key] = set()

        self.active_connections[key].add(websocket)

        self.logger.info(
            "WebSocket client connected",
            simulation_id=simulation_id,
            total_connections=sum(len(conns) for conns in self.active_connections.values())
        )

        # Send welcome message
        await self._send_to_websocket(
            websocket,
            WebSocketMessage(
                type="connection_established",
                data={"message": "Connected to simulation updates"}
            )
        )

    async def disconnect(self, websocket: WebSocket, simulation_id: Optional[str] = None) -> None:
        """Disconnect a WebSocket client."""
        key = simulation_id or "general"

        if key in self.active_connections:
            self.active_connections[key].discard(websocket)

            # Clean up empty sets
            if not self.active_connections[key]:
                del self.active_connections[key]

        self.logger.info(
            "WebSocket client disconnected",
            simulation_id=simulation_id,
            remaining_connections=sum(len(conns) for conns in self.active_connections.values())
        )

    async def broadcast_to_simulation(self, simulation_id: str, message: WebSocketMessage) -> None:
        """Broadcast message to all clients watching a specific simulation."""
        if simulation_id in self.active_connections:
            await self._broadcast_to_connections(
                self.active_connections[simulation_id],
                message
            )

    async def broadcast_general(self, message: WebSocketMessage) -> None:
        """Broadcast message to all general clients."""
        if "general" in self.active_connections:
            await self._broadcast_to_connections(
                self.active_connections["general"],
                message
            )

    async def broadcast_all(self, message: WebSocketMessage) -> None:
        """Broadcast message to all connected clients."""
        all_connections = set()
        for connections in self.active_connections.values():
            all_connections.update(connections)

        await self._broadcast_to_connections(all_connections, message)

    async def _broadcast_to_connections(self, connections: Set[WebSocket], message: WebSocketMessage) -> None:
        """Broadcast message to a set of connections."""
        if not connections:
            return

        # Create JSON message
        message_dict = message.dict()
        json_message = json.dumps(message_dict, default=str)

        # Send to all connections
        tasks = []
        for connection in connections:
            tasks.append(self._send_json_to_websocket(connection, json_message))

        # Execute all sends concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any failures
        failed_count = sum(1 for result in results if isinstance(result, Exception))
        if failed_count > 0:
            self.logger.warning(
                "Some WebSocket messages failed to send",
                total_connections=len(connections),
                failed_count=failed_count
            )

    async def _send_json_to_websocket(self, websocket: WebSocket, json_message: str) -> None:
        """Send JSON message to a WebSocket."""
        try:
            await websocket.send_text(json_message)
        except Exception as e:
            self.logger.warning(
                "Failed to send WebSocket message",
                error=str(e)
            )
            # Remove failed connection
            for key, connections in self.active_connections.items():
                connections.discard(websocket)
                if not connections:
                    del self.active_connections[key]
                    break

    async def _send_to_websocket(self, websocket: WebSocket, message: WebSocketMessage) -> None:
        """Send message to a single WebSocket."""
        try:
            message_dict = message.dict()
            json_message = json.dumps(message_dict, default=str)
            await websocket.send_text(json_message)
        except Exception as e:
            self.logger.warning(
                "Failed to send WebSocket message",
                error=str(e)
            )


class SimulationWebSocketHandler:
    """Handler for simulation WebSocket connections and events."""

    def __init__(self):
        """Initialize WebSocket handler."""
        self.connection_manager = WebSocketConnectionManager()
        self.logger = get_simulation_logger()
        self._event_subscription_id = None

    async def handle_simulation_connection(self, websocket: WebSocket, simulation_id: str) -> None:
        """Handle WebSocket connection for a specific simulation."""
        await self.connection_manager.connect(websocket, simulation_id)

        try:
            # Subscribe to simulation-specific events
            await self._subscribe_to_simulation_events(simulation_id)

            # Send initial simulation status
            await self._send_initial_simulation_status(websocket, simulation_id)

            # Keep connection alive and handle client messages
            while True:
                # Wait for client messages (ping/pong, subscription changes, etc.)
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                    # Handle client message
                    await self._handle_client_message(websocket, simulation_id, data)

                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket.send_text(json.dumps({"type": "ping"}))
                    continue

        except WebSocketDisconnect:
            self.logger.info(
                "WebSocket disconnected for simulation",
                simulation_id=simulation_id
            )
        except Exception as e:
            self.logger.error(
                "Error in simulation WebSocket handler",
                error=str(e),
                simulation_id=simulation_id
            )
        finally:
            await self.connection_manager.disconnect(websocket, simulation_id)

    async def handle_general_connection(self, websocket: WebSocket) -> None:
        """Handle general WebSocket connection for system-wide updates."""
        await self.connection_manager.connect(websocket, "general")

        try:
            # Subscribe to general system events
            await self._subscribe_to_general_events()

            # Send initial system status
            await self._send_initial_system_status(websocket)

            # Keep connection alive
            while True:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    await self._handle_client_message(websocket, "general", data)

                except asyncio.TimeoutError:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                    continue

        except WebSocketDisconnect:
            self.logger.info("General WebSocket disconnected")
        except Exception as e:
            self.logger.error(
                "Error in general WebSocket handler",
                error=str(e)
            )
        finally:
            await self.connection_manager.disconnect(websocket, "general")

    async def notify_simulation_progress(self, simulation_id: str, progress_data: Dict[str, Any]) -> None:
        """Notify clients about simulation progress updates."""
        message = SimulationProgressUpdate(
            simulation_id=simulation_id,
            progress_percentage=progress_data.get("progress_percentage", 0.0),
            current_phase=progress_data.get("current_phase"),
            status=progress_data.get("status", "unknown"),
            estimated_completion=progress_data.get("estimated_completion"),
            data=progress_data
        )

        await self.connection_manager.broadcast_to_simulation(simulation_id, message)

    async def notify_simulation_event(self, simulation_id: str, event: DomainEvent) -> None:
        """Notify clients about simulation domain events."""
        message = SimulationEventNotification(
            simulation_id=simulation_id,
            event_type=event.event_type,
            event_description=self._get_event_description(event),
            data={
                "event_id": getattr(event, 'event_id', 'unknown'),
                "occurred_at": getattr(event, 'timestamp', datetime.now().isoformat()),
                "aggregate_id": getattr(event, 'aggregate_id', 'unknown')
            }
        )

        await self.connection_manager.broadcast_to_simulation(simulation_id, message)

    async def notify_simulation_event_dict(self, simulation_id: str, event_data: Dict[str, Any]) -> None:
        """Notify clients about simulation events using dictionary data."""
        message = SimulationEventNotification(
            simulation_id=simulation_id,
            event_type=event_data.get("event_type", "custom_event"),
            event_description=f"Event: {event_data.get('event_type', 'unknown')}",
            data=event_data
        )

        await self.connection_manager.broadcast_to_simulation(simulation_id, message)

    async def notify_ecosystem_status(self, service_name: str, status: str, response_time: Optional[float] = None) -> None:
        """Notify clients about ecosystem service status changes."""
        message = EcosystemServiceStatus(
            service_name=service_name,
            service_status=status,
            response_time_ms=response_time,
            data={
                "timestamp": datetime.now().isoformat(),
                "service": service_name,
                "status": status
            }
        )

        await self.connection_manager.broadcast_general(message)

    async def _subscribe_to_simulation_events(self, simulation_id: str) -> None:
        """Subscribe to simulation-specific domain events."""
        # This would integrate with the domain event system
        # For now, we'll set up a placeholder
        self.logger.info(
            "Subscribed to simulation events",
            simulation_id=simulation_id
        )

    async def _subscribe_to_general_events(self) -> None:
        """Subscribe to general system events."""
        self.logger.info("Subscribed to general system events")

    async def _send_initial_simulation_status(self, websocket: WebSocket, simulation_id: str) -> None:
        """Send initial simulation status to newly connected client."""
        try:
            # Get simulation status from application service
            container = get_simulation_container()
            application_service = container.simulation_application_service

            result = await application_service.get_simulation_status(simulation_id)

            if result["success"]:
                message = SimulationProgressUpdate(
                    simulation_id=simulation_id,
                    progress_percentage=result.get("progress", 0.0),
                    current_phase=result.get("current_phase", "Unknown"),
                    status=result.get("status", "unknown"),
                    data=result
                )
                await self.connection_manager._send_to_websocket(websocket, message)
            else:
                await self.connection_manager._send_to_websocket(
                    websocket,
                    WebSocketMessage(
                        type="simulation_not_found",
                        simulation_id=simulation_id,
                        data={"error": result.get("error", "Simulation not found")}
                    )
                )

        except Exception as e:
            self.logger.error(
                "Failed to send initial simulation status",
                error=str(e),
                simulation_id=simulation_id
            )

    async def _send_initial_system_status(self, websocket: WebSocket) -> None:
        """Send initial system status to newly connected client."""
        try:
            # Get health status from health manager
            container = get_simulation_container()
            health_manager = container.health_manager

            health_result = await health_manager.simulation_health()

            message = WebSocketMessage(
                type="system_status",
                data={
                    "health": health_result,
                    "timestamp": datetime.now().isoformat()
                }
            )

            await self.connection_manager._send_to_websocket(websocket, message)

        except Exception as e:
            self.logger.error(
                "Failed to send initial system status",
                error=str(e)
            )

    async def _handle_client_message(self, websocket: WebSocket, context: str, data: str) -> None:
        """Handle incoming client messages."""
        try:
            message_data = json.loads(data)
            message_type = message_data.get("type", "unknown")

            if message_type == "ping":
                # Respond to ping
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message_type == "subscribe":
                # Handle subscription changes
                simulation_id = message_data.get("simulation_id")
                if simulation_id and context != simulation_id:
                    # Client wants to switch simulations
                    await self.connection_manager.disconnect(websocket, context)
                    await self.connection_manager.connect(websocket, simulation_id)
            elif message_type == "unsubscribe":
                # Handle unsubscribe
                await websocket.send_text(json.dumps({
                    "type": "unsubscribed",
                    "context": context
                }))
            else:
                self.logger.debug(
                    "Received unknown client message",
                    message_type=message_type,
                    context=context
                )

        except json.JSONDecodeError:
            self.logger.warning(
                "Received invalid JSON from client",
                context=context,
                data=data[:100]  # Log first 100 chars
            )
        except Exception as e:
            self.logger.error(
                "Error handling client message",
                error=str(e),
                context=context
            )

    def _get_event_description(self, event: DomainEvent) -> str:
        """Get human-readable description for a domain event."""
        event_type = event.event_type

        descriptions = {
            "ProjectCreated": "New project was created",
            "ProjectStatusChanged": "Project status was updated",
            "ProjectUpdated": "Project details were modified",
            "SimulationStarted": "Simulation execution began",
            "SimulationCompleted": "Simulation finished successfully",
            "SimulationFailed": "Simulation encountered an error",
            "DocumentGenerated": "New document was generated",
            "WorkflowExecuted": "Workflow completed execution",
            "PhaseStarted": "Project phase began",
            "PhaseCompleted": "Project phase finished"
        }

        return descriptions.get(event_type, f"Event: {event_type}")


# Global WebSocket handler instance
_websocket_handler: Optional[SimulationWebSocketHandler] = None


def get_websocket_handler() -> SimulationWebSocketHandler:
    """Get the global WebSocket handler instance."""
    global _websocket_handler
    if _websocket_handler is None:
        _websocket_handler = SimulationWebSocketHandler()
    return _websocket_handler


# Convenience functions for external use
async def notify_simulation_progress(simulation_id: str, progress_data: Dict[str, Any]) -> None:
    """Notify clients about simulation progress updates."""
    handler = get_websocket_handler()
    await handler.notify_simulation_progress(simulation_id, progress_data)


async def notify_simulation_event(simulation_id: str, event: DomainEvent) -> None:
    """Notify clients about simulation domain events."""
    handler = get_websocket_handler()
    await handler.notify_simulation_event(simulation_id, event)


async def notify_simulation_event_dict(simulation_id: str, event_data: Dict[str, Any]) -> None:
    """Notify clients about simulation events using dictionary data."""
    handler = get_websocket_handler()
    await handler.notify_simulation_event_dict(simulation_id, event_data)


async def notify_ecosystem_status(service_name: str, status: str, response_time: Optional[float] = None) -> None:
    """Notify clients about ecosystem service status changes."""
    handler = get_websocket_handler()
    await handler.notify_ecosystem_status(service_name, status, response_time)


__all__ = [
    'WebSocketMessage',
    'SimulationProgressUpdate',
    'SimulationEventNotification',
    'EcosystemServiceStatus',
    'WebSocketConnectionManager',
    'SimulationWebSocketHandler',
    'get_websocket_handler',
    'notify_simulation_progress',
    'notify_simulation_event',
    'notify_simulation_event_dict',
    'notify_ecosystem_status'
]
