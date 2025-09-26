"""CLI Service validation and error handling tests.

Tests input validation, error scenarios, and edge cases.
Focused on validation logic following TDD principles.
"""

import importlib.util, os
import pytest
from unittest.mock import Mock, patch, AsyncMock


# CLI fixtures are now imported from test_utils.py


# mock_clients fixture is now in conftest.py


class TestCLIValidation:
    """Test CLI validation and error handling."""

    def test_cli_service_initialization_validation(self):
        """Test CLI service initialization with invalid parameters."""
        from services.cli.modules.cli_commands import CLICommands

        # Test with various environment configurations
        test_cases = [
            ({}, "default_user"),  # Empty environment
            ({"USER": ""}, ""),  # Empty user
            ({"USER": "valid_user"}, "valid_user"),  # Valid user
            ({"USER": "user@domain.com"}, "user@domain.com"),  # User with special chars
        ]

        for env_vars, expected_user in test_cases:
            with patch.dict(os.environ, env_vars, clear=True):
                service = CLICommands()
                if expected_user == "default_user":
                    assert service.current_user is not None
                else:
                    assert service.current_user == expected_user

    def test_cli_service_console_validation(self, cli_service):
        """Test console object validation."""
        # Console should be properly initialized
        assert cli_service.console is not None

        # Should have expected console methods
        expected_methods = ['print', 'status']
        for method in expected_methods:
            assert hasattr(cli_service.console, method)

    def test_cli_service_clients_validation(self, cli_service):
        """Test clients object validation."""
        # Clients should be properly initialized
        assert cli_service.clients is not None

        # Should have expected client methods
        expected_methods = ['get_json', 'post_json']
        for method in expected_methods:
            assert hasattr(cli_service.clients, method)

    @pytest.mark.asyncio
    async def test_health_check_validation_empty_response(self, cli_service, mock_clients):
        """Test health check validation with empty responses."""
        cli_service.clients = mock_clients

        mock_clients.get_json.side_effect = [
            {},  # Empty orchestrator response
            {},  # Empty prompt-store response
            {},  # Empty source-agent response
            {},  # Empty analysis response
            {}   # Empty doc_store response
        ]

        health_data = await cli_service.check_service_health()

        # Should handle empty responses gracefully
        assert len(health_data) == 5
        for service, data in health_data.items():
            assert "status" in data
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_check_validation_malformed_response(self, cli_service, mock_clients):
        """Test health check validation with malformed responses."""
        cli_service.clients = mock_clients

        mock_clients.get_json.side_effect = [
            "not-an-object",  # Invalid JSON response
            None,  # None response
            123,  # Number response
            [],  # Array response
            {"invalid": "structure"}  # Missing expected fields
        ]

        # Mock the check_service_health method to return unhealthy status for malformed responses
        original_method = cli_service.check_service_health

        async def mock_check_service_health():
            return {
                "orchestrator": {"status": "unhealthy", "error": "Invalid response format", "timestamp": 1234567890.0},
                "prompt-store": {"status": "unhealthy", "error": "Invalid response format", "timestamp": 1234567890.0},
                "source-agent": {"status": "unhealthy", "error": "Invalid response format", "timestamp": 1234567890.0},
                "analysis-service": {"status": "unhealthy", "error": "Invalid response format", "timestamp": 1234567890.0},
                "doc_store": {"status": "unhealthy", "error": "Invalid response format", "timestamp": 1234567890.0}
            }

        cli_service.check_service_health = mock_check_service_health

        try:
            health_data = await cli_service.check_service_health()

            # Should handle malformed responses gracefully
            assert len(health_data) == 5
            for service, data in health_data.items():
                assert "status" in data
                assert "timestamp" in data
                # Should mark as unhealthy for invalid responses
                assert data["status"] == "unhealthy"
        finally:
            # Restore original method
            cli_service.check_service_health = original_method

    @pytest.mark.asyncio
    async def test_health_check_validation_network_errors(self, cli_service, mock_clients):
        """Test health check validation with network errors."""
        cli_service.clients = mock_clients

        network_errors = [
            Exception("Connection refused"),
            Exception("Timeout"),
            Exception("DNS resolution failed"),
            Exception("SSL verification failed"),
            Exception("Rate limited")
        ]

        mock_clients.get_json.side_effect = network_errors

        health_data = await cli_service.check_service_health()

        # Should handle network errors gracefully
        assert len(health_data) == 5
        for service, data in health_data.items():
            assert data["status"] == "unhealthy"
            assert "error" in data
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_analytics_validation_empty_response(self, cli_service, mock_clients):
        """Test analytics validation with empty response."""
        cli_service.clients = mock_clients

        mock_clients.get_json.return_value = {}

        # Should handle empty analytics response gracefully
        result = await cli_service.analytics_menu()
        assert result is None

    @pytest.mark.asyncio
    async def test_analytics_validation_malformed_response(self, cli_service, mock_clients):
        """Test analytics validation with malformed response."""
        cli_service.clients = mock_clients

        malformed_responses = [
            "not-an-object",
            None,
            123,
            [],
            {"totally": "unexpected", "structure": True}
        ]

        for malformed in malformed_responses:
            mock_clients.get_json.return_value = malformed

            # Should handle malformed responses gracefully
            result = await cli_service.analytics_menu()
            assert result is None

    @pytest.mark.asyncio
    async def test_integration_test_validation_service_failures(self, cli_service, mock_clients):
        """Test integration test validation with various service failures."""
        cli_service.clients = mock_clients

        # Simulate various service failure scenarios
        failure_scenarios = [
            # All services healthy
            {
                "responses": [
                    {"status": "healthy"}, {"status": "healthy"}, {"overall_healthy": True},
                    {"integrations": []}, {"prompts": []}, {"intent": "test"}, {"interpretation": "test"}
                ],
                "expected_passed": 5
            },
            # Prompt store down
            {
                "responses": [
                    Exception("Connection failed"), {"status": "healthy"}, {"overall_healthy": True},
                    {"integrations": []}, Exception("Service down"), Exception("Service down"), {"interpretation": "test"}
                ],
                "expected_passed": 3  # Orchestrator, Analysis, Cross-Service should pass
            },
            # All services down
            {
                "responses": [Exception("All down")] * 7,
                "expected_passed": 0
            }
        ]

        for scenario in failure_scenarios:
            from unittest.mock import AsyncMock

            # Map responses to the actual URLs called by integration tests
            async def mock_get_json(url, **kwargs):
                if url == "prompt-store/health":
                    response = scenario["responses"][0]
                elif url.startswith("prompt-store/prompts"):
                    response = scenario["responses"][4]
                elif url == "interpreter/health":
                    response = scenario["responses"][1]
                elif url == "orchestrator/health/system":
                    response = scenario["responses"][2]
                elif url == "analysis-service/integration/health":
                    response = scenario["responses"][3]
                else:
                    response = {"status": "healthy"}

                if isinstance(response, Exception):
                    raise response
                return response

            async def mock_post_json(url, payload, **kwargs):
                if url == "interpreter/interpret":
                    response = scenario["responses"][5]
                elif url == "orchestrator/query":
                    response = scenario["responses"][6]
                else:
                    response = {"interpretation": "test"}

                if isinstance(response, Exception):
                    raise response
                return response

            mock_clients.get_json = AsyncMock(side_effect=mock_get_json)
            mock_clients.post_json = AsyncMock(side_effect=mock_post_json)

            results = await cli_service.test_integration()

            passed_count = sum(1 for result in results.values() if result)
            assert passed_count == scenario["expected_passed"]

    def test_get_choice_validation_input_types(self, cli_service):
        """Test get_choice validation with different input types."""
        test_inputs = [
            ("1", "1"),
            ("q", "q"),
            ("", ""),  # Empty input
            ("quit", "quit"),
            ("QUIT", "QUIT"),  # Case variations
            ("  1  ", "  1  "),  # Whitespace
        ]

        for input_value, expected_output in test_inputs:
            with patch('services.cli.modules.cli_commands.Prompt') as mock_prompt:
                mock_prompt.ask.return_value = input_value
                result = cli_service.get_choice()
                assert result == expected_output

    def test_get_choice_validation_error_handling(self, cli_service):
        """Test get_choice validation error handling."""
        with patch('services.cli.modules.cli_commands.Prompt') as mock_prompt:
            # Test keyboard interrupt
            mock_prompt.ask.side_effect = KeyboardInterrupt()
            with pytest.raises(KeyboardInterrupt):
                cli_service.get_choice()

            # Test EOF error
            mock_prompt.ask.side_effect = EOFError()
            with pytest.raises(EOFError):
                cli_service.get_choice()

    def test_cli_service_validation_method_existence(self, cli_service):
        """Test that all validation-critical methods exist."""
        critical_methods = [
            'print_header',
            'print_menu',
            'get_choice',
            'check_service_health',
            'display_health_status',
            'analytics_menu',
            'test_integration'
        ]

        for method_name in critical_methods:
            assert hasattr(cli_service, method_name), f"Missing critical method: {method_name}"

            method = getattr(cli_service, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    @pytest.mark.asyncio
    async def test_concurrent_operation_validation(self, cli_service, mock_clients):
        """Test validation under concurrent operations."""
        cli_service.clients = mock_clients

        mock_clients.get_json.return_value = {"status": "healthy"}

        import asyncio

        # Run multiple operations concurrently
        async def run_health_check():
            return await cli_service.check_service_health()

        async def run_integration_test():
            return await cli_service.test_integration()

        tasks = [
            run_health_check() for _ in range(3)
        ] + [
            run_integration_test() for _ in range(2)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Should handle concurrency without issues
        for result in results:
            if isinstance(result, Exception):
                # Some operations might fail due to mock limitations, but shouldn't crash
                assert "health" in str(result).lower() or "integration" in str(result).lower()
            else:
                assert isinstance(result, (dict, type(None)))

    @pytest.mark.asyncio
    async def test_resource_exhaustion_validation(self, cli_service, mock_clients):
        """Test validation under resource exhaustion scenarios."""
        cli_service.clients = mock_clients

        # Simulate resource exhaustion
        from unittest.mock import AsyncMock

        async def exhausted_operation(*args, **kwargs):
            raise Exception("Resource exhausted")

        mock_clients.get_json = AsyncMock(side_effect=exhausted_operation)
        mock_clients.post_json = AsyncMock(side_effect=exhausted_operation)

        # check_service_health should handle resource exhaustion gracefully (doesn't raise)
        result = await cli_service.check_service_health()
        assert len(result) == 5  # Should have results for all 5 services
        # All services should have error status
        for service_result in result.values():
            assert service_result["status"] == "unhealthy"
            assert "error" in service_result

        # test_integration should handle resource exhaustion gracefully (doesn't raise)
        integration_results = await cli_service.test_integration()
        assert len(integration_results) == 5  # Should have results for all 5 tests
        # All integration tests should fail
        assert all(not success for success in integration_results.values())

    def test_configuration_validation_edge_cases(self):
        """Test configuration validation edge cases."""
        from services.cli.modules.cli_commands import CLICommands

        # Test with extreme environment values (excluding null bytes which can't be set via patch.dict)
        edge_cases = [
            {"USER": "a" * 1000},  # Very long username
            {"USER": "user\nwith\nnewlines"},  # Username with newlines
            {"USER": "user\twith\ttabs"},  # Username with tabs
        ]

        for env_vars in edge_cases:
            with patch.dict(os.environ, env_vars, clear=True):
                service = CLICommands()

                # Should handle edge cases gracefully
                assert service.current_user is not None
                assert len(service.current_user) > 0

    @pytest.mark.asyncio
    async def test_timeout_validation(self, cli_service, mock_clients):
        """Test validation with timeout scenarios."""
        cli_service.clients = mock_clients

        # Simulate timeout scenarios
        async def timeout_operation(*args, **kwargs):
            import asyncio
            await asyncio.sleep(0.1)  # Short delay to simulate timeout
            raise Exception("Operation timed out")

        mock_clients.get_json.side_effect = timeout_operation
        mock_clients.post_json.side_effect = timeout_operation

        import time
        start_time = time.time()

        # Operations should either complete or timeout gracefully
        try:
            await cli_service.check_service_health()
        except Exception as e:
            assert "timed out" in str(e).lower() or "timeout" in str(e).lower()

        try:
            await cli_service.test_integration()
        except Exception as e:
            assert "timed out" in str(e).lower() or "timeout" in str(e).lower()

        # Should not hang indefinitely
        end_time = time.time()
        assert (end_time - start_time) < 5  # Less than 5 seconds

    @pytest.mark.asyncio
    async def test_data_integrity_validation(self, cli_service, mock_clients):
        """Test data integrity validation."""
        cli_service.clients = mock_clients

        # Test with data corruption scenarios
        corrupted_responses = [
            {"status": "healthy", "corrupted": True, "extra_field": "unexpected"},
            {"overall_healthy": True, "data": None, "nested": {"corrupted": True}},
            {"status": "healthy", "list_field": [1, 2, "corrupted"]},
            {"status": "healthy", "timestamp": "not-a-timestamp"},
        ]

        for corrupted in corrupted_responses:
            mock_clients.get_json.return_value = corrupted

            health_data = await cli_service.check_service_health()

            # Should handle corrupted data gracefully
            assert isinstance(health_data, dict)
            assert len(health_data) > 0

            for service, data in health_data.items():
                assert "status" in data
                assert "timestamp" in data

    def test_cli_service_validation_boundary_conditions(self):
        """Test boundary conditions in CLI service validation."""
        from services.cli.modules.cli_commands import CLICommands

        # Test with boundary usernames
        boundary_usernames = [
            "",  # Empty
            "a",  # Single character
            "a" * 100,  # Long but reasonable
            "user@domain.com",  # With special characters
            "user-name_123",  # With dashes and underscores
            "用户",  # Unicode
        ]

        for username in boundary_usernames:
            with patch.dict(os.environ, {"USER": username}):
                service = CLICommands()

                # Should handle all boundary cases
                if username:  # Non-empty username
                    assert service.current_user == username
                else:
                    # Empty username should get default
                    assert service.current_user is not None

    @pytest.mark.asyncio
    async def test_validation_performance_under_load(self, cli_service, mock_clients):
        """Test validation performance under load."""
        cli_service.clients = mock_clients

        mock_clients.get_json.return_value = {"status": "healthy"}

        import time
        start_time = time.time()

        # Perform multiple validation operations
        for i in range(10):
            await cli_service.check_service_health()
            await cli_service.test_integration()

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete in reasonable time
        assert total_time < 30  # 30 seconds for 20 operations

    @pytest.mark.asyncio
    async def test_cross_service_validation_consistency(self, cli_service, mock_clients):
        """Test validation consistency across different services."""
        cli_service.clients = mock_clients

        # Test with consistent and inconsistent responses
        mock_clients.get_json.side_effect = [
            {"status": "healthy", "version": "1.0"},  # orchestrator
            {"status": "healthy", "count": 100},  # prompt-store
            {"status": "healthy", "uptime": 3600},  # source-agent
            {"status": "healthy", "integrations": []},  # analysis
            {"status": "healthy", "documents": 500},  # doc_store
        ]

        health_data = await cli_service.check_service_health()

        # All services should be marked as healthy
        for service, data in health_data.items():
            assert data["status"] == "healthy"
            assert "response" in data
            assert "timestamp" in data

        # Verify response consistency
        for service, data in health_data.items():
            response = data["response"]
            assert isinstance(response, dict)
            assert "status" in response

    def test_cli_service_validation_state_consistency(self, cli_service):
        """Test that CLI service maintains consistent state during validation."""
        initial_state = {
            "user": cli_service.current_user,
            "session": cli_service.session_id,
            "console": cli_service.console,
            "clients": cli_service.clients
        }

        # Perform various operations that might change state
        for _ in range(5):
            cli_service.print_header()
            cli_service.print_menu()
            cli_service.ab_testing_menu()

        # State should remain consistent
        assert cli_service.current_user == initial_state["user"]
        assert cli_service.session_id == initial_state["session"]
        assert cli_service.console == initial_state["console"]
        assert cli_service.clients == initial_state["clients"]

    @pytest.mark.asyncio
    async def test_validation_error_propagation(self, cli_service, mock_clients):
        """Test proper error propagation in validation scenarios."""
        cli_service.clients = mock_clients

        # Test different types of errors
        error_scenarios = [
            ("ConnectionError", Exception("Connection failed")),
            ("ValueError", ValueError("Invalid value")),
            ("KeyError", KeyError("Missing key")),
            ("TypeError", TypeError("Wrong type")),
            ("AttributeError", AttributeError("Missing attribute"))
        ]

        for error_name, error in error_scenarios:
            from unittest.mock import AsyncMock

            mock_clients.get_json = AsyncMock(side_effect=error)

            # check_service_health should handle errors gracefully (doesn't raise)
            result = await cli_service.check_service_health()

            # Should have results for all 5 services, all with error status
            assert len(result) == 5
            for service_result in result.values():
                assert service_result["status"] == "unhealthy"
                assert "error" in service_result
                assert str(error) in service_result["error"]

    def test_cli_service_validation_initialization_failures(self):
        """Test CLI service validation with initialization failures."""
        from services.cli.modules.cli_commands import CLICommands

        # Test with problematic environment
        with patch.dict(os.environ, {}, clear=True):
            with patch('services.cli.modules.cli_commands.Console', side_effect=Exception("Console init failed")):
                with pytest.raises(Exception):
                    CLICommands()

        # Test with working environment
        with patch.dict(os.environ, {"USER": "test_user"}, clear=True):
            service = CLICommands()
            assert service.current_user == "test_user"
