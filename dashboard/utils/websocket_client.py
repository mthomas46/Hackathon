"""
WebSocket client for real-time updates from MCP services.

This module provides async WebSocket connections to receive real-time
notifications about execution status, performance metrics, and system events.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
import websockets
from websockets.exceptions import WebSocketException

logger = logging.getLogger(__name__)


class WebSocketEventType(str, Enum):
    """Types of WebSocket events."""
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    PERFORMANCE_UPDATE = "performance_update"
    ANOMALY_DETECTED = "anomaly_detected"
    PACKAGE_UPLOADED = "package_uploaded"
    PACKAGE_DOWNLOADED = "package_downloaded"
    SYSTEM_ALERT = "system_alert"


class WebSocketClient:
    """
    WebSocket client for receiving real-time updates from MCP services.
    
    This client maintains persistent connections to service WebSocket endpoints
    and dispatches events to registered handlers.
    """
    
    def __init__(self, base_urls: Dict[str, str]):
        """
        Initialize WebSocket client.
        
        Args:
            base_urls: Dictionary mapping service names to their WebSocket URLs
                      Example: {"performance_store": "ws://localhost:5649/ws"}
        """
        self.base_urls = base_urls
        self.connections: Dict[str, Optional[websockets.WebSocketClientProtocol]] = {}
        self.event_handlers: Dict[WebSocketEventType, List[Callable]] = {
            event_type: [] for event_type in WebSocketEventType
        }
        self.is_running = False
        self.tasks: List[asyncio.Task] = []
    
    def register_handler(self, event_type: WebSocketEventType, handler: Callable[[Dict[str, Any]], None]):
        """
        Register a callback handler for a specific event type.
        
        Args:
            event_type: Type of event to listen for
            handler: Callback function that accepts event data dict
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
    
    def unregister_handler(self, event_type: WebSocketEventType, handler: Callable):
        """Remove a registered handler."""
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
    
    async def connect(self, service_name: str):
        """
        Establish WebSocket connection to a service.
        
        Args:
            service_name: Name of the service to connect to
        """
        if service_name not in self.base_urls:
            logger.error(f"No WebSocket URL configured for service: {service_name}")
            return
        
        url = self.base_urls[service_name]
        try:
            connection = await websockets.connect(url, ping_interval=20, ping_timeout=10)
            self.connections[service_name] = connection
            logger.info(f"WebSocket connected to {service_name} at {url}")
        except Exception as e:
            logger.error(f"Failed to connect to {service_name} WebSocket: {e}")
            self.connections[service_name] = None
    
    async def disconnect(self, service_name: str):
        """
        Close WebSocket connection to a service.
        
        Args:
            service_name: Name of the service to disconnect from
        """
        if service_name in self.connections and self.connections[service_name]:
            try:
                await self.connections[service_name].close()
                logger.info(f"WebSocket disconnected from {service_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {service_name}: {e}")
            finally:
                self.connections[service_name] = None
    
    async def listen(self, service_name: str):
        """
        Listen for messages from a service WebSocket.
        
        Args:
            service_name: Name of the service to listen to
        """
        while self.is_running:
            connection = self.connections.get(service_name)
            
            if not connection:
                # Try to reconnect
                logger.warning(f"No connection to {service_name}, attempting to connect...")
                await self.connect(service_name)
                await asyncio.sleep(5)  # Wait before retrying
                continue
            
            try:
                message = await connection.recv()
                event_data = json.loads(message)
                await self.handle_event(event_data)
            
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"WebSocket connection to {service_name} closed, reconnecting...")
                self.connections[service_name] = None
                await asyncio.sleep(5)
            
            except Exception as e:
                logger.error(f"Error receiving message from {service_name}: {e}")
                await asyncio.sleep(1)
    
    async def handle_event(self, event_data: Dict[str, Any]):
        """
        Process received event and dispatch to registered handlers.
        
        Args:
            event_data: Event data dictionary with 'event_type' and other fields
        """
        event_type_str = event_data.get("event_type")
        
        if not event_type_str:
            logger.warning("Received event without event_type field")
            return
        
        try:
            event_type = WebSocketEventType(event_type_str)
        except ValueError:
            logger.warning(f"Unknown event type: {event_type_str}")
            return
        
        # Call all registered handlers for this event type
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                # Run handler (support both sync and async)
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def start(self):
        """Start all WebSocket listeners."""
        self.is_running = True
        
        # Connect to all services
        for service_name in self.base_urls.keys():
            await self.connect(service_name)
        
        # Start listener tasks for each service
        for service_name in self.base_urls.keys():
            task = asyncio.create_task(self.listen(service_name))
            self.tasks.append(task)
        
        logger.info(f"WebSocket client started with {len(self.tasks)} listeners")
    
    async def stop(self):
        """Stop all WebSocket listeners and close connections."""
        self.is_running = False
        
        # Cancel all listener tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Disconnect from all services
        for service_name in list(self.connections.keys()):
            await self.disconnect(service_name)
        
        logger.info("WebSocket client stopped")
    
    def is_connected(self, service_name: str) -> bool:
        """Check if connected to a service."""
        connection = self.connections.get(service_name)
        return connection is not None and not connection.closed


# Singleton WebSocket client instance
_websocket_client: Optional[WebSocketClient] = None


def get_websocket_client(base_urls: Optional[Dict[str, str]] = None) -> WebSocketClient:
    """
    Get or create singleton WebSocket client instance.
    
    Args:
        base_urls: Optional base URLs for services (only used on first call)
    
    Returns:
        WebSocketClient instance
    """
    global _websocket_client
    
    if _websocket_client is None:
        if base_urls is None:
            # Default URLs
            base_urls = {
                "performance_store": "ws://localhost:5649/ws",
                "mcp_store": "ws://localhost:5648/ws",
            }
        _websocket_client = WebSocketClient(base_urls)
    
    return _websocket_client


# Streamlit-compatible wrapper for WebSocket updates
class StreamlitWebSocketManager:
    """
    Manager for WebSocket updates in Streamlit applications.
    
    This class provides a Streamlit-friendly interface for receiving
    real-time updates without blocking the main thread.
    """
    
    def __init__(self):
        self.client = get_websocket_client()
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.is_started = False
    
    def register_event_handler(self, event_type: WebSocketEventType):
        """Register handler that queues events for Streamlit."""
        def handler(event_data: Dict[str, Any]):
            # Put event in queue for Streamlit to retrieve
            try:
                self.event_queue.put_nowait(event_data)
            except asyncio.QueueFull:
                # Queue full, drop oldest event
                try:
                    self.event_queue.get_nowait()
                    self.event_queue.put_nowait(event_data)
                except:
                    pass
        
        self.client.register_handler(event_type, handler)
    
    async def start(self):
        """Start WebSocket client."""
        if not self.is_started:
            await self.client.start()
            self.is_started = True
    
    async def stop(self):
        """Stop WebSocket client."""
        if self.is_started:
            await self.client.stop()
            self.is_started = False
    
    def get_recent_events(self, max_count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent events from queue (non-blocking).
        
        Args:
            max_count: Maximum number of events to retrieve
        
        Returns:
            List of event data dictionaries
        """
        events = []
        for _ in range(max_count):
            try:
                event = self.event_queue.get_nowait()
                events.append(event)
            except asyncio.QueueEmpty:
                break
        return events
    
    def has_events(self) -> bool:
        """Check if there are pending events."""
        return not self.event_queue.empty()

