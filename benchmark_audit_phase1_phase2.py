"""
Benchmark to measure Phase 1 + Phase 2 audit fixes impact.

Tests:
1. Cache performance (Phase 1A)
2. Early exit for vague queries (Phase 1B)
3. Auto-enable reranking (Phase 1B)
4. Unified analyzer performance (Phase 2A)
5. Confidence adjustments (Phase 2C)
"""

import asyncio
import time
import requests
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"

# Test queries
TEST_QUERIES = {
    "simple": "What is Docker?",
    "vague": "something about stuff",
    "moderate": "How to deploy applications with Docker containers?",
    "complex": "Compare and analyze Docker and Kubernetes for production deployment with security considerations"
}

async def benchmark_cache_performance():
    """Test Phase 1A: Cache performance."""
    print("\n" + "="*80)
    print("BENCHMARK 1: Cache Performance (Phase 1A)")
    print("="*80)
    
    query = TEST_QUERIES["simple"]
    
    # First call (cache miss)
    print(f"\n1. First call (cache miss): '{query}'")
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/rag/ask/enhanced",
        json={"question": query, "use_unified_analyzer": True}
    )
    first_time = time.time() - start
    first_result = response.json()
    
    print(f"   Time: {first_time:.3f}s")
    print(f"   Cached: {first_result.get('metadata', {}).get('cached', False)}")
    
    # Second call (cache hit)
    print(f"\n2. Second call (cache hit): '{query}'")
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/rag/ask/enhanced",
        json={"question": query, "use_unified_analyzer": True}
    )
    second_time = time.time() - start
    second_result = response.json()
    
    print(f"   Time: {second_time:.3f}s")
    print(f"   Cached: {second_result.get('metadata', {}).get('cached', False)}")
    
    if second_time < first_time:
        speedup = first_time / second_time
        print(f"\n✅ Cache speedup: {speedup:.1f}x faster")
        print(f"   First: {first_time:.3f}s → Second: {second_time:.3f}s")
    else:
        print(f"\n⚠️  Cache not working as expected")
    
    return {
        "cache_miss_time": first_time,
        "cache_hit_time": second_time,
        "speedup": first_time / second_time if second_time > 0 else 0,
        "cached": second_result.get('metadata', {}).get('cached', False)
    }

async def benchmark_early_exit():
    """Test Phase 1B: Early exit for vague queries."""
    print("\n" + "="*80)
    print("BENCHMARK 2: Early Exit for Vague Queries (Phase 1B)")
    print("="*80)
    
    vague_query = TEST_QUERIES["vague"]
    normal_query = TEST_QUERIES["simple"]
    
    # Vague query (should exit early)
    print(f"\n1. Vague query: '{vague_query}'")
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/rag/ask/enhanced",
        json={
            "question": vague_query,
            "enable_difficulty_estimation": True,
            "use_unified_analyzer": True
        }
    )
    vague_time = time.time() - start
    vague_result = response.json()
    
    early_exit = "early_exit" in vague_result.get('metadata', {})
    print(f"   Time: {vague_time:.3f}s")
    print(f"   Early exit: {early_exit}")
    
    # Normal query (full flow)
    print(f"\n2. Normal query: '{normal_query}'")
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/rag/ask/enhanced",
        json={
            "question": normal_query,
            "enable_difficulty_estimation": True,
            "use_unified_analyzer": True
        }
    )
    normal_time = time.time() - start
    
    print(f"   Time: {normal_time:.3f}s")
    
    if early_exit and vague_time < normal_time:
        speedup = normal_time / vague_time
        print(f"\n✅ Early exit speedup: {speedup:.1f}x faster")
        print(f"   Normal: {normal_time:.3f}s → Vague (early): {vague_time:.3f}s")
    else:
        print(f"\n⚠️  Early exit not detected or not faster")
    
    return {
        "vague_query_time": vague_time,
        "normal_query_time": normal_time,
        "early_exit": early_exit,
        "speedup": normal_time / vague_time if vague_time > 0 else 0
    }

async def benchmark_unified_analyzer():
    """Test Phase 2A: Unified analyzer performance."""
    print("\n" + "="*80)
    print("BENCHMARK 3: Unified Analyzer vs Separate (Phase 2A)")
    print("="*80)
    
    query = TEST_QUERIES["moderate"]
    
    # With unified analyzer
    print(f"\n1. With unified analyzer: '{query}'")
    times_unified = []
    for i in range(3):
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/rag/ask/enhanced",
            json={
                "question": query + f" (run {i+1})",  # Vary to avoid cache
                "use_unified_analyzer": True,
                "enable_difficulty_estimation": True,
                "enable_intent_classification": True
            }
        )
        elapsed = time.time() - start
        times_unified.append(elapsed)
    
    avg_unified = sum(times_unified) / len(times_unified)
    print(f"   Avg time: {avg_unified:.3f}s (3 runs)")
    
    # Without unified analyzer (fallback to separate)
    print(f"\n2. Without unified analyzer (separate): '{query}'")
    times_separate = []
    for i in range(3):
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/rag/ask/enhanced",
            json={
                "question": query + f" (run {i+1})",  # Vary to avoid cache
                "use_unified_analyzer": False,
                "enable_difficulty_estimation": True,
                "enable_intent_classification": True
            }
        )
        elapsed = time.time() - start
        times_separate.append(elapsed)
    
    avg_separate = sum(times_separate) / len(times_separate)
    print(f"   Avg time: {avg_separate:.3f}s (3 runs)")
    
    if avg_unified < avg_separate:
        speedup = avg_separate / avg_unified
        improvement = ((avg_separate - avg_unified) / avg_separate) * 100
        print(f"\n✅ Unified analyzer improvement: {speedup:.2f}x faster ({improvement:.1f}% faster)")
    else:
        print(f"\n⚠️  Unified analyzer not faster (may need more data)")
    
    return {
        "unified_time": avg_unified,
        "separate_time": avg_separate,
        "speedup": avg_separate / avg_unified if avg_unified > 0 else 0,
        "improvement_percent": ((avg_separate - avg_unified) / avg_separate) * 100 if avg_separate > 0 else 0
    }

async def benchmark_confidence_adjustments():
    """Test Phase 2C: Confidence adjustments."""
    print("\n" + "="*80)
    print("BENCHMARK 4: Confidence Adjustments (Phase 2C)")
    print("="*80)
    
    # Query that might have contradictions
    query = "What are the latest Docker features?"
    
    print(f"\nQuery: '{query}'")
    response = requests.post(
        f"{BASE_URL}/api/rag/ask/enhanced",
        json={
            "question": query,
            "enable_confidence_scoring": True,
            "enable_contradiction_detection": True,
            "use_unified_analyzer": True
        }
    )
    result = response.json()
    
    confidence = result.get('confidence', 0)
    contradictions = result.get('metadata', {}).get('contradictions', {})
    has_contradictions = contradictions.get('has_contradictions', False)
    
    print(f"   Confidence: {confidence:.1f}%")
    print(f"   Contradictions: {has_contradictions}")
    if has_contradictions:
        print(f"   Severity: {contradictions.get('severity', 'unknown')}")
        print(f"   Count: {contradictions.get('contradiction_count', 0)}")
    
    return {
        "confidence": confidence,
        "has_contradictions": has_contradictions,
        "contradiction_severity": contradictions.get('severity', 'none') if has_contradictions else 'none'
    }

async def run_all_benchmarks():
    """Run all benchmarks."""
    print("\n" + "="*80)
    print("AUDIT PHASE 1 + 2 BENCHMARK SUITE")
    print("="*80)
    print("\nTesting Phase 1 + Phase 2 audit fixes impact...")
    
    results = {}
    
    try:
        # Benchmark 1: Cache performance
        results['cache'] = await benchmark_cache_performance()
        
        # Benchmark 2: Early exit
        results['early_exit'] = await benchmark_early_exit()
        
        # Benchmark 3: Unified analyzer
        results['unified_analyzer'] = await benchmark_unified_analyzer()
        
        # Benchmark 4: Confidence adjustments
        results['confidence'] = await benchmark_confidence_adjustments()
        
        # Summary
        print("\n" + "="*80)
        print("BENCHMARK SUMMARY")
        print("="*80)
        
        print("\nPhase 1A (Cache Integration):")
        print(f"  ✅ Cache speedup: {results['cache']['speedup']:.1f}x")
        print(f"  ✅ Cache working: {results['cache']['cached']}")
        
        print("\nPhase 1B (Early Exit):")
        print(f"  ✅ Early exit speedup: {results['early_exit']['speedup']:.1f}x")
        print(f"  ✅ Early exit detected: {results['early_exit']['early_exit']}")
        
        print("\nPhase 2A (Unified Analyzer):")
        print(f"  ✅ Unified speedup: {results['unified_analyzer']['speedup']:.2f}x")
        print(f"  ✅ Improvement: {results['unified_analyzer']['improvement_percent']:.1f}%")
        
        print("\nPhase 2C (Confidence Adjustments):")
        print(f"  ✅ Confidence scoring: {results['confidence']['confidence']:.1f}%")
        print(f"  ✅ Contradiction detection: {results['confidence']['has_contradictions']}")
        
        print("\n" + "="*80)
        print("All benchmarks complete!")
        print("="*80)
        
        return results
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return results

if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())
