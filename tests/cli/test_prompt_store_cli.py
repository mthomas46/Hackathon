"""
Prompt Store CLI Unit Tests

Comprehensive unit tests for prompt_store CLI commands including:
- health checks and configuration
- prompt listing with filtering and pagination
- prompt creation with all parameters
- prompt retrieval by ID
- prompt search with multiple criteria
- prompt updates with various fields
- prompt deletion
- category listing
"""

import sys
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from io import StringIO
import json

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from ecosystem_cli_executable import EcosystemCLI
from .mock_framework import CLIMockFramework, create_successful_service_test
from .test_fixtures import CLITestFixtures


class TestPromptStoreCLI:
    """Unit tests for Prompt Store CLI commands"""

    def setup_method(self):
        """Setup test method"""
        self.cli = EcosystemCLI()
        self.fixtures = CLITestFixtures()
        self.mock_framework = CLIMockFramework()

    @pytest.mark.asyncio
    async def test_prompt_store_health_success(self):
        """Test successful prompt_store health check"""
        with self.mock_framework.mock_cli_environment():
            # Setup health response
            health_response = self.fixtures.get_mock_health_response("prompt_store", "healthy")
            self.mock_framework.setup_service_responses("prompt_store", "health", health_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("health")

                output = mock_stdout.getvalue()
                assert "💚 Prompt Store Health:" in output
                assert "healthy" in output or "status" in output

    @pytest.mark.asyncio
    async def test_prompt_store_health_failure(self):
        """Test prompt_store health check failure"""
        with self.mock_framework.mock_cli_environment():
            # Setup error response
            self.mock_framework.setup_error_scenario("prompt_store", "connection_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("health")

                output = mock_stdout.getvalue()
                assert "❌ Health check failed" in output

    @pytest.mark.asyncio
    async def test_prompt_store_config_success(self):
        """Test successful prompt_store config retrieval"""
        with self.mock_framework.mock_cli_environment():
            # Setup health response with config data
            health_response = self.fixtures.get_mock_health_response("prompt_store", "healthy")
            health_response.json_data.update({
                "version": "1.5.0",
                "environment": "production",
                "uptime_seconds": 86400
            })
            self.mock_framework.setup_service_responses("prompt_store", "health", health_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("config")

                output = mock_stdout.getvalue()
                assert "⚙️  Prompt Store Configuration:" in output
                assert "1.5.0" in output
                assert "production" in output

    @pytest.mark.asyncio
    async def test_prompt_store_list_success(self):
        """Test successful prompt listing"""
        with self.mock_framework.mock_cli_environment():
            # Setup list response
            list_response = self.fixtures.get_mock_prompt_store_response("list")
            self.mock_framework.setup_service_responses("prompt_store", "list", list_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("list", limit=10, offset=0)

                output = mock_stdout.getvalue()
                assert "📋 Prompt List" in output
                assert "Total prompts:" in output
                assert "prompt_001" in output
                assert "Code Review Prompt" in output

    @pytest.mark.asyncio
    async def test_prompt_store_list_with_filters(self):
        """Test prompt listing with category and author filters"""
        with self.mock_framework.mock_cli_environment():
            # Setup list response
            list_response = self.fixtures.get_mock_prompt_store_response("list")
            self.mock_framework.setup_service_responses("prompt_store", "list", list_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("list",
                    limit=5,
                    offset=0,
                    category="development",
                    author="developer@example.com"
                )

                output = mock_stdout.getvalue()
                assert "Limit: 5, Offset: 0" in output

    @pytest.mark.asyncio
    async def test_prompt_store_list_failure(self):
        """Test prompt listing failure"""
        with self.mock_framework.mock_cli_environment():
            # Setup error response
            self.mock_framework.setup_error_scenario("prompt_store", "connection_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("list")

                output = mock_stdout.getvalue()
                assert "❌ Failed to list prompts" in output

    @pytest.mark.asyncio
    async def test_prompt_store_create_success(self):
        """Test successful prompt creation"""
        with self.mock_framework.mock_cli_environment():
            # Setup create response
            create_response = self.fixtures.get_mock_prompt_store_response("create")
            self.mock_framework.setup_service_responses("prompt_store", "create", create_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("create",
                    name="Test Analysis Prompt",
                    content="Analyze this code for potential issues",
                    category="development",
                    author="test-user",
                    tags="code,analysis,testing",
                    description="A test prompt for code analysis"
                )

                output = mock_stdout.getvalue()
                assert "✅ Prompt Created:" in output
                assert "Test Analysis Prompt" in output
                assert "development" in output
                assert "test-user" in output
                assert "code,analysis,testing" in output

    @pytest.mark.asyncio
    async def test_prompt_store_create_minimal(self):
        """Test prompt creation with minimal parameters"""
        with self.mock_framework.mock_cli_environment():
            # Setup create response
            create_response = self.fixtures.get_mock_prompt_store_response("create")
            self.mock_framework.setup_service_responses("prompt_store", "create", create_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("create")

                output = mock_stdout.getvalue()
                assert "✅ Prompt Created:" in output
                assert "CLI Created Prompt" in output  # Default name
                assert "general" in output  # Default category

    @pytest.mark.asyncio
    async def test_prompt_store_create_failure(self):
        """Test prompt creation failure"""
        with self.mock_framework.mock_cli_environment():
            # Setup error response
            self.mock_framework.setup_error_scenario("prompt_store", "server_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("create", name="Test", content="Content")

                output = mock_stdout.getvalue()
                assert "❌ Failed to create prompt" in output

    @pytest.mark.asyncio
    async def test_prompt_store_get_success(self):
        """Test successful prompt retrieval by ID"""
        with self.mock_framework.mock_cli_environment():
            # Mock individual prompt response
            prompt_data = {
                "id": "prompt_123",
                "name": "Specific Analysis Prompt",
                "content": "Analyze this specific code pattern",
                "category": "analysis",
                "author": "analyst@example.com",
                "tags": ["analysis", "patterns"],
                "created_at": "2024-01-20T10:00:00Z"
            }

            from .test_fixtures import MockServiceResponse
            get_response = MockServiceResponse(
                status_code=200,
                json_data=prompt_data
            )
            self.mock_framework.http_client.add_response("prompt_store_get", get_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("get", id="prompt_123")

                output = mock_stdout.getvalue()
                assert "📋 Prompt Details:" in output
                assert "Specific Analysis Prompt" in output
                assert "analysis" in output

    @pytest.mark.asyncio
    async def test_prompt_store_get_no_id(self):
        """Test get command without prompt ID"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            await self.cli.prompt_store_command("get")

            output = mock_stdout.getvalue()
            assert "❌ Prompt ID required" in output
            assert "--id" in output

    @pytest.mark.asyncio
    async def test_prompt_store_get_failure(self):
        """Test prompt get failure"""
        with self.mock_framework.mock_cli_environment():
            # Setup error response
            self.mock_framework.setup_error_scenario("prompt_store", "not_found")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("get", id="nonexistent")

                output = mock_stdout.getvalue()
                assert "❌ Failed to get prompt" in output

    @pytest.mark.asyncio
    async def test_prompt_store_search_success(self):
        """Test successful prompt search"""
        with self.mock_framework.mock_cli_environment():
            # Setup search response
            search_response = self.fixtures.get_mock_prompt_store_response("search")
            self.mock_framework.setup_service_responses("prompt_store", "search", search_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("search",
                    query="analysis",
                    category="development",
                    limit=5
                )

                output = mock_stdout.getvalue()
                assert "🔍 Search Results:" in output
                assert "Found" in output and "prompts" in output

    @pytest.mark.asyncio
    async def test_prompt_store_search_no_criteria(self):
        """Test search without any search criteria"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            await self.cli.prompt_store_command("search")

            output = mock_stdout.getvalue()
            assert "❌ Search requires" in output
            assert "--query, --category, or --author" in output

    @pytest.mark.asyncio
    async def test_prompt_store_search_by_category_only(self):
        """Test search by category only"""
        with self.mock_framework.mock_cli_environment():
            # Setup search response
            search_response = self.fixtures.get_mock_prompt_store_response("search")
            self.mock_framework.setup_service_responses("prompt_store", "search", search_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("search", category="analysis")

                output = mock_stdout.getvalue()
                assert "🔍 Search Results:" in output

    @pytest.mark.asyncio
    async def test_prompt_store_search_failure(self):
        """Test prompt search failure"""
        with self.mock_framework.mock_cli_environment():
            # Setup error response
            self.mock_framework.setup_error_scenario("prompt_store", "connection_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("search", query="test")

                output = mock_stdout.getvalue()
                assert "❌ Search failed" in output

    @pytest.mark.asyncio
    async def test_prompt_store_update_success(self):
        """Test successful prompt update"""
        with self.mock_framework.mock_cli_environment():
            # Setup update response
            update_response = self.fixtures.get_mock_prompt_store_response("update")
            self.mock_framework.setup_service_responses("prompt_store", "update", update_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("update",
                    id="prompt_001",
                    name="Updated Prompt Name",
                    category="updated_category",
                    description="Updated description",
                    tags="new_tag,another_tag"
                )

                output = mock_stdout.getvalue()
                assert "✅ Prompt prompt_001 updated:" in output
                assert "Updated Prompt Name" in output
                assert "updated_category" in output

    @pytest.mark.asyncio
    async def test_prompt_store_update_no_id(self):
        """Test update without prompt ID"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            await self.cli.prompt_store_command("update")

            output = mock_stdout.getvalue()
            assert "❌ Prompt ID required" in output
            assert "--id" in output

    @pytest.mark.asyncio
    async def test_prompt_store_update_no_fields(self):
        """Test update without any fields to update"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            await self.cli.prompt_store_command("update", id="prompt_001")

            output = mock_stdout.getvalue()
            assert "❌ At least one field to update required" in output
            assert "--name, --content, --category, --description, --tags" in output

    @pytest.mark.asyncio
    async def test_prompt_store_update_partial_fields(self):
        """Test update with only some fields"""
        with self.mock_framework.mock_cli_environment():
            # Setup update response
            update_response = self.fixtures.get_mock_prompt_store_response("update")
            self.mock_framework.setup_service_responses("prompt_store", "update", update_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("update",
                    id="prompt_001",
                    name="New Name Only"
                )

                output = mock_stdout.getvalue()
                assert "✅ Prompt prompt_001 updated:" in output
                assert "New Name Only" in output

    @pytest.mark.asyncio
    async def test_prompt_store_update_failure(self):
        """Test prompt update failure"""
        with self.mock_framework.mock_cli_environment():
            # Setup error response
            self.mock_framework.setup_error_scenario("prompt_store", "server_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("update",
                    id="prompt_001",
                    name="Test Update"
                )

                output = mock_stdout.getvalue()
                assert "❌ Failed to update prompt" in output

    @pytest.mark.asyncio
    async def test_prompt_store_delete_success(self):
        """Test successful prompt deletion"""
        with self.mock_framework.mock_cli_environment():
            # Mock urllib for DELETE request
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.__enter__.return_value = mock_response
                mock_urlopen.return_value = mock_response

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    await self.cli.prompt_store_command("delete", id="prompt_123")

                    output = mock_stdout.getvalue()
                    assert "✅ Prompt prompt_123 deleted successfully" in output

    @pytest.mark.asyncio
    async def test_prompt_store_delete_no_id(self):
        """Test delete without prompt ID"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            await self.cli.prompt_store_command("delete")

            output = mock_stdout.getvalue()
            assert "❌ Prompt ID required" in output
            assert "--id" in output

    @pytest.mark.asyncio
    async def test_prompt_store_delete_failure(self):
        """Test prompt deletion failure"""
        with self.mock_framework.mock_cli_environment():
            # Mock urllib for DELETE request failure
            with patch('urllib.request.urlopen', side_effect=Exception("Connection failed")):
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    await self.cli.prompt_store_command("delete", id="prompt_123")

                    output = mock_stdout.getvalue()
                    assert "❌ Failed to delete prompt" in output

    @pytest.mark.asyncio
    async def test_prompt_store_categories_success(self):
        """Test successful categories listing"""
        with self.mock_framework.mock_cli_environment():
            # Mock categories response
            categories_data = ["development", "analysis", "general", "testing", "documentation"]
            from .test_fixtures import MockServiceResponse
            categories_response = MockServiceResponse(
                status_code=200,
                json_data=categories_data
            )
            self.mock_framework.http_client.add_response("prompt_store_categories", categories_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("categories")

                output = mock_stdout.getvalue()
                assert "📂 Available Categories:" in output
                assert "development" in output
                assert "analysis" in output

    @pytest.mark.asyncio
    async def test_prompt_store_categories_failure(self):
        """Test categories listing failure"""
        with self.mock_framework.mock_cli_environment():
            # Setup error response
            self.mock_framework.setup_error_scenario("prompt_store", "connection_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("categories")

                output = mock_stdout.getvalue()
                assert "❌ Failed to get categories" in output

    def test_prompt_store_unknown_command(self):
        """Test unknown prompt_store command"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            asyncio.run(self.cli.prompt_store_command("unknown_command"))

            output = mock_stdout.getvalue()
            assert "❌ Unknown prompt_store command: unknown_command" in output
            assert "Available commands:" in output
            assert "health, config, list, create, get, search, update, delete, categories" in output

    @pytest.mark.asyncio
    async def test_prompt_store_comprehensive_workflow(self):
        """Test comprehensive prompt_store workflow"""
        with self.mock_framework.mock_cli_environment():
            # Setup responses for complete workflow
            self.mock_framework.setup_service_responses("prompt_store", "list")
            self.mock_framework.setup_service_responses("prompt_store", "create")
            self.mock_framework.setup_service_responses("prompt_store", "search")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Execute workflow
                await self.cli.prompt_store_command("list")
                await self.cli.prompt_store_command("create",
                    name="Workflow Test Prompt",
                    content="Testing complete workflow"
                )
                await self.cli.prompt_store_command("search", query="workflow")

                output = mock_stdout.getvalue()

                # Verify all operations were attempted
                assert "📋 Prompt List" in output
                assert "✅ Prompt Created:" in output
                assert "🔍 Search Results" in output

    @pytest.mark.asyncio
    async def test_prompt_store_complex_search(self):
        """Test complex search with multiple criteria"""
        with self.mock_framework.mock_cli_environment():
            # Setup search response
            search_response = self.fixtures.get_mock_prompt_store_response("search")
            self.mock_framework.setup_service_responses("prompt_store", "search", search_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("search",
                    query="complex search",
                    category="analysis",
                    author="analyst@example.com",
                    limit=20
                )

                output = mock_stdout.getvalue()
                assert "🔍 Search Results:" in output

    @pytest.mark.asyncio
    async def test_prompt_store_bulk_operations(self):
        """Test multiple operations in sequence"""
        with self.mock_framework.mock_cli_environment():
            # Setup multiple responses
            responses = ["list", "create", "get", "update", "search"]
            for operation in responses:
                self.mock_framework.setup_service_responses("prompt_store", operation)

            operations_executed = []

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Execute multiple operations
                await self.cli.prompt_store_command("list", limit=5)
                operations_executed.append("list")

                await self.cli.prompt_store_command("create",
                    name="Bulk Test",
                    content="Testing bulk operations"
                )
                operations_executed.append("create")

                # Mock get operation
                prompt_data = {"id": "bulk_test", "name": "Bulk Test"}
                from .test_fixtures import MockServiceResponse
                get_response = MockServiceResponse(status_code=200, json_data=prompt_data)
                self.mock_framework.http_client.add_response("prompt_store_get", get_response)

                await self.cli.prompt_store_command("get", id="bulk_test")
                operations_executed.append("get")

                output = mock_stdout.getvalue()

                # Verify operations were executed
                assert len(operations_executed) == 3
                assert "📋 Prompt List" in output
                assert "✅ Prompt Created:" in output
                assert "📋 Prompt Details:" in output

    @pytest.mark.asyncio
    async def test_prompt_store_error_handling_variations(self):
        """Test various error handling scenarios"""
        with self.mock_framework.mock_cli_environment():
            # Test different error types
            error_scenarios = ["connection_error", "server_error", "not_found"]

            for error_type in error_scenarios:
                self.mock_framework.setup_error_scenario("prompt_store", error_type)

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    await self.cli.prompt_store_command("list")

                    output = mock_stdout.getvalue()
                    # Should handle error gracefully
                    assert "❌" in output

    @pytest.mark.asyncio
    async def test_prompt_store_empty_results(self):
        """Test handling of empty results"""
        with self.mock_framework.mock_cli_environment():
            # Setup empty list response
            empty_response = self.fixtures.get_mock_prompt_store_response("list")
            empty_response.json_data["items"] = []
            empty_response.json_data["total"] = 0
            self.mock_framework.setup_service_responses("prompt_store", "list", empty_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("list")

                output = mock_stdout.getvalue()
                assert "Total prompts: 0" in output

    @pytest.mark.asyncio
    async def test_prompt_store_large_content_handling(self):
        """Test handling of prompts with large content"""
        with self.mock_framework.mock_cli_environment():
            # Create prompt with large content
            large_content = "x" * 5000  # 5KB of content
            large_prompt = {
                "id": "large_prompt_001",
                "name": "Large Content Prompt",
                "content": large_content,
                "category": "testing",
                "author": "test@example.com",
                "tags": ["large", "test"],
                "created_at": "2024-01-20T10:00:00Z"
            }

            from .test_fixtures import MockServiceResponse
            list_response = MockServiceResponse(
                status_code=200,
                json_data={"items": [large_prompt], "total": 1, "has_more": False}
            )
            self.mock_framework.http_client.add_response("prompt_store_list", list_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("list")

                output = mock_stdout.getvalue()
                assert "large_prompt_001" in output
                assert "Large Content Prompt" in output


if __name__ == "__main__":
    # Run prompt_store CLI tests
    test_instance = TestPromptStoreCLI()
    test_instance.setup_method()

    print("🧪 Running Prompt Store CLI Unit Tests...")
    print("=" * 50)

    # Test basic functionality
    try:
        asyncio.run(test_instance.test_prompt_store_health_success())
        print("✅ Health check test: PASSED")
    except Exception as e:
        print(f"❌ Health check test: FAILED - {e}")

    try:
        asyncio.run(test_instance.test_prompt_store_list_success())
        print("✅ List prompts test: PASSED")
    except Exception as e:
        print(f"❌ List prompts test: FAILED - {e}")

    try:
        asyncio.run(test_instance.test_prompt_store_create_success())
        print("✅ Create prompt test: PASSED")
    except Exception as e:
        print(f"❌ Create prompt test: FAILED - {e}")

    try:
        asyncio.run(test_instance.test_prompt_store_search_success())
        print("✅ Search prompts test: PASSED")
    except Exception as e:
        print(f"❌ Search prompts test: FAILED - {e}")

    print("\n🏁 Prompt Store CLI Unit Tests completed!")
