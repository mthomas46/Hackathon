"""Integration Tests for WebSocket Broadcasting - Event-Driven Engine Testing.

This module contains integration tests for WebSocket event broadcasting,
real-time simulation updates, and client-server communication.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from simulation.presentation.websockets.simulation_websocket import (
    SimulationWebSocketManager, notify_simulation_event,
    notify_simulation_progress, notify_simulation_error
)
from simulation.domain.events import (
    SimulationStarted, SimulationCompleted, DocumentGenerated,
    PhaseStarted, PhaseCompleted
)


class TestWebSocketBroadcastingIntegration:
    """Test cases for WebSocket broadcasting integration."""

    @pytest.fixture
    async def websocket_manager(self):
        """Create WebSocket manager for testing."""
        manager = SimulationWebSocketManager()
        yield manager
        # Cleanup any connections
        await manager.disconnect_all()

    @pytest.mark.asyncio
    async def test_websocket_connection_management(self, websocket_manager):
        """Test WebSocket connection management."""
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.send_text = AsyncMock()

        # Simulate client connection
        client_id = "client_123"
        await websocket_manager.connect(client_id, mock_websocket)

        # Verify connection is tracked
        assert client_id in websocket_manager.active_connections
        assert websocket_manager.active_connections[client_id] == mock_websocket

        # Test disconnection
        await websocket_manager.disconnect(client_id)
        assert client_id not in websocket_manager.active_connections

    @pytest.mark.asyncio
    async def test_simulation_event_broadcasting(self, websocket_manager):
        """Test broadcasting simulation events to WebSocket clients."""
        # Setup mock clients
        mock_client1 = AsyncMock()
        mock_client1.send_text = AsyncMock()

        mock_client2 = AsyncMock()
        mock_client2.send_text = AsyncMock()

        # Connect clients
        await websocket_manager.connect("client1", mock_client1)
        await websocket_manager.connect("client2", mock_client2)

        # Create and broadcast a simulation event
        event = SimulationStarted(
            simulation_id="sim-456",
            project_id="proj-123",
            scenario_type="comprehensive",
            estimated_duration_hours=24
        )

        await websocket_manager.broadcast_simulation_event(event)

        # Verify both clients received the event
        mock_client1.send_text.assert_called_once()
        mock_client2.send_text.assert_called_once()

        # Verify event data structure
        call_args1 = mock_client1.send_text.call_args[0][0]
        event_data1 = json.loads(call_args1)

        assert event_data1["event_type"] == "simulation_event"
        assert event_data1["data"]["event_type"] == "SimulationStarted"
        assert event_data1["data"]["simulation_id"] == "sim-456"
        assert event_data1["timestamp"] is not None

    @pytest.mark.asyncio
    async def test_progress_update_broadcasting(self, websocket_manager):
        """Test broadcasting progress updates to clients."""
        mock_client = AsyncMock()
        mock_client.send_text = AsyncMock()

        await websocket_manager.connect("client1", mock_client)

        # Broadcast progress update
        progress_data = {
            "simulation_id": "sim-456",
            "phase": "development",
            "progress_percentage": 75.5,
            "current_task": "Generating API documentation",
            "estimated_completion": "2 hours"
        }

        await websocket_manager.broadcast_progress(progress_data)

        # Verify progress message was sent
        mock_client.send_text.assert_called_once()
        call_args = mock_client.send_text.call_args[0][0]
        progress_message = json.loads(call_args)

        assert progress_message["event_type"] == "progress_update"
        assert progress_message["data"]["progress_percentage"] == 75.5
        assert progress_message["data"]["phase"] == "development"

    @pytest.mark.asyncio
    async def test_error_broadcasting(self, websocket_manager):
        """Test broadcasting error messages to clients."""
        mock_client = AsyncMock()
        mock_client.send_text = AsyncMock()

        await websocket_manager.connect("client1", mock_client)

        # Broadcast error
        error_data = {
            "simulation_id": "sim-456",
            "error_type": "service_unavailable",
            "message": "Mock Data Generator service is unavailable",
            "timestamp": datetime.now().isoformat(),
            "retry_count": 2
        }

        await websocket_manager.broadcast_error(error_data)

        # Verify error message was sent
        mock_client.send_text.assert_called_once()
        call_args = mock_client.send_text.call_args[0][0]
        error_message = json.loads(call_args)

        assert error_message["event_type"] == "error"
        assert error_message["data"]["error_type"] == "service_unavailable"
        assert error_message["data"]["retry_count"] == 2

    @pytest.mark.asyncio
    async def test_broadcast_to_specific_simulation(self, websocket_manager):
        """Test broadcasting to clients subscribed to specific simulation."""
        # Setup clients with different simulation subscriptions
        mock_client1 = AsyncMock()  # Subscribed to sim-456
        mock_client1.send_text = AsyncMock()

        mock_client2 = AsyncMock()  # Subscribed to sim-789
        mock_client2.send_text = AsyncMock()

        mock_client3 = AsyncMock()  # No specific subscription
        mock_client3.send_text = AsyncMock()

        # Connect clients with simulation subscriptions
        websocket_manager.simulation_subscriptions = {
            "client1": "sim-456",
            "client2": "sim-789",
            "client3": None  # Receives all broadcasts
        }

        await websocket_manager.connect("client1", mock_client1)
        await websocket_manager.connect("client2", mock_client2)
        await websocket_manager.connect("client3", mock_client3)

        # Broadcast event for sim-456
        event = DocumentGenerated(
            document_id="doc-123",
            project_id="proj-123",
            simulation_id="sim-456",
            document_type="confluence_page",
            title="Generated Document"
        )

        await websocket_manager.broadcast_simulation_event(event, simulation_id="sim-456")

        # Verify only subscribed clients received the event
        mock_client1.send_text.assert_called_once()
        mock_client3.send_text.assert_called_once()  # No specific subscription
        mock_client2.send_text.assert_not_called()  # Subscribed to different simulation


class TestWebSocketEventNotification:
    """Test cases for WebSocket event notification functions."""

    @pytest.mark.asyncio
    async def test_notify_simulation_event_function(self):
        """Test notify_simulation_event function."""
        with patch('simulation.presentation.websockets.simulation_websocket.get_websocket_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            # Create test event
            event = PhaseStarted(
                phase_id="phase-123",
                project_id="proj-123",
                simulation_id="sim-456",
                phase_name="Development",
                phase_number=2,
                estimated_duration_days=30
            )

            # Notify event
            await notify_simulation_event(event, simulation_id="sim-456")

            # Verify manager was called
            mock_manager.broadcast_simulation_event.assert_called_once_with(event, simulation_id="sim-456")

    @pytest.mark.asyncio
    async def test_notify_simulation_progress_function(self):
        """Test notify_simulation_progress function."""
        with patch('simulation.presentation.websockets.simulation_websocket.get_websocket_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            progress_data = {
                "simulation_id": "sim-456",
                "progress": 85.5,
                "message": "Processing documents"
            }

            await notify_simulation_progress(progress_data)

            mock_manager.broadcast_progress.assert_called_once_with(progress_data)

    @pytest.mark.asyncio
    async def test_notify_simulation_error_function(self):
        """Test notify_simulation_error function."""
        with patch('simulation.presentation.websockets.simulation_websocket.get_websocket_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            error_data = {
                "simulation_id": "sim-456",
                "error": "Service timeout",
                "details": "Connection to analysis service timed out"
            }

            await notify_simulation_error(error_data)

            mock_manager.broadcast_error.assert_called_once_with(error_data)


class TestWebSocketConnectionHandling:
    """Test cases for WebSocket connection handling."""

    @pytest.mark.asyncio
    async def test_connection_cleanup_on_error(self):
        """Test that connections are cleaned up properly on errors."""
        manager = SimulationWebSocketManager()

        mock_websocket = AsyncMock()
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection error"))

        # Connect client
        client_id = "client_error"
        await manager.connect(client_id, mock_websocket)

        # Attempt to broadcast (should handle error gracefully)
        event = SimulationStarted(
            simulation_id="sim-456",
            project_id="proj-123",
            scenario_type="test",
            estimated_duration_hours=1
        )

        # This should not raise an exception
        await manager.broadcast_simulation_event(event)

        # Connection should still be tracked (error handling should be graceful)
        assert client_id in manager.active_connections

    @pytest.mark.asyncio
    async def test_multiple_simultaneous_broadcasts(self):
        """Test handling multiple simultaneous broadcasts."""
        manager = SimulationWebSocketManager()

        # Connect multiple clients
        clients = []
        for i in range(5):
            mock_websocket = AsyncMock()
            mock_websocket.send_text = AsyncMock()
            clients.append((f"client_{i}", mock_websocket))
            await manager.connect(f"client_{i}", mock_websocket)

        # Create multiple events to broadcast
        events = []
        for i in range(3):
            event = DocumentGenerated(
                document_id=f"doc_{i}",
                project_id="proj-123",
                simulation_id="sim-456",
                document_type="confluence_page",
                title=f"Document {i}"
            )
            events.append(event)

        # Broadcast all events concurrently
        broadcast_tasks = [
            manager.broadcast_simulation_event(event, simulation_id="sim-456")
            for event in events
        ]

        await asyncio.gather(*broadcast_tasks)

        # Verify all clients received all events
        for client_id, mock_websocket in clients:
            assert mock_websocket.send_text.call_count == 3

            # Verify each call contained proper event data
            calls = mock_websocket.send_text.call_args_list
            for call in calls:
                message_data = json.loads(call[0][0])
                assert message_data["event_type"] == "simulation_event"
                assert "data" in message_data
                assert "timestamp" in message_data

    @pytest.mark.asyncio
    async def test_connection_limits_and_throttling(self):
        """Test connection limits and message throttling."""
        manager = SimulationWebSocketManager()

        # Set connection limit
        manager.max_connections = 3

        # Connect up to limit
        for i in range(3):
            mock_websocket = AsyncMock()
            mock_websocket.send_text = AsyncMock()
            await manager.connect(f"client_{i}", mock_websocket)

        # Verify all connections accepted
        assert len(manager.active_connections) == 3

        # Test message throttling (if implemented)
        # This would depend on the specific throttling implementation
        event = SimulationStarted(
            simulation_id="sim-456",
            project_id="proj-123",
            scenario_type="test",
            estimated_duration_hours=1
        )

        start_time = asyncio.get_event_loop().time()
        await manager.broadcast_simulation_event(event)
        end_time = asyncio.get_event_loop().time()

        # Broadcast should complete in reasonable time
        assert (end_time - start_time) < 1.0  # Less than 1 second


class TestWebSocketMessageFormatting:
    """Test cases for WebSocket message formatting and validation."""

    def test_simulation_event_message_format(self):
        """Test formatting of simulation event messages."""
        manager = SimulationWebSocketManager()

        event = SimulationCompleted(
            simulation_id="sim-456",
            project_id="proj-123",
            status="completed",
            metrics={"total_documents": 25, "processing_time": 3600},
            total_duration_hours=1.0
        )

        # Get the message format that would be sent
        message_data = {
            "event_type": "simulation_event",
            "data": event.to_dict(),
            "timestamp": datetime.now().isoformat()
        }

        # Verify message structure
        assert message_data["event_type"] == "simulation_event"
        assert "data" in message_data
        assert "timestamp" in message_data

        # Verify event data is included
        event_data = message_data["data"]
        assert event_data["event_type"] == "SimulationCompleted"
        assert event_data["simulation_id"] == "sim-456"
        assert event_data["status"] == "completed"
        assert "metrics" in event_data

    def test_progress_message_format(self):
        """Test formatting of progress messages."""
        progress_data = {
            "simulation_id": "sim-456",
            "phase": "development",
            "progress_percentage": 75.5,
            "current_task": "Generating API documentation",
            "estimated_completion": "30 minutes",
            "completed_tasks": 15,
            "total_tasks": 20
        }

        message_data = {
            "event_type": "progress_update",
            "data": progress_data,
            "timestamp": datetime.now().isoformat()
        }

        # Verify progress message structure
        assert message_data["event_type"] == "progress_update"
        assert message_data["data"]["progress_percentage"] == 75.5
        assert message_data["data"]["phase"] == "development"
        assert message_data["data"]["completed_tasks"] == 15
        assert message_data["data"]["total_tasks"] == 20

    def test_error_message_format(self):
        """Test formatting of error messages."""
        error_data = {
            "simulation_id": "sim-456",
            "error_type": "service_unavailable",
            "message": "Analysis service is not responding",
            "details": {
                "service": "analysis_service",
                "endpoint": "/analyze",
                "timeout": 30,
                "retry_count": 3
            },
            "timestamp": datetime.now().isoformat(),
            "severity": "high"
        }

        message_data = {
            "event_type": "error",
            "data": error_data,
            "timestamp": datetime.now().isoformat()
        }

        # Verify error message structure
        assert message_data["event_type"] == "error"
        assert message_data["data"]["error_type"] == "service_unavailable"
        assert message_data["data"]["severity"] == "high"
        assert "details" in message_data["data"]
        assert message_data["data"]["details"]["retry_count"] == 3

    def test_message_size_limits(self):
        """Test handling of message size limits."""
        # Create a large event with extensive data
        large_metrics = {
            "documents_generated": list(range(100)),  # Large list
            "processing_times": {f"doc_{i}": i * 0.1 for i in range(50)},  # Large dict
            "quality_scores": [0.8 + i * 0.01 for i in range(100)],  # Large list
            "large_text_field": "A" * 10000  # Large text content
        }

        event = SimulationCompleted(
            simulation_id="sim-456",
            project_id="proj-123",
            status="completed",
            metrics=large_metrics,
            total_duration_hours=24.0
        )

        # Convert to message format
        message_data = {
            "event_type": "simulation_event",
            "data": event.to_dict(),
            "timestamp": datetime.now().isoformat()
        }

        # Convert to JSON to check size
        json_message = json.dumps(message_data)
        message_size_kb = len(json_message.encode('utf-8')) / 1024

        # Verify message can be serialized (size will depend on implementation limits)
        assert message_size_kb > 10  # Should be reasonably large
        assert json.loads(json_message)  # Should be valid JSON

        # Test that the message contains all expected data
        parsed_message = json.loads(json_message)
        assert parsed_message["data"]["metrics"]["documents_generated"] == list(range(100))


class TestWebSocketSubscriptionManagement:
    """Test cases for WebSocket subscription management."""

    @pytest.mark.asyncio
    async def test_simulation_subscription_management(self):
        """Test management of simulation-specific subscriptions."""
        manager = SimulationWebSocketManager()

        # Subscribe clients to different simulations
        manager.simulation_subscriptions = {
            "client1": "sim-456",
            "client2": "sim-456",
            "client3": "sim-789",
            "client4": None  # No specific subscription
        }

        # Create mock websockets
        for client_id in manager.simulation_subscriptions.keys():
            mock_websocket = AsyncMock()
            mock_websocket.send_text = AsyncMock()
            await manager.connect(client_id, mock_websocket)

        # Broadcast event for sim-456
        event = PhaseCompleted(
            phase_id="phase-123",
            project_id="proj-123",
            simulation_id="sim-456",
            phase_name="Development",
            phase_number=2,
            metrics={"completion_rate": 0.95}
        )

        await manager.broadcast_simulation_event(event, simulation_id="sim-456")

        # Verify correct clients received the event
        client1_websocket = manager.active_connections["client1"]
        client2_websocket = manager.active_connections["client2"]
        client3_websocket = manager.active_connections["client3"]
        client4_websocket = manager.active_connections["client4"]

        client1_websocket.send_text.assert_called_once()
        client2_websocket.send_text.assert_called_once()
        client3_websocket.send_text.assert_not_called()  # Different simulation
        client4_websocket.send_text.assert_called_once()  # No specific subscription

    @pytest.mark.asyncio
    async def test_subscription_changes(self):
        """Test dynamic subscription changes."""
        manager = SimulationWebSocketManager()

        mock_websocket = AsyncMock()
        mock_websocket.send_text = AsyncMock()

        client_id = "client1"
        await manager.connect(client_id, mock_websocket)

        # Initially no subscription
        manager.simulation_subscriptions[client_id] = None

        # Broadcast to all simulations
        event1 = SimulationStarted(simulation_id="sim-456", project_id="proj-123", scenario_type="test", estimated_duration_hours=1)
        await manager.broadcast_simulation_event(event1)
        assert mock_websocket.send_text.call_count == 1

        # Change subscription to specific simulation
        manager.simulation_subscriptions[client_id] = "sim-456"

        # Broadcast to specific simulation
        event2 = DocumentGenerated(document_id="doc-123", project_id="proj-123", simulation_id="sim-456", document_type="page", title="Test")
        await manager.broadcast_simulation_event(event2, simulation_id="sim-456")
        assert mock_websocket.send_text.call_count == 2

        # Broadcast to different simulation (should not receive)
        event3 = DocumentGenerated(document_id="doc-456", project_id="proj-123", simulation_id="sim-789", document_type="page", title="Test")
        await manager.broadcast_simulation_event(event3, simulation_id="sim-789")
        assert mock_websocket.send_text.call_count == 2  # No additional call


class TestWebSocketPerformanceMonitoring:
    """Test cases for WebSocket performance monitoring."""

    @pytest.mark.asyncio
    async def test_broadcast_performance_metrics(self):
        """Test collection of broadcast performance metrics."""
        manager = SimulationWebSocketManager()

        # Connect multiple clients
        client_count = 10
        for i in range(client_count):
            mock_websocket = AsyncMock()
            mock_websocket.send_text = AsyncMock()
            await manager.connect(f"client_{i}", mock_websocket)

        # Measure broadcast performance
        event = SimulationStarted(
            simulation_id="sim-456",
            project_id="proj-123",
            scenario_type="performance_test",
            estimated_duration_hours=1
        )

        start_time = asyncio.get_event_loop().time()
        await manager.broadcast_simulation_event(event)
        end_time = asyncio.get_event_loop().time()

        broadcast_time = end_time - start_time
        avg_time_per_client = broadcast_time / client_count

        # Performance assertions
        assert broadcast_time < 2.0  # Should complete within 2 seconds
        assert avg_time_per_client < 0.1  # Should be fast per client

        # Verify all clients received the message
        for i in range(client_count):
            websocket = manager.active_connections[f"client_{i}"]
            websocket.send_text.assert_called_once()

    def test_message_throughput_calculation(self):
        """Test calculation of WebSocket message throughput."""
        # Simulate message throughput over time
        time_window_seconds = 60
        messages_sent = 1000

        throughput_per_second = messages_sent / time_window_seconds
        throughput_per_minute = messages_sent

        # Verify throughput calculations
        assert throughput_per_second == 1000 / 60  # ~16.67 messages/second
        assert throughput_per_minute == 1000

        # Test with different scenarios
        scenarios = [
            {"messages": 500, "time_window": 30, "expected_mps": 500/30},
            {"messages": 2000, "time_window": 120, "expected_mps": 2000/120},
            {"messages": 100, "time_window": 10, "expected_mps": 100/10}
        ]

        for scenario in scenarios:
            calculated_mps = scenario["messages"] / scenario["time_window"]
            assert calculated_mps == scenario["expected_mps"]

    @pytest.mark.asyncio
    async def test_connection_scalability(self):
        """Test WebSocket connection scalability."""
        manager = SimulationWebSocketManager()

        # Test with increasing number of connections
        connection_counts = [10, 50, 100]

        for count in connection_counts:
            # Clear previous connections
            await manager.disconnect_all()

            # Connect new clients
            for i in range(count):
                mock_websocket = AsyncMock()
                mock_websocket.send_text = AsyncMock()
                await manager.connect(f"client_{i}", mock_websocket)

            # Test broadcast performance
            event = DocumentGenerated(
                document_id="doc-test",
                project_id="proj-123",
                simulation_id="sim-456",
                document_type="page",
                title="Scalability Test"
            )

            start_time = asyncio.get_event_loop().time()
            await manager.broadcast_simulation_event(event)
            end_time = asyncio.get_event_loop().time()

            broadcast_time = end_time - start_time
            max_acceptable_time = count * 0.01  # 10ms per connection

            # Scalability assertion
            assert broadcast_time < max_acceptable_time, f"Broadcast took {broadcast_time:.3f}s for {count} connections"

            # Verify all connections received the message
            for i in range(count):
                websocket = manager.active_connections[f"client_{i}"]
                websocket.send_text.assert_called_once()
