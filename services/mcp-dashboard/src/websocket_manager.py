"""WebSocket manager for real-time updates."""

import asyncio
import websockets
import json
from typing import Dict, Set, Callable, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time dashboard updates.
    
    Provides:
    - Training job progress streaming
    - MCP health status updates
    - Query result streaming
    - System metric updates
    """
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.connections: Set[websockets.WebSocketServerProtocol] = set()
        self.subscribers: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
        self.running = False
    
    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        self.connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.connections)}")
        
        try:
            await websocket.send(json.dumps({
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error sending connection message: {e}")
    
    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """
        Unregister a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        self.connections.discard(websocket)
        
        # Remove from all subscriptions
        for topic in self.subscribers:
            self.subscribers[topic].discard(websocket)
        
        logger.info(f"WebSocket disconnected. Total: {len(self.connections)}")
    
    async def subscribe(
        self,
        websocket: websockets.WebSocketServerProtocol,
        topic: str
    ):
        """
        Subscribe a connection to a topic.
        
        Args:
            websocket: WebSocket connection
            topic: Topic to subscribe to (e.g., "training_progress", "mcp_health")
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = set()
        
        self.subscribers[topic].add(websocket)
        logger.info(f"WebSocket subscribed to {topic}")
        
        await websocket.send(json.dumps({
            "type": "subscription",
            "topic": topic,
            "status": "subscribed"
        }))
    
    async def unsubscribe(
        self,
        websocket: websockets.WebSocketServerProtocol,
        topic: str
    ):
        """
        Unsubscribe a connection from a topic.
        
        Args:
            websocket: WebSocket connection
            topic: Topic to unsubscribe from
        """
        if topic in self.subscribers:
            self.subscribers[topic].discard(websocket)
            logger.info(f"WebSocket unsubscribed from {topic}")
    
    async def broadcast(self, message: Dict[str, Any], topic: Optional[str] = None):
        """
        Broadcast a message to all connections or topic subscribers.
        
        Args:
            message: Message to broadcast
            topic: Optional topic for targeted broadcast
        """
        message_json = json.dumps(message)
        
        # Get target connections
        if topic and topic in self.subscribers:
            targets = self.subscribers[topic]
        else:
            targets = self.connections
        
        # Send to all targets
        disconnected = set()
        for websocket in targets:
            try:
                await websocket.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected
        for websocket in disconnected:
            await self.unregister(websocket)
    
    async def send_training_progress(
        self,
        job_id: str,
        percent: int,
        stage: str,
        message: str
    ):
        """
        Send training job progress update.
        
        Args:
            job_id: Training job ID
            percent: Progress percentage (0-100)
            stage: Current stage
            message: Status message
        """
        await self.broadcast({
            "type": "training_progress",
            "job_id": job_id,
            "percent": percent,
            "stage": stage,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }, topic="training_progress")
    
    async def send_mcp_health(
        self,
        mcp_id: str,
        status: str,
        health_data: Dict[str, Any]
    ):
        """
        Send MCP health status update.
        
        Args:
            mcp_id: MCP instance ID
            status: Health status
            health_data: Detailed health data
        """
        await self.broadcast({
            "type": "mcp_health",
            "mcp_id": mcp_id,
            "status": status,
            "data": health_data,
            "timestamp": datetime.now().isoformat()
        }, topic="mcp_health")
    
    async def send_query_result(
        self,
        query_id: str,
        result: Dict[str, Any]
    ):
        """
        Send query execution result.
        
        Args:
            query_id: Query ID
            result: Query result data
        """
        await self.broadcast({
            "type": "query_result",
            "query_id": query_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }, topic="query_results")
    
    async def send_system_metrics(self, metrics: Dict[str, Any]):
        """
        Send system metrics update.
        
        Args:
            metrics: System metrics data
        """
        await self.broadcast({
            "type": "system_metrics",
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }, topic="system_metrics")
    
    async def handle_client_message(
        self,
        websocket: websockets.WebSocketServerProtocol,
        message: str
    ):
        """
        Handle incoming message from client.
        
        Args:
            websocket: WebSocket connection
            message: Message from client
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                topic = data.get("topic")
                if topic:
                    await self.subscribe(websocket, topic)
            
            elif message_type == "unsubscribe":
                topic = data.get("topic")
                if topic:
                    await self.unsubscribe(websocket, topic)
            
            elif message_type == "ping":
                await websocket.send(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message: {message}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8016):
        """
        Start WebSocket server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.running = True
        
        async def handler(websocket, path):
            await self.register(websocket)
            try:
                async for message in websocket:
                    await self.handle_client_message(websocket, message)
            finally:
                await self.unregister(websocket)
        
        async with websockets.serve(handler, host, port):
            logger.info(f"WebSocket server started on {host}:{port}")
            await asyncio.Future()  # Run forever
    
    def stop(self):
        """Stop WebSocket server."""
        self.running = False


# Global WebSocket manager instance
ws_manager = WebSocketManager()

