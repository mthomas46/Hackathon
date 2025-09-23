#!/usr/bin/env python3
"""
Document Persistence Test Runner

Comprehensive test runner for all document persistence features including:
- Unit tests for core functionality
- Integration tests across services  
- Performance benchmarks and stress tests
- End-to-end validation scenarios
"""

import os
import sys
import subprocess
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DocumentPersistenceTestRunner:
    """Comprehensive test runner for document persistence features."""

    def __init__(self):
        self.project_root = project_root
        self.test_results = {}
        self.start_time = None
        self.end_time = None

    def run_all_tests(self, test_types: List[str] = None, verbose: bool = True) -> Dict[str, Any]:
        """Run all document persistence tests."""
        self.start_time = time.time()
        
        print("🧪 Document Persistence Test Suite")
        print("=" * 60)
        print(f"⏰ Test run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Project root: {self.project_root}")
        print()

        # Available test types
        available_tests = {
            "unit": self._run_unit_tests,
            "integration": self._run_integration_tests,
            "performance": self._run_performance_tests,
            "e2e": self._run_e2e_validation,
            "stress": self._run_stress_tests
        }

        # Default to all tests if none specified
        if not test_types:
            test_types = list(available_tests.keys())

        # Run requested test types
        for test_type in test_types:
            if test_type in available_tests:
                print(f"\n🔍 Running {test_type.upper()} Tests")
                print("-" * 40)
                
                try:
                    result = available_tests[test_type](verbose)
                    self.test_results[test_type] = result
                    
                    # Print summary
                    if isinstance(result, dict):
                        passed = result.get("passed", 0)
                        total = result.get("total", 0)
                        print(f"✅ {test_type.upper()}: {passed}/{total} tests passed")
                    else:
                        print(f"✅ {test_type.upper()}: Completed")
                        
                except Exception as e:
                    print(f"❌ {test_type.upper()}: Failed with error: {e}")
                    self.test_results[test_type] = {"error": str(e), "passed": 0, "total": 0}
            else:
                print(f"⚠️  Unknown test type: {test_type}")

        self.end_time = time.time()
        
        # Generate final report
        self._generate_final_report()
        
        return self.test_results

    def _run_unit_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run unit tests for document persistence."""
        test_files = [
            "tests/unit/interpreter/test_document_persistence.py"
        ]
        
        return self._run_pytest_tests(test_files, "unit", verbose)

    def _run_integration_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run integration tests for document persistence."""
        test_files = [
            "tests/integration/test_document_persistence_integration.py"
        ]
        
        return self._run_pytest_tests(test_files, "integration", verbose)

    def _run_performance_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run performance tests for document persistence."""
        test_files = [
            "tests/performance/test_document_persistence_performance.py"
        ]
        
        # Add performance markers
        extra_args = ["-m", "performance", "--tb=short"]
        return self._run_pytest_tests(test_files, "performance", verbose, extra_args)

    def _run_stress_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run stress tests for document persistence."""
        test_files = [
            "tests/performance/test_document_persistence_performance.py"
        ]
        
        # Run only stress test class
        extra_args = ["-k", "TestDocumentPersistenceStressTest", "--tb=short"]
        return self._run_pytest_tests(test_files, "stress", verbose, extra_args)

    def _run_e2e_validation(self, verbose: bool = True) -> Dict[str, Any]:
        """Run end-to-end validation using existing proof scripts."""
        print("Running comprehensive E2E validation...")
        
        try:
            # Run the E2E validation script
            validation_script = self.project_root / "scripts/validation/e2e_document_persistence_validation.py"
            
            if validation_script.exists():
                # Make script executable
                os.chmod(validation_script, 0o755)
                
                # Run validation script
                cmd = [sys.executable, str(validation_script), "--comprehensive"]
                if verbose:
                    cmd.append("--format=table")
                else:
                    cmd.append("--format=json")
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
                
                return {
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "passed": 1 if result.returncode == 0 else 0,
                    "total": 1,
                    "success": result.returncode == 0
                }
            else:
                return {
                    "error": "E2E validation script not found",
                    "passed": 0,
                    "total": 1,
                    "success": False
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "passed": 0,
                "total": 1,
                "success": False
            }

    def _run_pytest_tests(self, test_files: List[str], test_type: str, verbose: bool = True, extra_args: List[str] = None) -> Dict[str, Any]:
        """Run pytest tests and parse results."""
        if extra_args is None:
            extra_args = []
        
        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]
        
        # Add test files that exist
        existing_files = []
        for test_file in test_files:
            file_path = self.project_root / test_file
            if file_path.exists():
                existing_files.append(str(file_path))
            else:
                print(f"⚠️  Test file not found: {test_file}")
        
        if not existing_files:
            return {
                "error": f"No test files found for {test_type}",
                "passed": 0,
                "total": 0,
                "success": False
            }
        
        cmd.extend(existing_files)
        
        # Add verbosity and formatting
        if verbose:
            cmd.extend(["-v", "--tb=short"])
        else:
            cmd.extend(["-q"])
        
        # Add JSON report for parsing
        json_report = self.project_root / f"test_results_{test_type}_{int(time.time())}.json"
        cmd.extend(["--json-report", f"--json-report-file={json_report}"])
        
        # Add extra arguments
        cmd.extend(extra_args)
        
        try:
            # Run pytest
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            # Parse results
            test_result = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
            
            # Try to parse JSON report if available
            if json_report.exists():
                try:
                    with open(json_report, 'r') as f:
                        json_data = json.load(f)
                    
                    summary = json_data.get("summary", {})
                    test_result.update({
                        "passed": summary.get("passed", 0),
                        "failed": summary.get("failed", 0),
                        "error": summary.get("error", 0),
                        "skipped": summary.get("skipped", 0),
                        "total": summary.get("total", 0),
                        "duration": json_data.get("duration", 0),
                        "success": result.returncode == 0
                    })
                    
                    # Clean up JSON report
                    json_report.unlink()
                    
                except Exception as e:
                    print(f"Failed to parse JSON report: {e}")
                    # Fallback to basic result
                    test_result.update({
                        "passed": 1 if result.returncode == 0 else 0,
                        "total": 1,
                        "success": result.returncode == 0
                    })
            else:
                # Fallback parsing from stdout
                lines = result.stdout.split('\n')
                passed = 0
                failed = 0
                
                for line in lines:
                    if "passed" in line and "failed" in line:
                        # Try to extract numbers from pytest summary
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "passed" and i > 0:
                                try:
                                    passed = int(parts[i-1])
                                except ValueError:
                                    pass
                            elif part == "failed" and i > 0:
                                try:
                                    failed = int(parts[i-1])
                                except ValueError:
                                    pass
                
                test_result.update({
                    "passed": passed,
                    "failed": failed,
                    "total": passed + failed,
                    "success": result.returncode == 0
                })
            
            return test_result
            
        except Exception as e:
            return {
                "error": str(e),
                "passed": 0,
                "total": 0,
                "success": False
            }

    def _generate_final_report(self):
        """Generate final test report."""
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        print(f"\n📋 Final Test Report")
        print("=" * 60)
        print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Summary by test type
        total_passed = 0
        total_tests = 0
        successful_test_types = 0
        total_test_types = len(self.test_results)

        for test_type, result in self.test_results.items():
            if isinstance(result, dict):
                passed = result.get("passed", 0)
                total = result.get("total", 0)
                success = result.get("success", False)
                error = result.get("error")
                
                total_passed += passed
                total_tests += total
                
                if success:
                    successful_test_types += 1
                    status = "✅ PASSED"
                else:
                    status = "❌ FAILED"
                
                print(f"{status} {test_type.upper()}: {passed}/{total} tests")
                if error:
                    print(f"   Error: {error}")
            else:
                print(f"❓ {test_type.upper()}: Unknown result format")

        print()
        print(f"🎯 Overall Summary:")
        print(f"   Test Types: {successful_test_types}/{total_test_types} successful")
        print(f"   Individual Tests: {total_passed}/{total_tests} passed")
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"   Success Rate: {success_rate:.1f}%")
        
        # Overall status
        if successful_test_types == total_test_types and total_passed == total_tests:
            print(f"\n🏆 ALL TESTS PASSED! Document persistence system is working correctly.")
        elif successful_test_types >= total_test_types * 0.8:
            print(f"\n⚠️  Most tests passed. Some issues may need attention.")
        else:
            print(f"\n❌ Significant test failures. Document persistence system needs attention.")

        # Save detailed report
        report_data = {
            "test_run_timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "test_results": self.test_results,
            "summary": {
                "total_test_types": total_test_types,
                "successful_test_types": successful_test_types,
                "total_individual_tests": total_tests,
                "passed_individual_tests": total_passed,
                "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
            }
        }
        
        report_file = self.project_root / f"document_persistence_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file.name}")

    def check_service_health(self) -> bool:
        """Check if required services are running before tests."""
        print("🏥 Checking service health...")
        
        import aiohttp
        
        async def check_services():
            services = [
                ("interpreter", "http://localhost:5120"),
                ("doc_store", "http://localhost:5087"),
                ("orchestrator", "http://localhost:5099")
            ]
            
            healthy_services = 0
            
            async with aiohttp.ClientSession() as session:
                for service_name, service_url in services:
                    try:
                        async with session.get(f"{service_url}/health", 
                                             timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                print(f"   ✅ {service_name}: Healthy")
                                healthy_services += 1
                            else:
                                print(f"   ❌ {service_name}: Unhealthy (HTTP {response.status})")
                    except Exception as e:
                        print(f"   ❌ {service_name}: Unreachable ({e})")
            
            return healthy_services, len(services)
        
        try:
            healthy, total = asyncio.run(check_services())
            
            if healthy == total:
                print(f"✅ All {total} services are healthy")
                return True
            elif healthy >= total * 0.7:
                print(f"⚠️  {healthy}/{total} services healthy - proceeding with limited tests")
                return True
            else:
                print(f"❌ Only {healthy}/{total} services healthy - tests may fail")
                return False
        except Exception as e:
            print(f"❌ Service health check failed: {e}")
            return False


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Document Persistence Test Runner")
    parser.add_argument("--test-types", nargs="+", 
                       choices=["unit", "integration", "performance", "e2e", "stress"],
                       help="Specific test types to run (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--check-health", action="store_true",
                       help="Check service health before running tests")
    parser.add_argument("--skip-health-check", action="store_true",
                       help="Skip service health check")
    
    args = parser.parse_args()
    
    runner = DocumentPersistenceTestRunner()
    
    # Check service health unless skipped
    if not args.skip_health_check:
        if args.check_health or not args.test_types:
            health_ok = runner.check_service_health()
            print()
            
            if not health_ok:
                print("⚠️  Service health issues detected. Continue anyway? (y/N): ", end="")
                response = input().lower()
                if response != 'y':
                    print("Test run cancelled due to service health issues.")
                    return 1
    
    # Run tests
    results = runner.run_all_tests(args.test_types, args.verbose)
    
    # Return appropriate exit code
    total_passed = sum(r.get("passed", 0) for r in results.values() if isinstance(r, dict))
    total_tests = sum(r.get("total", 0) for r in results.values() if isinstance(r, dict))
    
    if total_tests == 0:
        return 2  # No tests run
    elif total_passed == total_tests:
        return 0  # All tests passed
    else:
        return 1  # Some tests failed


if __name__ == "__main__":
    exit(main())
