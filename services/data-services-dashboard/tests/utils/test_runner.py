"""Test runner utilities for the Data Services Dashboard."""

import subprocess
import sys
import os
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run tests with specified configuration."""
    project_root = Path(__file__).parent.parent.parent
    tests_dir = project_root / "tests"

    # Build pytest command
    cmd = ["python3", "-m", "pytest"]

    if test_type == "unit":
        cmd.append(str(tests_dir / "unit"))
    elif test_type == "integration":
        cmd.append(str(tests_dir / "integration"))
    elif test_type == "e2e":
        cmd.append(str(tests_dir / "e2e"))
    else:  # all
        cmd.append(str(tests_dir))

    # Add options
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])

    cmd.extend([
        "--tb=short",
        "--asyncio-mode=auto",
        "-x"  # Stop on first failure
    ])

    # Run tests
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)

    return result.returncode == 0


def run_specific_test(test_file, test_name=None):
    """Run a specific test file or test function."""
    project_root = Path(__file__).parent.parent.parent

    cmd = ["python3", "-m", "pytest", test_file]
    if test_name:
        cmd.append(f"-k {test_name}")

    cmd.extend(["-v", "--tb=short", "--asyncio-mode=auto"])

    print(f"Running specific test: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)

    return result.returncode == 0


def setup_test_environment():
    """Set up the test environment."""
    # Ensure we're in the right directory
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)

    # Add src to Python path if needed
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Set test environment variables
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("DEBUG", "true")

    print("Test environment setup complete.")


def generate_test_report():
    """Generate a test report."""
    import json
    from datetime import datetime

    report = {
        "timestamp": datetime.now().isoformat(),
        "environment": "test",
        "test_results": {
            "unit_tests": run_tests("unit", verbose=True),
            "integration_tests": run_tests("integration", verbose=True),
            "e2e_tests": run_tests("e2e", verbose=True)
        },
        "overall_success": False
    }

    # Calculate overall success
    report["overall_success"] = all(report["test_results"].values())

    # Save report
    report_file = Path(__file__).parent.parent / "test_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Test report saved to: {report_file}")
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Data Services Dashboard Test Runner")
    parser.add_argument("test_type", nargs="?", default="all",
                       choices=["all", "unit", "integration", "e2e"],
                       help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true",
                       help="Run with coverage")
    parser.add_argument("--report", "-r", action="store_true",
                       help="Generate test report")
    parser.add_argument("--setup", "-s", action="store_true",
                       help="Setup test environment")

    args = parser.parse_args()

    if args.setup:
        setup_test_environment()

    success = run_tests(args.test_type, args.verbose, args.coverage)

    if args.report:
        generate_test_report()

    sys.exit(0 if success else 1)
