"""Tests for GitHub MCP logging integration with LogCollectorClient."""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import httpx

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app, logger_client
from services.shared.utilities.logging_client import LogCollectorClient


class TestGitHubMCPLoggingIntegration:
    """Test GitHub MCP logging integration with LogCollectorClient."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

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
    async def test_tool_invocation_mock_mode_successful_logging(self, client, mock_logger_client):
        """Test successful tool invocation in mock mode logging."""
        # Mock the necessary components
        mock_result = {"repositories": [{"name": "test-repo", "stars": 42}]}

        with patch('main.mock_implementations') as mock_impl, \
             patch('main.event_system') as mock_events, \
             patch('main.config') as mock_config:

            mock_impl.invoke_tool.return_value = mock_result
            mock_config.is_mock_default.return_value = True
            mock_config.is_read_only.return_value = False
            mock_config.should_use_official_mcp.return_value = False

            # Make request
            request_data = {
                "arguments": {"owner": "testuser", "repo": "testrepo"},
                "correlation_id": "test-correlation-123"
            }

            response = client.post("/tools/repos.get/invoke", json=request_data)
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["tool"] == "repos.get"

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [call for call in mock_logger_client.log_business_event.call_args_list
                            if call[0][0] in ['github_mcp_tool_invocation_started', 'github_mcp_tool_invocation_completed']]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == 'github_mcp_tool_invocation_started')
            start_data = start_call[0][1]
            assert start_data['tool'] == 'repos.get'
            assert start_data['execution_mode'] == 'mock'
            assert start_data['correlation_id'] == 'test-correlation-123'
            assert start_data['argument_count'] == 2
            assert start_data['upstream_proxy'] is False
            assert 'request_id' in start_data

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == 'github_mcp_tool_invocation_completed')
            completion_data = completion_call[0][1]
            assert completion_data['tool'] == 'repos.get'
            assert completion_data['execution_mode'] == 'mock'
            assert completion_data['has_data'] is True
            assert completion_data['success'] is True
            assert 'processing_time_seconds' in completion_data
            assert 'result_size_bytes' in completion_data

    @pytest.mark.asyncio
    async def test_tool_invocation_upstream_proxy_successful_logging(self, client, mock_logger_client):
        """Test successful tool invocation via upstream proxy logging."""
        # Mock upstream proxy response
        upstream_result = {"data": "upstream response"}

        with patch('main.config') as mock_config, \
             patch('main.ServiceClients') as mock_clients_class:

            # Setup mocks for upstream proxy mode
            mock_config.is_mock_default.return_value = False
            mock_config.is_read_only.return_value = False
            mock_config.should_use_official_mcp.return_value = True
            mock_config.get_official_mcp_base_url.return_value = "https://api.github-mcp.com"

            # Mock the service client
            mock_client = AsyncMock()
            mock_client.post_json.return_value = upstream_result
            mock_clients_class.return_value = mock_client

            # Make request
            request_data = {
                "arguments": {"repo": "test/repo"},
                "mock": False
            }

            response = client.post("/tools/repos.get/invoke", json=request_data)
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["result"] == upstream_result

            # Check completion event for upstream proxy
            completion_events = [call for call in mock_logger_client.log_business_event.call_args_list
                               if call[0][0] == 'github_mcp_tool_invocation_completed']
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            assert completion_data['execution_mode'] == 'upstream_proxy'
            assert completion_data['upstream_url'] == 'https://api.github-mcp.com'
            assert completion_data['success'] is True

    @pytest.mark.asyncio
    async def test_tool_invocation_read_only_block_logging(self, client, mock_logger_client):
        """Test read-only mode blocking write operations logging."""
        with patch('main.config') as mock_config:

            # Setup read-only mode
            mock_config.is_read_only.return_value = True
            mock_config.is_mock_default.return_value = True

            # Make request with write operation
            request_data = {
                "arguments": {"title": "New Issue", "body": "Description"},
                "write": True
            }

            response = client.post("/tools/issues.create/invoke", json=request_data)
            assert response.status_code == 403

            # Verify blocking logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and blocked

            # Check blocking business event
            block_events = [call for call in mock_logger_client.log_business_event.call_args_list
                          if call[0][0] == 'github_mcp_tool_invocation_blocked']
            assert len(block_events) >= 1

            block_data = block_events[0][0][1]
            assert block_data['tool'] == 'issues.create'
            assert block_data['block_reason'] == 'read_only_mode'

            # Check error log
            error_calls = mock_logger_client.log_error.call_args_list
            block_error = next((call for call in error_calls if 'read-only mode violation' in call[0][0].lower()), None)
            assert block_error is not None

    @pytest.mark.asyncio
    async def test_tool_invocation_upstream_proxy_failure_logging(self, client, mock_logger_client):
        """Test upstream proxy failure logging."""
        with patch('main.config') as mock_config, \
             patch('main.ServiceClients') as mock_clients_class:

            # Setup upstream proxy mode
            mock_config.is_mock_default.return_value = False
            mock_config.is_read_only.return_value = False
            mock_config.should_use_official_mcp.return_value = True
            mock_config.get_official_mcp_base_url.return_value = "https://api.github-mcp.com"

            # Mock service client to raise exception
            mock_client = AsyncMock()
            mock_client.post_json.side_effect = Exception("Connection timeout")
            mock_clients_class.return_value = mock_client

            # Make request
            request_data = {
                "arguments": {"repo": "test/repo"}
            }

            response = client.post("/tools/repos.get/invoke", json=request_data)
            assert response.status_code == 502

            # Verify upstream failure logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failed

            # Check failure business event
            failure_events = [call for call in mock_logger_client.log_business_event.call_args_list
                            if call[0][0] == 'github_mcp_tool_invocation_failed']
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data['execution_mode'] == 'upstream_proxy'
            assert failure_data['upstream_url'] == 'https://api.github-mcp.com'
            assert failure_data['error_type'] == 'Exception'
            assert 'Connection timeout' in failure_data['error_message']

    @pytest.mark.asyncio
    async def test_tool_invocation_local_execution_failure_logging(self, client, mock_logger_client):
        """Test local tool execution failure logging."""
        with patch('main.mock_implementations') as mock_impl, \
             patch('main.config') as mock_config:

            # Setup mock mode
            mock_config.is_mock_default.return_value = True
            mock_config.is_read_only.return_value = False
            mock_config.should_use_official_mcp.return_value = False

            # Mock implementation to raise exception
            mock_impl.invoke_tool.side_effect = Exception("Invalid repository")

            # Make request
            request_data = {
                "arguments": {"owner": "invalid", "repo": "nonexistent"}
            }

            response = client.post("/tools/repos.get/invoke", json=request_data)
            assert response.status_code == 500

            # Verify local execution failure logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failed

            # Check failure business event
            failure_events = [call for call in mock_logger_client.log_business_event.call_args_list
                            if call[0][0] == 'github_mcp_tool_invocation_failed']
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data['execution_mode'] == 'mock'
            assert failure_data['error_type'] == 'Exception'
            assert 'Invalid repository' in failure_data['error_message']

    @pytest.mark.asyncio
    async def test_different_execution_modes_logging(self, client, mock_logger_client):
        """Test logging for different execution modes."""
        modes_and_results = [
            ("mock", {"mock": True}, "mock"),
            ("real_api", {"mock": False}, "real_api"),
        ]

        for mode_name, request_params, expected_mode in modes_and_results:
            with patch('main.mock_implementations') as mock_impl, \
                 patch('main.real_implementations') as mock_real_impl, \
                 patch('main.config') as mock_config, \
                 patch('main.event_system') as mock_events:

                # Setup config
                mock_config.is_read_only.return_value = False
                mock_config.should_use_official_mcp.return_value = False

                # Mock implementations
                mock_result = {"data": f"{mode_name}_result"}
                if expected_mode == "mock":
                    mock_impl.invoke_tool.return_value = mock_result
                else:
                    mock_real_impl.invoke_tool.return_value = mock_result

                # Make request
                request_data = {
                    "arguments": {"test": "data"},
                    **request_params
                }

                response = client.post("/tools/test.tool/invoke", json=request_data)
                assert response.status_code == 200

                # Check completion event for correct mode
                completion_events = [call for call in mock_logger_client.log_business_event.call_args_list
                                   if call[0][0] == 'github_mcp_tool_invocation_completed']

                # Get the most recent completion event
                completion_data = completion_events[-1][0][1]
                assert completion_data['execution_mode'] == expected_mode
                assert completion_data['tool'] == 'test.tool'

    @pytest.mark.asyncio
    async def test_startup_logging(self, mock_logger_client):
        """Test service startup logging."""
        from main import startup_event

        await startup_event()

        # Verify startup logging
        assert mock_logger_client.log_business_event.call_count >= 1
        assert mock_logger_client.log_info.call_count >= 1

        # Check startup business event
        business_call = mock_logger_client.log_business_event.call_args
        assert business_call[0][0] == 'github_mcp_startup'
        startup_data = business_call[0][1]
        assert 'capabilities' in startup_data
        assert 'tool_categories' in startup_data
        assert 'features' in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert 'GitHub MCP service started' in info_call[0][0]

    @pytest.mark.asyncio
    async def test_shutdown_logging(self, mock_logger_client):
        """Test service shutdown logging."""
        from main import shutdown_event

        # Set logger client
        global logger_client
        logger_client = mock_logger_client

        await shutdown_event()

        # Verify shutdown logging
        assert mock_logger_client.log_info.call_count >= 1

        info_call = mock_logger_client.log_info.call_args
        assert 'GitHub MCP service shutting down' in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        # Mock components
        mock_result = {"data": "test result"}

        with patch('main.mock_implementations') as mock_impl, \
             patch('main.config') as mock_config, \
             patch('main.event_system') as mock_events:

            mock_config.is_mock_default.return_value = True
            mock_config.is_read_only.return_value = False
            mock_config.should_use_official_mcp.return_value = False

            mock_impl.invoke_tool.return_value = mock_result

            # Make request - should still work without logging
            request_data = {
                "arguments": {"test": "data"}
            }

            response = client.post("/tools/test.tool/invoke", json=request_data)
            assert response.status_code == 200

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        # Mock components
        mock_result = {"data": "test"}

        with patch('main.mock_implementations') as mock_impl, \
             patch('main.config') as mock_config, \
             patch('main.event_system') as mock_events:

            mock_config.is_mock_default.return_value = True
            mock_config.is_read_only.return_value = False
            mock_config.should_use_official_mcp.return_value = False

            mock_impl.invoke_tool.return_value = mock_result

            # Make request
            request_data = {"arguments": {"test": "data"}}
            client.post("/tools/test.tool/invoke", json=request_data)

            # Check that request IDs are generated and used consistently
            business_calls = mock_logger_client.log_business_event.call_args_list
            perf_calls = mock_logger_client.log_performance_metric.call_args_list

            # Extract request IDs from all calls
            request_ids = set()
            for call in business_calls + perf_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get('request_id')
                    if request_id and 'tool_invocation' in call[0][0]:
                        request_ids.add(request_id)

            # All calls should use the same request ID
            assert len(request_ids) == 1
            request_id = list(request_ids)[0]
            assert request_id.startswith('github_mcp_invoke_')

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        # Mock components
        mock_result = {"data": "test result"}

        with patch('main.mock_implementations') as mock_impl, \
             patch('main.config') as mock_config, \
             patch('main.event_system') as mock_events:

            mock_config.is_mock_default.return_value = True
            mock_config.is_read_only.return_value = False
            mock_config.should_use_official_mcp.return_value = False

            mock_impl.invoke_tool.return_value = mock_result

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            # Make request
            request_data = {"arguments": {"test": "data"}}
            response = client.post("/tools/test.tool/invoke", json=request_data)
            assert response.status_code == 200

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            invoke_perf = next((call for call in perf_calls if call[0][0] == 'github_mcp_tool_invocation'), None)
            assert invoke_perf is not None

            processing_time = invoke_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_result_metrics_calculation(self, client, mock_logger_client):
        """Test that result metrics are calculated correctly."""
        test_cases = [
            ({"data": "result"}, True, True),  # Has data, structured
            ({}, False, True),  # Empty dict, no data but structured
            (None, False, False),  # None, no data, not structured
            ([], False, True),  # Empty list, no data but structured
        ]

        for mock_result, expected_has_data, expected_structured in test_cases:
            with patch('main.mock_implementations') as mock_impl, \
                 patch('main.config') as mock_config, \
                 patch('main.event_system') as mock_events:

                mock_config.is_mock_default.return_value = True
                mock_config.is_read_only.return_value = False
                mock_config.should_use_official_mcp.return_value = False

                mock_impl.invoke_tool.return_value = mock_result

                # Make request
                request_data = {"arguments": {"test": "data"}}
                response = client.post("/tools/test.tool/invoke", json=request_data)
                assert response.status_code == 200

                # Check completion event metrics
                completion_events = [call for call in mock_logger_client.log_business_event.call_args_list
                                   if call[0][0] == 'github_mcp_tool_invocation_completed']

                completion_data = completion_events[-1][0][1]  # Most recent
                assert completion_data['has_data'] == expected_has_data
                if 'result_size_bytes' in completion_data:
                    assert completion_data['result_size_bytes'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
