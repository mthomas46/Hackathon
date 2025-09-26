"""Tests for Frontend Shared Utilities"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException

from services.frontend.modules.shared_utils import (
    sanitize_input,
    validate_frontend_request,
    build_frontend_context,
    handle_frontend_error,
    get_frontend_clients,
    get_orchestrator_url,
    fetch_service_data,
    create_html_response,
)


class TestFrontendSharedUtils:
    """Test cases for frontend shared utilities."""

    def test_sanitize_input_basic(self):
        """Test basic input sanitization."""
        result = sanitize_input("normal input")
        assert result == "normal input"

    def test_sanitize_input_with_html(self):
        """Test input sanitization with HTML tags."""
        result = sanitize_input("<script>alert('xss')</script>test")
        assert "<script>" not in result
        assert "test" in result

    def test_sanitize_input_empty(self):
        """Test sanitization of empty input."""
        result = sanitize_input("")
        assert result == ""

    def test_sanitize_input_none(self):
        """Test sanitization of None input."""
        result = sanitize_input(None)
        assert result == ""

    def test_validate_frontend_request_valid(self):
        """Test validation of valid request."""
        is_valid, error = validate_frontend_request({"query": "test"})
        assert is_valid == True
        assert error is None

    def test_validate_frontend_request_invalid(self):
        """Test validation of invalid request."""
        is_valid, error = validate_frontend_request({})
        assert is_valid == False
        assert "required" in error.lower()

    def test_validate_frontend_request_empty_query(self):
        """Test validation with empty query."""
        is_valid, error = validate_frontend_request({"query": ""})
        assert is_valid == False
        assert "empty" in error.lower()

    def test_build_frontend_context(self):
        """Test building frontend context."""
        context = build_frontend_context("test_operation", user="test_user")

        assert context["operation"] == "test_operation"
        assert context["service"] == "frontend"
        assert context["user"] == "test_user"

    def test_build_frontend_context_minimal(self):
        """Test building minimal frontend context."""
        context = build_frontend_context("test_operation")

        assert context["operation"] == "test_operation"
        assert context["service"] == "frontend"
        assert len(context) == 2

    def test_handle_frontend_error(self):
        """Test frontend error handling."""
        with patch('services.frontend.modules.shared_utils.create_html_response') as mock_response:
            mock_response.return_value = Mock()

            error = Exception("Test error")
            result = handle_frontend_error("test operation", error, user="test_user")

            mock_response.assert_called_once()
            # Check that error details are included in the response
            call_args = mock_response.call_args
            assert "Test error" in str(call_args)

    def test_create_html_response(self):
        """Test HTML response creation."""
        html_content = "<html><body>Test</body></html>"
        result = create_html_response(html_content, "Test Title")

        assert result.status_code == 200
        assert "text/html" in result.headers.get("content-type", "")
        assert html_content in result.body.decode()

    def test_get_orchestrator_url(self):
        """Test getting orchestrator URL."""
        with patch.dict('os.environ', {'ORCHESTRATOR_SERVICE_URL': 'http://test-orchestrator:8080'}):
            url = get_orchestrator_url()
            assert url == 'http://test-orchestrator:8080'

    def test_get_orchestrator_url_default(self):
        """Test getting default orchestrator URL."""
        with patch.dict('os.environ', {}, clear=True):
            url = get_orchestrator_url()
            assert url == 'http://orchestrator:8000'

    @pytest.mark.asyncio
    async def test_fetch_service_data_success(self):
        """Test successful service data fetching."""
        mock_clients = AsyncMock()
        mock_clients.get_json.return_value = {"test": "data"}

        result = await fetch_service_data(mock_clients, "http://test-url", "test_endpoint")

        assert result == {"test": "data"}
        mock_clients.get_json.assert_called_once_with("http://test-url/test_endpoint")

    @pytest.mark.asyncio
    async def test_fetch_service_data_with_params(self):
        """Test service data fetching with parameters."""
        mock_clients = AsyncMock()
        mock_clients.get_json.return_value = {"results": []}

        params = {"query": "test", "limit": 10}
        result = await fetch_service_data(
            mock_clients, "http://test-url", "search", params=params
        )

        assert result == {"results": []}
        mock_clients.get_json.assert_called_once_with(
            "http://test-url/search", params={"query": "test", "limit": 10}
        )

    @pytest.mark.asyncio
    async def test_fetch_service_data_error(self):
        """Test service data fetching with error."""
        mock_clients = AsyncMock()
        mock_clients.get_json.side_effect = Exception("Connection failed")

        result = await fetch_service_data(mock_clients, "http://test-url", "test_endpoint")

        assert result == {"error": "Connection failed"}

    def test_get_frontend_clients(self):
        """Test getting frontend clients."""
        with patch('services.frontend.modules.shared_utils.ServiceClients') as mock_clients_class:
            mock_instance = Mock()
            mock_clients_class.return_value = mock_instance

            result = get_frontend_clients()

            assert result == mock_instance
            mock_clients_class.assert_called_once()


class TestInputValidation:
    """Test input validation functions."""

    @pytest.mark.parametrize("input_value,expected_valid", [
        ({"query": "test search"}, True),
        ({"query": "", "other": "data"}, False),
        ({}, False),
        ({"query": "test", "page": 1}, True),
        ({"query": "test", "page": "invalid"}, True),  # Type validation not implemented yet
    ])
    def test_validate_frontend_request_parametrized(self, input_value, expected_valid):
        """Test frontend request validation with various inputs."""
        is_valid, error = validate_frontend_request(input_value)

        assert is_valid == expected_valid
        if not expected_valid:
            assert error is not None
            assert len(error) > 0
        else:
            assert error is None


class TestErrorHandling:
    """Test error handling functions."""

    def test_handle_frontend_error_with_context(self):
        """Test error handling with additional context."""
        with patch('services.frontend.modules.shared_utils.create_html_response') as mock_response:
            mock_response.return_value = Mock()

            error = ValueError("Invalid value")
            context = {"user": "test_user", "operation": "test_op"}

            result = handle_frontend_error("test operation", error, **context)

            mock_response.assert_called_once()
            call_args = mock_response.call_args
            # Verify error details are included
            response_content = call_args[0][0]  # First positional argument
            assert "Invalid value" in response_content
            assert "test operation" in response_content

    def test_handle_frontend_error_http_exception(self):
        """Test error handling with HTTPException."""
        with patch('services.frontend.modules.shared_utils.create_html_response') as mock_response:
            mock_response.return_value = Mock()

            error = HTTPException(status_code=404, detail="Not found")

            result = handle_frontend_error("test operation", error)

            mock_response.assert_called_once()
            call_args = mock_response.call_args
            response_content = call_args[0][0]
            assert "404" in response_content
            assert "Not found" in response_content
