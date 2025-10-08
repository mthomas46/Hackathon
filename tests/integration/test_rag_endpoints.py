"""
Integration tests for RAG (Retrieval-Augmented Generation) endpoints.

Tests the complete RAG workflow:
1. Document ingestion
2. Embedding generation
3. Semantic search
4. RAG answer synthesis
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any


BASE_URL = "http://localhost:5087/api/v1"


class TestRAGEndpoints:
    """Test RAG endpoints with real service interaction."""
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """TEST 1: Verify service is running."""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:5087/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            print("✅ TEST 1 PASSED: Health check")
    
    @pytest.mark.asyncio
    async def test_embeddings_stats(self):
        """TEST 2: Get embedding statistics."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/embeddings/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "total_documents" in data["data"]
            assert "vectorized_documents" in data["data"]
            assert "coverage_percentage" in data["data"]
            print(f"✅ TEST 2 PASSED: Stats - {data['data']['total_documents']} docs, "
                  f"{data['data']['coverage_percentage']}% vectorized")
    
    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """TEST 3: Semantic search functionality."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/search/semantic",
                params={"query": "artificial intelligence", "limit": 5, "min_similarity": 0.3}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "results" in data["data"]
            assert "count" in data["data"]
            print(f"✅ TEST 3 PASSED: Semantic search found {data['data']['count']} results")
    
    @pytest.mark.asyncio
    async def test_rag_synthesis_basic(self):
        """TEST 4: Basic RAG answer synthesis."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/synthesis/generate",
                params={
                    "query": "What is machine learning?",
                    "temperature": 0.3,
                    "max_tokens": 200
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "answer" in data["data"]
            assert "query" in data["data"]
            assert "synthesis_method" in data["data"]
            print(f"✅ TEST 4 PASSED: RAG synthesis method={data['data']['synthesis_method']}")
    
    @pytest.mark.asyncio
    async def test_rag_synthesis_with_context(self):
        """TEST 5: RAG with document context."""
        # First, ensure we have some documents
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Check if we have documents
            stats_response = await client.get(f"{BASE_URL}/embeddings/stats")
            stats = stats_response.json()
            total_docs = stats["data"]["total_documents"]
            
            if total_docs == 0:
                pytest.skip("No documents available for testing")
            
            # Test RAG synthesis
            response = await client.post(
                f"{BASE_URL}/synthesis/generate",
                params={
                    "query": "test query",
                    "semantic_weight": 0.7,
                    "temperature": 0.3,
                    "max_tokens": 300
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "search_metadata" in data["data"]
            print(f"✅ TEST 5 PASSED: RAG with {data['data']['context_documents_used']} context docs")
    
    @pytest.mark.asyncio
    async def test_rag_parameter_validation(self):
        """TEST 6: Parameter validation."""
        async with httpx.AsyncClient() as client:
            # Test invalid temperature
            response = await client.post(
                f"{BASE_URL}/synthesis/generate",
                params={"query": "test", "temperature": 2.0}  # Invalid: > 1.0
            )
            assert response.status_code == 422  # Validation error
            
            # Test invalid semantic_weight
            response = await client.post(
                f"{BASE_URL}/synthesis/generate",
                params={"query": "test", "semantic_weight": 1.5}  # Invalid: > 1.0
            )
            assert response.status_code == 422
            print("✅ TEST 6 PASSED: Parameter validation working")
    
    @pytest.mark.asyncio
    async def test_rag_end_to_end_workflow(self):
        """TEST 7: Complete RAG workflow."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Check stats
            stats_response = await client.get(f"{BASE_URL}/embeddings/stats")
            assert stats_response.status_code == 200
            
            # Step 2: Semantic search
            search_response = await client.post(
                f"{BASE_URL}/search/semantic",
                params={"query": "test", "limit": 3}
            )
            assert search_response.status_code == 200
            
            # Step 3: RAG synthesis
            rag_response = await client.post(
                f"{BASE_URL}/synthesis/generate",
                params={"query": "test", "max_tokens": 100}
            )
            assert rag_response.status_code == 200
            data = rag_response.json()
            
            # Verify response structure
            assert "answer" in data["data"]
            assert "sources" in data["data"]
            assert "search_metadata" in data["data"]
            print(f"✅ TEST 7 PASSED: End-to-end workflow complete")
    
    @pytest.mark.asyncio
    async def test_rag_performance(self):
        """TEST 8: Performance benchmarks."""
        import time
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Measure RAG synthesis time
            start = time.time()
            response = await client.post(
                f"{BASE_URL}/synthesis/generate",
                params={"query": "performance test", "max_tokens": 100}
            )
            elapsed = time.time() - start
            
            assert response.status_code == 200
            assert elapsed < 30.0, f"RAG took {elapsed:.1f}s, should be < 30s"
            print(f"✅ TEST 8 PASSED: RAG completed in {elapsed:.2f}s")


def test_sync_wrapper():
    """Run async tests in sync context."""
    async def run_all():
        test = TestRAGEndpoints()
        await test.test_health_check()
        await test.test_embeddings_stats()
        await test.test_rag_synthesis_basic()
        print("\n✅ All core tests passed!")
    
    asyncio.run(run_all())


if __name__ == "__main__":
    print("🧪 Running RAG Integration Tests...")
    print("=" * 60)
    test_sync_wrapper()

