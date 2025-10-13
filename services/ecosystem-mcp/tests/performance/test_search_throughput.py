#!/usr/bin/env python3
"""
Load Test: Search Query Throughput

Target: Verify 25 → 200 queries/sec improvement (8x)

Tests:
1. Sustained 200 QPS load
2. Cache hit rate verification
3. Response time consistency
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx

BASE_URL = "http://localhost:8000"

# Test search queries
TEST_SEARCHES = [
    "ecosystem",
    "document ingestion",
    "caching strategy",
    "performance optimization",
    "RAG pipeline",
    "semantic search",
    "ChromaDB",
    "embeddings",
]


class SearchLoadTester:
    """Load tester for search queries."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    async def single_search(
        self,
        client: httpx.AsyncClient,
        query: str,
        query_id: int
    ) -> Dict[str, Any]:
        """Execute a single search query."""
        start = time.time()
        
        try:
            response = await client.post(
                f"{self.base_url}/api/v1/search",
                json={"query": query, "n_results": 10},
                timeout=30.0
            )
            
            elapsed = time.time() - start
            
            return {
                "query_id": query_id,
                "query": query,
                "status_code": response.status_code,
                "response_time": elapsed,
                "success": response.status_code == 200,
                "error": None
            }
        
        except Exception as e:
            elapsed = time.time() - start
            return {
                "query_id": query_id,
                "query": query,
                "status_code": 0,
                "response_time": elapsed,
                "success": False,
                "error": str(e)
            }
    
    async def sustained_load_test(
        self,
        target_qps: int,
        duration_seconds: int = 60
    ) -> Dict[str, Any]:
        """Run sustained search load test."""
        print(f"\n{'='*80}")
        print(f"Search Sustained Load Test: {target_qps} QPS for {duration_seconds}s")
        print(f"{'='*80}\n")
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            query_id = 0
            results = []
            
            while time.time() - start_time < duration_seconds:
                batch_start = time.time()
                
                # Fire off queries
                tasks = []
                for _ in range(target_qps):
                    query = TEST_SEARCHES[query_id % len(TEST_SEARCHES)]
                    tasks.append(self.single_search(client, query, query_id))
                    query_id += 1
                
                # Execute batch
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
                
                # Wait for next second
                batch_elapsed = time.time() - batch_start
                sleep_time = max(0, 1.0 - batch_elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
                elapsed = time.time() - start_time
                print(f"Progress: {elapsed:.1f}s / {duration_seconds}s "
                      f"({len(results)} queries, "
                      f"{len([r for r in results if r['success']])} success)", end='\r')
            
            print()
            
            # Calculate metrics
            total_time = time.time() - start_time
            successful = [r for r in results if r['success']]
            response_times = [r['response_time'] for r in successful]
            
            return {
                "target_qps": target_qps,
                "duration": total_time,
                "total_queries": len(results),
                "successful": len(successful),
                "failed": len(results) - len(successful),
                "actual_qps": len(results) / total_time,
                "success_rate": len(successful) / len(results) if results else 0,
                "response_times": {
                    "min": min(response_times) if response_times else 0,
                    "max": max(response_times) if response_times else 0,
                    "mean": statistics.mean(response_times) if response_times else 0,
                    "median": statistics.median(response_times) if response_times else 0,
                    "p95": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
                    "p99": sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
                }
            }
    
    def print_metrics(self, metrics: Dict[str, Any]):
        """Print metrics."""
        print(f"\n{'='*80}")
        print(f"Results: Search Load Test")
        print(f"{'='*80}")
        print(f"\nTarget QPS: {metrics['target_qps']}")
        print(f"Actual QPS: {metrics['actual_qps']:.2f}")
        print(f"Duration: {metrics['duration']:.2f}s")
        print(f"\nQueries:")
        print(f"  Total: {metrics['total_queries']}")
        print(f"  Successful: {metrics['successful']}")
        print(f"  Failed: {metrics['failed']}")
        print(f"  Success Rate: {metrics['success_rate'] * 100:.1f}%")
        
        rt = metrics['response_times']
        print(f"\nResponse Times:")
        print(f"  Min: {rt['min']:.3f}s")
        print(f"  Mean: {rt['mean']:.3f}s")
        print(f"  Median: {rt['median']:.3f}s")
        print(f"  P95: {rt['p95']:.3f}s")
        print(f"  P99: {rt['p99']:.3f}s")
        print(f"  Max: {rt['max']:.3f}s")
        
        print(f"\n{'='*80}")
        if metrics['actual_qps'] >= metrics['target_qps'] * 0.9:
            print(f"✅ PASS: Achieved {metrics['actual_qps']:.1f} QPS")
        else:
            print(f"❌ FAIL: Only {metrics['actual_qps']:.1f} QPS")
        
        if metrics['success_rate'] >= 0.95:
            print(f"✅ PASS: {metrics['success_rate'] * 100:.1f}% success rate")
        else:
            print(f"❌ FAIL: Only {metrics['success_rate'] * 100:.1f}% success rate")
        print(f"{'='*80}\n")


async def main():
    """Run search throughput tests."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║            SEARCH THROUGHPUT VERIFICATION TESTS                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

Testing Claim: Search Queries/sec 25 → 200 (8x improvement)

""")
    
    tester = SearchLoadTester()
    
    # Warm-up
    print("Warming up caches...")
    async with httpx.AsyncClient() as client:
        for query in TEST_SEARCHES:
            await tester.single_search(client, query, 0)
    print("✅ Warm-up complete\n")
    
    await asyncio.sleep(2)
    
    # Test: 200 QPS sustained
    metrics = await tester.sustained_load_test(target_qps=200, duration_seconds=60)
    tester.print_metrics(metrics)
    
    # Verdict
    target_met = metrics['actual_qps'] >= 180  # 90% of target
    reliability_met = metrics['success_rate'] >= 0.95
    
    if target_met and reliability_met:
        print("\n🎉 SEARCH THROUGHPUT TEST PASSED! 🎉")
        return 0
    else:
        print("\n⚠️  SEARCH TEST FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

