#!/usr/bin/env python3
"""
Audit Test Runner for Meta-Orchestrator

Comprehensive test runner for all audit and verification capabilities.
Can run tests against specific services or the entire ecosystem.

Usage:
    # Run all audit tests
    python scripts/test/audit_test_runner.py

    # Run tests for specific service
    python scripts/test/audit_test_runner.py --service user-store

    # Run specific test category
    python scripts/test/audit_test_runner.py --category docker-compose

    # Run against running ecosystem
    python scripts/test/audit_test_runner.py --live

    # Generate detailed report
    python scripts/test/audit_test_runner.py --report audit_report.json

    # Run with verbose output
    python scripts/test/audit_test_runner.py --verbose
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import subprocess
import requests
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a single test execution"""
    test_name: str
    service_name: Optional[str]
    category: str
    success: bool
    execution_time: float
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class TestSuiteResult:
    """Complete test suite execution result"""
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time: float
    target_service: Optional[str]
    target_category: Optional[str]
    results: List[TestResult]
    summary: Dict[str, Any]


class AuditTestRunner:
    """
    Comprehensive audit test runner for the meta-orchestrator ecosystem.

    Features:
    - Service-specific testing
    - Category-based testing
    - Live ecosystem testing
    - Detailed reporting
    - Parallel test execution
    """

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30

        # Define all available services in the ecosystem
        self.all_services = {
            'orchestrator', 'doc_store', 'analysis-service', 'source-agent',
            'frontend', 'memory-agent', 'discovery-agent', 'prompt_store',
            'interpreter', 'cli', 'user-store', 'external-service-store',
            'notification-service', 'llm-gateway', 'summarizer-hub',
            'github-mcp', 'bedrock-proxy', 'secure-analyzer', 'code-analyzer',
            'architecture-digitizer', 'project-simulation', 'mock-data-generator',
            'simulation-dashboard', 'unified-api-dashboard', 'log-collector'
        }

        # Test categories and their endpoints
        self.test_categories = {
            'docker-compose': {
                'endpoint': '/api/v1/audit/docker-compose/validate',
                'method': 'POST',
                'description': 'Docker Compose validation tests'
            },
            'config-drift': {
                'endpoint': '/api/v1/audit/config/drift-detect',
                'method': 'POST',
                'description': 'Configuration drift detection tests'
            },
            'production-readiness': {
                'endpoint': '/api/v1/audit/production-readiness/validate',
                'method': 'POST',
                'description': 'Production readiness validation tests'
            },
            'config-standardization': {
                'endpoint': '/api/v1/audit/config/standardize/all',
                'method': 'POST',
                'description': 'Configuration standardization tests'
            },
            'docker-standardization': {
                'endpoint': '/api/v1/audit/docker/standardize',
                'method': 'POST',
                'description': 'Docker standardization tests'
            }
        }

    def run_all_tests(self, target_service: Optional[str] = None,
                     target_category: Optional[str] = None,
                     live_mode: bool = False, test_mode: str = 'validate') -> TestSuiteResult:
        """
        Run all audit tests based on specified criteria.

        Args:
            target_service: Run tests only for this service (if applicable)
            target_category: Run only tests in this category
            live_mode: Run against live ecosystem instead of mocked
            test_mode: Test mode for standardization tests ('validate', 'dry_run', 'apply')

        Returns:
            Complete test suite results
        """
        start_time = time.time()
        results = []

        # Determine which tests to run
        categories_to_run = [target_category] if target_category else list(self.test_categories.keys())

        for category in categories_to_run:
            if category not in self.test_categories:
                logger.warning(f"Unknown category: {category}")
                continue

            category_config = self.test_categories[category]

            # Run category-specific tests
            if category == 'config-standardization' and target_service:
                # Service-specific config standardization
                result = self._run_service_specific_test(
                    f"{category}_service_{target_service}",
                    target_service,
                    category,
                    f'/api/v1/audit/config/standardize/service/{target_service}',
                    'POST',
                    test_mode
                )
                results.append(result)
            else:
                # General category test
                result = self._run_category_test(category, category_config, live_mode, test_mode)
                results.append(result)

        # Calculate results
        execution_time = time.time() - start_time
        passed_tests = len([r for r in results if r.success])
        failed_tests = len(results) - passed_tests

        # Generate summary
        summary = self._generate_summary(results)

        return TestSuiteResult(
            timestamp=datetime.now().isoformat(),
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            execution_time=execution_time,
            target_service=target_service,
            target_category=target_category,
            results=results,
            summary=summary
        )

    def _run_category_test(self, category: str, config: Dict[str, Any], live_mode: bool, test_mode: str = 'validate') -> TestResult:
        """Run a single category test"""
        start_time = time.time()

        try:
            url = f"{self.base_url}{config['endpoint']}"
            method = config['method']

            # Add query parameters for certain tests
            params = {}
            if category == 'production-readiness':
                params['target_level'] = 'development_ready'
            elif category in ['config-drift']:
                params['dev_only'] = 'true'
            elif category in ['config-standardization', 'docker-standardization']:
                params['mode'] = test_mode

            logger.info(f"Running {category} test: {method} {url}")

            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            execution_time = time.time() - start_time

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    return TestResult(
                        test_name=category,
                        service_name=None,
                        category=category,
                        success=True,
                        execution_time=execution_time,
                        response=response_data,
                        details=self._analyze_test_response(category, response_data)
                    )
                except json.JSONDecodeError:
                    return TestResult(
                        test_name=category,
                        service_name=None,
                        category=category,
                        success=False,
                        execution_time=execution_time,
                        error="Invalid JSON response",
                        details={"status_code": response.status_code, "response_text": response.text[:500]}
                    )
            else:
                return TestResult(
                    test_name=category,
                    service_name=None,
                    category=category,
                    success=False,
                    execution_time=execution_time,
                    error=f"HTTP {response.status_code}",
                    details={"status_code": response.status_code, "response_text": response.text[:500]}
                )

        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name=category,
                service_name=None,
                category=category,
                success=False,
                execution_time=execution_time,
                error=str(e),
                details={"exception_type": type(e).__name__}
            )

    def _run_service_specific_test(self, test_name: str, service_name: str,
                                 category: str, endpoint: str, method: str, test_mode: str = 'validate') -> TestResult:
        """Run a service-specific test"""
        start_time = time.time()

        try:
            url = f"{self.base_url}{endpoint}"

            # Add mode parameter for standardization tests
            params = {}
            if category == 'config-standardization':
                params['mode'] = test_mode

            logger.info(f"Running {test_name}: {method} {url} (mode: {test_mode})")

            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params)
            else:
                response = self.session.request(method.upper(), url)

            execution_time = time.time() - start_time

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    return TestResult(
                        test_name=test_name,
                        service_name=service_name,
                        category=category,
                        success=True,
                        execution_time=execution_time,
                        response=response_data,
                        details=self._analyze_service_test_response(category, response_data)
                    )
                except json.JSONDecodeError:
                    return TestResult(
                        test_name=test_name,
                        service_name=service_name,
                        category=category,
                        success=False,
                        execution_time=execution_time,
                        error="Invalid JSON response",
                        details={"status_code": response.status_code}
                    )
            else:
                return TestResult(
                    test_name=test_name,
                    service_name=service_name,
                    category=category,
                    success=False,
                    execution_time=execution_time,
                    error=f"HTTP {response.status_code}",
                    details={"status_code": response.status_code, "response_text": response.text[:200]}
                )

        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name=test_name,
                service_name=service_name,
                category=category,
                success=False,
                execution_time=execution_time,
                error=str(e),
                details={"exception_type": type(e).__name__}
            )

    def _analyze_test_response(self, category: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test response and extract meaningful metrics"""
        analysis = {}

        try:
            if category == 'docker-compose':
                data = response_data.get('docker_compose_validation', {})
                analysis.update({
                    'services_validated': data.get('services_count', 0),
                    'port_conflicts': data.get('port_conflicts', 0),
                    'issues_found': len(data.get('issues', [])),
                    'warnings': data.get('warnings', 0),
                    'errors': data.get('errors', 0)
                })

            elif category == 'config-drift':
                data = response_data.get('configuration_drift', {})
                analysis.update({
                    'total_issues': data.get('total_issues', 0),
                    'high_severity': data.get('high_severity', 0),
                    'medium_severity': data.get('medium_severity', 0),
                    'low_severity': data.get('low_severity', 0),
                    'files_scanned': data.get('scanned_files', 0),
                    'containers_scanned': data.get('scanned_containers', 0),
                    'schema_validation_passed': data.get('schema_validation_passed', False)
                })

            elif category == 'production-readiness':
                data = response_data.get('production_readiness', {})
                analysis.update({
                    'readiness_level': data.get('overall_readiness', 'unknown'),
                    'overall_score': data.get('overall_score', 0),
                    'total_checks': data.get('total_checks', 0),
                    'passed_checks': data.get('passed_checks', 0),
                    'failed_checks': data.get('failed_checks', 0),
                    'critical_failures': data.get('critical_failures', 0),
                    'recommendations_count': len(data.get('recommendations', []))
                })

            elif category == 'config-standardization':
                data = response_data.get('config_standardization', {})
                analysis.update({
                    'services_processed': data.get('services_processed', 0),
                    'services_standardized': data.get('services_standardized', 0),
                    'total_issues': data.get('total_issues', 0),
                    'fixes_applied': data.get('fixes_applied', 0),
                    'standardization_rate': data.get('standardization_rate', 0)
                })

            elif category == 'docker-standardization':
                data = response_data.get('docker_standardization', {})
                analysis.update({
                    'files_processed': data.get('files_processed', 0),
                    'files_modified': data.get('files_modified', 0),
                    'issues_found': data.get('issues_found', 0),
                    'issues_fixed': data.get('issues_fixed', 0),
                    'pydantic_validation_passed': data.get('pydantic_validation_passed', False)
                })

        except Exception as e:
            analysis['analysis_error'] = str(e)

        return analysis

    def _analyze_service_test_response(self, category: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze service-specific test response"""
        analysis = {}

        try:
            if category == 'config-standardization':
                data = response_data.get('config_standardization', {})
                analysis.update({
                    'changes_made': len(data.get('changes_made', [])),
                    'warnings': len(data.get('warnings', [])),
                    'errors': len(data.get('errors', [])),
                    'issues_found': len(data.get('issues', []))
                })

        except Exception as e:
            analysis['analysis_error'] = str(e)

        return analysis

    def _generate_summary(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate comprehensive test suite summary"""
        summary = {
            'categories_tested': set(),
            'services_tested': set(),
            'average_execution_time': 0,
            'category_breakdown': {},
            'success_rate_by_category': {},
            'performance_metrics': {}
        }

        if not results:
            return summary

        # Calculate averages and breakdowns
        total_execution_time = sum(r.execution_time for r in results)
        summary['average_execution_time'] = total_execution_time / len(results)

        # Category breakdown
        for result in results:
            summary['categories_tested'].add(result.category)

            if result.category not in summary['category_breakdown']:
                summary['category_breakdown'][result.category] = {
                    'total': 0, 'passed': 0, 'failed': 0, 'avg_time': 0
                }

            cat_breakdown = summary['category_breakdown'][result.category]
            cat_breakdown['total'] += 1
            if result.success:
                cat_breakdown['passed'] += 1
            else:
                cat_breakdown['failed'] += 1

        # Success rates
        for category, breakdown in summary['category_breakdown'].items():
            breakdown['success_rate'] = (breakdown['passed'] / breakdown['total']) if breakdown['total'] > 0 else 0
            breakdown['avg_time'] = total_execution_time / len(results)  # Simplified

        return summary

    def print_results(self, suite_result: TestSuiteResult, verbose: bool = False):
        """Print formatted test results"""
        print("\n" + "="*80)
        print("🎯 AUDIT TEST SUITE RESULTS")
        print("="*80)

        print(f"📊 Summary:")
        print(f"   Total Tests: {suite_result.total_tests}")
        print(f"   Passed: {suite_result.passed_tests}")
        print(f"   Failed: {suite_result.failed_tests}")
        print(f"   Success Rate: {(suite_result.passed_tests/suite_result.total_tests*100):.1f}%" if suite_result.total_tests > 0 else "0%")
        print(f"   Execution Time: {suite_result.execution_time:.2f}s")
        print(f"   Average Test Time: {suite_result.execution_time/suite_result.total_tests:.2f}s" if suite_result.total_tests > 0 else "N/A")

        if suite_result.target_service:
            print(f"   Target Service: {suite_result.target_service}")
        if suite_result.target_category:
            print(f"   Target Category: {suite_result.target_category}")

        print(f"\n📈 Category Breakdown:")
        for category, stats in suite_result.summary.get('category_breakdown', {}).items():
            success_rate = stats['success_rate'] * 100
            status_icon = "✅" if success_rate == 100 else "⚠️" if success_rate >= 50 else "❌"
            print(f"   {status_icon} {category}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")

        if verbose:
            print(f"\n📋 Detailed Results:")
            for result in suite_result.results:
                status_icon = "✅" if result.success else "❌"
                service_info = f" [{result.service_name}]" if result.service_name else ""
                print(f"   {status_icon} {result.test_name}{service_info}: {result.execution_time:.2f}s")

                if not result.success and result.error:
                    print(f"      Error: {result.error}")

                if result.details and verbose:
                    for key, value in result.details.items():
                        print(f"      {key}: {value}")

        print("\n" + "="*80)

    def save_report(self, suite_result: TestSuiteResult, output_file: str):
        """Save detailed test report to JSON file"""
        # Convert dataclasses to dictionaries
        report_data = asdict(suite_result)

        # Convert sets to lists for JSON serialization
        if 'categories_tested' in report_data.get('summary', {}):
            report_data['summary']['categories_tested'] = list(report_data['summary']['categories_tested'])

        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"📄 Detailed report saved to: {output_file}")


def check_service_availability(base_url: str) -> bool:
    """Check if the meta-orchestrator service is available"""
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Audit Test Runner for Meta-Orchestrator")
    parser.add_argument('--service', '-s', help='Target specific service for testing')
    parser.add_argument('--category', '-c', help='Test specific category',
                       choices=['docker-compose', 'config-drift', 'production-readiness',
                              'config-standardization', 'docker-standardization'])
    parser.add_argument('--live', action='store_true', help='Run against live ecosystem')
    parser.add_argument('--url', default='http://localhost:8080', help='Meta-orchestrator base URL')
    parser.add_argument('--report', '-r', help='Save detailed JSON report to file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--check-availability', action='store_true', help='Only check service availability')
    parser.add_argument('--dry-run', action='store_true', help='Run tests in dry-run mode (no actual changes)')
    parser.add_argument('--mode', choices=['validate', 'dry_run', 'apply'], default='validate',
                       help='Standardization mode for applicable tests')

    args = parser.parse_args()

    # Check service availability
    if not check_service_availability(args.url):
        print(f"❌ Meta-orchestrator service not available at {args.url}")
        print("   Make sure the service is running: docker-compose up meta-orchestrator")
        sys.exit(1)

    if args.check_availability:
        print(f"✅ Meta-orchestrator service available at {args.url}")
        sys.exit(0)

    # Create test runner
    runner = AuditTestRunner(args.url)

    print(f"🚀 Starting Audit Test Suite")
    print(f"   Target URL: {args.url}")
    if args.service:
        print(f"   Target Service: {args.service}")
    if args.category:
        print(f"   Target Category: {args.category}")
    print(f"   Live Mode: {args.live}")

    # Determine test mode
    test_mode = args.mode
    if args.dry_run:
        test_mode = 'dry_run'

    # Run tests
    try:
        suite_result = runner.run_all_tests(
            target_service=args.service,
            target_category=args.category,
            live_mode=args.live,
            test_mode=test_mode
        )

        # Print results
        runner.print_results(suite_result, args.verbose)

        # Save report if requested
        if args.report:
            runner.save_report(suite_result, args.report)

        # Exit with appropriate code
        success_rate = (suite_result.passed_tests / suite_result.total_tests * 100) if suite_result.total_tests > 0 else 0
        if success_rate >= 80:
            print("✅ Test suite completed successfully!")
            sys.exit(0)
        elif success_rate >= 50:
            print("⚠️ Test suite completed with warnings")
            sys.exit(1)
        else:
            print("❌ Test suite failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️ Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
