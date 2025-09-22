"""Tests for Frontend logging integration with LogCollectorClient."""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app, logger_client

from services.shared.utilities.logging_client import LogCollectorClient


class TestFrontendLoggingIntegration:
    """Test Frontend logging integration with LogCollectorClient."""

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
    async def test_logs_dashboard_access_logging(self, client, mock_logger_client):
        """Test logs dashboard page access logging."""
        # Mock the UI handlers
        with patch("main.ui_handlers") as mock_ui_handlers:
            mock_ui_handlers.handle_logs_dashboard.return_value = {"dashboard": "logs"}

            # Make request to logs dashboard
            response = client.get("/logs/dashboard")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # access and render
            assert mock_logger_client.log_info.call_count >= 1

            # Check page access event
            access_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "frontend_page_access"
            ]
            assert len(access_events) >= 1

            access_data = access_events[0][0][1]
            assert access_data["page"] == "logs_dashboard"
            assert access_data["page_type"] == "monitoring_dashboard"
            assert "log_viewer" in access_data["features"]
            assert access_data["access_type"] == "user_navigation"
            assert "request_id" in access_data

            # Check page render event
            render_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "frontend_page_rendered"
            ]
            assert len(render_events) >= 1

            render_data = render_events[0][0][1]
            assert render_data["page"] == "logs_dashboard"
            assert render_data["render_success"] is True
            assert "processing_time_seconds" in render_data

    @pytest.mark.asyncio
    async def test_logs_dashboard_failure_logging(self, client, mock_logger_client):
        """Test logs dashboard rendering failure logging."""
        # Mock the UI handlers to raise an exception
        with patch("main.ui_handlers") as mock_ui_handlers:
            mock_ui_handlers.handle_logs_dashboard.side_effect = Exception("Template rendering failed")

            # Make request to logs dashboard
            response = client.get("/logs/dashboard")
            assert response.status_code >= 400  # Should fail

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # access and render failed

            # Check error call
            error_calls = mock_logger_client.log_error.call_args_list
            dashboard_error = next(
                (call for call in error_calls if "Frontend logs dashboard rendering failed" in call[0][0]), None
            )
            assert dashboard_error is not None
            assert dashboard_error[0][1]["page"] == "logs_dashboard"
            assert dashboard_error[0][1]["error_type"] == "Exception"
            assert dashboard_error[0][1]["page_type"] == "monitoring_dashboard"

            # Check render failure event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "frontend_page_render_failed"
            ]
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data["page"] == "logs_dashboard"
            assert failure_data["error_type"] == "Exception"
            assert "Template rendering failed" in failure_data["error_message"]

    @pytest.mark.asyncio
    async def test_api_logs_fetch_success_logging(self, client, mock_logger_client):
        """Test successful logs API fetch logging."""
        # Mock the log fetching functions
        mock_logs = [
            {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "Test log 1"},
            {"timestamp": "2024-01-01T00:01:00Z", "level": "ERROR", "message": "Test log 2"},
        ]

        with patch("main.fetch_logs_from_collector") as mock_fetch_logs:
            mock_fetch_logs.return_value = mock_logs

            # Make request to fetch logs
            response = client.get("/api/logs/fetch?service=test_service&limit=50")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # api call and success
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check API call event
            api_call_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "frontend_api_call"
            ]
            assert len(api_call_events) >= 1

            api_call_data = api_call_events[0][0][1]
            assert api_call_data["api_endpoint"] == "fetch_logs"
            assert api_call_data["operation"] == "log_data_retrieval"
            assert api_call_data["filters_applied"] is True
            assert api_call_data["service_filter"] == "test_service"
            assert api_call_data["limit_requested"] == 50
            assert api_call_data["data_type"] == "system_logs"

            # Check API success event
            api_success_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "frontend_api_success"
            ]
            assert len(api_success_events) >= 1

            success_data = api_success_events[0][0][1]
            assert success_data["api_endpoint"] == "fetch_logs"
            assert success_data["logs_returned"] == 2
            assert success_data["filters_applied"] is True
            assert success_data["cache_updated"] is True
            assert success_data["success"] is True

    @pytest.mark.asyncio
    async def test_api_logs_fetch_failure_logging(self, client, mock_logger_client):
        """Test logs API fetch failure logging."""
        # Mock the log fetching function to raise an exception
        with patch("main.fetch_logs_from_collector") as mock_fetch_logs:
            mock_fetch_logs.side_effect = Exception("Log collector service unavailable")

            # Make request to fetch logs
            response = client.get("/api/logs/fetch?service=test_service")
            assert response.status_code == 200  # Error responses are wrapped in success format

            response_data = response.json()
            assert response_data["success"] is False

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # api call and failed

            # Check error call
            error_calls = mock_logger_client.log_error.call_args_list
            api_error = next((call for call in error_calls if "Frontend log fetching failed" in call[0][0]), None)
            assert api_error is not None
            assert api_error[0][1]["api_endpoint"] == "fetch_logs"
            assert api_error[0][1]["service_filter"] == "test_service"
            assert api_error[0][1]["error_type"] == "Exception"
            assert api_error[0][1]["log_collector_failure"] is True

            # Check API failure event
            api_failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "frontend_api_failed"
            ]
            assert len(api_failure_events) >= 1

            failure_data = api_failure_events[0][0][1]
            assert failure_data["api_endpoint"] == "fetch_logs"
            assert failure_data["error_type"] == "Exception"
            assert "Log collector service unavailable" in failure_data["error_message"]

    @pytest.mark.asyncio
    async def test_different_api_endpoints_logging(self, client, mock_logger_client):
        """Test logging for different API endpoints."""
        endpoints_and_operations = [
            ("/api/logs/fetch", "log_data_retrieval"),
            ("/api/logs/stats", "log_statistics_retrieval"),
            ("/api/logs/status", "log_status_retrieval"),
        ]

        for endpoint, expected_operation in endpoints_and_operations:
            # Mock the functions
            with patch("main.fetch_logs_from_collector") as mock_fetch_logs, patch(
                "main.fetch_log_stats_from_collector"
            ) as mock_stats, patch("main.get_cached_logs_data") as mock_cache:

                if "fetch" in endpoint:
                    mock_fetch_logs.return_value = []
                elif "stats" in endpoint:
                    mock_stats.return_value = {"total_logs": 100}
                else:  # status
                    mock_cache.return_value = {"logs": [], "stats": {}}

                # Make request
                response = client.get(endpoint)
                assert response.status_code == 200

                # Check API call event has correct operation type
                api_call_events = [
                    call
                    for call in mock_logger_client.log_business_event.call_args_list
                    if call[0][0] == "frontend_api_call"
                ]

                # Get the most recent API call event
                api_call_data = api_call_events[-1][0][1]
                assert api_call_data["api_endpoint"] in endpoint.split("/")[-1]
                assert api_call_data["operation"] == expected_operation

    @pytest.mark.asyncio
    async def test_logs_fetch_with_filters_logging(self, client, mock_logger_client):
        """Test logs fetch with different filter combinations."""
        filter_combinations = [
            {"service": "test_service"},
            {"level": "ERROR"},
            {"service": "test_service", "level": "WARN", "limit": "25"},
            {},  # No filters
        ]

        for filters in filter_combinations:
            # Mock the log fetching function
            with patch("main.fetch_logs_from_collector") as mock_fetch_logs:
                mock_fetch_logs.return_value = [{"test": "log"}]

                # Build query string
                query_params = "&".join([f"{k}={v}" for k, v in filters.items()])
                url = f"/api/logs/fetch?{query_params}" if query_params else "/api/logs/fetch"

                # Make request
                response = client.get(url)
                assert response.status_code == 200

                # Check that filters are logged correctly
                api_call_events = [
                    call
                    for call in mock_logger_client.log_business_event.call_args_list
                    if call[0][0] == "frontend_api_call"
                ]

                # Get the most recent API call event
                api_call_data = api_call_events[-1][0][1]

                expected_filters_applied = bool(filters)
                assert api_call_data["filters_applied"] == expected_filters_applied

                if "service" in filters:
                    assert api_call_data["service_filter"] == filters["service"]
                if "level" in filters:
                    assert api_call_data["level_filter"] == filters["level"]
                if "limit" in filters:
                    assert api_call_data["limit_requested"] == int(filters["limit"])

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
        assert business_call[0][0] == "frontend_startup"
        startup_data = business_call[0][1]
        assert "capabilities" in startup_data
        assert "ui_features" in startup_data
        assert "supported_pages" in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert "Frontend service started" in info_call[0][0]

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
        assert "Frontend service shutting down" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        # Mock the UI handlers
        with patch("main.ui_handlers") as mock_ui_handlers, patch("main.fetch_logs_from_collector") as mock_fetch_logs:

            mock_ui_handlers.handle_logs_dashboard.return_value = {"dashboard": "logs"}
            mock_fetch_logs.return_value = []

            # Make requests - should still work without logging
            response1 = client.get("/logs/dashboard")
            assert response1.status_code == 200

            response2 = client.get("/api/logs/fetch")
            assert response2.status_code == 200

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        # Mock the UI handlers and API functions
        with patch("main.ui_handlers") as mock_ui_handlers, patch("main.fetch_logs_from_collector") as mock_fetch_logs:

            mock_ui_handlers.handle_logs_dashboard.return_value = {"dashboard": "logs"}
            mock_fetch_logs.return_value = []

            # Make requests
            client.get("/logs/dashboard")
            client.get("/api/logs/fetch")

            # Check that request IDs are generated and used consistently
            business_calls = mock_logger_client.log_business_event.call_args_list

            # Extract request IDs from frontend events
            request_ids = set()
            for call in business_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get("request_id")
                    if request_id and "frontend" in call[0][0]:
                        request_ids.add(request_id)

            # Should have at least 2 different request IDs (one for each request)
            assert len(request_ids) >= 2

            # All request IDs should start with appropriate prefixes
            for request_id in request_ids:
                assert request_id.startswith(("frontend_logs_dashboard_", "frontend_log_fetch_"))

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        # Mock the API functions
        with patch("main.fetch_logs_from_collector") as mock_fetch_logs:
            mock_fetch_logs.return_value = [{"test": "log"}]

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            # Make request
            response = client.get("/api/logs/fetch?limit=10")
            assert response.status_code == 200

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            log_fetch_perf = next((call for call in perf_calls if call[0][0] == "frontend_log_fetch"), None)
            assert log_fetch_perf is not None

            processing_time = log_fetch_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

            # Check performance metric data
            perf_data = log_fetch_perf[0][2]
            assert perf_data["fetch_success"] is True
            assert perf_data["logs_returned"] == 1
            assert perf_data["filters_used"] is True  # limit parameter
            assert "log_collector_response_time" in perf_data

    @pytest.mark.asyncio
    async def test_page_render_performance_tracking(self, client, mock_logger_client):
        """Test that page rendering performance is tracked."""
        # Mock the UI handlers
        with patch("main.ui_handlers") as mock_ui_handlers:
            mock_ui_handlers.handle_logs_dashboard.return_value = {"dashboard": "logs"}

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            # Make request
            response = client.get("/logs/dashboard")
            assert response.status_code == 200

            # Check that page render time is tracked
            render_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "frontend_page_rendered"
            ]
            assert len(render_events) >= 1

            render_data = render_events[0][0][1]
            assert "processing_time_seconds" in render_data
            assert render_data["processing_time_seconds"] >= 0.01  # At least the sleep time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
