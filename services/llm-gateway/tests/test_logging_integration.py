"""Tests for LLM Gateway logging integration with LogCollectorClient."""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

from services.shared.utilities.logging_client import LogCollectorClient


class TestLLMGatewayLoggingIntegration:
    """Test LLM Gateway logging integration with LogCollectorClient."""

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
    async def test_llm_query_successful_logging(self, client, mock_logger_client):
        """Test successful LLM query logging."""
        # Mock Ollama response
        mock_response_data = {
            "response": "This is a test response from the LLM.",
            "done": True,
            "context": [1, 2, 3],
            "total_duration": 1234567890,
            "load_duration": 123456,
            "prompt_eval_count": 10,
            "prompt_eval_duration": 123456,
            "eval_count": 20,
            "eval_duration": 987654321,
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_http_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_http_client

            # Make request
            request_data = {
                "prompt": "Test prompt",
                "model": "llama2",
                "provider": "ollama",
                "max_tokens": 100,
                "temperature": 0.7,
            }

            response = client.post("/query", json=request_data)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] in ["llm_query_started", "llm_query_completed"]
            ]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == "llm_query_started")
            start_data = start_call[0][1]
            assert start_data["provider"] == "ollama"
            assert start_data["model"] == "llama2"
            assert start_data["prompt_length"] == len("Test prompt")
            assert "request_id" in start_data

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == "llm_query_completed")
            completion_data = completion_call[0][1]
            assert completion_data["provider"] == "ollama"
            assert completion_data["model"] == "llama2"
            assert completion_data["success"] is True
            assert "processing_time_seconds" in completion_data
            assert "tokens_used" in completion_data

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            assert perf_call[0][0] == "llm_query"
            assert "query_success" in perf_call[0][2]
            assert perf_call[0][2]["query_success"] is True

    @pytest.mark.asyncio
    async def test_llm_query_failure_logging(self, client, mock_logger_client):
        """Test failed LLM query logging."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_http_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_http_client

            # Make request
            request_data = {
                "prompt": "Test prompt",
                "model": "llama2",
                "provider": "ollama",
                "max_tokens": 100,
                "temperature": 0.7,
            }

            response = client.post("/query", json=request_data)
            assert response.status_code == 500

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "Ollama request failed with status 500" in error_call[0][0]
            assert error_call[0][1]["http_status_code"] == 500
            assert error_call[0][1]["error_type"] == "provider_error"

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "llm_query_failed"
            ]
            assert len(failure_events) >= 1

    @pytest.mark.asyncio
    async def test_llm_query_exception_logging(self, client, mock_logger_client):
        """Test LLM query exception logging."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_http_client.post.side_effect = Exception("Network timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_http_client

            # Make request
            request_data = {
                "prompt": "Test prompt",
                "model": "llama2",
                "provider": "ollama",
                "max_tokens": 100,
                "temperature": 0.7,
            }

            response = client.post("/query", json=request_data)
            assert response.status_code == 500

            # Verify exception logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2

            # Check exception error call
            error_calls = mock_logger_client.log_error.call_args_list
            exception_call = next((call for call in error_calls if "Network timeout" in call[0][0]), None)
            assert exception_call is not None
            assert exception_call[0][1]["error_type"] == "Exception"

    @pytest.mark.asyncio
    async def test_unsupported_provider_logging(self, client, mock_logger_client):
        """Test unsupported provider logging."""
        # Make request with unsupported provider
        request_data = {
            "prompt": "Test prompt",
            "model": "gpt-4",
            "provider": "openai",  # Not supported
            "max_tokens": 100,
            "temperature": 0.7,
        }

        response = client.post("/query", json=request_data)
        assert response.status_code == 400

        # Verify unsupported provider logging
        assert mock_logger_client.log_error.call_count >= 1

        error_call = mock_logger_client.log_error.call_args
        assert "Unsupported provider openai" in error_call[0][0]
        assert error_call[0][1]["error_type"] == "unsupported_provider"

    @pytest.mark.asyncio
    async def test_startup_logging(self, mock_logger_client):
        """Test service startup logging."""
        from services.llm_gateway.main import startup_event

        await startup_event()

        # Verify startup logging
        assert mock_logger_client.log_business_event.call_count >= 1
        assert mock_logger_client.log_info.call_count >= 1

        # Check startup business event
        business_call = mock_logger_client.log_business_event.call_args
        assert business_call[0][0] == "llm_gateway_startup"
        startup_data = business_call[0][1]
        assert "providers" in startup_data
        assert "capabilities" in startup_data
        assert "features" in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert "LLM Gateway service started" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_shutdown_logging(self, mock_logger_client):
        """Test service shutdown logging."""
        from services.llm_gateway.main import shutdown_event

        # Set logger client
        global logger_client
        logger_client = mock_logger_client

        await shutdown_event()

        # Verify shutdown logging
        assert mock_logger_client.log_info.call_count >= 1

        info_call = mock_logger_client.log_info.call_args
        assert "LLM Gateway service shutting down" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Test response", "done": True}
            mock_http_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_http_client

            # Make request - should still work without logging
            request_data = {
                "prompt": "Test prompt",
                "model": "llama2",
                "provider": "ollama",
                "max_tokens": 100,
                "temperature": 0.7,
            }

            response = client.post("/query", json=request_data)
            assert response.status_code == 200

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Test", "done": True}
            mock_http_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_http_client

            request_data = {"prompt": "Test", "model": "llama2", "provider": "ollama"}

            client.post("/query", json=request_data)

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
            assert request_id.startswith("llm_query_")

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        start_time = time.time()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Test", "done": True}
            mock_http_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_http_client

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            request_data = {"prompt": "Test", "model": "llama2", "provider": "ollama"}

            response = client.post("/query", json=request_data)
            assert response.status_code == 200

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            processing_time = perf_call[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
