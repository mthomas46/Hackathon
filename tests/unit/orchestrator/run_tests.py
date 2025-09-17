#!/usr/bin/env python3
"""
Orchestrator Test Runner

Provides comprehensive test execution for the orchestrator service
with support for parallel execution, bounded context filtering, and reporting.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional


class OrchestratorTestRunner:
    """Test runner for orchestrator service tests."""

    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent  # Go up to project root
        self.test_dir = Path(__file__).parent  # The directory containing this script

    def run_all_tests(self, parallel: bool = True, coverage: bool = True) -> int:
        """Run all orchestrator tests."""
        cmd = self._build_pytest_command(
            paths=["."],
            parallel=parallel,
            coverage=coverage
        )
        return self._execute_command(cmd)

    def run_bounded_context_tests(
        self,
        context: str,
        layer: Optional[str] = None,
        parallel: bool = True
    ) -> int:
        """Run tests for a specific bounded context."""
        paths = [f"bounded_contexts/{context}"]
        if layer:
            paths = [f"bounded_contexts/{context}/{layer}"]

        markers = [context.replace("_", "")]
        if layer:
            markers.append(layer)

        cmd = self._build_pytest_command(
            paths=paths,
            markers=markers,
            parallel=parallel
        )
        return self._execute_command(cmd)

    def run_layer_tests(self, layer: str, parallel: bool = True) -> int:
        """Run tests for a specific architectural layer."""
        cmd = self._build_pytest_command(
            markers=[layer],
            parallel=parallel
        )
        return self._execute_command(cmd)

    def run_domain_tests(self, parallel: bool = True) -> int:
        """Run all domain layer tests."""
        return self.run_layer_tests("domain", parallel)

    def run_application_tests(self, parallel: bool = True) -> int:
        """Run all application layer tests."""
        return self.run_layer_tests("application", parallel)

    def run_infrastructure_tests(self, parallel: bool = True) -> int:
        """Run all infrastructure layer tests."""
        return self.run_layer_tests("infrastructure", parallel)

    def run_integration_tests(self, parallel: bool = False) -> int:
        """Run integration tests (typically not parallel)."""
        cmd = self._build_pytest_command(
            paths=["integration"],
            markers=["integration"],
            parallel=parallel
        )
        return self._execute_command(cmd)

    def run_fast_tests(self) -> int:
        """Run only fast tests (exclude slow and integration)."""
        cmd = self._build_pytest_command(
            markers=["-slow", "-integration", "-e2e"]
        )
        return self._execute_command(cmd)

    def run_with_coverage(self) -> int:
        """Run tests with coverage reporting."""
        cmd = self._build_pytest_command(
            coverage=True,
            html_report=True
        )
        return self._execute_command(cmd)

    def _build_pytest_command(
        self,
        paths: Optional[List[str]] = None,
        markers: Optional[List[str]] = None,
        parallel: bool = True,
        coverage: bool = False,
        html_report: bool = False
    ) -> List[str]:
        """Build pytest command with appropriate options."""
        cmd = [sys.executable, "-m", "pytest"]

        # Add paths
        if paths:
            cmd.extend(paths)
        else:
            cmd.append(".")

        # Add markers
        if markers:
            marker_expr = " and ".join(f"({m})" for m in markers)
            cmd.extend(["-m", marker_expr])

        # Parallel execution
        if parallel:
            cmd.extend(["-n", "auto"])

        # Coverage
        if coverage:
            cmd.extend([
                "--cov=services.orchestrator",
                "--cov-report=term-missing",
                "--cov-report=xml",
                "--cov-fail-under=80"
            ])
            if html_report:
                cmd.append("--cov-report=html:htmlcov")

        # Standard options
        cmd.extend([
            "--tb=short",
            "-ra",
            "--maxfail=5",
            "--strict-markers",
            "--disable-warnings",
            f"--rootdir={self.root_dir}"
        ])

        return cmd

    def _execute_command(self, cmd: List[str]) -> int:
        """Execute a command and return the exit code."""
        print(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, cwd=self.test_dir, check=False)
            return result.returncode
        except KeyboardInterrupt:
            print("\nTest execution interrupted by user")
            return 130
        except Exception as e:
            print(f"Error executing tests: {e}")
            return 1

    def list_test_structure(self):
        """List the test directory structure."""
        print("Orchestrator Test Structure:")
        print("=" * 40)

        for context_dir in sorted(self.test_dir.glob("*")):
            if context_dir.is_dir() and not context_dir.name.startswith('__'):
                print(f"\n{context_dir.name.replace('_', ' ').title()}:")
                for layer_dir in sorted(context_dir.glob("*")):
                    if layer_dir.is_dir() and not layer_dir.name.startswith('__'):
                        test_files = list(layer_dir.glob("test_*.py"))
                        print(f"  {layer_dir.name.title()}: {len(test_files)} test files")
                        for test_file in sorted(test_files):
                            print(f"    - {test_file.name}")


def main():
    """Main entry point for test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Orchestrator Test Runner")
    parser.add_argument(
        "command",
        choices=[
            "all", "fast", "coverage", "domain", "application", "infrastructure",
            "integration", "structure"
        ],
        help="Test command to run"
    )
    parser.add_argument(
        "--context",
        choices=[
            "workflow_management", "health_monitoring", "infrastructure",
            "ingestion", "service_registry", "query_processing", "reporting"
        ],
        help="Specific bounded context to test"
    )
    parser.add_argument(
        "--layer",
        choices=["domain", "application", "infrastructure", "presentation"],
        help="Specific architectural layer to test"
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel test execution"
    )

    args = parser.parse_args()

    runner = OrchestratorTestRunner()
    parallel = not args.no_parallel

    if args.command == "structure":
        runner.list_test_structure()
        return 0

    if args.context:
        if args.layer:
            return runner.run_bounded_context_tests(args.context, args.layer, parallel)
        else:
            return runner.run_bounded_context_tests(args.context, parallel=parallel)

    commands = {
        "all": lambda: runner.run_all_tests(parallel=parallel),
        "fast": runner.run_fast_tests,
        "coverage": runner.run_with_coverage,
        "domain": lambda: runner.run_domain_tests(parallel=parallel),
        "application": lambda: runner.run_application_tests(parallel=parallel),
        "infrastructure": lambda: runner.run_infrastructure_tests(parallel=parallel),
        "integration": lambda: runner.run_integration_tests(parallel=False),
    }

    return commands[args.command]()


if __name__ == "__main__":
    sys.exit(main())
