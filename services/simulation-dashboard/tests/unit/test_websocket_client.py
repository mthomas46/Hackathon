"""Unit tests for WebSocket client."""

import pytest
import asyncio
import json
from unittest.mock import Mock, MagicMock, AsyncMock, patch, call
from websockets.exceptions import ConnectionClosedError, WebSocketException

from services.clients.websocket_client import (
    WebSocketClient, SimulationWebSocketManager,
    WebSocketClientError, WebSocketConnectionError
)


class TestWebSocketClient:
    """Test cases for WebSocketClient."""

    @pytest.fixture
    def config(self):
        """Create a mock WebSocket configuration."""
        config = MagicMock()
        config.websocket.enabled = True
        config.websocket.reconnect_attempts = 3
        config.websocket.heartbeat_interval = 30.0
        config.websocket.message_timeout = 10.0
        return config

    @pytest.fixture
    def websocket_client(self, config):
        """Create a WebSocketClient instance for testing."""
        return WebSocketClient(config.websocket)

    @pytest.mark.asyncio
    async def test_client_initialization(self, websocket_client):
        """Test client initialization."""
        assert websocket_client.enabled is True
        assert websocket_client.reconnect_attempts == 3
        assert websocket_client.heartbeat_interval == 30.0
        assert websocket_client.message_timeout == 10.0
        assert websocket_client.websocket is None
        assert websocket_client.is_connected is False

    @pytest.mark.asyncio
    async def test_successful_connection(self, websocket_client):
        """Test successful WebSocket connection."""
        mock_websocket = AsyncMock()

        with patch('websockets.connect', return_value=mock_websocket) as mock_connect:
            await websocket_client.connect("ws://test-server:8080")

            assert websocket_client.is_connected is True
            assert websocket_client.websocket == mock_websocket
            mock_connect.assert_called_once_with(
                "ws://test-server:8080",
                extra_headers=None,
                ping_interval=30.0,
                close_timeout=10.0
            )

    @pytest.mark.asyncio
    async def test_connection_with_authentication(self, websocket_client):
        """Test WebSocket connection with authentication headers."""
        mock_websocket = AsyncMock()
        headers = {"Authorization": "Bearer token123"}

        with patch('websockets.connect', return_value=mock_websocket) as mock_connect:
            await websocket_client.connect("ws://test-server:8080", headers=headers)

            mock_connect.assert_called_once_with(
                "ws://test-server:8080",
                extra_headers=headers,
                ping_interval=30.0,
                close_timeout=10.0
            )

    @pytest.mark.asyncio
    async def test_connection_failure(self, websocket_client):
        """Test WebSocket connection failure."""
        with patch('websockets.connect', side_effect=WebSocketException("Connection failed")):
            with pytest.raises(WebSocketConnectionError) as exc_info:
                await websocket_client.connect("ws://test-server:8080")

            assert "Connection failed" in str(exc_info.value)
            assert websocket_client.is_connected is False

    @pytest.mark.asyncio
    async def test_connection_disabled(self, websocket_client):
        """Test behavior when WebSocket is disabled."""
        websocket_client.enabled = False

        await websocket_client.connect("ws://test-server:8080")

        # Should not attempt connection when disabled
        assert websocket_client.is_connected is False
        assert websocket_client.websocket is None

    @pytest.mark.asyncio
    async def test_disconnect(self, websocket_client):
        """Test WebSocket disconnection."""
        mock_websocket = AsyncMock()

        # Set up connected state
        websocket_client.websocket = mock_websocket
        websocket_client.is_connected = True

        await websocket_client.disconnect()

        assert websocket_client.is_connected is False
        assert websocket_client.websocket is None
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_with_exception(self, websocket_client):
        """Test WebSocket disconnection with exception."""
        mock_websocket = AsyncMock()
        mock_websocket.close.side_effect = WebSocketException("Close failed")

        # Set up connected state
        websocket_client.websocket = mock_websocket
        websocket_client.is_connected = True

        # Should not raise exception
        await websocket_client.disconnect()

        assert websocket_client.is_connected is False
        assert websocket_client.websocket is None

    @pytest.mark.asyncio
    async def test_send_message(self, websocket_client):
        """Test sending message via WebSocket."""
        mock_websocket = AsyncMock()

        # Set up connected state
        websocket_client.websocket = mock_websocket
        websocket_client.is_connected = True

        test_message = {"type": "test", "data": "hello"}
        await websocket_client.send_message(test_message)

        mock_websocket.send.assert_called_once_with(json.dumps(test_message))

    @pytest.mark.asyncio
    async def test_send_message_not_connected(self, websocket_client):
        """Test sending message when not connected."""
        test_message = {"type": "test", "data": "hello"}

        with pytest.raises(WebSocketClientError) as exc_info:
            await websocket_client.send_message(test_message)

        assert "not connected" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_message_exception(self, websocket_client):
        """Test sending message with exception."""
        mock_websocket = AsyncMock()
        mock_websocket.send.side_effect = WebSocketException("Send failed")

        # Set up connected state
        websocket_client.websocket = mock_websocket
        websocket_client.is_connected = True

        test_message = {"type": "test", "data": "hello"}

        with pytest.raises(WebSocketClientError) as exc_info:
            await websocket_client.send_message(test_message)

        assert "Send failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_receive_message(self, websocket_client):
        """Test receiving message via WebSocket."""
        mock_websocket = AsyncMock()
        mock_websocket.recv.return_value = '{"type": "test", "data": "hello"}'

        # Set up connected state
        websocket_client.websocket = mock_websocket
        websocket_client.is_connected = True

        message = await websocket_client.receive_message()

        assert message == {"type": "test", "data": "hello"}
        mock_websocket.recv.assert_called_once()

    @pytest.mark.asyncio
    async def test_receive_message_not_connected(self, websocket_client):
        """Test receiving message when not connected."""
        with pytest.raises(WebSocketClientError) as exc_info:
            await websocket_client.receive_message()

        assert "not connected" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_receive_message_connection_closed(self, websocket_client):
        """Test receiving message when connection is closed."""
        mock_websocket = AsyncMock()
        mock_websocket.recv.side_effect = ConnectionClosedError(1000, "Connection closed")

        # Set up connected state
        websocket_client.websocket = mock_websocket
        websocket_client.is_connected = True

        with pytest.raises(WebSocketConnectionError):
            await websocket_client.receive_message()

        # Should mark as disconnected
        assert websocket_client.is_connected is False

    @pytest.mark.asyncio
    async def test_subscribe_to_simulation(self, websocket_client):
        """Test subscribing to simulation events."""
        mock_websocket = AsyncMock()

        # Set up connected state
        websocket_client.websocket = mock_websocket
        websocket_client.is_connected = True

        simulation_id = "sim_001"
        await websocket_client.subscribe_to_simulation(simulation_id)

        expected_message = {
            "type": "subscribe",
            "simulation_id": simulation_id
        }
        mock_websocket.send.assert_called_once_with(json.dumps(expected_message))

    @pytest.mark.asyncio
    async def test_unsubscribe_from_simulation(self, websocket_client):
        """Test unsubscribing from simulation events."""
        mock_websocket = AsyncMock()

        # Set up connected state
        websocket_client.websocket = mock_websocket
        websocket_client.is_connected = True

        simulation_id = "sim_001"
        await websocket_client.unsubscribe_from_simulation(simulation_id)

        expected_message = {
            "type": "unsubscribe",
            "simulation_id": simulation_id
        }
        mock_websocket.send.assert_called_once_with(json.dumps(expected_message))

    @pytest.mark.asyncio
    async def test_auto_reconnect_setup(self, websocket_client):
        """Test auto-reconnect setup."""
        websocket_client.start_auto_reconnect("ws://test-server:8080")

        assert websocket_client.auto_reconnect_enabled is True
        assert websocket_client.reconnect_url == "ws://test-server:8080"

    @pytest.mark.asyncio
    async def test_auto_reconnect_stop(self, websocket_client):
        """Test stopping auto-reconnect."""
        websocket_client.start_auto_reconnect("ws://test-server:8080")
        websocket_client.stop_auto_reconnect()

        assert websocket_client.auto_reconnect_enabled is False

    def test_message_handlers(self, websocket_client):
        """Test message handler registration and management."""
        # Test adding handler
        def test_handler(message):
            return "handled"

        websocket_client.add_message_handler("test_type", test_handler)
        assert "test_type" in websocket_client.message_handlers
        assert websocket_client.message_handlers["test_type"] == test_handler

        # Test removing handler
        websocket_client.remove_message_handler("test_type")
        assert "test_type" not in websocket_client.message_handlers

    def test_connection_handlers(self, websocket_client):
        """Test connection handler registration and management."""
        # Test adding handler
        def test_handler():
            return "handled"

        websocket_client.add_connection_handler(test_handler)
        assert test_handler in websocket_client.connection_handlers

        # Test removing handler
        websocket_client.remove_connection_handler(test_handler)
        assert test_handler not in websocket_client.connection_handlers

    def test_error_handlers(self, websocket_client):
        """Test error handler registration and management."""
        # Test adding handler
        def test_handler(error):
            return "handled"

        websocket_client.add_error_handler(test_handler)
        assert test_handler in websocket_client.error_handlers

        # Test removing handler
        websocket_client.remove_error_handler(test_handler)
        assert test_handler not in websocket_client.error_handlers

    def test_connection_status_property(self, websocket_client):
        """Test connection status property."""
        # Initially not connected
        assert websocket_client.connection_status == "disconnected"

        # Set connected state
        websocket_client.is_connected = True
        assert websocket_client.connection_status == "connected"

    def test_string_representation(self, websocket_client):
        """Test string representation."""
        websocket_client.is_connected = True
        expected = "WebSocketClient(status=connected, handlers=0)"
        assert str(websocket_client) == expected


class TestSimulationWebSocketManager:
    """Test cases for SimulationWebSocketManager."""

    @pytest.fixture
    def config(self):
        """Create a mock configuration."""
        config = MagicMock()
        config.websocket.enabled = True
        config.websocket.reconnect_attempts = 3
        return config

    @pytest.fixture
    def manager(self, config):
        """Create a SimulationWebSocketManager instance."""
        return SimulationWebSocketManager(config.websocket)

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager.clients == {}
        assert isinstance(manager.logger, type(manager.logger))

    def test_get_client_new(self, manager):
        """Test getting a new client."""
        client = manager.get_client("sim_001")

        assert "sim_001" in manager.clients
        assert isinstance(client, WebSocketClient)

    def test_get_client_existing(self, manager):
        """Test getting an existing client."""
        client1 = manager.get_client("sim_001")
        client2 = manager.get_client("sim_001")

        assert client1 is client2

    def test_get_client_system_default(self, manager):
        """Test getting system client with default key."""
        client = manager.get_client()

        assert "system" in manager.clients
        assert isinstance(client, WebSocketClient)

    @pytest.mark.asyncio
    async def test_connect_simulation(self, manager):
        """Test connecting to simulation WebSocket."""
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.subscribe_to_simulation = AsyncMock()

        with patch.object(manager, 'get_client', return_value=mock_client):
            result = await manager.connect_simulation("sim_001")

            assert result == mock_client
            mock_client.connect.assert_called_once_with("sim_001")
            mock_client.subscribe_to_simulation.assert_called_once_with("sim_001")

    @pytest.mark.asyncio
    async def test_connect_system(self, manager):
        """Test connecting to system WebSocket."""
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()

        with patch.object(manager, 'get_client', return_value=mock_client):
            result = await manager.connect_system()

            assert result == mock_client
            mock_client.connect.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_disconnect_all(self, manager):
        """Test disconnecting all clients."""
        mock_client1 = MagicMock()
        mock_client1.disconnect = AsyncMock()

        mock_client2 = MagicMock()
        mock_client2.disconnect = AsyncMock()

        manager.clients = {
            "sim_001": mock_client1,
            "sim_002": mock_client2
        }

        await manager.disconnect_all()

        mock_client1.disconnect.assert_called_once()
        mock_client2.disconnect.assert_called_once()
        assert manager.clients == {}

    @pytest.mark.asyncio
    async def test_disconnect_all_with_exceptions(self, manager):
        """Test disconnecting all clients with exceptions."""
        mock_client = MagicMock()
        mock_client.disconnect = AsyncMock(side_effect=Exception("Disconnect failed"))

        manager.clients = {"sim_001": mock_client}

        # Should not raise exception
        await manager.disconnect_all()

        assert manager.clients == {}

    def test_setup_event_handlers(self, manager):
        """Test setting up event handlers."""
        mock_client = MagicMock()
        manager.clients["sim_001"] = mock_client

        # Mock the handler imports (would normally be from pages.monitor)
        with patch('services.clients.websocket_client.handle_simulation_progress') as mock_progress, \
             patch('services.clients.websocket_client.handle_simulation_event') as mock_event, \
             patch('services.clients.websocket_client.handle_websocket_connected') as mock_connected:

            result = manager.setup_event_handlers("sim_001")

            assert result == mock_client
            mock_client.add_message_handler.assert_any_call("simulation_progress", mock_progress)
            mock_client.add_message_handler.assert_any_call("simulation_event", mock_event)
            mock_client.add_connection_handler.assert_any_call(mock_connected)

    @pytest.mark.asyncio
    async def test_start_realtime_updates_simulation(self, manager):
        """Test starting real-time updates for simulation."""
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.subscribe_to_simulation = AsyncMock()
        mock_client.start_auto_reconnect = MagicMock()

        with patch.object(manager, 'setup_event_handlers', return_value=mock_client) as mock_setup:
            result = await manager.start_realtime_updates("sim_001")

            assert result is True
            mock_setup.assert_called_once_with("sim_001")
            mock_client.connect.assert_called_once_with("sim_001")
            mock_client.subscribe_to_simulation.assert_called_once_with("sim_001")
            mock_client.start_auto_reconnect.assert_called_once_with("sim_001")

    @pytest.mark.asyncio
    async def test_start_realtime_updates_system(self, manager):
        """Test starting real-time updates for system."""
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.start_auto_reconnect = MagicMock()

        with patch.object(manager, 'setup_event_handlers', return_value=mock_client) as mock_setup:
            result = await manager.start_realtime_updates()

            assert result is True
            mock_setup.assert_called_once_with(None)
            mock_client.connect.assert_called_once_with()
            mock_client.start_auto_reconnect.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_start_realtime_updates_failure(self, manager):
        """Test starting real-time updates with failure."""
        mock_client = MagicMock()
        mock_client.connect = AsyncMock(side_effect=Exception("Connection failed"))

        with patch.object(manager, 'setup_event_handlers', return_value=mock_client):
            result = await manager.start_realtime_updates("sim_001")

            assert result is False

    def test_stop_realtime_updates(self, manager):
        """Test stopping real-time updates."""
        mock_client = MagicMock()
        mock_client.stop_auto_reconnect = MagicMock()
        manager.clients["sim_001"] = mock_client

        with patch('asyncio.create_task') as mock_create_task:
            manager.stop_realtime_updates("sim_001")

            mock_client.stop_auto_reconnect.assert_called_once()
            mock_create_task.assert_called_once()


class TestWebSocketErrors:
    """Test cases for WebSocket errors."""

    def test_client_error_initialization(self):
        """Test WebSocketClientError initialization."""
        error = WebSocketClientError("Test error")
        assert str(error) == "Test error"

    def test_connection_error_initialization(self):
        """Test WebSocketConnectionError initialization."""
        error = WebSocketConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, WebSocketClientError)


if __name__ == "__main__":
    pytest.main([__file__])
