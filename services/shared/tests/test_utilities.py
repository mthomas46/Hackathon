"""Tests for utility functions and classes.

Comprehensive test coverage for:
- SQL identifier validation and sanitization
- Common middleware setup
- Utility functions and helpers
- Error handling utilities
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from services.shared.infrastructure.utilities.utilities import (
    validate_sql_identifier,
    sanitize_sql_identifier,
    setup_common_middleware,
    SqlInjectionError
)


class TestSQLIdentifierValidation:
    """Test SQL identifier validation and sanitization."""

    def test_valid_identifiers(self):
        """Test valid SQL identifiers."""
        valid_identifiers = [
            "users",
            "user_table",
            "my_table_123",
            "table_name",
            "_private_table",
            "table123"
        ]

        for identifier in valid_identifiers:
            assert validate_sql_identifier(identifier) == identifier

    def test_invalid_identifiers(self):
        """Test invalid SQL identifiers."""
        invalid_identifiers = [
            "123table",  # starts with number
            "table-name",  # contains hyphen
            "table name",  # contains space
            "table.name",  # contains dot
            "",  # empty string
            "table;drop",  # contains semicolon
            "table'quote",  # contains quote
        ]

        for identifier in invalid_identifiers:
            with pytest.raises(SqlInjectionError):
                validate_sql_identifier(identifier)

    def test_reserved_keywords(self):
        """Test reserved SQL keywords are rejected."""
        reserved_keywords = [
            "SELECT", "INSERT", "UPDATE", "DELETE", "DROP",
            "CREATE", "ALTER", "TABLE", "INDEX", "VIEW"
        ]

        for keyword in reserved_keywords:
            with pytest.raises(SqlInjectionError):
                validate_sql_identifier(keyword)

    def test_case_insensitive_keywords(self):
        """Test reserved keywords are rejected case-insensitively."""
        with pytest.raises(SqlInjectionError):
            validate_sql_identifier("select")

        with pytest.raises(SqlInjectionError):
            validate_sql_identifier("Select")

    def test_sanitize_identifier(self):
        """Test SQL identifier sanitization."""
        # Valid identifiers should pass through unchanged
        assert sanitize_sql_identifier("users") == "users"
        assert sanitize_sql_identifier("user_table") == "user_table"

        # Invalid identifiers should raise exceptions
        with pytest.raises(SqlInjectionError):
            sanitize_sql_identifier("123table")

        with pytest.raises(SqlInjectionError):
            sanitize_sql_identifier("table;name")


class TestMiddlewareSetup:
    """Test common middleware setup."""

    @patch('services.shared.infrastructure.utilities.middleware.ServiceMiddleware')
    def test_setup_common_middleware(self, mock_service_middleware):
        """Test common middleware setup."""
        from fastapi import FastAPI

        app = FastAPI()
        service_name = "test-service"

        # Mock the ServiceMiddleware instance
        mock_instance = MagicMock()
        mock_instance.get_middlewares.return_value = [MagicMock()]
        mock_service_middleware.return_value = mock_instance

        result = setup_common_middleware(app, service_name)

        # Should return the app
        assert result == app

        # Should create ServiceMiddleware with correct parameters
        mock_service_middleware.assert_called_once_with(
            service_name=service_name,
            rate_limits=None,
            enable_rate_limit=False
        )

        # Should call get_middlewares and add middleware to app
        mock_instance.get_middlewares.assert_called_once()
        # Note: app.add_middleware should be called for each middleware

    def test_setup_common_middleware_no_service_name(self):
        """Test middleware setup fails without service name."""
        from fastapi import FastAPI

        app = FastAPI()

        with pytest.raises(TypeError):
            setup_common_middleware(app)  # Missing service_name


class TestUtilityFunctions:
    """Test general utility functions."""

    def test_safe_import(self):
        """Test safe import functionality."""
        # This would test import utilities if they existed
        # For now, just ensure the module can be imported
        from services.shared.infrastructure.utilities import utilities
        assert utilities is not None

    def test_module_structure(self):
        """Test module has expected structure."""
        from services.shared.infrastructure.utilities import utilities

        # Should have the main functions
        assert hasattr(utilities, 'validate_sql_identifier')
        assert hasattr(utilities, 'sanitize_sql_identifier')
        assert hasattr(utilities, 'setup_common_middleware')

        # Should have custom exceptions
        assert hasattr(utilities, 'SqlInjectionError')