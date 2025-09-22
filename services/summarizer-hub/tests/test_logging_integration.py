"""Tests for Summarizer Hub logging integration with LogCollectorClient."""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app, logger_client
from services.shared.utilities.logging_client import LogCollectorClient


class TestSummarizerHubLoggingIntegration:
    """Test Summarizer Hub logging integration with LogCollectorClient."""

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
    async def test_document_summarization_successful_logging(self, client, mock_logger_client):
        """Test successful document summarization logging."""
        # Mock the summarizer
        mock_summary = "This is a comprehensive summary of the document content."

        with patch('main.summarizer') as mock_summarizer:
            mock_summarizer.summarize_with_llm.return_value = mock_summary

            # Make request
            request_data = {
                "content": "This is a very long document with lots of content that needs to be summarized into a shorter form. It contains multiple paragraphs and various topics that should be condensed.",
                "format": "markdown",
                "max_length": 500,
                "style": "professional"
            }

            response = client.post("/summarize", json=request_data)
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"]["summary"] == mock_summary

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [call for call in mock_logger_client.log_business_event.call_args_list
                            if call[0][0] in ['document_summarization_started', 'document_summarization_completed']]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == 'document_summarization_started')
            start_data = start_call[0][1]
            assert start_data['content_length'] == len(request_data['content'])
            assert start_data['max_length'] == 500
            assert start_data['format'] == 'markdown'
            assert start_data['style'] == 'professional'
            assert start_data['operation_type'] == 'single_document_summarization'
            assert 'request_id' in start_data

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == 'document_summarization_completed')
            completion_data = completion_call[0][1]
            assert completion_data['original_word_count'] == len(request_data['content'].split())
            assert completion_data['summary_word_count'] == len(mock_summary.split())
            assert 'compression_ratio' in completion_data
            assert completion_data['format'] == 'markdown'
            assert completion_data['success'] is True
            assert 'processing_time_seconds' in completion_data

    @pytest.mark.asyncio
    async def test_document_summarization_failure_logging(self, client, mock_logger_client):
        """Test document summarization failure logging."""
        # Mock the summarizer to raise an exception
        with patch('main.summarizer') as mock_summarizer:
            mock_summarizer.summarize_with_llm.side_effect = Exception("LLM gateway timeout")

            # Make request
            request_data = {
                "content": "Short content that should fail",
                "format": "markdown",
                "max_length": 200
            }

            response = client.post("/summarize", json=request_data)
            assert response.status_code == 200  # Summarizer returns error in response

            response_data = response.json()
            assert response_data["success"] is False
            assert "LLM gateway timeout" in response_data["error"]

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check error call
            error_calls = mock_logger_client.log_error.call_args_list
            summarization_error = next((call for call in error_calls if 'Document summarization failed' in call[0][0]), None)
            assert summarization_error is not None
            assert summarization_error[0][1]['content_length'] == len(request_data['content'])
            assert summarization_error[0][1]['error_type'] == 'Exception'
            assert summarization_error[0][1]['llm_gateway_failure'] is True

            # Check failure business event
            failure_events = [call for call in mock_logger_client.log_business_event.call_args_list
                            if call[0][0] == 'document_summarization_failed']
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data['error_type'] == 'Exception'
            assert 'LLM gateway timeout' in failure_data['error_message']
            assert 'processing_time_seconds' in failure_data

    @pytest.mark.asyncio
    async def test_different_summarization_formats_logging(self, client, mock_logger_client):
        """Test summarization logging for different output formats."""
        formats = ["markdown", "plain", "structured"]

        for fmt in formats:
            # Mock the summarizer
            mock_summary = f"Summary in {fmt} format"

            with patch('main.summarizer') as mock_summarizer:
                mock_summarizer.summarize_with_llm.return_value = mock_summary

                # Make request
                request_data = {
                    "content": "Content to summarize",
                    "format": fmt,
                    "max_length": 300
                }

                response = client.post("/summarize", json=request_data)
                assert response.status_code == 200

                # Check completion event has correct format
                completion_events = [call for call in mock_logger_client.log_business_event.call_args_list
                                   if call[0][0] == 'document_summarization_completed']

                # Get the most recent completion event
                completion_data = completion_events[-1][0][1]
                assert completion_data['format'] == fmt

    @pytest.mark.asyncio
    async def test_different_summarization_styles_logging(self, client, mock_logger_client):
        """Test summarization logging for different writing styles."""
        styles = ["professional", "casual", "technical", "executive"]

        for style in styles:
            # Mock the summarizer
            mock_summary = f"Summary in {style} style"

            with patch('main.summarizer') as mock_summarizer:
                mock_summarizer.summarize_with_llm.return_value = mock_summary

                # Make request
                request_data = {
                    "content": "Content to summarize",
                    "format": "markdown",
                    "max_length": 400,
                    "style": style
                }

                response = client.post("/summarize", json=request_data)
                assert response.status_code == 200

                # Check completion event has correct style
                completion_events = [call for call in mock_logger_client.log_business_event.call_args_list
                                   if call[0][0] == 'document_summarization_completed']

                # Get the most recent completion event
                completion_data = completion_events[-1][0][1]
                assert completion_data['style'] == style

    @pytest.mark.asyncio
    async def test_compression_metrics_calculation_logging(self, client, mock_logger_client):
        """Test that compression metrics are calculated correctly."""
        # Test case with known compression ratio
        original_content = "This is a long document with many words that should be compressed significantly when summarized."
        expected_summary = "Document compressed."

        original_word_count = len(original_content.split())  # 16 words
        summary_word_count = len(expected_summary.split())   # 2 words

        with patch('main.summarizer') as mock_summarizer:
            mock_summarizer.summarize_with_llm.return_value = expected_summary

            # Make request
            request_data = {
                "content": original_content,
                "format": "markdown",
                "max_length": 100
            }

            response = client.post("/summarize", json=request_data)
            assert response.status_code == 200

            # Check completion event has correct compression metrics
            completion_events = [call for call in mock_logger_client.log_business_event.call_args_list
                               if call[0][0] == 'document_summarization_completed']
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            assert completion_data['original_word_count'] == original_word_count
            assert completion_data['summary_word_count'] == summary_word_count
            assert completion_data['compression_efficiency'] == summary_word_count / original_word_count
            assert 'compression_ratio' in completion_data

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
        assert business_call[0][0] == 'summarizer_hub_startup'
        startup_data = business_call[0][1]
        assert 'capabilities' in startup_data
        assert 'ai_features' in startup_data
        assert 'analysis_types' in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert 'Summarizer Hub service started' in info_call[0][0]

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
        assert 'Summarizer Hub service shutting down' in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        # Mock the summarizer
        mock_summary = "Mock summary response"

        with patch('main.summarizer') as mock_summarizer:
            mock_summarizer.summarize_with_llm.return_value = mock_summary

            # Make request - should still work without logging
            request_data = {
                "content": "Content to summarize",
                "format": "markdown",
                "max_length": 300
            }

            response = client.post("/summarize", json=request_data)
            assert response.status_code == 200

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        # Mock the summarizer
        mock_summary = "Test summary"

        with patch('main.summarizer') as mock_summarizer:
            mock_summarizer.summarize_with_llm.return_value = mock_summary

            # Make request
            request_data = {"content": "Test content", "format": "markdown", "max_length": 200}
            client.post("/summarize", json=request_data)

            # Check that request IDs are generated and used consistently
            business_calls = mock_logger_client.log_business_event.call_args_list
            perf_calls = mock_logger_client.log_performance_metric.call_args_list

            # Extract request IDs from all calls
            request_ids = set()
            for call in business_calls + perf_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get('request_id')
                    if request_id and 'summarization' in call[0][0]:
                        request_ids.add(request_id)

            # All summarization calls should use the same request ID
            assert len(request_ids) == 1
            request_id = list(request_ids)[0]
            assert request_id.startswith('summarizer_summarize_')

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        # Mock the summarizer
        mock_summary = "Quick summary response"

        with patch('main.summarizer') as mock_summarizer:
            mock_summarizer.summarize_with_llm.return_value = mock_summary

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            # Make request
            request_data = {
                "content": "Content to be summarized",
                "format": "markdown",
                "max_length": 250
            }
            response = client.post("/summarize", json=request_data)
            assert response.status_code == 200

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            summarize_perf = next((call for call in perf_calls if call[0][0] == 'document_summarization'), None)
            assert summarize_perf is not None

            processing_time = summarize_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

            # Check performance metric data
            perf_data = summarize_perf[0][2]
            assert perf_data['summarization_success'] is True
            assert perf_data['content_length'] == len(request_data['content'])
            assert 'compression_ratio' in perf_data
            assert perf_data['llm_processing_time'] == processing_time

    @pytest.mark.asyncio
    async def test_empty_content_summarization_logging(self, client, mock_logger_client):
        """Test summarization logging for empty content edge case."""
        # Mock the summarizer to handle empty content
        mock_summary = ""

        with patch('main.summarizer') as mock_summarizer:
            mock_summarizer.summarize_with_llm.return_value = mock_summary

            # Make request with empty content
            request_data = {
                "content": "",
                "format": "markdown",
                "max_length": 100
            }

            response = client.post("/summarize", json=request_data)
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True

            # Check completion event handles empty content gracefully
            completion_events = [call for call in mock_logger_client.log_business_event.call_args_list
                               if call[0][0] == 'document_summarization_completed']
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            assert completion_data['original_word_count'] == 0
            assert completion_data['summary_word_count'] == 0
            assert completion_data['compression_ratio'] == 0  # Division by zero handled

    @pytest.mark.asyncio
    async def test_max_length_constraint_logging(self, client, mock_logger_client):
        """Test summarization logging with different max length constraints."""
        max_lengths = [50, 200, 1000]

        for max_len in max_lengths:
            # Mock the summarizer to return summary of appropriate length
            mock_summary = "x" * min(max_len, 100)  # Mock summary of reasonable length

            with patch('main.summarizer') as mock_summarizer:
                mock_summarizer.summarize_with_llm.return_value = mock_summary

                # Make request
                request_data = {
                    "content": "Long content that needs to be summarized to different lengths",
                    "format": "markdown",
                    "max_length": max_len
                }

                response = client.post("/summarize", json=request_data)
                assert response.status_code == 200

                # Check start event has correct max_length
                start_events = [call for call in mock_logger_client.log_business_event.call_args_list
                              if call[0][0] == 'document_summarization_started']

                # Get the most recent start event
                start_data = start_events[-1][0][1]
                assert start_data['max_length'] == max_len


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
