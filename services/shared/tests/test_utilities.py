"""Tests for shared utilities module.

Comprehensive test coverage for core utility functions including:
- ID generation and validation
- String processing utilities
- Database identifier validation
- Date/time utilities
- Configuration helpers
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from services.shared.utilities import (
    generate_id,
    clean_string,
    safe_filename,
    sanitize_sql_identifier,
    validate_sql_identifier,
    iso_datetime,
    utc_now,
    attach_self_register,
    get_service_client,
    setup_common_middleware,
)


class TestIdGeneration:
    """Test ID generation utilities."""

    def test_generate_id_basic(self):
        """Test basic ID generation."""
        id1 = generate_id()
        id2 = generate_id()

        assert isinstance(id1, str)
        assert len(id1) > 0
        assert id1 != id2  # Should be unique

    def test_generate_id_length(self):
        """Test ID generation with specific length."""
        # Test default length
        id_default = generate_id()
        assert len(id_default) == 16  # Default length

    def test_generate_id_uniqueness(self):
        """Test ID uniqueness across multiple generations."""
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100  # All should be unique


class TestStringProcessing:
    """Test string processing utilities."""

    def test_clean_string_basic(self):
        """Test basic string cleaning."""
        result = clean_string("  Hello World  ")
        assert result == "Hello World"

    def test_clean_string_none(self):
        """Test clean_string with None input."""
        result = clean_string(None)
        assert result == ""

    def test_clean_string_empty(self):
        """Test clean_string with empty string."""
        result = clean_string("")
        assert result == ""

    def test_clean_string_special_chars(self):
        """Test clean_string with special characters."""
        result = clean_string("Hello\n\t\rWorld")
        assert result == "Hello World"

    def test_safe_filename_basic(self):
        """Test basic safe filename generation."""
        result = safe_filename("test file.txt")
        assert result == "test_file.txt"

    def test_safe_filename_special_chars(self):
        """Test safe_filename with various special characters."""
        result = safe_filename("file:with*chars?.txt")
        assert "file" in result
        assert "*" not in result
        assert "?" not in result
        assert ":" not in result


class TestSqlIdentifierValidation:
    """Test SQL identifier validation and sanitization."""

    def test_validate_sql_identifier_valid(self):
        """Test validation of valid SQL identifiers."""
        assert validate_sql_identifier("valid_table") == True
        assert validate_sql_identifier("valid_column_123") == True
        assert validate_sql_identifier("_private_field") == True

    def test_validate_sql_identifier_invalid(self):
        """Test validation of invalid SQL identifiers."""
        assert validate_sql_identifier("") == False
        assert validate_sql_identifier("table-name") == False  # Hyphens not allowed
        assert validate_sql_identifier("table name") == False  # Spaces not allowed
        assert validate_sql_identifier("123table") == False  # Cannot start with number
        assert validate_sql_identifier("table;drop") == False  # SQL injection attempt

    def test_sanitize_sql_identifier_valid(self):
        """Test sanitization of valid identifiers."""
        result = sanitize_sql_identifier("valid_table")
        assert result == "valid_table"

    def test_sanitize_sql_identifier_invalid(self):
        """Test sanitization of invalid identifiers."""
        result = sanitize_sql_identifier("table-name")
        assert result == "table_name"  # Hyphen becomes underscore

        result = sanitize_sql_identifier("table name")
        assert result == "table_name"  # Space becomes underscore

        result = sanitize_sql_identifier("123table")
        assert result == "_123table"  # Number prefix gets underscore


class TestDatetimeUtilities:
    """Test date/time utility functions."""

    def test_iso_datetime(self):
        """Test ISO datetime formatting."""
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = iso_datetime(dt)
        assert result == "2023-01-01T12:00:00+00:00"

    def test_iso_datetime_none(self):
        """Test iso_datetime with None input."""
        result = iso_datetime(None)
        assert result is None

    def test_utc_now(self):
        """Test UTC now timestamp generation."""
        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)

        assert isinstance(result, datetime)
        assert result.tzinfo is not None
        assert before <= result <= after


class TestServiceRegistration:
    """Test service registration utilities."""

    @patch("services.shared.utilities.ServiceClients")
    def test_attach_self_register(self, mock_clients):
        """Test self-registration functionality."""
        mock_app = MagicMock()
        mock_service_name = "test-service"

        # Mock the ServiceClients instance
        mock_client_instance = MagicMock()
        mock_clients.return_value = mock_client_instance

        attach_self_register(mock_app, mock_service_name)

        # Verify ServiceClients was instantiated
        mock_clients.assert_called_once()

        # Verify register_service was called on the app
        mock_app.add_event_handler.assert_called()

    @patch("services.shared.utilities.ServiceClients")
    def test_attach_self_register_error_handling(self, mock_clients):
        """Test error handling in self-registration."""
        mock_app = MagicMock()
        mock_service_name = "test-service"

        # Make ServiceClients raise an exception
        mock_clients.side_effect = Exception("Connection failed")

        # Should not raise exception
        attach_self_register(mock_app, mock_service_name)


class TestServiceClient:
    """Test service client utilities."""

    @patch("services.shared.utilities.ServiceClients")
    def test_get_service_client(self, mock_clients):
        """Test service client retrieval."""
        mock_client_instance = MagicMock()
        mock_clients.return_value = mock_client_instance

        result = get_service_client("test-service")

        mock_clients.assert_called_once()
        assert result == mock_client_instance


class TestMiddlewareSetup:
    """Test middleware setup utilities."""

    def test_setup_common_middleware_basic(self):
        """Test basic middleware setup."""
        mock_app = MagicMock()

        setup_common_middleware(mock_app, "test-service")

        # Verify middleware was added to app
        mock_app.add_middleware.assert_called()

    def test_setup_common_middleware_with_rate_limits(self):
        """Test middleware setup with rate limiting."""
        mock_app = MagicMock()
        rate_limits = {"api": (10, 60)}  # 10 requests per 60 seconds

        setup_common_middleware(
            mock_app, "test-service", enable_rate_limit=True, rate_limits=rate_limits
        )

        # Verify middleware was called with rate limits
        mock_app.add_middleware.assert_called()

    def test_setup_common_middleware_import_error(self):
        """Test middleware setup when ServiceMiddleware import fails."""
        mock_app = MagicMock()

        # Temporarily break the import
        with patch(
            "services.shared.utilities.ServiceMiddleware", side_effect=ImportError
        ):
            setup_common_middleware(mock_app, "test-service")

            # Should still work without raising exception
            mock_app.add_middleware.assert_called()


class TestIntegration:
    """Integration tests for utility combinations."""

    def test_full_service_initialization_flow(self):
        """Test complete service initialization using utilities."""
        mock_app = MagicMock()
        service_name = "integration-test-service"

        # Simulate full service setup
        setup_common_middleware(mock_app, service_name)

        # Verify middleware setup
        mock_app.add_middleware.assert_called()

    def test_id_and_string_processing_pipeline(self):
        """Test pipeline of ID generation and string processing."""
        # Generate an ID
        entity_id = generate_id()

        # Clean and sanitize it (simulating user input processing)
        clean_id = clean_string(entity_id)
        safe_id = sanitize_sql_identifier(clean_id)

        assert isinstance(clean_id, str)
        assert isinstance(safe_id, str)
        assert len(clean_id) > 0
        assert len(safe_id) > 0

    def test_datetime_formatting_pipeline(self):
        """Test datetime processing pipeline."""
        # Get current time
        now = utc_now()

        # Format as ISO
        iso_string = iso_datetime(now)

        # Verify it's a valid ISO format
        assert isinstance(iso_string, str)
        assert "T" in iso_string  # ISO format has T separator
        assert "+" in iso_string or "Z" in iso_string  # Has timezone


if __name__ == "__main__":
    pytest.main([__file__])
