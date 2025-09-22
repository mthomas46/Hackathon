"""Tests for CLI service logging integration with LogCollectorClient."""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock the logger client before importing the main CLI module
from services.shared.utilities.logging_client import LogCollectorClient

# Create mock logger client
mock_logger_client = AsyncMock(spec=LogCollectorClient)

# Patch the logger client before importing the CLI module
with patch("services.cli.main.get_log_collector_client") as mock_get_client:
    mock_get_client.return_value = mock_logger_client

    # Now import the CLI module
    # Override the logger client
    import main
    from main import cli, logger_client

    main.logger_client = mock_logger_client


class TestCLILoggingIntegration:
    """Test CLI service logging integration with LogCollectorClient."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_cli_startup_logging(self):
        """Test that CLI startup logging is initialized."""
        # The startup logging should have been called during module import
        # Verify it was called with the correct parameters
        startup_calls = [
            call for call in mock_logger_client.log_business_event.call_args_list if call[0][0] == "cli_service_startup"
        ]

        assert len(startup_calls) >= 1
        startup_data = startup_calls[0][0][1]
        assert "capabilities" in startup_data
        assert "commands" in startup_data
        assert "features" in startup_data

    @pytest.mark.asyncio
    async def test_health_command_logging(self, runner):
        """Test health command logging."""
        # Mock the CLI service health method
        with patch("main.cli_service") as mock_cli_service:
            mock_cli_service.display_health_status.return_value = {"status": "healthy"}

            # Run health command
            result = runner.invoke(cli, ["health"])
            assert result.exit_code == 0

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # startup + health check
            assert mock_logger_client.log_performance_metric.call_count >= 1

            # Check health check business events
            health_calls = [
                call for call in mock_logger_client.log_business_event.call_args_list if "health_check" in call[0][0]
            ]

            assert len(health_calls) >= 2  # started and completed

            # Check start event
            start_call = next((call for call in health_calls if call[0][0] == "cli_health_check_started"), None)
            assert start_call is not None
            start_data = start_call[0][1]
            assert start_data["command"] == "health"
            assert start_data["scope"] == "all_services"
            assert "command_id" in start_data

            # Check completion event
            completion_call = next((call for call in health_calls if call[0][0] == "cli_health_check_completed"), None)
            assert completion_call is not None
            completion_data = completion_call[0][1]
            assert completion_data["success"] is True
            assert "processing_time_seconds" in completion_data

    @pytest.mark.asyncio
    async def test_health_command_failure_logging(self, runner):
        """Test health command failure logging."""
        # Mock the CLI service to raise an exception
        with patch("main.cli_service") as mock_cli_service:
            mock_cli_service.display_health_status.side_effect = Exception("Service unreachable")

            # Run health command (should fail but still log)
            result = runner.invoke(cli, ["health"])
            # CLI might handle exceptions gracefully, check that logging occurred

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 3  # startup + health started + failed

            # Check error call
            error_calls = mock_logger_client.log_error.call_args_list
            health_error = next((call for call in error_calls if "CLI health check failed" in call[0][0]), None)
            assert health_error is not None
            assert health_error[0][1]["error_type"] == "Exception"

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "cli_health_check_failed"
            ]
            assert len(failure_events) >= 1

    @pytest.mark.asyncio
    async def test_interactive_command_logging_setup(self, runner):
        """Test that interactive command sets up logging properly."""
        # Mock the CLI service run method to return quickly
        with patch("main.cli_service") as mock_cli_service, patch("asyncio.run") as mock_asyncio_run:

            mock_cli_service.run.return_value = None

            # Run interactive command
            result = runner.invoke(cli, ["interactive"])
            assert result.exit_code == 0

            # Verify logging calls for interactive session
            interactive_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if "interactive_session" in call[0][0]
            ]

            assert len(interactive_calls) >= 2  # started and completed

            # Check start event
            start_call = next(
                (call for call in interactive_calls if call[0][0] == "cli_interactive_session_started"), None
            )
            assert start_call is not None
            start_data = start_call[0][1]
            assert start_data["command"] == "interactive"
            assert start_data["mode"] == "menu_driven"
            assert "session_id" in start_data

            # Check completion event
            completion_call = next(
                (call for call in interactive_calls if call[0][0] == "cli_interactive_session_completed"), None
            )
            assert completion_call is not None
            completion_data = completion_call[0][1]
            assert completion_data["exit_type"] == "normal_exit"
            assert completion_data["success"] is True

    @pytest.mark.asyncio
    async def test_interactive_command_keyboard_interrupt_logging(self, runner):
        """Test keyboard interrupt logging in interactive mode."""
        # Mock the CLI service to raise KeyboardInterrupt
        with patch("main.cli_service") as mock_cli_service, patch("asyncio.run") as mock_asyncio_run:

            mock_asyncio_run.side_effect = KeyboardInterrupt()

            # Run interactive command (will be interrupted)
            result = runner.invoke(cli, ["interactive"])
            # Should exit gracefully due to keyboard interrupt

            # Verify interrupt logging
            interrupt_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "cli_interactive_session_interrupted"
            ]
            assert len(interrupt_calls) >= 1

            interrupt_data = interrupt_calls[0][0][1]
            assert interrupt_data["interruption_type"] == "user_interrupt"
            assert interrupt_data["exit_type"] == "keyboard_interrupt"
            assert "duration_seconds" in interrupt_data

    @pytest.mark.asyncio
    async def test_interactive_command_exception_logging(self, runner):
        """Test exception logging in interactive mode."""
        # Mock the CLI service to raise an exception
        with patch("main.cli_service") as mock_cli_service, patch("asyncio.run") as mock_asyncio_run:

            mock_asyncio_run.side_effect = Exception("Interactive session error")

            # Run interactive command (will fail)
            result = runner.invoke(cli, ["interactive"])
            # Should handle exception gracefully

            # Verify exception logging
            failure_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "cli_interactive_session_failed"
            ]
            assert len(failure_calls) >= 1

            failure_data = failure_calls[0][0][1]
            assert failure_data["exit_type"] == "fatal_error"
            assert failure_data["error_message"] == "Interactive session error"
            assert "duration_seconds" in failure_data

    def test_request_id_generation(self, runner):
        """Test that command request IDs are properly generated."""
        with patch("main.cli_service") as mock_cli_service:
            mock_cli_service.display_health_status.return_value = {"status": "healthy"}

            # Run health command
            runner.invoke(cli, ["health"])

            # Check that request IDs are generated and used consistently
            business_calls = mock_logger_client.log_business_event.call_args_list
            perf_calls = mock_logger_client.log_performance_metric.call_args_list

            # Extract request IDs from health check calls
            request_ids = set()
            for call in business_calls + perf_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get("request_id")
                    if request_id and "health_check" in call[0][0]:
                        request_ids.add(request_id)

            # Should have at least one health check request ID
            assert len(request_ids) >= 1
            request_id = list(request_ids)[0]
            assert request_id.startswith("cli_health_check_")

    def test_session_id_generation(self, runner):
        """Test that interactive session IDs are properly generated."""
        with patch("main.cli_service") as mock_cli_service, patch("asyncio.run") as mock_asyncio_run:

            mock_cli_service.run.return_value = None

            # Run interactive command
            runner.invoke(cli, ["interactive"])

            # Check that session IDs are generated
            session_calls = [
                call for call in mock_logger_client.log_business_event.call_args_list if "session_id" in call[0][1]
            ]

            assert len(session_calls) >= 1
            session_data = session_calls[0][0][1]
            assert session_data["session_id"].startswith("cli_session_")

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, runner):
        """Test graceful handling when logging is disabled."""
        # Temporarily disable logger client
        original_logger = main.logger_client
        main.logger_client = None

        try:
            with patch("main.cli_service") as mock_cli_service:
                mock_cli_service.display_health_status.return_value = {"status": "healthy"}

                # Run health command - should still work without logging
                result = runner.invoke(cli, ["health"])
                assert result.exit_code == 0

        finally:
            # Restore logger client
            main.logger_client = original_logger

    @pytest.mark.asyncio
    async def test_multiple_commands_logging_isolation(self, runner):
        """Test that logging for different commands is properly isolated."""
        with patch("main.cli_service") as mock_cli_service:
            mock_cli_service.display_health_status.return_value = {"status": "healthy"}

            # Run health command twice
            runner.invoke(cli, ["health"])
            runner.invoke(cli, ["health"])

            # Check that we have separate request IDs for each command execution
            health_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "cli_health_check_started"
            ]

            assert len(health_calls) >= 2

            # Extract request IDs
            request_ids = set()
            for call in health_calls:
                request_ids.add(call[0][1]["command_id"])

            # Should have 2 different request IDs
            assert len(request_ids) == 2

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, runner):
        """Test that performance metrics are accurately measured."""
        with patch("main.cli_service") as mock_cli_service:
            mock_cli_service.display_health_status.return_value = {"status": "healthy"}

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            # Run health command
            runner.invoke(cli, ["health"])

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            health_perf = next((call for call in perf_calls if call[0][0] == "cli_health_check"), None)
            assert health_perf is not None

            processing_time = health_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    def test_verbose_flag_handling(self, runner):
        """Test that verbose flag is properly handled in context."""
        with patch("main.cli_service") as mock_cli_service:
            mock_cli_service.display_health_status.return_value = {"status": "healthy"}

            # Run command with verbose flag
            result = runner.invoke(cli, ["--verbose", "health"])
            assert result.exit_code == 0

            # The verbose flag should be stored in context but not affect logging
            # (logging behavior should be the same regardless of verbose flag)
            health_calls = [
                call for call in mock_logger_client.log_business_event.call_args_list if "health_check" in call[0][0]
            ]

            assert len(health_calls) >= 2  # started and completed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
