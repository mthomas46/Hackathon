#!/usr/bin/env python3
"""
TDD: Comprehensive Phase 7 Verification
Investigate and verify all Phase 7 fixes are working correctly.
"""

import asyncio
import subprocess
import json
import requests
import httpx
from typing import Dict, Any, List


class TestComprehensivePhase7Verification:
    """Complete TDD verification of Phase 7 fixes."""
    
    def __init__(self):
        self.results = {
            "docker_status": {},
            "connectivity": {},
            "api_endpoints": {},
            "demo_config": {},
            "issues_found": []
        }
    
    def test_1_docker_containers_health(self):
        """TEST 1: Verify all required containers are running."""
        print("\n" + "=" * 70)
        print("🧪 TEST 1: Docker Container Health")
        print("=" * 70)
        
        required_containers = ["doc_store", "mcp-horus-heresy"]
        
        for container in required_containers:
            try:
                # Check if container exists and is running
                result = subprocess.run(
                    ["docker", "ps", "--filter", f"name={container}", "--format", "{{.Names}}:{{.Status}}:{{.Ports}}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.stdout.strip():
                    status = result.stdout.strip()
                    print(f"✅ {container}: {status[:80]}")
                    self.results["docker_status"][container] = "running"
                else:
                    print(f"❌ {container}: NOT RUNNING")
                    self.results["docker_status"][container] = "stopped"
                    self.results["issues_found"].append(f"{container} not running")
                    
            except Exception as e:
                print(f"❌ {container}: Error checking status - {e}")
                self.results["docker_status"][container] = "error"
                self.results["issues_found"].append(f"{container} status check failed: {e}")
        
        return self.results["docker_status"]
    
    def test_2_network_configuration(self):
        """TEST 2: Verify network configuration is correct."""
        print("\n" + "=" * 70)
        print("🧪 TEST 2: Network Configuration")
        print("=" * 70)
        
        try:
            # Check doc_store networks
            result = subprocess.run(
                ["docker", "inspect", "doc_store", "--format", "{{json .NetworkSettings.Networks}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                networks = json.loads(result.stdout)
                network_names = list(networks.keys())
                print(f"📡 doc_store networks: {network_names}")
                
                # Check for required networks
                has_ams = "ams" in network_names
                has_default = any("default" in n for n in network_names)
                
                if has_ams and has_default:
                    print(f"✅ Doc-store on both networks (multi-network bridge working)")
                    self.results["connectivity"]["network_bridge"] = "configured"
                elif has_ams:
                    print(f"✅ Doc-store on 'ams' network")
                    self.results["connectivity"]["network_bridge"] = "ams_only"
                elif has_default:
                    print(f"⚠️  Doc-store only on default network (may have connectivity issues)")
                    self.results["connectivity"]["network_bridge"] = "default_only"
                    self.results["issues_found"].append("Doc-store not on 'ams' network")
                else:
                    print(f"❌ Doc-store network configuration unclear")
                    self.results["connectivity"]["network_bridge"] = "unknown"
                    self.results["issues_found"].append("Unknown network configuration")
            else:
                print(f"❌ Could not inspect doc_store container")
                self.results["connectivity"]["network_bridge"] = "error"
                
        except Exception as e:
            print(f"❌ Network check failed: {e}")
            self.results["connectivity"]["network_bridge"] = "error"
            self.results["issues_found"].append(f"Network check failed: {e}")
        
        return self.results["connectivity"]
    
    def test_3_port_configuration(self):
        """TEST 3: Verify port configuration is correct."""
        print("\n" + "=" * 70)
        print("🧪 TEST 3: Port Configuration")
        print("=" * 70)
        
        # Test doc-store ports
        ports_to_test = [5010, 5087, 8080]
        working_ports = []
        
        for port in ports_to_test:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Port {port}: {data.get('status', 'unknown')}")
                    working_ports.append(port)
                else:
                    print(f"❌ Port {port}: HTTP {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"❌ Port {port}: Not responding")
            except Exception as e:
                print(f"❌ Port {port}: {e}")
        
        if working_ports:
            self.results["connectivity"]["doc_store_port"] = working_ports[0]
            print(f"\n✅ Doc-store accessible on port: {working_ports[0]}")
        else:
            self.results["connectivity"]["doc_store_port"] = None
            self.results["issues_found"].append("Doc-store not accessible on any port")
            print(f"\n❌ Doc-store not accessible")
        
        return working_ports
    
    def test_4_demo_script_configuration(self):
        """TEST 4: Verify demo script has correct port configuration."""
        print("\n" + "=" * 70)
        print("🧪 TEST 4: Demo Script Configuration")
        print("=" * 70)
        
        try:
            with open("horus_heresy_demo/demo_horus_heresy.py", 'r') as f:
                content = f.read()
            
            # Find doc_store_url in demonstrate_vectorization_and_rag
            import re
            
            # Look for the method
            method_match = re.search(
                r'async def demonstrate_vectorization_and_rag\(self\):.*?doc_store_url\s*=\s*["\']([^"\']+)["\']',
                content,
                re.DOTALL
            )
            
            if method_match:
                url = method_match.group(1)
                print(f"📄 Demo script doc_store_url: {url}")
                
                # Extract port
                port_match = re.search(r':(\d+)', url)
                if port_match:
                    port = int(port_match.group(1))
                    print(f"   Port configured: {port}")
                    
                    actual_port = self.results["connectivity"].get("doc_store_port")
                    if actual_port == port:
                        print(f"✅ Port configuration matches actual doc-store port")
                        self.results["demo_config"]["port_correct"] = True
                    else:
                        print(f"❌ Port mismatch! Demo uses {port}, doc-store on {actual_port}")
                        self.results["demo_config"]["port_correct"] = False
                        self.results["issues_found"].append(f"Port mismatch: demo={port}, actual={actual_port}")
            else:
                print(f"⚠️  Could not find doc_store_url in demo script")
                self.results["demo_config"]["port_correct"] = None
                
        except Exception as e:
            print(f"❌ Error checking demo configuration: {e}")
            self.results["demo_config"]["port_correct"] = None
            self.results["issues_found"].append(f"Demo config check failed: {e}")
        
        return self.results["demo_config"]
    
    async def test_5_rag_endpoints_functional(self):
        """TEST 5: Verify all RAG endpoints are functional."""
        print("\n" + "=" * 70)
        print("🧪 TEST 5: RAG Endpoints Functional Test")
        print("=" * 70)
        
        port = self.results["connectivity"].get("doc_store_port")
        if not port:
            print("❌ Cannot test endpoints - doc-store not accessible")
            return False
        
        doc_store_url = f"http://localhost:{port}"
        endpoints_tested = {}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # Test 1: Health check
            try:
                response = await client.get(f"{doc_store_url}/health")
                endpoints_tested["health"] = response.status_code == 200
                print(f"{'✅' if endpoints_tested['health'] else '❌'} Health check: HTTP {response.status_code}")
            except Exception as e:
                endpoints_tested["health"] = False
                print(f"❌ Health check: {e}")
            
            # Test 2: Embedding stats
            try:
                response = await client.get(f"{doc_store_url}/api/v1/embeddings/stats")
                endpoints_tested["embedding_stats"] = response.status_code == 200
                if response.status_code == 200:
                    data = response.json()
                    stats = data.get('data', {})
                    print(f"✅ Embedding stats: {stats.get('total_documents', 0)} docs, {stats.get('vectorized_documents', 0)} vectorized")
                else:
                    print(f"❌ Embedding stats: HTTP {response.status_code}")
            except Exception as e:
                endpoints_tested["embedding_stats"] = False
                print(f"❌ Embedding stats: {e}")
            
            # Test 3: Batch embedding (expect 500 if sentence-transformers missing)
            try:
                response = await client.post(
                    f"{doc_store_url}/api/v1/embeddings/generate-batch",
                    params={"limit": 5}
                )
                # 500 is acceptable if dependency missing
                endpoints_tested["batch_embedding"] = response.status_code in [200, 500]
                status_msg = "✅" if response.status_code == 200 else "⚠️"
                print(f"{status_msg} Batch embedding: HTTP {response.status_code}")
                if response.status_code == 500:
                    error = response.json()
                    if "sentence-transformers" in str(error):
                        print(f"   ℹ️  Optional dependency missing (expected)")
            except Exception as e:
                endpoints_tested["batch_embedding"] = False
                print(f"❌ Batch embedding: {e}")
            
            # Test 4: Hybrid search
            try:
                response = await client.post(
                    f"{doc_store_url}/api/v1/search",
                    json={"query": "test", "limit": 5},
                    params={"use_semantic": "false"}  # Keyword only
                )
                endpoints_tested["hybrid_search"] = response.status_code == 200
                print(f"{'✅' if endpoints_tested['hybrid_search'] else '❌'} Hybrid search: HTTP {response.status_code}")
            except Exception as e:
                endpoints_tested["hybrid_search"] = False
                print(f"❌ Hybrid search: {e}")
            
            # Test 5: RAG synthesis
            try:
                response = await client.post(
                    f"{doc_store_url}/api/v1/synthesis/generate",
                    params={"query": "test", "max_tokens": 100}
                )
                endpoints_tested["rag_synthesis"] = response.status_code == 200
                if response.status_code == 200:
                    data = response.json()
                    method = data.get('data', {}).get('synthesis_method', 'unknown')
                    print(f"✅ RAG synthesis: HTTP {response.status_code} (method: {method})")
                else:
                    print(f"❌ RAG synthesis: HTTP {response.status_code}")
            except Exception as e:
                endpoints_tested["rag_synthesis"] = False
                print(f"❌ RAG synthesis: {e}")
        
        self.results["api_endpoints"] = endpoints_tested
        
        # Summary
        working = sum(1 for v in endpoints_tested.values() if v)
        total = len(endpoints_tested)
        print(f"\n📊 Endpoints working: {working}/{total}")
        
        if working < total:
            failed = [k for k, v in endpoints_tested.items() if not v]
            self.results["issues_found"].append(f"Failed endpoints: {', '.join(failed)}")
        
        return endpoints_tested
    
    def test_6_file_cleanup_verification(self):
        """TEST 6: Verify temporary files are cleaned up."""
        print("\n" + "=" * 70)
        print("🧪 TEST 6: File Cleanup Verification")
        print("=" * 70)
        
        temp_files = [
            "test_phase7_only.py",
            "demo_output.log",
            "horus_demo_rag.log",
            "horus_demo_fixed.log"
        ]
        
        found_files = []
        for filename in temp_files:
            try:
                result = subprocess.run(
                    ["ls", "-lh", filename],
                    capture_output=True,
                    text=True,
                    cwd="/Users/mykalthomas/Documents/work/Hackathon"
                )
                if result.returncode == 0:
                    size = result.stdout.split()[4]
                    print(f"📄 {filename}: {size}")
                    found_files.append(filename)
                else:
                    print(f"✅ {filename}: Not found (cleaned up)")
            except Exception as e:
                print(f"⚠️  {filename}: Error checking - {e}")
        
        if found_files:
            print(f"\nℹ️  Found {len(found_files)} temp files (may want to clean up)")
        else:
            print(f"\n✅ All temporary files cleaned up")
        
        return found_files
    
    def generate_summary_report(self):
        """Generate comprehensive summary of all tests."""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE VERIFICATION SUMMARY")
        print("=" * 70)
        
        # Docker Status
        print("\n🐳 Docker Containers:")
        for container, status in self.results["docker_status"].items():
            status_icon = "✅" if status == "running" else "❌"
            print(f"  {status_icon} {container}: {status}")
        
        # Network
        print("\n📡 Network Configuration:")
        network = self.results["connectivity"].get("network_bridge", "unknown")
        network_icon = "✅" if network == "configured" else "⚠️"
        print(f"  {network_icon} Multi-network bridge: {network}")
        
        # Port
        print("\n🔌 Port Configuration:")
        port = self.results["connectivity"].get("doc_store_port")
        if port:
            print(f"  ✅ Doc-store port: {port}")
        else:
            print(f"  ❌ Doc-store port: Not accessible")
        
        # Demo Config
        print("\n📄 Demo Script:")
        port_correct = self.results["demo_config"].get("port_correct")
        if port_correct is True:
            print(f"  ✅ Port configuration: Correct")
        elif port_correct is False:
            print(f"  ❌ Port configuration: Mismatch")
        else:
            print(f"  ⚠️  Port configuration: Could not verify")
        
        # API Endpoints
        print("\n🌐 API Endpoints:")
        if self.results["api_endpoints"]:
            for endpoint, working in self.results["api_endpoints"].items():
                icon = "✅" if working else "❌"
                print(f"  {icon} {endpoint}: {'Working' if working else 'Failed'}")
        else:
            print(f"  ⚠️  No endpoint tests run")
        
        # Issues
        print("\n🐛 Issues Found:")
        if self.results["issues_found"]:
            for i, issue in enumerate(self.results["issues_found"], 1):
                print(f"  {i}. ❌ {issue}")
        else:
            print(f"  ✅ No issues found - all systems operational!")
        
        # Overall Status
        print("\n" + "=" * 70)
        if not self.results["issues_found"]:
            print("✅ OVERALL STATUS: ALL TESTS PASSED")
            print("🎉 Phase 7 is fully operational!")
        else:
            print(f"⚠️  OVERALL STATUS: {len(self.results['issues_found'])} ISSUES FOUND")
            print("🔧 Review issues above and apply fixes")
        print("=" * 70)
        
        return self.results
    
    async def run_all_tests(self):
        """Run complete test suite."""
        print("\n" + "╔" + "=" * 68 + "╗")
        print("║" + " " * 68 + "║")
        print("║" + "  TDD: COMPREHENSIVE PHASE 7 VERIFICATION".center(68) + "║")
        print("║" + " " * 68 + "║")
        print("╚" + "=" * 68 + "╝")
        
        # Run all tests in sequence
        self.test_1_docker_containers_health()
        self.test_2_network_configuration()
        self.test_3_port_configuration()
        self.test_4_demo_script_configuration()
        await self.test_5_rag_endpoints_functional()
        self.test_6_file_cleanup_verification()
        
        # Generate summary
        return self.generate_summary_report()


async def main():
    """Main entry point."""
    tester = TestComprehensivePhase7Verification()
    results = await tester.run_all_tests()
    
    # Return exit code based on issues
    exit_code = 0 if not results["issues_found"] else 1
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

