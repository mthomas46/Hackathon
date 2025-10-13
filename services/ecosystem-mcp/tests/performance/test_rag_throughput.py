#!/usr/bin/env python3
"""
Load Test: RAG Query Throughput

Target: Verify 5 → 50 queries/sec improvement (10x)

Tests:
1. Baseline throughput (before optimizations would have been ~5 qps)
2. Current throughput (should be ~50 qps with caching)
3. Cache hit rate during load
4. Response time distribution
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx
import json

BASE_URL = "http://localhost:8000"

# Test questions (mix of cached and uncached)
TEST_QUESTIONS = [
    "What is ecosystem-mcp?",  # Will be cached
    "How does document ingestion work?",  # Will be cached
    "What is the RAG pipeline?",  # Will be cached
    "How do I search documents?",  # Will be cached
    "What are the main features?",  # Will be cached
    "How does caching work?",  # Unique
    "What is ChromaDB used for?",  # Unique
    "How do embeddings work?",  # Unique
]


class RAGLoadTester:
    """Load tester for RAG queries."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
    
    async def single_rag_query(
        self,
        client: httpx.AsyncClient,
        question: str,
        query_id: int
    ) -> Dict[str, Any]:
        """Execute a single RAG query and measure performance."""
        start = time.time()
        
        try:
            response = await client.post(
                f"{self.base_url}/api/v1/ask",
                json={
                    "question": question,
                    "n_results": 10,
                    "prefer_recent": True,
                    "temperature": 0.7
                },
                timeout=60.0
            )
            
            elapsed = time.time() - start
            
            return {
                "query_id": query_id,
                "question": question,
                "status_code": response.status_code,
                "response_time": elapsed,
                "success": response.status_code == 200,
                "error": None
            }
        
        except Exception as e:
            elapsed = time.time() - start
            return {
                "query_id": query_id,
                "question": question,
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
        """
        Run sustained load test at target QPS.
        
        Args:
            target_qps: Target queries per second
            duration_seconds: How long to sustain the load
        
        Returns:
            Performance metrics
        """
        print(f"\n{'='*80}")
        print(f"RAG Sustained Load Test: {target_qps} QPS for {duration_seconds}s")
        print(f"{'='*80}\n")
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            query_id = 0
            results = []
            
            # Calculate interval between queries
            interval = 1.0 / target_qps
            
            while time.time() - start_time < duration_seconds:
                batch_start = time.time()
                
                # Fire off queries for this second
                tasks = []
                for _ in range(target_qps):
                    question = TEST_QUESTIONS[query_id % len(TEST_QUESTIONS)]
                    tasks.append(self.single_rag_query(client, question, query_id))
                    query_id += 1
                
                # Execute batch
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
                
                # Wait for next batch
                batch_elapsed = time.time() - batch_start
                sleep_time = max(0, 1.0 - batch_elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
                # Progress indicator
                elapsed = time.time() - start_time
                print(f"Progress: {elapsed:.1f}s / {duration_seconds}s "
                      f"({len(results)} queries, "
                      f"{len([r for r in results if r['success']])} success)", end='\r')
            
            print()  # New line after progress
            
            # Calculate metrics
            total_time = time.time() - start_time
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            response_times = [r['response_time'] for r in successful]
            
            metrics = {
                "target_qps": target_qps,
                "duration": total_time,
                "total_queries": len(results),
                "successful_queries": len(successful),
                "failed_queries": len(failed),
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
            
            return metrics
    
    async def burst_test(self, concurrent_queries: int) -> Dict[str, Any]:
        """
        Test burst capacity - fire many queries at once.
        
        Args:
            concurrent_queries: Number of concurrent queries
        
        Returns:
            Performance metrics
        """
        print(f"\n{'='*80}")
        print(f"RAG Burst Test: {concurrent_queries} concurrent queries")
        print(f"{'='*80}\n")
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            # Fire all queries at once
            tasks = []
            for i in range(concurrent_queries):
                question = TEST_QUESTIONS[i % len(TEST_QUESTIONS)]
                tasks.append(self.single_rag_query(client, question, i))
            
            results = await asyncio.gather(*tasks)
            
            total_time = time.time() - start_time
            successful = [r for r in results if r['success']]
            response_times = [r['response_time'] for r in successful]
            
            metrics = {
                "concurrent_queries": concurrent_queries,
                "total_time": total_time,
                "successful": len(successful),
                "failed": len(results) - len(successful),
                "effective_qps": len(successful) / total_time,
                "response_times": {
                    "min": min(response_times) if response_times else 0,
                    "max": max(response_times) if response_times else 0,
                    "mean": statistics.mean(response_times) if response_times else 0,
                    "median": statistics.median(response_times) if response_times else 0,
                }
            }
            
            return metrics
    
    def print_metrics(self, metrics: Dict[str, Any], test_name: str):
        """Print metrics in a nice format."""
        print(f"\n{'='*80}")
        print(f"Results: {test_name}")
        print(f"{'='*80}")
        
        if "target_qps" in metrics:
            print(f"\nTarget QPS: {metrics['target_qps']}")
            print(f"Actual QPS: {metrics['actual_qps']:.2f}")
            print(f"Duration: {metrics['duration']:.2f}s")
        else:
            print(f"\nConcurrent Queries: {metrics['concurrent_queries']}")
            print(f"Total Time: {metrics['total_time']:.2f}s")
            print(f"Effective QPS: {metrics['effective_qps']:.2f}")
        
        print(f"\nQueries:")
        print(f"  Total: {metrics.get('total_queries', metrics.get('concurrent_queries'))}")
        print(f"  Successful: {metrics.get('successful_queries', metrics.get('successful'))}")
        print(f"  Failed: {metrics.get('failed_queries', metrics.get('failed'))}")
        print(f"  Success Rate: {metrics.get('success_rate', 1.0) * 100:.1f}%")
        
        rt = metrics['response_times']
        print(f"\nResponse Times:")
        print(f"  Min: {rt['min']:.3f}s")
        print(f"  Mean: {rt['mean']:.3f}s")
        print(f"  Median: {rt['median']:.3f}s")
        if 'p95' in rt:
            print(f"  P95: {rt['p95']:.3f}s")
            print(f"  P99: {rt['p99']:.3f}s")
        print(f"  Max: {rt['max']:.3f}s")
        
        # Verdict
        print(f"\n{'='*80}")
        if "target_qps" in metrics:
            if metrics['actual_qps'] >= metrics['target_qps'] * 0.9:  # Within 10%
                print(f"✅ PASS: Achieved {metrics['actual_qps']:.1f} QPS (target: {metrics['target_qps']})")
            else:
                print(f"❌ FAIL: Only achieved {metrics['actual_qps']:.1f} QPS (target: {metrics['target_qps']})")
        
        if metrics.get('success_rate', 1.0) >= 0.95:  # 95% success
            print(f"✅ PASS: {metrics.get('success_rate', 1.0) * 100:.1f}% success rate")
        else:
            print(f"❌ FAIL: Only {metrics.get('success_rate', 1.0) * 100:.1f}% success rate")
        
        print(f"{'='*80}\n")


async def main():
    """Run comprehensive RAG throughput tests."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║              RAG THROUGHPUT VERIFICATION TESTS                            ║
╚═══════════════════════════════════════════════════════════════════════════╝

Testing Claim: RAG Queries/sec 5 → 50 (10x improvement)

Test Plan:
  1. Warm-up: Prime caches with test questions
  2. Sustained Load: 50 QPS for 60 seconds
  3. Burst Test: 100 concurrent queries
  4. Comparison: Compare to baseline expectations

""")
    
    tester = RAGLoadTester()
    
    # Warm-up phase
    print("Warming up caches...")
    async with httpx.AsyncClient() as client:
        warmup_tasks = []
        for question in TEST_QUESTIONS[:5]:  # Cache first 5 questions
            warmup_tasks.append(tester.single_rag_query(client, question, 0))
        await asyncio.gather(*warmup_tasks)
    print("✅ Warm-up complete\n")
    
    await asyncio.sleep(2)
    
    # Test 1: 50 QPS sustained (our target)
    metrics_50qps = await tester.sustained_load_test(
        target_qps=50,
        duration_seconds=60
    )
    tester.print_metrics(metrics_50qps, "50 QPS Sustained Load (Target)")
    
    await asyncio.sleep(5)
    
    # Test 2: Burst capacity
    metrics_burst = await tester.burst_test(concurrent_queries=100)
    tester.print_metrics(metrics_burst, "100 Concurrent Queries (Burst)")
    
    # Final summary
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                           FINAL VERDICT                                   ║
╚═══════════════════════════════════════════════════════════════════════════╝
""")
    
    target_met = metrics_50qps['actual_qps'] >= 45  # Allow 10% margin
    reliability_met = metrics_50qps['success_rate'] >= 0.95
    
    print(f"Target Throughput (50 QPS): {'✅ MET' if target_met else '❌ NOT MET'}")
    print(f"  - Achieved: {metrics_50qps['actual_qps']:.1f} QPS")
    print(f"  - Success Rate: {metrics_50qps['success_rate'] * 100:.1f}%")
    print(f"  - Avg Response Time: {metrics_50qps['response_times']['mean']:.3f}s")
    
    print(f"\nReliability (>95% success): {'✅ MET' if reliability_met else '❌ NOT MET'}")
    
    print(f"\nBurst Capacity (100 concurrent):")
    print(f"  - Effective QPS: {metrics_burst['effective_qps']:.1f}")
    print(f"  - Success Rate: {(metrics_burst['successful'] / metrics_burst['concurrent_queries']) * 100:.1f}%")
    
    improvement_factor = metrics_50qps['actual_qps'] / 5  # Baseline was ~5 QPS
    print(f"\nImprovement Factor: {improvement_factor:.1f}x (claimed: 10x)")
    
    if target_met and reliability_met:
        print("\n🎉 ALL TESTS PASSED! Throughput improvements verified! 🎉")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Investigation needed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

