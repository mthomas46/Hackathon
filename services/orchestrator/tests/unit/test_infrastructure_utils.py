"""Tests for infrastructure utilities"""

import pytest
from unittest.mock import Mock, patch

from services.orchestrator.infrastructure.utils import (
    get_service_url,
    prepare_correlation_headers,
    build_service_request_context,
)


class TestInfrastructureUtils:
    """Test infrastructure utility functions."""

    def test_get_service_url_with_env_var(self):
        """Test getting service URL with environment variable set."""
        service_name = "doc_store"
        default_url = "http://localhost:8080"
        env_url = "http://docstore.production.com:9000"

        with patch.dict('os.environ', {'DOC_STORE_SERVICE_URL': env_url}):
            url = get_service_url(service_name, default_url)
            assert url == env_url

    def test_get_service_url_without_env_var(self):
        """Test getting service URL without environment variable."""
        service_name = "unknown_service"
        default_url = "http://localhost:8080"

        # Ensure no env var is set
        with patch.dict('os.environ', {}, clear=True):
            url = get_service_url(service_name, default_url)
            assert url == default_url

    def test_prepare_correlation_headers_with_request(self):
        """Test preparing correlation headers from request."""
        request = Mock()
        request.headers = {"X-Correlation-ID": "test-correlation-123"}

        headers = prepare_correlation_headers(request)

        assert headers == {"X-Correlation-ID": "test-correlation-123"}

    def test_prepare_correlation_headers_without_correlation_id(self):
        """Test preparing correlation headers when no correlation ID."""
        request = Mock()
        request.headers = {"Content-Type": "application/json"}

        headers = prepare_correlation_headers(request)

        assert headers == {}

    def test_prepare_correlation_headers_no_headers_attr(self):
        """Test preparing correlation headers when request has no headers."""
        request = Mock()
        del request.headers  # Remove headers attribute

        headers = prepare_correlation_headers(request)

        assert headers == {}

    def test_build_service_request_context(self):
        """Test building service request context."""
        context = build_service_request_context(
            operation="test_operation",
            user_id="user123",
            session_id="session456"
        )

        assert context["operation"] == "test_operation"
        assert context["service"] == "orchestrator"
        assert context["user_id"] == "user123"
        assert context["session_id"] == "session456"

    def test_build_service_request_context_minimal(self):
        """Test building minimal service request context."""
        context = build_service_request_context("test_operation")

        assert context["operation"] == "test_operation"
        assert context["service"] == "orchestrator"
        assert len(context) == 2
