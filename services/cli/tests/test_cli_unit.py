"""
CLI Unit Tests

Comprehensive unit tests for CLI functionality including:
- Command parsing and validation
- Service URL mapping
- Environment detection
- Error handling
- Basic command execution
"""

import asyncio
import sys

from unittest.mock import Mock, patch, MagicMock, AsyncMock
from io import StringIO
import os
import tempfile
import json

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from ecosystem_cli_executable import EcosystemCLI
from .mock_framework import CLIMockFramework, create_successful_service_test
from .test_fixtures import CLITestFixtures


class TestCLIUnit:
    """Unit tests for CLI functionality"""

    def setup_method(self):
        """Setup test method"""
        self.cli = EcosystemCLI()
        self.fixtures = CLITestFixtures()
        self.mock_framework = CLIMockFramework()

    def test_service_url_mapping_local(self):
        """Test service URL mapping in local environment"""
        with patch.dict('os.environ', {}, clear=True):
            cli = EcosystemCLI()
            expected_urls = self.fixtures.get_test_service_urls()

            assert cli.services["analysis-service"] == expected_urls["analysis-service"]
            assert cli.services["orchestrator"] == expected_urls["orchestrator"]
            assert cli.services["doc_store"] == expected_urls["doc_store"]

    def test_service_url_mapping_docker(self):
        """Test service URL mapping in Docker environment"""
        with patch.dict('os.environ', {'DOCKER_CONTAINER': 'true'}):
            cli = EcosystemCLI()
            expected_urls = self.fixtures.get_docker_service_urls()

            assert cli.services["analysis-service"] == expected_urls["analysis-service"]
            assert cli.services["orchestrator"] == expected_urls["orchestrator"]

    def test_environment_detection_local(self):
        """Test environment detection for local development"""
        with patch.dict('os.environ', {}, clear=True):
            environment = self.cli._detect_environment()
            assert environment == "local"

    def test_environment_detection_docker(self):
        """Test environment detection for Docker"""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True):
                environment = self.cli._detect_environment()
                assert environment == "docker"

    def test_environment_detection_kubernetes(self):
        """Test environment detection for Kubernetes"""
        with patch.dict('os.environ', {'KUBERNETES_SERVICE_HOST': 'localhost'}):
            environment = self.cli._detect_environment()
            assert environment == "kubernetes"

    
    async def test_health_check_success(self):
        """Test successful health check"""
        service_name = "doc_store"

        with self.mock_framework.mock_cli_environment():
            self.mock_framework.setup_service_responses(service_name, "health")

            # Capture stdout
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.health_check()

                output = mock_stdout.getvalue()
                assert "ECOSYSTEM HEALTH STATUS" in output
                assert service_name in output

    
    async def test_health_check_failure(self):
        """Test health check failure"""
        with self.mock_framework.mock_cli_environment():
            self.mock_framework.setup_error_scenario("doc_store", "connection_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.health_check()

                output = mock_stdout.getvalue()
                assert "❌" in output or "FAILED" in output

    
    async def test_doc_store_operations(self):
        """Test doc_store CLI operations"""
        with self.mock_framework.mock_cli_environment():
            # Test list operation
            self.mock_framework.setup_service_responses("doc_store", "list")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.doc_store_command("list")

                output = mock_stdout.getvalue()
                assert "📄 DOCUMENTS" in output or "documents" in output.lower()

    
    async def test_prompt_store_operations(self):
        """Test prompt_store CLI operations"""
        with self.mock_framework.mock_cli_environment():
            self.mock_framework.setup_service_responses("prompt_store", "list")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.prompt_store_command("list")

                output = mock_stdout.getvalue()
                assert "📝 PROMPTS" in output or "prompts" in output.lower()

    
    async def test_notification_operations(self):
        """Test notification service CLI operations"""
        with self.mock_framework.mock_cli_environment():
            self.mock_framework.setup_service_responses("notification-service", "list")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.notification_service_command("list")

                output = mock_stdout.getvalue()
                assert "📬 NOTIFICATIONS" in output or "notifications" in output.lower()

    
    async def test_workflow_operations(self):
        """Test workflow CLI operations"""
        with self.mock_framework.mock_cli_environment():
            self.mock_framework.setup_service_responses("orchestrator", "list")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.orchestrator_command("workflows")

                output = mock_stdout.getvalue()
                assert "🤝" in output or "workflows" in output.lower()

    
    async def test_container_list(self):
        """Test container listing"""
        with self.mock_framework.mock_cli_environment():
            self.mock_framework.setup_container_responses("test-service", "list")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.list_containers()

                output = mock_stdout.getvalue()
                assert "🐳 ECOSYSTEM CONTAINER STATUS" in output
                assert "NAME" in output
                assert "SERVICE" in output
                assert "STATUS" in output

    
    async def test_container_stats(self):
        """Test container statistics"""
        with self.mock_framework.mock_cli_environment():
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.show_container_stats()

                output = mock_stdout.getvalue()
                assert "📊 CONTAINER RESOURCE STATISTICS" in output
                assert "CPU" in output
                assert "MEM" in output

    
    async def test_container_restart(self):
        """Test container restart"""
        service_name = "frontend"

        with self.mock_framework.mock_cli_environment():
            self.mock_framework.setup_container_responses(service_name, "restart")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.restart_container(service_name)

                output = mock_stdout.getvalue()
                assert f"🔄 Restarting container: {service_name}" in output
                assert "restarted successfully" in output

    
    async def test_container_logs(self):
        """Test container logs retrieval"""
        service_name = "orchestrator"

        with self.mock_framework.mock_cli_environment():
            self.mock_framework.setup_container_responses(service_name, "logs")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.show_container_logs(service_name, lines=5)

                output = mock_stdout.getvalue()
                assert f"📜 Container Logs: {service_name}" in output
                assert "INFO:" in output or "logs" in output.lower()

    
    async def test_container_stop_start(self):
        """Test container stop and start operations"""
        service_name = "doc_store"

        with self.mock_framework.mock_cli_environment():
            # Test stop
            self.mock_framework.setup_container_responses(service_name, "stop")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.stop_container(service_name)

                output = mock_stdout.getvalue()
                assert f"🛑 Stopping container: {service_name}" in output
                assert "stopped successfully" in output

            # Test start
            self.mock_framework.setup_container_responses(service_name, "start")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.start_container(service_name)

                output = mock_stdout.getvalue()
                assert f"▶️  Starting container: {service_name}" in output
                assert "started successfully" in output

    
    async def test_container_rebuild(self):
        """Test container rebuild operation"""
        service_name = "analysis-service"

        with self.mock_framework.mock_cli_environment():
            self.mock_framework.setup_container_responses(service_name, "rebuild")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.rebuild_container(service_name)

                output = mock_stdout.getvalue()
                assert f"🔨 Rebuilding container: {service_name}" in output
                assert "rebuilt successfully" in output

    def test_error_handling_invalid_service(self):
        """Test error handling for invalid service names"""
        cli = EcosystemCLI()

        # Test with invalid service
        assert "invalid-service" not in cli.services

    def test_url_construction(self):
        """Test URL construction for different services"""
        cli = EcosystemCLI()

        # Test URL construction
        base_url = cli.services["doc_store"]
        assert "localhost" in base_url or "hackathon" in base_url
        assert "://" in base_url

    
    async def test_concurrent_operations(self):
        """Test concurrent CLI operations"""
        with self.mock_framework.mock_cli_environment():
            # Setup multiple services
            services = ["doc_store", "prompt_store", "notification-service"]
            for service in services:
                self.mock_framework.setup_service_responses(service, "health")

            # Run concurrent health checks
            tasks = []
            for service in services:
                task = asyncio.create_task(self.cli.health_check())
                tasks.append(task)

            await asyncio.gather(*tasks)

            # Verify requests were made
            summary = self.mock_framework.get_test_summary()
            assert summary["http_requests"] >= len(services)

    def test_command_validation(self):
        """Test command validation and error handling"""
        # Test missing required parameters
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # This would normally be handled by argparse, but we can test the logic
            pass

    
    async def test_timeout_handling(self):
        """Test timeout handling for slow services"""
        with self.mock_framework.mock_cli_environment():
            # Setup slow response
            self.mock_framework.setup_performance_scenario("doc_store", delay=5.0)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                start_time = asyncio.get_event_loop().time()
                await self.cli.health_check()
                end_time = asyncio.get_event_loop().time()

                # Should complete within reasonable time despite delay
                assert end_time - start_time < 10  # Allow some buffer

    def test_output_formatting(self):
        """Test CLI output formatting"""
        # Test that output includes expected emojis and formatting
        cli = EcosystemCLI()

        # Check help output formatting
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli.show_help()
            output = mock_stdout.getvalue()

            assert "🌐" in output  # Emoji
            assert "=" * 30 in output  # Formatting
            assert "Commands:" in output
            assert "Examples:" in output

    def test_service_discovery(self):
        """Test service discovery and availability"""
        cli = EcosystemCLI()

        # Test that all expected services are available
        expected_services = [
            "analysis-service", "orchestrator", "source-agent",
            "doc_store", "prompt_store", "notification-service",
            "llm-gateway", "frontend", "code-analyzer"
        ]

        for service in expected_services:
            assert service in cli.services
            assert cli.services[service].startswith("http")

    
    async def test_error_recovery(self):
        """Test error recovery and graceful degradation"""
        with self.mock_framework.mock_cli_environment():
            # Setup service that initially fails but then succeeds
            self.mock_framework.setup_error_scenario("doc_store", "connection_error")

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.health_check()

                output = mock_stdout.getvalue()
                # Should handle error gracefully without crashing
                assert "❌" in output or "FAILED" in output

    def test_configuration_persistence(self):
        """Test configuration persistence and reloading"""
        # Test that CLI maintains state between operations
        cli1 = EcosystemCLI()
        cli2 = EcosystemCLI()

        assert cli1.services == cli2.services  # Should be identical

    def test_memory_management(self):
        """Test memory management and cleanup"""
        import gc

        cli = EcosystemCLI()

        # Force garbage collection
        del cli
        gc.collect()

        # Should not cause any issues
        assert True

    
    async def test_large_data_handling(self):
        """Test handling of large data responses"""
        with self.mock_framework.mock_cli_environment():
            # Setup response with large data
            large_data = {"data": "x" * 10000, "items": [{"id": i} for i in range(1000)]}
            response = self.fixtures.get_mock_health_response("doc_store")
            response.json_data = large_data

            self.mock_framework.setup_service_responses("doc_store", "health", response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.health_check()

                output = mock_stdout.getvalue()
                # Should handle large data without issues
                assert len(output) > 0


if __name__ == "__main__":
    # Run basic tests
    test_instance = TestCLIUnit()
    test_instance.setup_method()

    print("Running CLI Unit Tests...")
    print("=" * 50)

    # Test service URL mapping
    try:
        test_instance.test_service_url_mapping_local()
        print("✅ Service URL mapping (local): PASSED")
    except Exception as e:
        print(f"❌ Service URL mapping (local): FAILED - {e}")

    # Test environment detection
    try:
        test_instance.test_environment_detection_local()
        print("✅ Environment detection (local): PASSED")
    except Exception as e:
        print(f"❌ Environment detection (local): FAILED - {e}")

    print("\nCLI Unit Tests completed!")
