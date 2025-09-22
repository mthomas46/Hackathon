"""Tests for Code Analyzer logging integration with LogCollectorClient."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

from services.shared.utilities.logging_client import LogCollectorClient


class TestCodeAnalyzerLoggingIntegration:
    """Test Code Analyzer logging integration with LogCollectorClient."""

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
    async def test_code_analysis_successful_logging(self, client, mock_logger_client):
        """Test successful code analysis logging."""
        # Make request
        request_data = {
            "code": "def hello():\n    print('Hello, World!')\n\nclass TestClass:\n    def method(self):\n        pass",
            "language": "python",
            "include_functions": True,
            "include_classes": True,
        }

        response = client.post("/analyze", json=request_data)
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
            if call[0][0] in ["code_analysis_started", "code_analysis_completed"]
        ]

        assert len(business_calls) == 2

        # Check start event
        start_call = next(call for call in business_calls if call[0][0] == "code_analysis_started")
        start_data = start_call[0][1]
        assert start_data["language"] == "python"
        assert start_data["code_length"] == len(request_data["code"])
        assert start_data["include_functions"] is True
        assert start_data["include_classes"] is True
        assert start_data["analysis_type"] == "structural"
        assert "request_id" in start_data

        # Check completion event
        completion_call = next(call for call in business_calls if call[0][0] == "code_analysis_completed")
        completion_data = completion_call[0][1]
        assert completion_data["language"] == "python"
        assert completion_data["functions_found"] == 1  # example_function
        assert completion_data["classes_found"] == 1  # ExampleClass
        assert completion_data["patterns_identified"] == 2  # factory, singleton
        assert completion_data["overall_complexity"] == 5
        assert completion_data["success"] is True
        assert "processing_time_seconds" in completion_data

        # Check performance metric
        perf_call = mock_logger_client.log_performance_metric.call_args
        assert perf_call[0][0] == "code_analysis"
        assert "analysis_success" in perf_call[0][2]
        assert perf_call[0][2]["analysis_success"] is True
        assert perf_call[0][2]["elements_found"] == 4  # 1 function + 1 class + 2 patterns

    @pytest.mark.asyncio
    async def test_code_analysis_minimal_scope_logging(self, client, mock_logger_client):
        """Test code analysis with minimal scope (functions and classes disabled)."""
        # Make request with minimal scope
        request_data = {
            "code": "print('Hello, World!')",
            "language": "python",
            "include_functions": False,
            "include_classes": False,
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["success"] is True

        # Check that functions and classes are empty in response
        analysis_data = response_data["data"]
        assert len(analysis_data["functions"]) == 0
        assert len(analysis_data["classes"]) == 0

        # Check completion event reflects minimal scope
        completion_events = [
            call
            for call in mock_logger_client.log_business_event.call_args_list
            if call[0][0] == "code_analysis_completed"
        ]
        assert len(completion_events) >= 1

        completion_data = completion_events[0][0][1]
        assert completion_data["functions_found"] == 0
        assert completion_data["classes_found"] == 0
        assert completion_data["patterns_identified"] == 2  # patterns are always included

        # Check performance metric reflects minimal elements found
        perf_call = mock_logger_client.log_performance_metric.call_args
        assert perf_call[0][2]["elements_found"] == 2  # only patterns

    @pytest.mark.asyncio
    async def test_code_analysis_failure_logging(self, client, mock_logger_client):
        """Test failed code analysis logging."""
        # Mock an exception in the analysis
        with patch("main.time") as mock_time:
            mock_time.time.side_effect = [1000.0, Exception("Analysis engine error")]

            # Make request
            request_data = {
                "code": "def broken_code(",
                "language": "python",
                "include_functions": True,
                "include_classes": True,
            }

            response = client.post("/analyze", json=request_data)
            assert response.status_code == 200  # Error responses are wrapped

            response_data = response.json()
            assert response_data["success"] is False
            assert "Analysis engine error" in response_data["error"]

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "Code analysis failed: Analysis engine error" in error_call[0][0]
            assert error_call[0][1]["language"] == "python"
            assert error_call[0][1]["code_length"] == len("def broken_code(")
            assert error_call[0][1]["error_type"] == "Exception"

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "code_analysis_failed"
            ]
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data["language"] == "python"
            assert failure_data["error_type"] == "Exception"
            assert "Analysis engine error" in failure_data["error_message"]

    @pytest.mark.asyncio
    async def test_code_analysis_different_languages_logging(self, client, mock_logger_client):
        """Test code analysis logging for different programming languages."""
        languages = ["javascript", "java", "go"]

        for language in languages:
            # Make request for each language
            request_data = {
                "code": f"// {language} code sample",
                "language": language,
                "include_functions": True,
                "include_classes": True,
            }

            response = client.post("/analyze", json=request_data)
            assert response.status_code == 200

            # Check that language is correctly logged
            completion_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "code_analysis_completed"
            ]

            # Get the most recent completion event
            completion_data = completion_events[-1][0][1]
            assert completion_data["language"] == language

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
        assert business_call[0][0] == "code_analyzer_startup"
        startup_data = business_call[0][1]
        assert "capabilities" in startup_data
        assert "supported_languages" in startup_data
        assert "features" in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert "Code Analyzer service started" in info_call[0][0]

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
        assert "Code Analyzer service shutting down" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        # Make request - should still work without logging
        request_data = {
            "code": "def test():\n    pass",
            "language": "python",
            "include_functions": True,
            "include_classes": False,
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["success"] is True

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        request_data = {
            "code": "print('test')",
            "language": "python",
            "include_functions": False,
            "include_classes": False,
        }

        client.post("/analyze", json=request_data)

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
        assert request_id.startswith("code_analysis_")

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        # Add small delay to ensure measurable processing time
        await asyncio.sleep(0.01)

        request_data = {
            "code": "class Test:\n    def method(self):\n        return True",
            "language": "python",
            "include_functions": True,
            "include_classes": True,
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        # Check performance metric
        perf_call = mock_logger_client.log_performance_metric.call_args
        processing_time = perf_call[0][1]

        # Processing time should be reasonable (between 0 and 1 second)
        assert 0 <= processing_time <= 1

        # Should be at least the sleep time we added
        assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_complexity_scoring_accuracy(self, client, mock_logger_client):
        """Test that complexity scoring is accurately calculated and logged."""
        # Test with functions and classes enabled
        request_data = {
            "code": "def func1():\n    pass\n\ndef func2():\n    pass\n\nclass Class1:\n    pass\n\nclass Class2:\n    pass",
            "language": "python",
            "include_functions": True,
            "include_classes": True,
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        # Check completion event has correct complexity data
        completion_events = [
            call
            for call in mock_logger_client.log_business_event.call_args_list
            if call[0][0] == "code_analysis_completed"
        ]
        assert len(completion_events) >= 1

        completion_data = completion_events[0][0][1]
        assert completion_data["functions_found"] == 1  # example_function
        assert completion_data["classes_found"] == 1  # ExampleClass
        assert completion_data["patterns_identified"] == 2
        assert completion_data["overall_complexity"] == 5

        # Verify elements_found calculation in performance metric
        perf_call = mock_logger_client.log_performance_metric.call_args
        expected_elements = 1 + 1 + 2  # functions + classes + patterns
        assert perf_call[0][2]["elements_found"] == expected_elements


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
