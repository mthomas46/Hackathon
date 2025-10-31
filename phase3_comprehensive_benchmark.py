#!/usr/bin/env python3
"""
Phase 3 Comprehensive Benchmark

Measures performance with and without cache to demonstrate Phase 3 effectiveness.
"""

import asyncio
import httpx
import time
from typing import Dict, Any
import json

API_BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 120.0

TEST_QUESTIONS = [
    {"id": "Q1", "question": "What is ChromaDB?", "category": "simple"},
    {"id": "Q2", "question": "What is BM25?", "category": "simple"},
    {"id": "Q3", "question": "How does ingestion work?", "category": "technical"},
]

async def clear_cache():
    """Clear Redis cache to get fresh measurements."""
    print("🧹 Clearing cache...")
    # Note: In production, you'd call a cache clear endpoint
    # For now, we'll just note that first queries will be cache misses
    await asyncio.sleep(1)
    print("   ✅ Ready for fresh queries")

async def query_rag(client, question: str, **options) -> Dict[str, Any]:
    """Query RAG endpoint and measure time."""
    start = time.time()
    try:
        response = await client.post(
            f"{API_BASE_URL}/rag/ask/enhanced",
            json={"question": question, "n_results": 10, **options}
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "elapsed": elapsed,
                "confidence": result.get('confidence', 0),
                "sources": len(result.get('sources', [])),
                "answer_length": len(result.get('answer', ''))
            }
        else:
            return {
                "success": False,
                "elapsed": elapsed,
                "error": response.text[:200]
            }
    except Exception as e:
        return {
            "success": False,
            "elapsed": time.time() - start,
            "error": str(e)
        }

async def run_benchmark():
    """Run comprehensive Phase 3 benchmark."""
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║              PHASE 3 COMPREHENSIVE BENCHMARK                                 ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    results = []
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        
        for test in TEST_QUESTIONS:
            print(f"\n{'='*80}")
            print(f"Testing: {test['id']} - {test['question']}")
            print(f"Category: {test['category']}")
            print(f"{'='*80}\n")
            
            result = {
                "question_id": test['id'],
                "question": test['question'],
                "category": test['category'],
                "runs": {}
            }
            
            # Run 1: Standard RAG (baseline)
            print("   1️⃣  Standard RAG (baseline)...")
            std_result = await query_rag(client, test['question'])
            result['runs']['standard'] = std_result
            if std_result['success']:
                print(f"      ✅ {std_result['elapsed']:.2f}s | Confidence: {std_result['confidence']:.1f}%")
            else:
                print(f"      ❌ Failed: {std_result.get('error', 'Unknown error')[:50]}")
            
            await asyncio.sleep(1)
            
            # Run 2: Phase 1+2 (First Query - Cache Miss)
            print("   2️⃣  Phase 1+2 - First Query (Cache Miss)...")
            p1_first = await query_rag(
                client, test['question'],
                enable_hybrid_search=True,
                enable_query_rewriting=True,
                enable_confidence_scoring=True,
                enable_reranking=True,
                enable_context_optimization=True
            )
            result['runs']['phase1_2_first'] = p1_first
            if p1_first['success']:
                print(f"      ✅ {p1_first['elapsed']:.2f}s | Confidence: {p1_first['confidence']:.1f}%")
            else:
                print(f"      ❌ Failed: {p1_first.get('error', 'Unknown error')[:50]}")
            
            await asyncio.sleep(2)  # Wait for cache to settle
            
            # Run 3: Phase 1+2 (Second Query - Cache Hit)
            print("   3️⃣  Phase 1+2 - Second Query (Cache Hit)...")
            p1_cached = await query_rag(
                client, test['question'],
                enable_hybrid_search=True,
                enable_query_rewriting=True,
                enable_confidence_scoring=True,
                enable_reranking=True,
                enable_context_optimization=True
            )
            result['runs']['phase1_2_cached'] = p1_cached
            if p1_cached['success']:
                print(f"      ✅ {p1_cached['elapsed']:.2f}s | Confidence: {p1_cached['confidence']:.1f}%")
            else:
                print(f"      ❌ Failed: {p1_cached.get('error', 'Unknown error')[:50]}")
            
            # Calculate speedups
            if p1_first['success'] and p1_cached['success']:
                cache_speedup = ((p1_first['elapsed'] - p1_cached['elapsed']) / p1_first['elapsed']) * 100
                vs_standard = ((std_result['elapsed'] - p1_cached['elapsed']) / std_result['elapsed']) * 100
                
                result['cache_speedup_pct'] = cache_speedup
                result['vs_standard_speedup_pct'] = vs_standard
                
                print(f"\n   📊 Results:")
                print(f"      Cache Speedup:    {cache_speedup:+.1f}% ({p1_first['elapsed']:.2f}s → {p1_cached['elapsed']:.2f}s)")
                print(f"      vs Standard:      {vs_standard:+.1f}% ({std_result['elapsed']:.2f}s → {p1_cached['elapsed']:.2f}s)")
            
            results.append(result)
            
            await asyncio.sleep(1)
    
    # Summary
    print(f"\n{'='*80}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*80}\n")
    
    total_questions = len(results)
    successful_questions = sum(1 for r in results if r['runs'].get('phase1_2_cached', {}).get('success', False))
    
    print(f"Questions Tested: {total_questions}")
    print(f"Successful:       {successful_questions}/{total_questions}")
    print()
    
    if successful_questions > 0:
        # Calculate averages
        std_times = [r['runs']['standard']['elapsed'] for r in results if r['runs']['standard']['success']]
        p1_first_times = [r['runs']['phase1_2_first']['elapsed'] for r in results if r['runs']['phase1_2_first']['success']]
        p1_cached_times = [r['runs']['phase1_2_cached']['elapsed'] for r in results if r['runs']['phase1_2_cached']['success']]
        
        avg_std = sum(std_times) / len(std_times) if std_times else 0
        avg_p1_first = sum(p1_first_times) / len(p1_first_times) if p1_first_times else 0
        avg_p1_cached = sum(p1_cached_times) / len(p1_cached_times) if p1_cached_times else 0
        
        print("Average Response Times:")
        print(f"  Standard RAG:              {avg_std:.2f}s  (baseline)")
        print(f"  Phase 1+2 (Cache Miss):    {avg_p1_first:.2f}s  ({((avg_p1_first/avg_std - 1) * 100):+.1f}%)")
        print(f"  Phase 1+2 (Cache Hit):     {avg_p1_cached:.2f}s  ({((avg_p1_cached/avg_std - 1) * 100):+.1f}%)")
        print()
        
        cache_benefit = ((avg_p1_first - avg_p1_cached) / avg_p1_first) * 100
        print(f"🚀 Cache Benefit: {cache_benefit:.1f}% faster on cache hits")
        print(f"   ({avg_p1_first:.2f}s → {avg_p1_cached:.2f}s)")
        print()
        
        # Confidence scores
        std_confs = [r['runs']['standard']['confidence'] for r in results if r['runs']['standard']['success']]
        p1_first_confs = [r['runs']['phase1_2_first']['confidence'] for r in results if r['runs']['phase1_2_first']['success']]
        
        if std_confs and p1_first_confs:
            avg_std_conf = sum(std_confs) / len(std_confs)
            avg_p1_conf = sum(p1_first_confs) / len(p1_first_confs)
            
            print("Average Confidence Scores:")
            print(f"  Standard RAG:      {avg_std_conf:.1f}%")
            print(f"  Phase 1+2:         {avg_p1_conf:.1f}%  ({(avg_p1_conf - avg_std_conf):+.1f}%)")
            print()
    
    # Save results
    output_file = "phase3_comprehensive_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📄 Results saved to: {output_file}")
    print()
    
    print("✅ Benchmark Complete!")
    print()

if __name__ == "__main__":
    asyncio.run(run_benchmark())

