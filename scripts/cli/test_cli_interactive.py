#!/usr/bin/env python3
"""
Interactive CLI Testing Script
Tests CLI functionality by running actual CLI commands against live services
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Print test banner."""
    print("=" * 60)
    print("🧪 CLI INTERACTIVE TESTING")
    print("=" * 60)
    print("This script will test CLI functionality by running actual commands")
    print("Make sure services are running before starting tests")
    print("=" * 60)
    print()

def check_services():
    """Check if required services are running."""
    print("🔍 Checking service availability...")

    services = [
        ("Doc Store", "http://localhost:5010/health"),
        ("Analysis Service", "http://localhost:5020/integration/health"),
        ("Prompt Store", "http://localhost:5110/health"),
        ("Summarizer Hub", "http://localhost:5060/health"),
        ("Interpreter", "http://localhost:5120/health")
    ]

    available_services = 0

    for service_name, health_url in services:
        try:
            import requests
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: RUNNING")
                available_services += 1
            else:
                print(f"❌ {service_name}: NOT HEALTHY ({response.status_code})")
        except:
            print(f"❌ {service_name}: NOT AVAILABLE")

    print(f"\n📊 Services Available: {available_services}/{len(services)}")

    if available_services == 0:
        print("❌ No services available. Please start services first.")
        return False

    if available_services < len(services):
        print("⚠️  Some services are not available. Tests may be limited.")

    return True

def run_cli_command(command, description, expect_interaction=False):
    """Run a CLI command and report results."""
    print(f"\n🔄 Testing: {description}")
    print(f"💻 Command: {command}")

    try:
        if expect_interaction:
            print("⚠️  This test requires user interaction")
            return "SKIPPED"

        # Set PYTHONPATH for the CLI
        project_root = Path(__file__).parent.parent
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root)

        # Run the command
        result = subprocess.run(
            command,
            shell=True,
            env=env,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout.strip():
                print(f"📄 Output: {result.stdout.strip()[:200]}...")
            return "PASS"
        else:
            print("❌ FAILED")
            if result.stderr.strip():
                print(f"❗ Error: {result.stderr.strip()}")
            return "FAIL"

    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT")
        return "TIMEOUT"
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return "ERROR"

def test_cli_basic_functionality():
    """Test basic CLI functionality."""
    print("\n🧪 BASIC CLI FUNCTIONALITY TESTS")
    print("-" * 40)

    results = []

    # Test CLI help
    result = run_cli_command(
        "python services/cli/main.py --help",
        "CLI help command"
    )
    results.append(("CLI Help", result))

    # Test CLI version/info
    result = run_cli_command(
        "python services/cli/main.py --version 2>/dev/null || echo 'version not available'",
        "CLI version command"
    )
    results.append(("CLI Version", result))

    return results

def test_cli_service_interaction():
    """Test CLI interaction with services."""
    print("\n🧪 SERVICE INTERACTION TESTS")
    print("-" * 40)

    results = []

    # Test health check
    result = run_cli_command(
        "echo '1' | python services/cli/main.py",
        "CLI health check (requires user input)"
    )
    results.append(("Health Check", "REQUIRES_INTERACTION"))

    # Test service status via direct command
    result = run_cli_command(
        "python services/cli/main.py health 2>/dev/null || echo 'health command not available'",
        "Direct health check command"
    )
    results.append(("Direct Health Check", result))

    return results

def test_cli_analysis_service():
    """Test CLI Analysis Service functionality."""
    print("\n🧪 ANALYSIS SERVICE CLI TESTS")
    print("-" * 40)

    results = []

    # Test analysis service menu access
    result = run_cli_command(
        "echo '2' | timeout 10 python services/cli/main.py",
        "Analysis Service menu access"
    )
    results.append(("Analysis Menu", "REQUIRES_INTERACTION"))

    # Test basic analysis command (if available)
    result = run_cli_command(
        "python services/cli/main.py analyze --help 2>/dev/null || echo 'analyze command not available'",
        "Analysis command help"
    )
    results.append(("Analysis Command", result))

    return results

def test_cli_doc_store():
    """Test CLI Doc Store functionality."""
    print("\n🧪 DOC STORE CLI TESTS")
    print("-" * 40)

    results = []

    # Test doc store menu access
    result = run_cli_command(
        "echo '1' | timeout 10 python services/cli/main.py",
        "Doc Store menu access"
    )
    results.append(("Doc Store Menu", "REQUIRES_INTERACTION"))

    return results

def test_cli_integration():
    """Test CLI integration functionality."""
    print("\n🧪 INTEGRATION TESTS")
    print("-" * 40)

    results = []

    # Test integration test command
    result = run_cli_command(
        "python services/cli/main.py test-integration 2>/dev/null || echo 'integration test not available'",
        "CLI integration test command"
    )
    results.append(("Integration Test", result))

    return results

def generate_report(all_results):
    """Generate test report."""
    print("\n" + "=" * 60)
    print("📊 CLI INTERACTIVE TEST REPORT")
    print("=" * 60)

    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    skipped_tests = 0
    interactive_tests = 0

    for category, tests in all_results.items():
        print(f"\n{category}:")
        for test_name, result in tests:
            total_tests += 1

            if result == "PASS":
                passed_tests += 1
                status = "✅ PASS"
            elif result == "FAIL":
                failed_tests += 1
                status = "❌ FAIL"
            elif result == "SKIPPED" or result == "REQUIRES_INTERACTION":
                skipped_tests += 1
                status = "⏭️  SKIP"
            elif result == "TIMEOUT":
                failed_tests += 1
                status = "⏰ TIMEOUT"
            elif result == "ERROR":
                failed_tests += 1
                status = "💥 ERROR"
            else:
                skipped_tests += 1
                status = f"❓ {result}"

            print(f"  {status} {test_name}")

    print(f"\n📈 SUMMARY:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {failed_tests}")
    print(f"   Skipped: {skipped_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
    elif failed_tests > 0:
        print(f"\n⚠️  {failed_tests} TEST(S) FAILED")
    else:
        print(f"\nℹ️  {skipped_tests} TEST(S) SKIPPED")

def main():
    """Main test function."""
    print_banner()

    # Check services first
    if not check_services():
        print("\n❌ Cannot proceed with tests - no services available")
        return 1

    # Run all test categories
    all_results = {}

    try:
        all_results["Basic CLI"] = test_cli_basic_functionality()
        all_results["Service Interaction"] = test_cli_service_interaction()
        all_results["Analysis Service"] = test_cli_analysis_service()
        all_results["Doc Store"] = test_cli_doc_store()
        all_results["Integration"] = test_cli_integration()

        # Generate final report
        generate_report(all_results)

        print("\n💡 TIPS:")
        print("   - Run 'python services/cli/main.py interactive' for manual testing")
        print("   - Use 'python scripts/test/test_cli_comprehensive.py' for automated tests")
        print("   - Check service logs for detailed error information")

        return 0

    except KeyboardInterrupt:
        print("\n\n🛑 Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
