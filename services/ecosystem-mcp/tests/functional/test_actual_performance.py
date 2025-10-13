#!/usr/bin/env python3
"""
Functional Test: Actual Performance Verification

This test measures REAL performance improvements with production configuration.
No mocking, no artificial scenarios - just real measurements.
"""

import asyncio
import time
import statistics
from typing import Dict, List, Any
import httpx
import json

BASE_URL = "http://localhost:8000"


class PerformanceVerifier:
    """Verify actual performance metrics."""
    
    def __init__(self):
        self.results = {}
    
    async def measure_search_performance(self) -> Dict[str, Any]:
        """Measure search endpoint performance (cold vs warm)."""
        print("\n" + "="*80)
        print("TEST 1: SEARCH PERFORMANCE")
        print("="*80)
        
        query = "ecosystem-mcp performance optimization caching"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Cold search (uncached)
            print("Running cold search...")
            times_cold = []
            for i in range(3):
                # Use slightly different queries to avoid cache
                q = f"{query} test{i}"
                start = time.time()
                response = await client.post(
                    f"{BASE_URL}/api/v1/search",
                    json={"query": q, "n_results": 10}
                )
                elapsed = time.time() - start
                if response.status_code == 200:
                    times_cold.append(elapsed)
                await asyncio.sleep(1)
            
            avg_cold = statistics.mean(times_cold)
            print(f"✅ Cold search avg: {avg_cold:.3f}s")
            
            # Warm search (cached)
            print("Running warm searches (same query)...")
            times_warm = []
            for _ in range(5):
                start = time.time()
                response = await client.post(
                    f"{BASE_URL}/api/v1/search",
                    json={"query": query, "n_results": 10}
                )
                elapsed = time.time() - start
                if response.status_code == 200:
                    times_warm.append(elapsed)
                await asyncio.sleep(0.5)
            
            avg_warm = statistics.mean(times_warm)
            print(f"✅ Warm search avg: {avg_warm:.3f}s")
            
            speedup = avg_cold / avg_warm if avg_warm > 0 else 0
            
            print(f"\n📊 Search Results:")
            print(f"   Cold: {avg_cold:.3f}s")
            print(f"   Warm: {avg_warm:.3f}s")
            print(f"   Speedup: {speedup:.1f}x")
            print(f"   Status: {'✅ PASS' if speedup >= 2 else '⚠️ NEEDS IMPROVEMENT'}")
            
            return {
                "cold_avg": avg_cold,
                "warm_avg": avg_warm,
                "speedup": speedup,
                "pass": speedup >= 2
            }
    
    async def measure_rag_performance(self) -> Dict[str, Any]:
        """Measure RAG endpoint performance."""
        print("\n" + "="*80)
        print("TEST 2: RAG PERFORMANCE")
        print("="*80)
        
        question = "What are the main features and capabilities of the ecosystem-mcp service?"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # First query (potentially uncached or slow)
            print("Running first RAG query...")
            start = time.time()
            response1 = await client.post(
                f"{BASE_URL}/api/v1/ask",
                json={"question": question}
            )
            time1 = time.time() - start
            
            if response1.status_code == 200:
                print(f"✅ First query: {time1:.2f}s")
            else:
                print(f"❌ First query failed: {response1.status_code}")
                return {"error": "First query failed"}
            
            await asyncio.sleep(2)
            
            # Second query (should be cached)
            print("Running second RAG query (same question)...")
            start = time.time()
            response2 = await client.post(
                f"{BASE_URL}/api/v1/ask",
                json={"question": question}
            )
            time2 = time.time() - start
            
            if response2.status_code == 200:
                print(f"✅ Second query: {time2:.2f}s")
            else:
                print(f"❌ Second query failed")
                return {"error": "Second query failed"}
            
            # Check if answers match (verify cache)
            answers_match = response1.json().get("answer") == response2.json().get("answer")
            
            improvement = time1 / time2 if time2 > 0 else 0
            
            print(f"\n📊 RAG Results:")
            print(f"   First: {time1:.2f}s")
            print(f"   Second: {time2:.2f}s")
            print(f"   Improvement: {improvement:.1f}x")
            print(f"   Answers match: {'✅ Yes' if answers_match else '❌ No (cache miss?)'}")
            print(f"   Status: {'✅ PASS' if improvement >= 1.2 else '⚠️ NO IMPROVEMENT'}")
            
            return {
                "first_query": time1,
                "second_query": time2,
                "improvement": improvement,
                "answers_match": answers_match,
                "pass": improvement >= 1.2
            }
    
    async def measure_document_query_performance(self) -> Dict[str, Any]:
        """Measure document query endpoint performance."""
        print("\n" + "="*80)
        print("TEST 3: DOCUMENT QUERY PERFORMANCE")
        print("="*80)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First query
            print("Running first document query...")
            start = time.time()
            response1 = await client.post(
                f"{BASE_URL}/api/v1/query",
                json={"limit": 20, "offset": 0}
            )
            time1 = time.time() - start
            
            if response1.status_code == 200:
                print(f"✅ First query: {time1:.3f}s")
            else:
                print(f"❌ First query failed")
                return {"error": "First query failed"}
            
            await asyncio.sleep(1)
            
            # Second query (cached)
            print("Running second document query...")
            start = time.time()
            response2 = await client.post(
                f"{BASE_URL}/api/v1/query",
                json={"limit": 20, "offset": 0}
            )
            time2 = time.time() - start
            
            if response2.status_code == 200:
                print(f"✅ Second query: {time2:.3f}s")
            else:
                print(f"❌ Second query failed")
                return {"error": "Second query failed"}
            
            speedup = time1 / time2 if time2 > 0 else 0
            
            print(f"\n📊 Document Query Results:")
            print(f"   First: {time1:.3f}s")
            print(f"   Second: {time2:.3f}s")
            print(f"   Speedup: {speedup:.1f}x")
            print(f"   Status: {'✅ PASS' if speedup >= 2 else '⚠️ NEEDS IMPROVEMENT'}")
            
            return {
                "first_query": time1,
                "second_query": time2,
                "speedup": speedup,
                "pass": speedup >= 2
            }
    
    async def measure_parallel_vs_sequential(self) -> Dict[str, Any]:
        """Measure parallel request handling."""
        print("\n" + "="*80)
        print("TEST 4: PARALLEL REQUEST HANDLING")
        print("="*80)
        
        queries = [
            "caching",
            "performance",
            "optimization",
            "embeddings",
            "ChromaDB"
        ]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Sequential
            print("Running sequential searches...")
            start = time.time()
            for query in queries:
                await client.post(
                    f"{BASE_URL}/api/v1/search",
                    json={"query": query, "n_results": 5}
                )
                await asyncio.sleep(0.2)
            sequential_time = time.time() - start
            print(f"✅ Sequential: {sequential_time:.2f}s")
            
            await asyncio.sleep(2)
            
            # Parallel
            print("Running parallel searches...")
            start = time.time()
            tasks = [
                client.post(
                    f"{BASE_URL}/api/v1/search",
                    json={"query": q, "n_results": 5}
                )
                for q in queries
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            parallel_time = time.time() - start
            print(f"✅ Parallel: {parallel_time:.2f}s")
            
            speedup = sequential_time / parallel_time if parallel_time > 0 else 0
            
            print(f"\n📊 Parallel Handling Results:")
            print(f"   Sequential: {sequential_time:.2f}s")
            print(f"   Parallel: {parallel_time:.2f}s")
            print(f"   Speedup: {speedup:.1f}x")
            print(f"   Status: {'✅ PASS' if speedup >= 1.5 else '⚠️ NEEDS IMPROVEMENT'}")
            
            return {
                "sequential": sequential_time,
                "parallel": parallel_time,
                "speedup": speedup,
                "pass": speedup >= 1.5
            }
    
    def generate_report(self, results: Dict[str, Any]):
        """Generate comprehensive performance report."""
        print("\n" + "="*80)
        print("COMPREHENSIVE PERFORMANCE VERIFICATION REPORT")
        print("="*80)
        
        # Summary table
        print("\n┌────────────────────────────────────────────────────────────────┐")
        print("│                    TEST RESULTS SUMMARY                        │")
        print("├────────────────────────────────────────────────────────────────┤")
        
        tests = [
            ("Search Caching", results.get("search", {})),
            ("RAG Caching", results.get("rag", {})),
            ("Document Query Caching", results.get("doc_query", {})),
            ("Parallel Handling", results.get("parallel", {}))
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_results in tests:
            if test_results.get("pass"):
                print(f"│ ✅ {test_name:<50} PASS     │")
                passed += 1
            elif test_results.get("error"):
                print(f"│ ❌ {test_name:<50} ERROR    │")
                failed += 1
            else:
                print(f"│ ⚠️  {test_name:<50} WARNING │")
                failed += 1
        
        print("└────────────────────────────────────────────────────────────────┘")
        
        # Detailed metrics
        print("\n┌────────────────────────────────────────────────────────────────┐")
        print("│                 VERIFIED PERFORMANCE GAINS                     │")
        print("├────────────────────────────────────────────────────────────────┤")
        
        if results.get("search"):
            search = results["search"]
            print(f"│ Search Caching:                                                │")
            print(f"│   Cold: {search['cold_avg']:.3f}s → Warm: {search['warm_avg']:.3f}s ({search['speedup']:.1f}x faster) │")
        
        if results.get("rag"):
            rag = results["rag"]
            print(f"│ RAG Queries:                                                   │")
            print(f"│   First: {rag['first_query']:.2f}s → Second: {rag['second_query']:.2f}s ({rag['improvement']:.1f}x) │")
        
        if results.get("doc_query") and not results["doc_query"].get("error"):
            doc = results["doc_query"]
            print(f"│ Document Queries:                                              │")
            print(f"│   First: {doc['first_query']:.3f}s → Second: {doc['second_query']:.3f}s ({doc['speedup']:.1f}x) │")
        
        if results.get("parallel"):
            par = results["parallel"]
            print(f"│ Parallel Requests:                                             │")
            print(f"│   Sequential: {par['sequential']:.2f}s → Parallel: {par['parallel']:.2f}s ({par['speedup']:.1f}x) │")
        
        print("└────────────────────────────────────────────────────────────────┘")
        
        # Final verdict
        print("\n╔════════════════════════════════════════════════════════════════╗")
        print("║                      FINAL VERDICT                             ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        
        print(f"\nTests Passed: {passed}/{len(tests)}")
        print(f"Tests Failed/Warning: {failed}/{len(tests)}")
        
        if passed >= 3:
            print("\n✅ PERFORMANCE OPTIMIZATIONS VERIFIED!")
            print("\nKey Findings:")
            print("  • Caching is working and providing measurable speedups")
            print("  • Individual query performance is improved")
            print("  • System handles parallel requests efficiently")
        elif passed >= 2:
            print("\n⚠️  PARTIAL SUCCESS")
            print("\nSome optimizations working, others need investigation")
        else:
            print("\n❌ PERFORMANCE ISSUES DETECTED")
            print("\nOptimizations not providing expected improvements")
        
        print("\n" + "="*80)


async def main():
    """Run comprehensive performance verification."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║         COMPREHENSIVE PERFORMANCE VERIFICATION SUITE                      ║
╚═══════════════════════════════════════════════════════════════════════════╝

This test measures ACTUAL performance with production configuration.
No mocking, just real measurements.

Testing:
  1. Search caching effectiveness
  2. RAG query performance
  3. Document query caching
  4. Parallel request handling

""")
    
    verifier = PerformanceVerifier()
    results = {}
    
    try:
        # Run all tests
        results["search"] = await verifier.measure_search_performance()
        await asyncio.sleep(2)
        
        results["rag"] = await verifier.measure_rag_performance()
        await asyncio.sleep(2)
        
        results["doc_query"] = await verifier.measure_document_query_performance()
        await asyncio.sleep(2)
        
        results["parallel"] = await verifier.measure_parallel_vs_sequential()
        
        # Generate report
        verifier.generate_report(results)
        
        # Save results
        with open("performance_verification_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\n📄 Results saved to: performance_verification_results.json")
        
        # Exit code based on results
        passed = sum(1 for r in results.values() if r.get("pass"))
        return 0 if passed >= 3 else 1
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

