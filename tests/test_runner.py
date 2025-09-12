"""Test Runner - Infrastructure for running tests against mocked and live services.

This module provides comprehensive test execution infrastructure supporting:
- Unit tests with mocked dependencies
- Integration tests with in-memory databases
- Live tests against Docker containerized services
- Performance and load testing capabilities
"""

import pytest
import subprocess
import time
import requests
import docker
import os
from typing import Dict, List, Any, Optional
from pathlib import Path


class ServiceContainer:
    """Manages Docker containers for live testing."""

    def __init__(self, service_name: str, image: str, ports: Dict[str, int], env_vars: Dict[str, str] = None):
        self.service_name = service_name
        self.image = image
        self.ports = ports
        self.env_vars = env_vars or {}
        self.container = None
        self.client = docker.from_env()

    def start(self):
        """Start the service container."""
        try:
            port_bindings = {f"{container_port}/tcp": host_port for container_port, host_port in self.ports.items()}

            self.container = self.client.containers.run(
                self.image,
                detach=True,
                ports=port_bindings,
                environment=self.env_vars,
                name=f"test-{self.service_name}",
                remove=True
            )

            print(f"Started {self.service_name} container: {self.container.id}")

            # Wait for service to be ready
            self._wait_for_ready()

        except Exception as e:
            print(f"Failed to start {self.service_name}: {e}")
            raise

    def stop(self):
        """Stop the service container."""
        if self.container:
            try:
                self.container.stop(timeout=10)
                print(f"Stopped {self.service_name} container")
            except Exception as e:
                print(f"Error stopping {self.service_name}: {e}")

    def _wait_for_ready(self, timeout: int = 60):
        """Wait for service to be ready."""
        host_port = list(self.ports.values())[0]
        url = f"http://localhost:{host_port}/health"

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"{self.service_name} is ready")
                    return
            except:
                pass

            time.sleep(2)

        raise Exception(f"{self.service_name} failed to become ready within {timeout} seconds")

    def is_running(self) -> bool:
        """Check if container is running."""
        if self.container:
            self.container.reload()
            return self.container.status == 'running'
        return False


class TestEnvironment:
    """Manages test environment setup and teardown."""

    def __init__(self, test_mode: str = "mocked"):
        """
        Initialize test environment.

        Args:
            test_mode: "mocked", "integration", or "live"
        """
        self.test_mode = test_mode
        self.services: Dict[str, ServiceContainer] = {}
        self.base_path = Path(__file__).parent.parent

    def setup_services(self, services_to_start: List[str] = None):
        """Setup services based on test mode."""
        if self.test_mode == "mocked":
            # No services needed for mocked tests
            return

        if services_to_start is None:
            services_to_start = ["orchestrator", "doc-store", "analysis-service", "source-agent"]

        for service in services_to_start:
            self._setup_service(service)

    def _setup_service(self, service_name: str):
        """Setup individual service."""
        if self.test_mode == "live":
            self._setup_live_service(service_name)
        elif self.test_mode == "integration":
            self._setup_integration_service(service_name)

    def _setup_live_service(self, service_name: str):
        """Setup live service with Docker."""
        # Service configurations for live testing
        service_configs = {
            "orchestrator": {
                "image": "doc-consistency-orchestrator:latest",
                "ports": {"8000": 18000},
                "env": {
                    "ENVIRONMENT": "test",
                    "REDIS_HOST": "localhost",
                    "DOC_STORE_URL": "http://localhost:18001",
                    "ANALYSIS_SERVICE_URL": "http://localhost:18002"
                }
            },
            "doc-store": {
                "image": "doc-consistency-doc-store:latest",
                "ports": {"8000": 18001},
                "env": {
                    "ENVIRONMENT": "test",
                    "DATABASE_URL": "sqlite:///test.db",
                    "REDIS_HOST": "localhost"
                }
            },
            "analysis-service": {
                "image": "doc-consistency-analysis:latest",
                "ports": {"8000": 18002},
                "env": {
                    "ENVIRONMENT": "test",
                    "DOC_STORE_URL": "http://localhost:18001"
                }
            },
            "source-agent": {
                "image": "doc-consistency-source-agent:latest",
                "ports": {"8000": 18003},
                "env": {
                    "ENVIRONMENT": "test",
                    "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", ""),
                    "JIRA_URL": os.getenv("JIRA_URL", ""),
                    "CONFLUENCE_URL": os.getenv("CONFLUENCE_URL", "")
                }
            }
        }

        if service_name in service_configs:
            config = service_configs[service_name]
            container = ServiceContainer(
                service_name,
                config["image"],
                config["ports"],
                config["env"]
            )
            self.services[service_name] = container

    def _setup_integration_service(self, service_name: str):
        """Setup integration service (in-memory for faster testing)."""
        # For integration tests, we might use in-memory versions
        # or lightweight containers
        pass

    def start_services(self):
        """Start all configured services."""
        for service in self.services.values():
            service.start()

    def stop_services(self):
        """Stop all running services."""
        for service in self.services.values():
            service.stop()

    def get_service_url(self, service_name: str) -> str:
        """Get service URL for testing."""
        if service_name in self.services:
            container = self.services[service_name]
            host_port = list(container.ports.values())[0]
            return f"http://localhost:{host_port}"

        # Default URLs for different test modes
        if self.test_mode == "mocked":
            return f"http://mock-{service_name}:8000"
        elif self.test_mode == "integration":
            return f"http://localhost:8{['orchestrator', 'doc-store', 'analysis-service', 'source-agent'].index(service_name) + 1}00"

        return f"http://localhost:1800{['orchestrator', 'doc-store', 'analysis-service', 'source-agent'].index(service_name)}"


class TestRunner:
    """Main test runner for different test modes."""

    def __init__(self, test_mode: str = "mocked"):
        self.test_mode = test_mode
        self.environment = TestEnvironment(test_mode)

    def run_tests(self, test_pattern: str = "test_*.py", services: List[str] = None, **pytest_args):
        """Run tests with specified configuration."""
        print(f"Running tests in {self.test_mode} mode")

        # Setup environment
        self.environment.setup_services(services)

        try:
            # Start services if needed
            if self.test_mode in ["integration", "live"]:
                self.environment.start_services()

            # Set environment variables for tests
            os.environ["TEST_MODE"] = self.test_mode

            for service in (services or []):
                url = self.environment.get_service_url(service)
                os.environ[f"{service.upper()}_URL"] = url

            # Run pytest with custom configuration
            args = [
                "-v",
                "--tb=short",
                f"--override-ini=markers=unit:Unit tests,integration:Integration tests,live:Live tests,slow:Slow tests"
            ]

            if test_pattern:
                args.append(test_pattern)

            # Add custom arguments
            for key, value in pytest_args.items():
                if isinstance(value, bool) and value:
                    args.append(f"--{key}")
                elif isinstance(value, str):
                    args.extend([f"--{key}", value])

            # Run tests
            result = pytest.main(args)

            return result

        finally:
            # Cleanup
            if self.test_mode in ["integration", "live"]:
                self.environment.stop_services()

    def run_service_tests(self, service_name: str, test_type: str = "unit"):
        """Run tests for specific service."""
        test_pattern = f"services/{service_name}/test_*.py"

        if test_type == "live":
            self.test_mode = "live"
            self.environment = TestEnvironment("live")

        return self.run_tests(test_pattern, services=[service_name])

    def run_integration_tests(self, services: List[str] = None):
        """Run integration tests across services."""
        if services is None:
            services = ["orchestrator", "doc-store", "analysis-service", "source-agent"]

        self.test_mode = "integration"
        self.environment = TestEnvironment("integration")

        return self.run_tests(
            "integration/",
            services=services,
            integration=True
        )

    def run_performance_tests(self, services: List[str] = None, duration: int = 60):
        """Run performance tests."""
        print(f"Running performance tests for {duration} seconds")

        self.test_mode = "live"
        self.environment = TestEnvironment("live")
        self.environment.setup_services(services)

        try:
            self.environment.start_services()

            # Run load tests
            self._run_load_tests(duration)

        finally:
            self.environment.stop_services()

    def _run_load_tests(self, duration: int):
        """Run load testing against services."""
        import concurrent.futures
        import threading

        results = {"requests": 0, "errors": 0, "response_times": []}

        def make_request(service_url: str):
            try:
                start_time = time.time()
                response = requests.get(f"{service_url}/health", timeout=5)
                end_time = time.time()

                results["requests"] += 1
                results["response_times"].append(end_time - start_time)

                if response.status_code != 200:
                    results["errors"] += 1

            except Exception as e:
                results["errors"] += 1

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            while time.time() - start_time < duration:
                for service in self.environment.services.values():
                    if service.is_running():
                        service_url = f"http://localhost:{list(service.ports.values())[0]}"
                        executor.submit(make_request, service_url)

                time.sleep(0.1)  # Small delay to prevent overwhelming

        # Report results
        total_time = time.time() - start_time
        rps = results["requests"] / total_time

        print("Performance Test Results:")
        print(f"- Total requests: {results['requests']}")
        print(f"- Error rate: {results['errors'] / max(results['requests'], 1) * 100:.2f}%")
        print(".2f")
        print(".2f")

        if results["response_times"]:
            avg_response_time = sum(results["response_times"]) / len(results["response_times"])
            max_response_time = max(results["response_times"])
            print(".2f")
            print(".2f")


class DockerTestRunner:
    """Docker-based test runner for live testing."""

    def __init__(self):
        self.client = docker.from_env()
        self.containers = []

    def build_service_images(self, services: List[str] = None):
        """Build Docker images for services."""
        if services is None:
            services = ["orchestrator", "doc-store", "analysis-service", "source-agent", "frontend"]

        for service in services:
            self._build_service_image(service)

    def _build_service_image(self, service_name: str):
        """Build Docker image for specific service."""
        dockerfile_path = f"services/{service_name}/Dockerfile"
        image_name = f"doc-consistency-{service_name}:test"

        if os.path.exists(dockerfile_path):
            print(f"Building {service_name} image...")
            try:
                self.client.images.build(
                    path=".",
                    dockerfile=dockerfile_path,
                    tag=image_name,
                    rm=True
                )
                print(f"Built {service_name} image successfully")
            except Exception as e:
                print(f"Failed to build {service_name}: {e}")
        else:
            print(f"No Dockerfile found for {service_name}")

    def run_docker_compose_tests(self, compose_file: str = "docker-compose.test.yml"):
        """Run tests using Docker Compose."""
        try:
            # Start services
            subprocess.run([
                "docker-compose",
                "-f", compose_file,
                "up",
                "-d"
            ], check=True)

            # Wait for services to be ready
            time.sleep(30)

            # Run tests
            result = subprocess.run([
                "docker-compose",
                "-f", compose_file,
                "exec",
                "-T",
                "test-runner",
                "pytest",
                "/app/tests",
                "-v",
                "--tb=short"
            ])

            return result.returncode

        finally:
            # Cleanup
            subprocess.run([
                "docker-compose",
                "-f", compose_file,
                "down",
                "-v"
            ])

    def create_test_compose_file(self, services: List[str] = None):
        """Create Docker Compose file for testing."""
        if services is None:
            services = ["orchestrator", "doc-store", "analysis-service", "source-agent"]

        compose_content = """
version: '3.8'

services:
"""

        port_offset = 18000
        for i, service in enumerate(services):
            port = port_offset + i
            compose_content += f"""
  {service}:
    build:
      context: ..
      dockerfile: services/{service}/Dockerfile
    ports:
      - "{port}:8000"
    environment:
      - ENVIRONMENT=test
      - REDIS_HOST=redis
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
"""

        compose_content += """
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  test-runner:
    build:
      context: ..
      dockerfile: Dockerfile.test
    volumes:
      - ..:/app
      - /app/__pycache__
    depends_on:
      - orchestrator
      - doc-store
      - analysis-service
      - source-agent
    environment:
      - TEST_MODE=live
"""

        with open("docker-compose.test.yml", "w") as f:
            f.write(compose_content)

        print("Created docker-compose.test.yml")


# Convenience functions for different test modes
def run_mocked_tests(test_pattern: str = "test_*.py", **kwargs):
    """Run tests with mocked dependencies."""
    runner = TestRunner("mocked")
    return runner.run_tests(test_pattern, **kwargs)


def run_integration_tests(services: List[str] = None, **kwargs):
    """Run integration tests."""
    runner = TestRunner("integration")
    return runner.run_integration_tests(services, **kwargs)


def run_live_tests(services: List[str] = None, **kwargs):
    """Run live tests against Docker containers."""
    runner = TestRunner("live")
    return runner.run_tests("test_*.py", services=services, **kwargs)


def run_performance_tests(services: List[str] = None, duration: int = 60):
    """Run performance tests."""
    runner = TestRunner("live")
    return runner.run_performance_tests(services, duration)


def setup_docker_environment(services: List[str] = None):
    """Setup Docker environment for testing."""
    docker_runner = DockerTestRunner()

    print("Building service images...")
    docker_runner.build_service_images(services)

    print("Creating test compose file...")
    docker_runner.create_test_compose_file(services)

    return docker_runner


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_runner.py <mode> [services...]")
        print("Modes: mocked, integration, live, performance, setup")
        sys.exit(1)

    mode = sys.argv[1]
    services = sys.argv[2:] if len(sys.argv) > 2 else None

    if mode == "mocked":
        exit_code = run_mocked_tests()
    elif mode == "integration":
        exit_code = run_integration_tests(services)
    elif mode == "live":
        exit_code = run_live_tests(services)
    elif mode == "performance":
        exit_code = run_performance_tests(services)
    elif mode == "setup":
        setup_docker_environment(services)
        exit_code = 0
    else:
        print(f"Unknown mode: {mode}")
        exit_code = 1

    sys.exit(exit_code)
