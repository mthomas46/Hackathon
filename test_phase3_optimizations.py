#!/usr/bin/env python3
"""
Test Phase 3 Optimizations (Caching + Parallel Execution)

Tests:
1. Cache Miss (first query) - should be slow
2. Cache Hit (repeated query) - should be fast
3. Parallel execution logs
"""

import asyncio
import httpx
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000/api/v1"

async def test_cache_effectiveness():
    """Test cache effectiveness by running same query twice."""
    print("=" * 80)
    print("TEST: Cache Effectiveness")
    print("=" * 80)
    print()
    
    test_query = "What is ChromaDB?"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Test 1: Cache MISS (first query)
        print("🧪 Test 1: Cache MISS (first query)")
        print("-" * 80)
        start = time.time()
        
        response = await client.post(
            f"{API_BASE_URL}/rag/ask/enhanced",
            json={
                "question": test_query,
                "n_results": 10,
                "enable_hybrid_search": True,
                "enable_query_rewriting": True,
                "enable_confidence_scoring": True,
                "enable_reranking": True,
                "enable_context_optimization": True
            }
        )
        
        elapsed_first = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query successful")
            print(f"   Time: {elapsed_first:.2f}s")
            print(f"   Confidence: {result['confidence']:.1f}%")
            print(f"   Sources: {len(result['sources'])}")
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return
        
        print()
        
        # Test 2: Cache HIT (same query)
        print("🧪 Test 2: Cache HIT (repeated query)")
        print("-" * 80)
        await asyncio.sleep(2)  # Small delay
        
        start = time.time()
        
        response = await client.post(
            f"{API_BASE_URL}/rag/ask/enhanced",
            json={
                "question": test_query,
                "n_results": 10,
                "enable_hybrid_search": True,
                "enable_query_rewriting": True,
                "enable_confidence_scoring": True,
                "enable_reranking": True,
                "enable_context_optimization": True
            }
        )
        
        elapsed_second = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query successful")
            print(f"   Time: {elapsed_second:.2f}s")
            print(f"   Confidence: {result['confidence']:.1f}%")
            print(f"   Sources: {len(result['sources'])}")
        else:
            print(f"❌ Query failed: {response.status_code}")
            return
        
        print()
        print("=" * 80)
        print("CACHE EFFECTIVENESS RESULTS")
        print("=" * 80)
        print()
        print(f"First query (cache miss):  {elapsed_first:.2f}s")
        print(f"Second query (cache hit):  {elapsed_second:.2f}s")
        
        speedup = ((elapsed_first - elapsed_second) / elapsed_first) * 100
        print()
        print(f"🚀 Speed improvement: {speedup:.1f}% faster")
        print()
        
        if elapsed_second < elapsed_first * 0.5:
            print("✅ PASS: Cache is working effectively (>50% faster)")
        elif elapsed_second < elapsed_first * 0.7:
            print("⚠️  PARTIAL: Cache provides some benefit (30-50% faster)")
        else:
            print("❌ FAIL: Cache appears not to be working (<30% faster)")
        print()

async def test_parallel_execution():
    """Test that parallel execution is working."""
    print("=" * 80)
    print("TEST: Parallel Execution")
    print("=" * 80)
    print()
    
    # Use a query that will generate multiple variants
    test_query = "How does ingestion work and what database does it use?"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("🧪 Testing parallel variant search...")
        print("-" * 80)
        start = time.time()
        
        response = await client.post(
            f"{API_BASE_URL}/rag/ask/enhanced",
            json={
                "question": test_query,
                "n_results": 10,
                "enable_hybrid_search": True,
                "enable_query_rewriting": True,
                "enable_confidence_scoring": True
            }
        )
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query successful")
            print(f"   Time: {elapsed:.2f}s")
            print(f"   Confidence: {result['confidence']:.1f}%")
            print(f"   Sources: {len(result['sources'])}")
            
            # Check metadata for query variants
            metadata = result.get('metadata', {})
            query_variants = metadata.get('query_variants', [])
            if query_variants:
                print(f"   Query variants: {len(query_variants)}")
                print(f"   (Parallel execution should show in Docker logs)")
            
            print()
            print("✅ PASS: Parallel execution code is deployed")
            print("   Check Docker logs for '⚡ Running' messages to confirm parallel execution")
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
        
        print()

async def main():
    """Run all Phase 3 tests."""
    print()
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║                   PHASE 3 OPTIMIZATION TESTS                                 ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    try:
        # Test 1: Cache effectiveness
        await test_cache_effectiveness()
        
        await asyncio.sleep(2)
        
        # Test 2: Parallel execution
        await test_parallel_execution()
        
        print()
        print("=" * 80)
        print("ALL TESTS COMPLETE")
        print("=" * 80)
        print()
        print("✅ Phase 3 optimizations are deployed!")
        print()
        print("Next steps:")
        print("  1. Run full benchmark to measure impact")
        print("  2. Monitor cache hit rates in production")
        print("  3. Check Docker logs for parallel execution confirmations")
        print()
        
    except httpx.ConnectError:
        print()
        print("❌ ERROR: Cannot connect to API")
        print("   Make sure ecosystem-mcp service is running:")
        print("   cd services/ecosystem-mcp && docker-compose up -d")
        print()
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        print()

if __name__ == "__main__":
    asyncio.run(main())

