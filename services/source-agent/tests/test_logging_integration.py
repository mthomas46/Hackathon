"""Tests for Source Agent logging integration with LogCollectorClient."""

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


class TestSourceAgentLoggingIntegration:
    """Test Source Agent logging integration with LogCollectorClient."""

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
    async def test_document_fetch_github_successful_logging(self, client, mock_logger_client):
        """Test successful GitHub document fetch logging."""
        # Mock the fetch handler
        mock_result = {
            "content": "# Test README\nThis is a test repository.",
            "metadata": {"source": "github", "owner": "testuser", "repo": "testrepo"},
            "title": "README.md",
        }

        with patch("main.fetch_handler") as mock_fetch_handler:
            mock_fetch_handler.fetch_github_document.return_value = mock_result

            # Make request
            request_data = {
                "source": "github",
                "identifier": "testuser:testrepo",
                "doc_type": "readme",
                "include_metadata": True,
            }

            response = client.post("/docs/fetch", json=request_data)
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["content"] == mock_result["content"]

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1
            assert mock_logger_client.log_info.call_count >= 2  # general + github specific

            # Check business events
            business_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] in ["document_fetch_started", "document_fetch_completed"]
            ]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == "document_fetch_started")
            start_data = start_call[0][1]
            assert start_data["source"] == "github"
            assert start_data["identifier"] == "testuser:testrepo"
            assert start_data["document_type"] == "readme"
            assert start_data["has_auth"] is False  # No auth_token provided
            assert start_data["include_metadata"] is True
            assert "request_id" in start_data

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == "document_fetch_completed")
            completion_data = completion_call[0][1]
            assert completion_data["source"] == "github"
            assert completion_data["identifier"] == "testuser:testrepo"
            assert completion_data["document_type"] == "readme"
            assert completion_data["has_content"] is True
            assert completion_data["has_metadata"] is True
            assert completion_data["success"] is True
            assert "processing_time_seconds" in completion_data
            assert "result_size_bytes" in completion_data

    @pytest.mark.asyncio
    async def test_document_fetch_jira_successful_logging(self, client, mock_logger_client):
        """Test successful Jira document fetch logging."""
        # Mock the fetch handler
        mock_result = {
            "content": "Jira issue description with details",
            "metadata": {"source": "jira", "issue_key": "PROJ-123"},
            "title": "PROJ-123: Feature Implementation",
        }

        with patch("main.fetch_handler") as mock_fetch_handler:
            mock_fetch_handler.fetch_jira_document.return_value = mock_result

            # Make request
            request_data = {
                "source": "jira",
                "identifier": "PROJ-123",
                "doc_type": "issue",
                "auth_token": "jira_token_123",
            }

            response = client.post("/docs/fetch", json=request_data)
            assert response.status_code == 200

            # Check that Jira-specific logging occurred
            info_calls = mock_logger_client.log_info.call_args_list
            jira_call = next((call for call in info_calls if "Jira issue/ticket" in call[0][0]), None)
            assert jira_call is not None
            assert jira_call[0][1]["jira_identifier"] == "PROJ-123"

    @pytest.mark.asyncio
    async def test_document_fetch_confluence_successful_logging(self, client, mock_logger_client):
        """Test successful Confluence document fetch logging."""
        # Mock the fetch handler
        mock_result = {
            "content": "Confluence page content with documentation",
            "metadata": {"source": "confluence", "page_id": "12345"},
            "title": "API Documentation",
        }

        with patch("main.fetch_handler") as mock_fetch_handler:
            mock_fetch_handler.fetch_confluence_document.return_value = mock_result

            # Make request
            request_data = {
                "source": "confluence",
                "identifier": "page_12345",
                "doc_type": "page",
                "auth_token": "confluence_token_456",
            }

            response = client.post("/docs/fetch", json=request_data)
            assert response.status_code == 200

            # Check that Confluence-specific logging occurred
            info_calls = mock_logger_client.log_info.call_args_list
            confluence_call = next((call for call in info_calls if "Confluence page" in call[0][0]), None)
            assert confluence_call is not None
            assert confluence_call[0][1]["confluence_identifier"] == "page_12345"

    @pytest.mark.asyncio
    async def test_document_fetch_unsupported_source_logging(self, client, mock_logger_client):
        """Test unsupported source error logging."""
        # Make request with unsupported source
        request_data = {"source": "unsupported_source", "identifier": "test:123", "doc_type": "document"}

        response = client.post("/docs/fetch", json=request_data)
        assert response.status_code == 400

        # Verify error logging
        assert mock_logger_client.log_error.call_count >= 1
        assert mock_logger_client.log_business_event.call_count >= 2  # start and failed

        # Check error call
        error_calls = mock_logger_client.log_error.call_args_list
        source_error = next((call for call in error_calls if "Unsupported source" in call[0][0]), None)
        assert source_error is not None
        assert source_error[0][1]["source"] == "unsupported_source"
        assert source_error[0][1]["error_type"] == "unsupported_source"

        # Check failure business event
        failure_events = [
            call
            for call in mock_logger_client.log_business_event.call_args_list
            if call[0][0] == "document_fetch_failed"
        ]
        assert len(failure_events) >= 1

        failure_data = failure_events[0][0][1]
        assert failure_data["source"] == "unsupported_source"
        assert failure_data["error_type"] == "unsupported_source"

    @pytest.mark.asyncio
    async def test_document_fetch_failure_logging(self, client, mock_logger_client):
        """Test document fetch failure logging."""
        # Mock the fetch handler to raise an exception
        with patch("main.fetch_handler") as mock_fetch_handler:
            mock_fetch_handler.fetch_github_document.side_effect = Exception("GitHub API rate limit exceeded")

            # Make request
            request_data = {"source": "github", "identifier": "testuser:testrepo", "doc_type": "readme"}

            response = client.post("/docs/fetch", json=request_data)
            assert response.status_code >= 400  # Should fail

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failed

            # Check error call
            error_calls = mock_logger_client.log_error.call_args_list
            fetch_error = next((call for call in error_calls if "Document fetch failed" in call[0][0]), None)
            assert fetch_error is not None
            assert fetch_error[0][1]["source"] == "github"
            assert fetch_error[0][1]["error_type"] == "Exception"
            assert fetch_error[0][1]["external_api_failure"] is True

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "document_fetch_failed"
            ]
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data["source"] == "github"
            assert failure_data["error_type"] == "Exception"
            assert "GitHub API rate limit exceeded" in failure_data["error_message"]

    @pytest.mark.asyncio
    async def test_different_document_types_logging(self, client, mock_logger_client):
        """Test logging for different document types."""
        document_types = ["readme", "issue", "pr", "page"]

        for doc_type in document_types:
            # Determine source based on doc_type
            if doc_type in ["readme", "pr"]:
                source = "github"
                identifier = "testuser:testrepo"
                mock_method = "fetch_github_document"
            elif doc_type == "issue":
                source = "jira"
                identifier = "PROJ-123"
                mock_method = "fetch_jira_document"
            else:  # page
                source = "confluence"
                identifier = "page_123"
                mock_method = "fetch_confluence_document"

            # Mock the fetch handler
            mock_result = {
                "content": f"Content for {doc_type}",
                "metadata": {"source": source, "type": doc_type},
                "title": f"Test {doc_type.title()}",
            }

            with patch("main.fetch_handler") as mock_fetch_handler:
                getattr(mock_fetch_handler, mock_method).return_value = mock_result

                # Make request
                request_data = {"source": source, "identifier": identifier, "doc_type": doc_type}

                response = client.post("/docs/fetch", json=request_data)
                assert response.status_code == 200

                # Check completion event has correct document type
                completion_events = [
                    call
                    for call in mock_logger_client.log_business_event.call_args_list
                    if call[0][0] == "document_fetch_completed"
                ]

                # Get the most recent completion event
                completion_data = completion_events[-1][0][1]
                assert completion_data["document_type"] == doc_type
                assert completion_data["source"] == source

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
        assert business_call[0][0] == "source_agent_startup"
        startup_data = business_call[0][1]
        assert "capabilities" in startup_data
        assert "supported_sources" in startup_data
        assert "integrations" in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert "Source Agent service started" in info_call[0][0]

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
        assert "Source Agent service shutting down" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        # Mock the fetch handler
        mock_result = {"content": "Test content", "metadata": {}}

        with patch("main.fetch_handler") as mock_fetch_handler:
            mock_fetch_handler.fetch_github_document.return_value = mock_result

            # Make request - should still work without logging
            request_data = {"source": "github", "identifier": "testuser:testrepo", "doc_type": "readme"}

            response = client.post("/docs/fetch", json=request_data)
            assert response.status_code == 200

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        # Mock the fetch handler
        mock_result = {"content": "Test content"}

        with patch("main.fetch_handler") as mock_fetch_handler:
            mock_fetch_handler.fetch_github_document.return_value = mock_result

            # Make request
            request_data = {"source": "github", "identifier": "testuser:testrepo", "doc_type": "readme"}
            client.post("/docs/fetch", json=request_data)

            # Check that request IDs are generated and used consistently
            business_calls = mock_logger_client.log_business_event.call_args_list
            perf_calls = mock_logger_client.log_performance_metric.call_args_list

            # Extract request IDs from all calls
            request_ids = set()
            for call in business_calls + perf_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get("request_id")
                    if request_id and "document_fetch" in call[0][0]:
                        request_ids.add(request_id)

            # All document fetch calls should use the same request ID
            assert len(request_ids) == 1
            request_id = list(request_ids)[0]
            assert request_id.startswith("source_fetch_")

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        # Mock the fetch handler
        mock_result = {"content": "Test content", "metadata": {"large": "data" * 100}}

        with patch("main.fetch_handler") as mock_fetch_handler:
            mock_fetch_handler.fetch_github_document.return_value = mock_result

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            # Make request
            request_data = {"source": "github", "identifier": "testuser:testrepo", "doc_type": "readme"}
            response = client.post("/docs/fetch", json=request_data)
            assert response.status_code == 200

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            fetch_perf = next((call for call in perf_calls if call[0][0] == "document_fetch"), None)
            assert fetch_perf is not None

            processing_time = fetch_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

            # Check performance metric data
            perf_data = fetch_perf[0][2]
            assert perf_data["fetch_success"] is True
            assert perf_data["result_has_content"] is True
            assert perf_data["source"] == "github"
            assert perf_data["document_type"] == "readme"

    @pytest.mark.asyncio
    async def test_result_metrics_calculation(self, client, mock_logger_client):
        """Test that result metrics are calculated correctly."""
        test_cases = [
            ({"content": "Has content", "metadata": {"key": "value"}}, True, True, "content and metadata"),
            ({"content": "Only content"}, True, False, "content only"),
            ({"metadata": {"key": "value"}}, False, True, "metadata only"),
            ({}, False, False, "empty result"),
            (None, False, False, "None result"),
        ]

        for mock_result, expected_has_content, expected_has_metadata, description in test_cases:
            with patch("main.fetch_handler") as mock_fetch_handler:
                mock_fetch_handler.fetch_github_document.return_value = mock_result

                # Make request
                request_data = {"source": "github", "identifier": "testuser:testrepo", "doc_type": "readme"}
                response = client.post("/docs/fetch", json=request_data)
                assert response.status_code == 200

                # Check completion event metrics
                completion_events = [
                    call
                    for call in mock_logger_client.log_business_event.call_args_list
                    if call[0][0] == "document_fetch_completed"
                ]

                completion_data = completion_events[-1][0][1]  # Most recent
                assert completion_data["has_content"] == expected_has_content, f"Failed for {description}"
                assert completion_data["has_metadata"] == expected_has_metadata, f"Failed for {description}"
                assert "result_size_bytes" in completion_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
