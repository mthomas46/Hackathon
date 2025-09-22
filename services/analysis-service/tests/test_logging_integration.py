"""Tests for Analysis Service logging integration with LogCollectorClient."""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.analysis_handlers import AnalysisHandlers, logger_client

from services.shared.utilities.logging_client import LogCollectorClient


class TestAnalysisServiceLoggingIntegration:
    """Test Analysis Service logging integration with LogCollectorClient."""

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
    async def test_document_analysis_successful_logging(self, mock_logger_client):
        """Test successful document analysis logging."""
        handlers = AnalysisHandlers()

        # Mock the service and registry
        with patch("services.analysis_service.modules.analysis_handlers.handler_registry") as mock_registry:
            mock_handler = AsyncMock()
            mock_result = {
                "findings": [
                    {"severity": "high", "type": "consistency_issue"},
                    {"severity": "medium", "type": "quality_issue"},
                ],
                "analyzed_documents": ["doc1", "doc2", "doc3"],
            }
            mock_handler.handle.return_value = mock_result
            mock_registry.get_handler.return_value = mock_handler

            # Create test request
            request = MagicMock()
            request.targets = ["doc1", "doc2", "doc3"]
            request.detectors = ["consistency", "quality"]
            request.correlation_id = "test-correlation-123"

            # Call the handler
            result = await handlers.handle_analyze_documents(request)

            # Verify the result is returned
            assert result == mock_result

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] in ["document_analysis_started", "document_analysis_completed"]
            ]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == "document_analysis_started")
            start_data = start_call[0][1]
            assert start_data["analysis_type"] == "document_consistency"
            assert start_data["target_count"] == 3
            assert start_data["detectors"] == ["consistency", "quality"]
            assert start_data["correlation_id"] == "test-correlation-123"
            assert "request_id" in start_data

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == "document_analysis_completed")
            completion_data = completion_call[0][1]
            assert completion_data["analysis_type"] == "document_consistency"
            assert completion_data["success"] is True
            assert completion_data["findings_count"] == 2
            assert completion_data["documents_analyzed"] == 3
            assert "processing_time_seconds" in completion_data

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            assert perf_call[0][0] == "document_analysis"
            assert "analysis_success" in perf_call[0][2]
            assert perf_call[0][2]["analysis_success"] is True

    @pytest.mark.asyncio
    async def test_risk_assessment_successful_logging(self, mock_logger_client):
        """Test successful risk assessment logging."""
        handlers = AnalysisHandlers()

        # Mock the service and registry
        with patch("services.analysis_service.modules.analysis_handlers.handler_registry") as mock_registry:
            mock_handler = AsyncMock()
            mock_result = {
                "overall_risk_score": 7.5,
                "findings": [
                    {"severity": "critical", "type": "security_risk"},
                    {"severity": "high", "type": "performance_risk"},
                    {"severity": "medium", "type": "maintenance_risk"},
                ],
            }
            mock_handler.handle.return_value = mock_result
            mock_registry.get_handler.return_value = mock_handler

            # Create test request
            request = MagicMock()
            request.targets = ["component1", "component2"]
            request.assessment_type = "comprehensive"

            # Call the handler
            result = await handlers.handle_risk_assessment(request)

            # Verify the result is returned
            assert result == mock_result

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] in ["risk_assessment_started", "risk_assessment_completed"]
            ]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == "risk_assessment_started")
            start_data = start_call[0][1]
            assert start_data["analysis_type"] == "risk_assessment"
            assert start_data["target_count"] == 2
            assert start_data["assessment_type"] == "comprehensive"

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == "risk_assessment_completed")
            completion_data = completion_call[0][1]
            assert completion_data["analysis_type"] == "risk_assessment"
            assert completion_data["success"] is True
            assert completion_data["overall_risk_score"] == 7.5
            assert completion_data["critical_issues_count"] == 1  # One critical finding
            assert completion_data["findings_count"] == 3

    @pytest.mark.asyncio
    async def test_document_analysis_handler_unavailable_logging(self, mock_logger_client):
        """Test logging when document analysis handler is unavailable."""
        handlers = AnalysisHandlers()

        # Mock the registry to return None (handler not available)
        with patch("services.analysis_service.modules.analysis_handlers.handler_registry") as mock_registry:
            mock_registry.get_handler.return_value = None

            # Create test request
            request = MagicMock()
            request.targets = ["doc1"]

            # Call the handler
            result = await handlers.handle_analyze_documents(request)

            # Verify error result
            assert "error" in result
            assert result["error"] == "Handler not available"

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "No semantic similarity handler available" in error_call[0][0]
            assert error_call[0][1]["error_type"] == "handler_unavailable"

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "document_analysis_failed"
            ]
            assert len(failure_events) >= 1

    @pytest.mark.asyncio
    async def test_risk_assessment_exception_logging(self, mock_logger_client):
        """Test risk assessment exception logging."""
        handlers = AnalysisHandlers()

        # Mock the registry and handler to raise an exception
        with patch("services.analysis_service.modules.analysis_handlers.handler_registry") as mock_registry:
            mock_handler = AsyncMock()
            mock_handler.handle.side_effect = Exception("Analysis engine failure")
            mock_registry.get_handler.return_value = mock_handler

            # Create test request
            request = MagicMock()
            request.targets = ["component1"]

            # Call the handler
            result = await handlers.handle_risk_assessment(request)

            # Verify error result
            assert "error" in result
            assert "Analysis engine failure" in result["error"]

            # Verify exception logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check exception error call
            error_calls = mock_logger_client.log_error.call_args_list
            exception_call = next((call for call in error_calls if "Analysis engine failure" in call[0][0]), None)
            assert exception_call is not None
            assert exception_call[0][1]["error_type"] == "Exception"

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "risk_assessment_failed"
            ]
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data["error_type"] == "Exception"
            assert failure_data["error_message"] == "Analysis engine failure"

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, mock_logger_client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        handlers = AnalysisHandlers()

        # Mock the service and registry
        with patch("services.analysis_service.modules.analysis_handlers.handler_registry") as mock_registry:
            mock_handler = AsyncMock()
            mock_result = {"findings": [], "analyzed_documents": ["doc1"]}
            mock_handler.handle.return_value = mock_result
            mock_registry.get_handler.return_value = mock_handler

            # Create test request
            request = MagicMock()
            request.targets = ["doc1"]

            # Call the handler - should still work without logging
            result = await handlers.handle_analyze_documents(request)
            assert result == mock_result

    def test_request_id_generation(self, mock_logger_client):
        """Test that request IDs are properly generated."""
        handlers = AnalysisHandlers()

        # Mock the service and registry
        with patch("services.analysis_service.modules.analysis_handlers.handler_registry") as mock_registry:
            mock_handler = AsyncMock()
            mock_result = {"findings": [], "analyzed_documents": ["doc1"]}
            mock_handler.handle.return_value = mock_result
            mock_registry.get_handler.return_value = mock_handler

            # Create test request
            request = MagicMock()
            request.targets = ["doc1"]

            handlers.handle_analyze_documents(request)

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
            assert request_id.startswith("analysis_")

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        handlers = AnalysisHandlers()

        # Mock the service and registry
        with patch("services.analysis_service.modules.analysis_handlers.handler_registry") as mock_registry:
            mock_handler = AsyncMock()
            mock_result = {"findings": [{"severity": "high"}], "analyzed_documents": ["doc1"]}
            mock_handler.handle.return_value = mock_result
            mock_registry.get_handler.return_value = mock_handler

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            # Create test request
            request = MagicMock()
            request.targets = ["doc1"]

            await handlers.handle_analyze_documents(request)

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            processing_time = perf_call[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_business_event_risk_score_calculation(self, mock_logger_client):
        """Test that risk score and critical issue counting is accurate."""
        handlers = AnalysisHandlers()

        # Mock the service and registry
        with patch("services.analysis_service.modules.analysis_handlers.handler_registry") as mock_registry:
            mock_handler = AsyncMock()
            mock_result = {
                "overall_risk_score": 8.2,
                "findings": [
                    {"severity": "critical", "type": "security_vulnerability"},
                    {"severity": "critical", "type": "data_breach_risk"},
                    {"severity": "high", "type": "performance_issue"},
                    {"severity": "medium", "type": "code_smell"},
                    {"severity": "low", "type": "documentation_issue"},
                ],
            }
            mock_handler.handle.return_value = mock_result
            mock_registry.get_handler.return_value = mock_handler

            # Create test request
            request = MagicMock()
            request.targets = ["component1"]

            await handlers.handle_risk_assessment(request)

            # Check completion business event
            completion_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "risk_assessment_completed"
            ]
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            assert completion_data["overall_risk_score"] == 8.2
            assert completion_data["critical_issues_count"] == 2  # Two critical findings
            assert completion_data["findings_count"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
