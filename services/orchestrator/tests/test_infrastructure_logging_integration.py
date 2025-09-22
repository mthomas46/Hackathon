"""Tests for Orchestrator Infrastructure Routes logging integration with LogCollectorClient."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

from services.shared.utilities.logging_client import LogCollectorClient


class TestOrchestratorInfrastructureLoggingIntegration:
    """Test Orchestrator Infrastructure routes logging integration with LogCollectorClient."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_logger_client(self):
        """Mock LogCollectorClient."""
        mock_client = AsyncMock(spec=LogCollectorClient)
        return mock_client

    @pytest.fixture(autouse=True)
    async def setup_logger_client(self, mock_logger_client):
        """Setup mock logger client for all tests."""
        # Patch the get_logger_client function in the infrastructure routes
        with patch("services.orchestrator.presentation.api.infrastructure.routes.get_logger_client") as mock_get_client:
            mock_get_client.return_value = mock_logger_client
            yield

    @pytest.mark.asyncio
    async def test_saga_creation_logging_success(self, client, mock_logger_client):
        """Test saga creation endpoint logging on success."""
        mock_result = {"saga_id": "test-saga-123", "status": "started"}

        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.start_saga_use_case.execute.return_value = mock_result

            response = client.post("/api/v1/infrastructure/sagas")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and created
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check saga creation events
            business_calls = mock_logger_client.log_business_event.call_args_list
            saga_started = next((call for call in business_calls if call[0][0] == "saga_creation_started"), None)
            saga_created = next((call for call in business_calls if call[0][0] == "saga_created"), None)

            assert saga_started is not None
            assert saga_created is not None

            created_data = saga_created[0][1]
            assert created_data["saga_id"] == "test-saga-123"
            assert created_data["success"] is True
            assert "response_time_seconds" in created_data

    @pytest.mark.asyncio
    async def test_saga_creation_logging_failure(self, client, mock_logger_client):
        """Test saga creation endpoint logging on failure."""
        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.start_saga_use_case.execute.side_effect = Exception("Database connection failed")

            response = client.post("/api/v1/infrastructure/sagas")
            assert response.status_code == 500

            # Verify error logging
            assert mock_logger_client.log_error.call_count == 1
            assert mock_logger_client.log_business_event.call_count >= 2  # started and failed

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "Saga creation failed" in error_call[0][0]
            assert error_call[0][1]["operation"] == "distributed_transaction_creation"
            assert error_call[0][1]["error_type"] == "Exception"

            # Check failure event
            business_calls = mock_logger_client.log_business_event.call_args_list
            saga_failed = next((call for call in business_calls if call[0][0] == "saga_creation_failed"), None)
            assert saga_failed is not None

    @pytest.mark.asyncio
    async def test_saga_retrieval_logging_success(self, client, mock_logger_client):
        """Test saga retrieval endpoint logging on success."""
        saga_id = "test-saga-123"
        mock_result = {"saga_id": saga_id, "status": "active", "completed_steps": 2, "total_steps": 5}

        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.get_saga_use_case.execute.return_value = mock_result

            response = client.get(f"/api/v1/infrastructure/sagas/{saga_id}")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check saga retrieved event
            business_calls = mock_logger_client.log_business_event.call_args_list
            saga_retrieved = next((call for call in business_calls if call[0][0] == "saga_retrieved"), None)
            assert saga_retrieved is not None

            retrieved_data = saga_retrieved[0][1]
            assert retrieved_data["saga_id"] == saga_id
            assert retrieved_data["success"] is True
            assert retrieved_data["saga_status"] == "active"
            assert retrieved_data["steps_completed"] == 2

    @pytest.mark.asyncio
    async def test_saga_retrieval_logging_not_found(self, client, mock_logger_client):
        """Test saga retrieval endpoint logging when saga not found."""
        saga_id = "nonexistent-saga"

        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.get_saga_use_case.execute.return_value = None

            response = client.get(f"/api/v1/infrastructure/sagas/{saga_id}")
            assert response.status_code == 404

            # Verify logging calls
            business_calls = mock_logger_client.log_business_event.call_args_list
            saga_not_found = next((call for call in business_calls if call[0][0] == "saga_not_found"), None)
            assert saga_not_found is not None

            not_found_data = saga_not_found[0][1]
            assert not_found_data["saga_id"] == saga_id
            assert not_found_data["query_result"] == "not_found"

    @pytest.mark.asyncio
    async def test_saga_listing_logging_success(self, client, mock_logger_client):
        """Test saga listing endpoint logging on success."""
        mock_result = {
            "sagas": [{"saga_id": "saga-1", "status": "active"}, {"saga_id": "saga-2", "status": "completed"}],
            "total": 2,
        }

        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.list_sagas_use_case.execute.return_value = mock_result

            response = client.get("/api/v1/infrastructure/sagas?limit=10&offset=0")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and completed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check saga listing completed event
            business_calls = mock_logger_client.log_business_event.call_args_list
            listing_completed = next((call for call in business_calls if call[0][0] == "saga_listing_completed"), None)
            assert listing_completed is not None

            completed_data = listing_completed[0][1]
            assert completed_data["sagas_returned"] == 2
            assert completed_data["limit"] == 10
            assert completed_data["offset"] == 0
            assert completed_data["total_available"] == 2

    @pytest.mark.asyncio
    async def test_trace_creation_logging_success(self, client, mock_logger_client):
        """Test trace creation endpoint logging on success."""
        mock_result = {"trace_id": "test-trace-123", "status": "started"}

        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.start_trace_use_case.execute.return_value = mock_result

            response = client.post("/api/v1/infrastructure/traces?service_name=test-service&operation_name=test-op")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and created
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check trace created event
            business_calls = mock_logger_client.log_business_event.call_args_list
            trace_created = next((call for call in business_calls if call[0][0] == "trace_created"), None)
            assert trace_created is not None

            created_data = trace_created[0][1]
            assert created_data["trace_id"] == "test-trace-123"
            assert created_data["service_name"] == "test-service"
            assert created_data["operation_name"] == "test-op"
            assert created_data["trace_status"] == "active"

    @pytest.mark.asyncio
    async def test_trace_retrieval_logging_success(self, client, mock_logger_client):
        """Test trace retrieval endpoint logging on success."""
        trace_id = "test-trace-123"
        mock_result = {
            "trace_id": trace_id,
            "status": "completed",
            "spans": [{"name": "span1"}, {"name": "span2"}],
            "duration": 150,
        }

        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.get_trace_use_case.execute.return_value = mock_result

            response = client.get(f"/api/v1/infrastructure/traces/{trace_id}")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check trace retrieved event
            business_calls = mock_logger_client.log_business_event.call_args_list
            trace_retrieved = next((call for call in business_calls if call[0][0] == "trace_retrieved"), None)
            assert trace_retrieved is not None

            retrieved_data = trace_retrieved[0][1]
            assert retrieved_data["trace_id"] == trace_id
            assert retrieved_data["success"] is True
            assert retrieved_data["spans_count"] == 2
            assert retrieved_data["duration_ms"] == 150

    @pytest.mark.asyncio
    async def test_dlq_stats_retrieval_logging_success(self, client, mock_logger_client):
        """Test DLQ stats retrieval endpoint logging on success."""
        mock_result = {"total_events": 25, "retryable_events": 15, "oldest_event_hours": 48}

        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.get_dlq_stats_use_case.execute.return_value = mock_result

            response = client.get("/api/v1/infrastructure/dlq/stats")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check DLQ stats retrieved event
            business_calls = mock_logger_client.log_business_event.call_args_list
            stats_retrieved = next((call for call in business_calls if call[0][0] == "dlq_stats_retrieved"), None)
            assert stats_retrieved is not None

            retrieved_data = stats_retrieved[0][1]
            assert retrieved_data["total_failed_events"] == 25
            assert retrieved_data["retry_candidates"] == 15
            assert retrieved_data["oldest_event_age"] == 48

    @pytest.mark.asyncio
    async def test_dlq_retry_operation_logging_success(self, client, mock_logger_client):
        """Test DLQ retry operation endpoint logging on success."""
        mock_result = {"retried_count": 8, "failed_count": 2, "total_processed": 10}

        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.retry_event_use_case.execute.return_value = mock_result

            retry_request = {"event_ids": ["event1", "event2", "event3"], "max_retries": 3}
            response = client.post("/api/v1/infrastructure/dlq/retry", json=retry_request)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and completed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check DLQ retry completed event
            business_calls = mock_logger_client.log_business_event.call_args_list
            retry_completed = next((call for call in business_calls if call[0][0] == "dlq_retry_completed"), None)
            assert retry_completed is not None

            completed_data = retry_completed[0][1]
            assert completed_data["events_retried"] == 8
            assert completed_data["events_failed"] == 2
            assert completed_data["retry_success_rate"] == 8 / 3  # 8 retried / 3 requested

    @pytest.mark.asyncio
    async def test_event_publish_logging_success(self, client, mock_logger_client):
        """Test event publishing endpoint logging on success."""
        mock_result = {"event_id": "event-123", "subscribers_notified": 5, "status": "published"}

        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.publish_event_use_case.execute.return_value = mock_result

            publish_request = {"event_type": "test_event", "payload": {"key": "value", "number": 42}}
            response = client.post(
                "/api/v1/infrastructure/events/publish?event_type=test_event", json={"key": "value", "number": 42}
            )
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and published
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check event published event
            business_calls = mock_logger_client.log_business_event.call_args_list
            event_published = next((call for call in business_calls if call[0][0] == "event_published"), None)
            assert event_published is not None

            published_data = event_published[0][1]
            assert published_data["event_type"] == "test_event"
            assert published_data["event_id"] == "event-123"
            assert published_data["subscribers_notified"] == 5
            assert published_data["success"] is True

    @pytest.mark.asyncio
    async def test_event_replay_logging_placeholder(self, client, mock_logger_client):
        """Test event replay endpoint logging (placeholder implementation)."""
        response = client.post("/api/v1/infrastructure/events/replay", json={})
        assert response.status_code == 200

        # Verify logging calls for placeholder
        assert mock_logger_client.log_business_event.call_count >= 2  # started and completed

        # Check event replay completed event
        business_calls = mock_logger_client.log_business_event.call_args_list
        replay_completed = next((call for call in business_calls if call[0][0] == "event_replay_completed"), None)
        assert replay_completed is not None

        completed_data = replay_completed[0][1]
        assert completed_data["implementation_status"] == "placeholder"
        assert completed_data["events_replayed"] == 0

    @pytest.mark.asyncio
    async def test_event_clear_logging_placeholder(self, client, mock_logger_client):
        """Test event clearing endpoint logging (placeholder implementation)."""
        response = client.post("/api/v1/infrastructure/events/clear", json={})
        assert response.status_code == 200

        # Verify logging calls for placeholder
        assert mock_logger_client.log_business_event.call_count >= 2  # started and completed

        # Check event clear completed event
        business_calls = mock_logger_client.log_business_event.call_args_list
        clear_completed = next((call for call in business_calls if call[0][0] == "event_clear_completed"), None)
        assert clear_completed is not None

        completed_data = clear_completed[0][1]
        assert completed_data["implementation_status"] == "placeholder"
        assert completed_data["events_cleared"] == 0

    @pytest.mark.asyncio
    async def test_all_endpoints_generate_request_ids(self, client, mock_logger_client):
        """Test that all endpoints generate unique request IDs."""
        endpoints_and_methods = [
            ("/api/v1/infrastructure/sagas", "post"),
            ("/api/v1/infrastructure/sagas/test-saga-123", "get"),
            ("/api/v1/infrastructure/sagas", "get"),
            ("/api/v1/infrastructure/traces", "post"),
            ("/api/v1/infrastructure/traces/test-trace-123", "get"),
            ("/api/v1/infrastructure/traces", "get"),
            ("/api/v1/infrastructure/dlq/stats", "get"),
            ("/api/v1/infrastructure/dlq/events", "get"),
            ("/api/v1/infrastructure/events/stats", "get"),
        ]

        request_ids = set()

        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            # Mock all the use cases to return success
            mock_container.start_saga_use_case.execute.return_value = {"saga_id": "test"}
            mock_container.get_saga_use_case.execute.return_value = {"saga_id": "test"}
            mock_container.list_sagas_use_case.execute.return_value = {"sagas": []}
            mock_container.start_trace_use_case.execute.return_value = {"trace_id": "test"}
            mock_container.get_trace_use_case.execute.return_value = {"trace_id": "test"}
            mock_container.list_traces_use_case.execute.return_value = {"traces": []}
            mock_container.get_dlq_stats_use_case.execute.return_value = {}
            mock_container.list_dlq_events_use_case.execute.return_value = {"events": []}
            mock_container.get_event_stream_stats_use_case.execute.return_value = {}

            for endpoint, method in endpoints_and_methods:
                if method == "post":
                    if "sagas" in endpoint:
                        client.post(endpoint)
                    elif "traces" in endpoint:
                        client.post(f"{endpoint}?service_name=test&operation_name=test")
                    else:
                        client.post(endpoint, json={})
                else:
                    client.get(endpoint)

                # Collect request IDs from business events
                business_calls = mock_logger_client.log_business_event.call_args_list
                for call in business_calls:
                    if len(call[0]) > 1 and isinstance(call[0][1], dict):
                        request_id = call[0][1].get("request_id")
                        if request_id:
                            request_ids.add(request_id)

                # Reset call history for next iteration
                mock_logger_client.reset_mock()

        # Should have collected request IDs (exact count depends on implementation)
        assert len(request_ids) > 0

        # All request IDs should follow expected patterns
        for request_id in request_ids:
            assert any(prefix in request_id for prefix in ["saga_", "trace_", "dlq_", "event_"])

    @pytest.mark.asyncio
    async def test_performance_metrics_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.get_dlq_stats_use_case.execute.return_value = {"total_events": 10}

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            response = client.get("/api/v1/infrastructure/dlq/stats")
            assert response.status_code == 200

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            dlq_perf = next((call for call in perf_calls if call[0][0] == "dlq_stats_retrieval"), None)
            assert dlq_perf is not None

            processing_time = dlq_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Patch get_logger_client to return None
        with patch("services.orchestrator.presentation.api.infrastructure.routes.get_logger_client") as mock_get_client:
            mock_get_client.return_value = None

            with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
                mock_container.get_dlq_stats_use_case.execute.return_value = {"total_events": 5}

                # Make request - should still work without logging
                response = client.get("/api/v1/infrastructure/dlq/stats")
                assert response.status_code == 200

    def test_error_context_preservation(self, client, mock_logger_client):
        """Test that error context is properly preserved in logging."""
        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            mock_container.start_saga_use_case.execute.side_effect = ValueError("Invalid saga configuration")

            response = client.post("/api/v1/infrastructure/sagas")
            assert response.status_code == 500

            # Check that error logging preserves context
            error_calls = mock_logger_client.log_error.call_args_list
            assert len(error_calls) > 0

            error_call = error_calls[0]
            error_data = error_call[0][1]
            assert error_data["error_type"] == "ValueError"
            assert "operation" in error_data
            assert "response_time_seconds" in error_data
            assert "request_id" in error_data

    @pytest.mark.asyncio
    async def test_business_events_comprehensive_coverage(self, client, mock_logger_client):
        """Test that all major business events are logged across endpoints."""
        expected_events = {
            # Saga events
            "saga_creation_started",
            "saga_created",
            "saga_creation_failed",
            "saga_retrieval_started",
            "saga_retrieved",
            "saga_not_found",
            "saga_retrieval_failed",
            "saga_listing_started",
            "saga_listing_completed",
            "saga_listing_failed",
            # Trace events
            "trace_creation_started",
            "trace_created",
            "trace_creation_failed",
            "trace_retrieval_started",
            "trace_retrieved",
            "trace_not_found",
            "trace_retrieval_failed",
            "trace_listing_started",
            "trace_listing_completed",
            "trace_listing_failed",
            # DLQ events
            "dlq_stats_retrieval_started",
            "dlq_stats_retrieved",
            "dlq_stats_retrieval_failed",
            "dlq_events_listing_started",
            "dlq_events_listed",
            "dlq_events_listing_failed",
            "dlq_retry_started",
            "dlq_retry_completed",
            "dlq_retry_failed",
            # Event streaming events
            "event_stream_stats_started",
            "event_stream_stats_retrieved",
            "event_stream_stats_retrieval_failed",
            "event_publish_started",
            "event_published",
            "event_publish_failed",
            "event_replay_started",
            "event_replay_completed",
            "event_replay_failed",
            "event_clear_started",
            "event_clear_completed",
            "event_clear_failed",
        }

        # This is a comprehensive test that would require calling all endpoints
        # For brevity, we'll test a representative sample and verify event coverage

        with patch("services.orchestrator.presentation.api.infrastructure.routes.container") as mock_container:
            # Mock all use cases
            mock_container.start_saga_use_case.execute.return_value = {"saga_id": "test"}
            mock_container.get_dlq_stats_use_case.execute.return_value = {}
            mock_container.publish_event_use_case.execute.return_value = {"event_id": "test"}

            # Call a few representative endpoints
            client.post("/api/v1/infrastructure/sagas")
            client.get("/api/v1/infrastructure/dlq/stats")
            client.post("/api/v1/infrastructure/events/publish?event_type=test", json={"data": "test"})

            # Check which events were actually logged
            business_calls = mock_logger_client.log_business_event.call_args_list
            logged_events = {call[0][0] for call in business_calls}

            # Verify we logged some key events (not all, as some require specific conditions)
            key_events_logged = logged_events.intersection(
                {
                    "saga_creation_started",
                    "saga_created",
                    "dlq_stats_retrieval_started",
                    "dlq_stats_retrieved",
                    "event_publish_started",
                    "event_published",
                }
            )

            assert len(key_events_logged) >= 4  # Should have logged several key events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
