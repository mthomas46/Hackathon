"""Tests for Architecture Digitizer logging integration with LogCollectorClient."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

from services.shared.utilities.logging_client import LogCollectorClient


class TestArchitectureDigitizerLoggingIntegration:
    """Test Architecture Digitizer logging integration with LogCollectorClient."""

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
        global logger_client
        logger_client = mock_logger_client
        yield
        logger_client = None

    @pytest.mark.asyncio
    async def test_architecture_normalization_successful_logging(self, client, mock_logger_client):
        """Test successful architecture normalization logging."""
        # Mock the normalizer and related functions
        mock_normalizer = AsyncMock()
        mock_result = {
            "components": [
                {"id": "comp1", "name": "Web Server", "type": "service"},
                {"id": "comp2", "name": "Database", "type": "storage"},
                {"id": "comp3", "name": "Cache", "type": "service"},
            ],
            "connections": [
                {"from": "comp1", "to": "comp2", "type": "uses"},
                {"from": "comp1", "to": "comp3", "type": "caches"},
            ],
            "metadata": {"source": "miro", "board_id": "board123"},
        }
        mock_normalizer.normalize.return_value = mock_result

        with patch("main.get_normalizer") as mock_get_normalizer, patch(
            "main.record_architecture_digitizer_request"
        ) as mock_record_request, patch("main.fire_and_forget") as mock_fire_and_forget:

            mock_get_normalizer.return_value = mock_normalizer

            # Make request
            request_data = {"system": "miro", "board_id": "board123", "token": "test_token_123"}

            response = client.post("/normalize", json=request_data)
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] in ["architecture_normalization_started", "architecture_normalization_completed"]
            ]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == "architecture_normalization_started")
            start_data = start_call[0][1]
            assert start_data["system"] == "miro"
            assert start_data["board_id"] == "board123"
            assert start_data["has_token"] is True
            assert start_data["normalization_type"] == "diagram_fetch_and_normalize"
            assert "request_id" in start_data

            # Check completion event
            completion_call = next(
                call for call in business_calls if call[0][0] == "architecture_normalization_completed"
            )
            completion_data = completion_call[0][1]
            assert completion_data["system"] == "miro"
            assert completion_data["board_id"] == "board123"
            assert completion_data["components_extracted"] == 3
            assert completion_data["connections_mapped"] == 2
            assert completion_data["doc_store_stored"] is True
            assert completion_data["success"] is True
            assert "processing_time_seconds" in completion_data
            assert "data_size_bytes" in completion_data

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            assert perf_call[0][0] == "architecture_normalization"
            assert "normalization_success" in perf_call[0][2]
            assert perf_call[0][2]["normalization_success"] is True
            assert perf_call[0][2]["components_count"] == 3
            assert perf_call[0][2]["connections_count"] == 2

    @pytest.mark.asyncio
    async def test_architecture_normalization_unsupported_system_logging(self, client, mock_logger_client):
        """Test logging for unsupported diagram system."""
        with patch("main.get_normalizer") as mock_get_normalizer, patch(
            "main.record_architecture_digitizer_request"
        ) as mock_record_request:

            mock_get_normalizer.return_value = None  # No normalizer available

            # Make request with unsupported system
            request_data = {"system": "unsupported_system", "board_id": "board123", "token": "test_token"}

            response = client.post("/normalize", json=request_data)
            assert response.status_code == 400

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "Unsupported system unsupported_system" in error_call[0][0]
            assert error_call[0][1]["system"] == "unsupported_system"
            assert error_call[0][1]["board_id"] == "board123"
            assert error_call[0][1]["error_type"] == "unsupported_system"

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "architecture_normalization_failed"
            ]
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data["system"] == "unsupported_system"
            assert failure_data["board_id"] == "board123"
            assert failure_data["error_type"] == "unsupported_system"

    @pytest.mark.asyncio
    async def test_architecture_normalization_failure_logging(self, client, mock_logger_client):
        """Test failed architecture normalization logging."""
        # Mock normalizer to raise exception
        mock_normalizer = AsyncMock()
        mock_normalizer.normalize.side_effect = Exception("API authentication failed")

        with patch("main.get_normalizer") as mock_get_normalizer, patch(
            "main.record_architecture_digitizer_request"
        ) as mock_record_request, patch("main.record_architecture_digitizer_api_failure") as mock_record_failure:

            mock_get_normalizer.return_value = mock_normalizer

            # Make request
            request_data = {"system": "miro", "board_id": "board123", "token": "invalid_token"}

            response = client.post("/normalize", json=request_data)
            assert response.status_code == 500

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "Architecture normalization failed: API authentication failed" in error_call[0][0]
            assert error_call[0][1]["system"] == "miro"
            assert error_call[0][1]["board_id"] == "board123"
            assert error_call[0][1]["error_type"] == "Exception"
            assert error_call[0][1]["external_api_failure"] is True

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "architecture_normalization_failed"
            ]
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data["system"] == "miro"
            assert failure_data["board_id"] == "board123"
            assert failure_data["error_type"] == "Exception"
            assert "API authentication failed" in failure_data["error_message"]

    @pytest.mark.asyncio
    async def test_different_diagram_systems_logging(self, client, mock_logger_client):
        """Test logging for different diagram systems."""
        systems = ["miro", "figjam", "lucid", "confluence"]

        for system in systems:
            # Mock normalizer
            mock_normalizer = AsyncMock()
            mock_result = {
                "components": [{"id": "comp1", "name": f"{system} Component", "type": "service"}],
                "connections": [],
                "metadata": {"source": system},
            }
            mock_normalizer.normalize.return_value = mock_result

            with patch("main.get_normalizer") as mock_get_normalizer, patch(
                "main.record_architecture_digitizer_request"
            ) as mock_record_request, patch("main.fire_and_forget") as mock_fire_and_forget:

                mock_get_normalizer.return_value = mock_normalizer

                # Make request for each system
                request_data = {"system": system, "board_id": f"{system}_board_123", "token": f"{system}_token"}

                response = client.post("/normalize", json=request_data)
                assert response.status_code == 200

                # Check that system is correctly logged
                completion_events = [
                    call
                    for call in mock_logger_client.log_business_event.call_args_list
                    if call[0][0] == "architecture_normalization_completed"
                ]

                # Get the most recent completion event
                completion_data = completion_events[-1][0][1]
                assert completion_data["system"] == system
                assert completion_data["components_extracted"] == 1

    @pytest.mark.asyncio
    async def test_component_and_connection_metrics_logging(self, client, mock_logger_client):
        """Test that component and connection counts are accurately logged."""
        # Mock normalizer with complex architecture
        mock_normalizer = AsyncMock()
        mock_result = {
            "components": [
                {"id": "web", "name": "Web Server", "type": "service"},
                {"id": "api", "name": "API Gateway", "type": "service"},
                {"id": "db", "name": "Database", "type": "storage"},
                {"id": "cache", "name": "Redis Cache", "type": "service"},
                {"id": "queue", "name": "Message Queue", "type": "service"},
            ],
            "connections": [
                {"from": "web", "to": "api", "type": "routes_to"},
                {"from": "api", "to": "db", "type": "reads_from"},
                {"from": "api", "to": "cache", "type": "caches_with"},
                {"from": "api", "to": "queue", "type": "publishes_to"},
                {"from": "queue", "to": "api", "type": "consumed_by"},
                {"from": "cache", "to": "db", "type": "backed_by"},
            ],
            "metadata": {"complexity": "high"},
        }
        mock_normalizer.normalize.return_value = mock_result

        with patch("main.get_normalizer") as mock_get_normalizer, patch(
            "main.record_architecture_digitizer_request"
        ) as mock_record_request, patch("main.fire_and_forget") as mock_fire_and_forget:

            mock_get_normalizer.return_value = mock_normalizer

            request_data = {"system": "miro", "board_id": "complex_board_123", "token": "complex_token"}

            response = client.post("/normalize", json=request_data)
            assert response.status_code == 200

            # Check completion event has correct component/connection counts
            completion_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "architecture_normalization_completed"
            ]
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            assert completion_data["components_extracted"] == 5
            assert completion_data["connections_mapped"] == 6

            # Check performance metrics
            perf_call = mock_logger_client.log_performance_metric.call_args
            assert perf_call[0][2]["components_count"] == 5
            assert perf_call[0][2]["connections_count"] == 6

    @pytest.mark.asyncio
    async def test_startup_logging(self, mock_logger_client):
        """Test service startup logging."""
        from main import startup_event

        await startup_event()

        # Verify startup logging
        assert mock_logger_client.log_business_event.call_count >= 1
        assert mock_logger_client.log_info.call_count >= 1

        # Check startup business event
        business_call = mock_logger_client.log_business_event.call_args
        assert business_call[0][0] == "architecture_digitizer_startup"
        startup_data = business_call[0][1]
        assert "capabilities" in startup_data
        assert "supported_formats" in startup_data
        assert "features" in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert "Architecture Digitizer service started" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_shutdown_logging(self, mock_logger_client):
        """Test service shutdown logging."""
        from main import shutdown_event

        # Set logger client
        global logger_client
        logger_client = mock_logger_client

        await shutdown_event()

        # Verify shutdown logging
        assert mock_logger_client.log_info.call_count >= 1

        info_call = mock_logger_client.log_info.call_args
        assert "Architecture Digitizer service shutting down" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        # Mock normalizer
        mock_normalizer = AsyncMock()
        mock_result = {"components": [], "connections": []}
        mock_normalizer.normalize.return_value = mock_result

        with patch("main.get_normalizer") as mock_get_normalizer, patch(
            "main.record_architecture_digitizer_request"
        ) as mock_record_request, patch("main.fire_and_forget") as mock_fire_and_forget:

            mock_get_normalizer.return_value = mock_normalizer

            # Make request - should still work without logging
            request_data = {"system": "miro", "board_id": "test_board", "token": "test_token"}

            response = client.post("/normalize", json=request_data)
            assert response.status_code == 200

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        # Mock normalizer
        mock_normalizer = AsyncMock()
        mock_result = {"components": [], "connections": []}
        mock_normalizer.normalize.return_value = mock_result

        with patch("main.get_normalizer") as mock_get_normalizer, patch(
            "main.record_architecture_digitizer_request"
        ) as mock_record_request, patch("main.fire_and_forget") as mock_fire_and_forget:

            mock_get_normalizer.return_value = mock_normalizer

            request_data = {"system": "miro", "board_id": "test_board", "token": "test_token"}

            client.post("/normalize", json=request_data)

            # Check that request IDs are generated and used consistently
            business_calls = mock_logger_client.log_business_event.call_args_list
            perf_calls = mock_logger_client.log_performance_metric.call_args_list

            # Extract request IDs from all calls
            request_ids = set()
            for call in business_calls + perf_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get("request_id")
                    if request_id:
                        request_ids.add(request_id)

            # All calls should use the same request ID
            assert len(request_ids) == 1
            request_id = list(request_ids)[0]
            assert request_id.startswith("arch_normalize_")

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        # Mock normalizer
        mock_normalizer = AsyncMock()
        mock_result = {"components": [{"id": "test"}], "connections": []}
        mock_normalizer.normalize.return_value = mock_result

        with patch("main.get_normalizer") as mock_get_normalizer, patch(
            "main.record_architecture_digitizer_request"
        ) as mock_record_request, patch("main.fire_and_forget") as mock_fire_and_forget:

            mock_get_normalizer.return_value = mock_normalizer

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            request_data = {"system": "miro", "board_id": "test_board", "token": "test_token"}

            response = client.post("/normalize", json=request_data)
            assert response.status_code == 200

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            processing_time = perf_call[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_data_size_calculation_logging(self, client, mock_logger_client):
        """Test that data size is accurately calculated and logged."""
        # Mock normalizer with known result size
        mock_normalizer = AsyncMock()
        # Create a result with predictable string representation
        mock_result = {
            "components": [{"id": "comp1", "name": "Test Component"}],
            "connections": [{"from": "comp1", "to": "comp2"}],
            "metadata": {"size_test": True},
        }
        # Pre-calculate expected size
        expected_size = len(str(mock_result))
        mock_normalizer.normalize.return_value = mock_result

        with patch("main.get_normalizer") as mock_get_normalizer, patch(
            "main.record_architecture_digitizer_request"
        ) as mock_record_request, patch("main.fire_and_forget") as mock_fire_and_forget:

            mock_get_normalizer.return_value = mock_normalizer

            request_data = {"system": "miro", "board_id": "size_test_board", "token": "test_token"}

            response = client.post("/normalize", json=request_data)
            assert response.status_code == 200

            # Check that data size is logged
            completion_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "architecture_normalization_completed"
            ]
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            assert "data_size_bytes" in completion_data
            # The actual size may vary due to JSON formatting, but it should be reasonable
            assert completion_data["data_size_bytes"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
