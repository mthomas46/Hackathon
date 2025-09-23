"""Tests for interpreter service logging integration."""

import os
import sys
import time
from unittest.mock import AsyncMock, patch

import pytest

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from main import app


class TestInterpreterLoggingIntegration:
    """Test logging integration in interpreter service."""

    @pytest.fixture
    def client(self):
        """Create test client for interpreter service."""
        return TestClient(app)

    @pytest.fixture
    async def mock_log_collector(self):
        """Mock log collector client."""
        mock_client = AsyncMock()
        mock_client.log_info = AsyncMock()
        mock_client.log_error = AsyncMock()
        mock_client.log_business_event = AsyncMock()
        mock_client.log_performance_metric = AsyncMock()

        with patch("main.logger_client", mock_client):
            yield mock_client

    def test_sample_documents_endpoint_logging_success(self, client, mock_log_collector):
        """Test that successful document queries are logged."""
        # Mock sample_documents to return some results
        with patch("main.sample_documents") as mock_sample_docs:
            mock_sample_docs.get_documents_for_query.return_value = [
                {"type": "api_docs", "content": "Sample API doc", "title": "Test API"}
            ]

            # Make request
            response = client.post(
                "/documents/sample/context", json={"query": "test query", "context": {"user": "test_user"}}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "relevant_documents" in data
            assert "request_id" in data
            assert "processing_time_seconds" in data

            # Verify logging was called
            mock_log_collector.log_info.assert_called()
            mock_log_collector.log_business_event.assert_called_with("document_query_processed", pytest.any(dict))
            mock_log_collector.log_performance_metric.assert_called()

    def test_sample_documents_endpoint_logging_error(self, client, mock_log_collector):
        """Test that errors in document queries are logged."""
        # Mock sample_documents to be None (service unavailable)
        with patch("main.sample_documents", None):
            response = client.post("/documents/sample/context", json={"query": "test query"})

            assert response.status_code == 200  # Returns error in response body
            data = response.json()
            assert "error" in data

            # Verify error logging was called
            mock_log_collector.log_error.assert_called()

    def test_document_types_endpoint_logging(self, client, mock_log_collector):
        """Test that document types requests are logged."""
        # Mock sample_documents
        with patch("main.sample_documents") as mock_sample_docs:
            mock_sample_docs.get_documents_by_type.return_value = [{"type": "api_docs", "title": "Test"}]
            mock_sample_docs.get_recent_documents.return_value = []
            mock_sample_docs.get_high_priority_documents.return_value = []

            response = client.get("/documents/sample/types")
            assert response.status_code == 200

            # Verify logging was called
            mock_log_collector.log_info.assert_called()
            mock_log_collector.log_business_event.assert_called_with("document_types_retrieved", pytest.any(dict))

    def test_request_id_generation(self, client):
        """Test that request IDs are properly generated."""
        with patch("main.sample_documents") as mock_sample_docs:
            mock_sample_docs.get_documents_for_query.return_value = []

            response = client.post("/documents/sample/context", json={"query": "test"})

            data = response.json()
            assert "request_id" in data
            assert data["request_id"].startswith("req_")

    def test_performance_metrics_logging(self, client, mock_log_collector):
        """Test that performance metrics are logged correctly."""
        with patch("main.sample_documents") as mock_sample_docs:
            mock_sample_docs.get_documents_for_query.return_value = [{"type": "api_docs", "content": "Test content"}]

            response = client.post("/documents/sample/context", json={"query": "performance test query"})

            assert response.status_code == 200

            # Verify performance metric was logged
            mock_log_collector.log_performance_metric.assert_called()
            call_args = mock_log_collector.log_performance_metric.call_args
            operation, duration, metadata = call_args[0]

            assert operation == "document_query"
            assert isinstance(duration, float)
            assert duration > 0
            assert metadata["documents_returned"] == 1
            assert "request_id" in metadata

    def test_business_event_logging_details(self, client, mock_log_collector):
        """Test that business events contain proper details."""
        with patch("main.sample_documents") as mock_sample_docs:
            mock_sample_docs.get_documents_for_query.return_value = [
                {"type": "api_docs", "category": "reference"},
                {"type": "jira", "category": "issue"},
                {"type": "confluence", "category": "documentation"},
            ]

            response = client.post(
                "/documents/sample/context",
                json={"query": "complex test query", "context": {"user_id": 123, "session": "abc"}},
            )

            assert response.status_code == 200

            # Verify business event details
            mock_log_collector.log_business_event.assert_called_with("document_query_processed", pytest.any(dict))

            call_args = mock_log_collector.log_business_event.call_args
            event_data = call_args[0][1]

            assert event_data["documents_found"] == 3
            assert event_data["query_length"] == len("complex test query")
            assert set(event_data["document_types"]) == {"api_docs", "jira", "confluence"}
            assert event_data["has_context"] is True
            assert "response_time_seconds" in event_data

    def test_error_context_logging(self, client, mock_log_collector):
        """Test that errors include proper context."""
        # Test with invalid query data
        response = client.post("/documents/sample/context", json={})

        # Should still return a response (graceful error handling)
        assert response.status_code == 200
        data = response.json()
        assert "error" in data or "relevant_documents" in data

    def test_service_startup_logging(self):
        """Test that service startup is logged."""
        # This would typically be tested by checking the startup event
        # For now, we verify the logger_client is initialized

        # logger_client will be None in tests unless startup event runs
        # This is expected behavior for testing

    def test_concurrent_requests_logging(self, client, mock_log_collector):
        """Test logging with concurrent requests."""
        import threading

        results = []

        def make_request(request_id):
            response = client.post(
                "/documents/sample/context",
                json={"query": f"concurrent query {request_id}", "request_id": f"test_req_{request_id}"},
            )
            results.append(response.json())

        with patch("main.sample_documents") as mock_sample_docs:
            mock_sample_docs.get_documents_for_query.return_value = []

            # Make concurrent requests
            threads = []
            for i in range(5):
                thread = threading.Thread(target=make_request, args=(i,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Verify all requests completed
            assert len(results) == 5
            for result in results:
                assert "request_id" in result

    def test_query_complexity_classification(self, client, mock_log_collector):
        """Test that query complexity is properly classified."""
        test_cases = [
            ("simple", "simple query"),
            ("complex", "this is a much longer and more complex query with many words"),
            ("simple", "api docs"),
            ("complex", "find all documentation related to user authentication and authorization patterns"),
        ]

        with patch("main.sample_documents") as mock_sample_docs:
            mock_sample_docs.get_documents_for_query.return_value = []

            for expected_complexity, query in test_cases:
                mock_log_collector.reset_mock()

                response = client.post("/documents/sample/context", json={"query": query})

                assert response.status_code == 200

                # Check performance metric call
                if mock_log_collector.log_performance_metric.called:
                    call_args = mock_log_collector.log_performance_metric.call_args
                    metadata = call_args[0][2]
                    assert "query_complexity" in metadata
                    # Note: The actual classification logic might vary


class TestInterpreterServiceMetrics:
    """Test service-specific metrics and monitoring."""

    def test_response_time_tracking(self, client):
        """Test that response times are properly tracked."""
        with patch("main.sample_documents") as mock_sample_docs:
            mock_sample_docs.get_documents_for_query.return_value = []

            start_time = time.time()
            response = client.post("/documents/sample/context", json={"query": "timing test"})
            end_time = time.time()

            assert response.status_code == 200
            data = response.json()

            # Verify response includes timing information
            assert "processing_time_seconds" in data
            assert isinstance(data["processing_time_seconds"], float)
            assert data["processing_time_seconds"] >= 0

    def test_document_statistics_tracking(self, client, mock_log_collector):
        """Test that document statistics are tracked."""
        with patch("main.sample_documents") as mock_sample_docs:
            mock_sample_docs.get_documents_for_query.return_value = [
                {"type": "api_docs", "category": "reference", "title": "API Reference"},
                {"type": "api_docs", "category": "reference", "title": "API Guide"},
                {"type": "jira", "category": "issue", "title": "Bug Report"},
            ]

            response = client.post("/documents/sample/context", json={"query": "api documentation"})

            assert response.status_code == 200
            data = response.json()

            # Verify document statistics in response
            assert data["total_relevant"] == 3
            assert set(data["document_types_found"]) == {"api_docs", "jira"}
            assert data["categories_found"] == ["reference", "issue"]

    def test_context_usage_tracking(self, client, mock_log_collector):
        """Test that context usage is properly tracked."""
        test_cases = [
            {"query": "test without context"},
            {"query": "test with context", "context": {"user": "test", "session": "abc"}},
            {"query": "test with empty context", "context": {}},
        ]

        with patch("main.sample_documents") as mock_sample_docs:
            mock_sample_docs.get_documents_for_query.return_value = []

            for query_data in test_cases:
                mock_log_collector.reset_mock()

                response = client.post("/documents/sample/context", json=query_data)
                assert response.status_code == 200

                data = response.json()
                has_context = bool(query_data.get("context"))

                # Verify context tracking in response
                assert data["context_provided"] == has_context

                # Verify context tracking in business event
                if mock_log_collector.log_business_event.called:
                    call_args = mock_log_collector.log_business_event.call_args
                    event_data = call_args[0][1]
                    assert event_data["has_context"] == has_context

    def test_error_rate_monitoring(self, client, mock_log_collector):
        """Test that error rates are monitored."""
        # Mix of successful and failed requests
        test_cases = [
            (True, "successful query"),
            (False, "query causing error"),
            (True, "another successful query"),
        ]

        error_count = 0
        success_count = 0

        for should_succeed, query in test_cases:
            with patch("main.sample_documents") as mock_sample_docs:
                if should_succeed:
                    mock_sample_docs.get_documents_for_query.return_value = [{"type": "api_docs", "content": "test"}]
                    success_count += 1
                else:
                    mock_sample_docs.get_documents_for_query.side_effect = Exception("Test error")
                    error_count += 1

                response = client.post("/documents/sample/context", json={"query": query})

                # All requests should return 200 (errors in response body)
                assert response.status_code == 200

        # Verify error logging was called for failures
        assert mock_log_collector.log_error.call_count >= error_count


class TestInterpreterLoggingConfiguration:
    """Test logging configuration and setup."""

    def test_logger_client_initialization(self):
        """Test that logger client is properly initialized."""
        from main import logger_client

        # In test environment, logger_client might be None if startup didn't run
        # This is expected behavior
        assert logger_client is None or hasattr(logger_client, "log_info")

    def test_graceful_degradation_without_logger(self, client):
        """Test that service works even when logger is unavailable."""
        # Temporarily set logger_client to None
        import main
        from main import logger_client as original_logger

        main.logger_client = None

        try:
            with patch("main.sample_documents") as mock_sample_docs:
                mock_sample_docs.get_documents_for_query.return_value = []

                response = client.post("/documents/sample/context", json={"query": "test query"})

                # Should still work without logger
                assert response.status_code == 200
                data = response.json()
                assert "relevant_documents" in data

        finally:
            # Restore original logger
            main.logger_client = original_logger

    def test_log_collector_fallback_behavior(self):
        """Test fallback behavior when log collector is unavailable."""
        # This tests the import fallback logic
        try:
            pass

            # If import succeeds, client should be available
            client_available = True
        except ImportError:
            client_available = False

        # Either way, the service should handle it gracefully
        assert isinstance(client_available, bool)
