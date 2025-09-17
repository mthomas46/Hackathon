#!/usr/bin/env python3
"""
Simple CLI Test Script
Tests CLI functionality without complex imports
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def run_command(cmd, description, cwd=None):
    """Run a command and return result."""
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent)

        result = subprocess.run(
            cmd,
            shell=True,
            env=env,
            cwd=cwd or str(Path(__file__).parent.parent),
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Command timed out',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

def test_cli_help():
    """Test CLI help command."""
    console.print("🔍 Testing CLI help...")
    result = run_command("python services/cli/main.py --help", "CLI help command")

    if result['success']:
        console.print("✅ CLI help works")
        return True
    else:
        console.print(f"❌ CLI help failed: {result['stderr']}")
        return False

def test_cli_health():
    """Test CLI health command."""
    console.print("🔍 Testing CLI health command...")
    result = run_command("python services/cli/main.py health", "CLI health command")

    if result['success']:
        console.print("✅ CLI health command works")
        return True
    else:
        console.print(f"❌ CLI health command failed: {result['stderr']}")
        return False

def test_cli_commands_list():
    """Test that CLI shows available commands."""
    console.print("🔍 Testing CLI commands listing...")
    result = run_command("python services/cli/main.py --help", "CLI commands listing")

    if result['success'] and 'Commands:' in result['stdout']:
        # Count commands
        lines = result['stdout'].split('\n')
        command_section = False
        command_count = 0

        for line in lines:
            if 'Commands:' in line:
                command_section = True
                continue
            if command_section and line.strip() and not line.startswith('  '):
                break
            if command_section and line.strip() and line.startswith('  '):
                command_count += 1

        console.print(f"✅ CLI has {command_count} commands available")
        return True
    else:
        console.print("❌ CLI commands listing failed")
        return False

def test_cli_integration_test():
    """Test CLI integration test command."""
    console.print("🔍 Testing CLI integration test...")
    result = run_command("python services/cli/main.py test-integration", "CLI integration test")

    # Integration test might fail if services aren't running, but command should work
    if 'Testing Service Integration' in result['stdout']:
        console.print("✅ CLI integration test command works")
        return True
    else:
        console.print(f"❌ CLI integration test failed: {result['stderr']}")
        return False

def test_cli_analyze_docs():
    """Test CLI analyze docs command."""
    console.print("🔍 Testing CLI analyze-docs command...")
    result = run_command("python services/cli/main.py analyze-docs --help", "CLI analyze-docs help")

    if result['success']:
        console.print("✅ CLI analyze-docs command available")
        return True
    else:
        console.print("❌ CLI analyze-docs command not available")
        return False

def test_cli_analyze_code():
    """Test CLI analyze code command."""
    console.print("🔍 Testing CLI analyze-code command...")
    result = run_command("python services/cli/main.py analyze-code --help", "CLI analyze-code help")

    if result['success']:
        console.print("✅ CLI analyze-code command available")
        return True
    else:
        console.print("❌ CLI analyze-code command not available")
        return False

def test_cli_list_prompts():
    """Test CLI list prompts command."""
    console.print("🔍 Testing CLI list-prompts command...")
    result = run_command("python services/cli/main.py list-prompts", "CLI list prompts")

    # Command should work even if no prompts are available
    if result['returncode'] == 0 or 'No prompts found' in result['stdout']:
        console.print("✅ CLI list-prompts command works")
        return True
    else:
        console.print(f"❌ CLI list-prompts command failed: {result['stderr']}")
        return False

def generate_report(results):
    """Generate test report."""
    console.print("\n" + "=" * 50)
    console.print("📊 CLI SIMPLE TEST REPORT")
    console.print("=" * 50)

    table = Table()
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="green")

    total_tests = len(results)
    passed_tests = 0

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        if success:
            passed_tests += 1
        table.add_row(test_name, status)

    console.print(table)

    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

    console.print("\n📈 SUMMARY:")
    console.print(f"   Total Tests: {total_tests}")
    console.print(f"   Passed: {passed_tests}")
    console.print(f"   Failed: {total_tests - passed_tests}")
    console.print(f"   Success Rate: {success_rate:.1f}%")
    if success_rate == 100:
        console.print("\n🎉 ALL TESTS PASSED!")
    elif success_rate >= 75:
        console.print("\n👍 MOST TESTS PASSED!")
    else:
        console.print("\n⚠️  SOME TESTS FAILED")

    # Save results
    report_data = {
        'timestamp': str(Path(__file__).parent.parent / 'cli_test_results.json'),
        'results': results,
        'summary': {
            'total': total_tests,
            'passed': passed_tests,
            'failed': total_tests - passed_tests,
            'success_rate': success_rate
        }
    }

    report_file = Path(__file__).parent / 'cli_simple_test_results.json'
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    console.print(f"\n📄 Results saved to: {report_file}")

def main():
    """Main test function."""
    console.print("🚀 CLI Simple Test Suite")
    console.print("=" * 30)
    console.print("Testing CLI functionality without complex dependencies")
    console.print()

    # Run tests
    test_results = {}

    test_results['CLI Help'] = test_cli_help()
    test_results['CLI Commands List'] = test_cli_commands_list()
    test_results['CLI Health Command'] = test_cli_health()
    test_results['CLI Integration Test'] = test_cli_integration_test()
    test_results['CLI Analyze Docs'] = test_cli_analyze_docs()
    test_results['CLI Analyze Code'] = test_cli_analyze_code()
    test_results['CLI List Prompts'] = test_cli_list_prompts()

    # Generate report
    generate_report(test_results)

    # Exit with appropriate code
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)

    if passed == total:
        console.print("\n✅ All CLI tests passed!")
        return 0
    else:
        console.print(f"\n⚠️  {total - passed} CLI test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
