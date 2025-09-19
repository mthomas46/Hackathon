#!/usr/bin/env python3
"""Test runner for the Simulation Dashboard Service.

This script provides a convenient way to run different types of tests
for the simulation dashboard with various options and configurations.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for Simulation Dashboard Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py --unit              # Run unit tests only
  python test_runner.py --integration       # Run integration tests only
  python test_runner.py --functional        # Run functional tests only
  python test_runner.py --all               # Run all tests
  python test_runner.py --coverage          # Run with coverage report
  python test_runner.py --verbose           # Run with verbose output
  python test_runner.py --web               # Generate HTML coverage report
        """
    )

    # Test type options
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        '--unit', '-u',
        action='store_true',
        help='Run unit tests only'
    )
    test_group.add_argument(
        '--integration', '-i',
        action='store_true',
        help='Run integration tests only'
    )
    test_group.add_argument(
        '--functional', '-f',
        action='store_true',
        help='Run functional tests only'
    )
    test_group.add_argument(
        '--all', '-a',
        action='store_true',
        default=True,
        help='Run all tests (default)'
    )

    # Output options
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Generate coverage report'
    )
    parser.add_argument(
        '--web', '-w',
        action='store_true',
        help='Generate HTML coverage report (implies --coverage)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet output'
    )

    # Specific test options
    parser.add_argument(
        '--pattern', '-p',
        help='Run tests matching pattern (e.g., "test_config")'
    )
    parser.add_argument(
        '--marker', '-m',
        help='Run tests with specific marker (e.g., "slow", "websocket")'
    )

    # Environment options
    parser.add_argument(
        '--env',
        choices=['development', 'test', 'production'],
        default='test',
        help='Test environment (default: test)'
    )

    args = parser.parse_args()

    # Build pytest command
    cmd = [sys.executable, '-m', 'pytest']

    # Test directory selection
    if args.unit:
        cmd.append('tests/unit/')
    elif args.integration:
        cmd.append('tests/integration/')
    elif args.functional:
        cmd.append('tests/functional/')
    else:
        cmd.append('tests/')

    # Coverage options
    if args.web:
        args.coverage = True

    if args.coverage:
        cmd.extend([
            '--cov=.',
            '--cov-report=term-missing'
        ])
        if args.web:
            cmd.extend(['--cov-report=html'])

    # Output options
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')

    # Pattern matching
    if args.pattern:
        cmd.extend(['-k', args.pattern])

    # Marker filtering
    if args.marker:
        cmd.extend(['-m', args.marker])

    # Environment setup
    os.environ['DASHBOARD_ENVIRONMENT'] = args.env
    os.environ['DASHBOARD_DEBUG'] = 'true' if args.env == 'development' else 'false'

    print("🚀 Running Simulation Dashboard Tests")
    print(f"Environment: {args.env}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)

    try:
        # Run the tests
        result = subprocess.run(cmd, cwd=Path(__file__).parent)

        # Print results summary
        print("-" * 50)
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")

        if args.web:
            print("📊 HTML coverage report generated in htmlcov/index.html")

        return result.returncode

    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def run_specific_test_suite(suite_name: str):
    """Run a specific test suite."""
    suites = {
        'unit': 'tests/unit/',
        'integration': 'tests/integration/',
        'functional': 'tests/functional/',
        'websocket': ['-m', 'websocket'],
        'slow': ['-m', 'slow'],
        'ui': ['-m', 'ui']
    }

    if suite_name not in suites:
        print(f"❌ Unknown test suite: {suite_name}")
        print(f"Available suites: {', '.join(suites.keys())}")
        return 1

    cmd = [sys.executable, '-m', 'pytest']
    if isinstance(suites[suite_name], list):
        cmd.extend(suites[suite_name])
    else:
        cmd.append(suites[suite_name])
    cmd.extend(['-v', '--tb=short'])

    print(f"🧪 Running {suite_name} test suite...")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def check_test_environment():
    """Check if test environment is properly set up."""
    issues = []

    # Check if tests directory exists
    if not Path('tests').exists():
        issues.append("❌ Tests directory not found")

    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        issues.append("❌ pytest not installed")

    # Check if coverage is available
    try:
        import pytest_cov
    except ImportError:
        issues.append("⚠️  pytest-cov not installed (coverage reports unavailable)")

    # Check test structure
    test_dirs = ['tests/unit', 'tests/integration', 'tests/functional']
    for test_dir in test_dirs:
        if not Path(test_dir).exists():
            issues.append(f"⚠️  {test_dir} directory not found")

    if issues:
        print("🔍 Test Environment Issues:")
        for issue in issues:
            print(f"   {issue}")
        print()
    else:
        print("✅ Test environment looks good!")

    return len([i for i in issues if i.startswith("❌")]) == 0


if __name__ == "__main__":
    # If run with suite name as argument
    if len(sys.argv) == 2 and sys.argv[1] in ['unit', 'integration', 'functional', 'websocket', 'slow', 'ui']:
        suite_name = sys.argv[1]
        sys.exit(run_specific_test_suite(suite_name))
    elif len(sys.argv) == 2 and sys.argv[1] == 'check':
        success = check_test_environment()
        sys.exit(0 if success else 1)
    else:
        # Run main test runner
        sys.exit(main())
