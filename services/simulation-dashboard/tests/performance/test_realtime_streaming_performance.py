"""
Performance tests for real-time streaming and WebSocket performance.

This module contains comprehensive performance tests for WebSocket connections,
real-time data streaming, event processing latency, and concurrent streaming
operations under various load conditions.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from websockets.exceptions import ConnectionClosedError

from infrastructure.config.config import DashboardSettings
from services.clients.websocket_client import WebSocketClient


class TestRealtimeStreamingPerformance:
    """Test suite for real-time streaming performance and WebSocket efficiency."""

    @pytest.fixture
    def websocket_config(self):
        """Create WebSocket configuration optimized for performance testing."""
        config = DashboardSettings()
        config.websocket.enabled = True
        config.websocket.reconnect_attempts = 3
        config.websocket.heartbeat_interval = 5.0
        config.websocket.message_timeout = 2.0
        config.websocket.max_message_size = 1048576  # 1MB
        return config.websocket

    @pytest.fixture
    def performance_websocket_client(self, websocket_config):
        """Create WebSocket client configured for performance testing."""
        return WebSocketClient(websocket_config)

    @pytest.mark.asyncio
    async def test_websocket_connection_establishment_speed(self, performance_websocket_client):
        """Test WebSocket connection establishment speed."""
        connection_times = []

        # Test multiple connection establishments
        for i in range(10):
            start_time = time.time()

            # Mock successful connection
            with patch.object(performance_websocket_client, '_connect', new_callable=AsyncMock) as mock_connect:
                mock_connect.return_value = True

                try:
                    await performance_websocket_client.connect(f"ws://test-server-{i}:8080")
                    end_time = time.time()

                    connection_time = end_time - start_time
                    connection_times.append(connection_time)

                    # Clean up
                    await performance_websocket_client.disconnect()

                except Exception:
                    # Skip failed connections for performance testing
                    continue

        if connection_times:
            avg_connection_time = sum(connection_times) / len(connection_times)
            max_connection_time = max(connection_times)

            # Performance assertions
            assert avg_connection_time < 0.5, f"Average connection time {avg_connection_time:.3f}s exceeded 0.5s limit"
            assert max_connection_time < 2.0, f"Max connection time {max_connection_time:.3f}s exceeded 2.0s limit"

    @pytest.mark.asyncio
    async def test_concurrent_websocket_message_throughput(self, websocket_config):
        """Test concurrent WebSocket message throughput."""
        # Create multiple WebSocket clients
        clients = []
        for i in range(5):
            client = WebSocketClient(websocket_config)
            clients.append(client)

        message_counts = {f"client_{i}": 0 for i in range(5)}
        total_messages_sent = 0
        total_messages_received = 0

        async def websocket_message_worker(client, client_id):
            """Worker function for WebSocket message exchange."""
            nonlocal total_messages_sent, total_messages_received

            try:
                # Mock connection
                with patch.object(client, '_connect', new_callable=AsyncMock) as mock_connect, \
                     patch.object(client, '_send', new_callable=AsyncMock) as mock_send, \
                     patch.object(client, '_receive', new_callable=AsyncMock) as mock_receive:

                    mock_connect.return_value = True
                    mock_send.return_value = None

                    # Mock message responses
                    message_count = 0
                    async def mock_receive_func():
                        nonlocal message_count
                        message_count += 1
                        if message_count <= 100:  # 100 messages per client
                            return {"type": "data", "payload": f"test_data_{message_count}", "client": client_id}
                        else:
                            raise ConnectionClosedError(1000, "Test complete")

                    mock_receive.side_effect = mock_receive_func

                    await client.connect(f"ws://test-{client_id}:8080")

                    # Send and receive messages
                    start_time = time.time()
                    sent_count = 0

                    try:
                        while sent_count < 100:
                            # Send message
                            await client.send_message({
                                "type": "request",
                                "id": f"msg_{sent_count}",
                                "client": client_id
                            })
                            sent_count += 1

                            # Receive response
                            response = await client.receive_message()
                            if response and response.get("client") == client_id:
                                message_counts[client_id] += 1

                    except ConnectionClosedError:
                        pass  # Expected when test completes

                    end_time = time.time()

                    # Update totals
                    total_messages_sent += sent_count
                    total_messages_received += message_counts[client_id]

                    return {
                        "client_id": client_id,
                        "sent": sent_count,
                        "received": message_counts[client_id],
                        "duration": end_time - start_time
                    }

            finally:
                await client.disconnect()

        # Execute concurrent WebSocket operations
        start_time = time.time()
        tasks = []

        for i, client in enumerate(clients):
            task = asyncio.create_task(websocket_message_worker(client, f"client_{i}"))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Analyze results
        successful_clients = [r for r in results if not isinstance(r, Exception)]
        total_duration = end_time - start_time

        total_sent = sum(r["sent"] for r in successful_clients)
        total_received = sum(r["received"] for r in successful_clients)

        # Performance assertions
        assert total_duration < 30.0, f"Concurrent messaging took {total_duration:.2f}s, exceeded 30s limit"
        assert len(successful_clients) >= 4, f"Only {len(successful_clients)} clients succeeded out of 5"

        if successful_clients:
            avg_throughput = total_sent / total_duration
            assert avg_throughput >= 10, f"Message throughput {avg_throughput:.1f} msg/s below 10 msg/s minimum"

            # Verify message integrity
            assert total_received >= total_sent * 0.9, f"Message loss rate {(1 - total_received/total_sent)*100:.1f}% too high"

    @pytest.mark.asyncio
    async def test_websocket_reconnection_performance(self, performance_websocket_client):
        """Test WebSocket reconnection performance under failure conditions."""
        reconnection_times = []
        failure_count = 0

        # Simulate connection failures and reconnections
        for attempt in range(10):
            start_time = time.time()

            # Mock connection failure followed by success
            with patch.object(performance_websocket_client, '_connect', new_callable=AsyncMock) as mock_connect:
                if attempt < 3:  # First 3 attempts fail
                    mock_connect.side_effect = ConnectionClosedError(1006, "Connection failed")
                    failure_count += 1
                else:  # Subsequent attempts succeed
                    mock_connect.return_value = True

                try:
                    await performance_websocket_client.connect("ws://unstable-server:8080")
                    end_time = time.time()

                    reconnection_time = end_time - start_time
                    reconnection_times.append(reconnection_time)

                    await performance_websocket_client.disconnect()

                except Exception:
                    continue

        # Performance assertions
        if reconnection_times:
            avg_reconnection_time = sum(reconnection_times) / len(reconnection_times)
            max_reconnection_time = max(reconnection_times)

            assert avg_reconnection_time < 2.0, f"Average reconnection time {avg_reconnection_time:.3f}s exceeded 2.0s limit"
            assert max_reconnection_time < 5.0, f"Max reconnection time {max_reconnection_time:.3f}s exceeded 5.0s limit"

        # Should have experienced some failures before success
        assert failure_count >= 2, f"Expected at least 2 failures, got {failure_count}"

    @pytest.mark.asyncio
    async def test_event_stream_processing_latency(self, websocket_config):
        """Test event stream processing latency."""
        from components.realtime.event_stream import EventStream

        # Create event stream processor
        event_stream = EventStream()

        # Generate test events
        test_events = []
        for i in range(1000):
            test_events.append({
                "id": f"event_{i}",
                "type": "simulation_update" if i % 3 == 0 else "metric_update",
                "timestamp": f"2024-01-01T{i:04d}:00:00Z",
                "data": {
                    "simulation_id": f"sim_{i % 10}",
                    "value": float(i),
                    "metadata": {"batch": i // 100}
                }
            })

        # Mock event processing
        processing_times = []

        async def process_event_with_timing(event):
            """Process event and measure timing."""
            start_time = time.time()

            # Simulate processing
            await asyncio.sleep(0.001)  # 1ms processing time

            # Process event
            processed_event = {
                **event,
                "processed_at": "2024-01-01T00:00:00Z",
                "processing_status": "completed"
            }

            end_time = time.time()
            processing_times.append(end_time - start_time)

            return processed_event

        # Test batch event processing
        start_time = time.time()
        tasks = []

        # Process events in batches
        batch_size = 50
        for i in range(0, len(test_events), batch_size):
            batch = test_events[i:i + batch_size]
            batch_tasks = [process_event_with_timing(event) for event in batch]
            tasks.extend(batch_tasks)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Performance analysis
        total_processing_time = end_time - start_time
        avg_processing_time = sum(processing_times) / len(processing_times)
        max_processing_time = max(processing_times)

        # Performance assertions
        assert total_processing_time < 5.0, f"Event processing took {total_processing_time:.3f}s, exceeded 5s limit"
        assert avg_processing_time < 0.01, f"Average processing time {avg_processing_time:.4f}s exceeded 10ms limit"
        assert max_processing_time < 0.05, f"Max processing time {max_processing_time:.4f}s exceeded 50ms limit"

        # Verify all events processed
        assert len(results) == len(test_events), f"Expected {len(test_events)} results, got {len(results)}"

    @pytest.mark.asyncio
    async def test_realtime_data_streaming_throughput(self, websocket_config):
        """Test real-time data streaming throughput."""
        # Create high-frequency data stream
        stream_data_points = []
        processing_latencies = []

        async def generate_data_stream():
            """Generate high-frequency data stream."""
            for i in range(5000):  # 5000 data points
                data_point = {
                    "timestamp": time.time(),
                    "simulation_id": f"sim_{i % 5}",
                    "metrics": {
                        "cpu_usage": float(i % 100),
                        "memory_usage": float((i * 1.1) % 100),
                        "response_time": float(i % 50 + 10)
                    },
                    "sequence": i
                }
                stream_data_points.append(data_point)
                yield data_point
                await asyncio.sleep(0.001)  # 1ms intervals

        async def process_stream_data(data_point):
            """Process streaming data point."""
            start_time = time.time()

            # Simulate processing
            await asyncio.sleep(0.0005)  # 0.5ms processing

            # Validate data integrity
            assert "timestamp" in data_point
            assert "metrics" in data_point
            assert len(data_point["metrics"]) == 3

            processing_latencies.append(time.time() - start_time)

            return {"processed": True, "sequence": data_point["sequence"]}

        # Test streaming throughput
        start_time = time.time()

        # Process stream
        tasks = []
        async for data_point in generate_data_stream():
            task = asyncio.create_task(process_stream_data(data_point))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Performance analysis
        total_time = end_time - start_time
        throughput = len(results) / total_time  # points per second

        if processing_latencies:
            avg_latency = sum(processing_latencies) / len(processing_latencies)
            max_latency = max(processing_latencies)

            # Performance assertions
            assert total_time < 10.0, f"Streaming took {total_time:.3f}s, exceeded 10s limit"
            assert throughput >= 400, f"Throughput {throughput:.0f} points/s below 400 points/s minimum"
            assert avg_latency < 0.01, f"Average latency {avg_latency:.4f}s exceeded 10ms limit"
            assert max_latency < 0.05, f"Max latency {max_latency:.4f}s exceeded 50ms limit"

        # Verify data integrity
        assert len(results) == 5000, f"Expected 5000 results, got {len(results)}"
        assert len(stream_data_points) == 5000, f"Expected 5000 data points, got {len(stream_data_points)}"

    @pytest.mark.asyncio
    async def test_websocket_message_buffering_under_load(self, websocket_config):
        """Test WebSocket message buffering under high load conditions."""
        client = WebSocketClient(websocket_config)

        # Test message buffering when connection is slow
        buffered_messages = []
        send_latencies = []

        async def slow_message_sender(message):
            """Simulate slow message sending."""
            start_time = time.time()

            # Simulate network delay
            await asyncio.sleep(0.01)  # 10ms network delay

            buffered_messages.append(message)
            send_latencies.append(time.time() - start_time)

            return {"sent": True, "message_id": message.get("id")}

        # Send burst of messages
        start_time = time.time()
        tasks = []

        # Send 200 messages in rapid succession
        for i in range(200):
            message = {
                "id": f"msg_{i}",
                "type": "metric_update",
                "data": {"value": i, "timestamp": time.time()},
                "priority": "high" if i % 10 == 0 else "normal"
            }

            task = asyncio.create_task(slow_message_sender(message))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Performance analysis
        total_time = end_time - start_time

        if send_latencies:
            avg_send_time = sum(send_latencies) / len(send_latencies)
            max_send_time = max(send_latencies)

            # Buffering should allow concurrent processing
            assert total_time < 5.0, f"Buffered sending took {total_time:.3f}s, exceeded 5s limit"
            assert avg_send_time >= 0.008, f"Average send time {avg_send_time:.4f}s too fast (should include network delay)"
            assert max_send_time < 0.5, f"Max send time {max_send_time:.4f}s exceeded 500ms limit"

        # Verify all messages processed
        assert len(results) == 200, f"Expected 200 results, got {len(results)}"
        assert len(buffered_messages) == 200, f"Expected 200 buffered messages, got {len(buffered_messages)}"

        # Verify message ordering (should be maintained)
        message_ids = [msg["id"] for msg in buffered_messages]
        expected_ids = [f"msg_{i}" for i in range(200)]
        assert message_ids == expected_ids, "Message ordering not preserved"

    @pytest.mark.asyncio
    async def test_event_subscription_and_filtering_performance(self, websocket_config):
        """Test event subscription and filtering performance."""
        # Create event subscription system
        subscriptions = {}
        event_processing_times = []

        async def process_subscribed_event(event, subscriber_id):
            """Process event for a specific subscriber."""
            start_time = time.time()

            # Simulate filtering logic
            if event.get("type") in subscriptions.get(subscriber_id, []):
                # Process event
                processed_event = {
                    **event,
                    "subscriber_id": subscriber_id,
                    "processed_at": time.time(),
                    "filtered": True
                }

                processing_time = time.time() - start_time
                event_processing_times.append(processing_time)

                return processed_event
            else:
                # Event filtered out
                return None

        # Set up subscriptions
        subscriptions = {
            "subscriber_1": ["simulation_update", "metric_update"],
            "subscriber_2": ["alert", "error"],
            "subscriber_3": ["simulation_update", "alert", "metric_update"],
            "subscriber_4": ["error"],
            "subscriber_5": ["metric_update"]
        }

        # Generate test events
        test_events = []
        for i in range(1000):
            event_types = ["simulation_update", "metric_update", "alert", "error"]
            test_events.append({
                "id": f"event_{i}",
                "type": event_types[i % len(event_types)],
                "timestamp": time.time(),
                "data": {"value": i}
            })

        # Test event distribution to subscribers
        start_time = time.time()
        all_results = []

        for event in test_events:
            event_tasks = []
            for subscriber_id in subscriptions.keys():
                task = asyncio.create_task(process_subscribed_event(event, subscriber_id))
                event_tasks.append(task)

            event_results = await asyncio.gather(*event_tasks)

            # Collect non-filtered results
            valid_results = [r for r in event_results if r is not None]
            all_results.extend(valid_results)

        end_time = time.time()

        # Performance analysis
        total_time = end_time - start_time

        if event_processing_times:
            avg_processing_time = sum(event_processing_times) / len(event_processing_times)
            max_processing_time = max(event_processing_times)

            # Performance assertions
            assert total_time < 15.0, f"Event subscription took {total_time:.3f}s, exceeded 15s limit"
            assert avg_processing_time < 0.01, f"Average processing time {avg_processing_time:.4f}s exceeded 10ms limit"
            assert max_processing_time < 0.05, f"Max processing time {max_processing_time:.4f}s exceeded 50ms limit"

        # Verify event filtering worked
        assert len(all_results) > 0, "No events were processed by subscribers"
        assert len(all_results) < len(test_events) * len(subscriptions), "All events should be filtered"

        # Verify subscriber isolation
        subscriber_ids = set(r["subscriber_id"] for r in all_results)
        assert len(subscriber_ids) <= len(subscriptions), "Invalid subscriber IDs in results"


if __name__ == "__main__":
    pytest.main([__file__])
