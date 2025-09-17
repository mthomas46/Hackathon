#!/usr/bin/env python3
"""Test runner for LLM Gateway Service.

Runs all unit and integration tests for the LLM Gateway service with support for parallel execution.
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


class LLMGatewayTestRunner:
    """Enhanced test runner for LLM Gateway with parallel execution support."""

    def __init__(self):
        self.project_root = project_root
        self.llm_gateway_dir = project_root / "services" / "llm-gateway"

    def run_unit_tests(self, parallel: bool = False, workers: int = 4, coverage: bool = True) -> bool:
        """Run unit tests for LLM Gateway."""
        print("🧪 Running LLM Gateway Unit Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/llm_gateway/",
            "-v",
            "--tb=short",
            "-m", "unit and parallel_safe",
            "--durations=10"
        ]

        if parallel:
            cmd.extend(["-n", str(workers), "--dist=worksteal"])

        if coverage:
            cmd.extend([
                "--cov=services.llm_gateway",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml",
                "--cov-fail-under=85"
            ])

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_integration_tests(self, parallel: bool = False, workers: int = 2) -> bool:
        """Run integration tests for LLM Gateway."""
        print("\n🔗 Running LLM Gateway Integration Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/llm_gateway/",
            "-v",
            "--tb=short",
            "-m", "integration",
            "--durations=15"
        ]

        if parallel:
            cmd.extend(["-n", str(workers), "--dist=worksteal"])

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_slow_tests(self) -> bool:
        """Run slow tests serially."""
        print("\n🐌 Running LLM Gateway Slow Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/llm_gateway/",
            "tests/integration/llm_gateway/",
            "-v",
            "--tb=short",
            "-m", "slow or serial_only",
            "--durations=0",
            "-s"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_provider_tests(self) -> bool:
        """Run tests that interact with LLM providers (serial only)."""
        print("\n🤖 Running LLM Gateway Provider Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/llm_gateway/",
            "-v",
            "--tb=short",
            "-m", "provider",
            "--durations=10",
            "-s"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_security_tests(self, parallel: bool = False, workers: int = 4) -> bool:
        """Run security-related tests."""
        print("\n🔒 Running LLM Gateway Security Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/llm_gateway/",
            "-v",
            "--tb=short",
            "-m", "security",
            "--durations=10"
        ]

        if parallel:
            cmd.extend(["-n", str(workers), "--dist=worksteal"])

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_performance_tests(self) -> bool:
        """Run performance and load tests."""
        print("\n⚡ Running LLM Gateway Performance Tests...")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/llm_gateway/",
            "-v",
            "--tb=short",
            "-m", "cache or metrics",
            "--durations=5"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0

    def run_all_tests_parallel(self, workers: int = 4, include_slow: bool = False) -> bool:
        """Run all tests with parallel execution where possible."""
        print("🚀 LLM Gateway Test Suite (Parallel Execution)")
        print("=" * 60)
        print(f"Workers: {workers}")
        print(f"Include slow tests: {include_slow}")
        print()

        results = []

        # Run fast parallel tests
        print("📦 Running parallel-safe tests...")
        parallel_success = self.run_unit_tests(parallel=True, workers=workers)
        results.append(("Parallel Unit Tests", parallel_success))

        # Run integration tests with fewer workers
        integration_success = self.run_integration_tests(parallel=True, workers=min(2, workers))
        results.append(("Parallel Integration Tests", integration_success))

        # Run security tests in parallel
        security_success = self.run_security_tests(parallel=True, workers=workers)
        results.append(("Security Tests", security_success))

        # Run performance tests
        perf_success = self.run_performance_tests()
        results.append(("Performance Tests", perf_success))

        # Run slow/serial tests if requested
        if include_slow:
            slow_success = self.run_slow_tests()
            results.append(("Slow Tests", slow_success))

            provider_success = self.run_provider_tests()
            results.append(("Provider Tests", provider_success))

        # Print results summary
        self._print_results_summary(results)
        return all(success for _, success in results)

    def run_all_tests_serial(self, coverage: bool = True) -> bool:
        """Run all tests serially for comparison."""
        print("🔄 LLM Gateway Test Suite (Serial Execution)")
        print("=" * 60)

        results = []

        unit_success = self.run_unit_tests(parallel=False, coverage=coverage)
        results.append(("Unit Tests", unit_success))

        integration_success = self.run_integration_tests(parallel=False)
        results.append(("Integration Tests", integration_success))

        security_success = self.run_security_tests(parallel=False)
        results.append(("Security Tests", security_success))

        perf_success = self.run_performance_tests()
        results.append(("Performance Tests", perf_success))

        slow_success = self.run_slow_tests()
        results.append(("Slow Tests", slow_success))

        provider_success = self.run_provider_tests()
        results.append(("Provider Tests", provider_success))

        self._print_results_summary(results)
        return all(success for _, success in results)

    def _print_results_summary(self, results: List[tuple]) -> None:
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)

        all_passed = True
        for test_name, success in results:
            status = "✅" if success else "❌"
            print("15")
            if not success:
                all_passed = False

        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 All test suites passed!")
            print("   LLM Gateway is ready for deployment! 🚀")
        else:
            print("⚠️  Some test suites failed!")
            print("   Please review the test output above for details.")

        return all_passed

    def check_dependencies(self) -> bool:
        """Check if all test dependencies are installed."""
        print("🔍 Checking test dependencies...")
        try:
            import xdist  # pytest-xdist
            import coverage  # pytest-cov
            import pytest_asyncio
            import pytest_mock
            print("✅ All test dependencies are available")
            return True
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("   Install with: pip install pytest-xdist pytest-cov")
            return False


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="LLM Gateway Test Runner")
    parser.add_argument("--parallel", "-p", action="store_true",
                       help="Run tests in parallel where possible")
    parser.add_argument("--workers", "-w", type=int, default=4,
                       help="Number of parallel workers (default: 4)")
    parser.add_argument("--serial", "-s", action="store_true",
                       help="Run all tests serially (for comparison)")
    parser.add_argument("--include-slow", action="store_true",
                       help="Include slow tests in parallel run")
    parser.add_argument("--check-deps", action="store_true",
                       help="Check if all test dependencies are installed")
    parser.add_argument("--coverage", action="store_true", default=True,
                       help="Generate coverage reports")

    args = parser.parse_args()

    runner = LLMGatewayTestRunner()

    # Check dependencies first
    if args.check_deps or not runner.check_dependencies():
        if not args.check_deps:
            print("\n💡 Tip: Install missing dependencies with:")
            print("   pip install -r services/llm-gateway/requirements.txt")
            return 1
        return 0

    try:
        if args.serial:
            success = runner.run_all_tests_serial(coverage=args.coverage)
        elif args.parallel:
            success = runner.run_all_tests_parallel(
                workers=args.workers,
                include_slow=args.include_slow
            )
        else:
            # Default: run parallel tests
            print("🤔 No execution mode specified, running parallel tests...")
            success = runner.run_all_tests_parallel(workers=args.workers)

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
