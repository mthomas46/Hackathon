#!/usr/bin/env python3
"""Test Runner for Project Simulation Service.

This script provides comprehensive test execution capabilities for the
Project Simulation Service, supporting different test categories, parallel
execution, and detailed reporting.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit            # Run unit tests only
    python run_tests.py --integration     # Run integration tests only
    python run_tests.py --performance     # Run performance tests only
    python run_tests.py --critical        # Run critical path tests only
    python run_tests.py --domain          # Run domain layer tests only
    python run_tests.py --parallel        # Run tests in parallel
    python run_tests.py --coverage        # Generate coverage report
    python run_tests.py --verbose         # Verbose output
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRunner:
    """Comprehensive test runner for the Project Simulation Service."""

    def __init__(self, project_root: Path):
        """Initialize the test runner."""
        self.project_root = project_root
        self.test_dir = project_root / "tests"
        self.coverage_dir = project_root / "htmlcov"

    def run_all_tests(self,
                     parallel: bool = False,
                     coverage: bool = True,
                     verbose: bool = False) -> int:
        """Run all tests."""
        print("🧪 Running ALL tests for Project Simulation Service")
        print("=" * 60)

        cmd = self._build_pytest_command(
            markers=None,
            parallel=parallel,
            coverage=coverage,
            verbose=verbose
        )

        return self._execute_command(cmd)

    def run_unit_tests(self,
                      parallel: bool = False,
                      coverage: bool = True,
                      verbose: bool = False) -> int:
        """Run unit tests."""
        print("🔬 Running UNIT tests")
        print("=" * 30)

        cmd = self._build_pytest_command(
            markers=["unit"],
            parallel=parallel,
            coverage=coverage,
            verbose=verbose
        )

        return self._execute_command(cmd)

    def run_integration_tests(self,
                            parallel: bool = False,
                            coverage: bool = True,
                            verbose: bool = False) -> int:
        """Run integration tests."""
        print("🔗 Running INTEGRATION tests")
        print("=" * 35)

        cmd = self._build_pytest_command(
            markers=["integration"],
            parallel=parallel,
            coverage=coverage,
            verbose=verbose
        )

        return self._execute_command(cmd)

    def run_domain_tests(self,
                        parallel: bool = False,
                        coverage: bool = True,
                        verbose: bool = False) -> int:
        """Run domain layer tests."""
        print("🏗️ Running DOMAIN layer tests")
        print("=" * 35)

        cmd = self._build_pytest_command(
            markers=["domain", "ddd"],
            parallel=parallel,
            coverage=coverage,
            verbose=verbose
        )

        return self._execute_command(cmd)

    def run_critical_tests(self,
                          parallel: bool = False,
                          coverage: bool = True,
                          verbose: bool = False) -> int:
        """Run critical path tests."""
        print("🚨 Running CRITICAL path tests")
        print("=" * 35)

        cmd = self._build_pytest_command(
            markers=["critical"],
            parallel=parallel,
            coverage=coverage,
            verbose=verbose
        )

        return self._execute_command(cmd)

    def run_performance_tests(self,
                             parallel: bool = False,
                             coverage: bool = True,
                             verbose: bool = False) -> int:
        """Run performance tests."""
        print("⚡ Running PERFORMANCE tests")
        print("=" * 35)

        cmd = self._build_pytest_command(
            markers=["performance", "slow"],
            parallel=parallel,
            coverage=coverage,
            verbose=verbose
        )

        return self._execute_command(cmd)

    def run_ddd_foundation_tests(self,
                               parallel: bool = False,
                               coverage: bool = True,
                               verbose: bool = False) -> int:
        """Run DDD Foundation tests (Phase 29)."""
        print("🏛️ Running DDD FOUNDATION tests (Phase 29)")
        print("=" * 45)

        # Run specific test files for Phase 29
        test_files = [
            "tests/unit/domain/test_project_aggregate.py",
            "tests/unit/domain/test_value_objects.py",
            "tests/unit/domain/test_domain_events.py",
            "tests/unit/domain/test_repositories.py"
        ]

        cmd = self._build_pytest_command(
            test_paths=test_files,
            parallel=parallel,
            coverage=coverage,
            verbose=verbose
        )

        return self._execute_command(cmd)

    def generate_coverage_report(self) -> None:
        """Generate and display coverage report."""
        print("📊 Generating coverage report...")
        print("=" * 35)

        if self.coverage_dir.exists():
            print(f"Coverage report available at: file://{self.coverage_dir}/index.html")
        else:
            print("No coverage report found. Run tests with --coverage flag.")

    def _build_pytest_command(self,
                            markers: Optional[List[str]] = None,
                            test_paths: Optional[List[str]] = None,
                            parallel: bool = False,
                            coverage: bool = True,
                            verbose: bool = False) -> List[str]:
        """Build pytest command with appropriate options."""
        cmd = [sys.executable, "-m", "pytest"]

        # Add test paths or markers
        if test_paths:
            cmd.extend(test_paths)
        elif markers:
            marker_expr = " or ".join(markers)
            cmd.extend(["-m", marker_expr])

        # Add parallel execution
        if parallel:
            try:
                import pytest_xdist
                cmd.extend(["-n", "auto"])
            except ImportError:
                print("⚠️  pytest-xdist not installed. Install with: pip install pytest-xdist")
                print("   Running tests sequentially...")

        # Add coverage
        if coverage:
            cmd.extend([
                "--cov=simulation",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-fail-under=80"
            ])

        # Add verbosity
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        # Add other useful options
        cmd.extend([
            "--tb=short",
            "--strict-markers",
            "--disable-warnings"
        ])

        return cmd

    def _execute_command(self, cmd: List[str]) -> int:
        """Execute a command and return the exit code."""
        try:
            print(f"Executing: {' '.join(cmd)}")
            print("-" * 60)

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=False,  # Show output in real-time
                text=True
            )

            print("-" * 60)
            if result.returncode == 0:
                print("✅ Tests completed successfully!")
            else:
                print(f"❌ Tests failed with exit code: {result.returncode}")

            return result.returncode

        except FileNotFoundError:
            print("❌ pytest not found. Please install pytest: pip install pytest")
            return 1
        except Exception as e:
            print(f"❌ Error executing tests: {e}")
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Runner for Project Simulation Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                          # Run all tests
  python run_tests.py --unit                   # Run unit tests only
  python run_tests.py --integration            # Run integration tests only
  python run_tests.py --domain                 # Run domain layer tests
  python run_tests.py --critical               # Run critical path tests
  python run_tests.py --performance            # Run performance tests
  python run_tests.py --ddd-foundation         # Run Phase 29 DDD tests
  python run_tests.py --parallel               # Run tests in parallel
  python run_tests.py --coverage               # Generate coverage report
  python run_tests.py --verbose                # Verbose output

Test Categories:
  --unit:         Unit tests (fast, isolated)
  --integration:  Integration tests (service interactions)
  --domain:       Domain layer tests (DDD, business logic)
  --critical:     Critical path tests (must pass)
  --performance:  Performance and load tests
  --ddd-foundation: Phase 29 DDD foundation tests
        """
    )

    # Test category options
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only"
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only"
    )

    parser.add_argument(
        "--domain",
        action="store_true",
        help="Run domain layer tests only"
    )

    parser.add_argument(
        "--critical",
        action="store_true",
        help="Run critical path tests only"
    )

    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests only"
    )

    parser.add_argument(
        "--ddd-foundation",
        action="store_true",
        help="Run Phase 29 DDD foundation tests"
    )

    # Execution options
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)"
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Initialize test runner
    runner = TestRunner(project_root)

    # Determine which tests to run
    test_functions = []

    if args.unit:
        test_functions.append(runner.run_unit_tests)
    elif args.integration:
        test_functions.append(runner.run_integration_tests)
    elif args.domain:
        test_functions.append(runner.run_domain_tests)
    elif args.critical:
        test_functions.append(runner.run_critical_tests)
    elif args.performance:
        test_functions.append(runner.run_performance_tests)
    elif args.ddd_foundation:
        test_functions.append(runner.run_ddd_foundation_tests)
    else:
        # Default: run all tests
        test_functions.append(runner.run_all_tests)

    # Execute tests
    exit_codes = []
    for test_func in test_functions:
        exit_code = test_func(
            parallel=args.parallel,
            coverage=args.coverage,
            verbose=args.verbose
        )
        exit_codes.append(exit_code)

        # Generate coverage report if requested
        if args.coverage and exit_code == 0:
            runner.generate_coverage_report()

    # Return the highest exit code (0 if all passed)
    final_exit_code = max(exit_codes) if exit_codes else 0

    if final_exit_code == 0:
        print("\n🎉 All tests completed successfully!")
    else:
        print(f"\n💥 Some tests failed with exit code: {final_exit_code}")

    sys.exit(final_exit_code)


if __name__ == "__main__":
    main()
