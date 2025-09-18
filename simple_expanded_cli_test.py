#!/usr/bin/env python3
"""
Simple test of the expanded CLI ecosystem using the production CLI
Tests all service adapters through the unified CLI interface
"""

import subprocess
import sys
import json
import time
from typing import List, Dict, Any, Tuple


class SimpleExpandedCLITester:
    """
    Tests the expanded CLI through the production CLI executable
    """
    
    def __init__(self):
        self.cli_path = "/tmp/ecosystem-cli-fixed.py"
        self.test_results: List[Dict[str, Any]] = []
    
    def run_cli_command(self, service: str, command: str) -> Tuple[bool, str, float]:
        """Run a CLI command and return success, output, and execution time"""
        start_time = time.time()
        try:
            # Run the CLI command
            result = subprocess.run(
                [sys.executable, self.cli_path, service, command],
                capture_output=True,
                text=True,
                timeout=10
            )
            execution_time = time.time() - start_time
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            return success, output, execution_time
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return False, "Command timed out", execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            return False, f"Exception: {str(e)}", execution_time
    
    def test_service_commands(self, service: str, commands: List[str]) -> None:
        """Test multiple commands for a service"""
        print(f"\n🔧 Testing {service.upper()} Service")
        print("-" * 40)
        
        service_results = {"service": service, "commands": [], "success_count": 0, "total_count": 0}
        
        for command in commands:
            success, output, exec_time = self.run_cli_command(service, command)
            
            command_result = {
                "command": command,
                "success": success,
                "execution_time": exec_time,
                "output_length": len(output),
                "error": output if not success else None
            }
            
            service_results["commands"].append(command_result)
            service_results["total_count"] += 1
            if success:
                service_results["success_count"] += 1
            
            # Display result
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} {command}: {'SUCCESS' if success else 'FAILED'} ({exec_time:.3f}s)")
            if not success:
                # Show first line of error for brevity
                error_line = output.split('\n')[0] if output else "Unknown error"
                print(f"    ↳ Error: {error_line}")
        
        self.test_results.append(service_results)
    
    def run_all_tests(self) -> None:
        """Run tests on all available services"""
        print("🚀 Starting Simple Expanded CLI Tests")
        print("=" * 60)
        
        # Test core services with new adapters
        self.test_service_commands("analysis-service", ["status", "health"])
        self.test_service_commands("orchestrator", ["status", "peers"])
        
        # Test newly implemented adapter services
        self.test_service_commands("doc-store", ["status"])  # Note: CLI might use different naming
        self.test_service_commands("memory-agent", ["status"])
        self.test_service_commands("discovery-agent", ["status"])
        self.test_service_commands("bedrock-proxy", ["status"])
        self.test_service_commands("frontend", ["status"])
        self.test_service_commands("interpreter", ["status"])
        self.test_service_commands("github-mcp", ["status"])
        self.test_service_commands("source-agent", ["status"])
        
        # Test overall ecosystem health
        print(f"\n🌐 Testing Overall Ecosystem Health")
        print("-" * 40)
        
        health_success, health_output, health_time = self.run_cli_command("health", "")
        status_icon = "✅" if health_success else "❌"
        print(f"  {status_icon} ecosystem health: {'SUCCESS' if health_success else 'FAILED'} ({health_time:.3f}s)")
        
        if health_success:
            # Try to extract service count from health output
            lines = health_output.split('\n')
            for line in lines:
                if "services healthy" in line.lower() or "health summary" in line.lower():
                    print(f"    ↳ {line.strip()}")
                    break
        
        # Generate report
        self.generate_report()
    
    def generate_report(self) -> None:
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 SIMPLE EXPANDED CLI TEST RESULTS")
        print("=" * 60)
        
        # Calculate statistics
        total_services = len(self.test_results)
        total_commands = sum(result["total_count"] for result in self.test_results)
        total_successful = sum(result["success_count"] for result in self.test_results)
        overall_success_rate = (total_successful / total_commands * 100) if total_commands > 0 else 0
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Services Tested: {total_services}")
        print(f"   Commands Executed: {total_commands}")
        print(f"   Successful Commands: {total_successful}")
        print(f"   Success Rate: {overall_success_rate:.1f}%")
        
        # Service-by-service results
        print(f"\n🔧 Service Results:")
        fully_working_services = 0
        
        for result in self.test_results:
            service = result["service"]
            success_count = result["success_count"]
            total_count = result["total_count"]
            rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            if rate == 100:
                fully_working_services += 1
                status_icon = "✅"
            elif rate >= 75:
                status_icon = "⚠️"
            else:
                status_icon = "❌"
            
            print(f"   {status_icon} {service:20}: {success_count}/{total_count} ({rate:.1f}%)")
            
            # Show failed commands
            failed_commands = [cmd for cmd in result["commands"] if not cmd["success"]]
            for failed_cmd in failed_commands:
                error_preview = failed_cmd["error"][:60] + "..." if failed_cmd["error"] and len(failed_cmd["error"]) > 60 else failed_cmd["error"]
                print(f"     └─ {failed_cmd['command']}: {error_preview}")
        
        # Summary assessment
        print(f"\n📊 Adapter Implementation Status:")
        print(f"   Fully Working Services: {fully_working_services}/{total_services}")
        print(f"   Services with Adapters: {total_services} (expanded from original 4)")
        
        # Overall status
        if overall_success_rate >= 90:
            status = "🎉 EXCELLENT - Most adapters working!"
        elif overall_success_rate >= 75:
            status = "👍 GOOD - Many adapters operational"
        elif overall_success_rate >= 50:
            status = "⚠️  FAIR - Some adapters need work"
        else:
            status = "❌ NEEDS IMPROVEMENT - Many issues detected"
        
        print(f"\n{status}")
        print("=" * 60)


def main():
    """Main test runner"""
    tester = SimpleExpandedCLITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
