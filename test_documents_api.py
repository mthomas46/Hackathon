#!/usr/bin/env python3
"""Test script to diagnose the documents API issue."""

import httpx
import json
import sys

API_BASE = "http://localhost:8000"

def test_api_health():
    """Test if API is running."""
    print("=" * 60)
    print("TEST 1: API Health Check")
    print("=" * 60)
    try:
        response = httpx.get(f"{API_BASE}/api/v1/health", timeout=5.0)
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Response: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_query_endpoint_minimal():
    """Test /api/v1/query with minimal payload."""
    print("\n" + "=" * 60)
    print("TEST 2: Query Endpoint - Minimal Payload")
    print("=" * 60)
    
    payload = {"limit": 20}
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/query",
            json=payload,
            timeout=10.0
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 422:
            print("\n❌ VALIDATION ERROR (422)")
            error_detail = response.json()
            print(f"Error details: {json.dumps(error_detail, indent=2)}")
            return False
        elif response.status_code == 200:
            print("✓ SUCCESS")
            return True
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_query_endpoint_full():
    """Test /api/v1/query with full payload."""
    print("\n" + "=" * 60)
    print("TEST 3: Query Endpoint - Full Payload")
    print("=" * 60)
    
    payload = {
        "service_name": None,
        "file_path": None,
        "phase": None,
        "tags": [],
        "min_word_count": None,
        "max_word_count": None,
        "has_diagrams": None,
        "limit": 20,
        "offset": 0
    }
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/query",
            json=payload,
            timeout=10.0
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 422:
            print("\n❌ VALIDATION ERROR (422)")
            error_detail = response.json()
            print(f"Error details: {json.dumps(error_detail, indent=2)}")
            return False
        elif response.status_code == 200:
            print("✓ SUCCESS")
            data = response.json()
            print(f"Total documents: {data.get('total', 0)}")
            print(f"Returned: {len(data.get('documents', []))}")
            return True
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_openapi_spec():
    """Check OpenAPI spec for query endpoint."""
    print("\n" + "=" * 60)
    print("TEST 4: Check OpenAPI Spec for /query endpoint")
    print("=" * 60)
    
    try:
        response = httpx.get(f"{API_BASE}/openapi.json", timeout=5.0)
        spec = response.json()
        
        # Find the query endpoint
        if "/api/v1/query" in spec.get("paths", {}):
            query_spec = spec["paths"]["/api/v1/query"]["post"]
            print("✓ Found /api/v1/query endpoint")
            
            # Get request body schema
            if "requestBody" in query_spec:
                schema_ref = query_spec["requestBody"]["content"]["application/json"]["schema"]["$ref"]
                schema_name = schema_ref.split("/")[-1]
                
                schema = spec["components"]["schemas"][schema_name]
                print(f"\nSchema: {schema_name}")
                print(f"Required fields: {schema.get('required', [])}")
                print(f"\nAll properties:")
                for prop, details in schema.get("properties", {}).items():
                    prop_type = details.get("type", "unknown")
                    default = details.get("default", "no default")
                    print(f"  - {prop}: {prop_type} (default: {default})")
                return True
        else:
            print("✗ /api/v1/query not found in OpenAPI spec")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_documents_endpoint():
    """Test /api/v1/documents endpoint as alternative."""
    print("\n" + "=" * 60)
    print("TEST 5: Documents List Endpoint")
    print("=" * 60)
    
    try:
        response = httpx.get(
            f"{API_BASE}/api/v1/documents",
            params={"limit": 20, "offset": 0},
            timeout=10.0
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ SUCCESS")
            data = response.json()
            print(f"Total documents: {data.get('total', 0)}")
            print(f"Returned: {len(data.get('documents', []))}")
            return True
        else:
            print(f"✗ Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "█" * 60)
    print("  DOCUMENTS API DIAGNOSTIC TEST SUITE")
    print("█" * 60 + "\n")
    
    results = []
    
    # Test 1: Health check
    results.append(("API Health", test_api_health()))
    
    if not results[0][1]:
        print("\n❌ API is not running. Cannot continue tests.")
        print("Start the API with:")
        print("  cd services/ecosystem-mcp")
        print("  python3 -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Test 2-5: Various endpoint tests
    results.append(("Query - Minimal", test_query_endpoint_minimal()))
    results.append(("Query - Full", test_query_endpoint_full()))
    results.append(("OpenAPI Spec", test_openapi_spec()))
    results.append(("Documents Endpoint", test_documents_endpoint()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10s} {name}")
    
    print("\n" + "=" * 60)
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60 + "\n")
    
    if not results[1][1]:  # Query minimal failed
        print("🔍 DIAGNOSIS:")
        print("The /api/v1/query endpoint is rejecting the minimal payload.")
        print("This explains why the dashboard hangs with a 422 error.")
        print("\n💡 SOLUTION:")
        print("Check TEST 4 output above for required fields, or")
        print("use /api/v1/documents endpoint instead (TEST 5).")

if __name__ == "__main__":
    main()

