"""
TDD Diagnostic Tests for doc_store Route Loading Issue.

These tests expose and validate the fix for doc_store routes not loading.
"""

import pytest
import httpx
import asyncio


@pytest.mark.diagnostic
@pytest.mark.asyncio
class TestDocStoreRoutes:
    """Test that doc_store routes are properly loaded."""
    
    async def test_health_endpoint_works(self):
        """Verify basic health endpoint works (baseline)."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:5087/health")
            assert response.status_code == 200, f"Health endpoint failed: {response.status_code}"
            print(f"✅ Health endpoint working: {response.json()}")
    
    async def test_documents_endpoint_exists(self):
        """Test that POST /api/v1/documents endpoint exists (should fail before fix)."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try to create a document
            response = await client.post(
                "http://localhost:5087/api/v1/documents",
                json={
                    "content": "Test document content",
                    "metadata": {"title": "Test Document"}
                }
            )
            
            print(f"\n📋 POST /api/v1/documents status: {response.status_code}")
            print(f"📋 Response: {response.text[:200]}")
            
            # Should NOT be 404 - that means endpoint not found
            assert response.status_code != 404, \
                "❌ EXPOSED BUG: /api/v1/documents returns 404 (route not loaded)"
            
            # Accept 200, 201 (success), 400 (validation error), or 422 (pydantic validation)
            # These all indicate the endpoint EXISTS
            assert response.status_code in [200, 201, 400, 422], \
                f"Unexpected status: {response.status_code}"
    
    async def test_search_endpoint_exists(self):
        """Test that POST /api/v1/search endpoint exists (should fail before fix)."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                "http://localhost:5087/api/v1/search",
                json={
                    "query": "test query",
                    "limit": 10
                }
            )
            
            print(f"\n📋 POST /api/v1/search status: {response.status_code}")
            print(f"📋 Response: {response.text[:200]}")
            
            # Should NOT be 404
            assert response.status_code != 404, \
                "❌ EXPOSED BUG: /api/v1/search returns 404 (route not loaded)"
            
            # Accept success or validation errors
            assert response.status_code in [200, 201, 400, 422], \
                f"Unexpected status: {response.status_code}"
    
    async def test_list_documents_endpoint_exists(self):
        """Test that GET /api/v1/documents endpoint exists."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:5087/api/v1/documents")
            
            print(f"\n📋 GET /api/v1/documents status: {response.status_code}")
            
            assert response.status_code != 404, \
                "❌ EXPOSED BUG: GET /api/v1/documents returns 404 (route not loaded)"
            
            assert response.status_code in [200, 400, 422], \
                f"Unexpected status: {response.status_code}"
    
    async def test_router_has_routes(self):
        """Test that the router object has routes loaded."""
        # This test checks the app configuration
        # We can't directly access the app, but we can infer from endpoint tests
        print("\n📊 Router validation via endpoint tests...")
        
        endpoints_to_test = [
            ("POST", "/api/v1/documents"),
            ("POST", "/api/v1/search"),
            ("GET", "/api/v1/documents"),
        ]
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            results = {}
            for method, endpoint in endpoints_to_test:
                try:
                    if method == "POST":
                        response = await client.post(
                            f"http://localhost:5087{endpoint}",
                            json={}
                        )
                    else:
                        response = await client.get(f"http://localhost:5087{endpoint}")
                    
                    exists = response.status_code != 404
                    results[f"{method} {endpoint}"] = exists
                    print(f"  {method} {endpoint}: {'✅ EXISTS' if exists else '❌ 404'}")
                    
                except Exception as e:
                    results[f"{method} {endpoint}"] = False
                    print(f"  {method} {endpoint}: ❌ ERROR: {e}")
            
            # At least some routes should exist
            routes_exist = any(results.values())
            assert routes_exist, "❌ NO ROUTES LOADED: All endpoints return 404"


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s', '-m', 'diagnostic'])

