#!/usr/bin/env python3
"""Integration test for the enhanced Discovery Agent service.

This script provides a comprehensive integration test that validates
all the new features and endpoints implemented in Phases 1-5.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import httpx
import pytest


class DiscoveryAgentIntegrationTest:
    """Integration test suite for Discovery Agent."""

    def __init__(self, base_url: str = "http://localhost:5045"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def test_health_endpoint(self):
        """Test the health endpoint."""
        print("🩺 Testing health endpoint...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"
            assert "service" in data
            assert data["service"] == "discovery-agent"

            print("✅ Health endpoint working")
            return True
        except Exception as e:
            print(f"❌ Health endpoint failed: {e}")
            return False

    async def test_ecosystem_discovery(self):
        """Test ecosystem discovery endpoint."""
        print("🔍 Testing ecosystem discovery...")
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/discovery/ecosystem")
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text[:200]}...")

            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data

            discovery_data = data["data"]
            assert "services_tested" in discovery_data
            assert "healthy_services" in discovery_data
            assert "total_tools_discovered" in discovery_data

            print(f"✅ Ecosystem discovery working - found {discovery_data['total_tools_discovered']} tools")
            return True
        except Exception as e:
            print(f"❌ Ecosystem discovery failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_orchestrator_registration(self):
        """Test tool registration with orchestrator."""
        print("🔗 Testing orchestrator tool registration...")
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/orchestrator/register-tools")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data

            registration_data = data["data"]
            assert "registered_tools" in registration_data
            assert "total_tools" in registration_data

            print(f"✅ Orchestrator registration working - registered {registration_data['registered_tools']} tools")
            return True
        except Exception as e:
            print(f"❌ Orchestrator registration failed: {e}")
            return False

    async def test_ai_workflow_creation(self):
        """Test AI-powered workflow creation."""
        print("🤖 Testing AI workflow creation...")
        try:
            workflow_request = {
                "task_description": "Analyze all documents and create a summary report",
                "name": "integration_test_workflow"
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/workflows/create-ai",
                json=workflow_request
            )
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data

            workflow_data = data["data"]
            assert "workflow" in workflow_data
            assert "orchestrator_result" in workflow_data

            print("✅ AI workflow creation working")
            return True
        except Exception as e:
            print(f"❌ AI workflow creation failed: {e}")
            return False

    async def test_semantic_analysis(self):
        """Test semantic analysis endpoint."""
        print("🧠 Testing semantic analysis...")
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/analysis/semantic")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data

            analysis_data = data["data"]
            assert "analyzed_tools" in analysis_data
            assert "relationship_analysis" in analysis_data

            print(f"✅ Semantic analysis working - analyzed {analysis_data['analyzed_tools']} tools")
            return True
        except Exception as e:
            print(f"❌ Semantic analysis failed: {e}")
            return False

    async def test_performance_optimization(self):
        """Test performance optimization endpoint."""
        print("⚡ Testing performance optimization...")
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/optimization/performance")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data

            optimization_data = data["data"]
            assert "analysis" in optimization_data

            print("✅ Performance optimization working")
            return True
        except Exception as e:
            print(f"❌ Performance optimization failed: {e}")
            return False

    async def test_dependency_analysis(self):
        """Test tool dependency analysis."""
        print("🔗 Testing dependency analysis...")
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/optimization/dependencies")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data

            dependency_data = data["data"]
            assert "dependency_analysis" in dependency_data

            print("✅ Dependency analysis working")
            return True
        except Exception as e:
            print(f"❌ Dependency analysis failed: {e}")
            return False

    async def test_registry_endpoints(self):
        """Test registry query endpoints."""
        print("📚 Testing registry endpoints...")

        # Test tools query
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/registry/tools")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data

            tools_data = data["data"]
            assert "tools" in tools_data
            assert "count" in tools_data

            print(f"✅ Registry tools query working - found {tools_data['count']} tools")
        except Exception as e:
            print(f"❌ Registry tools query failed: {e}")
            return False

        # Test stats query
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/registry/stats")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data

            stats_data = data["data"]
            assert "total_tools_in_registry" in stats_data

            print("✅ Registry stats query working")
            return True
        except Exception as e:
            print(f"❌ Registry stats query failed: {e}")
            return False

    async def test_monitoring_dashboard(self):
        """Test monitoring dashboard endpoint."""
        print("📊 Testing monitoring dashboard...")
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/monitoring/dashboard")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data

            dashboard_data = data["data"]
            assert "dashboard_title" in dashboard_data
            assert "health_summary" in dashboard_data

            print("✅ Monitoring dashboard working")
            return True
        except Exception as e:
            print(f"❌ Monitoring dashboard failed: {e}")
            return False

    async def test_optimization_status(self):
        """Test optimization status endpoint."""
        print("📈 Testing optimization status...")
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/optimization/status")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data

            status_data = data["data"]
            assert "registry_health" in status_data
            assert "optimization_readiness" in status_data

            print("✅ Optimization status working")
            return True
        except Exception as e:
            print(f"❌ Optimization status failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all integration tests."""
        print("🚀 Starting Discovery Agent Integration Tests")
        print("=" * 50)

        test_results = []

        # Run all tests
        tests = [
            self.test_health_endpoint,
            self.test_ecosystem_discovery,
            self.test_orchestrator_registration,
            self.test_ai_workflow_creation,
            self.test_semantic_analysis,
            self.test_performance_optimization,
            self.test_dependency_analysis,
            self.test_registry_endpoints,
            self.test_monitoring_dashboard,
            self.test_optimization_status
        ]

        for test in tests:
            result = await test()
            test_results.append(result)

        # Summary
        print("\n" + "=" * 50)
        passed = sum(test_results)
        total = len(test_results)

        print(f"📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 ALL TESTS PASSED! Discovery Agent is fully functional.")
            return True
        else:
            print(f"❌ {total - passed} tests failed. Check the output above for details.")
            return False


async def check_service_running(base_url: str = "http://localhost:5045") -> bool:
    """Check if the discovery agent service is running."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/health")
            return response.status_code == 200
    except Exception:
        return False


async def main():
    """Main test runner."""
    base_url = "http://localhost:5045"  # Discovery agent default port

    print("🔍 Checking if Discovery Agent service is running...")

    if not await check_service_running(base_url):
        print("❌ Discovery Agent service is not running on", base_url)
        print("Please start the service first:")
        print("  cd services/discovery-agent && python main.py")
        print("Or run with Docker:")
        print("  docker-compose up discovery-agent")
        return False

    print("✅ Discovery Agent service is running")

    async with DiscoveryAgentIntegrationTest(base_url) as tester:
        success = await tester.run_all_tests()

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
