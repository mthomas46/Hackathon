"""Tests for Secure Analyzer logging integration with LogCollectorClient."""

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


class TestSecureAnalyzerLoggingIntegration:
    """Test Secure Analyzer logging integration with LogCollectorClient."""

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
    async def test_content_detection_successful_logging(self, client, mock_logger_client):
        """Test successful content detection logging."""
        # Mock the content detector and circuit breaker
        mock_detection_result = {
            "sensitive": True,
            "matches": ["password", "secret_key"],
            "topics": ["credentials", "secrets"]
        }

        with patch('main.content_detector') as mock_detector, \
             patch('main.circuit_breaker') as mock_circuit_breaker:

            mock_detector.detect_sensitive_content.return_value = mock_detection_result
            mock_circuit_breaker.is_open.return_value = False

            # Make request
            request_data = {
                "content": "This document contains password: admin123 and secret_key: xyz789",
                "keywords": ["password", "secret"]
            }

            response = client.post("/detect", json=request_data)
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["sensitive"] is True
            assert len(response_data["matches"]) == 2
            assert len(response_data["topics"]) == 2

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [call for call in mock_logger_client.log_business_event.call_args_list
                            if call[0][0] in ['secure_content_detection_started', 'secure_content_detection_completed']]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == 'secure_content_detection_started')
            start_data = start_call[0][1]
            assert start_data['content_length'] == len(request_data['content'])
            assert start_data['has_custom_keywords'] is True
            assert start_data['has_keyword_document'] is False
            assert start_data['custom_keywords_count'] == 2
            assert 'request_id' in start_data

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == 'secure_content_detection_completed')
            completion_data = completion_call[0][1]
            assert completion_data['sensitive_content_detected'] is True
            assert completion_data['matches_found'] == 2
            assert completion_data['topics_identified'] == 2
            assert completion_data['total_patterns_checked'] == 4
            assert completion_data['success'] is True
            assert 'processing_time_seconds' in completion_data

    @pytest.mark.asyncio
    async def test_circuit_breaker_rejection_logging(self, client, mock_logger_client):
        """Test circuit breaker rejection logging."""
        with patch('main.circuit_breaker') as mock_circuit_breaker:
            mock_circuit_breaker.is_open.return_value = True

            # Make request
            request_data = {
                "content": "This content should be blocked",
                "keywords": ["test"]
            }

            response = client.post("/detect", json=request_data)
            assert response.status_code == 503

            # Verify circuit breaker rejection logging
            assert mock_logger_client.log_business_event.call_count >= 1
            assert mock_logger_client.log_error.call_count >= 1

            # Check rejection business event
            rejection_events = [call for call in mock_logger_client.log_business_event.call_args_list
                              if call[0][0] == 'secure_analyzer_circuit_breaker_rejection']
            assert len(rejection_events) >= 1

            rejection_data = rejection_events[0][0][1]
            assert rejection_data['operation'] == 'detect'
            assert rejection_data['rejection_reason'] == 'circuit_breaker_open'
            assert 'processing_time_seconds' in rejection_data

    @pytest.mark.asyncio
    async def test_content_detection_with_keyword_document_logging(self, client, mock_logger_client):
        """Test content detection with keyword document URL logging."""
        # Mock the content detector and circuit breaker
        mock_detection_result = {
            "sensitive": False,
            "matches": [],
            "topics": []
        }

        with patch('main.content_detector') as mock_detector, \
             patch('main.circuit_breaker') as mock_circuit_breaker:

            mock_detector.detect_sensitive_content.return_value = mock_detection_result
            mock_circuit_breaker.is_open.return_value = False

            # Make request with keyword document
            request_data = {
                "content": "This is safe content",
                "keyword_document": "https://example.com/keywords.txt"
            }

            response = client.post("/detect", json=request_data)
            assert response.status_code == 200

            # Check that keyword document is logged
            start_events = [call for call in mock_logger_client.log_business_event.call_args_list
                          if call[0][0] == 'secure_content_detection_started']
            assert len(start_events) >= 1

            start_data = start_events[0][0][1]
            assert start_data['has_keyword_document'] is True
            assert start_data['keyword_document_url'] == "https://example.com/keywords.txt"
            assert start_data['custom_keywords_count'] == 0

    @pytest.mark.asyncio
    async def test_content_detection_failure_logging(self, client, mock_logger_client):
        """Test content detection failure logging."""
        with patch('main.content_detector') as mock_detector, \
             patch('main.circuit_breaker') as mock_circuit_breaker:

            # Setup mocks
            mock_circuit_breaker.is_open.return_value = False
            mock_detector.detect_sensitive_content.side_effect = Exception("Pattern matching engine failure")

            # Make request
            request_data = {
                "content": "This will fail",
                "keywords": ["fail"]
            }

            response = client.post("/detect", json=request_data)
            assert response.status_code == 500

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check failure business event
            failure_events = [call for call in mock_logger_client.log_business_event.call_args_list
                            if call[0][0] == 'secure_content_detection_failed']
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data['error_type'] == 'Exception'
            assert 'Pattern matching engine failure' in failure_data['error_message']
            assert 'processing_time_seconds' in failure_data

    @pytest.mark.asyncio
    async def test_different_content_types_logging(self, client, mock_logger_client):
        """Test logging for different types of content and sensitivity levels."""
        test_cases = [
            {
                "content": "Normal safe content without any sensitive information",
                "expected_sensitive": False,
                "expected_matches": 0,
                "expected_topics": 0
            },
            {
                "content": "This contains a password: admin123 and API key: sk-123456",
                "expected_sensitive": True,
                "expected_matches": 2,
                "expected_topics": 2
            },
            {
                "content": "User email: user@example.com and SSN: 123-45-6789",
                "expected_sensitive": True,
                "expected_matches": 2,
                "expected_topics": 2
            }
        ]

        with patch('main.circuit_breaker') as mock_circuit_breaker:
            mock_circuit_breaker.is_open.return_value = False

            for i, test_case in enumerate(test_cases):
                with patch('main.content_detector') as mock_detector:
                    mock_result = {
                        "sensitive": test_case["expected_sensitive"],
                        "matches": ["match"] * test_case["expected_matches"],
                        "topics": ["topic"] * test_case["expected_topics"]
                    }
                    mock_detector.detect_sensitive_content.return_value = mock_result

                    # Make request
                    request_data = {
                        "content": test_case["content"],
                        "keywords": ["test"]
                    }

                    response = client.post("/detect", json=request_data)
                    assert response.status_code == 200

                    response_data = response.json()
                    assert response_data["sensitive"] == test_case["expected_sensitive"]

                    # Check completion event metrics
                    completion_events = [call for call in mock_logger_client.log_business_event.call_args_list
                                       if call[0][0] == 'secure_content_detection_completed']

                    # Get the most recent completion event
                    completion_data = completion_events[-1][0][1]
                    assert completion_data['sensitive_content_detected'] == test_case["expected_sensitive"]
                    assert completion_data['matches_found'] == test_case["expected_matches"]
                    assert completion_data['topics_identified'] == test_case["expected_topics"]

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
        assert business_call[0][0] == 'secure_analyzer_startup'
        startup_data = business_call[0][1]
        assert 'capabilities' in startup_data
        assert 'security_features' in startup_data
        assert 'analysis_types' in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert 'Secure Analyzer service started' in info_call[0][0]

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
        assert 'Secure Analyzer service shutting down' in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        # Mock components
        mock_result = {
            "sensitive": False,
            "matches": [],
            "topics": []
        }

        with patch('main.content_detector') as mock_detector, \
             patch('main.circuit_breaker') as mock_circuit_breaker:

            mock_detector.detect_sensitive_content.return_value = mock_result
            mock_circuit_breaker.is_open.return_value = False

            # Make request - should still work without logging
            request_data = {
                "content": "Safe content",
                "keywords": ["test"]
            }

            response = client.post("/detect", json=request_data)
            assert response.status_code == 200

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        # Mock components
        mock_result = {
            "sensitive": False,
            "matches": [],
            "topics": []
        }

        with patch('main.content_detector') as mock_detector, \
             patch('main.circuit_breaker') as mock_circuit_breaker:

            mock_detector.detect_sensitive_content.return_value = mock_result
            mock_circuit_breaker.is_open.return_value = False

            # Make request
            request_data = {"content": "Test content", "keywords": ["test"]}
            client.post("/detect", json=request_data)

            # Check that request IDs are generated and used consistently
            business_calls = mock_logger_client.log_business_event.call_args_list
            perf_calls = mock_logger_client.log_performance_metric.call_args_list

            # Extract request IDs from all calls
            request_ids = set()
            for call in business_calls + perf_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get('request_id')
                    if request_id and 'detection' in call[0][0]:
                        request_ids.add(request_id)

            # All detection calls should use the same request ID
            assert len(request_ids) == 1
            request_id = list(request_ids)[0]
            assert request_id.startswith('secure_detect_')

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        # Mock components
        mock_result = {
            "sensitive": True,
            "matches": ["password", "api_key"],
            "topics": ["credentials"]
        }

        with patch('main.content_detector') as mock_detector, \
             patch('main.circuit_breaker') as mock_circuit_breaker:

            mock_detector.detect_sensitive_content.return_value = mock_result
            mock_circuit_breaker.is_open.return_value = False

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            # Make request
            request_data = {
                "content": "Content with password: secret123 and api_key: xyz789",
                "keywords": ["password", "api_key"]
            }
            response = client.post("/detect", json=request_data)
            assert response.status_code == 200

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            detect_perf = next((call for call in perf_calls if call[0][0] == 'secure_content_detection'), None)
            assert detect_perf is not None

            processing_time = detect_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

            # Check performance metric data
            perf_data = detect_perf[0][2]
            assert perf_data['detection_success'] is True
            assert perf_data['sensitive_content_found'] is True
            assert perf_data['patterns_analyzed'] == 3  # 2 matches + 1 topic

    @pytest.mark.asyncio
    async def test_content_length_validation_logging(self, client, mock_logger_client):
        """Test that content length validation is properly logged."""
        # Test with content exceeding max size
        large_content = "x" * 1000000  # 1MB content

        with patch('main.circuit_breaker') as mock_circuit_breaker:
            mock_circuit_breaker.is_open.return_value = False

            # Make request with oversized content
            request_data = {
                "content": large_content,
                "keywords": ["test"]
            }

            # This should fail validation before reaching our logging
            response = client.post("/detect", json=request_data)
            assert response.status_code == 422  # Validation error

            # Since validation happens before our logging, we shouldn't see our custom logs
            # But the request should still be handled gracefully

    @pytest.mark.asyncio
    async def test_empty_content_logging(self, client, mock_logger_client):
        """Test logging for empty content detection attempts."""
        with patch('main.circuit_breaker') as mock_circuit_breaker:
            mock_circuit_breaker.is_open.return_value = False

            # Make request with empty content
            request_data = {
                "content": "",
                "keywords": ["test"]
            }

            response = client.post("/detect", json=request_data)
            assert response.status_code == 422  # Validation error

            # Empty content validation happens before our logging, so our logs shouldn't appear
            # This tests that validation errors are handled before our business logic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
