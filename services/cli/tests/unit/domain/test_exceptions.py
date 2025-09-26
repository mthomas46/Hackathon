"""Tests for CLI domain exceptions"""

import pytest

from services.cli.domain.exceptions import (
    CliError,
    CliValidationError,
    CliNetworkError,
    CliTimeoutError,
    CliCommandError,
    CliConfigurationError,
    CliAuthenticationError,
    CliAuthorizationError,
    CliInputError,
    CliOutputError,
    CliCacheError,
)


class TestCliExceptions:
    """Test CLI domain exceptions."""

    def test_cli_error_base(self):
        """Test base CliError exception."""
        error = CliError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_cli_validation_error(self):
        """Test CliValidationError exception."""
        error = CliValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert isinstance(error, CliError)
        assert isinstance(error, Exception)

    def test_cli_network_error(self):
        """Test CliNetworkError exception."""
        error = CliNetworkError("Network failure")
        assert str(error) == "Network failure"
        assert isinstance(error, CliError)

    def test_cli_timeout_error(self):
        """Test CliTimeoutError exception."""
        error = CliTimeoutError("Operation timed out")
        assert str(error) == "Operation timed out"
        assert isinstance(error, CliNetworkError)
        assert isinstance(error, CliError)

    def test_cli_command_error(self):
        """Test CliCommandError exception."""
        error = CliCommandError("Command failed")
        assert str(error) == "Command failed"
        assert isinstance(error, CliError)

    def test_cli_configuration_error(self):
        """Test CliConfigurationError exception."""
        error = CliConfigurationError("Configuration error")
        assert str(error) == "Configuration error"
        assert isinstance(error, CliError)

    def test_cli_authentication_error(self):
        """Test CliAuthenticationError exception."""
        error = CliAuthenticationError("Authentication failed")
        assert str(error) == "Authentication failed"
        assert isinstance(error, CliError)

    def test_cli_authorization_error(self):
        """Test CliAuthorizationError exception."""
        error = CliAuthorizationError("Authorization denied")
        assert str(error) == "Authorization denied"
        assert isinstance(error, CliError)

    def test_cli_input_error(self):
        """Test CliInputError exception."""
        error = CliInputError("Invalid input provided")
        assert str(error) == "Invalid input provided"
        assert isinstance(error, CliValidationError)
        assert isinstance(error, CliError)

    def test_cli_output_error(self):
        """Test CliOutputError exception."""
        error = CliOutputError("Output generation failed")
        assert str(error) == "Output generation failed"
        assert isinstance(error, CliError)

    def test_cli_cache_error(self):
        """Test CliCacheError exception."""
        error = CliCacheError("Cache operation failed")
        assert str(error) == "Cache operation failed"
        assert isinstance(error, CliError)

    def test_exception_inheritance(self):
        """Test that exceptions properly inherit from base classes."""
        # Test that all exceptions inherit from CliError
        exceptions = [
            CliValidationError("test"),
            CliNetworkError("test"),
            CliTimeoutError("test"),
            CliCommandError("test"),
            CliConfigurationError("test"),
            CliAuthenticationError("test"),
            CliAuthorizationError("test"),
            CliInputError("test"),
            CliOutputError("test"),
            CliCacheError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, CliError)
            assert isinstance(exc, Exception)

    def test_exception_with_cause(self):
        """Test exceptions with underlying causes."""
        original_error = ValueError("Original error")
        cli_error = CliNetworkError("Network failed")

        # Test that we can set the cause
        try:
            raise cli_error from original_error
        except CliNetworkError as e:
            assert e.__cause__ == original_error
