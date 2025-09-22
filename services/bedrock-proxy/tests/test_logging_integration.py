"""Tests for Bedrock Proxy logging integration with LogCollectorClient."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

from services.shared.utilities.logging_client import LogCollectorClient


class TestBedrockProxyLoggingIntegration:
    """Test Bedrock Proxy logging integration with LogCollectorClient."""

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
    async def test_bedrock_invoke_successful_logging(self, client, mock_logger_client):
        """Test successful Bedrock invoke logging."""
        # Mock the processor function
        mock_result = {
            "content": "This is a structured response from the template engine.",
            "template": "summary",
            "format": "md",
            "model": "anthropic.claude-3-sonnet-20240229-v1:0",
        }

        with patch("main.process_invoke_request") as mock_processor:
            mock_processor.return_value = mock_result

            # Make request
            request_data = {
                "prompt": "Summarize the following requirements",
                "template": "summary",
                "format": "md",
                "model": "anthropic.claude-3-sonnet-20240229-v1:0",
                "region": "us-east-1",
                "title": "Requirements Summary",
                "params": {"max_tokens": 500},
            }

            response = client.post("/invoke", json=request_data)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] in ["bedrock_invoke_started", "bedrock_invoke_completed"]
            ]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == "bedrock_invoke_started")
            start_data = start_call[0][1]
            assert start_data["model"] == "anthropic.claude-3-sonnet-20240229-v1:0"
            assert start_data["template"] == "summary"
            assert start_data["format"] == "md"
            assert start_data["region"] == "us-east-1"
            assert start_data["prompt_length"] == len("Summarize the following requirements")
            assert start_data["has_title"] is True
            assert start_data["has_params"] is True
            assert start_data["stub_mode"] is True
            assert "request_id" in start_data

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == "bedrock_invoke_completed")
            completion_data = completion_call[0][1]
            assert completion_data["model"] == "anthropic.claude-3-sonnet-20240229-v1:0"
            assert completion_data["template"] == "summary"
            assert completion_data["format"] == "md"
            assert completion_data["structured_output"] is True  # Has 'content' key
            assert completion_data["success"] is True
            assert "processing_time_seconds" in completion_data
            assert "response_length" in completion_data

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            assert perf_call[0][0] == "bedrock_invoke"
            assert "invoke_success" in perf_call[0][2]
            assert perf_call[0][2]["invoke_success"] is True
            assert perf_call[0][2]["stub_mode"] is True

    @pytest.mark.asyncio
    async def test_bedrock_invoke_minimal_request_logging(self, client, mock_logger_client):
        """Test Bedrock invoke with minimal parameters."""
        # Mock the processor function
        mock_result = "Simple text response without structure"

        with patch("main.process_invoke_request") as mock_processor:
            mock_processor.return_value = mock_result

            # Make request with minimal parameters
            request_data = {"prompt": "Hello world"}

            response = client.post("/invoke", json=request_data)
            assert response.status_code == 200

            # Check start event reflects minimal parameters
            start_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "bedrock_invoke_started"
            ]
            assert len(start_events) >= 1

            start_data = start_events[0][0][1]
            assert start_data["prompt_length"] == len("Hello world")
            assert start_data["has_title"] is False
            assert start_data["has_params"] is False
            assert start_data["template"] is None
            assert start_data["format"] is None
            assert start_data["model"] is None

            # Check completion event for unstructured response
            completion_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "bedrock_invoke_completed"
            ]
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            assert completion_data["structured_output"] is False  # No 'content' key

    @pytest.mark.asyncio
    async def test_bedrock_invoke_failure_logging(self, client, mock_logger_client):
        """Test failed Bedrock invoke logging."""
        # Mock the processor to raise an exception
        with patch("main.process_invoke_request") as mock_processor:
            mock_processor.side_effect = Exception("Template processing failed")

            # Make request
            request_data = {
                "prompt": "Generate a summary",
                "template": "summary",
                "format": "json",
                "model": "test-model",
            }

            response = client.post("/invoke", json=request_data)
            assert response.status_code >= 400  # Should fail

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "Bedrock invoke failed: Template processing failed" in error_call[0][0]
            assert error_call[0][1]["model"] == "test-model"
            assert error_call[0][1]["template"] == "summary"
            assert error_call[0][1]["format"] == "json"
            assert error_call[0][1]["error_type"] == "Exception"
            assert error_call[0][1]["stub_mode"] is True

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "bedrock_invoke_failed"
            ]
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data["model"] == "test-model"
            assert failure_data["template"] == "summary"
            assert failure_data["format"] == "json"
            assert failure_data["error_type"] == "Exception"
            assert "Template processing failed" in failure_data["error_message"]

    @pytest.mark.asyncio
    async def test_bedrock_invoke_different_templates_logging(self, client, mock_logger_client):
        """Test Bedrock invoke logging for different template types."""
        templates = ["summary", "risks", "decisions", "pr_confidence"]

        for template in templates:
            # Mock the processor
            mock_result = {
                "content": f"Generated content for {template} template",
                "template": template,
                "confidence": 0.85 if template == "pr_confidence" else None,
            }

            with patch("main.process_invoke_request") as mock_processor:
                mock_processor.return_value = mock_result

                # Make request for each template
                request_data = {
                    "prompt": f"Process this with {template} template",
                    "template": template,
                    "format": "md",
                }

                response = client.post("/invoke", json=request_data)
                assert response.status_code == 200

                # Check that template is correctly logged
                completion_events = [
                    call
                    for call in mock_logger_client.log_business_event.call_args_list
                    if call[0][0] == "bedrock_invoke_completed"
                ]

                # Get the most recent completion event
                completion_data = completion_events[-1][0][1]
                assert completion_data["template"] == template
                assert completion_data["structured_output"] is True

    @pytest.mark.asyncio
    async def test_bedrock_invoke_different_formats_logging(self, client, mock_logger_client):
        """Test Bedrock invoke logging for different output formats."""
        formats = ["md", "txt", "json"]

        for fmt in formats:
            # Mock the processor
            mock_result = f"Response in {fmt} format"

            with patch("main.process_invoke_request") as mock_processor:
                mock_processor.return_value = mock_result

                # Make request for each format
                request_data = {"prompt": "Generate response", "template": "summary", "format": fmt}

                response = client.post("/invoke", json=request_data)
                assert response.status_code == 200

                # Check that format is correctly logged
                completion_events = [
                    call
                    for call in mock_logger_client.log_business_event.call_args_list
                    if call[0][0] == "bedrock_invoke_completed"
                ]

                # Get the most recent completion event
                completion_data = completion_events[-1][0][1]
                assert completion_data["format"] == fmt

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
        assert business_call[0][0] == "bedrock_proxy_startup"
        startup_data = business_call[0][1]
        assert "capabilities" in startup_data
        assert "features" in startup_data
        assert "stub_mode" in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert "Bedrock Proxy service started" in info_call[0][0]

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
        assert "Bedrock Proxy service shutting down" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        # Mock the processor
        mock_result = {"content": "Test response"}
        with patch("main.process_invoke_request") as mock_processor:
            mock_processor.return_value = mock_result

            # Make request - should still work without logging
            request_data = {"prompt": "Test prompt", "template": "summary"}

            response = client.post("/invoke", json=request_data)
            assert response.status_code == 200

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        # Mock the processor
        with patch("main.process_invoke_request") as mock_processor:
            mock_processor.return_value = {"content": "response"}

            request_data = {"prompt": "Test", "template": "summary"}

            client.post("/invoke", json=request_data)

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
            assert request_id.startswith("bedrock_invoke_")

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        # Mock the processor
        with patch("main.process_invoke_request") as mock_processor:
            mock_processor.return_value = {"content": "Test response"}

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            request_data = {"prompt": "Test", "template": "summary"}

            response = client.post("/invoke", json=request_data)
            assert response.status_code == 200

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            processing_time = perf_call[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_response_metrics_calculation(self, client, mock_logger_client):
        """Test that response metrics are calculated correctly."""
        # Test different response types
        test_cases = [
            ("string response", False, 15),  # Simple string, not structured, length 15
            ({"content": "structured response"}, True, 48),  # Dict with content, structured, length of str(dict)
            ([{"item": "list response"}], False, 27),  # List, not structured, length of str(list)
            ({"data": "no content key"}, False, 27),  # Dict without content, not structured
        ]

        for mock_response, expected_structured, expected_length in test_cases:
            with patch("main.process_invoke_request") as mock_processor:
                mock_processor.return_value = mock_response

                request_data = {"prompt": "test"}
                response = client.post("/invoke", json=request_data)
                assert response.status_code == 200

                # Check completion event metrics
                completion_events = [
                    call
                    for call in mock_logger_client.log_business_event.call_args_list
                    if call[0][0] == "bedrock_invoke_completed"
                ]

                completion_data = completion_events[-1][0][1]  # Most recent
                assert completion_data["structured_output"] == expected_structured
                assert completion_data["response_length"] == expected_length


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
