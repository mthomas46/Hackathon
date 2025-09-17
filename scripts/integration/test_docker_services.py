#!/usr/bin/env python3
"""
Docker Services Testing Script
Tests individual services and all services in Docker containers
"""

import os
import sys
import asyncio
import subprocess
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import docker
import json

console = Console()

class DockerServiceTester:
    """Test Docker services individually and as a group."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.docker_client = docker.from_env()
        self.services_config = {
            "redis": {
                "name": "Redis",
                "image": "redis:7-alpine",
                "ports": {"6379/tcp": 6379},
                "health_url": None,
                "health_check": self._check_redis_health
            },
            "doc_store": {
                "name": "Doc Store",
                "build": {"context": ".", "dockerfile": "services/doc_store/Dockerfile"},
                "ports": {"5010/tcp": 5010},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis"],
                "health_url": "http://localhost:5010/health"
            },
            "analysis_service": {
                "name": "Analysis Service",
                "build": {"context": ".", "dockerfile": "services/analysis_service/Dockerfile"},
                "ports": {"5020/tcp": 5020},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis", "doc_store"],
                "health_url": "http://localhost:5020/health"
            },
            "orchestrator": {
                "name": "Orchestrator",
                "build": {"context": ".", "dockerfile": "services/orchestrator/Dockerfile"},
                "ports": {"5099/tcp": 5099},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis"],
                "health_url": "http://localhost:5099/health/system"
            },
            "prompt_store": {
                "name": "Prompt Store",
                "build": {"context": ".", "dockerfile": "services/prompt_store/Dockerfile"},
                "ports": {"5110/tcp": 5110},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis"],
                "health_url": "http://localhost:5110/health"
            },
            "summarizer_hub": {
                "name": "Summarizer Hub",
                "build": {"context": ".", "dockerfile": "services/summarizer_hub/Dockerfile"},
                "ports": {"5060/tcp": 5060},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis"],
                "health_url": "http://localhost:5060/health"
            },
            "architecture_digitizer": {
                "name": "Architecture Digitizer",
                "build": {"context": ".", "dockerfile": "services/architecture_digitizer/Dockerfile"},
                "ports": {"5105/tcp": 5105},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis"],
                "health_url": "http://localhost:5105/health"
            },
            "bedrock_proxy": {
                "name": "Bedrock Proxy",
                "build": {"context": ".", "dockerfile": "services/bedrock_proxy/Dockerfile"},
                "ports": {"7090/tcp": 7090},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis"],
                "health_url": "http://localhost:7090/health"
            },
            "github_mcp": {
                "name": "GitHub MCP",
                "build": {"context": ".", "dockerfile": "services/github_mcp/Dockerfile"},
                "ports": {"5072/tcp": 5072},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis"],
                "health_url": "http://localhost:5072/health"
            },
            "interpreter": {
                "name": "Interpreter",
                "build": {"context": ".", "dockerfile": "services/interpreter/Dockerfile"},
                "ports": {"5120/tcp": 5120},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis"],
                "health_url": "http://localhost:5120/health"
            },
            "code_analyzer": {
                "name": "Code Analyzer",
                "build": {"context": ".", "dockerfile": "services/code_analyzer/Dockerfile"},
                "ports": {"5085/tcp": 5085},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis"],
                "health_url": "http://localhost:5085/health"
            },
            "secure_analyzer": {
                "name": "Secure Analyzer",
                "build": {"context": ".", "dockerfile": "services/secure_analyzer/Dockerfile"},
                "ports": {"5070/tcp": 5070},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis"],
                "health_url": "http://localhost:5070/health"
            },
            "log_collector": {
                "name": "Log Collector",
                "build": {"context": ".", "dockerfile": "services/log_collector/Dockerfile"},
                "ports": {"5080/tcp": 5080},
                "volumes": [f"{self.project_root}:/app:ro"],
                "environment": ["PYTHONPATH=/app"],
                "depends_on": ["redis"],
                "health_url": "http://localhost:5080/health"
            }
        }

        self.containers: Dict[str, docker.models.containers.Container] = {}
        self.test_results: Dict[str, Dict] = {}

    def _check_redis_health(self) -> bool:
        """Check Redis health."""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            return r.ping()
        except:
            return False

    async def check_service_health(self, service_id: str, timeout: int = 60) -> bool:
        """Check if a service is healthy."""
        service = self.services_config.get(service_id)
        if not service:
            return False

        # Special handling for Redis
        if service_id == "redis":
            return service.get("health_check", lambda: False)()

        health_url = service.get("health_url")
        if not health_url:
            return True  # No health check defined, assume healthy

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                pass
            await asyncio.sleep(2)

        return False

    def cleanup_containers(self):
        """Clean up any existing containers."""
        console.print("🧹 Cleaning up existing containers...")

        try:
            for container in self.docker_client.containers.list(all=True):
                if any(service in container.name for service in self.services_config.keys()):
                    console.print(f"🔄 Removing container: {container.name}")
                    container.remove(force=True)
        except Exception as e:
            console.print(f"[yellow]⚠️  Cleanup warning: {e}[/yellow]")

    async def test_service_docker(self, service_id: str) -> bool:
        """Test a single service in Docker."""
        service = self.services_config.get(service_id)
        if not service:
            console.print(f"[red]❌ Unknown service: {service_id}[/red]")
            return False

        console.print(f"🐳 Testing {service['name']} in Docker...")

        try:
            # Create container
            container_config = service.copy()
            container_name = f"test_{service_id}"

            # Remove health_url from container config as it's not a Docker parameter
            container_config.pop("health_url", None)
            container_config.pop("health_check", None)
            container_config["name"] = container_name
            container_config["detach"] = True

            container = self.docker_client.containers.run(**container_config)
            self.containers[service_id] = container

            console.print(f"✅ Container created: {container.name}")

            # Wait for container to start
            await asyncio.sleep(5)

            # Check if container is running
            container.reload()
            if container.status != "running":
                console.print(f"❌ Container not running: {container.status}")
                logs = container.logs().decode('utf-8')
                console.print(f"Logs: {logs[:500]}...")
                return False

            # Check service health
            if await self.check_service_health(service_id, timeout=30):
                console.print(f"✅ {service['name']} is healthy in Docker")
                return True
            else:
                console.print(f"❌ {service['name']} health check failed")
                logs = container.logs().decode('utf-8')
                console.print(f"Logs: {logs[:500]}...")
                return False

        except Exception as e:
            console.print(f"❌ Error testing {service['name']}: {e}")
            return False

    async def test_all_services_docker(self) -> bool:
        """Test all services in Docker using docker-compose."""
        console.print("🐳 Testing all services with Docker Compose...")

        try:
            # Change to project directory
            os.chdir(self.project_root)

            # Start services with docker-compose
            console.print("🚀 Starting services with docker-compose...")
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.dev.yml", "up", "-d"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                console.print(f"❌ Docker Compose failed: {result.stderr}")
                return False

            console.print("✅ Docker Compose started")

            # Wait for services to initialize
            console.print("⏳ Waiting for services to initialize...")
            await asyncio.sleep(30)

            # Check service health
            healthy_services = 0
            total_services = 0

            for service_id, service in self.services_config.items():
                total_services += 1
                if await self.check_service_health(service_id, timeout=30):
                    console.print(f"✅ {service['name']} is healthy")
                    healthy_services += 1
                else:
                    console.print(f"❌ {service['name']} health check failed")

            success_rate = healthy_services / total_services if total_services > 0 else 0

            console.print(f"\n📊 Health Check Results: {healthy_services}/{total_services} services healthy ({success_rate:.1%})")

            if success_rate >= 0.8:  # 80% success rate
                console.print("🎉 Docker ecosystem test PASSED")
                return True
            else:
                console.print("❌ Docker ecosystem test FAILED")
                return False

        except subprocess.TimeoutExpired:
            console.print("❌ Docker Compose timed out")
            return False
        except Exception as e:
            console.print(f"❌ Error testing Docker ecosystem: {e}")
            return False

    async def run_individual_tests(self):
        """Run individual service tests."""
        console.print("🐳 INDIVIDUAL DOCKER SERVICE TESTS")
        console.print("=" * 50)

        self.cleanup_containers()

        results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Testing individual services...", total=len(self.services_config))

            for service_id in self.services_config.keys():
                service = self.services_config[service_id]

                progress.update(task, description=f"Testing {service['name']}...")

                success = await self.test_service_docker(service_id)
                results[service_id] = success

                progress.update(task, advance=1)

        # Cleanup
        self.cleanup_containers()

        # Summary
        successful = sum(1 for result in results.values() if result)
        total = len(results)

        console.print(f"\n📊 Individual Tests: {successful}/{total} services passed")

        return successful == total

    async def run_ecosystem_test(self):
        """Run full ecosystem test."""
        console.print("🐳 FULL ECOSYSTEM DOCKER TEST")
        console.print("=" * 50)

        try:
            success = await self.test_all_services_docker()

            # Cleanup
            console.print("🧹 Cleaning up Docker containers...")
            subprocess.run(["docker-compose", "-f", "docker-compose.dev.yml", "down"],
                         capture_output=True)

            return success

        except Exception as e:
            console.print(f"❌ Ecosystem test error: {e}")
            return False

    def display_service_status(self):
        """Display service status table."""
        table = Table(title="Docker Service Status")
        table.add_column("Service", style="cyan")
        table.add_column("Port", style="white")
        table.add_column("Description", style="white")
        table.add_column("Status", style="green")

        for service_id, service in self.services_config.items():
            port = list(service.get("ports", {}).values())[0] if service.get("ports") else "N/A"
            status = "🟢 Running" if service_id in self.containers and self.containers[service_id].status == "running" else "🔴 Stopped"
            table.add_row(service["name"], str(port), service.get("description", "N/A"), status)

        console.print(table)

async def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Docker Services Testing")
    parser.add_argument("--individual", action="store_true", help="Test individual services")
    parser.add_argument("--ecosystem", action="store_true", help="Test full ecosystem")
    parser.add_argument("--all", action="store_true", help="Test both individual and ecosystem")
    parser.add_argument("--service", help="Test only specific service")
    parser.add_argument("--status", action="store_true", help="Show service status")

    args = parser.parse_args()

    tester = DockerServiceTester()

    if args.status:
        tester.display_service_status()
        return

    if args.service:
        success = await tester.test_service_docker(args.service)
        if success:
            console.print(f"\n[green]🎉 {args.service} Docker test PASSED[/green]")
        else:
            console.print(f"\n[red]❌ {args.service} Docker test FAILED[/red]")
        return

    if args.individual or args.all:
        success = await tester.run_individual_tests()
        if not args.all:
            sys.exit(0 if success else 1)

    if args.ecosystem or args.all:
        success = await tester.run_ecosystem_test()
        if not args.all:
            sys.exit(0 if success else 1)

    if not any([args.individual, args.ecosystem, args.all, args.service, args.status]):
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
