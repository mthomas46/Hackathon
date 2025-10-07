"""Utility modules for the dashboard."""

from .websocket_client import (
    WebSocketClient,
    WebSocketEventType,
    StreamlitWebSocketManager,
    get_websocket_client,
)

__all__ = [
    "WebSocketClient",
    "WebSocketEventType",
    "StreamlitWebSocketManager",
    "get_websocket_client",
]

