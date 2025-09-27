"""Unit tests for github-mcp modules."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json


class TestConfig:
    """Test cases for config module."""

    @patch('services.github_mcp.modules.config.os.getenv')
    def test_config_loading(self, mock_getenv):
        """Test configuration loading from environment."""
        from services.github_mcp.modules.config import Config

        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            'GITHUB_TOKEN': 'test-token',
            'GITHUB_API_BASE_URL': 'https://api.github.com',
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': '6379',
            'LOG_LEVEL': 'INFO'
        }.get(key, default)

        config = Config()

        assert config.github_token == 'test-token'
        assert config.github_api_base_url == 'https://api.github.com'
        assert config.redis_host == 'localhost'
        assert config.redis_port == 6379
        assert config.log_level == 'INFO'

    @patch('services.github_mcp.modules.config.os.getenv')
    def test_config_defaults(self, mock_getenv):
        """Test configuration defaults when environment variables are not set."""
        from services.github_mcp.modules.config import Config

        mock_getenv.return_value = None

        config = Config()

        assert config.github_token is None
        assert config.github_api_base_url == 'https://api.github.com'
        assert config.redis_host == 'redis'
        assert config.redis_port == 6379
        assert config.log_level == 'INFO'


class TestEventSystem:
    """Test cases for event system module."""

    def test_event_creation(self):
        """Test event creation and properties."""
        from services.github_mcp.modules.event_system import Event

        event = Event(
            event_type='tool_registered',
            data={'tool_name': 'test_tool', 'capabilities': ['read', 'write']},
            source='test_source'
        )

        assert event.event_type == 'tool_registered'
        assert event.data['tool_name'] == 'test_tool'
        assert event.source == 'test_source'
        assert event.timestamp is not None
        assert event.event_id is not None

    def test_event_system_registration(self):
        """Test event system handler registration."""
        from services.github_mcp.modules.event_system import EventSystem

        system = EventSystem()
        handler = Mock()

        # Register handler
        system.register_handler('test_event', handler)

        # Emit event
        event = Mock()
        event.event_type = 'test_event'
        system.emit_event(event)

        # Verify handler was called
        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_async_event_handling(self):
        """Test asynchronous event handling."""
        from services.github_mcp.modules.event_system import EventSystem

        system = EventSystem()
        handler = AsyncMock()

        system.register_handler('async_event', handler)

        event = Mock()
        event.event_type = 'async_event'

        await system.emit_event_async(event)

        handler.assert_called_once_with(event)

    def test_event_filtering(self):
        """Test event filtering capabilities."""
        from services.github_mcp.modules.event_system import EventSystem

        system = EventSystem()
        handler = Mock()

        # Register handler with filter
        system.register_handler('filtered_event', handler, event_filter=lambda e: e.data.get('priority') == 'high')

        # Emit events
        high_priority_event = Mock()
        high_priority_event.event_type = 'filtered_event'
        high_priority_event.data = {'priority': 'high'}

        low_priority_event = Mock()
        low_priority_event.event_type = 'filtered_event'
        low_priority_event.data = {'priority': 'low'}

        system.emit_event(high_priority_event)
        system.emit_event(low_priority_event)

        # Handler should only be called for high priority event
        assert handler.call_count == 1
        handler.assert_called_once_with(high_priority_event)


class TestToolRegistry:
    """Test cases for tool registry module."""

    def test_tool_registration(self):
        """Test tool registration and retrieval."""
        from services.github_mcp.modules.tool_registry import ToolRegistry

        registry = ToolRegistry()

        tool_info = {
            'name': 'github_repo_analyzer',
            'description': 'Analyzes GitHub repository structure',
            'capabilities': ['read_repository', 'analyze_code'],
            'endpoint': '/api/tools/github_repo_analyzer',
            'version': '1.0.0'
        }

        # Register tool
        registry.register_tool(tool_info)

        # Retrieve tool
        retrieved = registry.get_tool('github_repo_analyzer')
        assert retrieved == tool_info

        # List all tools
        all_tools = registry.list_tools()
        assert 'github_repo_analyzer' in all_tools

    def test_tool_capability_search(self):
        """Test searching tools by capabilities."""
        from services.github_mcp.modules.tool_registry import ToolRegistry

        registry = ToolRegistry()

        # Register multiple tools
        tools = [
            {
                'name': 'code_analyzer',
                'capabilities': ['analyze_code', 'read_files'],
                'endpoint': '/api/tools/code_analyzer'
            },
            {
                'name': 'pr_manager',
                'capabilities': ['manage_prs', 'review_code'],
                'endpoint': '/api/tools/pr_manager'
            },
            {
                'name': 'issue_tracker',
                'capabilities': ['track_issues', 'manage_labels'],
                'endpoint': '/api/tools/issue_tracker'
            }
        ]

        for tool in tools:
            registry.register_tool(tool)

        # Search by capability
        code_tools = registry.find_tools_by_capability('analyze_code')
        assert len(code_tools) == 1
        assert code_tools[0]['name'] == 'code_analyzer'

        # Search by multiple capabilities
        multi_cap_tools = registry.find_tools_by_capability(['read_files', 'review_code'])
        assert len(multi_cap_tools) == 2

    def test_tool_validation(self):
        """Test tool registration validation."""
        from services.github_mcp.modules.tool_registry import ToolRegistry

        registry = ToolRegistry()

        # Valid tool
        valid_tool = {
            'name': 'valid_tool',
            'description': 'A valid tool',
            'capabilities': ['test'],
            'endpoint': '/api/tools/valid'
        }
        registry.register_tool(valid_tool)

        # Invalid tool (missing required fields)
        invalid_tool = {
            'name': 'invalid_tool',
            'capabilities': ['test']
            # Missing description and endpoint
        }

        with pytest.raises(ValueError):
            registry.register_tool(invalid_tool)

    def test_tool_metadata_management(self):
        """Test tool metadata management."""
        from services.github_mcp.modules.tool_registry import ToolRegistry

        registry = ToolRegistry()

        tool = {
            'name': 'metadata_tool',
            'description': 'Tool with metadata',
            'capabilities': ['test'],
            'endpoint': '/api/tools/metadata',
            'metadata': {
                'author': 'test-team',
                'version': '2.0.0',
                'tags': ['experimental', 'beta']
            }
        }

        registry.register_tool(tool)

        # Update metadata
        registry.update_tool_metadata('metadata_tool', {'status': 'stable', 'last_updated': '2023-12-01'})

        updated_tool = registry.get_tool('metadata_tool')
        assert updated_tool['metadata']['status'] == 'stable'
        assert updated_tool['metadata']['last_updated'] == '2023-12-01'


class TestMockImplementations:
    """Test cases for mock implementations module."""

    @pytest.mark.asyncio
    async def test_mock_github_client(self):
        """Test mock GitHub client implementation."""
        from services.github_mcp.modules.mock_implementations import MockGitHubClient

        client = MockGitHubClient()

        # Test repository retrieval
        repo = await client.get_repository('test-owner', 'test-repo')
        assert repo['name'] == 'test-repo'
        assert repo['owner'] == 'test-owner'
        assert 'stars' in repo

        # Test issue retrieval
        issues = await client.get_issues('test-owner', 'test-repo')
        assert isinstance(issues, list)
        assert len(issues) > 0

        # Test pull request retrieval
        prs = await client.get_pull_requests('test-owner', 'test-repo')
        assert isinstance(prs, list)

    @pytest.mark.asyncio
    async def test_mock_redis_client(self):
        """Test mock Redis client implementation."""
        from services.github_mcp.modules.mock_implementations import MockRedisClient

        client = MockRedisClient()

        # Test basic operations
        await client.set('test_key', 'test_value')
        value = await client.get('test_key')
        assert value == 'test_value'

        # Test JSON operations
        test_data = {'name': 'test', 'value': 123}
        await client.set_json('json_key', test_data)
        retrieved_data = await client.get_json('json_key')
        assert retrieved_data == test_data

    def test_mock_rate_limiter(self):
        """Test mock rate limiter implementation."""
        from services.github_mcp.modules.mock_implementations import MockRateLimiter

        limiter = MockRateLimiter()

        # Test rate limiting
        assert limiter.allow_request('test_user') is True

        # Test limit enforcement (mock always allows)
        for _ in range(100):
            assert limiter.allow_request('test_user') is True


class TestRealImplementations:
    """Test cases for real implementations module."""

    @patch('services.github_mcp.modules.real_implementations.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_real_github_client(self, mock_client):
        """Test real GitHub client implementation."""
        from services.github_mcp.modules.real_implementations import RealGitHubClient

        # Mock HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'test-repo',
            'owner': {'login': 'test-owner'},
            'stargazers_count': 42
        }

        mock_client_instance = Mock()
        mock_client_instance.get.return_value.__aenter__ = Mock(return_value=mock_response)
        mock_client.return_value.__aenter__ = Mock(return_value=mock_client_instance)

        client = RealGitHubClient(token='test-token')

        repo = await client.get_repository('test-owner', 'test-repo')
        assert repo['name'] == 'test-repo'
        assert repo['stargazers_count'] == 42

    @patch('services.github_mcp.modules.real_implementations.redis.Redis')
    def test_real_redis_client(self, mock_redis):
        """Test real Redis client implementation."""
        from services.github_mcp.modules.real_implementations import RealRedisClient

        # Mock Redis client
        mock_instance = Mock()
        mock_redis.return_value = mock_instance

        client = RealRedisClient()

        # Test operations
        mock_instance.set.return_value = True
        mock_instance.get.return_value = b'test_value'

        result = client.set_sync('test_key', 'test_value')
        assert result is True

        value = client.get_sync('test_key')
        assert value == 'test_value'

    def test_real_rate_limiter(self):
        """Test real rate limiter implementation."""
        from services.github_mcp.modules.real_implementations import RealRateLimiter

        limiter = RealRateLimiter(requests_per_hour=100)

        # Test rate limiting logic
        assert limiter.allow_request('user1') is True

        # Test with different users
        assert limiter.allow_request('user2') is True

        # Test rate limit exceeded (would depend on timing in real implementation)
        # This is a basic test of the interface
        assert hasattr(limiter, 'allow_request')


class TestIntegration:
    """Integration tests for module interactions."""

    def test_config_with_event_system(self):
        """Test configuration integration with event system."""
        from services.github_mcp.modules.config import Config
        from services.github_mcp.modules.event_system import EventSystem

        # Test that config can be used with event system
        config = Config()
        event_system = EventSystem()

        # Both should initialize without errors
        assert config is not None
        assert event_system is not None

    def test_tool_registry_with_event_system(self):
        """Test tool registry integration with event system."""
        from services.github_mcp.modules.tool_registry import ToolRegistry
        from services.github_mcp.modules.event_system import EventSystem

        registry = ToolRegistry()
        event_system = EventSystem()

        # Register a tool and emit an event
        tool = {
            'name': 'integration_test_tool',
            'description': 'Tool for integration testing',
            'capabilities': ['test'],
            'endpoint': '/api/test'
        }

        registry.register_tool(tool)

        # Emit tool registration event
        event = Mock()
        event.event_type = 'tool_registered'
        event.data = {'tool_name': 'integration_test_tool'}

        # Should not raise errors
        event_system.emit_event(event)

        # Verify tool was registered
        retrieved = registry.get_tool('integration_test_tool')
        assert retrieved == tool

    @pytest.mark.asyncio
    async def test_full_workflow_simulation(self):
        """Test a simulated full workflow using multiple modules."""
        from services.github_mcp.modules.mock_implementations import MockGitHubClient, MockRedisClient
        from services.github_mcp.modules.tool_registry import ToolRegistry
        from services.github_mcp.modules.event_system import EventSystem

        # Initialize components
        github_client = MockGitHubClient()
        redis_client = MockRedisClient()
        registry = ToolRegistry()
        event_system = EventSystem()

        # Simulate workflow: register tool, fetch data, cache result, emit event
        tool = {
            'name': 'workflow_test_tool',
            'description': 'Tool for workflow testing',
            'capabilities': ['github_integration'],
            'endpoint': '/api/workflow'
        }

        # Register tool
        registry.register_tool(tool)

        # Simulate data fetching and caching
        repo_data = await github_client.get_repository('test', 'repo')
        await redis_client.set_json('repo:test/repo', repo_data)

        # Emit completion event
        event = Mock()
        event.event_type = 'workflow_completed'
        event.data = {'tool': 'workflow_test_tool', 'status': 'success'}
        event_system.emit_event(event)

        # Verify workflow completion
        cached_data = await redis_client.get_json('repo:test/repo')
        assert cached_data == repo_data

        registered_tool = registry.get_tool('workflow_test_tool')
        assert registered_tool == tool
