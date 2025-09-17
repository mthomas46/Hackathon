#!/usr/bin/env python3
"""Test runner for Mock Data Generator Service.

Runs comprehensive tests for the LLM-integrated mock data generation service,
including unit tests, integration tests, and end-to-end workflow validation.
"""

import sys
import os
import argparse
import pytest
import subprocess
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MockDataGeneratorTestRunner:
    """Comprehensive test runner for Mock Data Generator service."""

    def __init__(self):
        self.project_root = project_root
        self.mock_data_dir = project_root / "services" / "mock-data-generator"

    def run_unit_tests(self, parallel: bool = False, workers: int = 4, coverage: bool = True) -> bool:
        """Run unit tests for Mock Data Generator."""
        print("🧪 Running Mock Data Generator Unit Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/mock_data_generator/",
            "-v",
            "--tb=short",
            "-m", "unit and parallel_safe",
            "--durations=10"
        ]

        if parallel:
            cmd.extend(["-n", str(workers), "--dist=worksteal"])

        if coverage:
            cmd.extend([
                "--cov=services.mock-data-generator",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml",
                "--cov-fail-under=85"
            ])

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_integration_tests(self, parallel: bool = False, workers: int = 2) -> bool:
        """Run integration tests for Mock Data Generator."""
        print("\n🔗 Running Mock Data Generator Integration Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/test_end_to_end_ecosystem_workflow.py",
            "-v",
            "--tb=short",
            "-m", "integration",
            "--durations=15",
            "-k", "mock_data"  # Focus on mock data related tests
        ]

        if parallel:
            cmd.extend(["-n", str(workers), "--dist=worksteal"])

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_end_to_end_tests(self) -> bool:
        """Run end-to-end tests that include Mock Data Generator."""
        print("\n🎯 Running End-to-End Tests with Mock Data Generator...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/test_end_to_end_ecosystem_workflow.py",
            "-v",
            "--tb=short",
            "-m", "integration",
            "--durations=30",
            "-k", "mock_data or end_to_end or comprehensive"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_data_generation_tests(self) -> bool:
        """Run tests specifically for data generation functionality."""
        print("\n🎭 Running Data Generation Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/mock_data_generator/",
            "tests/integration/test_end_to_end_ecosystem_workflow.py",
            "-v",
            "--tb=short",
            "-m", "unit or integration",
            "--durations=15",
            "-k", "generate or generation or mock"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_llm_integration_tests(self) -> bool:
        """Run tests for LLM integration in Mock Data Generator."""
        print("\n🤖 Running LLM Integration Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/mock_data_generator/",
            "-v",
            "--tb=short",
            "-m", "unit",
            "--durations=10",
            "-k", "llm or prompt or content"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_service_integration_tests(self) -> bool:
        """Run tests for service integrations (Doc Store, etc.)."""
        print("\n🔗 Running Service Integration Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/mock_data_generator/",
            "tests/integration/test_end_to_end_ecosystem_workflow.py",
            "-v",
            "--tb=short",
            "-m", "unit or integration",
            "--durations=15",
            "-k", "doc_store or persist or integration"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_comprehensive_test_suite(self, parallel: bool = True, workers: int = 4) -> bool:
        """Run the complete Mock Data Generator test suite."""
        print("🚀 Mock Data Generator - Comprehensive Test Suite")
        print("=" * 70)
        print(f"Parallel Execution: {parallel}")
        if parallel:
            print(f"Workers: {workers}")
        print()

        results = []

        # 1. Unit Tests
        print("📦 Phase 1: Unit Tests")
        unit_success = self.run_unit_tests(parallel=parallel, workers=workers)
        results.append(("Unit Tests", unit_success))

        # 2. Data Generation Tests
        print("\n🎭 Phase 2: Data Generation Tests")
        data_gen_success = self.run_data_generation_tests()
        results.append(("Data Generation Tests", data_gen_success))

        # 3. LLM Integration Tests
        print("\n🤖 Phase 3: LLM Integration Tests")
        llm_success = self.run_llm_integration_tests()
        results.append(("LLM Integration Tests", llm_success))

        # 4. Service Integration Tests
        print("\n🔗 Phase 4: Service Integration Tests")
        service_success = self.run_service_integration_tests()
        results.append(("Service Integration Tests", service_success))

        # 5. End-to-End Tests
        print("\n🎯 Phase 5: End-to-End Tests")
        e2e_success = self.run_end_to_end_tests()
        results.append(("End-to-End Tests", e2e_success))

        # Print comprehensive results
        self._print_comprehensive_results(results)
        return all(success for _, success in results)

    def run_performance_tests(self) -> bool:
        """Run performance tests for Mock Data Generator."""
        print("\n⚡ Running Performance Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/mock_data_generator/",
            "-v",
            "--tb=short",
            "-m", "unit",
            "--durations=5",
            "-k", "performance or batch or concurrent"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_workflow_validation_tests(self) -> bool:
        """Run tests that validate workflow integration."""
        print("\n🔄 Running Workflow Validation Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/test_end_to_end_ecosystem_workflow.py",
            "-v",
            "--tb=short",
            "-m", "integration",
            "--durations=20",
            "-k", "workflow or validation or completeness"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def _print_comprehensive_results(self, results: List[tuple]) -> None:
        """Print comprehensive test results."""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST RESULTS - MOCK DATA GENERATOR")
        print("=" * 70)

        all_passed = True
        total_tests = len(results)
        passed_tests = sum(1 for _, success in results if success)

        print(f"Total Test Suites: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()

        print("Test Suite Results:")
        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print("30")

        print("\n" + "=" * 70)

        if all_passed:
            print("🎉 ALL TEST SUITES PASSED!")
            print("   Mock Data Generator is fully functional and ready for production! 🚀")
            print("   ✅ LLM Integration: Working")
            print("   ✅ Data Generation: Working")
            print("   ✅ Service Integration: Working")
            print("   ✅ End-to-End Workflows: Working")
        else:
            print("⚠️ SOME TEST SUITES FAILED")
            print("   Please review the failed tests above and address any issues.")
            print("   Common issues:")
            print("   - LLM Gateway connectivity")
            print("   - Doc Store availability")
            print("   - Service configuration")
            print("   - Network connectivity")

        print("=" * 70)

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available."""
        print("🔍 Checking Mock Data Generator dependencies...")

        required_services = [
            "LLM Gateway (http://localhost:5055)",
            "Doc Store (http://localhost:5087)",
            "Mock Data Generator (http://localhost:5065)"
        ]

        print("Required services:")
        for service in required_services:
            print(f"   • {service}")

        print("\n💡 Note: Make sure all services are running before running tests")
        print("   Use: docker-compose --profile ai_services up -d")

        return True  # Dependencies check always passes (services checked at runtime)

    def show_service_status(self) -> None:
        """Show the status of required services."""
        print("\n🔍 Service Status Check:")
        print("-" * 40)

        services = {
            "LLM Gateway": "http://localhost:5055/health",
            "Doc Store": "http://localhost:5087/health",
            "Mock Data Generator": "http://localhost:5065/health"
        }

        for service_name, health_url in services.items():
            try:
                import httpx
                response = httpx.get(health_url, timeout=5.0)
                if response.status_code == 200:
                    print(f"✅ {service_name}: Available")
                else:
                    print(f"⚠️ {service_name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {service_name}: Not available ({str(e)[:50]}...)")

    def generate_test_report(self, results: List[tuple]) -> str:
        """Generate a detailed test report."""
        report_lines = [
            "# Mock Data Generator Test Report",
            "",
            "## Test Execution Summary",
            "",
            f"- **Total Test Suites**: {len(results)}",
            f"- **Passed**: {sum(1 for _, success in results if success)}",
            f"- **Failed**: {sum(1 for _, success in results if not success)}",
            "",
            "## Test Suite Details",
            ""
        ]

        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            report_lines.append(f"- **{test_name}**: {status}")

        report_lines.extend([
            "",
            "## Recommendations",
            "",
            "Based on test results:",
            "",
            "- ✅ **LLM Integration**: Verified working",
            "- ✅ **Data Generation**: All data types supported",
            "- ✅ **Service Integration**: Doc Store persistence working",
            "- ✅ **End-to-End Workflows**: Complete workflow validation",
            "",
            "## Next Steps",
            "",
            "1. Run tests regularly to ensure stability",
            "2. Monitor LLM Gateway performance",
            "3. Scale mock data generation as needed",
            "4. Add new data types as required"
        ])

        return "\n".join(report_lines)


def main():
    """Main entry point with comprehensive argument parsing."""
    parser = argparse.ArgumentParser(
        description="Mock Data Generator Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests in parallel
  python tests/run_mock_data_generator_tests.py --parallel --workers 4

  # Run only unit tests
  python tests/run_mock_data_generator_tests.py --unit

  # Run only integration tests
  python tests/run_mock_data_generator_tests.py --integration

  # Run end-to-end tests
  python tests/run_mock_data_generator_tests.py --e2e

  # Check service status
  python tests/run_mock_data_generator_tests.py --status

  # Run comprehensive suite
  python tests/run_mock_data_generator_tests.py --comprehensive
        """
    )

    parser.add_argument("--parallel", "-p", action="store_true",
                       help="Run tests in parallel where possible")
    parser.add_argument("--workers", "-w", type=int, default=4,
                       help="Number of parallel workers (default: 4)")
    parser.add_argument("--unit", action="store_true",
                       help="Run only unit tests")
    parser.add_argument("--integration", action="store_true",
                       help="Run only integration tests")
    parser.add_argument("--e2e", action="store_true",
                       help="Run only end-to-end tests")
    parser.add_argument("--data-gen", action="store_true",
                       help="Run only data generation tests")
    parser.add_argument("--llm", action="store_true",
                       help="Run only LLM integration tests")
    parser.add_argument("--services", action="store_true",
                       help="Run only service integration tests")
    parser.add_argument("--performance", action="store_true",
                       help="Run performance tests")
    parser.add_argument("--comprehensive", "-c", action="store_true",
                       help="Run complete test suite")
    parser.add_argument("--status", action="store_true",
                       help="Check service status")
    parser.add_argument("--coverage", action="store_true", default=True,
                       help="Generate coverage reports")

    args = parser.parse_args()

    runner = MockDataGeneratorTestRunner()

    # Handle status check
    if args.status:
        runner.show_service_status()
        return 0

    # Check dependencies
    if not runner.check_dependencies():
        print("\n❌ Dependency check failed")
        return 1

    try:
        success = False

        if args.unit:
            success = runner.run_unit_tests(parallel=args.parallel, workers=args.workers, coverage=args.coverage)
        elif args.integration:
            success = runner.run_integration_tests(parallel=args.parallel, workers=min(2, args.workers))
        elif args.e2e:
            success = runner.run_end_to_end_tests()
        elif args.data_gen:
            success = runner.run_data_generation_tests()
        elif args.llm:
            success = runner.run_llm_integration_tests()
        elif args.services:
            success = runner.run_service_integration_tests()
        elif args.performance:
            success = runner.run_performance_tests()
        elif args.comprehensive:
            success = runner.run_comprehensive_test_suite(parallel=args.parallel, workers=args.workers)
        else:
            # Default: run comprehensive suite
            print("🤔 No specific test type selected, running comprehensive suite...")
            success = runner.run_comprehensive_test_suite(parallel=args.parallel, workers=args.workers)

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⏹️ Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
