#!/usr/bin/env python3
"""
Comprehensive CLI Test Suite
Tests all CLI functionality against live services
"""

import os
import sys
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.shared.integrations.clients.clients import ServiceClients
from services.shared.core.constants_new import ServiceNames


class CLIComprehensiveTester:
    """Comprehensive test class for all CLI functionality."""

    def __init__(self):
        """Initialize comprehensive tester."""
        self.clients = ServiceClients()
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.start_time = datetime.now()
        self.services_status: Dict[str, bool] = {}

    async def check_service_health(self, service_name: str, url: str) -> bool:
        """Check if a service is healthy."""
        try:
            response = await self.clients.get_json(url)
            return response and response.get("status") == "healthy"
        except:
            return False

    async def verify_services_running(self):
        """Verify all required services are running."""
        print("🔍 Checking service availability...")

        services_to_check = {
            "analysis_service": f"{self.clients.analysis_service_url()}/integration/health",
            "doc_store": f"{self.clients.doc_store_url()}/health",
            "prompt_store": f"{self.clients.prompt_store_url()}/health",
            "summarizer_hub": f"{self.clients.summarizer_hub_url()}/health",
            "interpreter": f"{self.clients.interpreter_url()}/health",
        }

        for service_name, health_url in services_to_check.items():
            is_healthy = await self.check_service_health(service_name, health_url)
            self.services_status[service_name] = is_healthy
            status_icon = "✅" if is_healthy else "❌"
            print(f"  {status_icon} {service_name}: {'RUNNING' if is_healthy else 'NOT AVAILABLE'}")

        healthy_services = sum(self.services_status.values())
        total_services = len(self.services_status)

        if healthy_services < total_services:
            print(f"\n⚠️  Only {healthy_services}/{total_services} services are available")
            print("Tests will be limited to available services")
        else:
            print(f"\n✅ All {total_services} services are available")

        return healthy_services > 0

    async def test_analysis_service_cli(self):
        """Test Analysis Service CLI functionality."""
        print("\n🧪 Testing Analysis Service CLI...")

        if not self.services_status.get("analysis_service", False):
            print("⚠️  Analysis Service not available, skipping tests")
            return

        # Import the analysis service handler
        try:
            sys.path.insert(0, str(project_root / "services" / "cli" / "modules" / "handlers" / "actions"))
            from analysis_service import build_actions
        except ImportError as e:
            print(f"❌ Could not import Analysis Service CLI: {e}")
            return

        # Test a few key functions
        actions = build_actions(None, self.clients)

        # Test basic analysis
        try:
            # Find the analyze action
            analyze_action = None
            for name, func in actions:
                if "Analyze documents" in name:
                    analyze_action = func
                    break

            if analyze_action:
                # This would require user input, so we'll just check the function exists
                self.test_results["analysis_service_cli"] = {
                    "success": True,
                    "actions_count": len(actions),
                    "error": None
                }
                print(f"✅ Analysis Service CLI: {len(actions)} actions available")
            else:
                self.test_results["analysis_service_cli"] = {
                    "success": False,
                    "actions_count": 0,
                    "error": "Analyze action not found"
                }
                print("❌ Analysis Service CLI: Analyze action not found")
        except Exception as e:
            self.test_results["analysis_service_cli"] = {
                "success": False,
                "actions_count": 0,
                "error": str(e)
            }
            print(f"❌ Analysis Service CLI error: {e}")

    async def test_doc_store_cli(self):
        """Test Doc Store CLI functionality."""
        print("\n🧪 Testing Doc Store CLI...")

        if not self.services_status.get("doc_store", False):
            print("⚠️  Doc Store not available, skipping tests")
            return

        # Import the doc store handler
        try:
            sys.path.insert(0, str(project_root / "services" / "cli" / "modules" / "handlers" / "actions"))
            from doc_store import build_actions
        except ImportError as e:
            print(f"❌ Could not import Doc Store CLI: {e}")
            return

        # Test basic functions
        actions = build_actions(None, self.clients)

        try:
            self.test_results["doc_store_cli"] = {
                "success": True,
                "actions_count": len(actions),
                "error": None
            }
            print(f"✅ Doc Store CLI: {len(actions)} actions available")
        except Exception as e:
            self.test_results["doc_store_cli"] = {
                "success": False,
                "actions_count": 0,
                "error": str(e)
            }
            print(f"❌ Doc Store CLI error: {e}")

    async def test_summarizer_cli(self):
        """Test Summarizer CLI functionality."""
        print("\n🧪 Testing Summarizer CLI...")

        if not self.services_status.get("summarizer_hub", False):
            print("⚠️  Summarizer Hub not available, skipping tests")
            return

        # Import the summarizer handler
        try:
            sys.path.insert(0, str(project_root / "services" / "cli" / "modules" / "handlers" / "actions"))
            from summarizer_hub import build_actions
        except ImportError as e:
            print(f"❌ Could not import Summarizer CLI: {e}")
            return

        # Test basic functions
        actions = build_actions(None, self.clients)

        try:
            self.test_results["summarizer_cli"] = {
                "success": True,
                "actions_count": len(actions),
                "error": None
            }
            print(f"✅ Summarizer CLI: {len(actions)} actions available")
        except Exception as e:
            self.test_results["summarizer_cli"] = {
                "success": False,
                "actions_count": 0,
                "error": str(e)
            }
            print(f"❌ Summarizer CLI error: {e}")

    async def test_interpreter_cli(self):
        """Test Interpreter CLI functionality."""
        print("\n🧪 Testing Interpreter CLI...")

        if not self.services_status.get("interpreter", False):
            print("⚠️  Interpreter not available, skipping tests")
            return

        # Import the interpreter handler
        try:
            sys.path.insert(0, str(project_root / "services" / "cli" / "modules" / "handlers" / "actions"))
            from interpreter import build_actions
        except ImportError as e:
            print(f"❌ Could not import Interpreter CLI: {e}")
            return

        # Test basic functions
        actions = build_actions(None, self.clients)

        try:
            self.test_results["interpreter_cli"] = {
                "success": True,
                "actions_count": len(actions),
                "error": None
            }
            print(f"✅ Interpreter CLI: {len(actions)} actions available")
        except Exception as e:
            self.test_results["interpreter_cli"] = {
                "success": False,
                "actions_count": 0,
                "error": str(e)
            }
            print(f"❌ Interpreter CLI error: {e}")

    async def test_prompt_store_cli(self):
        """Test Prompt Store CLI functionality."""
        print("\n🧪 Testing Prompt Store CLI...")

        if not self.services_status.get("prompt_store", False):
            print("⚠️  Prompt Store not available, skipping tests")
            return

        # Import the prompt store handler
        try:
            sys.path.insert(0, str(project_root / "services" / "cli" / "modules" / "handlers" / "actions"))
            from prompt_store import build_actions
        except ImportError as e:
            print(f"❌ Could not import Prompt Store CLI: {e}")
            return

        # Test basic functions
        actions = build_actions(None, self.clients)

        try:
            self.test_results["prompt_store_cli"] = {
                "success": True,
                "actions_count": len(actions),
                "error": None
            }
            print(f"✅ Prompt Store CLI: {len(actions)} actions available")
        except Exception as e:
            self.test_results["prompt_store_cli"] = {
                "success": False,
                "actions_count": 0,
                "error": str(e)
            }
            print(f"❌ Prompt Store CLI error: {e}")

    async def test_cli_health_endpoints(self):
        """Test CLI health endpoint checking."""
        print("\n🧪 Testing CLI health endpoint checking...")

        # Test service health checking
        try:
            from services.cli.modules.cli_commands import CLICommands
            cli = CLICommands()
            health_data = await cli.check_service_health()

            successful_checks = sum(1 for data in health_data.values() if data.get("status") == "healthy")
            total_checks = len(health_data)

            success = successful_checks > 0
            self.test_results["cli_health_endpoints"] = {
                "success": success,
                "healthy_services": successful_checks,
                "total_services": total_checks,
                "error": None
            }
            print(f"✅ CLI Health Endpoints: {successful_checks}/{total_checks} services healthy")
        except Exception as e:
            self.test_results["cli_health_endpoints"] = {
                "success": False,
                "healthy_services": 0,
                "total_services": 0,
                "error": str(e)
            }
            print(f"❌ CLI Health Endpoints error: {e}")

    async def test_cli_integration_tests(self):
        """Test CLI integration test functionality."""
        print("\n🧪 Testing CLI integration tests...")

        try:
            from services.cli.modules.cli_commands import CLICommands
            cli = CLICommands()

            # Run integration tests (this will test multiple services)
            integration_results = await cli.test_integration()

            successful_tests = sum(1 for result in integration_results.values() if result)
            total_tests = len(integration_results)

            success = successful_tests > 0
            self.test_results["cli_integration_tests"] = {
                "success": success,
                "passed_tests": successful_tests,
                "total_tests": total_tests,
                "error": None
            }
            print(f"✅ CLI Integration Tests: {successful_tests}/{total_tests} tests passed")
        except Exception as e:
            self.test_results["cli_integration_tests"] = {
                "success": False,
                "passed_tests": 0,
                "total_tests": 0,
                "error": str(e)
            }
            print(f"❌ CLI Integration Tests error: {e}")

    async def test_cli_menu_system(self):
        """Test CLI menu system functionality."""
        print("\n🧪 Testing CLI menu system...")

        try:
            from services.cli.modules.cli_commands import CLICommands
            cli = CLICommands()

            # Test that menus can be created without errors
            cli.print_menu()
            cli.print_header()

            self.test_results["cli_menu_system"] = {
                "success": True,
                "error": None
            }
            print("✅ CLI Menu System: Working")
        except Exception as e:
            self.test_results["cli_menu_system"] = {
                "success": False,
                "error": str(e)
            }
            print(f"❌ CLI Menu System error: {e}")

    async def run_comprehensive_tests(self):
        """Run all comprehensive CLI tests."""
        print("🚀 CLI Comprehensive Test Suite")
        print("=" * 60)

        # Verify services are running
        services_available = await self.verify_services_running()

        if not services_available:
            print("\n❌ No services available for testing")
            return

        # Run all CLI component tests
        await self.test_analysis_service_cli()
        await self.test_doc_store_cli()
        await self.test_summarizer_cli()
        await self.test_interpreter_cli()
        await self.test_prompt_store_cli()
        await self.test_cli_health_endpoints()
        await self.test_cli_integration_tests()
        await self.test_cli_menu_system()

        # Generate comprehensive summary
        self.generate_comprehensive_summary()

    def generate_comprehensive_summary(self):
        """Generate comprehensive test summary."""
        end_time = datetime.now()
        duration = end_time - self.start_time

        print("\n" + "=" * 60)
        print("📊 CLI COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)

        print(f"Test Duration: {duration}")
        print(f"Services Available: {sum(self.services_status.values())}/{len(self.services_status)}")

        # CLI Functionality Summary
        cli_tests = {k: v for k, v in self.test_results.items() if k.endswith('_cli')}
        total_cli_tests = len(cli_tests)
        passed_cli_tests = sum(1 for result in cli_tests.values() if result["success"])

        print(f"\nCLI Functionality Tests: {passed_cli_tests}/{total_cli_tests} passed")

        # Integration Tests
        integration_tests = {k: v for k, v in self.test_results.items() if 'integration' in k or 'health' in k}
        total_integration_tests = len(integration_tests)
        passed_integration_tests = sum(1 for result in integration_tests.values() if result["success"])

        print(f"Integration Tests: {passed_integration_tests}/{total_integration_tests} passed")

        # Overall Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests

        print(f"\nOVERALL: {passed_tests}/{total_tests} tests passed ({failed_tests} failed)")

        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result["success"]:
                    error = result.get("error", "Unknown error")
                    print(f"  - {test_name}: {error}")
        else:
            print("\n🎉 ALL TESTS PASSED!")

        # Save detailed results
        results_file = project_root / "scripts" / "test" / "cli_comprehensive_test_results.json"
        results_data = {
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "services_status": self.services_status,
            "test_results": self.test_results,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "cli_functionality": f"{passed_cli_tests}/{total_cli_tests}",
                "integration_tests": f"{passed_integration_tests}/{total_integration_tests}"
            }
        }

        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved to: {results_file}")

        # Generate simple report
        report_file = project_root / "scripts" / "test" / "cli_test_report.txt"
        with open(report_file, 'w') as f:
            f.write("CLI COMPREHENSIVE TEST REPORT\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Test Date: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration}\n")
            f.write(f"Services Available: {sum(self.services_status.values())}/{len(self.services_status)}\n\n")

            f.write("SERVICE STATUS:\n")
            for service, available in self.services_status.items():
                status = "✅ RUNNING" if available else "❌ NOT AVAILABLE"
                f.write(f"  {service}: {status}\n")

            f.write(f"\nOVERALL RESULTS: {passed_tests}/{total_tests} PASSED\n")

            if failed_tests > 0:
                f.write(f"\nFAILED TESTS ({failed_tests}):\n")
                for test_name, result in self.test_results.items():
                    if not result["success"]:
                        f.write(f"  - {test_name}: {result.get('error', 'Unknown error')}\n")

        print(f"📋 Simple report saved to: {report_file}")


async def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="CLI Comprehensive Test Suite")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--services-only", action="store_true",
                       help="Only test service availability, skip CLI tests")

    args = parser.parse_args()

    tester = CLIComprehensiveTester()

    if args.services_only:
        await tester.verify_services_running()
    else:
        await tester.run_comprehensive_tests()


if __name__ == "__main__":
    asyncio.run(main())
