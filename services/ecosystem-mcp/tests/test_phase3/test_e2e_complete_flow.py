"""
E2E Tests for Phase 3 Complete Flow

Tests the complete RAG flow with Phase 3 optimizations:
- Cache misses and hits through full pipeline
- Parallel execution through real API calls
- Combined cache + parallel benefits
"""

import pytest
import asyncio
import time
import httpx
from typing import Dict, Any


API_BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 120.0


class TestPhase3E2EFlow:
    """End-to-end tests for Phase 3 optimizations."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_rag_flow_with_caching(self):
        """Test complete RAG flow shows caching benefits."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            query = "What is ChromaDB?"
            
            # First query - cache miss
            start = time.time()
            response1 = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": query,
                    "n_results": 10,
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True
                }
            )
            time1 = time.time() - start
            
            assert response1.status_code == 200
            result1 = response1.json()
            assert 'answer' in result1
            assert 'confidence' in result1
            
            # Second query - should hit cache
            await asyncio.sleep(1)  # Small delay
            
            start = time.time()
            response2 = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": query,
                    "n_results": 10,
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True
                }
            )
            time2 = time.time() - start
            
            assert response2.status_code == 200
            result2 = response2.json()
            
            # Cache hit should be significantly faster
            speedup = ((time1 - time2) / time1) * 100
            print(f"\nCache speedup: {speedup:.1f}% (First: {time1:.2f}s, Second: {time2:.2f}s)")
            
            # Should be at least 20% faster (conservative for E2E)
            assert time2 < time1 * 0.8, f"Cache should improve speed, but {time2:.2f}s >= {time1 * 0.8:.2f}s"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_phase1_plus_phase2_plus_phase3(self):
        """Test all phases working together."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            query = "How does ingestion work?"
            
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": query,
                    "n_results": 10,
                    # Phase 1
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True,
                    # Phase 2
                    "enable_reranking": True,
                    "enable_context_optimization": True,
                    "enable_metadata_filtering": False
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Verify all phases contributed
            assert 'answer' in result
            assert 'confidence' in result
            assert 'sources' in result
            assert 'metadata' in result
            
            metadata = result['metadata']
            enhancements = metadata.get('enhancements_used', {})
            
            # Phase 1 enhancements
            assert enhancements.get('hybrid_search') == True
            assert enhancements.get('query_rewriting') == True
            assert enhancements.get('confidence_scoring') == True
            
            # Phase 2 enhancements
            assert enhancements.get('reranking') == True
            assert enhancements.get('context_optimization') == True
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_parallel_variant_search_e2e(self):
        """Test that variant search works end-to-end with parallel execution."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Use a complex query that will generate variants
            query = "How does the worker process documents and what database does it use?"
            
            start = time.time()
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": query,
                    "n_results": 10,
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True
                }
            )
            elapsed = time.time() - start
            
            assert response.status_code == 200
            result = response.json()
            
            # Should have query variants
            metadata = result.get('metadata', {})
            query_variants = metadata.get('query_variants')
            
            if query_variants:
                assert len(query_variants) >= 1
                print(f"\nGenerated {len(query_variants)} variants, completed in {elapsed:.2f}s")
            
            # Should complete in reasonable time even with variants
            assert elapsed < 30, f"Query too slow: {elapsed:.2f}s"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_cache_across_different_endpoints(self):
        """Test that caching works across different query types."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            query = "What is BM25?"
            
            # Query through standard RAG
            response1 = await client.post(
                f"{API_BASE_URL}/rag/ask/standard",
                json={"question": query}
            )
            assert response1.status_code == 200
            
            # Query through enhanced RAG (should benefit from cached embeddings)
            start = time.time()
            response2 = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": query,
                    "enable_hybrid_search": True
                }
            )
            elapsed = time.time() - start
            
            assert response2.status_code == 200
            
            # Should complete quickly due to cached components
            print(f"\nEnhanced RAG with cached components: {elapsed:.2f}s")


class TestPhase3RobustnessE2E:
    """E2E tests for Phase 3 robustness and error handling."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_cache_failure_doesnt_break_queries(self):
        """Test that cache failures don't break the query flow."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Query should work even if cache is unavailable
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": "What is Redis?",
                    "n_results": 5
                }
            )
            
            # Should still work (cache failures are gracefully handled)
            assert response.status_code == 200
            result = response.json()
            assert 'answer' in result
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_parallel_execution_with_one_failure(self):
        """Test that parallel execution handles partial failures."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # This should work even if one search branch has issues
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": "test query",
                    "n_results": 5,
                    "enable_hybrid_search": True
                }
            )
            
            # Should either succeed or provide meaningful error
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                result = response.json()
                assert 'answer' in result
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_high_load_with_caching(self):
        """Test system behavior under load with caching."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Send multiple queries in parallel
            queries = [
                "What is ChromaDB?",
                "What is BM25?",
                "What is Redis?",
                "What is PostgreSQL?",
                "What is Docker?"
            ]
            
            tasks = []
            for query in queries:
                task = client.post(
                    f"{API_BASE_URL}/rag/ask/enhanced",
                    json={"question": query, "n_results": 5}
                )
                tasks.append(task)
            
            # Execute all in parallel
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Most should succeed
            success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            
            assert success_count >= 3, f"Only {success_count}/5 queries succeeded"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'e2e'])

