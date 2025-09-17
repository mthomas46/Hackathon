#!/usr/bin/env python3
"""Comprehensive Test Suite Runner for LLM Documentation Ecosystem.

Executes all test suites including the newly created comprehensive coverage
for Frontend, Analysis Service, Interpreter, Summarizer Hub, Source Agent,
and Code Analyzer services. Provides detailed reporting and parallel execution.
"""

import sys
import os
import argparse
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import json


@dataclass
class TestSuite:
    """Represents a test suite with its configuration."""
    name: str
    path: str
    description: str
    marker: str = ""
    timeout: int = 300
    parallel_safe: bool = True


@dataclass
class TestResult:
    """Represents the result of a test suite execution."""
    suite: TestSuite
    success: bool
    duration: float
    output: str
    error_output: str
    test_count: int = 0
    failure_count: int = 0


class ComprehensiveTestRunner:
    """Comprehensive test runner for the entire ecosystem."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_suites = self._define_test_suites()

    def _define_test_suites(self) -> List[TestSuite]:
        """Define all available test suites."""
        return [
            # Unit Test Suites
            TestSuite(
                name="Frontend Service",
                path="tests/unit/frontend/",
                description="UI handlers, routing, and user interface logic",
                marker="frontend",
                parallel_safe=True
            ),
            TestSuite(
                name="Analysis Service",
                path="tests/unit/analysis_service/",
                description="AI-powered document analysis and quality assessment",
                marker="analysis_service",
                parallel_safe=True
            ),
            TestSuite(
                name="Interpreter Service",
                path="tests/unit/interpreter/",
                description="Natural language processing and workflow interpretation",
                marker="interpreter",
                parallel_safe=True
            ),
            TestSuite(
                name="Summarizer Hub",
                path="tests/unit/summarizer_hub/",
                description="Multi-model LLM summarization and provider management",
                marker="summarizer_hub",
                parallel_safe=True
            ),
            TestSuite(
                name="Source Agent",
                path="tests/unit/source_agent/",
                description="Data ingestion from GitHub, Jira, and Confluence",
                marker="source_agent",
                parallel_safe=True
            ),
            TestSuite(
                name="Code Analyzer",
                path="tests/unit/code_analyzer/",
                description="Code analysis, security scanning, and documentation generation",
                marker="code_analyzer",
                parallel_safe=True
            ),
            TestSuite(
                name="LLM Gateway",
                path="tests/unit/llm_gateway/",
                description="LLM provider routing, caching, and security",
                marker="llm_gateway",
                parallel_safe=True
            ),
            TestSuite(
                name="Mock Data Generator",
                path="tests/unit/mock_data_generator/",
                description="LLM-integrated mock data generation",
                marker="mock_data_generator",
                parallel_safe=True
            ),

            # Integration Test Suites
            TestSuite(
                name="End-to-End Workflow",
                path="tests/integration/test_end_to_end_ecosystem_workflow.py",
                description="Complete workflow from mock data to final report",
                marker="integration",
                parallel_safe=False,
                timeout=600
            ),
            TestSuite(
                name="Multi-Source Ingestion",
                path="tests/integration/test_multi_source_ingestion.py",
                description="Multi-source document ingestion workflows",
                marker="integration",
                parallel_safe=False
            ),
            TestSuite(
                name="Documentation Quality",
                path="tests/integration/test_documentation_quality_workflow.py",
                description="Documentation quality assessment workflows",
                marker="integration",
                parallel_safe=False
            ),
            TestSuite(
                name="Security Compliance",
                path="tests/integration/test_security_compliance_workflow.py",
                description="Security compliance and policy workflows",
                marker="integration",
                parallel_safe=False
            ),

            # Performance Test Suites
            TestSuite(
                name="Performance Tests",
                path="tests/performance/",
                description="Load testing and performance benchmarking",
                marker="slow",
                parallel_safe=False,
                timeout=900
            )
        ]

    def run_single_test_suite(self, suite: TestSuite, parallel: bool = False,
                            workers: int = 4, coverage: bool = True) -> TestResult:
        """Run a single test suite."""
        start_time = time.time()

        cmd = [
            sys.executable, "-m", "pytest",
            suite.path,
            "-v",
            "--tb=short",
            "--durations=10",
            f"--timeout={suite.timeout}"
        ]

        if suite.marker:
            cmd.extend(["-m", suite.marker])

        if parallel and suite.parallel_safe:
            cmd.extend(["-n", str(workers), "--dist=worksteal"])

        if coverage:
            cmd.extend([
                "--cov=services",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml",
                "--cov-fail-under=80"
            ])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=suite.timeout + 60  # Add buffer time
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            # Extract test counts from output
            test_count = 0
            failure_count = 0

            for line in result.stdout.split('\n'):
                if 'passed' in line and 'failed' in line:
                    # Parse pytest summary line
                    parts = line.split(',')
                    for part in parts:
                        if 'passed' in part:
                            test_count += int(part.split()[0])
                        elif 'failed' in part or 'errors' in part:
                            failure_count += int(part.split()[0])

            return TestResult(
                suite=suite,
                success=success,
                duration=duration,
                output=result.stdout,
                error_output=result.stderr,
                test_count=test_count,
                failure_count=failure_count
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                suite=suite,
                success=False,
                duration=duration,
                output="",
                error_output=f"Test suite timed out after {suite.timeout} seconds",
                test_count=0,
                failure_count=0
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                suite=suite,
                success=False,
                duration=duration,
                output="",
                error_output=str(e),
                test_count=0,
                failure_count=0
            )

    def run_all_test_suites(self, parallel: bool = True, workers: int = 4,
                          coverage: bool = True, max_workers: int = 3) -> List[TestResult]:
        """Run all test suites, with parallel execution where possible."""
        print("🚀 Starting Comprehensive Test Suite Execution")
        print("=" * 70)
        print(f"Parallel Execution: {parallel}")
        if parallel:
            print(f"Max Parallel Workers: {max_workers}")
            print(f"Workers per Suite: {workers}")
        print(f"Coverage Reporting: {coverage}")
        print()

        results = []

        # Separate parallel-safe and serial-only suites
        parallel_suites = [s for s in self.test_suites if s.parallel_safe]
        serial_suites = [s for s in self.test_suites if not s.parallel_safe]

        # Run parallel suites concurrently
        if parallel and parallel_suites:
            print(f"📦 Running {len(parallel_suites)} parallel-safe test suites...")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_suite = {
                    executor.submit(self.run_single_test_suite, suite, parallel, workers, coverage): suite
                    for suite in parallel_suites
                }

                for future in as_completed(future_to_suite):
                    suite = future_to_suite[future]
                    try:
                        result = future.result()
                        results.append(result)
                        self._print_suite_result(result)
                    except Exception as e:
                        print(f"❌ Error running {suite.name}: {e}")

        # Run serial suites sequentially
        if serial_suites:
            print(f"🔄 Running {len(serial_suites)} serial test suites...")
            for suite in serial_suites:
                result = self.run_single_test_suite(suite, False, 1, coverage)
                results.append(result)
                self._print_suite_result(result)

        return results

    def _print_suite_result(self, result: TestResult):
        """Print the result of a test suite execution."""
        status = "✅ PASSED" if result.success else "❌ FAILED"
        duration_str = ".2f"

        print("30")
        if result.test_count > 0:
            print(f"      Tests: {result.test_count}")
        if result.failure_count > 0:
            print(f"      Failures: {result.failure_count}")

        if not result.success and result.error_output:
            # Print first few lines of error output
            error_lines = result.error_output.split('\n')[:5]
            for line in error_lines:
                if line.strip():
                    print(f"      {line}")

    def generate_comprehensive_report(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        total_suites = len(results)
        passed_suites = sum(1 for r in results if r.success)
        failed_suites = total_suites - passed_suites

        total_tests = sum(r.test_count for r in results)
        total_failures = sum(r.failure_count for r in results)
        total_duration = sum(r.duration for r in results)

        # Calculate success rate
        success_rate = (passed_suites / total_suites * 100) if total_suites > 0 else 0

        # Group results by category
        unit_tests = [r for r in results if "unit" in r.suite.path]
        integration_tests = [r for r in results if "integration" in r.suite.path]
        performance_tests = [r for r in results if "performance" in r.suite.path]

        report = {
            "summary": {
                "total_suites": total_suites,
                "passed_suites": passed_suites,
                "failed_suites": failed_suites,
                "success_rate": success_rate,
                "total_tests": total_tests,
                "total_failures": total_failures,
                "total_duration": total_duration,
                "average_duration": total_duration / total_suites if total_suites > 0 else 0
            },
            "categories": {
                "unit_tests": {
                    "count": len(unit_tests),
                    "passed": sum(1 for r in unit_tests if r.success),
                    "failed": sum(1 for r in unit_tests if not r.success)
                },
                "integration_tests": {
                    "count": len(integration_tests),
                    "passed": sum(1 for r in integration_tests if r.success),
                    "failed": sum(1 for r in integration_tests if not r.success)
                },
                "performance_tests": {
                    "count": len(performance_tests),
                    "passed": sum(1 for r in performance_tests if r.success),
                    "failed": sum(1 for r in performance_tests if not r.success)
                }
            },
            "suite_details": [
                {
                    "name": r.suite.name,
                    "success": r.success,
                    "duration": r.duration,
                    "test_count": r.test_count,
                    "failure_count": r.failure_count,
                    "description": r.suite.description
                }
                for r in results
            ],
            "generated_at": time.time(),
            "test_run_id": f"comprehensive-{int(time.time())}"
        }

        return report

    def print_comprehensive_report(self, results: List[TestResult]):
        """Print a comprehensive test report."""
        report = self.generate_comprehensive_report(results)

        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUITE REPORT")
        print("=" * 70)

        summary = report["summary"]
        print(f"Test Suites Executed: {summary['total_suites']}")
        print(f"Passed: {summary['passed_suites']}")
        print(f"Failed: {summary['failed_suites']}")
        print(".1f")
        print(f"Total Tests: {summary['total_tests']}")
        if summary['total_failures'] > 0:
            print(f"Test Failures: {summary['total_failures']}")
        print(".2f")
        print(".2f")

        print("\n📈 Category Breakdown:")
        categories = report["categories"]
        for category, stats in categories.items():
            if stats["count"] > 0:
                success_rate = (stats["passed"] / stats["count"] * 100) if stats["count"] > 0 else 0
                print("25")

        print("\n📋 Suite Details:")
        for suite_detail in report["suite_details"]:
            status = "✅" if suite_detail["success"] else "❌"
            duration = ".2f"
            print("25")

        print("\n" + "=" * 70)

        # Overall assessment
        if summary["success_rate"] >= 95:
            print("🎉 EXCELLENT: Test suite passed with outstanding results!")
            print("   ✅ Comprehensive coverage achieved")
            print("   ✅ High reliability demonstrated")
            print("   ✅ Production-ready quality verified")
        elif summary["success_rate"] >= 85:
            print("👍 GOOD: Test suite passed with solid results")
            print("   ✅ Good coverage achieved")
            print("   ✅ Reliable functionality demonstrated")
            print("   ⚠️  Minor issues may need attention")
        elif summary["success_rate"] >= 70:
            print("⚠️  FAIR: Test suite passed but improvements needed")
            print("   ✅ Basic functionality verified")
            print("   ⚠️  Some reliability issues detected")
            print("   🔧 Additional testing recommended")
        else:
            print("❌ POOR: Test suite has significant issues")
            print("   ❌ Major functionality problems detected")
            print("   🔧 Critical fixes required before production")
            print("   📋 Review failed tests for critical issues")

        print("=" * 70)

    def save_report_to_file(self, results: List[TestResult], filename: str = None):
        """Save the comprehensive report to a JSON file."""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"

        report = self.generate_comprehensive_report(results)

        report_path = self.project_root / filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Report saved to: {report_path}")
        return report_path

    def check_service_health(self) -> Dict[str, bool]:
        """Check the health of required services."""
        print("🔍 Checking service health for comprehensive testing...")

        services = {
            "Mock Data Generator": "http://mock-data-generator:5065/health",
            "LLM Gateway": "http://llm-gateway:5055/health",
            "Orchestrator": "http://orchestrator:5099/health",
            "Doc Store": "http://doc_store:5087/health",
            "Prompt Store": "http://prompt-store:5110/health",
            "Analysis Service": "http://analysis-service:5020/health",
            "Summarizer Hub": "http://summarizer-hub:5060/health",
            "Interpreter": "http://interpreter:5120/health"
        }

        health_status = {}

        for service_name, health_url in services.items():
            try:
                import httpx
                response = httpx.get(health_url, timeout=5.0)
                is_healthy = response.status_code == 200
                health_status[service_name] = is_healthy

                status = "✅ Healthy" if is_healthy else f"❌ Status {response.status_code}"
                print(f"   {service_name}: {status}")

            except Exception as e:
                health_status[service_name] = False
                print(f"   {service_name}: ❌ Not available ({str(e)[:50]}...)")

        healthy_count = sum(1 for status in health_status.values() if status)
        total_count = len(health_status)

        print(f"\n🏥 Service Health: {healthy_count}/{total_count} services healthy")

        if healthy_count < total_count:
            print("⚠️  Some services are not healthy. Integration tests may fail.")
            print("💡 Start services with: docker-compose --profile ai_services up -d")

        return health_status

    def list_available_test_suites(self):
        """List all available test suites."""
        print("📋 Available Test Suites:")
        print("=" * 50)

        for i, suite in enumerate(self.test_suites, 1):
            parallel_indicator = "🔄" if suite.parallel_safe else "🔂"
            print("2d")

        print("\n📊 Test Suite Categories:")
        unit_count = sum(1 for s in self.test_suites if "unit" in s.path)
        integration_count = sum(1 for s in self.test_suites if "integration" in s.path)
        performance_count = sum(1 for s in self.test_suites if "performance" in s.path)

        print(f"   Unit Tests: {unit_count}")
        print(f"   Integration Tests: {integration_count}")
        print(f"   Performance Tests: {performance_count}")
        print(f"   Total: {len(self.test_suites)}")


def main():
    """Main entry point with comprehensive argument parsing."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Suite Runner for LLM Documentation Ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests with parallel execution
  python tests/run_comprehensive_test_suite.py --parallel --workers 4

  # Run only unit tests
  python tests/run_comprehensive_test_suite.py --unit-only

  # Run only integration tests
  python tests/run_comprehensive_test_suite.py --integration-only

  # Run with coverage reporting
  python tests/run_comprehensive_test_suite.py --coverage

  # Check service health
  python tests/run_comprehensive_test_suite.py --health-check

  # List available test suites
  python tests/run_comprehensive_test_suite.py --list-suites

  # Save report to file
  python tests/run_comprehensive_test_suite.py --save-report report.json
        """
    )

    parser.add_argument("--parallel", "-p", action="store_true",
                       help="Run tests in parallel where possible")
    parser.add_argument("--workers", "-w", type=int, default=4,
                       help="Number of workers for parallel execution (default: 4)")
    parser.add_argument("--max-parallel-suites", type=int, default=3,
                       help="Maximum number of test suites to run in parallel (default: 3)")
    parser.add_argument("--unit-only", action="store_true",
                       help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true",
                       help="Run only integration tests")
    parser.add_argument("--performance-only", action="store_true",
                       help="Run only performance tests")
    parser.add_argument("--coverage", "-c", action="store_true", default=True,
                       help="Generate coverage reports")
    parser.add_argument("--health-check", action="store_true",
                       help="Check service health before running tests")
    parser.add_argument("--list-suites", action="store_true",
                       help="List available test suites")
    parser.add_argument("--save-report", type=str,
                       help="Save comprehensive report to specified JSON file")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")

    args = parser.parse_args()

    runner = ComprehensiveTestRunner()

    # Handle special commands
    if args.list_suites:
        runner.list_available_test_suites()
        return 0

    if args.health_check:
        health_status = runner.check_service_health()
        healthy_count = sum(1 for status in health_status.values() if status)
        total_count = len(health_status)

        if healthy_count == total_count:
            print("🎉 All services are healthy!")
            return 0
        else:
            print(f"⚠️  Only {healthy_count}/{total_count} services are healthy.")
            return 1

    # Filter test suites based on arguments
    if args.unit_only:
        test_suites = [s for s in runner.test_suites if "unit" in s.path]
    elif args.integration_only:
        test_suites = [s for s in runner.test_suites if "integration" in s.path]
    elif args.performance_only:
        test_suites = [s for s in runner.test_suites if "performance" in s.path]
    else:
        test_suites = runner.test_suites

    if not test_suites:
        print("❌ No test suites match the specified criteria.")
        return 1

    # Run health check if not explicitly disabled
    if not args.health_check:
        print("🔍 Performing quick health check...")
        health_status = runner.check_service_health()
        healthy_count = sum(1 for status in health_status.values() if status)
        total_count = len(health_status)

        if healthy_count < total_count * 0.5:  # Less than 50% healthy
            print("⚠️  Many services are not healthy. Consider starting them first:")
            print("   docker-compose --profile ai_services up -d")
            print()

    # Temporarily replace test suites for filtered execution
    original_suites = runner.test_suites
    runner.test_suites = test_suites

    try:
        # Run the comprehensive test suite
        results = runner.run_all_test_suites(
            parallel=args.parallel,
            workers=args.workers,
            coverage=args.coverage,
            max_workers=args.max_parallel_suites
        )

        # Print comprehensive report
        runner.print_comprehensive_report(results)

        # Save report if requested
        if args.save_report:
            report_path = runner.save_report_to_file(results, args.save_report)
            print(f"📄 Detailed report saved to: {report_path}")

        # Determine exit code based on results
        failed_suites = sum(1 for r in results if not r.success)
        return 1 if failed_suites > 0 else 0

    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        # Restore original test suites
        runner.test_suites = original_suites


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
