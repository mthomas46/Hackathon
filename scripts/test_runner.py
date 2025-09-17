#!/usr/bin/env python3
"""
Comprehensive Test Runner for LLM Documentation Ecosystem
Orchestrates all test suites in proper dependency order
"""

import os
import sys
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
import subprocess

console = Console()

class TestRunner:
    """Comprehensive test runner for the entire ecosystem."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results: Dict[str, Any] = {}
        self.start_time = time.time()

        # Define test suites in execution order
        self.test_suites = {
            "validation": {
                "name": "Validation Tests",
                "description": "API compatibility and compliance validation",
                "scripts": [
                    "scripts/validation/test_api_compatibility.py",
                    "scripts/validation/test_all_endpoints.py",
                    "scripts/validation/test_service_imports.py"
                ],
                "optional": False
            },
            "services": {
                "name": "Service Tests",
                "description": "Individual service functionality and imports",
                "scripts": [
                    "scripts/services/test_services.py",
                    "scripts/services/test_services_direct.py",
                    "scripts/services/test_interpreter_only.py"
                ],
                "optional": False
            },
            "integration": {
                "name": "Integration Tests",
                "description": "Cross-service integration and workflows",
                "scripts": [
                    "scripts/integration/test_service_mesh.py",
                    "scripts/integration/test_workflow_management.py",
                    "scripts/integration/test_orchestrator_simple.py"
                ],
                "optional": True  # Require services to be running
            },
            "cli": {
                "name": "CLI Tests",
                "description": "Command-line interface functionality",
                "scripts": [
                    "scripts/cli/test_cli_simple.py",
                    "scripts/cli/test_cli_analysis_service.py"
                ],
                "optional": True  # May require services running
            },
            "performance": {
                "name": "Performance Tests",
                "description": "Performance benchmarking and optimization",
                "scripts": [
                    "scripts/validation/performance_benchmark.py",
                    "scripts/integration/benchmark_prompt_store.py"
                ],
                "optional": True
            }
        }

    async def check_services_availability(self) -> Dict[str, bool]:
        """Check which services are currently available."""
        services_to_check = {
            "redis": ("redis-server", "--version"),
            "doc_store": ("python", "-c", "import requests; requests.get('http://localhost:5010/health', timeout=2)"),
            "analysis_service": ("python", "-c", "import requests; requests.get('http://localhost:5020/health', timeout=2)"),
            "orchestrator": ("python", "-c", "import requests; requests.get('http://localhost:5099/health/system', timeout=2)"),
            "prompt_store": ("python", "-c", "import requests; requests.get('http://localhost:5110/health', timeout=2)"),
            "summarizer_hub": ("python", "-c", "import requests; requests.get('http://localhost:5060/health', timeout=2)"),
            "interpreter": ("python", "-c", "import requests; requests.get('http://localhost:5120/health', timeout=2)")
        }

        availability = {}

        for service_name, check_cmd in services_to_check.items():
            try:
                result = subprocess.run(
                    check_cmd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd=self.project_root
                )
                availability[service_name] = result.returncode == 0
            except:
                availability[service_name] = False

        return availability

    async def run_test_script(self, script_path: str, suite_name: str) -> Dict[str, Any]:
        """Run a single test script and capture results."""
        script_name = Path(script_path).name

        try:
            console.print(f"🔄 Running {script_name}...")

            # Set PYTHONPATH
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.project_root)

            # Run the script
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                script_path,
                env=env,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # Parse output for test results
            output = stdout.decode('utf-8', errors='ignore')
            error_output = stderr.decode('utf-8', errors='ignore')

            # Try to extract test results from output
            success = process.returncode == 0
            test_count = 0
            passed_count = 0

            # Look for common test result patterns
            lines = output.split('\n')
            for line in lines:
                if 'tests passed' in line.lower() or 'tests successful' in line.lower():
                    try:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.isdigit():
                                if 'passed' in line.lower():
                                    passed_count = int(part)
                                elif 'total' in line.lower() or 'tests' in line.lower():
                                    test_count = int(part)
                    except:
                        pass

            return {
                "script": script_name,
                "suite": suite_name,
                "success": success,
                "return_code": process.returncode,
                "test_count": test_count,
                "passed_count": passed_count,
                "output": output[-1000:],  # Last 1000 chars
                "error": error_output[-500:] if error_output else None
            }

        except Exception as e:
            return {
                "script": script_name,
                "suite": suite_name,
                "success": False,
                "return_code": -1,
                "test_count": 0,
                "passed_count": 0,
                "output": "",
                "error": str(e)
            }

    async def run_test_suite(self, suite_name: str, suite_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run all scripts in a test suite."""
        console.print(f"\n🧪 Running {suite_config['name']}")
        console.print(f"   {suite_config['description']}")

        suite_results = {
            "suite_name": suite_config["name"],
            "scripts": [],
            "total_scripts": len(suite_config["scripts"]),
            "successful_scripts": 0,
            "total_tests": 0,
            "passed_tests": 0
        }

        for script_path in suite_config["scripts"]:
            if not Path(script_path).exists():
                console.print(f"⚠️  Script not found: {script_path}")
                continue

            result = await self.run_test_script(script_path, suite_name)

            if result["success"]:
                suite_results["successful_scripts"] += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"

            suite_results["scripts"].append(result)
            suite_results["total_tests"] += result["test_count"]
            suite_results["passed_tests"] += result["passed_count"]

            console.print(f"   {status} {result['script']}")
            if result["test_count"] > 0:
                console.print(f"      Tests: {result['passed_count']}/{result['test_count']}")

        return suite_results

    def generate_report(self, results: Dict[str, Any]):
        """Generate comprehensive test report."""
        end_time = time.time()
        duration = end_time - self.start_time

        console.print("\n" + "=" * 80)
        console.print("📊 COMPREHENSIVE TEST REPORT")
        console.print("=" * 80)

        # Overall summary
        total_suites = len(results)
        successful_suites = sum(1 for suite in results.values() if suite["successful_scripts"] == suite["total_scripts"])
        total_scripts = sum(suite["total_scripts"] for suite in results.values())
        successful_scripts = sum(suite["successful_scripts"] for suite in results.values())
        total_tests = sum(suite["total_tests"] for suite in results.values())
        passed_tests = sum(suite["passed_tests"] for suite in results.values())

        # Overall status
        if successful_suites == total_suites:
            overall_status = "🎉 ALL SUITES PASSED"
            status_color = "green"
        elif successful_suites > 0:
            overall_status = "⚠️  PARTIAL SUCCESS"
            status_color = "yellow"
        else:
            overall_status = "❌ ALL SUITES FAILED"
            status_color = "red"

        console.print(f"Overall Status: {overall_status}")
        console.print(f"Duration: {duration:.1f} seconds")
        console.print(f"Test Suites: {successful_suites}/{total_suites}")
        console.print(f"Test Scripts: {successful_scripts}/{total_scripts}")
        if total_tests > 0:
            console.print(f"Individual Tests: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")

        # Suite breakdown
        console.print("\n🧪 SUITE BREAKDOWN:")
        table = Table()
        table.add_column("Suite", style="cyan")
        table.add_column("Scripts", style="white")
        table.add_column("Tests", style="white")
        table.add_column("Status", style="green")

        for suite_name, suite_result in results.items():
            scripts_status = f"{suite_result['successful_scripts']}/{suite_result['total_scripts']}"
            tests_status = f"{suite_result['passed_tests']}/{suite_result['total_tests']}" if suite_result['total_tests'] > 0 else "N/A"

            if suite_result["successful_scripts"] == suite_result["total_scripts"]:
                status = "✅ PASS"
            else:
                status = "❌ FAIL"

            table.add_row(
                suite_result["suite_name"],
                scripts_status,
                tests_status,
                status
            )

        console.print(table)

        # Failed tests detail
        failed_scripts = []
        for suite_result in results.values():
            for script in suite_result["scripts"]:
                if not script["success"]:
                    failed_scripts.append(script)

        if failed_scripts:
            console.print("\n❌ FAILED SCRIPTS:")
            for script in failed_scripts:
                console.print(f"   • {script['script']} (Suite: {script['suite']})")
                if script.get("error"):
                    console.print(f"     Error: {script['error'][:100]}...")

        # Save detailed results
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": duration,
            "results": results,
            "summary": {
                "total_suites": total_suites,
                "successful_suites": successful_suites,
                "total_scripts": total_scripts,
                "successful_scripts": successful_scripts,
                "total_tests": total_tests,
                "passed_tests": passed_tests
            }
        }

        report_file = self.project_root / "scripts" / "comprehensive_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        console.print(f"\n📄 Detailed report saved to: {report_file}")

        # Generate simple summary
        summary_file = self.project_root / "scripts" / "test_summary.txt"
        with open(summary_file, 'w') as f:
            f.write("COMPREHENSIVE TEST SUMMARY\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration:.1f} seconds\n")
            f.write(f"Overall Status: {overall_status}\n\n")
            f.write(f"Test Suites: {successful_suites}/{total_suites}\n")
            f.write(f"Test Scripts: {successful_scripts}/{total_scripts}\n")
            if total_tests > 0:
                f.write(f"Individual Tests: {passed_tests}/{total_tests}\n")

        console.print(f"📋 Summary saved to: {summary_file}")

    async def run_all_tests(self, skip_optional: bool = False):
        """Run all test suites in proper order."""
        console.print(Panel.fit(
            "[bold blue]🚀 LLM Documentation Ecosystem Test Runner[/bold blue]\n"
            "[dim]Running comprehensive test suites in dependency order[/dim]"
        ))

        # Check service availability
        console.print("🔍 Checking service availability...")
        services_available = await self.check_services_availability()

        available_count = sum(services_available.values())
        total_services = len(services_available)

        console.print(f"Services Available: {available_count}/{total_services}")

        if available_count < total_services:
            console.print("⚠️  Some services not available - integration and CLI tests may be limited")

        # Run test suites
        results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            overall_task = progress.add_task("Running test suites...", total=len(self.test_suites))

            for suite_name, suite_config in self.test_suites.items():
                # Skip optional suites if requested or if services aren't available
                if suite_config.get("optional", False) and (skip_optional or available_count < total_services):
                    progress.update(overall_task, description=f"Skipping {suite_config['name']} (optional)")
                    progress.update(overall_task, advance=1)
                    continue

                progress.update(overall_task, description=f"Running {suite_config['name']}")

                suite_result = await self.run_test_suite(suite_name, suite_config)
                results[suite_name] = suite_result

                progress.update(overall_task, advance=1)

        # Generate comprehensive report
        self.generate_report(results)

        return results

async def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM Documentation Ecosystem Test Runner")
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    parser.add_argument("--suite", help="Run specific test suite (validation, services, integration, cli, performance)")
    parser.add_argument("--skip-optional", action="store_true", help="Skip optional test suites")
    parser.add_argument("--list", action="store_true", help="List available test suites")

    args = parser.parse_args()

    runner = TestRunner()

    if args.list:
        console.print("Available Test Suites:")
        for suite_name, suite_config in runner.test_suites.items():
            optional = " (optional)" if suite_config.get("optional") else ""
            console.print(f"  • {suite_name}: {suite_config['description']}{optional}")
            console.print(f"    Scripts: {len(suite_config['scripts'])}")
        return

    if args.suite:
        if args.suite not in runner.test_suites:
            console.print(f"❌ Unknown test suite: {args.suite}")
            console.print("Use --list to see available suites")
            return

        suite_config = runner.test_suites[args.suite]
        result = await runner.run_test_suite(args.suite, suite_config)
        runner.generate_report({args.suite: result})

    elif args.all:
        await runner.run_all_tests(skip_optional=args.skip_optional)

    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
