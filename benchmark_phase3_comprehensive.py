"""
Comprehensive benchmark for Phase 3 validation.

Tests:
1. Document enrichment cache hit rates
2. BM25 index cold start vs warm start
3. Overlapping document query patterns
4. Cache monitoring metrics
"""

import asyncio
import time
import requests
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"

def test_document_corpus():
    """Verify documents exist in the system."""
    print("\n" + "="*80)
    print("VERIFICATION: Document Corpus")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"\n1. Service health: {response.status_code}")
    
    # Try to get document count
    try:
        response = requests.get(f"{BASE_URL}/api/documents?limit=1")
        if response.status_code == 200:
            print(f"2. Documents endpoint accessible: ✅")
        else:
            print(f"2. Documents endpoint: {response.status_code}")
    except Exception as e:
        print(f"2. Documents endpoint error: {e}")

def benchmark_document_enrichment_cache():
    """Test Phase 3A: Document enrichment caching."""
    print("\n" + "="*80)
    print("BENCHMARK 1: Document Enrichment Cache (Phase 3A)")
    print("="*80)
    
    # Query that should retrieve documents
    queries = [
        "What is Docker container orchestration?",
        "How does Docker handle networking?",
        "What is Docker container orchestration?",  # Repeat for cache
    ]
    
    times = []
    for i, query in enumerate(queries):
        print(f"\n{i+1}. Query: '{query}'")
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/rag/ask/enhanced",
            json={
                "question": query,
                "enable_hybrid_search": True,
                "enable_context_optimization": True,
                "n_results": 10
            }
        )
        elapsed = time.time() - start
        times.append(elapsed)
        
        if response.status_code == 200:
            result = response.json()
            sources = result.get("sources", [])
            confidence = result.get("confidence", 0)
            print(f"   Time: {elapsed:.3f}s")
            print(f"   Sources: {len(sources)}")
            print(f"   Confidence: {confidence:.1f}%")
            
            if i == 2:  # Third query (repeat of first)
                if elapsed < times[0]:
                    speedup = times[0] / elapsed
                    print(f"   🎉 Cache benefit: {speedup:.1f}x faster than first query")
        else:
            print(f"   Error: {response.status_code}")
    
    return {
        "times": times,
        "avg_time": sum(times) / len(times),
        "cache_improvement": times[0] / times[2] if len(times) > 2 and times[2] > 0 else 1.0
    }

def benchmark_bm25_cold_start():
    """Test Phase 3B: BM25 index serialization."""
    print("\n" + "="*80)
    print("BENCHMARK 2: BM25 Index Load Time (Phase 3B)")
    print("="*80)
    
    # Check if BM25 is being used
    print("\n1. Testing hybrid search with BM25...")
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/rag/ask/enhanced",
        json={
            "question": "docker containers kubernetes",
            "enable_hybrid_search": True,
            "semantic_weight": 0.5,
            "keyword_weight": 0.5,
            "n_results": 5
        }
    )
    elapsed = time.time() - start
    
    print(f"   Hybrid search time: {elapsed:.3f}s")
    
    if response.status_code == 200:
        result = response.json()
        metadata = result.get("metadata", {})
        print(f"   Hybrid search: {metadata.get('search_method', 'unknown')}")
        print(f"   Sources: {len(result.get('sources', []))}")
    
    return {"bm25_query_time": elapsed}

def benchmark_overlapping_queries():
    """Test cache effectiveness with overlapping document queries."""
    print("\n" + "="*80)
    print("BENCHMARK 3: Overlapping Document Queries (Phase 3A Impact)")
    print("="*80)
    
    # Related queries that should retrieve overlapping documents
    related_queries = [
        "What is Docker?",
        "How does Docker work?",
        "Docker container basics",
        "Docker image management"
    ]
    
    times = []
    source_overlap = []
    
    for i, query in enumerate(related_queries):
        print(f"\n{i+1}. Query: '{query}'")
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/rag/ask/enhanced",
            json={
                "question": query,
                "enable_hybrid_search": True,
                "n_results": 10
            }
        )
        elapsed = time.time() - start
        times.append(elapsed)
        
        if response.status_code == 200:
            result = response.json()
            sources = result.get("sources", [])
            print(f"   Time: {elapsed:.3f}s")
            print(f"   Sources: {len(sources)}")
            
            if i > 0:
                improvement = (times[0] - elapsed) / times[0] * 100
                if improvement > 0:
                    print(f"   📈 {improvement:.1f}% faster than first query (cache effect)")
    
    avg_time = sum(times) / len(times) if times else 0
    print(f"\n📊 Average time: {avg_time:.3f}s")
    
    return {
        "times": times,
        "avg_time": avg_time,
        "improvement_vs_first": ((times[0] - times[-1]) / times[0] * 100) if times and times[0] > 0 else 0
    }

def get_cache_metrics():
    """Get cache hit rate metrics."""
    print("\n" + "="*80)
    print("MONITORING: Cache Hit Rates")
    print("="*80)
    
    try:
        # Try to get Redis stats
        response = requests.get(f"{BASE_URL}/api/admin/redis/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"\n✅ Redis Stats:")
            print(f"   Connected clients: {stats.get('connected_clients', 'N/A')}")
            print(f"   Used memory: {stats.get('used_memory_human', 'N/A')}")
            print(f"   Keyspace hits: {stats.get('keyspace_hits', 'N/A')}")
            print(f"   Keyspace misses: {stats.get('keyspace_misses', 'N/A')}")
            
            hits = stats.get('keyspace_hits', 0)
            misses = stats.get('keyspace_misses', 0)
            total = hits + misses
            if total > 0:
                hit_rate = (hits / total) * 100
                print(f"   Hit rate: {hit_rate:.1f}%")
                return {"hit_rate": hit_rate, "hits": hits, "misses": misses}
        else:
            print(f"   Redis stats not available: {response.status_code}")
    except Exception as e:
        print(f"   Error getting cache metrics: {e}")
    
    return {}

async def run_all_benchmarks():
    """Run all Phase 3 benchmarks."""
    print("\n" + "="*80)
    print("PHASE 3 COMPREHENSIVE BENCHMARK SUITE")
    print("="*80)
    print("\nValidating Phase 1 + 2 + 3 improvements...")
    
    results = {}
    
    # Verify documents exist
    test_document_corpus()
    
    # Benchmark 1: Document enrichment cache
    results['enrichment'] = benchmark_document_enrichment_cache()
    
    # Benchmark 2: BM25 index
    results['bm25'] = benchmark_bm25_cold_start()
    
    # Benchmark 3: Overlapping queries
    results['overlapping'] = benchmark_overlapping_queries()
    
    # Monitoring: Cache metrics
    results['cache_metrics'] = get_cache_metrics()
    
    # Summary
    print("\n" + "="*80)
    print("COMPREHENSIVE BENCHMARK SUMMARY")
    print("="*80)
    
    print("\nPhase 3A (Document Enrichment Cache):")
    if 'enrichment' in results:
        print(f"  Average time: {results['enrichment']['avg_time']:.3f}s")
        print(f"  Cache improvement: {results['enrichment']['cache_improvement']:.1f}x")
    
    print("\nPhase 3B (BM25 Index):")
    if 'bm25' in results:
        print(f"  Query time: {results['bm25']['bm25_query_time']:.3f}s")
    
    print("\nOverlapping Query Performance:")
    if 'overlapping' in results:
        print(f"  Average time: {results['overlapping']['avg_time']:.3f}s")
        print(f"  Improvement: {results['overlapping']['improvement_vs_first']:.1f}%")
    
    print("\nCache Hit Rates:")
    if 'cache_metrics' in results and 'hit_rate' in results['cache_metrics']:
        metrics = results['cache_metrics']
        print(f"  Hit rate: {metrics['hit_rate']:.1f}%")
        print(f"  Hits: {metrics['hits']}")
        print(f"  Misses: {metrics['misses']}")
    
    print("\n" + "="*80)
    print("Benchmark complete!")
    print("="*80)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())

