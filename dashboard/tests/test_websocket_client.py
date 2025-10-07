"""
Tests for WebSocket client functionality.

These tests verify the WebSocket client can connect, receive events,
and dispatch to registered handlers correctly.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.websocket_client import (
    WebSocketClient,
    WebSocketEventType,
    StreamlitWebSocketManager,
)


@pytest.fixture
def mock_base_urls():
    """Fixture providing test WebSocket URLs."""
    return {
        "performance_store": "ws://localhost:5649/ws",
        "mcp_store": "ws://localhost:5648/ws",
    }


@pytest.fixture
def websocket_client(mock_base_urls):
    """Fixture providing WebSocket client instance."""
    return WebSocketClient(mock_base_urls)


@pytest.mark.asyncio
async def test_websocket_client_initialization(mock_base_urls):
    """Test WebSocket client initializes correctly."""
    client = WebSocketClient(mock_base_urls)
    
    assert client.base_urls == mock_base_urls
    assert len(client.connections) == 0
    assert client.is_running is False
    assert all(isinstance(handlers, list) for handlers in client.event_handlers.values())


@pytest.mark.asyncio
async def test_register_handler(websocket_client):
    """Test registering event handlers."""
    mock_handler = Mock()
    
    websocket_client.register_handler(WebSocketEventType.EXECUTION_COMPLETED, mock_handler)
    
    handlers = websocket_client.event_handlers[WebSocketEventType.EXECUTION_COMPLETED]
    assert mock_handler in handlers


@pytest.mark.asyncio
async def test_unregister_handler(websocket_client):
    """Test unregistering event handlers."""
    mock_handler = Mock()
    
    websocket_client.register_handler(WebSocketEventType.EXECUTION_COMPLETED, mock_handler)
    websocket_client.unregister_handler(WebSocketEventType.EXECUTION_COMPLETED, mock_handler)
    
    handlers = websocket_client.event_handlers[WebSocketEventType.EXECUTION_COMPLETED]
    assert mock_handler not in handlers


@pytest.mark.asyncio
async def test_handle_event_with_handler(websocket_client):
    """Test event handling with registered handler."""
    mock_handler = Mock()
    websocket_client.register_handler(WebSocketEventType.EXECUTION_COMPLETED, mock_handler)
    
    event_data = {
        "event_type": "execution_completed",
        "execution_id": "test-123",
        "status": "success"
    }
    
    await websocket_client.handle_event(event_data)
    
    mock_handler.assert_called_once_with(event_data)


@pytest.mark.asyncio
async def test_handle_event_async_handler(websocket_client):
    """Test event handling with async handler."""
    mock_handler = AsyncMock()
    websocket_client.register_handler(WebSocketEventType.EXECUTION_COMPLETED, mock_handler)
    
    event_data = {
        "event_type": "execution_completed",
        "execution_id": "test-123",
        "status": "success"
    }
    
    await websocket_client.handle_event(event_data)
    
    mock_handler.assert_awaited_once_with(event_data)


@pytest.mark.asyncio
async def test_handle_event_unknown_type(websocket_client):
    """Test handling event with unknown type."""
    mock_handler = Mock()
    websocket_client.register_handler(WebSocketEventType.EXECUTION_COMPLETED, mock_handler)
    
    event_data = {
        "event_type": "unknown_event_type",
        "data": "test"
    }
    
    # Should not raise exception
    await websocket_client.handle_event(event_data)
    
    # Handler should not be called
    mock_handler.assert_not_called()


@pytest.mark.asyncio
async def test_handle_event_missing_type(websocket_client):
    """Test handling event without event_type field."""
    mock_handler = Mock()
    websocket_client.register_handler(WebSocketEventType.EXECUTION_COMPLETED, mock_handler)
    
    event_data = {
        "data": "test"
    }
    
    # Should not raise exception
    await websocket_client.handle_event(event_data)
    
    # Handler should not be called
    mock_handler.assert_not_called()


@pytest.mark.asyncio
async def test_handle_event_multiple_handlers(websocket_client):
    """Test event dispatches to multiple handlers."""
    mock_handler1 = Mock()
    mock_handler2 = Mock()
    
    websocket_client.register_handler(WebSocketEventType.EXECUTION_COMPLETED, mock_handler1)
    websocket_client.register_handler(WebSocketEventType.EXECUTION_COMPLETED, mock_handler2)
    
    event_data = {
        "event_type": "execution_completed",
        "execution_id": "test-123"
    }
    
    await websocket_client.handle_event(event_data)
    
    mock_handler1.assert_called_once_with(event_data)
    mock_handler2.assert_called_once_with(event_data)


@pytest.mark.asyncio
async def test_is_connected(websocket_client):
    """Test connection status check."""
    # Initially not connected
    assert websocket_client.is_connected("performance_store") is False
    
    # Mock a connection
    mock_connection = Mock()
    mock_connection.closed = False
    websocket_client.connections["performance_store"] = mock_connection
    
    assert websocket_client.is_connected("performance_store") is True
    
    # Test closed connection
    mock_connection.closed = True
    assert websocket_client.is_connected("performance_store") is False


@pytest.mark.asyncio
async def test_streamlit_websocket_manager():
    """Test Streamlit WebSocket manager."""
    manager = StreamlitWebSocketManager()
    
    assert manager.client is not None
    assert manager.is_started is False
    assert manager.has_events() is False


@pytest.mark.asyncio
async def test_streamlit_manager_event_queue():
    """Test Streamlit manager event queuing."""
    manager = StreamlitWebSocketManager()
    
    # Register handler for test event type
    manager.register_event_handler(WebSocketEventType.EXECUTION_COMPLETED)
    
    # Simulate event
    event_data = {
        "event_type": "execution_completed",
        "execution_id": "test-123"
    }
    
    await manager.client.handle_event(event_data)
    
    # Check event was queued
    assert manager.has_events() is True
    
    events = manager.get_recent_events()
    assert len(events) == 1
    assert events[0] == event_data


@pytest.mark.asyncio
async def test_streamlit_manager_get_recent_events_limit():
    """Test Streamlit manager respects event limit."""
    manager = StreamlitWebSocketManager()
    manager.register_event_handler(WebSocketEventType.EXECUTION_COMPLETED)
    
    # Queue multiple events
    for i in range(20):
        event_data = {
            "event_type": "execution_completed",
            "execution_id": f"test-{i}"
        }
        await manager.client.handle_event(event_data)
    
    # Get only 10 events
    events = manager.get_recent_events(max_count=10)
    assert len(events) == 10
    
    # Get remaining events
    remaining = manager.get_recent_events(max_count=20)
    assert len(remaining) == 10  # Should have 10 left


@pytest.mark.asyncio
async def test_event_type_enum():
    """Test WebSocketEventType enum values."""
    assert WebSocketEventType.EXECUTION_STARTED == "execution_started"
    assert WebSocketEventType.EXECUTION_COMPLETED == "execution_completed"
    assert WebSocketEventType.EXECUTION_FAILED == "execution_failed"
    assert WebSocketEventType.PERFORMANCE_UPDATE == "performance_update"
    assert WebSocketEventType.ANOMALY_DETECTED == "anomaly_detected"
    assert WebSocketEventType.PACKAGE_UPLOADED == "package_uploaded"
    assert WebSocketEventType.PACKAGE_DOWNLOADED == "package_downloaded"
    assert WebSocketEventType.SYSTEM_ALERT == "system_alert"

