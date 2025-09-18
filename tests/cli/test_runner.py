"""
CLI Test Runner

Comprehensive test runner for all CLI tests including:
- Unit tests execution
- Integration tests execution
- Performance tests execution
- Test reporting and metrics
- Coverage analysis
- Automated test discovery
"""

import asyncio
import sys
import os
import time
import json

import unittest
from unittest.mock import patch
from io import StringIO
import subprocess
import coverage
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from .mock_framework import CLIMockFramework
from .test_fixtures import CLITestFixtures


class CLITestRunner:
    """Comprehensive CLI test runner"""

    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.coverage_data = {}
        self.start_time = None
        self.end_time = None

    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests"""
        print("🔬 Running CLI Unit Tests...")
        print("-" * 40)

        self.start_time = time.time()

        try:
            # Import and run unit tests
            from .test_cli_unit import TestCLIUnit

            # Create test suite
            suite = unittest.TestLoader().loadTestsFromTestCase(TestCLIUnit)
            runner = unittest.TextTestRunner(verbosity=2, stream=StringIO())

            # Run tests
            result = runner.run(suite)

            self.end_time = time.time()

            unit_results = {
                "tests_run": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "skipped": len(result.skipped) if hasattr(result, 'skipped') else 0,
                "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100 if result.testsRun > 0 else 0,
                "duration": self.end_time - self.start_time,
                "failures_detail": result.failures,
                "errors_detail": result.errors
            }

            print(f"✅ Unit Tests: {unit_results['success_rate']:.1f}% passed ({result.testsRun} tests)")
            return unit_results

        except Exception as e:
            print(f"❌ Unit Tests Failed: {e}")
            return {"error": str(e)}

    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        print("🔗 Running CLI Integration Tests...")
        print("-" * 40)

        start_time = time.time()

        try:
            # Import and run integration tests
            from .test_cli_integration import TestCLIIntegration

            # Create test instance
            test_instance = TestCLIIntegration()
            test_instance.setup_method()

            # Run key integration tests
            test_methods = [
                'test_full_health_check_workflow',
                'test_document_lifecycle_workflow',
                'test_container_management_workflow',
                'test_cross_service_workflow'
            ]

            results = []
            for method_name in test_methods:
                try:
                    method = getattr(test_instance, method_name)
                    await method()
                    results.append({"method": method_name, "status": "PASSED"})
                    print(f"✅ {method_name}: PASSED")
                except Exception as e:
                    results.append({"method": method_name, "status": "FAILED", "error": str(e)})
                    print(f"❌ {method_name}: FAILED - {e}")

            end_time = time.time()

            integration_results = {
                "tests_run": len(test_methods),
                "passed": len([r for r in results if r["status"] == "PASSED"]),
                "failed": len([r for r in results if r["status"] == "FAILED"]),
                "success_rate": len([r for r in results if r["status"] == "PASSED"]) / len(test_methods) * 100,
                "duration": end_time - start_time,
                "results": results
            }

            print(f"✅ Integration Tests: {integration_results['success_rate']:.1f}% passed ({integration_results['passed']}/{integration_results['tests_run']} tests)")
            return integration_results

        except Exception as e:
            print(f"❌ Integration Tests Failed: {e}")
            return {"error": str(e)}

    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        print("⚡ Running CLI Performance Tests...")
        print("-" * 40)

        start_time = time.time()

        try:
            # Import and run performance tests
            from .test_cli_performance import TestCLIPerformance

            # Create test instance
            test_instance = TestCLIPerformance()
            test_instance.setup_method()

            # Run key performance tests
            test_methods = [
                'test_response_time_baseline',
                'test_memory_usage_baseline',
                'test_startup_performance'
            ]

            results = []
            for method_name in test_methods:
                try:
                    method = getattr(test_instance, method_name)
                    if asyncio.iscoroutinefunction(method):
                        asyncio.run(method())
                    else:
                        method()
                    results.append({"method": method_name, "status": "PASSED"})
                    print(f"✅ {method_name}: PASSED")
                except Exception as e:
                    results.append({"method": method_name, "status": "FAILED", "error": str(e)})
                    print(f"❌ {method_name}: FAILED - {e}")

            end_time = time.time()

            performance_results = {
                "tests_run": len(test_methods),
                "passed": len([r for r in results if r["status"] == "PASSED"]),
                "failed": len([r for r in results if r["status"] == "FAILED"]),
                "success_rate": len([r for r in results if r["status"] == "PASSED"]) / len(test_methods) * 100,
                "duration": end_time - start_time,
                "results": results
            }

            print(f"✅ Performance Tests: {performance_results['success_rate']:.1f}% passed ({performance_results['passed']}/{performance_results['tests_run']} tests)")
            return performance_results

        except Exception as e:
            print(f"❌ Performance Tests Failed: {e}")
            return {"error": str(e)}

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all CLI tests"""
        print("🚀 Running Complete CLI Test Suite...")
        print("=" * 60)

        overall_start_time = time.time()

        # Run unit tests
        unit_results = self.run_unit_tests()
        self.test_results["unit"] = unit_results

        # Run integration tests
        integration_results = asyncio.run(self.run_integration_tests())
        self.test_results["integration"] = integration_results

        # Run performance tests
        performance_results = self.run_performance_tests()
        self.test_results["performance"] = performance_results

        overall_end_time = time.time()

        # Calculate overall results
        overall_results = self.calculate_overall_results()

        print("\n" + "=" * 60)
        print("🎯 CLI TEST SUITE RESULTS")
        print("=" * 60)

        print(f"📊 Overall Success Rate: {overall_results['overall_success_rate']:.1f}%")
        print(f"⏱️  Total Duration: {overall_results['total_duration']:.2f}s")
        print(f"🔬 Unit Tests: {unit_results.get('success_rate', 0):.1f}% ({unit_results.get('tests_run', 0)} tests)")
        print(f"🔗 Integration Tests: {integration_results.get('success_rate', 0):.1f}% ({integration_results.get('tests_run', 0)} tests)")
        print(f"⚡ Performance Tests: {performance_results.get('success_rate', 0):.1f}% ({performance_results.get('tests_run', 0)} tests)")

        if overall_results['failed_tests'] > 0:
            print(f"❌ Failed Tests: {overall_results['failed_tests']}")
        else:
            print("✅ All Tests Passed!")

        return {
            "overall": overall_results,
            "unit": unit_results,
            "integration": integration_results,
            "performance": performance_results
        }

    def calculate_overall_results(self) -> Dict[str, Any]:
        """Calculate overall test results"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_duration = 0

        for test_type, results in self.test_results.items():
            if "error" not in results:
                total_tests += results.get("tests_run", 0)
                if test_type == "unit":
                    total_passed += results.get("tests_run", 0) - results.get("failures", 0) - results.get("errors", 0)
                    total_failed += results.get("failures", 0) + results.get("errors", 0)
                else:
                    total_passed += results.get("passed", 0)
                    total_failed += results.get("failed", 0)
                total_duration += results.get("duration", 0)

        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        return {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "failed_tests": total_failed,
            "overall_success_rate": overall_success_rate,
            "total_duration": total_duration
        }

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate detailed test report"""
        report = []
        report.append("# CLI Test Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Overall summary
        overall = results.get("overall", {})
        report.append("## Overall Results")
        report.append(f"- **Success Rate**: {overall.get('overall_success_rate', 0):.1f}%")
        report.append(f"- **Total Tests**: {overall.get('total_tests', 0)}")
        report.append(f"- **Passed**: {overall.get('total_passed', 0)}")
        report.append(f"- **Failed**: {overall.get('failed_tests', 0)}")
        report.append(f"- **Duration**: {overall.get('total_duration', 0):.2f}s")
        report.append("")

        # Detailed results by test type
        for test_type in ["unit", "integration", "performance"]:
            if test_type in results:
                test_results = results[test_type]
                report.append(f"## {test_type.title()} Tests")

                if "error" in test_results:
                    report.append(f"❌ **Error**: {test_results['error']}")
                else:
                    report.append(f"- **Tests Run**: {test_results.get('tests_run', 0)}")
                    report.append(f"- **Success Rate**: {test_results.get('success_rate', 0):.1f}%")
                    report.append(f"- **Duration**: {test_results.get('duration', 0):.2f}s")

                    if test_type == "unit":
                        report.append(f"- **Failures**: {test_results.get('failures', 0)}")
                        report.append(f"- **Errors**: {test_results.get('errors', 0)}")
                    else:
                        report.append(f"- **Passed**: {test_results.get('passed', 0)}")
                        report.append(f"- **Failed**: {test_results.get('failed', 0)}")

                report.append("")

        # Performance metrics
        if self.performance_metrics:
            report.append("## Performance Metrics")
            for metric, value in self.performance_metrics.items():
                report.append(f"- **{metric}**: {value}")
            report.append("")

        return "\n".join(report)

    def save_report(self, report: str, filename: str = "cli_test_report.md"):
        """Save test report to file"""
        with open(filename, 'w') as f:
            f.write(report)
        print(f"📄 Test report saved to: {filename}")

    def run_with_coverage(self) -> Dict[str, Any]:
        """Run tests with coverage analysis"""
        print("📊 Running Tests with Coverage Analysis...")
        print("-" * 50)

        # Start coverage
        cov = coverage.Coverage(
            source=['ecosystem_cli_executable'],
            omit=['*/tests/*', '*/venv/*']
        )
        cov.start()

        try:
            # Run all tests
            results = self.run_all_tests()

            # Stop coverage
            cov.stop()
            cov.save()

            # Generate coverage report
            coverage_report = StringIO()
            cov.report(file=coverage_report)

            coverage_data = coverage_report.getvalue()

            # Add coverage to results
            results["coverage"] = {
                "report": coverage_data,
                "html_report": cov.html_report(directory='htmlcov')
            }

            print("📈 Coverage Report:")
            print(coverage_data)

            return results

        except Exception as e:
            print(f"❌ Coverage analysis failed: {e}")
            return {"error": str(e)}

    def run_pytest_suite(self) -> Dict[str, Any]:
        """Run tests using pytest framework"""
        print("🧪 Running CLI Tests with Pytest...")
        print("-" * 40)

        try:
            # Run pytest programmatically
            result = pytest.main([
                os.path.join(os.path.dirname(__file__), 'test_cli_unit.py'),
                os.path.join(os.path.dirname(__file__), 'test_cli_integration.py'),
                os.path.join(os.path.dirname(__file__), 'test_cli_performance.py'),
                '-v', '--tb=short', '--disable-warnings'
            ])

            return {
                "pytest_exit_code": result,
                "status": "PASSED" if result == 0 else "FAILED"
            }

        except Exception as e:
            print(f"❌ Pytest execution failed: {e}")
            return {"error": str(e)}


def main():
    """Main CLI test runner entry point"""
    parser = argparse.ArgumentParser(description="CLI Test Runner")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--performance-only", action="store_true", help="Run only performance tests")
    parser.add_argument("--with-coverage", action="store_true", help="Run with coverage analysis")
    parser.add_argument("--pytest", action="store_true", help="Run using pytest framework")
    parser.add_argument("--report-file", default="cli_test_report.md", help="Report output file")

    args = parser.parse_args()

    runner = CLITestRunner()

    if args.pytest:
        results = runner.run_pytest_suite()
    elif args.with_coverage:
        results = runner.run_with_coverage()
    elif args.unit_only:
        results = {"unit": runner.run_unit_tests()}
    elif args.integration_only:
        results = {"integration": asyncio.run(runner.run_integration_tests())}
    elif args.performance_only:
        results = {"performance": runner.run_performance_tests()}
    else:
        results = runner.run_all_tests()

    # Generate and save report
    if "error" not in str(results):
        report = runner.generate_report(results)
        runner.save_report(report, args.report_file)

    return 0 if all("error" not in str(r) for r in results.values()) else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
