#!/usr/bin/env python3
"""
Tests for Core Constants Module

Tests the shared constants and configuration values.
"""

import pytest
from services.shared.core.constants_new import (
    HTTPStatus,
    EnvVars,
    Patterns,
    ServiceNames,
    ErrorCodes
)


class TestHTTPStatus:
    """Test HTTP status code constants."""

    def test_http_status_codes(self):
        """Test that HTTP status codes are correctly defined."""
        assert HTTPStatus.OK == 200
        assert HTTPStatus.CREATED == 201
        assert HTTPStatus.BAD_REQUEST == 400
        assert HTTPStatus.NOT_FOUND == 404
        assert HTTPStatus.INTERNAL_SERVER_ERROR == 500

    def test_all_status_codes_are_integers(self):
        """Test that all HTTP status codes are integers."""
        status_attrs = [attr for attr in dir(HTTPStatus) if not attr.startswith('_')]
        for attr in status_attrs:
            value = getattr(HTTPStatus, attr)
            assert isinstance(value, int), f"HTTPStatus.{attr} should be an integer"
            assert 100 <= value <= 599, f"HTTPStatus.{attr} should be a valid HTTP status code"


class TestEnvVars:
    """Test environment variable constants."""

    def test_basic_env_vars(self):
        """Test basic environment variable names."""
        assert EnvVars.ENVIRONMENT == "ENVIRONMENT"
        assert EnvVars.DEBUG == "DEBUG"

    def test_service_env_vars(self):
        """Test service-specific environment variable names."""
        assert EnvVars.DOC_STORE_URL == "DOC_STORE_URL"
        assert EnvVars.ANALYSIS_SERVICE_URL == "ANALYSIS_SERVICE_URL"
        assert EnvVars.PROMPT_STORE_URL == "PROMPT_STORE_URL"


class TestPatterns:
    """Test regex pattern constants."""

    def test_variable_pattern(self):
        """Test variable extraction pattern."""
        import re
        pattern = re.compile(Patterns.VARIABLE)
        assert pattern.search("{variable}")
        assert pattern.search("{test_var}")
        assert not pattern.search("no variables here")

    def test_email_pattern(self):
        """Test email validation pattern."""
        import re
        pattern = re.compile(Patterns.EMAIL)
        assert pattern.match("test@example.com")
        assert pattern.match("user.name+tag@domain.co.uk")
        assert not pattern.match("invalid-email")

    def test_url_pattern(self):
        """Test URL validation pattern."""
        import re
        pattern = re.compile(Patterns.URL)
        assert pattern.match("https://example.com")
        assert pattern.match("http://localhost:8000")
        assert not pattern.match("not a url")


class TestServiceNames:
    """Test service name constants."""

    def test_service_names_defined(self):
        """Test that all expected service names are defined."""
        assert ServiceNames.ORCHESTRATOR == "orchestrator"
        assert ServiceNames.ANALYSIS_SERVICE == "analysis-service"
        assert ServiceNames.DOC_STORE == "doc_store"
        assert ServiceNames.PROMPT_STORE == "prompt-store"
        assert ServiceNames.SOURCE_AGENT == "source-agent"

    def test_service_name_format(self):
        """Test that service names follow expected format."""
        service_attrs = [attr for attr in dir(ServiceNames) if not attr.startswith('_')]
        for attr in service_attrs:
            value = getattr(ServiceNames, attr)
            assert isinstance(value, str), f"ServiceNames.{attr} should be a string"
            assert len(value) > 0, f"ServiceNames.{attr} should not be empty"


class TestErrorCodes:
    """Test error code constants."""

    def test_error_codes_defined(self):
        """Test that error codes are properly defined."""
        assert hasattr(ErrorCodes, 'VALIDATION_ERROR')
        assert hasattr(ErrorCodes, 'NOT_FOUND')
        assert hasattr(ErrorCodes, 'INTERNAL_ERROR')

    def test_error_code_values(self):
        """Test that error codes have valid values."""
        error_attrs = [attr for attr in dir(ErrorCodes) if not attr.startswith('_')]
        for attr in error_attrs:
            value = getattr(ErrorCodes, attr)
            assert isinstance(value, str), f"ErrorCodes.{attr} should be a string"
            assert len(value) > 0, f"ErrorCodes.{attr} should not be empty"


if __name__ == "__main__":
    pytest.main([__file__])
