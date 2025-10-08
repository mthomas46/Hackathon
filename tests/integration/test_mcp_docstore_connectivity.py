"""
TDD: Diagnose MCP to doc-store connectivity issue.

Test Cases:
1. Doc-store is reachable from host
2. Doc-store is reachable from MCP container
3. Doc-store returns valid responses
4. Network DNS resolution works
5. Port mappings are correct
"""

import subprocess
import json
import requests
import time


class TestMCPDocStoreConnectivity:
    """Systematic TDD to diagnose connectivity."""
    
    def test_1_docstore_from_host(self):
        """TEST 1: Can host reach doc-store?"""
        print("\n🧪 TEST 1: Doc-store reachable from host")
        print("=" * 60)
        
        try:
            response = requests.get("http://localhost:5087/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            print(f"✅ PASS: Doc-store responds on localhost:5087")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('data', {}).get('database_status')}")
            return True
        except Exception as e:
            print(f"❌ FAIL: {e}")
            return False
    
    def test_2_docstore_internal_port(self):
        """TEST 2: Check doc-store internal port."""
        print("\n🧪 TEST 2: Doc-store internal port configuration")
        print("=" * 60)
        
        # Check what port doc-store is actually listening on
        result = subprocess.run(
            ["docker", "exec", "doc_store", "netstat", "-tuln"],
            capture_output=True,
            text=True
        )
        
        print(f"Listening ports in doc-store container:")
        for line in result.stdout.split('\n'):
            if '5010' in line or 'LISTEN' in line:
                print(f"   {line}")
        
        # Check if 5010 is listening
        if ':5010' in result.stdout:
            print(f"✅ PASS: Doc-store listening on port 5010")
            return True
        else:
            print(f"❌ FAIL: Doc-store not listening on expected port 5010")
            return False
    
    def test_3_mcp_can_resolve_docstore(self):
        """TEST 3: Can MCP container resolve 'doc_store' hostname?"""
        print("\n🧪 TEST 3: DNS resolution from MCP container")
        print("=" * 60)
        
        # Get latest MCP container
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=mcp-mcp-horus", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        mcp_containers = [c for c in result.stdout.strip().split('\n') if c]
        if not mcp_containers:
            print("❌ FAIL: No MCP containers found")
            return False
        
        mcp_name = mcp_containers[0]
        print(f"Testing with container: {mcp_name}")
        
        # Test DNS resolution
        result = subprocess.run(
            ["docker", "exec", mcp_name, "nslookup", "doc_store"],
            capture_output=True,
            text=True
        )
        
        print(f"DNS lookup result:")
        print(f"   {result.stdout[:200]}")
        
        if "can't resolve" in result.stderr or "not found" in result.stderr.lower():
            print(f"❌ FAIL: Cannot resolve 'doc_store' hostname")
            print(f"   Error: {result.stderr}")
            return False
        else:
            print(f"✅ PASS: MCP can resolve 'doc_store' hostname")
            return True
    
    def test_4_mcp_can_reach_docstore_port(self):
        """TEST 4: Can MCP reach doc-store on port 5010?"""
        print("\n🧪 TEST 4: Port connectivity from MCP to doc-store")
        print("=" * 60)
        
        # Get latest MCP container
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=mcp-mcp-horus", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        mcp_containers = [c for c in result.stdout.strip().split('\n') if c]
        if not mcp_containers:
            print("❌ FAIL: No MCP containers found")
            return False
        
        mcp_name = mcp_containers[0]
        
        # Try to curl doc_store from MCP
        result = subprocess.run(
            ["docker", "exec", mcp_name, "curl", "-s", "-m", "5", "http://doc_store:5010/health"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"Connection attempt:")
        print(f"   Exit code: {result.returncode}")
        print(f"   Output: {result.stdout[:200]}")
        if result.stderr:
            print(f"   Error: {result.stderr[:200]}")
        
        if result.returncode == 0 and result.stdout:
            try:
                data = json.loads(result.stdout)
                print(f"✅ PASS: MCP can reach doc-store on port 5010")
                print(f"   Status: {data.get('status')}")
                return True
            except:
                print(f"❌ FAIL: Got response but invalid JSON")
                return False
        else:
            print(f"❌ FAIL: Cannot reach doc-store:5010 from MCP")
            return False
    
    def test_5_docstore_api_endpoints(self):
        """TEST 5: Check if doc-store API endpoints are working."""
        print("\n🧪 TEST 5: Doc-store API endpoints functional")
        print("=" * 60)
        
        endpoints = [
            ("/health", "GET"),
            ("/api/v1/embeddings/stats", "GET"),
            ("/api/v1/documents", "GET"),
        ]
        
        all_passed = True
        for endpoint, method in endpoints:
            try:
                url = f"http://localhost:5087{endpoint}"
                response = requests.request(method, url, timeout=5)
                status = "✅" if response.status_code < 400 else "❌"
                print(f"   {status} {method} {endpoint}: HTTP {response.status_code}")
                if response.status_code >= 400:
                    all_passed = False
            except Exception as e:
                print(f"   ❌ {method} {endpoint}: {e}")
                all_passed = False
        
        if all_passed:
            print(f"✅ PASS: All endpoints responding")
        else:
            print(f"❌ FAIL: Some endpoints not responding")
        
        return all_passed
    
    def test_6_network_connectivity(self):
        """TEST 6: Verify both containers on same network."""
        print("\n🧪 TEST 6: Network configuration")
        print("=" * 60)
        
        # Check doc-store network
        result = subprocess.run(
            ["docker", "inspect", "doc_store", "--format", "{{json .NetworkSettings.Networks}}"],
            capture_output=True,
            text=True
        )
        
        doc_store_networks = json.loads(result.stdout)
        print(f"Doc-store networks: {list(doc_store_networks.keys())}")
        
        # Check MCP network
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=mcp-mcp-horus", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        mcp_containers = [c for c in result.stdout.strip().split('\n') if c]
        if mcp_containers:
            mcp_name = mcp_containers[0]
            result = subprocess.run(
                ["docker", "inspect", mcp_name, "--format", "{{json .NetworkSettings.Networks}}"],
                capture_output=True,
                text=True
            )
            
            mcp_networks = json.loads(result.stdout)
            print(f"MCP networks: {list(mcp_networks.keys())}")
            
            # Check for common networks
            common = set(doc_store_networks.keys()) & set(mcp_networks.keys())
            if common:
                print(f"✅ PASS: Both on common network(s): {common}")
                return True
            else:
                print(f"❌ FAIL: No common networks!")
                return False
        else:
            print(f"❌ FAIL: No MCP containers found")
            return False
    
    def run_all_tests(self):
        """Run all diagnostic tests."""
        print("\n" + "=" * 60)
        print("  MCP → DOC-STORE CONNECTIVITY DIAGNOSTIC")
        print("=" * 60)
        
        results = []
        results.append(("Host → Doc-store", self.test_1_docstore_from_host()))
        results.append(("Doc-store port config", self.test_2_docstore_internal_port()))
        results.append(("MCP DNS resolution", self.test_3_mcp_can_resolve_docstore()))
        results.append(("MCP → Doc-store port", self.test_4_mcp_can_reach_docstore_port()))
        results.append(("Doc-store API", self.test_5_docstore_api_endpoints()))
        results.append(("Network config", self.test_6_network_connectivity()))
        
        print("\n" + "=" * 60)
        print("  DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        for name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {name}")
        
        failed = [name for name, passed in results if not passed]
        if failed:
            print(f"\n❌ {len(failed)} test(s) failed:")
            for name in failed:
                print(f"   • {name}")
            print(f"\n💡 Fix these issues to restore connectivity")
        else:
            print(f"\n✅ All tests passed! Connectivity should work.")
        
        return len(failed) == 0


if __name__ == "__main__":
    tester = TestMCPDocStoreConnectivity()
    success = tester.run_all_tests()
    exit(0 if success else 1)

