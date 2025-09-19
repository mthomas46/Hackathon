"""WebSocket Client for Real-Time Simulation Updates.

This module provides WebSocket client functionality for receiving real-time
updates from the project-simulation service, including progress updates,
event notifications, and ecosystem status changes.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime
import threading
import time

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

from infrastructure.config.config import WebSocketConfig, get_config
from infrastructure.logging.logger import get_dashboard_logger


class WebSocketClientError(Exception):
    """Base exception for WebSocket client errors."""
    pass


class WebSocketClient:
    """WebSocket client for real-time simulation updates."""

    def __init__(self, config: WebSocketConfig):
        """Initialize the WebSocket client."""
        if not WEBSOCKETS_AVAILABLE:
            raise WebSocketClientError("websockets package is required for WebSocket functionality")

        self.config = config
        self.logger = get_dashboard_logger("websocket_client")

        # Connection state
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        self.reconnect_task: Optional[asyncio.Task] = None

        # Event handlers
        self.message_handlers: Dict[str, Set[Callable]] = {}
        self.error_handlers: Set[Callable] = set()
        self.connection_handlers: Set[Callable] = set()

        # Message queue for thread safety
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None

        # Configuration from simulation service
        dashboard_config = get_config()
        self.ws_base_url = dashboard_config.simulation_service.base_url.replace("http", "ws")

    def add_message_handler(self, message_type: str, handler: Callable) -> None:
        """Add a message handler for a specific message type."""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = set()
        self.message_handlers[message_type].add(handler)

    def remove_message_handler(self, message_type: str, handler: Callable) -> None:
        """Remove a message handler."""
        if message_type in self.message_handlers:
            self.message_handlers[message_type].discard(handler)
            if not self.message_handlers[message_type]:
                del self.message_handlers[message_type]

    def add_error_handler(self, handler: Callable) -> None:
        """Add an error handler."""
        self.error_handlers.add(handler)

    def remove_error_handler(self, handler: Callable) -> None:
        """Remove an error handler."""
        self.error_handlers.discard(handler)

    def add_connection_handler(self, handler: Callable) -> None:
        """Add a connection state change handler."""
        self.connection_handlers.add(handler)

    def remove_connection_handler(self, handler: Callable) -> None:
        """Remove a connection handler."""
        self.connection_handlers.discard(handler)

    async def connect(self, simulation_id: Optional[str] = None) -> None:
        """Connect to the WebSocket endpoint."""
        if self.connected:
            return

        endpoint = f"/ws/simulations/{simulation_id}" if simulation_id else "/ws/system"
        ws_url = f"{self.ws_base_url}{endpoint}"

        try:
            self.logger.info(f"Connecting to WebSocket: {ws_url}")
            self.websocket = await websockets.connect(ws_url)
            self.connected = True

            # Start message processing
            self.processing_task = asyncio.create_task(self._process_messages())

            # Notify connection handlers
            for handler in self.connection_handlers:
                try:
                    await handler(True, simulation_id)
                except Exception as e:
                    self.logger.error(f"Error in connection handler: {str(e)}")

            # Start heartbeat
            asyncio.create_task(self._heartbeat())

        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {str(e)}")
            self.connected = False
            raise WebSocketClientError(f"Connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket."""
        if not self.connected:
            return

        try:
            if self.websocket:
                await self.websocket.close()
            self.connected = False

            # Cancel processing task
            if self.processing_task and not self.processing_task.done():
                self.processing_task.cancel()

            # Notify connection handlers
            for handler in self.connection_handlers:
                try:
                    await handler(False, None)
                except Exception as e:
                    self.logger.error(f"Error in disconnection handler: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error during disconnect: {str(e)}")

    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message through the WebSocket."""
        if not self.connected or not self.websocket:
            raise WebSocketClientError("WebSocket not connected")

        try:
            json_message = json.dumps(message)
            await self.websocket.send(json_message)
            self.logger.log_websocket_message("sent", message.get("simulation_id"))
        except Exception as e:
            self.logger.error(f"Error sending WebSocket message: {str(e)}")
            raise WebSocketClientError(f"Send failed: {str(e)}")

    async def subscribe_to_simulation(self, simulation_id: str) -> None:
        """Subscribe to updates for a specific simulation."""
        await self.send_message({
            "type": "subscribe",
            "simulation_id": simulation_id
        })

    async def unsubscribe_from_simulation(self, simulation_id: str) -> None:
        """Unsubscribe from updates for a specific simulation."""
        await self.send_message({
            "type": "unsubscribe",
            "simulation_id": simulation_id
        })

    async def send_ping(self) -> None:
        """Send a ping message."""
        await self.send_message({"type": "ping"})

    async def _process_messages(self) -> None:
        """Process incoming WebSocket messages."""
        try:
            while self.connected and self.websocket:
                try:
                    # Receive message with timeout
                    message_raw = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=self.config.message_timeout
                    )

                    # Parse message
                    message_data = json.loads(message_raw)
                    message_type = message_data.get("type", "unknown")

                    self.logger.log_websocket_message(
                        message_type,
                        message_data.get("simulation_id")
                    )

                    # Handle message
                    await self._handle_message(message_data)

                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await self.send_ping()
                    continue

                except websockets.exceptions.ConnectionClosed:
                    self.logger.info("WebSocket connection closed")
                    break

        except Exception as e:
            self.logger.error(f"Error in message processing: {str(e)}")
            # Notify error handlers
            for handler in self.error_handlers:
                try:
                    await handler(e)
                except Exception as handler_error:
                    self.logger.error(f"Error in error handler: {str(handler_error)}")

        finally:
            self.connected = False

    async def _handle_message(self, message_data: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message."""
        message_type = message_data.get("type", "unknown")

        # Handle pong responses
        if message_type == "pong":
            return

        # Handle connection established
        if message_type == "connection_established":
            self.logger.info("WebSocket connection established")
            return

        # Route to specific handlers
        if message_type in self.message_handlers:
            for handler in self.message_handlers[message_type]:
                try:
                    await handler(message_data)
                except Exception as e:
                    self.logger.error(f"Error in message handler for {message_type}: {str(e)}")

    async def _heartbeat(self) -> None:
        """Send periodic heartbeat messages."""
        while self.connected:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                if self.connected:
                    await self.send_ping()
            except Exception as e:
                self.logger.error(f"Heartbeat error: {str(e)}")
                break

    async def _reconnect(self) -> None:
        """Attempt to reconnect to WebSocket."""
        for attempt in range(self.config.reconnect_attempts):
            try:
                self.logger.info(f"Reconnection attempt {attempt + 1}/{self.config.reconnect_attempts}")
                await asyncio.sleep(self.config.reconnect_delay * (attempt + 1))
                await self.connect()
                self.logger.info("Reconnection successful")
                return
            except Exception as e:
                self.logger.warning(f"Reconnection attempt {attempt + 1} failed: {str(e)}")

        self.logger.error("All reconnection attempts failed")

    def start_auto_reconnect(self, simulation_id: Optional[str] = None) -> None:
        """Start automatic reconnection in background."""
        if self.reconnect_task and not self.reconnect_task.done():
            return

        async def reconnect_loop():
            while True:
                if not self.connected:
                    try:
                        await self._reconnect()
                        if self.connected and simulation_id:
                            await self.subscribe_to_simulation(simulation_id)
                    except Exception as e:
                        self.logger.error(f"Reconnection failed: {str(e)}")

                await asyncio.sleep(5)  # Check every 5 seconds

        self.reconnect_task = asyncio.create_task(reconnect_loop())

    def stop_auto_reconnect(self) -> None:
        """Stop automatic reconnection."""
        if self.reconnect_task and not self.reconnect_task.done():
            self.reconnect_task.cancel()


class SimulationWebSocketManager:
    """Manager for multiple WebSocket connections."""

    def __init__(self):
        """Initialize the WebSocket manager."""
        self.clients: Dict[str, WebSocketClient] = {}
        self.logger = get_dashboard_logger("websocket_manager")

    def get_client(self, simulation_id: Optional[str] = None) -> WebSocketClient:
        """Get or create a WebSocket client."""
        key = simulation_id or "system"

        if key not in self.clients:
            config = get_config()
            self.clients[key] = WebSocketClient(config.websocket)

        return self.clients[key]

    async def connect_simulation(self, simulation_id: str) -> WebSocketClient:
        """Connect to a simulation's WebSocket."""
        client = self.get_client(simulation_id)
        await client.connect(simulation_id)
        await client.subscribe_to_simulation(simulation_id)
        return client

    async def connect_system(self) -> WebSocketClient:
        """Connect to system WebSocket."""
        client = self.get_client("system")
        await client.connect()
        return client

    async def disconnect_all(self) -> None:
        """Disconnect all WebSocket clients."""
        for client in self.clients.values():
            try:
                await client.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting client: {str(e)}")

        self.clients.clear()

    def setup_event_handlers(self, simulation_id: Optional[str] = None):
        """Setup event handlers for real-time updates."""
        client = self.get_client(simulation_id)

        # Import here to avoid circular imports
        from pages.monitor import handle_simulation_progress, handle_simulation_event, handle_websocket_connected

        # Setup message handlers
        client.add_message_handler("simulation_progress", handle_simulation_progress)
        client.add_message_handler("simulation_event", handle_simulation_event)

        # Setup connection handlers
        client.add_connection_handler(handle_websocket_connected)

        # Setup error handler
        def handle_error(error):
            self.logger.error(f"WebSocket error: {str(error)}")

        client.add_error_handler(handle_error)

        return client

    async def start_realtime_updates(self, simulation_id: Optional[str] = None):
        """Start real-time updates for monitoring."""
        try:
            client = self.setup_event_handlers(simulation_id)

            if simulation_id:
                await self.connect_simulation(simulation_id)
            else:
                await self.connect_system()

            # Start auto-reconnect
            client.start_auto_reconnect(simulation_id)

            self.logger.info(f"Real-time updates started for {'simulation ' + simulation_id if simulation_id else 'system'}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start real-time updates: {str(e)}")
            return False

    def stop_realtime_updates(self, simulation_id: Optional[str] = None):
        """Stop real-time updates."""
        client = self.get_client(simulation_id)
        client.stop_auto_reconnect()

        # Disconnect
        asyncio.create_task(client.disconnect())

        self.logger.info(f"Real-time updates stopped for {'simulation ' + simulation_id if simulation_id else 'system'}")


# Global WebSocket manager instance
_websocket_manager: Optional[SimulationWebSocketManager] = None


def get_websocket_manager() -> SimulationWebSocketManager:
    """Get the global WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = SimulationWebSocketManager()
    return _websocket_manager
