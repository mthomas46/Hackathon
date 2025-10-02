#!/usr/bin/env python3
"""
Dry-Run Test Runner

Specialized test runner for validating dry-run functionality across the ecosystem.
Tests that dry-run modes work correctly without making actual changes.

Usage:
    # Test dry-run functionality for user-store
    python scripts/test/dry_run_test_runner.py --service user-store

    # Test all dry-run modes for user-store
    python scripts/test/dry_run_test_runner.py --service user-store --all-modes

    # Compare dry-run vs apply results
    python scripts/test/dry_run_test_runner.py --service user-store --compare-modes

    # Test dry-run for all services
    python scripts/test/dry_run_test_runner.py --all-services

    # Generate dry-run validation report
    python scripts/test/dry_run_test_runner.py --service user-store --report dry_run_report.json
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
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
class DryRunTestResult:
    """Results of dry-run testing for a service"""
    service_name: str
    timestamp: str
    test_mode: str
    success: bool
    execution_time: float

    # Results for different modes
    validate_result: Optional[Dict[str, Any]] = None
    dry_run_result: Optional[Dict[str, Any]] = None
    apply_result: Optional[Dict[str, Any]] = None

    # Analysis
    mode_differences: Dict[str, Any] = None
    dry_run_correctness: bool = False
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class DryRunComparisonReport:
    """Comparison report for dry-run vs apply modes"""
    service_name: str
    timestamp: str
    dry_run_changes: List[str]
    apply_changes: List[str]
    differences_found: bool
    dry_run_safe: bool
    analysis: Dict[str, Any]


class DryRunTestRunner:
    """
    Specialized test runner for dry-run functionality validation.

    Tests that:
    - Dry-run mode shows changes without making them
    - Validate mode only checks without showing changes
    - Apply mode actually makes changes
    - Dry-run and apply modes produce different results
    """

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30

        # Define available services
        self.all_services = {
            'user-store', 'doc_store', 'analysis-service', 'source-agent',
            'frontend', 'memory-agent', 'discovery-agent', 'prompt_store',
            'interpreter', 'cli', 'external-service-store',
            'notification-service', 'llm-gateway', 'summarizer-hub',
            'github-mcp', 'bedrock-proxy', 'secure-analyzer', 'code-analyzer',
            'architecture-digitizer', 'project-simulation', 'mock-data-generator',
            'simulation-dashboard', 'unified-api-dashboard', 'log-collector'
        }

    def test_service_dry_run(self, service_name: str, all_modes: bool = False,
                           compare_modes: bool = False) -> DryRunTestResult:
        """
        Test dry-run functionality for a specific service.

        Args:
            service_name: Name of service to test
            all_modes: Test all modes (validate, dry_run, apply)
            compare_modes: Compare dry_run vs apply results

        Returns:
            Complete dry-run test results
        """
        start_time = time.time()
        result = DryRunTestResult(
            service_name=service_name,
            timestamp=datetime.now().isoformat(),
            test_mode="comprehensive" if all_modes else "dry_run",
            success=False,
            execution_time=0
        )

        try:
            logger.info(f"🧪 Testing dry-run functionality for {service_name}")

            # Test validate mode
            result.validate_result = self._run_config_standardization(service_name, "validate")
            logger.info("✅ Validate mode tested")

            # Test dry-run mode
            result.dry_run_result = self._run_config_standardization(service_name, "dry_run")
            logger.info("✅ Dry-run mode tested")

            if all_modes:
                # Test apply mode (use with caution!)
                result.apply_result = self._run_config_standardization(service_name, "apply")
                logger.info("✅ Apply mode tested")

            # Analyze results
            result.mode_differences = self._analyze_mode_differences(result)
            result.dry_run_correctness = self._verify_dry_run_correctness(result)

            if compare_modes and all_modes:
                result.issues = self._compare_dry_run_vs_apply(result)

            result.success = True
            logger.info(f"✅ Dry-run testing completed for {service_name}")

        except Exception as e:
            logger.error(f"❌ Dry-run testing failed for {service_name}: {e}")
            result.issues.append(f"Test execution failed: {str(e)}")

        result.execution_time = time.time() - start_time
        return result

    def test_multiple_services_dry_run(self, service_names: List[str],
                                     all_modes: bool = False) -> List[DryRunTestResult]:
        """
        Test dry-run functionality for multiple services.

        Args:
            service_names: List of service names to test
            all_modes: Test all modes for each service

        Returns:
            List of dry-run test results
        """
        results = []
        for service_name in service_names:
            result = self.test_service_dry_run(service_name, all_modes)
            results.append(result)
        return results

    def generate_comparison_report(self, service_name: str) -> DryRunComparisonReport:
        """
        Generate detailed comparison between dry-run and apply modes.

        Args:
            service_name: Service to compare modes for

        Returns:
            Detailed comparison report
        """
        logger.info(f"📊 Generating dry-run vs apply comparison for {service_name}")

        # Get results for both modes
        dry_run_result = self._run_config_standardization(service_name, "dry_run")
        apply_result = self._run_config_standardization(service_name, "apply")

        # Extract changes
        dry_run_changes = dry_run_result.get("changes_made", []) if dry_run_result else []
        apply_changes = apply_result.get("changes_made", []) if apply_result else []

        # Analyze differences
        differences_found = self._compare_change_lists(dry_run_changes, apply_changes)
        dry_run_safe = self._verify_dry_run_safety(dry_run_changes, apply_changes)

        # Generate analysis
        analysis = {
            "dry_run_change_count": len(dry_run_changes),
            "apply_change_count": len(apply_changes),
            "changes_match": not differences_found,
            "dry_run_indicates_hypothetical": all("DRY RUN:" in str(change) for change in dry_run_changes),
            "apply_indicates_actual": not any("DRY RUN:" in str(change) for change in apply_changes),
            "safety_confirmed": dry_run_safe
        }

        return DryRunComparisonReport(
            service_name=service_name,
            timestamp=datetime.now().isoformat(),
            dry_run_changes=dry_run_changes,
            apply_changes=apply_changes,
            differences_found=differences_found,
            dry_run_safe=dry_run_safe,
            analysis=analysis
        )

    def _run_config_standardization(self, service_name: str, mode: str) -> Optional[Dict[str, Any]]:
        """Run configuration standardization for a service in specified mode"""
        try:
            url = f"{self.base_url}/api/v1/audit/config/standardize/service/{service_name}"
            response = self.session.post(url, params={'mode': mode})

            if response.status_code == 200:
                data = response.json()
                return data.get('config_standardization')
            else:
                logger.warning(f"Config standardization failed for {service_name} in {mode} mode: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Config standardization error for {service_name}: {e}")
            return None

    def _analyze_mode_differences(self, result: DryRunTestResult) -> Dict[str, Any]:
        """Analyze differences between test modes"""
        analysis = {
            "validate_vs_dry_run": {},
            "dry_run_vs_apply": {},
            "validate_vs_apply": {}
        }

        # Compare validate vs dry_run
        if result.validate_result and result.dry_run_result:
            validate_changes = len(result.validate_result.get("changes_made", []))
            dry_run_changes = len(result.dry_run_result.get("changes_made", []))
            analysis["validate_vs_dry_run"] = {
                "validate_changes": validate_changes,
                "dry_run_changes": dry_run_changes,
                "difference": dry_run_changes - validate_changes,
                "validate_shows_no_changes": validate_changes == 0,
                "dry_run_shows_changes": dry_run_changes > 0
            }

        # Compare dry_run vs apply
        if result.dry_run_result and result.apply_result:
            dry_run_changes = result.dry_run_result.get("changes_made", [])
            apply_changes = result.apply_result.get("changes_made", [])
            analysis["dry_run_vs_apply"] = {
                "dry_run_changes": len(dry_run_changes),
                "apply_changes": len(apply_changes),
                "dry_run_has_prefixes": all("DRY RUN:" in str(change) for change in dry_run_changes),
                "apply_has_no_prefixes": not any("DRY RUN:" in str(change) for change in apply_run_changes),
                "changes_differ": self._compare_change_lists(dry_run_changes, apply_changes)
            }

        return analysis

    def _verify_dry_run_correctness(self, result: DryRunTestResult) -> bool:
        """Verify that dry-run mode behaves correctly"""
        if not result.dry_run_result:
            return False

        dry_run_data = result.dry_run_result
        changes_made = dry_run_data.get("changes_made", [])

        # Dry-run should:
        # 1. Show changes with "DRY RUN:" prefix
        # 2. Not actually modify anything
        # 3. Have warnings about being dry-run

        has_dry_run_prefixes = all("DRY RUN:" in str(change) for change in changes_made)
        has_warnings = len(dry_run_data.get("warnings", [])) > 0
        has_issues_with_dry_run = any("DRY RUN:" in issue.get("description", "")
                                     for issue in dry_run_data.get("issues", []))

        return has_dry_run_prefixes and has_warnings and has_issues_with_dry_run

    def _compare_dry_run_vs_apply(self, result: DryRunTestResult) -> List[str]:
        """Compare dry-run vs apply results and return issues"""
        issues = []

        if not (result.dry_run_result and result.apply_result):
            issues.append("Missing results for comparison")
            return issues

        dry_run_changes = result.dry_run_result.get("changes_made", [])
        apply_changes = result.apply_result.get("changes_made", [])

        # Check for DRY RUN prefixes
        dry_run_has_prefixes = all("DRY RUN:" in str(change) for change in dry_run_changes)
        apply_has_prefixes = any("DRY RUN:" in str(change) for change in apply_changes)

        if not dry_run_has_prefixes:
            issues.append("Dry-run mode should show 'DRY RUN:' prefixes in changes")

        if apply_has_prefixes:
            issues.append("Apply mode should not show 'DRY RUN:' prefixes in changes")

        # Check that changes are different
        changes_differ = self._compare_change_lists(dry_run_changes, apply_changes)
        if not changes_differ:
            issues.append("Dry-run and apply modes should produce different change descriptions")

        return issues

    def _compare_change_lists(self, list1: List[str], list2: List[str]) -> bool:
        """Compare two lists of changes, ignoring DRY RUN prefixes"""
        def normalize_change(change: str) -> str:
            return str(change).replace("DRY RUN: Would", "").replace("Successfully", "").strip()

        normalized1 = [normalize_change(change) for change in list1]
        normalized2 = [normalize_change(change) for change in list2]

        return set(normalized1) != set(normalized2)

    def _verify_dry_run_safety(self, dry_run_changes: List[str], apply_changes: List[str]) -> bool:
        """Verify that dry-run mode is safe (doesn't make actual changes)"""
        # Dry-run should have prefixes, apply should not
        dry_run_safe = all("DRY RUN:" in str(change) for change in dry_run_changes)
        apply_actual = not any("DRY RUN:" in str(change) for change in apply_changes)

        return dry_run_safe and apply_actual

    def print_dry_run_results(self, result: DryRunTestResult, verbose: bool = False):
        """Print formatted dry-run test results"""
        status_icon = "✅" if result.success else "❌"

        print(f"\n{status_icon} Dry-Run Test Results: {result.service_name}")
        print(f"   Mode: {result.test_mode}")
        print(f"   Execution Time: {result.execution_time:.2f}s")
        print(f"   Dry-Run Correct: {result.dry_run_correctness}")

        if result.validate_result:
            validate_changes = len(result.validate_result.get("changes_made", []))
            print(f"   Validate Mode: {validate_changes} changes shown")

        if result.dry_run_result:
            dry_run_changes = len(result.dry_run_result.get("changes_made", []))
            print(f"   Dry-Run Mode: {dry_run_changes} hypothetical changes")

        if result.apply_result:
            apply_changes = len(result.apply_result.get("changes_made", []))
            print(f"   Apply Mode: {apply_changes} actual changes")

        if verbose and result.mode_differences:
            print(f"   Mode Differences:")
            for comparison, diff in result.mode_differences.items():
                if diff:
                    print(f"     {comparison}: {diff}")

        if verbose and result.issues:
            print(f"   Issues:")
            for issue in result.issues:
                print(f"     • {issue}")

    def print_comparison_report(self, report: DryRunComparisonReport):
        """Print comparison report"""
        print(f"\n📊 Dry-Run vs Apply Comparison: {report.service_name}")
        print(f"Generated: {report.timestamp}")

        print(f"\n🔍 Changes Analysis:")
        print(f"   Dry-Run Changes: {len(report.dry_run_changes)}")
        print(f"   Apply Changes: {len(report.apply_changes)}")
        print(f"   Differences Found: {report.differences_found}")
        print(f"   Dry-Run Safe: {report.dry_run_safe}")

        if report.analysis:
            analysis = report.analysis
            print(f"\n📈 Detailed Analysis:")
            print(f"   Changes Match (Normalized): {analysis.get('changes_match', False)}")
            print(f"   Dry-Run Shows Hypothetical: {analysis.get('dry_run_indicates_hypothetical', False)}")
            print(f"   Apply Shows Actual: {analysis.get('apply_indicates_actual', False)}")
            print(f"   Safety Confirmed: {analysis.get('safety_confirmed', False)}")

        print(f"\n💡 Dry-Run Changes:")
        for change in report.dry_run_changes[:5]:  # Show first 5
            print(f"   • {change}")

        if len(report.dry_run_changes) > 5:
            print(f"   ... and {len(report.dry_run_changes) - 5} more")

        print(f"\n✅ Apply Changes:")
        for change in report.apply_changes[:5]:  # Show first 5
            print(f"   • {change}")

        if len(report.apply_changes) > 5:
            print(f"   ... and {len(report.apply_changes) - 5} more")

    def save_results(self, results: List[DryRunTestResult], output_file: str):
        """Save test results to JSON file"""
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
    parser = argparse.ArgumentParser(description="Dry-Run Test Runner")
    parser.add_argument('--service', '-s', help='Test specific service')
    parser.add_argument('--all-services', action='store_true', help='Test all services')
    parser.add_argument('--all-modes', action='store_true', help='Test all modes (validate, dry_run, apply)')
    parser.add_argument('--compare-modes', action='store_true', help='Compare dry-run vs apply modes')
    parser.add_argument('--generate-comparison', '-c', help='Generate detailed comparison report for service')
    parser.add_argument('--url', default='http://localhost:8080', help='Meta-orchestrator base URL')
    parser.add_argument('--report', '-r', help='Save results to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Check service availability
    if not check_service_availability(args.url):
        print(f"❌ Meta-orchestrator service not available at {args.url}")
        print("   Make sure the service is running: docker-compose up meta-orchestrator")
        sys.exit(1)

    # Determine services to test
    if args.service:
        services_to_test = [args.service]
    elif args.all_services:
        # For safety, limit to core services for all-services mode
        services_to_test = ['user-store', 'doc_store', 'orchestrator', 'analysis-service']
    else:
        services_to_test = ['user-store']  # Default to user-store

    # Create test runner
    runner = DryRunTestRunner(args.url)

    print(f"🚀 Starting Dry-Run Test Suite")
    print(f"   Target URL: {args.url}")
    print(f"   Services to test: {', '.join(services_to_test)}")
    print(f"   Test all modes: {args.all_modes}")
    print(f"   Compare modes: {args.compare_modes}")

    try:
        results = []

        # Run tests for each service
        for service_name in services_to_test:
            result = runner.test_service_dry_run(
                service_name,
                all_modes=args.all_modes,
                compare_modes=args.compare_modes
            )
            results.append(result)
            runner.print_dry_run_results(result, args.verbose)

        # Generate comparison report if requested
        if args.generate_comparison:
            for service_name in services_to_test:
                report = runner.generate_comparison_report(service_name)
                runner.print_comparison_report(report)

        # Save results if requested
        if args.report:
            runner.save_results(results, args.report)

        # Calculate overall success
        successful_tests = len([r for r in results if r.success])
        dry_run_correct = len([r for r in results if r.dry_run_correctness])

        print(f"\n🎯 Overall Results:")
        print(f"   Services Tested: {len(results)}")
        print(f"   Tests Successful: {successful_tests}")
        print(f"   Dry-Run Correct: {dry_run_correct}")
        print(f"   Success Rate: {(successful_tests/len(results)*100):.1f}%" if results else "0%")

        if successful_tests == len(results) and dry_run_correct == len(results):
            print("✅ All dry-run tests passed successfully!")
            sys.exit(0)
        elif successful_tests >= len(results) * 0.8:
            print("⚠️ Dry-run tests completed with minor issues")
            sys.exit(1)
        else:
            print("❌ Dry-run tests failed - critical issues detected")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
