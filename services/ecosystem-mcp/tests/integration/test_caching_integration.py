#!/usr/bin/env python3
"""
Integration Tests: Caching System

Tests end-to-end caching behavior across the full stack.
"""

import asyncio
import time
import pytest

BASE_URL = "http://localhost:8000"


class TestCachingIntegration:
    """Integration tests for caching system."""
    
    @pytest.mark.asyncio
    async def test_rag_response_caching(self):
        """
        Test that RAG responses are cached and served faster on repeat queries.
        
        Expected: First query slow (15-20s), second query fast (<1s)
        """
        question = "What is ecosystem-mcp and what are its main features?"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # First query - cache miss (slow)
            start1 = time.time()
            response1 = await client.post(
                f"{BASE_URL}/api/v1/ask",
                json={
                    "question": question,
                    "n_results": 10,
                    "prefer_recent": True,
                    "temperature": 0.7
                }
            )
            time1 = time.time() - start1
            
            assert response1.status_code == 200
            data1 = response1.json()
            answer1 = data1["answer"]
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Second query - cache hit (fast)
            start2 = time.time()
            response2 = await client.post(
                f"{BASE_URL}/api/v1/ask",
                json={
                    "question": question,
                    "n_results": 10,
                    "prefer_recent": True,
                    "temperature": 0.7
                }
            )
            time2 = time.time() - start2
            
            assert response2.status_code == 200
            data2 = response2.json()
            answer2 = data2["answer"]
            
            # Verify caching worked
            print(f"\n📊 RAG Caching Test:")
            print(f"   First query: {time1:.2f}s")
            print(f"   Second query: {time2:.2f}s")
            print(f"   Speedup: {time1/time2:.1f}x")
            
            # Cache hit should be MUCH faster
            assert time2 < time1 / 5, f"Cache hit should be at least 5x faster (was {time1/time2:.1f}x)"
            assert time2 < 2.0, f"Cached response should be under 2s (was {time2:.2f}s)"
            
            # Answers should be identical
            assert answer1 == answer2, "Cached answer should match original"
    
    @pytest.mark.asyncio
    async def test_search_result_caching(self):
        """
        Test that search results are cached.
        
        Expected: First search ~400ms, second search <50ms
        """
        query = "performance optimization caching"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First search - cache miss
            start1 = time.time()
            response1 = await client.post(
                f"{BASE_URL}/api/v1/search",
                json={"query": query, "n_results": 10}
            )
            time1 = time.time() - start1
            
            assert response1.status_code == 200
            data1 = response1.json()
            
            await asyncio.sleep(1)
            
            # Second search - cache hit
            start2 = time.time()
            response2 = await client.post(
                f"{BASE_URL}/api/v1/search",
                json={"query": query, "n_results": 10}
            )
            time2 = time.time() - start2
            
            assert response2.status_code == 200
            data2 = response2.json()
            
            print(f"\n📊 Search Caching Test:")
            print(f"   First search: {time1:.3f}s")
            print(f"   Second search: {time2:.3f}s")
            print(f"   Speedup: {time1/time2:.1f}x")
            
            # Cache hit should be much faster
            assert time2 < time1 / 3, f"Cache hit should be at least 3x faster"
            assert time2 < 0.1, f"Cached search should be under 100ms"
            
            # Results should match
            assert data1["results"] == data2["results"]
    
    @pytest.mark.asyncio
    async def test_document_query_caching(self):
        """Test that document queries are cached."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First query - cache miss
            start1 = time.time()
            response1 = await client.post(
                f"{BASE_URL}/api/v1/query",
                json={"limit": 10, "offset": 0}
            )
            time1 = time.time() - start1
            
            assert response1.status_code == 200
            data1 = response1.json()
            
            await asyncio.sleep(0.5)
            
            # Second query - cache hit
            start2 = time.time()
            response2 = await client.post(
                f"{BASE_URL}/api/v1/query",
                json={"limit": 10, "offset": 0}
            )
            time2 = time.time() - start2
            
            assert response2.status_code == 200
            data2 = response2.json()
            
            print(f"\n📊 Document Query Caching Test:")
            print(f"   First query: {time1:.3f}s")
            print(f"   Second query: {time2:.3f}s")
            print(f"   Speedup: {time1/time2:.1f}x")
            
            # Cache hit should be faster
            assert time2 < time1 / 2, f"Cache hit should be at least 2x faster"
            assert time2 < 0.05, f"Cached query should be under 50ms"
            
            # Results should match
            assert len(data1["documents"]) == len(data2["documents"])
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_different_params(self):
        """Test that different parameters don't hit the same cache."""
        question1 = "What is caching?"
        question2 = "What is performance?"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Query 1
            response1 = await client.post(
                f"{BASE_URL}/api/v1/ask",
                json={"question": question1}
            )
            assert response1.status_code == 200
            answer1 = response1.json()["answer"]
            
            await asyncio.sleep(1)
            
            # Query 2 (different question)
            response2 = await client.post(
                f"{BASE_URL}/api/v1/ask",
                json={"question": question2}
            )
            assert response2.status_code == 200
            answer2 = response2.json()["answer"]
            
            # Answers should be different
            assert answer1 != answer2, "Different questions should have different answers"
    
    @pytest.mark.asyncio
    async def test_parallel_requests_benefit_from_pooling(self):
        """Test that parallel requests benefit from connection pooling."""
        questions = [
            "What is ecosystem-mcp?",
            "How does caching work?",
            "What is RAG?",
            "What is ChromaDB?",
            "What is Ollama?"
        ]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Fire parallel requests
            start = time.time()
            
            tasks = []
            for question in questions:
                task = client.post(
                    f"{BASE_URL}/api/v1/ask",
                    json={"question": question}
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            elapsed = time.time() - start
            
            # Count successes
            successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            
            print(f"\n📊 Parallel Request Test:")
            print(f"   Total requests: {len(questions)}")
            print(f"   Successful: {successful}")
            print(f"   Total time: {elapsed:.2f}s")
            print(f"   Average time per request: {elapsed/len(questions):.2f}s")
            
            # With connection pooling, parallel requests should complete faster
            # than sequential (which would be ~20s * 5 = 100s)
            assert elapsed < 60, "Parallel requests should complete in under 60s with pooling"


@pytest.mark.asyncio
async def test_end_to_end_performance():
    """
    End-to-end test verifying all optimizations work together.
    
    This simulates a real user workflow:
    1. Search for documents
    2. Ask a question (RAG)
    3. Repeat both (should be much faster)
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n" + "="*80)
        print("END-TO-END PERFORMANCE TEST")
        print("="*80)
        
        # Step 1: Search (cold)
        print("\n1️⃣  Searching for documents (cold)...")
        start = time.time()
        search_response = await client.post(
            f"{BASE_URL}/api/v1/search",
            json={"query": "ecosystem-mcp features"}
        )
        search_time_cold = time.time() - start
        assert search_response.status_code == 200
        print(f"   ✅ Search completed in {search_time_cold:.3f}s")
        
        await asyncio.sleep(1)
        
        # Step 2: RAG query (cold)
        print("\n2️⃣  Asking question (cold)...")
        start = time.time()
        rag_response = await client.post(
            f"{BASE_URL}/api/v1/ask",
            json={"question": "What are the main features of ecosystem-mcp?"}
        )
        rag_time_cold = time.time() - start
        assert rag_response.status_code == 200
        print(f"   ✅ RAG completed in {rag_time_cold:.2f}s")
        
        await asyncio.sleep(2)
        
        # Step 3: Repeat search (warm)
        print("\n3️⃣  Searching for documents (warm/cached)...")
        start = time.time()
        search_response2 = await client.post(
            f"{BASE_URL}/api/v1/search",
            json={"query": "ecosystem-mcp features"}
        )
        search_time_warm = time.time() - start
        assert search_response2.status_code == 200
        print(f"   ✅ Search completed in {search_time_warm:.3f}s")
        
        await asyncio.sleep(1)
        
        # Step 4: Repeat RAG (warm)
        print("\n4️⃣  Asking question (warm/cached)...")
        start = time.time()
        rag_response2 = await client.post(
            f"{BASE_URL}/api/v1/ask",
            json={"question": "What are the main features of ecosystem-mcp?"}
        )
        rag_time_warm = time.time() - start
        assert rag_response2.status_code == 200
        print(f"   ✅ RAG completed in {rag_time_warm:.2f}s")
        
        # Calculate improvements
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        
        search_speedup = search_time_cold / search_time_warm if search_time_warm > 0 else float('inf')
        rag_speedup = rag_time_cold / rag_time_warm if rag_time_warm > 0 else float('inf')
        
        print(f"\n📊 Search Performance:")
        print(f"   Cold: {search_time_cold:.3f}s")
        print(f"   Warm: {search_time_warm:.3f}s")
        print(f"   Speedup: {search_speedup:.1f}x")
        
        print(f"\n📊 RAG Performance:")
        print(f"   Cold: {rag_time_cold:.2f}s")
        print(f"   Warm: {rag_time_warm:.2f}s")
        print(f"   Speedup: {rag_speedup:.1f}x")
        
        print(f"\n📊 Total Time:")
        print(f"   First run: {search_time_cold + rag_time_cold:.2f}s")
        print(f"   Second run: {search_time_warm + rag_time_warm:.2f}s")
        print(f"   Improvement: {(search_time_cold + rag_time_cold) / (search_time_warm + rag_time_warm):.1f}x")
        
        # Verify improvements
        assert search_speedup > 2, f"Search should be at least 2x faster with cache"
        assert rag_speedup > 5, f"RAG should be at least 5x faster with cache"
        
        print("\n✅ ALL END-TO-END TESTS PASSED!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

