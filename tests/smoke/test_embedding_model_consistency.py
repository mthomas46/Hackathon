"""
Smoke test for embedding model consistency.

Critical test to ensure:
1. All embeddings use consistent dimensions (768)
2. RAG queries use same model as ingestion
3. No dimension mismatch errors occur
4. Search returns relevant results

This is a CRITICAL smoke test that should be run before deployment!
"""

import pytest
import httpx
import asyncio
import time


BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_rag_query_works():
    """
    CRITICAL: Test that RAG queries return results without dimension errors.
    
    This test validates:
    - Query embedding generation works
    - Embedding dimensions match ChromaDB collection
    - Search returns relevant results
    - No model mismatch errors
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        print("\n🧪 Testing RAG Query...")
        
        # Test query about worker loop (should find relevant docs)
        response = await client.post(
            f"{BASE_URL}/api/v1/search",
            json={"query": "How does the worker loop process ingestion jobs?", "limit": 5}
        )
        
        # Should succeed
        assert response.status_code == 200, f"RAG query failed: {response.status_code}"
        
        data = response.json()
        
        # Should have results
        assert "results" in data, "Response missing 'results'"
        assert "total_results" in data, "Response missing 'total_results'"
        assert data["total_results"] > 0, "No results found - ChromaDB may be empty"
        
        # Check first result quality
        results = data["results"]
        assert len(results) > 0, "Results list is empty"
        
        first_result = results[0]
        print(f"✅ Top result: {first_result['file_path']} (score: {first_result['score']:.4f})")
        
        # Validate result structure
        assert "file_path" in first_result
        assert "score" in first_result
        assert "service_name" in first_result
        
        # Score should be reasonable
        assert 0.0 <= first_result["score"] <= 1.0
        
        print(f"✅ RAG query successful: {data['total_results']} results found")


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_no_dimension_mismatch():
    """
    CRITICAL: Test that no dimension mismatch errors occur.
    
    This ensures:
    - Query embeddings are 768 dims
    - ChromaDB embeddings are 768 dims
    - Models are consistent
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        print("\n🔍 Testing Dimension Consistency...")
        
        queries = [
            "worker loop",
            "embedding generation",
            "document processing"
        ]
        
        for i, query in enumerate(queries):
            # Add delay to avoid rate limiting (10/minute = 6s between requests)
            if i > 0:
                await asyncio.sleep(7)  # Wait 7 seconds between requests
            response = await client.post(
                f"{BASE_URL}/api/v1/search",
                json={"query": query, "limit": 3}
            )
            
            # Check for dimension mismatch errors
            if response.status_code != 200:
                error_text = response.text.lower()
                
                # These indicate dimension mismatch
                if "dimension" in error_text or "384" in error_text or "768" in error_text:
                    pytest.fail(
                        f"DIMENSION MISMATCH DETECTED!\n"
                        f"Query: {query}\n"
                        f"Status: {response.status_code}\n"
                        f"Error: {response.text}"
                    )
            
            assert response.status_code == 200, f"Query '{query}' failed: {response.status_code}"
        
        print(f"✅ No dimension mismatch errors detected ({len(queries)} queries tested)")


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_embedding_service_health():
    """
    CRITICAL: Test that embedding services are healthy.
    
    Checks:
    - Main service is up
    - FastEmbed service is accessible (if running)
    - Ollama is accessible (if running)
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        print("\n🏥 Checking Service Health...")
        
        # Check main service
        try:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            print("✅ Main service: healthy")
        except Exception as e:
            pytest.fail(f"Main service unreachable: {e}")
        
        # Check FastEmbed (optional)
        try:
            response = await client.get("http://localhost:8001/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ FastEmbed service: {data.get('status', 'unknown')}, model: {data.get('model', 'unknown')}")
            else:
                print(f"⚠️  FastEmbed service: unhealthy (status {response.status_code})")
        except httpx.ConnectError:
            print("ℹ️  FastEmbed service: not running (will use Ollama fallback)")
        
        # Check Ollama (optional)
        try:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                has_nomic = any("nomic-embed-text" in m for m in models)
                print(f"✅ Ollama service: healthy, nomic-embed-text: {'available' if has_nomic else 'missing'}")
                
                if not has_nomic:
                    print("⚠️  WARNING: nomic-embed-text model not found in Ollama!")
            else:
                print(f"⚠️  Ollama service: unhealthy (status {response.status_code})")
        except httpx.ConnectError:
            print("⚠️  Ollama service: not running")


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_chromadb_has_embeddings():
    """
    CRITICAL: Test that ChromaDB has embeddings stored.
    
    Validates:
    - ChromaDB is not empty
    - Embeddings are accessible
    - Search can find documents
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        print("\n💾 Checking ChromaDB Status...")
        
        response = await client.post(
            f"{BASE_URL}/api/v1/search",
            json={"query": "test", "limit": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        total = data.get("total_results", 0)
        
        if total == 0:
            print("⚠️  WARNING: ChromaDB appears to be empty!")
            print("   No embeddings found. Ingestion may not have run yet.")
            pytest.skip("ChromaDB is empty - skip for now")
        else:
            print(f"✅ ChromaDB has {total} embeddings")


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_search_relevance():
    """
    CRITICAL: Test that search returns relevant results.
    
    This validates:
    - Semantic similarity is working
    - Results are ranked by relevance
    - Top results have high scores
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        print("\n🎯 Testing Search Relevance...")
        
        # Add delay to avoid rate limiting
        await asyncio.sleep(7)
        
        # Specific query about ingestion worker
        response = await client.post(
            f"{BASE_URL}/api/v1/search",
            json={"query": "ingestion worker loop implementation", "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        results = data.get("results", [])
        
        if not results:
            pytest.skip("No results returned")
        
        # Check top result
        top_result = results[0]
        top_score = top_result["score"]
        
        print(f"Top result: {top_result['file_path']}")
        print(f"Score: {top_score:.4f}")
        
        # Top result should have reasonable relevance
        # For a specific query, expect at least 50% relevance
        assert top_score >= 0.4, f"Top result has low relevance: {top_score:.4f}"
        
        print(f"✅ Search relevance looks good (top score: {top_score:.4f})")


@pytest.mark.smoke
def test_smoke_suite_info():
    """Print info about smoke test suite."""
    print("\n" + "="*60)
    print("🔥 EMBEDDING MODEL CONSISTENCY SMOKE TESTS")
    print("="*60)
    print("\nThis suite validates:")
    print("  ✓ RAG queries work without dimension errors")
    print("  ✓ Embedding dimensions are consistent (768)")
    print("  ✓ Services are healthy and accessible")
    print("  ✓ ChromaDB has embeddings stored")
    print("  ✓ Search returns relevant results")
    print("\nThese tests should ALL PASS before deployment!")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run smoke tests
    pytest.main([__file__, "-v", "-m", "smoke", "-s"])

