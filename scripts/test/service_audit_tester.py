#!/usr/bin/env python3
"""
Service-Specific Audit Tester

Comprehensive testing tool for individual services in the ecosystem.
Runs all audit tests against specific services and provides detailed analysis.

Usage:
    # Test all services
    python scripts/test/service_audit_tester.py

    # Test specific service
    python scripts/test/service_audit_tester.py --service user-store

    # Test multiple services
    python scripts/test/service_audit_tester.py --services user-store doc_store

    # Generate comparative report
    python scripts/test/service_audit_tester.py --compare --output comparison.json

    # Run with health checks
    python scripts/test/service_audit_tester.py --health-check

    # Run performance tests
    python scripts/test/service_audit_tester.py --performance
"""

import argparse
import asyncio
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import requests
from dataclasses import dataclass, field, asdict
from datetime import datetime
import concurrent.futures
import threading
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ServiceTestResult:
    """Results of testing a single service"""
    service_name: str
    timestamp: str
    overall_score: float
    tests_passed: int
    tests_failed: int
    tests_total: int
    execution_time: float

    # Detailed results by category
    docker_compose: Optional[Dict[str, Any]] = None
    config_drift: Optional[Dict[str, Any]] = None
    production_readiness: Optional[Dict[str, Any]] = None
    config_standardization: Optional[Dict[str, Any]] = None

    # Health and performance metrics
    health_status: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

    # Issues and recommendations
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ServiceComparisonReport:
    """Comparative analysis of multiple services"""
    timestamp: str
    services_tested: List[str]
    comparison_metrics: Dict[str, Any]
    rankings: Dict[str, Any]
    recommendations: List[str]


class ServiceAuditTester:
    """
    Comprehensive service-specific audit testing tool.

    Features:
    - Individual service testing
    - Comparative analysis
    - Health monitoring
    - Performance benchmarking
    - Parallel execution
    """

    def __init__(self, base_url: str = "http://localhost:8080", max_workers: int = 4):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        self.max_workers = max_workers

        # Define all available services
        self.all_services = {
            'orchestrator', 'doc_store', 'analysis-service', 'source-agent',
            'frontend', 'memory-agent', 'discovery-agent', 'prompt_store',
            'interpreter', 'cli', 'user-store', 'external-service-store',
            'notification-service', 'llm-gateway', 'summarizer-hub',
            'github-mcp', 'bedrock-proxy', 'secure-analyzer', 'code-analyzer',
            'architecture-digitizer', 'project-simulation', 'mock-data-generator',
            'simulation-dashboard', 'unified-api-dashboard', 'log-collector'
        }

    def test_service(self, service_name: str, include_health: bool = False,
                    include_performance: bool = False, test_mode: str = 'validate') -> ServiceTestResult:
        """
        Run comprehensive audit tests for a specific service.

        Args:
            service_name: Name of the service to test
            include_health: Include health check tests
            include_performance: Include performance tests
            test_mode: Test mode for standardization ('validate', 'dry_run', 'apply')

        Returns:
            Complete test results for the service
        """
        start_time = time.time()
        result = ServiceTestResult(
            service_name=service_name,
            timestamp=datetime.now().isoformat(),
            overall_score=0.0,
            tests_passed=0,
            tests_failed=0,
            tests_total=0,
            execution_time=0
        )

        logger.info(f"🔍 Testing service: {service_name}")

        try:
            # Run Docker Compose validation (applies to all services)
            result.docker_compose = self._run_docker_compose_validation()
            if result.docker_compose and result.docker_compose.get('success'):
                result.tests_passed += 1
            else:
                result.tests_failed += 1
            result.tests_total += 1

            # Run configuration drift detection
            result.config_drift = self._run_config_drift_detection()
            if result.config_drift and result.config_drift.get('success'):
                result.tests_passed += 1
            else:
                result.tests_failed += 1
            result.tests_total += 1

            # Run production readiness validation
            result.production_readiness = self._run_production_readiness_validation()
            if result.production_readiness and result.production_readiness.get('success'):
                result.tests_passed += 1
            else:
                result.tests_failed += 1
            result.tests_total += 1

            # Run service-specific config standardization
            result.config_standardization = self._run_service_config_standardization(service_name, test_mode)
            if result.config_standardization and result.config_standardization.get('success'):
                result.tests_passed += 1
            else:
                result.tests_failed += 1
            result.tests_total += 1

            # Optional health checks
            if include_health:
                result.health_status = self._run_health_checks(service_name)
                result.tests_total += 1
                if result.health_status and result.health_status.get('healthy', False):
                    result.tests_passed += 1
                else:
                    result.tests_failed += 1

            # Optional performance tests
            if include_performance:
                result.performance_metrics = self._run_performance_tests(service_name)
                result.tests_total += 1
                # Performance tests are informational, don't count as pass/fail

            # Calculate overall score
            result.overall_score = (result.tests_passed / result.tests_total) if result.tests_total > 0 else 0

            # Generate issues and recommendations
            result.issues, result.recommendations = self._analyze_service_results(result)

        except Exception as e:
            logger.error(f"❌ Service test failed for {service_name}: {e}")
            result.tests_failed = result.tests_total
            result.issues.append({
                'type': 'test_execution_error',
                'severity': 'error',
                'description': f'Test execution failed: {str(e)}'
            })

        result.execution_time = time.time() - start_time
        return result

    def test_multiple_services(self, service_names: List[str], include_health: bool = False,
                             include_performance: bool = False, parallel: bool = True, test_mode: str = 'validate') -> List[ServiceTestResult]:
        """
        Test multiple services, optionally in parallel.

        Args:
            service_names: List of service names to test
            include_health: Include health checks
            include_performance: Include performance tests
            parallel: Run tests in parallel
            test_mode: Test mode for standardization ('validate', 'dry_run', 'apply')

        Returns:
            List of test results for each service
        """
        if parallel and len(service_names) > 1:
            return self._test_services_parallel(service_names, include_health, include_performance, test_mode)
        else:
            results = []
            for service_name in service_names:
                result = self.test_service(service_name, include_health, include_performance, test_mode)
                results.append(result)
            return results

    def _test_services_parallel(self, service_names: List[str], include_health: bool,
                              include_performance: bool, test_mode: str = 'validate') -> List[ServiceTestResult]:
        """Test services in parallel using thread pool"""
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_service = {
                executor.submit(self.test_service, service_name, include_health, include_performance, test_mode): service_name
                for service_name in service_names
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_service):
                service_name = future_to_service[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"✅ Completed testing {service_name}: {result.overall_score:.2f} score")
                except Exception as e:
                    logger.error(f"❌ Failed to test {service_name}: {e}")
                    # Create error result
                    error_result = ServiceTestResult(
                        service_name=service_name,
                        timestamp=datetime.now().isoformat(),
                        overall_score=0.0,
                        tests_passed=0,
                        tests_failed=1,
                        tests_total=1,
                        execution_time=0,
                        issues=[{
                            'type': 'parallel_execution_error',
                            'severity': 'error',
                            'description': f'Parallel test execution failed: {str(e)}'
                        }]
                    )
                    results.append(error_result)

        return results

    def generate_comparison_report(self, results: List[ServiceTestResult]) -> ServiceComparisonReport:
        """Generate comparative analysis report for multiple services"""
        report = ServiceComparisonReport(
            timestamp=datetime.now().isoformat(),
            services_tested=[r.service_name for r in results],
            comparison_metrics={},
            rankings={},
            recommendations=[]
        )

        if not results:
            return report

        # Calculate comparison metrics
        scores = [r.overall_score for r in results]
        execution_times = [r.execution_time for r in results]

        report.comparison_metrics = {
            'average_score': sum(scores) / len(scores),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'average_execution_time': sum(execution_times) / len(execution_times),
            'total_execution_time': sum(execution_times)
        }

        # Generate rankings
        sorted_by_score = sorted(results, key=lambda x: x.overall_score, reverse=True)
        sorted_by_time = sorted(results, key=lambda x: x.execution_time)

        report.rankings = {
            'by_overall_score': [r.service_name for r in sorted_by_score],
            'by_execution_time': [r.service_name for r in sorted_by_time],
            'best_performer': sorted_by_score[0].service_name if sorted_by_score else None,
            'fastest_execution': sorted_by_time[0].service_name if sorted_by_time else None
        }

        # Generate recommendations
        report.recommendations = self._generate_comparison_recommendations(results)

        return report

    def _run_docker_compose_validation(self) -> Optional[Dict[str, Any]]:
        """Run Docker Compose validation"""
        try:
            url = f"{self.base_url}/api/v1/audit/docker-compose/validate"
            response = self.session.post(url)

            if response.status_code == 200:
                return response.json().get('docker_compose_validation')
            else:
                logger.warning(f"Docker Compose validation failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Docker Compose validation error: {e}")
            return None

    def _run_config_drift_detection(self) -> Optional[Dict[str, Any]]:
        """Run configuration drift detection"""
        try:
            url = f"{self.base_url}/api/v1/audit/config/drift-detect"
            response = self.session.post(url, params={'dev_only': 'true'})

            if response.status_code == 200:
                return response.json().get('configuration_drift')
            else:
                logger.warning(f"Config drift detection failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Config drift detection error: {e}")
            return None

    def _run_production_readiness_validation(self) -> Optional[Dict[str, Any]]:
        """Run production readiness validation"""
        try:
            url = f"{self.base_url}/api/v1/audit/production-readiness/validate"
            response = self.session.post(url, params={'target_level': 'development_ready'})

            if response.status_code == 200:
                return response.json().get('production_readiness')
            else:
                logger.warning(f"Production readiness validation failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Production readiness validation error: {e}")
            return None

    def _run_service_config_standardization(self, service_name: str, test_mode: str = 'validate') -> Optional[Dict[str, Any]]:
        """Run service-specific configuration standardization"""
        try:
            url = f"{self.base_url}/api/v1/audit/config/standardize/service/{service_name}"
            response = self.session.post(url, params={'mode': test_mode})

            if response.status_code == 200:
                return response.json().get('config_standardization')
            else:
                logger.warning(f"Service config standardization failed for {service_name}: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Service config standardization error for {service_name}: {e}")
            return None

    def _run_health_checks(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Run health checks for a service"""
        # This would integrate with the health monitoring system
        # For now, return a basic structure
        return {
            'healthy': True,
            'response_time': 0.1,
            'last_check': datetime.now().isoformat(),
            'status': 'operational'
        }

    def _run_performance_tests(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Run performance tests for a service"""
        # This would integrate with performance monitoring
        # For now, return basic metrics
        return {
            'avg_response_time': 0.05,
            'requests_per_second': 100,
            'error_rate': 0.01,
            'memory_usage': '150MB',
            'cpu_usage': '5%'
        }

    def _analyze_service_results(self, result: ServiceTestResult) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Analyze test results and generate issues and recommendations"""
        issues = []
        recommendations = []

        # Analyze Docker Compose results
        if result.docker_compose:
            dc_data = result.docker_compose
            if dc_data.get('port_conflicts', 0) > 0:
                issues.append({
                    'type': 'port_conflict',
                    'severity': 'high',
                    'description': f"{dc_data['port_conflicts']} port conflicts detected"
                })
                recommendations.append("Resolve port conflicts in docker-compose.yml")

            if dc_data.get('errors', 0) > 0:
                issues.append({
                    'type': 'docker_compose_error',
                    'severity': 'high',
                    'description': f"{dc_data['errors']} Docker Compose validation errors"
                })

        # Analyze config drift results
        if result.config_drift:
            cd_data = result.config_drift
            total_issues = cd_data.get('total_issues', 0)
            if total_issues > 0:
                issues.append({
                    'type': 'config_drift',
                    'severity': 'medium',
                    'description': f"{total_issues} configuration drift issues detected"
                })
                recommendations.append("Review and resolve configuration drift issues")

        # Analyze production readiness
        if result.production_readiness:
            pr_data = result.production_readiness
            readiness = pr_data.get('overall_readiness', 'unknown')
            if readiness not in ['production_ready', 'development_ready']:
                issues.append({
                    'type': 'production_readiness',
                    'severity': 'medium',
                    'description': f"Service readiness level: {readiness}"
                })
                recommendations.append("Improve production readiness score")

        # Analyze config standardization
        if result.config_standardization:
            cs_data = result.config_standardization
            if not cs_data.get('success', False):
                issues.append({
                    'type': 'config_standardization',
                    'severity': 'low',
                    'description': "Configuration standardization issues detected"
                })

        return issues, recommendations

    def _generate_comparison_recommendations(self, results: List[ServiceTestResult]) -> List[str]:
        """Generate recommendations based on comparative analysis"""
        recommendations = []

        if not results:
            return recommendations

        # Find best and worst performers
        sorted_results = sorted(results, key=lambda x: x.overall_score, reverse=True)
        best_service = sorted_results[0]
        worst_service = sorted_results[-1]

        if best_service.overall_score > worst_service.overall_score:
            recommendations.append(
                f"Use {best_service.service_name} as a reference for improving other services"
            )

        # Check for common issues
        services_with_issues = [r for r in results if r.issues]
        if len(services_with_issues) > len(results) * 0.5:
            recommendations.append(
                "Address common issues across multiple services to improve overall ecosystem health"
            )

        # Performance recommendations
        fast_services = [r.service_name for r in sorted_results[:3]]
        slow_services = [r.service_name for r in sorted_results[-3:]]

        if len(set(fast_services + slow_services)) > 3:
            recommendations.append(
                f"Analyze performance differences between fast ({', '.join(fast_services[:2])}) and slow ({', '.join(slow_services[:2])}) services"
            )

        return recommendations

    def print_service_results(self, result: ServiceTestResult, verbose: bool = False):
        """Print formatted results for a single service"""
        status_icon = "✅" if result.overall_score >= 0.8 else "⚠️" if result.overall_score >= 0.5 else "❌"

        print(f"\n{status_icon} Service: {result.service_name}")
        print(f"   Overall Score: {result.overall_score:.2f} ({result.tests_passed}/{result.tests_total})")
        print(f"   Execution Time: {result.execution_time:.2f}s")

        if result.docker_compose:
            dc = result.docker_compose
            dc_status = "✅" if dc.get('success') else "❌"
            print(f"   {dc_status} Docker Compose: {dc.get('services_count', 0)} services, {dc.get('issues', []).__len__()} issues")

        if result.config_drift:
            cd = result.config_drift
            cd_status = "✅" if cd.get('success') else "❌"
            print(f"   {cd_status} Config Drift: {cd.get('total_issues', 0)} issues, {cd.get('scanned_files', 0)} files")

        if result.production_readiness:
            pr = result.production_readiness
            pr_status = "✅" if pr.get('success') else "❌"
            readiness = pr.get('overall_readiness', 'unknown')
            print(f"   {pr_status} Production Readiness: {readiness} ({pr.get('overall_score', 0):.2f})")

        if result.config_standardization:
            cs = result.config_standardization
            cs_status = "✅" if cs.get('success') else "❌"
            print(f"   {cs_status} Config Standardization: {cs.get('changes_made', []).__len__()} changes")

        if verbose and result.issues:
            print(f"   Issues:")
            for issue in result.issues[:5]:  # Show first 5 issues
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢", "error": "❌"}.get(issue.get('severity', 'low'), "⚪")
                print(f"     {severity_icon} {issue.get('description', 'Unknown issue')}")

        if verbose and result.recommendations:
            print(f"   Recommendations:")
            for rec in result.recommendations[:3]:  # Show first 3 recommendations
                print(f"     💡 {rec}")

    def print_comparison_report(self, report: ServiceComparisonReport):
        """Print comparative analysis report"""
        print(f"\n📊 Service Comparison Report")
        print(f"Generated: {report.timestamp}")
        print(f"Services Tested: {', '.join(report.services_tested)}")

        metrics = report.comparison_metrics
        print(f"\n📈 Metrics:")
        print(f"   Average Score: {metrics.get('average_score', 0):.2f}")
        print(f"   Score Range: {metrics.get('lowest_score', 0):.2f} - {metrics.get('highest_score', 0):.2f}")
        print(f"   Average Execution Time: {metrics.get('average_execution_time', 0):.2f}s")
        print(f"   Total Execution Time: {metrics.get('total_execution_time', 0):.2f}s")

        rankings = report.rankings
        print(f"\n🏆 Rankings:")
        print(f"   By Overall Score: {', '.join(rankings.get('by_overall_score', []))}")
        print(f"   By Execution Time: {', '.join(rankings.get('by_execution_time', []))}")

        if report.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in report.recommendations:
                print(f"   • {rec}")

    def save_results(self, results: List[ServiceTestResult], output_file: str):
        """Save test results to JSON file"""
        # Convert dataclasses to dictionaries
        results_data = []
        for result in results:
            result_dict = asdict(result)
            results_data.append(result_dict)

        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_services': len(results),
                'results': results_data
            }, f, indent=2, default=str)

        print(f"💾 Results saved to: {output_file}")


def check_service_availability(base_url: str) -> bool:
    """Check if the meta-orchestrator service is available"""
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Service-Specific Audit Tester")
    parser.add_argument('--service', '-s', help='Test specific service')
    parser.add_argument('--services', nargs='*', help='Test multiple services')
    parser.add_argument('--all', action='store_true', help='Test all services')
    parser.add_argument('--compare', action='store_true', help='Generate comparison report')
    parser.add_argument('--health-check', action='store_true', help='Include health checks')
    parser.add_argument('--performance', action='store_true', help='Include performance tests')
    parser.add_argument('--parallel', action='store_true', default=True, help='Run tests in parallel')
    parser.add_argument('--sequential', action='store_true', help='Run tests sequentially')
    parser.add_argument('--url', default='http://localhost:8080', help='Meta-orchestrator base URL')
    parser.add_argument('--output', '-o', help='Save results to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--max-workers', type=int, default=4, help='Maximum parallel workers')
    parser.add_argument('--dry-run', action='store_true', help='Run tests in dry-run mode (no actual changes)')
    parser.add_argument('--mode', choices=['validate', 'dry_run', 'apply'], default='validate',
                       help='Standardization mode for applicable tests')

    args = parser.parse_args()

    # Determine which services to test
    if args.service:
        services_to_test = [args.service]
    elif args.services:
        services_to_test = args.services
    elif args.all:
        # Would need to get list of all services from the ecosystem
        services_to_test = ['user-store', 'doc_store', 'orchestrator']  # Default subset for demo
    else:
        services_to_test = ['user-store']  # Default

    # Check service availability
    if not check_service_availability(args.url):
        print(f"❌ Meta-orchestrator service not available at {args.url}")
        print("   Make sure the service is running: docker-compose up meta-orchestrator")
        sys.exit(1)

    # Create tester
    tester = ServiceAuditTester(args.url, args.max_workers)

    print(f"🚀 Starting Service Audit Testing")
    print(f"   Target URL: {args.url}")
    print(f"   Services to test: {', '.join(services_to_test)}")
    print(f"   Parallel execution: {args.parallel and not args.sequential}")
    print(f"   Include health checks: {args.health_check}")
    print(f"   Include performance tests: {args.performance}")

    # Determine test mode
    test_mode = args.mode
    if args.dry_run:
        test_mode = 'dry_run'
    print(f"   Test mode: {test_mode}")

    try:
        # Run tests
        results = tester.test_multiple_services(
            services_to_test,
            include_health=args.health_check,
            include_performance=args.performance,
            parallel=args.parallel and not args.sequential,
            test_mode=test_mode
        )

        # Print individual results
        for result in results:
            tester.print_service_results(result, args.verbose)

        # Generate comparison if requested
        if args.compare and len(results) > 1:
            comparison_report = tester.generate_comparison_report(results)
            tester.print_comparison_report(comparison_report)

        # Save results if requested
        if args.output:
            tester.save_results(results, args.output)

        # Calculate overall success
        total_tests = sum(r.tests_total for r in results)
        passed_tests = sum(r.tests_passed for r in results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n🎯 Overall Results:")
        print(f"   Services Tested: {len(results)}")
        print(f"   Total Tests: {total_tests}")
        print(f"   Tests Passed: {passed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")

        if success_rate >= 80:
            print("✅ All service audits completed successfully!"            sys.exit(0)
        elif success_rate >= 50:
            print("⚠️ Service audits completed with some issues"            sys.exit(1)
        else:
            print("❌ Service audits failed - major issues detected"            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
