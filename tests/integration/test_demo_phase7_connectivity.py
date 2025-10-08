"""
TDD: Diagnose Phase 7 RAG demonstration failures.

The demo shows "All connection attempts failed" for all RAG operations.
This test will identify what's wrong.
"""

import subprocess
import requests
import json


class TestDemoPhase7Connectivity:
    """TDD to fix Phase 7 RAG demonstration."""
    
    def test_1_docstore_on_correct_port(self):
        """TEST 1: Which port is doc-store actually on?"""
        print("\n🧪 TEST 1: Doc-store port detection")
        print("=" * 60)
        
        # Check docker port mapping
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=doc_store", "--format", "{{.Ports}}"],
            capture_output=True,
            text=True
        )
        
        ports = result.stdout.strip()
        print(f"Doc-store port mapping: {ports}")
        
        # Test different ports
        test_ports = [5010, 5087, 8080]
        working_port = None
        
        for port in test_ports:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✅ PASS: Doc-store responding on port {port}")
                    working_port = port
                    break
            except:
                print(f"❌ Port {port}: Not responding")
        
        if working_port:
            print(f"\n✅ Doc-store is on port: {working_port}")
            return working_port
        else:
            print(f"\n❌ FAIL: Doc-store not accessible on any port")
            return None
    
    def test_2_demo_script_port_config(self):
        """TEST 2: What port does demo script use?"""
        print("\n🧪 TEST 2: Demo script configuration")
        print("=" * 60)
        
        # Read demo script
        with open("horus_heresy_demo/demo_horus_heresy.py", 'r') as f:
            content = f.read()
        
        # Find doc_store_url configurations
        import re
        urls = re.findall(r'doc_store_url\s*=\s*["\']([^"\']+)["\']', content)
        
        print(f"Found {len(urls)} doc_store_url configurations:")
        for i, url in enumerate(set(urls), 1):
            print(f"  {i}. {url}")
        
        # Check for localhost:5010 (wrong) vs localhost:5087 (correct)
        wrong_port = any("5010" in url for url in urls)
        correct_port = any("5087" in url for url in urls)
        
        if wrong_port and not correct_port:
            print(f"\n❌ FAIL: Demo using port 5010 (doc-store is on 5087)")
            return False
        elif correct_port:
            print(f"\n✅ PASS: Demo configured for correct port")
            return True
        else:
            print(f"\n⚠️  WARNING: No doc_store_url found")
            return None
    
    def test_3_rag_endpoints_accessible(self):
        """TEST 3: Can we reach RAG endpoints?"""
        print("\n🧪 TEST 3: RAG endpoint accessibility")
        print("=" * 60)
        
        # Find correct port first
        working_port = self.test_1_docstore_on_correct_port()
        if not working_port:
            print("❌ FAIL: Cannot test endpoints, doc-store not accessible")
            return False
        
        base_url = f"http://localhost:{working_port}/api/v1"
        
        endpoints = [
            "/embeddings/stats",
            "/embeddings/generate",
            "/search/semantic",
            "/synthesis/generate?query=test"
        ]
        
        all_accessible = True
        for endpoint in endpoints:
            try:
                if "generate" in endpoint and endpoint != "/embeddings/stats":
                    response = requests.post(f"{base_url}{endpoint}", timeout=5)
                else:
                    response = requests.get(f"{base_url}{endpoint}", timeout=5)
                
                if response.status_code < 500:
                    print(f"✅ {endpoint}: HTTP {response.status_code}")
                else:
                    print(f"❌ {endpoint}: HTTP {response.status_code}")
                    all_accessible = False
            except Exception as e:
                print(f"❌ {endpoint}: {e}")
                all_accessible = False
        
        if all_accessible:
            print(f"\n✅ PASS: All RAG endpoints accessible")
        else:
            print(f"\n❌ FAIL: Some endpoints not accessible")
        
        return all_accessible
    
    def test_4_demo_error_location(self):
        """TEST 4: Where in demo script is the connection failing?"""
        print("\n🧪 TEST 4: Locate error in demo script")
        print("=" * 60)
        
        with open("horus_heresy_demo/demo_horus_heresy.py", 'r') as f:
            lines = f.readlines()
        
        # Find demonstrate_vectorization_and_rag method
        in_method = False
        method_start = None
        doc_store_url_line = None
        
        for i, line in enumerate(lines, 1):
            if 'def demonstrate_vectorization_and_rag' in line:
                in_method = True
                method_start = i
                print(f"Found method at line {i}")
            
            if in_method and 'doc_store_url' in line and '=' in line:
                doc_store_url_line = i
                print(f"Found doc_store_url at line {i}:")
                print(f"  {line.strip()}")
                
                # Check if it's the wrong port
                if '5010' in line:
                    print(f"  ❌ WRONG PORT! Should be 5087")
                    return i
                elif '5087' in line:
                    print(f"  ✅ Correct port")
                
            if in_method and line.strip().startswith('async def ') and i > method_start + 5:
                break
        
        if doc_store_url_line:
            return doc_store_url_line
        else:
            print("❌ Could not find doc_store_url in method")
            return None
    
    def run_all_tests(self):
        """Run all diagnostic tests."""
        print("\n" + "=" * 60)
        print("  PHASE 7 RAG DEMO FAILURE DIAGNOSTIC")
        print("=" * 60)
        
        # Test 1: Find correct port
        correct_port = self.test_1_docstore_on_correct_port()
        
        # Test 2: Check demo configuration
        demo_configured = self.test_2_demo_script_port_config()
        
        # Test 3: Verify endpoints work
        endpoints_work = self.test_3_rag_endpoints_accessible()
        
        # Test 4: Find exact line to fix
        line_to_fix = self.test_4_demo_error_location()
        
        print("\n" + "=" * 60)
        print("  DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        print(f"\n✅ Doc-store port: {correct_port}")
        print(f"{'✅' if demo_configured else '❌'} Demo configured correctly: {demo_configured}")
        print(f"{'✅' if endpoints_work else '❌'} RAG endpoints accessible: {endpoints_work}")
        
        if line_to_fix and not demo_configured:
            print(f"\n🔧 FIX NEEDED:")
            print(f"   File: horus_heresy_demo/demo_horus_heresy.py")
            print(f"   Line: {line_to_fix}")
            print(f"   Change: doc_store_url from port 5010 to {correct_port}")
            print(f"\n   Command to fix:")
            print(f"   sed -i '' 's/localhost:5010/localhost:{correct_port}/g' horus_heresy_demo/demo_horus_heresy.py")
        
        return correct_port, line_to_fix


if __name__ == "__main__":
    tester = TestDemoPhase7Connectivity()
    tester.run_all_tests()

