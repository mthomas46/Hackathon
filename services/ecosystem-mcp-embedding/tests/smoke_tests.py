"""
Smoke tests for embedding service.

Quick sanity checks to verify service is operational.
"""

import requests
import sys
import time


def run_smoke_tests(base_url: str = "http://localhost:8001") -> bool:
    """
    Run smoke tests against embedding service.
    
    Args:
        base_url: Base URL of the service
    
    Returns:
        True if all tests pass, False otherwise
    """
    print("=" * 80)
    print("🔥 RUNNING SMOKE TESTS FOR EMBEDDING SERVICE")
    print("=" * 80)
    print()
    
    all_passed = True
    
    # Test 1: Health Check
    print("Test 1: Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "healthy":
                print("✅ PASSED: Service is healthy")
            else:
                print(f"❌ FAILED: Service unhealthy: {data}")
                all_passed = False
        else:
            print(f"❌ FAILED: Health check returned {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"❌ FAILED: Health check error: {e}")
        all_passed = False
    print()
    
    # Test 2: Root Endpoint
    print("Test 2: Root Endpoint...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "service" in data and "endpoints" in data:
                print("✅ PASSED: Root endpoint working")
            else:
                print(f"❌ FAILED: Unexpected response: {data}")
                all_passed = False
        else:
            print(f"❌ FAILED: Root endpoint returned {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"❌ FAILED: Root endpoint error: {e}")
        all_passed = False
    print()
    
    # Test 3: Single Embedding Generation
    print("Test 3: Single Embedding Generation...")
    try:
        start = time.time()
        response = requests.post(
            f"{base_url}/embed/single",
            json={"text": "Smoke test embedding"},
            timeout=30
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if (len(data["embedding"]) == 768 and 
                data["dimensions"] == 768):
                print(f"✅ PASSED: Single embedding generated ({duration:.2f}s)")
            else:
                print(f"❌ FAILED: Invalid embedding: {len(data.get('embedding', []))} dimensions")
                all_passed = False
        else:
            print(f"❌ FAILED: Single embedding returned {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"❌ FAILED: Single embedding error: {e}")
        all_passed = False
    print()
    
    # Test 4: Batch Embedding Generation
    print("Test 4: Batch Embedding Generation...")
    try:
        start = time.time()
        response = requests.post(
            f"{base_url}/embed/batch",
            json={"texts": ["Test 1", "Test 2", "Test 3"]},
            timeout=30
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if len(data["embeddings"]) == 3:
                print(f"✅ PASSED: Batch embeddings generated ({duration:.2f}s)")
            else:
                print(f"❌ FAILED: Expected 3 embeddings, got {len(data.get('embeddings', []))}")
                all_passed = False
        else:
            print(f"❌ FAILED: Batch embedding returned {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"❌ FAILED: Batch embedding error: {e}")
        all_passed = False
    print()
    
    # Test 5: Cache Functionality
    print("Test 5: Cache Functionality...")
    try:
        # First request (cache miss)
        response1 = requests.post(
            f"{base_url}/embed/single",
            json={"text": "Cache test unique text"},
            timeout=30
        )
        data1 = response1.json()
        duration1 = data1["duration_ms"]
        cached1 = data1["cached"]
        
        # Second request (cache hit)
        response2 = requests.post(
            f"{base_url}/embed/single",
            json={"text": "Cache test unique text"},
            timeout=30
        )
        data2 = response2.json()
        duration2 = data2["duration_ms"]
        cached2 = data2["cached"]
        
        if (not cached1 and cached2 and duration2 < duration1 * 0.1):
            print(f"✅ PASSED: Cache working ({duration1:.1f}ms → {duration2:.1f}ms)")
        else:
            print(f"❌ FAILED: Cache not working properly")
            print(f"   First: cached={cached1}, duration={duration1:.1f}ms")
            print(f"   Second: cached={cached2}, duration={duration2:.1f}ms")
            all_passed = False
    except Exception as e:
        print(f"❌ FAILED: Cache test error: {e}")
        all_passed = False
    print()
    
    # Test 6: OpenAPI Documentation
    print("Test 6: OpenAPI Documentation...")
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "openapi" in data and "paths" in data:
                print("✅ PASSED: OpenAPI docs available")
            else:
                print(f"❌ FAILED: Invalid OpenAPI schema")
                all_passed = False
        else:
            print(f"❌ FAILED: OpenAPI endpoint returned {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"❌ FAILED: OpenAPI docs error: {e}")
        all_passed = False
    print()
    
    # Summary
    print("=" * 80)
    if all_passed:
        print("✅ ALL SMOKE TESTS PASSED")
    else:
        print("❌ SOME SMOKE TESTS FAILED")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    # Allow custom URL from command line
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
    
    success = run_smoke_tests(base_url)
    sys.exit(0 if success else 1)

