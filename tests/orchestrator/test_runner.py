#!/usr/bin/env python3
"""
Orchestrator Service Test Runner

Comprehensive test runner for all orchestrator service tests.
Runs unit tests, integration tests, API tests, and performance tests.
"""

import asyncio
import pytest
import sys
import os
import time
import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

# Add services to path
sys.path.insert(0, '/Users/mykalthomas/Documents/work/Hackathon/services')


class OrchestratorTestRunner:
    """Comprehensive test runner for orchestrator service."""

    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None

    def discover_test_files(self) -> List[str]:
        """Discover all test files in the orchestrator test directory."""
        test_dir = Path(__file__).parent / "orchestrator"
        test_files = []

        if test_dir.exists():
            for file_path in test_dir.glob("test_*.py"):
                test_files.append(str(file_path))

        return test_files

    async def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests for orchestrator components."""
        print("🧪 Running Unit Tests...")

        test_files = [
            "tests/orchestrator/test_orchestrator_features.py::TestOrchestratorWorkflowManagement",
            "tests/orchestrator/test_orchestrator_features.py::TestOrchestratorEventStreaming",
            "tests/orchestrator/test_orchestrator_features.py::TestOrchestratorServiceMesh",
            "tests/orchestrator/test_orchestrator_features.py::TestOrchestratorEnterpriseIntegration",
            "tests/orchestrator/test_orchestrator_features.py::TestOrchestratorHealthMonitoring"
        ]

        return await self._run_pytest_async(test_files, "unit_tests")

    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests for orchestrator scenarios."""
        print("🔗 Running Integration Tests...")

        test_files = [
            "tests/orchestrator/test_integration_scenarios.py::TestDocumentAnalysisWorkflow",
            "tests/orchestrator/test_integration_scenarios.py::TestPRConfidenceAnalysisWorkflow",
            "tests/orchestrator/test_integration_scenarios.py::TestMultiServiceOrchestration",
            "tests/orchestrator/test_integration_scenarios.py::TestEventDrivenWorkflows",
            "tests/orchestrator/test_integration_scenarios.py::TestWorkflowPerformanceAndScalability"
        ]

        return await self._run_pytest_async(test_files, "integration_tests")

    async def run_api_tests(self) -> Dict[str, Any]:
        """Run API endpoint tests."""
        print("🌐 Running API Tests...")

        test_files = [
            "tests/orchestrator/test_api_endpoints.py::TestWorkflowAPICreate",
            "tests/orchestrator/test_api_endpoints.py::TestWorkflowAPIRead",
            "tests/orchestrator/test_api_endpoints.py::TestWorkflowAPIUpdate",
            "tests/orchestrator/test_api_endpoints.py::TestWorkflowAPIDelete",
            "tests/orchestrator/test_api_endpoints.py::TestWorkflowAPIExecution",
            "tests/orchestrator/test_api_endpoints.py::TestWorkflowAPISearch",
            "tests/orchestrator/test_api_endpoints.py::TestWorkflowAPIStatistics",
            "tests/orchestrator/test_api_endpoints.py::TestWorkflowAPIHealth",
            "tests/orchestrator/test_api_endpoints.py::TestWorkflowAPITemplates"
        ]

        return await self._run_pytest_async(test_files, "api_tests")

    async def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance and load tests."""
        print("⚡ Running Performance Tests...")

        test_files = [
            "tests/orchestrator/test_orchestrator_features.py::TestOrchestratorPerformance",
            "tests/orchestrator/test_integration_scenarios.py::TestWorkflowPerformanceAndScalability"
        ]

        return await self._run_pytest_async(test_files, "performance_tests")

    async def run_error_handling_tests(self) -> Dict[str, Any]:
        """Run error handling and edge case tests."""
        print("🚨 Running Error Handling Tests...")

        test_files = [
            "tests/orchestrator/test_orchestrator_features.py::TestOrchestratorErrorHandling"
        ]

        return await self._run_pytest_async(test_files, "error_handling_tests")

    async def _run_pytest_async(self, test_files: List[str], test_category: str) -> Dict[str, Any]:
        """Run pytest asynchronously for given test files."""
        # Filter out files that don't exist
        existing_files = []
        for test_file in test_files:
            file_path = test_file.split("::")[0]
            if os.path.exists(file_path):
                existing_files.append(test_file)

        if not existing_files:
            return {
                "status": "skipped",
                "reason": "No test files found",
                "tests_run": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0
            }

        # Run tests using pytest programmatically
        try:
            # Import pytest components
            import pytest_asyncio
            from _pytest.config import Config
            from _pytest.python import Module
            from _pytest.main import Session

            # This is a simplified approach - in practice, you might want to use
            # pytest's programmatic API more directly
            import subprocess

            # Run pytest as subprocess for each test file
            results = []
            for test_file in existing_files:
                try:
                    # Run individual test class/method
                    cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short", "--disable-warnings"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                    results.append({
                        "test": test_file,
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    })

                except subprocess.TimeoutExpired:
                    results.append({
                        "test": test_file,
                        "returncode": -1,
                        "error": "Test timed out"
                    })
                except Exception as e:
                    results.append({
                        "test": test_file,
                        "returncode": -1,
                        "error": str(e)
                    })

            # Analyze results
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r["returncode"] == 0)
            failed_tests = total_tests - passed_tests

            return {
                "status": "completed",
                "tests_run": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "results": results
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "tests_run": 0,
                "passed": 0,
                "failed": 0
            }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories."""
        self.start_time = time.time()

        print("🚀 STARTING COMPREHENSIVE ORCHESTRATOR TEST SUITE")
        print("=" * 80)
        print(f"Test Start Time: {datetime.now().isoformat()}")
        print()

        # Run all test categories
        test_categories = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("API Tests", self.run_api_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Error Handling Tests", self.run_error_handling_tests)
        ]

        all_results = {}

        for category_name, test_func in test_categories:
            print(f"\n{'='*20} {category_name.upper()} {'='*20}")
            try:
                results = await test_func()
                all_results[category_name.lower().replace(" ", "_")] = results

                if results["status"] == "completed":
                    passed = results.get("passed", 0)
                    total = results.get("tests_run", 0)
                    print(f"✅ {category_name}: {passed}/{total} tests passed")
                elif results["status"] == "skipped":
                    print(f"⏭️  {category_name}: Skipped - {results.get('reason', 'N/A')}")
                else:
                    print(f"❌ {category_name}: Failed - {results.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"❌ {category_name}: Error - {e}")
                all_results[category_name.lower().replace(" ", "_")] = {
                    "status": "error",
                    "error": str(e)
                }

        self.end_time = time.time()

        # Generate comprehensive report
        return self._generate_test_report(all_results)

    def _generate_test_report(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_time = self.end_time - self.start_time

        # Calculate overall statistics
        total_tests_run = 0
        total_passed = 0
        total_failed = 0
        category_status = {}

        for category, results in all_results.items():
            if results.get("status") == "completed":
                total_tests_run += results.get("tests_run", 0)
                total_passed += results.get("passed", 0)
                total_failed += results.get("failed", 0)
                category_status[category] = "passed" if results.get("passed", 0) > 0 else "failed"
            elif results.get("status") == "skipped":
                category_status[category] = "skipped"
            else:
                category_status[category] = "error"
                total_failed += 1

        overall_success_rate = (total_passed / total_tests_run * 100) if total_tests_run > 0 else 0

        report = {
            "summary": {
                "total_execution_time": total_time,
                "total_tests_run": total_tests_run,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "overall_success_rate": overall_success_rate,
                "test_timestamp": datetime.now().isoformat(),
                "categories_tested": len(all_results)
            },
            "category_results": all_results,
            "category_status": category_status,
            "recommendations": self._generate_recommendations(
                overall_success_rate, category_status
            )
        }

        return report

    def _generate_recommendations(self, success_rate: float, category_status: Dict[str, str]) -> List[str]:
        """Generate test recommendations based on results."""
        recommendations = []

        if success_rate < 50:
            recommendations.append("⚠️  CRITICAL: Overall test success rate is below 50%. Immediate attention required.")
            recommendations.append("   • Review failing tests and fix underlying issues")
            recommendations.append("   • Check test environment setup and dependencies")
            recommendations.append("   • Verify service connectivity and configuration")

        elif success_rate < 75:
            recommendations.append("⚠️  WARNING: Test success rate is below 75%. Issues need attention.")
            recommendations.append("   • Address failing test categories")
            recommendations.append("   • Review error messages for common patterns")
            recommendations.append("   • Consider test isolation and mocking improvements")

        else:
            recommendations.append("✅ GOOD: Test success rate is above 75%. System is functioning well.")
            if success_rate < 90:
                recommendations.append("   • Minor improvements possible in failing areas")
            else:
                recommendations.append("   • Excellent test coverage and system stability")

        # Category-specific recommendations
        failed_categories = [cat for cat, status in category_status.items() if status == "failed"]
        if failed_categories:
            recommendations.append(f"   • Focus on these failing categories: {', '.join(failed_categories)}")

        error_categories = [cat for cat, status in category_status.items() if status == "error"]
        if error_categories:
            recommendations.append(f"   • Fix errors in these categories: {', '.join(error_categories)}")

        return recommendations

    def print_test_report(self, report: Dict[str, Any]):
        """Print formatted test report."""
        print("\n" + "=" * 80)
        print("📊 ORCHESTRATOR TEST SUITE REPORT")
        print("=" * 80)

        summary = report["summary"]

        print("\n🎯 EXECUTION SUMMARY:")
        print(".2f")
        print(f"   Tests Run: {summary['total_tests_run']}")
        print(f"   Tests Passed: {summary['total_passed']}")
        print(f"   Tests Failed: {summary['total_failed']}")
        print(".1f")
        print(f"   Categories Tested: {summary['categories_tested']}")

        print("\n📋 CATEGORY RESULTS:")
        for category, results in report["category_results"].items():
            status = results.get("status", "unknown")
            if status == "completed":
                passed = results.get("passed", 0)
                total = results.get("tests_run", 0)
                print(f"   ✅ {category.replace('_', ' ').title()}: {passed}/{total} passed")
            elif status == "skipped":
                print(f"   ⏭️  {category.replace('_', ' ').title()}: Skipped")
            else:
                print(f"   ❌ {category.replace('_', ' ').title()}: {status}")

        print("\n💡 RECOMMENDATIONS:")
        for recommendation in report["recommendations"]:
            print(f"   {recommendation}")

        print("\n🏆 FINAL ASSESSMENT:")
        success_rate = summary["overall_success_rate"]
        if success_rate >= 95:
            print("   🏆 EXCELLENT - All systems operational with high reliability!")
        elif success_rate >= 90:
            print("   ✅ VERY GOOD - System performing well with minor issues.")
        elif success_rate >= 80:
            print("   ✅ GOOD - System functional with acceptable performance.")
        elif success_rate >= 70:
            print("   ⚠️  NEEDS ATTENTION - Some issues require resolution.")
        else:
            print("   ❌ REQUIRES IMMEDIATE ATTENTION - Critical issues present.")

        print(f"\n🕒 Report Generated: {summary['test_timestamp']}")
        print("=" * 80)


async def run_smoke_tests():
    """Run basic smoke tests for orchestrator functionality."""
    print("🚀 Running Orchestrator Smoke Tests...")

    try:
        # Add services to path
        import sys
        sys.path.insert(0, "/Users/mykalthomas/Documents/work/Hackathon/services")

        from orchestrator.modules.workflow_management.service import WorkflowManagementService

        # Test basic workflow service functionality
        workflow_service = WorkflowManagementService()

        # Create simple test workflow
        workflow_data = {
            "name": "Smoke Test Workflow",
            "description": "Basic smoke test for orchestrator",
            "parameters": [
                {
                    "name": "test_input",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "smoke_action",
                    "action_type": "notification",
                    "name": "Smoke Test Action",
                    "config": {
                        "message": "Smoke test successful: {{test_input}}"
                    }
                }
            ]
        }

        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "smoke_test_user"
        )

        if success:
            print("✅ Smoke Test PASSED - Basic orchestrator functionality working")
            return True
        else:
            print(f"❌ Smoke Test FAILED - {message}")
            return False

    except Exception as e:
        print(f"❌ Smoke Test ERROR - {e}")
        return False


async def main():
    """Main test runner function."""
    # Add services to path
    import sys
    sys.path.insert(0, "/Users/mykalthomas/Documents/work/Hackathon/services")

    import argparse

    parser = argparse.ArgumentParser(description="Orchestrator Service Test Runner")
    parser.add_argument("--smoke", action="store_true", help="Run only smoke tests")
    parser.add_argument("--category", choices=["unit", "integration", "api", "performance", "error"],
                       help="Run specific test category")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.smoke:
        # Run only smoke tests
        success = await run_smoke_tests()
        if success:
            print("\n🎉 Smoke tests passed! Orchestrator is ready.")
        else:
            print("\n❌ Smoke tests failed! Check orchestrator setup.")
        return

    # Run comprehensive test suite
    test_runner = OrchestratorTestRunner()

    if args.category:
        # Run specific category
        category_map = {
            "unit": test_runner.run_unit_tests,
            "integration": test_runner.run_integration_tests,
            "api": test_runner.run_api_tests,
            "performance": test_runner.run_performance_tests,
            "error": test_runner.run_error_handling_tests
        }

        print(f"🧪 Running {args.category} tests...")
        results = await category_map[args.category]()

        print(f"\n📊 {args.category.upper()} TEST RESULTS:")
        print(f"   Status: {results.get('status', 'unknown')}")
        if results.get("status") == "completed":
            print(f"   Tests Run: {results.get('tests_run', 0)}")
            print(f"   Passed: {results.get('passed', 0)}")
            print(f"   Failed: {results.get('failed', 0)}")

    else:
        # Run all tests
        report = await test_runner.run_all_tests()
        test_runner.print_test_report(report)

        # Save detailed report to file
        report_file = f"orchestrator_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
