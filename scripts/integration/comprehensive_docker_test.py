#!/usr/bin/env python3
"""
Comprehensive Docker Services Integration Test

This script provides a complete testing framework for Docker services in the LLM Documentation Ecosystem.
It tests individual services, service groups by profile, and full ecosystem startup.

Usage:
    python scripts/integration/comprehensive_docker_test.py --all
    python scripts/integration/comprehensive_docker_test.py --individual
    python scripts/integration/comprehensive_docker_test.py --profiles
    python scripts/integration/comprehensive_docker_test.py --service redis
"""

import asyncio
import subprocess
import time
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

@dataclass
class ServiceConfig:
    """Configuration for a Docker service."""
    name: str
    port: int
    health_endpoint: str
    dependencies: List[str]
    profile: str
    build_type: str  # 'image' or 'dockerfile'
    expected_issues: List[str] = None

class ComprehensiveDockerTester:
    """Comprehensive Docker services testing framework."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent.parent
        self.compose_file = self.project_root / "docker-compose.dev.yml"
        
        # Service configurations based on docker-compose.dev.yml
        self.services = {
            # Infrastructure
            "redis": ServiceConfig(
                name="Redis", port=6379, health_endpoint="ping",
                dependencies=[], profile="core", build_type="image"
            ),
            
            # Core Services
            "orchestrator": ServiceConfig(
                name="Orchestrator", port=5099, health_endpoint="/health",
                dependencies=["redis"], profile="core", build_type="image"
            ),
            "doc_store": ServiceConfig(
                name="Doc Store", port=5087, health_endpoint="/health",
                dependencies=["redis"], profile="core", build_type="image",
                expected_issues=["port_mapping", "import_issues"]
            ),
            "analysis-service": ServiceConfig(
                name="Analysis Service", port=5020, health_endpoint="/health",
                dependencies=["redis", "doc_store"], profile="core", build_type="image",
                expected_issues=["module_import_path", "dependency_resolution"]
            ),
            "source-agent": ServiceConfig(
                name="Source Agent", port=5000, health_endpoint="/health",
                dependencies=["redis"], profile="core", build_type="image",
                expected_issues=["module_import_path"]
            ),
            "frontend": ServiceConfig(
                name="Frontend", port=3000, health_endpoint="/health",
                dependencies=["orchestrator", "analysis-service"], profile="core", build_type="image"
            ),
            
            # AI Services
            "summarizer-hub": ServiceConfig(
                name="Summarizer Hub", port=5060, health_endpoint="/health",
                dependencies=[], profile="ai_services", build_type="image"
            ),
            "architecture-digitizer": ServiceConfig(
                name="Architecture Digitizer", port=5105, health_endpoint="/health",
                dependencies=[], profile="ai_services", build_type="image"
            ),
            "bedrock-proxy": ServiceConfig(
                name="Bedrock Proxy", port=7090, health_endpoint="/health",
                dependencies=[], profile="ai_services", build_type="image"
            ),
            "github-mcp": ServiceConfig(
                name="GitHub MCP", port=5072, health_endpoint="/health",
                dependencies=[], profile="ai_services", build_type="image"
            ),
            "prompt-store": ServiceConfig(
                name="Prompt Store", port=5110, health_endpoint="/health",
                dependencies=["redis"], profile="ai_services", build_type="dockerfile",
                expected_issues=["missing_requirements_txt"]
            ),
            "interpreter": ServiceConfig(
                name="Interpreter", port=5120, health_endpoint="/health",
                dependencies=["prompt-store", "orchestrator", "analysis-service"], 
                profile="ai_services", build_type="dockerfile",
                expected_issues=["missing_requirements_txt"]
            ),
            
            # Development Services
            "memory-agent": ServiceConfig(
                name="Memory Agent", port=5040, health_endpoint="/health",
                dependencies=["redis"], profile="development", build_type="image"
            ),
            "discovery-agent": ServiceConfig(
                name="Discovery Agent", port=5045, health_endpoint="/health",
                dependencies=["orchestrator"], profile="development", build_type="image"
            ),
            
            # Production Services
            "notification-service": ServiceConfig(
                name="Notification Service", port=5095, health_endpoint="/health",
                dependencies=[], profile="production", build_type="image"
            ),
            "code-analyzer": ServiceConfig(
                name="Code Analyzer", port=5085, health_endpoint="/health",
                dependencies=["redis"], profile="production", build_type="image",
                expected_issues=["aioredis_import"]
            ),
            "secure-analyzer": ServiceConfig(
                name="Secure Analyzer", port=5070, health_endpoint="/health",
                dependencies=[], profile="production", build_type="image",
                expected_issues=["aioredis_import"]
            ),
            "log-collector": ServiceConfig(
                name="Log Collector", port=5080, health_endpoint="/health",
                dependencies=[], profile="production", build_type="image"
            ),
            
            # Tooling
            "cli": ServiceConfig(
                name="CLI", port=None, health_endpoint=None,
                dependencies=["prompt-store", "orchestrator", "analysis-service"], 
                profile="tooling", build_type="dockerfile",
                expected_issues=["missing_requirements_txt"]
            )
        }
        
        self.test_results = {}
        self.issues_found = []
        
    def run_command(self, cmd: str, timeout: int = 300) -> Tuple[bool, str, str]:
        """Run a shell command and return success, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=self.project_root,
                capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)
    
    async def check_redis_health(self) -> bool:
        """Check Redis health using redis-cli."""
        success, stdout, stderr = self.run_command("docker exec hackathon-redis-1 redis-cli ping")
        return success and "PONG" in stdout
    
    async def check_http_health(self, port: int, endpoint: str, timeout: int = 5) -> bool:
        """Check HTTP health endpoint."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"http://localhost:{port}{endpoint}")
                return response.status_code == 200
        except:
            return False
    
    async def check_service_health(self, service_id: str, timeout: int = 30) -> bool:
        """Check if a service is healthy."""
        service = self.services.get(service_id)
        if not service:
            return False
        
        if service_id == "redis":
            return await self.check_redis_health()
        
        if not service.port or not service.health_endpoint:
            # Services without health endpoints (like CLI)
            return self.is_container_running(service_id)
        
        # HTTP health check with retries
        for _ in range(timeout // 2):
            if await self.check_http_health(service.port, service.health_endpoint):
                return True
            await asyncio.sleep(2)
        
        return False
    
    def is_container_running(self, service_id: str) -> bool:
        """Check if container is running."""
        success, stdout, stderr = self.run_command(f"docker ps --filter name=hackathon-{service_id.replace('_', '-')}-1 --format '{{{{.Status}}}}'")
        return success and "Up" in stdout
    
    def get_container_logs(self, service_id: str, lines: int = 50) -> str:
        """Get container logs."""
        container_name = f"hackathon-{service_id.replace('_', '-')}-1"
        success, stdout, stderr = self.run_command(f"docker logs {container_name} --tail {lines}")
        return stdout if success else f"Failed to get logs: {stderr}"
    
    def cleanup_containers(self):
        """Clean up all containers."""
        console.print("🧹 Cleaning up containers...")
        self.run_command(f"docker compose -f {self.compose_file} down --remove-orphans")
    
    async def test_individual_service(self, service_id: str) -> Dict:
        """Test a single service."""
        service = self.services[service_id]
        result = {
            "service": service_id,
            "name": service.name,
            "success": False,
            "healthy": False,
            "logs": "",
            "issues": [],
            "duration": 0
        }
        
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn(f"Testing {service.name}..."),
            console=console
        ) as progress:
            task = progress.add_task("", total=None)
            
            try:
                # Start service and dependencies
                deps = " ".join(service.dependencies + [service_id])
                success, stdout, stderr = self.run_command(
                    f"docker compose -f {self.compose_file} up -d {deps}"
                )
                
                if not success:
                    result["issues"].append(f"Failed to start: {stderr}")
                    return result
                
                # Wait for startup
                await asyncio.sleep(5)
                
                # Check if container is running
                if not self.is_container_running(service_id):
                    result["issues"].append("Container not running")
                    result["logs"] = self.get_container_logs(service_id)
                    return result
                
                # Check health
                result["healthy"] = await self.check_service_health(service_id)
                result["success"] = result["healthy"]
                
                if not result["healthy"]:
                    result["issues"].append("Health check failed")
                    result["logs"] = self.get_container_logs(service_id, 100)
                
                # Check for expected issues
                if service.expected_issues:
                    logs = self.get_container_logs(service_id, 200)
                    for expected_issue in service.expected_issues:
                        if self._check_for_issue(expected_issue, logs, stderr):
                            result["issues"].append(f"Expected issue found: {expected_issue}")
                
            except Exception as e:
                result["issues"].append(f"Test error: {str(e)}")
            
            result["duration"] = time.time() - start_time
            
        return result
    
    def _check_for_issue(self, issue_type: str, logs: str, stderr: str) -> bool:
        """Check for specific issue patterns."""
        patterns = {
            "missing_requirements_txt": "services/shared/requirements.txt\": not found",
            "aioredis_import": "'NoneType' object has no attribute 'Redis'",
            "module_import_path": "ModuleNotFoundError: No module named 'services.",
            "port_mapping": "Failed to connect",
            "import_issues": "ImportError",
            "dependency_resolution": "AttributeError"
        }
        
        pattern = patterns.get(issue_type, issue_type)
        return pattern in logs or pattern in stderr
    
    async def test_profile_services(self, profile: str) -> Dict:
        """Test all services in a profile."""
        profile_services = [
            service_id for service_id, service in self.services.items()
            if service.profile == profile
        ]
        
        console.print(f"🔍 Testing {profile} profile services: {', '.join(profile_services)}")
        
        result = {
            "profile": profile,
            "services": profile_services,
            "success": False,
            "healthy_count": 0,
            "total_count": len(profile_services),
            "issues": [],
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # Start all services in profile
            success, stdout, stderr = self.run_command(
                f"docker compose -f {self.compose_file} --profile {profile} up -d"
            )
            
            if not success:
                result["issues"].append(f"Failed to start profile: {stderr}")
                return result
            
            # Wait for startup
            await asyncio.sleep(10)
            
            # Check health of each service
            for service_id in profile_services:
                if await self.check_service_health(service_id):
                    result["healthy_count"] += 1
            
            result["success"] = result["healthy_count"] > 0
            result["duration"] = time.time() - start_time
            
        except Exception as e:
            result["issues"].append(f"Profile test error: {str(e)}")
        
        return result
    
    async def test_full_ecosystem(self) -> Dict:
        """Test starting all services together."""
        console.print("🌐 Testing full ecosystem startup...")
        
        result = {
            "test": "full_ecosystem",
            "success": False,
            "healthy_services": [],
            "failed_services": [],
            "total_services": len(self.services),
            "issues": [],
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # Try to start all profiles
            profiles = ["core", "ai_services", "development", "production", "tooling"]
            profile_args = " ".join([f"--profile {p}" for p in profiles])
            
            success, stdout, stderr = self.run_command(
                f"docker compose -f {self.compose_file} {profile_args} up -d"
            )
            
            if not success:
                result["issues"].append(f"Failed to start ecosystem: {stderr}")
                # Try core services only
                success, stdout, stderr = self.run_command(
                    f"docker compose -f {self.compose_file} --profile core up -d"
                )
                if success:
                    result["issues"].append("Core services started, full ecosystem failed")
            
            # Wait for startup
            await asyncio.sleep(15)
            
            # Check health of all services
            for service_id in self.services:
                if await self.check_service_health(service_id):
                    result["healthy_services"].append(service_id)
                else:
                    result["failed_services"].append(service_id)
            
            result["success"] = len(result["healthy_services"]) > 0
            result["duration"] = time.time() - start_time
            
        except Exception as e:
            result["issues"].append(f"Ecosystem test error: {str(e)}")
        
        return result
    
    def generate_report(self):
        """Generate comprehensive test report."""
        console.print("\n" + "=" * 80)
        console.print("📊 COMPREHENSIVE DOCKER SERVICES TEST REPORT")
        console.print("=" * 80)
        
        # Summary table
        table = Table(title="Service Test Results")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Health", style="white")
        table.add_column("Issues", style="yellow")
        table.add_column("Duration", style="white")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r.get("success", False))
        
        for service_id, result in self.test_results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            health = "🟢 Healthy" if result.get("healthy", False) else "🔴 Unhealthy"
            issues = str(len(result.get("issues", [])))
            duration = f"{result.get('duration', 0):.1f}s"
            
            table.add_row(
                self.services.get(service_id, {}).get("name", service_id),
                status, health, issues, duration
            )
        
        console.print(table)
        
        # Summary stats
        console.print(f"\n📈 Overall Results:")
        console.print(f"   • Tests run: {total_tests}")
        console.print(f"   • Passed: {passed_tests}")
        console.print(f"   • Failed: {total_tests - passed_tests}")
        console.print(f"   • Success rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Issues summary
        if self.issues_found:
            console.print(f"\n⚠️  Common Issues Found:")
            for issue in set(self.issues_found):
                console.print(f"   • {issue}")
        
        # Recommendations
        console.print(f"\n💡 Recommendations:")
        console.print(f"   • Fix missing requirements.txt for custom Dockerfiles")
        console.print(f"   • Resolve aioredis import issues in shared modules")
        console.print(f"   • Fix Python module import paths")
        console.print(f"   • Review service startup dependencies")
        
        # Save detailed report
        report_file = self.project_root / "COMPREHENSIVE_DOCKER_TEST_REPORT.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": time.time(),
                "results": self.test_results,
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": total_tests - passed_tests,
                    "success_rate": passed_tests/total_tests if total_tests > 0 else 0
                },
                "issues": self.issues_found
            }, f, indent=2)
        
        console.print(f"\n📄 Detailed report saved to: {report_file}")
    
    async def run_individual_tests(self):
        """Run tests for individual services."""
        console.print("🔍 Running individual service tests...")
        
        # Test in dependency order
        test_order = [
            "redis",  # Infrastructure first
            "orchestrator", "doc_store", "source-agent", "analysis-service", "frontend",  # Core
            "summarizer-hub", "architecture-digitizer", "bedrock-proxy", "github-mcp",  # AI (no custom Dockerfile)
            "memory-agent", "discovery-agent",  # Development
            "notification-service", "code-analyzer", "secure-analyzer", "log-collector"  # Production
        ]
        
        for service_id in test_order:
            if service_id in self.services:
                result = await self.test_individual_service(service_id)
                self.test_results[service_id] = result
                
                status = "✅" if result["success"] else "❌"
                console.print(f"{status} {result['name']}: {result.get('duration', 0):.1f}s")
                
                if result["issues"]:
                    self.issues_found.extend(result["issues"])
                
                # Cleanup between tests
                await asyncio.sleep(2)
    
    async def run_profile_tests(self):
        """Run tests for service profiles."""
        console.print("📋 Running profile tests...")
        
        profiles = ["core", "ai_services", "development", "production"]
        
        for profile in profiles:
            result = await self.test_profile_services(profile)
            self.test_results[f"profile_{profile}"] = result
            
            status = "✅" if result["success"] else "❌"
            console.print(f"{status} {profile}: {result['healthy_count']}/{result['total_count']} healthy")
    
    async def run_ecosystem_test(self):
        """Run full ecosystem test."""
        result = await self.test_full_ecosystem()
        self.test_results["ecosystem"] = result
        
        status = "✅" if result["success"] else "❌"
        console.print(f"{status} Ecosystem: {len(result['healthy_services'])}/{result['total_services']} services healthy")

async def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Docker Services Testing")
    parser.add_argument("--individual", action="store_true", help="Test individual services")
    parser.add_argument("--profiles", action="store_true", help="Test service profiles")
    parser.add_argument("--ecosystem", action="store_true", help="Test full ecosystem")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--service", help="Test specific service")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup containers before testing")
    
    args = parser.parse_args()
    
    tester = ComprehensiveDockerTester()
    
    console.print("🐳 Comprehensive Docker Services Testing Framework")
    console.print("=" * 60)
    
    if args.cleanup:
        tester.cleanup_containers()
    
    try:
        if args.service:
            result = await tester.test_individual_service(args.service)
            tester.test_results[args.service] = result
        elif args.individual or args.all:
            await tester.run_individual_tests()
        
        if args.profiles or args.all:
            await tester.run_profile_tests()
        
        if args.ecosystem or args.all:
            await tester.run_ecosystem_test()
        
        if not any([args.individual, args.profiles, args.ecosystem, args.all, args.service]):
            parser.print_help()
            return
        
        tester.generate_report()
        
    except KeyboardInterrupt:
        console.print("\n🛑 Testing interrupted by user")
    except Exception as e:
        console.print(f"\n❌ Testing failed: {e}")
    finally:
        if args.cleanup:
            tester.cleanup_containers()

if __name__ == "__main__":
    asyncio.run(main())
