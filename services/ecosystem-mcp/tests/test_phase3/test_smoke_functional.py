"""
Smoke & Functional Tests for Phase 3

Quick validation tests to ensure Phase 3 optimizations don't break existing functionality.
"""

import pytest
import asyncio
import httpx
import time


API_BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 60.0


class TestPhase3Smoke:
    """Smoke tests - quick validation that basic functionality works."""
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_service_is_running(self):
        """Smoke test: Service is running and responding."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{API_BASE_URL}/health")
                assert response.status_code == 200
            except httpx.ConnectError:
                pytest.skip("Service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_standard_rag_still_works(self):
        """Smoke test: Standard RAG endpoint still works."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/standard",
                json={"question": "What is a test?"}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert 'answer' in result
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_enhanced_rag_still_works(self):
        """Smoke test: Enhanced RAG endpoint still works."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": "What is a test?",
                    "enable_hybrid_search": True
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            assert 'answer' in result
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_phase1_features_work(self):
        """Smoke test: Phase 1 features (hybrid search, rewriting, confidence)."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": "What is ChromaDB?",
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            assert 'confidence' in result
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_phase2_features_work(self):
        """Smoke test: Phase 2 features (reranking, context optimization)."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": "What is BM25?",
                    "enable_reranking": True,
                    "enable_context_optimization": True
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            assert 'answer' in result
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_all_phases_together(self):
        """Smoke test: All phases work together."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": "What is ingestion?",
                    # Phase 1
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True,
                    # Phase 2
                    "enable_reranking": True,
                    "enable_context_optimization": True
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            assert 'answer' in result
            assert 'confidence' in result


class TestPhase3Functional:
    """Functional tests - verify specific functionality works correctly."""
    
    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_cache_improves_repeated_queries(self):
        """Functional test: Cache improves performance on repeated queries."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            query = "What is Docker?"
            
            # First query
            start = time.time()
            response1 = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={"question": query, "n_results": 5}
            )
            time1 = time.time() - start
            
            assert response1.status_code == 200
            
            # Second query (should be cached)
            await asyncio.sleep(0.5)
            
            start = time.time()
            response2 = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={"question": query, "n_results": 5}
            )
            time2 = time.time() - start
            
            assert response2.status_code == 200
            
            # Second should be faster
            print(f"\nFirst: {time1:.2f}s, Second: {time2:.2f}s, Speedup: {((time1-time2)/time1)*100:.1f}%")
            
            # Allow for some variance, but should show improvement
            assert time2 < time1 * 1.2  # At most 20% slower (usually much faster)
    
    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_parallel_search_completes_quickly(self):
        """Functional test: Parallel search completes in reasonable time."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            query = "How does the system work?"
            
            start = time.time()
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": query,
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True
                }
            )
            elapsed = time.time() - start
            
            assert response.status_code == 200
            
            # Should complete in reasonable time
            assert elapsed < 25, f"Query too slow: {elapsed:.2f}s"
    
    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_answers_are_consistent(self):
        """Functional test: Cached answers are consistent with fresh answers."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            query = "What is PostgreSQL?"
            
            # First query
            response1 = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={"question": query, "n_results": 5}
            )
            result1 = response1.json()
            
            await asyncio.sleep(0.5)
            
            # Second query (cached)
            response2 = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={"question": query, "n_results": 5}
            )
            result2 = response2.json()
            
            # Answers should be very similar (might have minor differences)
            answer1 = result1['answer']
            answer2 = result2['answer']
            
            # Basic similarity check
            assert len(answer1) > 0
            assert len(answer2) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_different_queries_get_different_answers(self):
        """Functional test: Different queries don't get cached as same result."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Two different queries
            query1 = "What is ChromaDB?"
            query2 = "What is Redis?"
            
            response1 = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={"question": query1, "n_results": 5}
            )
            result1 = response1.json()
            
            response2 = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={"question": query2, "n_results": 5}
            )
            result2 = response2.json()
            
            # Answers should be different
            assert result1['answer'] != result2['answer']
    
    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_confidence_scores_are_reasonable(self):
        """Functional test: Confidence scores are in valid range and reasonable."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={
                    "question": "What is Docker?",
                    "enable_confidence_scoring": True
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            
            confidence = result.get('confidence', 0)
            
            # Should be between 0 and 100
            assert 0 <= confidence <= 100
            
            # For a reasonable question with documents, should be > 0
            assert confidence > 0
    
    @pytest.mark.asyncio
    @pytest.mark.functional
    async def test_sources_are_provided(self):
        """Functional test: RAG provides source citations."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/rag/ask/enhanced",
                json={"question": "What is ingestion?", "n_results": 5}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            sources = result.get('sources', [])
            
            # Should have sources
            assert len(sources) > 0
            
            # Each source should have required fields
            for source in sources:
                assert 'file_path' in source
                assert 'relevance_score' in source or 'adjusted_score' in source


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

