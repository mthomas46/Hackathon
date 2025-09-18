#!/usr/bin/env python3
"""
Power User CLI Test - Advanced Capabilities
Tests document store browsing, prompt store operations, and advanced CLI features
"""

import subprocess
import sys
import json
import time
from typing import List, Dict, Any, Tuple, Optional


class PowerUserCLITester:
    """
    Advanced CLI tester focusing on power user capabilities
    """
    
    def __init__(self):
        self.cli_path = "/tmp/ecosystem-cli-fixed.py"
        self.test_results: List[Dict[str, Any]] = []
        self.services_tested = set()
    
    def run_cli_command(self, service: str, command: str, timeout: int = 15) -> Tuple[bool, str, float]:
        """Run a CLI command with enhanced error handling"""
        start_time = time.time()
        try:
            # Run the CLI command
            result = subprocess.run(
                [sys.executable, self.cli_path, service, command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            execution_time = time.time() - start_time
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            return success, output, execution_time
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return False, f"Command timed out after {timeout}s", execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            return False, f"Exception: {str(e)}", execution_time
    
    def test_doc_store_browsing(self) -> None:
        """Test comprehensive document store browsing capabilities"""
        print("📁 TESTING DOC STORE BROWSING CAPABILITIES")
        print("=" * 60)
        
        doc_store_tests = [
            ("status", "Get doc store status and health"),
            ("health", "Check doc store health endpoints"),
            ("documents", "Browse available documents"),
            ("collections", "List document collections"),
            ("stats", "Get storage statistics")
        ]
        
        service_results = {"service": "doc-store", "tests": [], "success_count": 0}
        
        for command, description in doc_store_tests:
            print(f"\n🔸 Testing: {description}")
            success, output, exec_time = self.run_cli_command("doc-store", command)
            
            test_result = {
                "command": command,
                "description": description,
                "success": success,
                "execution_time": exec_time,
                "output_preview": output[:200] + "..." if len(output) > 200 else output,
                "full_output": output
            }
            
            service_results["tests"].append(test_result)
            if success:
                service_results["success_count"] += 1
            
            # Display result with output preview
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} {command}: {'SUCCESS' if success else 'FAILED'} ({exec_time:.3f}s)")
            
            if success:
                # Show meaningful output preview
                lines = output.split('\n')[:3]
                for line in lines:
                    if line.strip():
                        print(f"    ↳ {line.strip()}")
            else:
                error_line = output.split('\n')[0] if output else "Unknown error"
                print(f"    ↳ Error: {error_line}")
        
        self.test_results.append(service_results)
        self.services_tested.add("doc-store")
    
    def test_prompt_store_operations(self) -> None:
        """Test prompt store operations and browsing"""
        print("\n📝 TESTING PROMPT STORE OPERATIONS")
        print("=" * 60)
        
        prompt_store_tests = [
            ("status", "Get prompt store status"),
            ("health", "Check prompt store health"),
            ("prompts", "Browse available prompts"),
            ("categories", "List prompt categories"),
            ("templates", "List prompt templates"),
            ("stats", "Get prompt statistics")
        ]
        
        service_results = {"service": "prompt_store", "tests": [], "success_count": 0}
        
        for command, description in prompt_store_tests:
            print(f"\n🔸 Testing: {description}")
            success, output, exec_time = self.run_cli_command("prompt_store", command)
            
            test_result = {
                "command": command,
                "description": description,
                "success": success,
                "execution_time": exec_time,
                "output_preview": output[:200] + "..." if len(output) > 200 else output,
                "full_output": output
            }
            
            service_results["tests"].append(test_result)
            if success:
                service_results["success_count"] += 1
            
            # Display result
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} {command}: {'SUCCESS' if success else 'FAILED'} ({exec_time:.3f}s)")
            
            if success:
                lines = output.split('\n')[:3]
                for line in lines:
                    if line.strip():
                        print(f"    ↳ {line.strip()}")
            else:
                error_line = output.split('\n')[0] if output else "Unknown error"
                print(f"    ↳ Error: {error_line}")
        
        self.test_results.append(service_results)
        self.services_tested.add("prompt_store")
    
    def test_memory_agent_advanced(self) -> None:
        """Test advanced memory agent capabilities"""
        print("\n🧠 TESTING MEMORY AGENT ADVANCED FEATURES")
        print("=" * 60)
        
        memory_tests = [
            ("status", "Memory agent status and health"),
            ("memories", "Browse stored memories"),
            ("contexts", "List conversation contexts"),
            ("stats", "Memory usage statistics")
        ]
        
        service_results = {"service": "memory-agent", "tests": [], "success_count": 0}
        
        for command, description in memory_tests:
            print(f"\n🔸 Testing: {description}")
            success, output, exec_time = self.run_cli_command("memory-agent", command)
            
            test_result = {
                "command": command,
                "description": description,
                "success": success,
                "execution_time": exec_time,
                "output_preview": output[:200] + "..." if len(output) > 200 else output
            }
            
            service_results["tests"].append(test_result)
            if success:
                service_results["success_count"] += 1
            
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} {command}: {'SUCCESS' if success else 'FAILED'} ({exec_time:.3f}s)")
            
            if success:
                lines = output.split('\n')[:2]
                for line in lines:
                    if line.strip():
                        print(f"    ↳ {line.strip()}")
            else:
                error_line = output.split('\n')[0] if output else "Unknown error"
                print(f"    ↳ Error: {error_line}")
        
        self.test_results.append(service_results)
        self.services_tested.add("memory-agent")
    
    def test_bedrock_proxy_advanced(self) -> None:
        """Test Bedrock proxy advanced capabilities"""
        print("\n🤖 TESTING BEDROCK PROXY AI CAPABILITIES")
        print("=" * 60)
        
        bedrock_tests = [
            ("status", "Bedrock proxy service status"),
            ("models", "List available AI models"),
            ("test-connection", "Test AWS Bedrock connection"),
            ("stats", "AI service statistics")
        ]
        
        service_results = {"service": "bedrock-proxy", "tests": [], "success_count": 0}
        
        for command, description in bedrock_tests:
            print(f"\n🔸 Testing: {description}")
            success, output, exec_time = self.run_cli_command("bedrock-proxy", command)
            
            test_result = {
                "command": command,
                "description": description,
                "success": success,
                "execution_time": exec_time,
                "output_preview": output[:200] + "..." if len(output) > 200 else output
            }
            
            service_results["tests"].append(test_result)
            if success:
                service_results["success_count"] += 1
            
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} {command}: {'SUCCESS' if success else 'FAILED'} ({exec_time:.3f}s)")
            
            if success:
                lines = output.split('\n')[:2]
                for line in lines:
                    if line.strip():
                        print(f"    ↳ {line.strip()}")
            else:
                error_line = output.split('\n')[0] if output else "Unknown error"
                print(f"    ↳ Error: {error_line}")
        
        self.test_results.append(service_results)
        self.services_tested.add("bedrock-proxy")
    
    def test_discovery_agent_ecosystem(self) -> None:
        """Test discovery agent ecosystem mapping"""
        print("\n🔍 TESTING DISCOVERY AGENT ECOSYSTEM MAPPING")
        print("=" * 60)
        
        discovery_tests = [
            ("status", "Discovery agent status"),
            ("services", "Discover ecosystem services"),
            ("topology", "Map service topology"),
            ("stats", "Discovery statistics")
        ]
        
        service_results = {"service": "discovery-agent", "tests": [], "success_count": 0}
        
        for command, description in discovery_tests:
            print(f"\n🔸 Testing: {description}")
            success, output, exec_time = self.run_cli_command("discovery-agent", command)
            
            test_result = {
                "command": command,
                "description": description,
                "success": success,
                "execution_time": exec_time,
                "output_preview": output[:200] + "..." if len(output) > 200 else output
            }
            
            service_results["tests"].append(test_result)
            if success:
                service_results["success_count"] += 1
            
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} {command}: {'SUCCESS' if success else 'FAILED'} ({exec_time:.3f}s)")
            
            if success:
                lines = output.split('\n')[:2]
                for line in lines:
                    if line.strip():
                        print(f"    ↳ {line.strip()}")
            else:
                error_line = output.split('\n')[0] if output else "Unknown error"
                print(f"    ↳ Error: {error_line}")
        
        self.test_results.append(service_results)
        self.services_tested.add("discovery-agent")
    
    def test_interpreter_capabilities(self) -> None:
        """Test interpreter code execution capabilities"""
        print("\n⚡ TESTING INTERPRETER CODE EXECUTION")
        print("=" * 60)
        
        interpreter_tests = [
            ("status", "Interpreter service status"),
            ("languages", "List supported languages"),
            ("sessions", "List active sessions"),
            ("stats", "Execution statistics")
        ]
        
        service_results = {"service": "interpreter", "tests": [], "success_count": 0}
        
        for command, description in interpreter_tests:
            print(f"\n🔸 Testing: {description}")
            success, output, exec_time = self.run_cli_command("interpreter", command)
            
            test_result = {
                "command": command,
                "description": description,
                "success": success,
                "execution_time": exec_time,
                "output_preview": output[:200] + "..." if len(output) > 200 else output
            }
            
            service_results["tests"].append(test_result)
            if success:
                service_results["success_count"] += 1
            
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} {command}: {'SUCCESS' if success else 'FAILED'} ({exec_time:.3f}s)")
            
            if success:
                lines = output.split('\n')[:2]
                for line in lines:
                    if line.strip():
                        print(f"    ↳ {line.strip()}")
            else:
                error_line = output.split('\n')[0] if output else "Unknown error"
                print(f"    ↳ Error: {error_line}")
        
        self.test_results.append(service_results)
        self.services_tested.add("interpreter")
    
    def test_ecosystem_health_overview(self) -> None:
        """Test comprehensive ecosystem health overview"""
        print("\n🌐 TESTING ECOSYSTEM HEALTH OVERVIEW")
        print("=" * 60)
        
        print(f"\n🔸 Testing: Complete ecosystem health check")
        success, output, exec_time = self.run_cli_command("health", "")
        
        status_icon = "✅" if success else "❌"
        print(f"  {status_icon} ecosystem health: {'SUCCESS' if success else 'FAILED'} ({exec_time:.3f}s)")
        
        if success:
            # Parse and display health summary
            lines = output.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['health summary', 'services healthy', 'ecosystem status']):
                    print(f"    ↳ {line.strip()}")
        else:
            error_line = output.split('\n')[0] if output else "Unknown error"
            print(f"    ↳ Error: {error_line}")
        
        return success
    
    def generate_power_user_report(self) -> None:
        """Generate comprehensive power user capability report"""
        print("\n" + "=" * 70)
        print("📊 POWER USER CLI CAPABILITIES REPORT")
        print("=" * 70)
        
        # Calculate overall statistics
        total_tests = sum(len(result["tests"]) for result in self.test_results)
        total_successful = sum(result["success_count"] for result in self.test_results)
        overall_success_rate = (total_successful / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 Power User Test Summary:")
        print(f"   Services Tested: {len(self.services_tested)}")
        print(f"   Total Commands: {total_tests}")
        print(f"   Successful Commands: {total_successful}")
        print(f"   Success Rate: {overall_success_rate:.1f}%")
        
        # Service-specific results
        print(f"\n🔧 Service-Specific Results:")
        for result in self.test_results:
            service = result["service"]
            success_count = result["success_count"]
            total_count = len(result["tests"])
            rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            if rate == 100:
                status_icon = "✅"
            elif rate >= 75:
                status_icon = "⚠️"
            else:
                status_icon = "❌"
            
            print(f"   {status_icon} {service:20}: {success_count}/{total_count} ({rate:.1f}%)")
            
            # Show failed commands
            failed_tests = [test for test in result["tests"] if not test["success"]]
            for failed_test in failed_tests:
                print(f"     └─ {failed_test['command']}: {failed_test.get('description', 'Failed')}")
        
        # Power user capabilities assessment
        print(f"\n💪 Power User Capabilities Assessment:")
        
        capabilities = {
            "📁 Document Browsing": "doc-store" in self.services_tested,
            "📝 Prompt Management": "prompt_store" in self.services_tested,
            "🧠 Memory Operations": "memory-agent" in self.services_tested,
            "🤖 AI Model Access": "bedrock-proxy" in self.services_tested,
            "🔍 Service Discovery": "discovery-agent" in self.services_tested,
            "⚡ Code Execution": "interpreter" in self.services_tested
        }
        
        available_capabilities = sum(1 for available in capabilities.values() if available)
        
        for capability, available in capabilities.items():
            status = "✅ AVAILABLE" if available else "❌ NOT TESTED"
            print(f"   {capability}: {status}")
        
        print(f"\n📊 Capability Coverage: {available_capabilities}/{len(capabilities)} ({available_capabilities/len(capabilities)*100:.1f}%)")
        
        # Overall assessment
        if overall_success_rate >= 90 and available_capabilities >= 5:
            status = "🚀 EXCELLENT - Full power user capabilities operational!"
        elif overall_success_rate >= 75 and available_capabilities >= 4:
            status = "👍 GOOD - Most power user features working"
        elif overall_success_rate >= 50:
            status = "⚠️  FAIR - Basic power user features available"
        else:
            status = "❌ NEEDS IMPROVEMENT - Limited capabilities"
        
        print(f"\n{status}")
        
        # Usage recommendations
        print(f"\n💡 Power User Recommendations:")
        if "doc-store" in self.services_tested:
            print("   📁 Use 'doc-store documents' to browse available documentation")
            print("   📁 Use 'doc-store search --query <term>' for targeted searches")
        
        if "prompt_store" in self.services_tested:
            print("   📝 Use 'prompt_store prompts' to browse available prompts")
            print("   📝 Use 'prompt_store categories' to explore prompt organization")
        
        if "memory-agent" in self.services_tested:
            print("   🧠 Use 'memory-agent memories' to review conversation history")
            print("   🧠 Use 'memory-agent contexts' to manage conversation contexts")
        
        print("=" * 70)
    
    def run_all_power_user_tests(self) -> None:
        """Run comprehensive power user testing suite"""
        print("🚀 STARTING POWER USER CLI CAPABILITIES TEST")
        print("Testing advanced browsing, management, and operational features")
        print("=" * 70)
        
        # Core storage and content tests
        self.test_doc_store_browsing()
        self.test_prompt_store_operations()
        
        # Advanced service tests
        self.test_memory_agent_advanced()
        self.test_bedrock_proxy_advanced()
        self.test_discovery_agent_ecosystem()
        self.test_interpreter_capabilities()
        
        # Overall ecosystem test
        ecosystem_healthy = self.test_ecosystem_health_overview()
        
        # Generate comprehensive report
        self.generate_power_user_report()


def main():
    """Main power user test runner"""
    tester = PowerUserCLITester()
    tester.run_all_power_user_tests()


if __name__ == "__main__":
    main()
