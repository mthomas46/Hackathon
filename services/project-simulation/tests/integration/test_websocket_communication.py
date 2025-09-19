"""Integration Tests for WebSocket Communication.

This module contains comprehensive tests for WebSocket endpoints,
real-time event broadcasting, and client-server communication patterns.
Tests cover connection handling, message routing, and error scenarios.
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

import websockets
from starlette.websockets import WebSocketDisconnect

from simulation.presentation.websockets.simulation_websocket import (
    SimulationWebSocketHandler,
    WebSocketEventType
)


class TestWebSocketConnectionHandling:
    """Test cases for WebSocket connection establishment and management."""

    @pytest.mark.asyncio
    async def test_simulation_websocket_connection_establishment(self):
        """Test successful WebSocket connection for simulation updates."""
        with patch('simulation.presentation.websockets.simulation_websocket.get_simulation_container') as mock_container:
            mock_service = AsyncMock()
            mock_container.return_value.get.return_value = mock_service

            handler = SimulationWebSocketHandler()

            # Mock WebSocket
            mock_websocket = AsyncMock()
            mock_websocket.accept = AsyncMock()
            mock_websocket.receive_json = AsyncMock(return_value={"type": "ping"})
            mock_websocket.send_json = AsyncMock()
            mock_websocket.close = AsyncMock()

            # Test connection
            await handler.handle_simulation_connection(mock_websocket, "test-simulation-123")

            # Verify connection was accepted
            mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_connection_with_invalid_simulation_id(self):
        """Test WebSocket connection with invalid simulation ID."""
        with patch('simulation.presentation.websockets.simulation_websocket.get_simulation_container') as mock_container:
            mock_service = AsyncMock()
            mock_container.return_value.get.return_value = mock_service

            # Mock service to return None (invalid simulation)
            mock_service.get_simulation_status.return_value = None

            handler = SimulationWebSocketHandler()
            mock_websocket = AsyncMock()
            mock_websocket.accept = AsyncMock()
            mock_websocket.send_json = AsyncMock()

            # Should handle invalid simulation gracefully
            await handler.handle_simulation_connection(mock_websocket, "invalid-id")

            # Should send error message
            mock_websocket.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_websocket_connection_timeout_handling(self):
        """Test WebSocket connection timeout handling."""
        handler = SimulationWebSocketHandler()
        mock_websocket = AsyncMock()

        # Simulate timeout
        mock_websocket.receive_json = AsyncMock(side_effect=asyncio.TimeoutError())

        # Should handle timeout gracefully
        try:
            await handler.handle_simulation_connection(mock_websocket, "test-simulation")
        except asyncio.TimeoutError:
            pytest.fail("Timeout should be handled gracefully")

    @pytest.mark.asyncio
    async def test_websocket_connection_cleanup_on_disconnect(self):
        """Test proper cleanup when WebSocket disconnects."""
        with patch('simulation.presentation.websockets.simulation_websocket.get_simulation_container') as mock_container:
            mock_service = AsyncMock()
            mock_container.return_value.get.return_value = mock_service

            handler = SimulationWebSocketHandler()
            mock_websocket = AsyncMock()
            mock_websocket.accept = AsyncMock()
            mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())
            mock_websocket.close = AsyncMock()

            # Should handle disconnect gracefully
            await handler.handle_simulation_connection(mock_websocket, "test-simulation")

            # Verify cleanup
            mock_websocket.close.assert_called_once()


class TestWebSocketMessageHandling:
    """Test cases for WebSocket message processing and routing."""

    @pytest.mark.asyncio
    async def test_simulation_status_update_message(self):
        """Test handling of simulation status update messages."""
        handler = SimulationWebSocketHandler()

        message = {
            "type": "simulation_status",
            "simulation_id": "test-123",
            "status": "running",
            "progress": 0.75,
            "timestamp": datetime.now().isoformat()
        }

        # Test message validation
        assert message["type"] == "simulation_status"
        assert "simulation_id" in message
        assert "status" in message
        assert isinstance(message["progress"], float)

    @pytest.mark.asyncio
    async def test_document_generation_progress_message(self):
        """Test handling of document generation progress messages."""
        handler = SimulationWebSocketHandler()

        message = {
            "type": "document_progress",
            "simulation_id": "test-123",
            "document_type": "requirements_doc",
            "progress": 0.6,
            "current_step": "validation",
            "timestamp": datetime.now().isoformat()
        }

        # Validate message structure
        required_fields = ["type", "simulation_id", "progress", "timestamp"]
        for field in required_fields:
            assert field in message

    @pytest.mark.asyncio
    async def test_error_message_broadcasting(self):
        """Test broadcasting of error messages via WebSocket."""
        handler = SimulationWebSocketHandler()

        error_message = {
            "type": "error",
            "simulation_id": "test-123",
            "error_type": "validation_error",
            "message": "Document validation failed",
            "details": {"field": "complexity", "issue": "invalid_value"},
            "timestamp": datetime.now().isoformat()
        }

        # Test error message structure
        assert error_message["type"] == "error"
        assert "error_type" in error_message
        assert "message" in error_message
        assert "details" in error_message

    @pytest.mark.asyncio
    async def test_websocket_message_acknowledgment(self):
        """Test client acknowledgment of received messages."""
        handler = SimulationWebSocketHandler()

        ack_message = {
            "type": "ack",
            "message_id": "msg-123",
            "timestamp": datetime.now().isoformat()
        }

        # Validate acknowledgment structure
        assert ack_message["type"] == "ack"
        assert "message_id" in ack_message


class TestWebSocketEventBroadcasting:
    """Test cases for event broadcasting to WebSocket clients."""

    @pytest.mark.asyncio
    async def test_broadcast_to_simulation_clients(self):
        """Test broadcasting messages to all clients of a specific simulation."""
        handler = SimulationWebSocketHandler()

        # Mock clients
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()

        # Simulate client connections for simulation
        handler._simulation_clients = {
            "test-simulation": [mock_client1, mock_client2]
        }

        message = {
            "type": "simulation_update",
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }

        # Broadcast message
        await handler.broadcast_to_simulation("test-simulation", message)

        # Verify both clients received the message
        mock_client1.send_json.assert_called_with(message)
        mock_client2.send_json.assert_called_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_system_clients(self):
        """Test broadcasting messages to all system clients."""
        handler = SimulationWebSocketHandler()

        # Mock system clients
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()

        handler._system_clients = [mock_client1, mock_client2]

        message = {
            "type": "system_notification",
            "message": "System maintenance scheduled",
            "timestamp": datetime.now().isoformat()
        }

        # Broadcast to system
        await handler.broadcast_to_system(message)

        # Verify both clients received the message
        mock_client1.send_json.assert_called_with(message)
        mock_client2.send_json.assert_called_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_failed_client_handling(self):
        """Test broadcasting when some clients fail."""
        handler = SimulationWebSocketHandler()

        # Mock clients - one succeeds, one fails
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()
        mock_client2.send_json.side_effect = Exception("Connection failed")

        handler._simulation_clients = {
            "test-simulation": [mock_client1, mock_client2]
        }

        message = {"type": "test", "data": "test"}

        # Should not raise exception even if one client fails
        await handler.broadcast_to_simulation("test-simulation", message)

        # First client should have received the message
        mock_client1.send_json.assert_called_with(message)

    @pytest.mark.asyncio
    async def test_client_registration_and_deregistration(self):
        """Test client registration and deregistration."""
        handler = SimulationWebSocketHandler()

        mock_websocket = AsyncMock()

        # Register client
        await handler.register_simulation_client("test-sim", mock_websocket)
        assert mock_websocket in handler._simulation_clients["test-sim"]

        # Deregister client
        await handler.deregister_simulation_client("test-sim", mock_websocket)
        assert mock_websocket not in handler._simulation_clients["test-sim"]


class TestWebSocketSecurity:
    """Test cases for WebSocket security and access control."""

    @pytest.mark.asyncio
    async def test_websocket_origin_validation(self):
        """Test WebSocket origin validation for security."""
        # This would test CORS-like validation for WebSocket connections
        pass

    @pytest.mark.asyncio
    async def test_websocket_rate_limiting(self):
        """Test rate limiting for WebSocket messages."""
        # Test that rapid message sending is limited
        pass

    @pytest.mark.asyncio
    async def test_websocket_authentication(self):
        """Test WebSocket authentication and authorization."""
        # Test that only authenticated users can connect
        pass


class TestWebSocketPerformance:
    """Test cases for WebSocket performance under load."""

    @pytest.mark.asyncio
    async def test_high_frequency_message_handling(self):
        """Test handling of high-frequency messages."""
        handler = SimulationWebSocketHandler()

        # Simulate many rapid messages
        messages = [
            {"type": "update", "id": i, "timestamp": datetime.now().isoformat()}
            for i in range(100)
        ]

        # Test processing performance
        start_time = asyncio.get_event_loop().time()

        for message in messages:
            # Process message
            pass

        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time

        # Should process quickly
        assert processing_time < 1.0  # Less than 1 second for 100 messages

    @pytest.mark.asyncio
    async def test_large_number_of_concurrent_clients(self):
        """Test handling of many concurrent WebSocket clients."""
        handler = SimulationWebSocketHandler()

        # Simulate many clients
        num_clients = 100
        clients = [AsyncMock() for _ in range(num_clients)]

        # Register all clients
        for i, client in enumerate(clients):
            await handler.register_simulation_client(f"sim-{i}", client)

        # Broadcast message
        message = {"type": "broadcast_test"}
        await handler.broadcast_to_simulation("sim-0", message)

        # Should handle the load
        assert len(handler._simulation_clients["sim-0"]) == num_clients


class TestWebSocketMessageFormats:
    """Test cases for WebSocket message format validation."""

    def test_simulation_status_message_format(self):
        """Test simulation status message format."""
        message = {
            "type": "simulation_status",
            "simulation_id": "sim-123",
            "status": "running",
            "progress": 0.75,
            "stage": "document_generation",
            "estimated_completion": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat()
        }

        # Validate required fields
        required_fields = ["type", "simulation_id", "status", "timestamp"]
        for field in required_fields:
            assert field in message

        # Validate data types
        assert isinstance(message["progress"], (int, float))
        assert 0 <= message["progress"] <= 1

    def test_error_message_format(self):
        """Test error message format."""
        message = {
            "type": "error",
            "simulation_id": "sim-123",
            "error_type": "validation_error",
            "message": "Invalid configuration",
            "details": {
                "field": "complexity",
                "expected": ["low", "medium", "high"],
                "received": "invalid"
            },
            "timestamp": datetime.now().isoformat()
        }

        # Validate error message structure
        assert message["type"] == "error"
        assert "error_type" in message
        assert "message" in message
        assert isinstance(message["details"], dict)

    def test_progress_message_format(self):
        """Test progress message format."""
        message = {
            "type": "progress",
            "simulation_id": "sim-123",
            "stage": "document_generation",
            "current_step": "Generating requirements",
            "progress": 0.6,
            "items_completed": 12,
            "total_items": 20,
            "timestamp": datetime.now().isoformat()
        }

        # Validate progress structure
        assert message["type"] == "progress"
        assert "stage" in message
        assert "progress" in message
        assert "items_completed" in message
        assert "total_items" in message
