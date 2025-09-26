"""Tests for shared utilities in the orchestrator service"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio
from datetime import datetime, timezone
import json

from services.orchestrator.modules.shared_utils import (
    validate_service_request,
    create_workflow_context,
    safe_service_call,
    handle_service_error,
    format_service_response,
    extract_service_metadata,
    validate_workflow_parameters,
    create_execution_context,
    log_service_interaction,
    retry_with_backoff
)


class TestSharedUtilsValidation:
    """Test validation utilities."""

    def test_validate_service_request_valid(self):
        """Test validating a valid service request."""
        request = {
            "service_id": "test-service",
            "action": "execute",
            "parameters": {"key": "value"}
        }

        result = validate_service_request(request)
        assert result["service_id"] == "test-service"
        assert result["action"] == "execute"
        assert result["parameters"] == {"key": "value"}

    def test_validate_service_request_missing_fields(self):
        """Test validating request with missing required fields."""
        with pytest.raises(ValueError, match="Missing required field"):
            validate_service_request({})

    def test_validate_service_request_invalid_service_id(self):
        """Test validating request with invalid service ID."""
        request = {
            "service_id": "",
            "action": "execute"
        }

        with pytest.raises(ValueError, match="Invalid service_id"):
            validate_service_request(request)

    def test_validate_workflow_parameters_valid(self):
        """Test validating valid workflow parameters."""
        params = {
            "workflow_id": "test-workflow",
            "input_data": {"key": "value"}
        }
        required = ["workflow_id"]

        result = validate_workflow_parameters(params, required)
        assert result == params

    def test_validate_workflow_parameters_missing_required(self):
        """Test validating parameters with missing required field."""
        params = {"input_data": {"key": "value"}}
        required = ["workflow_id"]

        with pytest.raises(ValueError, match="Missing required parameter"):
            validate_workflow_parameters(params, required)


class TestSharedUtilsContextCreation:
    """Test context creation utilities."""

    def test_create_workflow_context(self):
        """Test creating workflow context."""
        workflow_id = "test-workflow"
        parameters = {"param1": "value1"}

        context = create_workflow_context(workflow_id, parameters)

        assert context["workflow_id"] == workflow_id
        assert context["parameters"] == parameters
        assert "timestamp" in context
        assert "correlation_id" in context

    def test_create_execution_context(self):
        """Test creating execution context."""
        execution_id = "test-execution"
        workflow_id = "test-workflow"

        context = create_execution_context(execution_id, workflow_id)

        assert context["execution_id"] == execution_id
        assert context["workflow_id"] == workflow_id
        assert "start_time" in context
        assert "status" in context
        assert context["status"] == "pending"


class TestSharedUtilsServiceInteraction:
    """Test service interaction utilities."""

    @patch('services.orchestrator.modules.shared_utils.get_service_client')
    @pytest.mark.asyncio
    async def test_safe_service_call_success(self, mock_get_client):
        """Test successful safe service call."""
        mock_client = Mock()
        mock_client.call.return_value = {"result": "success"}
        mock_get_client.return_value = mock_client

        result = await safe_service_call("test-service", "test_action", {"param": "value"})

        assert result["result"] == "success"
        mock_client.call.assert_called_once_with("test_action", {"param": "value"})

    @patch('services.orchestrator.modules.shared_utils.get_service_client')
    @pytest.mark.asyncio
    async def test_safe_service_call_failure(self, mock_get_client):
        """Test failed safe service call."""
        mock_client = Mock()
        mock_client.call.side_effect = Exception("Service error")
        mock_get_client.return_value = mock_client

        result = await safe_service_call("test-service", "test_action", {"param": "value"})

        assert result["error"] == "Service error"
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self):
        """Test successful retry with backoff."""
        call_count = 0

        async def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary error")
            return "success"

        result = await retry_with_backoff(mock_operation, max_attempts=3, base_delay=0.01)

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_with_backoff_exhaustion(self):
        """Test retry exhaustion."""
        async def mock_operation():
            raise Exception("Persistent error")

        with pytest.raises(Exception, match="Persistent error"):
            await retry_with_backoff(mock_operation, max_attempts=2, base_delay=0.01)


class TestSharedUtilsResponseFormatting:
    """Test response formatting utilities."""

    def test_format_service_response_success(self):
        """Test formatting successful service response."""
        data = {"result": "success"}
        response = format_service_response(data, status="success")

        assert response["status"] == "success"
        assert response["data"] == data
        assert "timestamp" in response

    def test_format_service_response_error(self):
        """Test formatting error service response."""
        error = "Something went wrong"
        response = format_service_response(None, status="error", error=error)

        assert response["status"] == "error"
        assert response["error"] == error
        assert "timestamp" in response

    def test_handle_service_error(self):
        """Test handling service error."""
        try:
            raise ValueError("Test error")
        except Exception as e:
            error_response = handle_service_error(e, "test_service", "test_action")

        assert error_response["status"] == "error"
        assert "Test error" in error_response["error"]
        assert error_response["service"] == "test_service"
        assert error_response["action"] == "test_action"


class TestSharedUtilsMetadata:
    """Test metadata extraction utilities."""

    def test_extract_service_metadata_from_response(self):
        """Test extracting metadata from service response."""
        response = {
            "status": "success",
            "data": {"result": "ok"},
            "metadata": {
                "version": "1.0",
                "timestamp": "2024-01-01T10:00:00Z"
            }
        }

        metadata = extract_service_metadata(response)

        assert metadata["version"] == "1.0"
        assert metadata["timestamp"] == "2024-01-01T10:00:00Z"
        assert metadata["response_status"] == "success"

    def test_extract_service_metadata_empty(self):
        """Test extracting metadata from response without metadata."""
        response = {"status": "success", "data": {"result": "ok"}}

        metadata = extract_service_metadata(response)

        assert metadata["response_status"] == "success"
        assert "version" not in metadata


class TestSharedUtilsLogging:
    """Test logging utilities."""

    @patch('services.orchestrator.modules.shared_utils.fire_and_forget')
    def test_log_service_interaction(self, mock_fire_and_forget):
        """Test logging service interaction."""
        interaction = {
            "service": "test-service",
            "action": "test_action",
            "request": {"param": "value"},
            "response": {"result": "ok"},
            "duration": 0.5
        }

        log_service_interaction(interaction)

        # Verify that fire_and_forget was called (logging is async)
        mock_fire_and_forget.assert_called_once()
        logged_data = mock_fire_and_forget.call_args[0][0]

        assert logged_data["service"] == "test-service"
        assert logged_data["action"] == "test_action"
        assert logged_data["level"] == "INFO"
        assert "interaction" in logged_data
