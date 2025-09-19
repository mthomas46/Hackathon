"""
CLI Integration Tests

End-to-end integration tests for CLI functionality including:
- Full command execution workflows
- Service-to-service communication
- Container management workflows
- Error scenarios and recovery
- Performance testing
"""

import asyncio
import sys
import time
import tempfile
import os
import subprocess
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from io import StringIO
import json
from concurrent.futures import ThreadPoolExecutor

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from ecosystem_cli_executable import EcosystemCLI, main
from .mock_framework import CLIMockFramework, create_integration_test, create_performance_test
from .test_fixtures import CLITestFixtures


class TestCLIIntegration:
    """Integration tests for CLI functionality"""

    def setup_method(self):
        """Setup test method"""
        self.cli = EcosystemCLI()
        self.fixtures = CLITestFixtures()
        self.mock_framework = CLIMockFramework()

    async def test_full_health_check_workflow(self):
        """Test complete health check workflow"""
        with self.mock_framework.mock_cli_environment():
            # Setup all services with health responses
            services = ["analysis-service", "orchestrator", "doc_store", "llm-gateway"]
            for service in services:
                self.mock_framework.setup_service_responses(service, "health")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.health_check_all()

                output = mock_stdout.getvalue()

                # Verify output contains expected elements
                assert "ECOSYSTEM HEALTH STATUS" in output
                for service in services:
                    assert service in output

                # Verify HTTP requests were made
                summary = self.mock_framework.get_test_summary()
                assert summary["http_requests"] >= len(services)

    
    async def test_document_lifecycle_workflow(self):
        """Test complete document lifecycle through CLI"""
        with self.mock_framework.mock_cli_environment():
            # Setup doc_store responses for full lifecycle
            operations = ["list", "create", "search", "delete"]
            for operation in operations:
                self.mock_framework.setup_service_responses("doc_store", operation)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Execute document operations
                await self.cli.doc_store_command("list")
                await self.cli.doc_store_command("create", content="Test document", metadata={"test": True})
                await self.cli.doc_store_command("search", query="test")
                await self.cli.doc_store_command("delete", document_id="doc_001")

                output = mock_stdout.getvalue()

                # Verify operations were attempted
                assert "documents" in output.lower() or "📄" in output

    
    async def test_workflow_execution_integration(self):
        """Test workflow execution integration"""
        with self.mock_framework.mock_cli_environment():
            # Setup orchestrator workflow responses
            self.mock_framework.setup_service_responses("orchestrator", "list")
            self.mock_framework.setup_service_responses("orchestrator", "execute")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.orchestrator_command("workflows")
                await self.cli.orchestrator_command("execute", workflow_id="wf_001")

                output = mock_stdout.getvalue()

                # Verify workflow operations
                assert "🤝" in output or "workflows" in output.lower()

    
    async def test_container_management_workflow(self):
        """Test container management workflow"""
        with self.mock_framework.mock_cli_environment():
            service_name = "doc_store"

            # Setup container responses
            operations = ["list", "restart", "logs", "stats"]
            for operation in operations:
                self.mock_framework.setup_container_responses(service_name, operation)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Execute container operations
                await self.cli.list_containers()
                await self.cli.restart_container(service_name)
                await self.cli.show_container_logs(service_name)
                await self.cli.show_container_stats()

                output = mock_stdout.getvalue()

                # Verify container operations
                assert "🐳" in output  # Container status
                assert "📊" in output  # Container stats
                assert "🔄" in output  # Restart operation
                assert "📜" in output  # Logs

    
    async def test_cross_service_workflow(self):
        """Test workflow spanning multiple services"""
        with self.mock_framework.mock_cli_environment():
            # Setup multi-service workflow
            workflow_services = ["doc_store", "analysis-service", "summarizer-hub"]

            for service in workflow_services:
                self.mock_framework.setup_service_responses(service, "health")

            # Execute cross-service operations
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Health check all services
                await self.cli.health_check_all()

                # Execute document operations
                await self.cli.doc_store_command("list")

                output = mock_stdout.getvalue()

                # Verify cross-service communication
                for service in workflow_services:
                    assert service in output or service.replace("-", "_") in output

    
    async def test_error_handling_integration(self):
        """Test error handling in integration scenarios"""
        with self.mock_framework.mock_cli_environment():
            # Setup mixed success/failure scenario
            self.mock_framework.setup_service_responses("doc_store", "health")
            self.mock_framework.setup_error_scenario("llm-gateway", "connection_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.health_check_all()

                output = mock_stdout.getvalue()

                # Should show both success and failure
                assert ("✅" in output or "doc_store" in output)
                assert ("❌" in output or "FAILED" in output)

    
    async def test_performance_integration(self):
        """Test performance in integration scenarios"""
        with self.mock_framework.mock_cli_environment():
            # Setup performance test scenario
            self.mock_framework.setup_performance_scenario("doc_store", delay=0.5)
            self.mock_framework.setup_performance_scenario("analysis-service", delay=0.3)

            start_time = time.time()

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.health_check_all()

            end_time = time.time()

            # Should complete within reasonable time
            duration = end_time - start_time
            assert duration < 3.0  # Allow buffer for processing

    
    async def test_concurrent_service_calls(self):
        """Test concurrent service calls"""
        with self.mock_framework.mock_cli_environment():
            # Setup concurrent scenario
            self.mock_framework.setup_concurrent_scenario("doc_store", num_requests=3)

            start_time = time.time()

            # Execute multiple operations concurrently
            tasks = []
            for i in range(3):
                task = asyncio.create_task(self.cli.doc_store_command("list"))
                tasks.append(task)

            await asyncio.gather(*tasks)

            end_time = time.time()

            # Verify reasonable completion time
            duration = end_time - start_time
            assert duration < 2.0

    
    async def test_service_recovery_integration(self):
        """Test service recovery integration"""
        with self.mock_framework.mock_cli_environment():
            # Setup initial failure then recovery
            self.mock_framework.setup_error_scenario("doc_store", "connection_error")

            # First attempt should fail
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.health_check_all()
                first_output = mock_stdout.getvalue()
                assert "❌" in first_output or "FAILED" in first_output

            # Setup recovery
            self.mock_framework.setup_service_responses("doc_store", "health")

            # Second attempt should succeed
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.health_check_all()
                second_output = mock_stdout.getvalue()
                assert "✅" in second_output or "HEALTHY" in second_output.upper()

    def test_cli_command_line_interface(self):
        """Test CLI command line interface"""
        # Test help command
        with patch('sys.argv', ['ecosystem_cli_executable.py', '--help-cli']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                try:
                    asyncio.run(main())
                except SystemExit:
                    pass  # Expected for --help

                output = mock_stdout.getvalue()
                assert "🌐 ECOSYSTEM CLI HELP" in output

    
    async def test_notification_workflow_integration(self):
        """Test notification workflow integration"""
        with self.mock_framework.mock_cli_environment():
            # Setup notification responses
            self.mock_framework.setup_service_responses("notification-service", "list")
            self.mock_framework.setup_service_responses("notification-service", "send")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.notification_service_command("list")
                await self.cli.notification_service_command("send",
                    title="Test Notification",
                    message="Integration test",
                    priority="normal"
                )

                output = mock_stdout.getvalue()
                assert "📬" in output or "notifications" in output.lower()

    
    async def test_prompt_management_integration(self):
        """Test prompt management integration"""
        with self.mock_framework.mock_cli_environment():
            # Setup prompt store responses
            operations = ["list", "create", "update"]
            for operation in operations:
                self.mock_framework.setup_service_responses("prompt_store", operation)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("list")
                await self.cli.prompt_store_command("create",
                    name="Test Prompt",
                    content="Test prompt content"
                )
                await self.cli.prompt_store_command("update",
                    prompt_id="prompt_001",
                    content="Updated content"
                )

                output = mock_stdout.getvalue()
                assert "📝" in output or "prompts" in output.lower()

    
    async def test_frontend_integration(self):
        """Test frontend service integration"""
        with self.mock_framework.mock_cli_environment():
            # Setup frontend responses
            self.mock_framework.setup_service_responses("frontend", "health")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.frontend_command("status")

                output = mock_stdout.getvalue()
                assert "🎨" in output or "frontend" in output.lower()

    
    async def test_full_ecosystem_test_workflow(self):
        """Test full ecosystem test workflow"""
        with self.mock_framework.mock_cli_environment():
            # Setup comprehensive test scenario
            services = ["analysis-service", "orchestrator", "doc_store",
                       "llm-gateway", "frontend", "code-analyzer"]

            for service in services:
                self.mock_framework.setup_service_responses(service, "health")

            start_time = time.time()

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.test_ecosystem_workflows()

            end_time = time.time()

            output = mock_stdout.getvalue()

            # Verify comprehensive testing
            for service in services:
                assert service in output

            # Verify reasonable execution time
            duration = end_time - start_time
            assert duration < 10.0

    
    async def test_load_testing_integration(self):
        """Test load testing integration"""
        with self.mock_framework.mock_cli_environment():
            # Setup load testing scenario
            num_requests = 10
            self.mock_framework.setup_concurrent_scenario("doc_store", num_requests)

            start_time = time.time()

            # Execute multiple concurrent requests
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for _ in range(num_requests):
                    future = executor.submit(asyncio.run, self.cli.doc_store_command("list"))
                    futures.append(future)

                # Wait for all to complete
                for future in futures:
                    future.result()

            end_time = time.time()

            # Verify load handling
            duration = end_time - start_time
            assert duration < 5.0  # Should handle load reasonably

    
    async def test_data_consistency_integration(self):
        """Test data consistency across operations"""
        with self.mock_framework.mock_cli_environment():
            # Setup consistent data scenario
            test_data = {
                "document_id": "test_doc_001",
                "content": "Consistent test content",
                "metadata": {"test": True, "version": "1.0"}
            }

            # Mock consistent responses
            list_response = self.fixtures.get_mock_doc_store_response("list")
            list_response.json_data["items"][0].update(test_data)
            self.mock_framework.http_client.add_response("doc_store_list", list_response)

            search_response = self.fixtures.get_mock_doc_store_response("search")
            search_response.json_data["items"][0].update(test_data)
            self.mock_framework.http_client.add_response("doc_store_search", search_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("list")
                await self.cli.doc_store_command("search", query="test")

                output = mock_stdout.getvalue()

                # Verify data consistency
                assert test_data["document_id"] in output
                assert test_data["content"] in output

    def test_cli_process_management(self):
        """Test CLI process management and cleanup"""
        import psutil
        import os

        # Get initial process count
        initial_processes = len(psutil.Process(os.getpid()).children(recursive=True))

        # Run CLI command
        with patch('sys.argv', ['ecosystem_cli_executable.py', 'health']):
            with patch('sys.stdout', new_callable=StringIO):
                try:
                    asyncio.run(main())
                except SystemExit:
                    pass

        # Check for proper cleanup
        final_processes = len(psutil.Process(os.getpid()).children(recursive=True))
        assert final_processes <= initial_processes + 1  # Allow small buffer


if __name__ == "__main__":
    # Run integration tests
    test_instance = TestCLIIntegration()
    test_instance.setup_method()

    print("Running CLI Integration Tests...")
    print("=" * 50)

    # Run async test
    async def run_async_tests():
        try:
            await test_instance.test_full_health_check_workflow()
            print("✅ Full health check workflow: PASSED")
        except Exception as e:
            print(f"❌ Full health check workflow: FAILED - {e}")

        try:
            await test_instance.test_document_lifecycle_workflow()
            print("✅ Document lifecycle workflow: PASSED")
        except Exception as e:
            print(f"❌ Document lifecycle workflow: FAILED - {e}")

        try:
            await test_instance.test_container_management_workflow()
            print("✅ Container management workflow: PASSED")
        except Exception as e:
            print(f"❌ Container management workflow: FAILED - {e}")

    asyncio.run(run_async_tests())
    print("\nCLI Integration Tests completed!")
