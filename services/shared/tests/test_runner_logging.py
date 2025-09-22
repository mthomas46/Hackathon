#!/usr/bin/env python3
"""Comprehensive test runner for all logging functionality.

This script runs all logging-related tests across the ecosystem and provides
detailed reporting on test results, coverage, and any issues found.

Features:
- Runs tests for LogCollectorClient, enhanced log collector, and service integrations
- Provides detailed test reporting with failure analysis
- Measures test coverage for logging functionality
- Validates logging integration across services
- Generates summary reports for CI/CD integration

Usage:
    python test_runner_logging.py [--verbose] [--coverage] [--services SERVICE_LIST]

Examples:
    python test_runner_logging.py  # Run all logging tests
    python test_runner_logging.py --verbose  # Detailed output
    python test_runner_logging.py --coverage  # Include coverage report
    python test_runner_logging.py --services interpreter,memory-agent  # Test specific services
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class LoggingTestRunner:
    """Comprehensive test runner for logging functionality."""

    def __init__(self, verbose: bool = False, coverage: bool = False, services: Optional[List[str]] = None):
        """Initialize the test runner.

        Args:
            verbose: Enable verbose output
            coverage: Enable coverage reporting
            services: List of specific services to test (None = all)
        """
        self.verbose = verbose
        self.coverage = coverage
        self.services = services or []
        self.test_results = {}
        self.start_time = None
        self.end_time = None

        # Test categories and their corresponding test files
        self.test_categories = {
            "log_collector_client": {
                "name": "Log Collector Client",
                "path": "services/shared/tests/test_logging_client.py",
                "description": "Tests for the centralized logging client",
            },
            "log_collector_enhanced": {
                "name": "Enhanced Log Collector",
                "path": "services/log-collector/tests/test_log_collector_enhanced.py",
                "description": "Tests for enhanced log storage, search, and analytics",
            },
            "interpreter_logging": {
                "name": "Interpreter Service Logging",
                "path": "services/interpreter/tests/test_logging_integration.py",
                "description": "Tests for interpreter service logging integration",
            },
            "analysis_service_logging": {
                "name": "Analysis Service Logging",
                "path": "services/analysis-service/tests/test_logging_integration.py",
                "description": "Tests for analysis service logging integration",
            },
            "llm_gateway_logging": {
                "name": "LLM Gateway Logging",
                "path": "services/llm-gateway/tests/test_logging_integration.py",
                "description": "Tests for LLM gateway logging integration",
            },
            "discovery_agent_logging": {
                "name": "Discovery Agent Logging",
                "path": "services/discovery-agent/tests/test_logging_integration.py",
                "description": "Tests for discovery agent logging integration",
            },
            "notification_service_logging": {
                "name": "Notification Service Logging",
                "path": "services/notification-service/tests/test_logging_integration.py",
                "description": "Tests for notification service logging integration",
            },
            "mock_data_generator_logging": {
                "name": "Mock Data Generator Logging",
                "path": "services/mock-data-generator/tests/test_logging_integration.py",
                "description": "Tests for mock data generator logging integration",
            },
            "code_analyzer_logging": {
                "name": "Code Analyzer Logging",
                "path": "services/code-analyzer/tests/test_logging_integration.py",
                "description": "Tests for code analyzer logging integration",
            },
            "bedrock_proxy_logging": {
                "name": "Bedrock Proxy Logging",
                "path": "services/bedrock-proxy/tests/test_logging_integration.py",
                "description": "Tests for bedrock proxy logging integration",
            },
            "architecture_digitizer_logging": {
                "name": "Architecture Digitizer Logging",
                "path": "services/architecture-digitizer/tests/test_logging_integration.py",
                "description": "Tests for architecture digitizer logging integration",
            },
            "cli_logging": {
                "name": "CLI Service Logging",
                "path": "services/cli/tests/test_logging_integration.py",
                "description": "Tests for CLI service logging integration",
            },
            "github_mcp_logging": {
                "name": "GitHub MCP Logging",
                "path": "services/github-mcp/tests/test_logging_integration.py",
                "description": "Tests for GitHub MCP logging integration",
            },
            "project_simulation_logging": {
                "name": "Project Simulation Logging",
                "path": "services/project-simulation/tests/test_logging_integration.py",
                "description": "Tests for project simulation logging integration",
            },
            "secure_analyzer_logging": {
                "name": "Secure Analyzer Logging",
                "path": "services/secure-analyzer/tests/test_logging_integration.py",
                "description": "Tests for secure analyzer logging integration",
            },
            "source_agent_logging": {
                "name": "Source Agent Logging",
                "path": "services/source-agent/tests/test_logging_integration.py",
                "description": "Tests for source agent logging integration",
            },
            "summarizer_hub_logging": {
                "name": "Summarizer Hub Logging",
                "path": "services/summarizer-hub/tests/test_logging_integration.py",
                "description": "Tests for summarizer hub logging integration",
            },
            "frontend_logging": {
                "name": "Frontend Logging",
                "path": "services/frontend/tests/test_logging_integration.py",
                "description": "Tests for frontend logging integration",
            },
            "orchestrator_infrastructure_logging": {
                "name": "Orchestrator Infrastructure Logging",
                "path": "services/orchestrator/tests/test_infrastructure_logging_integration.py",
                "description": "Tests for orchestrator infrastructure routes logging integration",
            },
            "orchestrator_service_registry_logging": {
                "name": "Orchestrator Service Registry Logging",
                "path": "services/orchestrator/tests/test_service_registry_logging_integration.py",
                "description": "Tests for orchestrator service registry routes logging integration",
            },
            "orchestrator_ingestion_logging": {
                "name": "Orchestrator Ingestion Logging",
                "path": "services/orchestrator/tests/test_ingestion_logging_integration.py",
                "description": "Tests for orchestrator ingestion routes logging integration",
            },
            "orchestrator_query_processing_logging": {
                "name": "Orchestrator Query Processing Logging",
                "path": "services/orchestrator/tests/test_query_processing_logging_integration.py",
                "description": "Tests for orchestrator query processing routes logging integration",
            },
            "orchestrator_reporting_logging": {
                "name": "Orchestrator Reporting Logging",
                "path": "services/orchestrator/tests/test_reporting_logging_integration.py",
                "description": "Tests for orchestrator reporting routes logging integration",
            },
            "orchestrator_workflow_management_logging": {
                "name": "Orchestrator Workflow Management Logging",
                "path": "services/orchestrator/tests/test_workflow_management_logging_integration.py",
                "description": "Tests for orchestrator workflow management routes logging integration",
            },
            "prompt_store_handlers_logging": {
                "name": "Prompt Store Handlers Logging",
                "path": "services/prompt_store/tests/test_prompt_store_handlers_logging_integration.py",
                "description": "Tests for prompt store additional handlers logging integration",
            },
            "doc_store_handlers_logging": {
                "name": "Doc Store Handlers Logging",
                "path": "services/doc_store/tests/test_doc_store_handlers_logging_integration.py",
                "description": "Tests for doc store additional handlers logging integration",
            },
            # Future: Add more service logging tests
            # "orchestrator_logging": {
            #     "name": "Orchestrator Service Logging",
            #     "path": "services/orchestrator/tests/test_logging_integration.py",
            # },
        }

        # Filter test categories if specific services requested
        if self.services:
            filtered_categories = {}
            for service in self.services:
                for category_key, category_info in self.test_categories.items():
                    if service.lower() in category_key:
                        filtered_categories[category_key] = category_info
            self.test_categories = filtered_categories

    def run_tests(self) -> bool:
        """Run all logging tests and return success status.

        Returns:
            True if all tests pass, False otherwise
        """
        self.start_time = time.time()
        print("🚀 Starting Logging Functionality Tests")
        print("=" * 60)

        if self.services:
            print(f"📋 Testing specific services: {', '.join(self.services)}")
        else:
            print("📋 Testing all logging functionality")

        if self.coverage:
            print("📊 Coverage reporting enabled")

        print()

        success = True
        total_tests = 0
        total_passed = 0
        total_failed = 0

        for category_key, category_info in self.test_categories.items():
            print(f"🔍 Running {category_info['name']} tests...")
            if self.verbose:
                print(f"   Description: {category_info['description']}")
                print(f"   Test file: {category_info['path']}")

            result = self._run_test_category(category_key, category_info)

            self.test_results[category_key] = result
            total_tests += result["tests_run"]
            total_passed += result["tests_passed"]
            total_failed += result["tests_failed"]

            if not result["success"]:
                success = False

            print()

        self.end_time = time.time()
        self._print_summary(total_tests, total_passed, total_failed, success)

        return success

    def _run_test_category(self, category_key: str, category_info: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests for a specific category.

        Args:
            category_key: Test category identifier
            category_info: Test category information

        Returns:
            Test results dictionary
        """
        test_file = category_info["path"]

        if not os.path.exists(test_file):
            print(f"   ⚠️  Test file not found: {test_file}")
            return {
                "success": False,
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "error": f"Test file not found: {test_file}",
            }

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest", test_file, "-v"]

        if not self.verbose:
            cmd.append("-q")  # Quiet mode unless verbose requested

        if self.coverage:
            cmd.extend(["--cov=services", "--cov-report=term-missing", f"--cov-report=html:htmlcov_{category_key}"])

        # Set environment variables for testing
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)
        env["LOGGING_TEST_MODE"] = "1"

        try:
            if self.verbose:
                print(f"   🏃 Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.parent.parent,
                env=env,
                capture_output=not self.verbose,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # Parse pytest output to extract test counts
            tests_run, tests_passed, tests_failed = self._parse_pytest_output(result.stdout, result.stderr)

            success = result.returncode == 0

            if success:
                print(f"   ✅ {category_info['name']} tests passed ({tests_passed}/{tests_run})")
            else:
                print(f"   ❌ {category_info['name']} tests failed ({tests_failed}/{tests_run} failed)")
                if not self.verbose and result.stderr:
                    print(f"   Error: {result.stderr.strip()[:200]}...")

            return {
                "success": success,
                "tests_run": tests_run,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "return_code": result.returncode,
                "stdout": result.stdout if self.verbose else None,
                "stderr": result.stderr if self.verbose else None,
            }

        except subprocess.TimeoutExpired:
            print(f"   ⏰ {category_info['name']} tests timed out")
            return {
                "success": False,
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "error": "Test execution timed out",
            }
        except Exception as e:
            print(f"   💥 {category_info['name']} tests failed with exception: {e}")
            return {"success": False, "tests_run": 0, "tests_passed": 0, "tests_failed": 0, "error": str(e)}

    def _parse_pytest_output(self, stdout: str, stderr: str) -> tuple[int, int, int]:
        """Parse pytest output to extract test counts.

        Args:
            stdout: Standard output from pytest
            stderr: Standard error from pytest

        Returns:
            Tuple of (tests_run, tests_passed, tests_failed)
        """
        output = stdout + stderr

        # Look for pytest summary lines
        lines = output.split("\n")
        for line in reversed(lines):
            line = line.strip()
            if line.startswith("=") and ("passed" in line or "failed" in line):
                # Example: "5 passed, 2 failed, 1 error in 1.23s"
                parts = line.split(",")
                tests_run = 0
                tests_passed = 0
                tests_failed = 0

                for part in parts:
                    part = part.strip()
                    if "passed" in part:
                        tests_passed = int(part.split()[0])
                        tests_run += tests_passed
                    elif "failed" in part:
                        tests_failed = int(part.split()[0])
                        tests_run += tests_failed
                    elif "error" in part:
                        tests_failed += int(part.split()[0])
                        tests_run += int(part.split()[0])

                return tests_run, tests_passed, tests_failed

        # Fallback: try to count from individual test results
        passed_count = output.count(". ")
        failed_count = output.count("F ") + output.count("E ")

        return passed_count + failed_count, passed_count, failed_count

    def _print_summary(self, total_tests: int, total_passed: int, total_failed: int, success: bool):
        """Print comprehensive test summary.

        Args:
            total_tests: Total number of tests run
            total_passed: Number of tests that passed
            total_failed: Number of tests that failed
            success: Overall success status
        """
        duration = self.end_time - self.start_time

        print("=" * 60)
        print("📊 LOGGING TESTS SUMMARY")
        print("=" * 60)

        print(f"⏱️  Total execution time: {duration:.2f} seconds")
        print(f"🧪 Total tests run: {total_tests}")
        print(f"✅ Tests passed: {total_passed}")
        print(f"❌ Tests failed: {total_failed}")

        if total_tests > 0:
            pass_rate = (total_passed / total_tests) * 100
            print(f"📈 Pass rate: {pass_rate:.1f}%")
        print()

        # Category breakdown
        print("📋 Category Results:")
        for category_key, result in self.test_results.items():
            category_name = self.test_categories[category_key]["name"]
            status = "✅" if result["success"] else "❌"
            tests_run = result["tests_run"]
            tests_passed = result["tests_passed"]
            tests_failed = result["tests_failed"]

            print(f"   {status} {category_name}: {tests_passed}/{tests_run} passed")

            if not result["success"] and "error" in result:
                print(f"      Error: {result['error']}")

        print()

        if success:
            print("🎉 ALL LOGGING TESTS PASSED!")
            print("✅ Logging functionality is working correctly across all tested services.")
        else:
            print("⚠️  SOME LOGGING TESTS FAILED!")
            print("❌ Please review the failed tests and fix any issues before deploying.")

        if self.coverage:
            print("\n📈 Coverage reports generated in htmlcov_* directories")

        print()

    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate a detailed test report.

        Args:
            output_file: Optional file path to save the report

        Returns:
            Report data dictionary
        """
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_run": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "duration_seconds": self.end_time - self.start_time if self.end_time else None,
                "services_tested": self.services or ["all"],
                "coverage_enabled": self.coverage,
                "verbose_mode": self.verbose,
            },
            "results": {
                "overall_success": all(result["success"] for result in self.test_results.values()),
                "categories_tested": len(self.test_results),
                "total_tests_run": sum(result["tests_run"] for result in self.test_results.values()),
                "total_tests_passed": sum(result["tests_passed"] for result in self.test_results.values()),
                "total_tests_failed": sum(result["tests_failed"] for result in self.test_results.values()),
            },
            "category_results": self.test_results,
            "recommendations": self._generate_recommendations(),
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"📄 Detailed report saved to: {output_file}")

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        failed_categories = [category for category, result in self.test_results.items() if not result["success"]]

        if failed_categories:
            recommendations.append(f"Fix failing tests in categories: {', '.join(failed_categories)}")

        # Check for low test coverage
        total_tests = sum(result["tests_run"] for result in self.test_results.values())
        if total_tests < 20:  # Arbitrary threshold
            recommendations.append("Consider adding more comprehensive tests for better coverage")

        # Check for specific service gaps
        tested_services = set()
        for category_key in self.test_results.keys():
            if "_logging" in category_key:
                service_name = category_key.replace("_logging", "")
                tested_services.add(service_name)

        all_services = {"interpreter", "orchestrator", "memory_agent", "prompt_store", "doc_store", "dashboard"}
        missing_services = all_services - tested_services

        if missing_services:
            recommendations.append(f"Add logging tests for services: {', '.join(missing_services)}")

        if not recommendations:
            recommendations.append("All logging tests passed successfully!")

        return recommendations


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for logging functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner_logging.py
  python test_runner_logging.py --verbose --coverage
  python test_runner_logging.py --services interpreter memory-agent
  python test_runner_logging.py --report results.json
        """,
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    parser.add_argument("--coverage", "-c", action="store_true", help="Enable coverage reporting")

    parser.add_argument(
        "--services", "-s", nargs="+", help="Test only specific services (e.g., interpreter memory-agent)"
    )

    parser.add_argument("--report", "-r", help="Generate detailed JSON report to specified file")

    args = parser.parse_args()

    # Create and run test runner
    runner = LoggingTestRunner(verbose=args.verbose, coverage=args.coverage, services=args.services)

    success = runner.run_tests()

    if args.report:
        runner.generate_report(args.report)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
