"""
Doc Store CLI Unit Tests

Comprehensive unit tests for doc_store CLI commands including:
- health checks and configuration
- document listing with pagination
- document creation
- document search
- document deletion
- document metadata updates
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


class TestDocStoreCLI:
    """Unit tests for Doc Store CLI commands"""

    def setup_method(self):
        """Setup test method"""
        self.cli = EcosystemCLI()
        self.fixtures = CLITestFixtures()
        self.mock_framework = CLIMockFramework()

    @pytest.mark.asyncio
    async def test_doc_store_health_success(self):
        """Test successful doc_store health check"""
        with self.mock_framework.mock_cli_environment():
            # Setup health response
            health_response = self.fixtures.get_mock_health_response("doc_store", "healthy")
            self.mock_framework.setup_service_responses("doc_store", "health", health_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("health")

                output = mock_stdout.getvalue()
                assert "💚 Doc Store Health:" in output
                assert "healthy" in output or "status" in output

    @pytest.mark.asyncio
    async def test_doc_store_health_failure(self):
        """Test doc_store health check failure"""
        with self.mock_framework.mock_cli_environment():
            # Setup error response
            self.mock_framework.setup_error_scenario("doc_store", "connection_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("health")

                output = mock_stdout.getvalue()
                assert "❌ Health check failed" in output

    @pytest.mark.asyncio
    async def test_doc_store_config_success(self):
        """Test successful doc_store config retrieval"""
        with self.mock_framework.mock_cli_environment():
            # Setup health response with config data
            health_response = self.fixtures.get_mock_health_response("doc_store", "healthy")
            health_response.json_data.update({
                "version": "1.2.3",
                "environment": "test",
                "uptime_seconds": 3600
            })
            self.mock_framework.setup_service_responses("doc_store", "health", health_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("config")

                output = mock_stdout.getvalue()
                assert "⚙️  Doc Store Configuration:" in output
                assert "1.2.3" in output
                assert "test" in output

    @pytest.mark.asyncio
    async def test_doc_store_list_success(self):
        """Test successful document listing"""
        with self.mock_framework.mock_cli_environment():
            # Setup list response
            list_response = self.fixtures.get_mock_doc_store_response("list")
            self.mock_framework.setup_service_responses("doc_store", "list", list_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("list", limit=10, offset=0)

                output = mock_stdout.getvalue()
                assert "📄 Document List" in output
                assert "Total documents:" in output
                assert "doc_001" in output
                assert "doc_002" in output

    @pytest.mark.asyncio
    async def test_doc_store_list_with_pagination(self):
        """Test document listing with custom pagination"""
        with self.mock_framework.mock_cli_environment():
            # Setup list response
            list_response = self.fixtures.get_mock_doc_store_response("list")
            self.mock_framework.setup_service_responses("doc_store", "list", list_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("list", limit=5, offset=10)

                output = mock_stdout.getvalue()
                assert "Limit: 5, Offset: 10" in output

    @pytest.mark.asyncio
    async def test_doc_store_list_failure(self):
        """Test document listing failure"""
        with self.mock_framework.mock_cli_environment():
            # Setup error response
            self.mock_framework.setup_error_scenario("doc_store", "connection_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("list")

                output = mock_stdout.getvalue()
                assert "❌ Failed to list documents" in output

    @pytest.mark.asyncio
    async def test_doc_store_create_success(self):
        """Test successful document creation"""
        with self.mock_framework.mock_cli_environment():
            # Setup create response
            create_response = self.fixtures.get_mock_doc_store_response("create")
            self.mock_framework.setup_service_responses("doc_store", "create", create_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("create",
                    title="Test Document",
                    content="Test content for CLI",
                    tags="test,cli,demo"
                )

                output = mock_stdout.getvalue()
                assert "✅ Document Created:" in output
                assert "Test Document" in output
                assert "doc_003" in output

    @pytest.mark.asyncio
    async def test_doc_store_create_minimal(self):
        """Test document creation with minimal parameters"""
        with self.mock_framework.mock_cli_environment():
            # Setup create response
            create_response = self.fixtures.get_mock_doc_store_response("create")
            self.mock_framework.setup_service_responses("doc_store", "create", create_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("create")

                output = mock_stdout.getvalue()
                assert "✅ Document Created:" in output
                assert "CLI Created Document" in output  # Default title

    @pytest.mark.asyncio
    async def test_doc_store_create_failure(self):
        """Test document creation failure"""
        with self.mock_framework.mock_cli_environment():
            # Setup error response
            self.mock_framework.setup_error_scenario("doc_store", "server_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("create", title="Test", content="Content")

                output = mock_stdout.getvalue()
                assert "❌ Failed to create document" in output

    @pytest.mark.asyncio
    async def test_doc_store_search_success(self):
        """Test successful document search"""
        with self.mock_framework.mock_cli_environment():
            # Setup search response
            search_response = self.fixtures.get_mock_doc_store_response("search")
            self.mock_framework.setup_service_responses("doc_store", "search", search_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("search", query="python code", limit=5)

                output = mock_stdout.getvalue()
                assert "🔍 Search Results for 'python code':" in output
                assert "Found" in output and "documents" in output
                assert "doc_001" in output

    @pytest.mark.asyncio
    async def test_doc_store_search_no_query(self):
        """Test search without query parameter"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            await self.cli.doc_store_command("search")

            output = mock_stdout.getvalue()
            assert "❌ Search query required" in output
            assert "--query" in output

    @pytest.mark.asyncio
    async def test_doc_store_search_failure(self):
        """Test document search failure"""
        with self.mock_framework.mock_cli_environment():
            # Setup error response
            self.mock_framework.setup_error_scenario("doc_store", "connection_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("search", query="test")

                output = mock_stdout.getvalue()
                assert "❌ Search failed" in output

    @pytest.mark.asyncio
    async def test_doc_store_delete_success(self):
        """Test successful document deletion"""
        with self.mock_framework.mock_cli_environment():
            # Mock urllib for DELETE request
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.__enter__.return_value = mock_response
                mock_urlopen.return_value = mock_response

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    await self.cli.doc_store_command("delete", id="test-doc-123")

                    output = mock_stdout.getvalue()
                    assert "✅ Document test-doc-123 deleted successfully" in output

    @pytest.mark.asyncio
    async def test_doc_store_delete_no_id(self):
        """Test delete without document ID"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            await self.cli.doc_store_command("delete")

            output = mock_stdout.getvalue()
            assert "❌ Document ID required" in output
            assert "--id" in output

    @pytest.mark.asyncio
    async def test_doc_store_delete_failure(self):
        """Test document deletion failure"""
        with self.mock_framework.mock_cli_environment():
            # Mock urllib for DELETE request failure
            with patch('urllib.request.urlopen', side_effect=Exception("Connection failed")):
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    await self.cli.doc_store_command("delete", id="test-doc-123")

                    output = mock_stdout.getvalue()
                    assert "❌ Failed to delete document" in output

    @pytest.mark.asyncio
    async def test_doc_store_update_success(self):
        """Test successful document metadata update"""
        with self.mock_framework.mock_cli_environment():
            # Mock the _make_request_with_method for PATCH/PUT
            with patch.object(self.cli.client, '_make_request_with_method', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {"success": True, "updated": True}

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    await self.cli.doc_store_command("update",
                        id="test-doc-123",
                        metadata="author:John,status:draft,priority:high"
                    )

                    output = mock_stdout.getvalue()
                    assert "✅ Document test-doc-123 metadata updated:" in output
                    assert "author" in output
                    assert "John" in output

    @pytest.mark.asyncio
    async def test_doc_store_update_no_id(self):
        """Test update without document ID"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            await self.cli.doc_store_command("update")

            output = mock_stdout.getvalue()
            assert "❌ Document ID required" in output
            assert "--id" in output

    @pytest.mark.asyncio
    async def test_doc_store_update_invalid_metadata(self):
        """Test update with invalid metadata format"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            await self.cli.doc_store_command("update",
                id="test-doc-123",
                metadata="invalid-format-no-colon"
            )

            output = mock_stdout.getvalue()
            assert "❌ Invalid metadata format" in output

    @pytest.mark.asyncio
    async def test_doc_store_update_endpoint_not_implemented(self):
        """Test update when endpoint is not implemented"""
        with self.mock_framework.mock_cli_environment():
            # Mock the _make_request_with_method to raise exception
            with patch.object(self.cli.client, '_make_request_with_method', new_callable=AsyncMock) as mock_request:
                mock_request.side_effect = Exception("Endpoint not found")

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    await self.cli.doc_store_command("update",
                        id="test-doc-123",
                        metadata="status:draft"
                    )

                    output = mock_stdout.getvalue()
                    assert "❌ Document metadata update endpoint not implemented yet" in output

    def test_doc_store_unknown_command(self):
        """Test unknown doc_store command"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            asyncio.run(self.cli.doc_store_command("unknown_command"))

            output = mock_stdout.getvalue()
            assert "❌ Unknown doc_store command: unknown_command" in output
            assert "Available commands:" in output
            assert "health, config, list, create, search, delete, update" in output

    @pytest.mark.asyncio
    async def test_doc_store_create_with_tags_parsing(self):
        """Test document creation with tags parsing"""
        with self.mock_framework.mock_cli_environment():
            # Setup create response
            create_response = self.fixtures.get_mock_doc_store_response("create")
            self.mock_framework.setup_service_responses("doc_store", "create", create_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("create",
                    title="Tagged Document",
                    content="Content with tags",
                    tags="important,urgent,review"
                )

                output = mock_stdout.getvalue()
                assert "✅ Document Created:" in output
                assert "Tagged Document" in output

    @pytest.mark.asyncio
    async def test_doc_store_search_with_limit(self):
        """Test search with custom limit"""
        with self.mock_framework.mock_cli_environment():
            # Setup search response
            search_response = self.fixtures.get_mock_doc_store_response("search")
            self.mock_framework.setup_service_responses("doc_store", "search", search_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("search", query="test query", limit=20)

                output = mock_stdout.getvalue()
                assert "🔍 Search Results for 'test query':" in output
                # The limit parameter is passed to the API call

    @pytest.mark.asyncio
    async def test_doc_store_comprehensive_workflow(self):
        """Test comprehensive doc_store workflow"""
        with self.mock_framework.mock_cli_environment():
            # Setup responses for complete workflow
            self.mock_framework.setup_service_responses("doc_store", "list")
            self.mock_framework.setup_service_responses("doc_store", "create")
            self.mock_framework.setup_service_responses("doc_store", "search")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Execute workflow
                await self.cli.doc_store_command("list")
                await self.cli.doc_store_command("create",
                    title="Workflow Test",
                    content="Testing complete workflow"
                )
                await self.cli.doc_store_command("search", query="workflow")

                output = mock_stdout.getvalue()

                # Verify all operations were attempted
                assert "📄 Document List" in output
                assert "✅ Document Created:" in output
                assert "🔍 Search Results" in output

    @pytest.mark.asyncio
    async def test_doc_store_error_handling_variations(self):
        """Test various error handling scenarios"""
        with self.mock_framework.mock_cli_environment():
            # Test different error types
            error_scenarios = ["connection_error", "server_error", "not_found"]

            for error_type in error_scenarios:
                self.mock_framework.setup_error_scenario("doc_store", error_type)

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    await self.cli.doc_store_command("list")

                    output = mock_stdout.getvalue()
                    assert "❌" in output  # Some form of error indication

    @pytest.mark.asyncio
    async def test_doc_store_large_content_handling(self):
        """Test handling of documents with large content"""
        with self.mock_framework.mock_cli_environment():
            # Create document with large content
            large_content = "x" * 10000  # 10KB of content
            large_doc = {
                "id": "large_doc_001",
                "content": large_content,
                "content_hash": "hash_large",
                "metadata": {"size": "large"},
                "created_at": "2024-01-20T10:00:00Z"
            }

            list_response = self.fixtures.get_mock_doc_store_response("list")
            list_response.json_data["items"] = [large_doc]
            self.mock_framework.setup_service_responses("doc_store", "list", list_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("list")

                output = mock_stdout.getvalue()
                assert "large_doc_001" in output
                # Content should be truncated in preview
                assert "..." in output


if __name__ == "__main__":
    # Run doc_store CLI tests
    test_instance = TestDocStoreCLI()
    test_instance.setup_method()

    print("🧪 Running Doc Store CLI Unit Tests...")
    print("=" * 50)

    # Test basic functionality
    try:
        asyncio.run(test_instance.test_doc_store_health_success())
        print("✅ Health check test: PASSED")
    except Exception as e:
        print(f"❌ Health check test: FAILED - {e}")

    try:
        asyncio.run(test_instance.test_doc_store_list_success())
        print("✅ List documents test: PASSED")
    except Exception as e:
        print(f"❌ List documents test: FAILED - {e}")

    try:
        asyncio.run(test_instance.test_doc_store_create_success())
        print("✅ Create document test: PASSED")
    except Exception as e:
        print(f"❌ Create document test: FAILED - {e}")

    print("\n🏁 Doc Store CLI Unit Tests completed!")
