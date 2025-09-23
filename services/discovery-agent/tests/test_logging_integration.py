"""Tests for Discovery Agent logging integration with LogCollectorClient."""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

from services.shared.utilities.logging_client import LogCollectorClient


class TestDiscoveryAgentLoggingIntegration:
    """Test Discovery Agent logging integration with LogCollectorClient."""

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
    async def test_service_discovery_successful_logging(self, client, mock_logger_client):
        """Test successful service discovery logging."""
        # Mock the fetch_openapi_spec_with_fallback function
        with patch("services.discovery_agent.main.fetch_openapi_spec_with_fallback") as mock_fetch, patch(
            "services.discovery_agent.main.extract_endpoints_from_spec"
        ) as mock_extract:

            # Setup mocks
            mock_spec = {"openapi": "3.0.0", "paths": {"/test": {"get": {"summary": "Test endpoint"}}}}
            mock_fetch.return_value = mock_spec
            mock_extract.return_value = [{"method": "GET", "path": "/test", "summary": "Test endpoint"}]

            # Make request
            request_data = {"name": "test-service", "base_url": "http://localhost:8000"}

            response = client.post("/discover", json=request_data)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] in ["service_discovery_started", "service_discovery_completed"]
            ]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == "service_discovery_started")
            start_data = start_call[0][1]
            assert start_data["service_name"] == "test-service"
            assert start_data["base_url"] == "http://localhost:8000"
            assert "request_id" in start_data

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == "service_discovery_completed")
            completion_data = completion_call[0][1]
            assert completion_data["service_name"] == "test-service"
            assert completion_data["success"] is True
            assert completion_data["endpoints_discovered"] == 1
            assert "processing_time_seconds" in completion_data

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            assert perf_call[0][0] == "service_discovery"
            assert "discovery_success" in perf_call[0][2]
            assert perf_call[0][2]["discovery_success"] is True

    @pytest.mark.asyncio
    async def test_service_discovery_failure_logging(self, client, mock_logger_client):
        """Test failed service discovery logging."""
        # Mock the fetch function to return None (spec not found)
        with patch("services.discovery_agent.main.fetch_openapi_spec_with_fallback") as mock_fetch:
            mock_fetch.return_value = None

            # Make request
            request_data = {"name": "test-service", "base_url": "http://localhost:8000"}

            response = client.post("/discover", json=request_data)
            assert response.status_code == 200  # Error responses are wrapped in success response format

            response_data = response.json()
            assert response_data["success"] is False

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "Could not fetch OpenAPI spec for test-service" in error_call[0][0]
            assert error_call[0][1]["service_name"] == "test-service"
            assert error_call[0][1]["error_type"] == "spec_fetch_failed"

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "service_discovery_failed"
            ]
            assert len(failure_events) >= 1

    @pytest.mark.asyncio
    async def test_service_discovery_exception_logging(self, client, mock_logger_client):
        """Test service discovery exception logging."""
        # Mock the fetch function to raise an exception
        with patch("services.discovery_agent.main.fetch_openapi_spec_with_fallback") as mock_fetch:
            mock_fetch.side_effect = Exception("Network timeout")

            # Make request
            request_data = {"name": "test-service", "base_url": "http://localhost:8000"}

            response = client.post("/discover", json=request_data)
            assert response.status_code == 200  # Error responses are wrapped

            response_data = response.json()
            assert response_data["success"] is False

            # Verify exception logging
            assert mock_logger_client.log_error.call_count >= 1

            # Check exception error call
            error_calls = mock_logger_client.log_error.call_args_list
            exception_call = next((call for call in error_calls if "Network timeout" in call[0][0]), None)
            assert exception_call is not None
            assert exception_call[0][1]["error_type"] == "Exception"

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
        assert business_call[0][0] == "discovery_agent_startup"
        startup_data = business_call[0][1]
        assert "capabilities" in startup_data
        assert "features" in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert "Discovery Agent service started" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_shutdown_logging(self, mock_logger_client):
        """Test service shutdown logging."""
        from services.discovery_agent.main import shutdown_event

        # Set logger client
        global logger_client
        logger_client = mock_logger_client

        await shutdown_event()

        # Verify shutdown logging
        assert mock_logger_client.log_info.call_count >= 1

        info_call = mock_logger_client.log_info.call_args
        assert "Discovery Agent service shutting down" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        with patch("services.discovery_agent.main.fetch_openapi_spec_with_fallback") as mock_fetch, patch(
            "services.discovery_agent.main.extract_endpoints_from_spec"
        ) as mock_extract:

            # Setup mocks
            mock_spec = {"openapi": "3.0.0", "paths": {"/test": {"get": {"summary": "Test endpoint"}}}}
            mock_fetch.return_value = mock_spec
            mock_extract.return_value = [{"method": "GET", "path": "/test", "summary": "Test endpoint"}]

            # Make request - should still work without logging
            request_data = {"name": "test-service", "base_url": "http://localhost:8000"}

            response = client.post("/discover", json=request_data)
            assert response.status_code == 200

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        with patch("services.discovery_agent.main.fetch_openapi_spec_with_fallback") as mock_fetch, patch(
            "services.discovery_agent.main.extract_endpoints_from_spec"
        ) as mock_extract:

            # Setup mocks
            mock_spec = {"openapi": "3.0.0", "paths": {"/test": {"get": {"summary": "Test endpoint"}}}}
            mock_fetch.return_value = mock_spec
            mock_extract.return_value = [{"method": "GET", "path": "/test", "summary": "Test endpoint"}]

            request_data = {"name": "test-service", "base_url": "http://localhost:8000"}

            client.post("/discover", json=request_data)

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
            assert request_id.startswith("discovery_")

    @pytest.mark.asyncio
    async def test_inline_spec_success_logging(self, client, mock_logger_client):
        """Test successful discovery with inline spec."""
        # Mock only the extract function since spec is provided inline
        with patch("services.discovery_agent.main.extract_endpoints_from_spec") as mock_extract:
            mock_extract.return_value = [{"method": "POST", "path": "/analyze", "summary": "Analyze documents"}]

            # Make request with inline spec
            request_data = {
                "name": "analysis-service",
                "base_url": "http://localhost:5000",
                "spec": {"openapi": "3.0.0", "paths": {"/analyze": {"post": {"summary": "Analyze documents"}}}},
            }

            response = client.post("/discover", json=request_data)
            assert response.status_code == 200

            # Check that spec_source is correctly identified as "inline"
            completion_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "service_discovery_completed"
            ]
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            assert completion_data["spec_source"] == "inline"
            assert completion_data["endpoints_discovered"] == 1

    @pytest.mark.asyncio
    async def test_url_normalization_logging(self, client, mock_logger_client):
        """Test that URL normalization is properly tracked."""
        with patch("services.discovery_agent.main.fetch_openapi_spec_with_fallback") as mock_fetch, patch(
            "services.discovery_agent.main.extract_endpoints_from_spec"
        ) as mock_extract:

            # Setup mocks
            mock_spec = {"openapi": "3.0.0", "paths": {"/test": {"get": {"summary": "Test endpoint"}}}}
            mock_fetch.return_value = mock_spec
            mock_extract.return_value = [{"method": "GET", "path": "/test", "summary": "Test endpoint"}]

            # Make request with localhost URL that should be normalized
            request_data = {"name": "test-service", "base_url": "http://localhost:8000"}

            response = client.post("/discover", json=request_data)
            assert response.status_code == 200

            # Check that the normalized URL is logged
            completion_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "service_discovery_completed"
            ]
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            # The base_url should be normalized (though in this test it's the same)
            assert "base_url" in completion_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
