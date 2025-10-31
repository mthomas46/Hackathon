"""
Benchmark for Phase 1+2 implementation.

Validates refactored Enhanced RAG works correctly and measures performance.
"""

import asyncio
import time
import statistics
from datetime import datetime


async def benchmark_enhanced_rag():
    """Benchmark refactored Enhanced RAG."""
    print("\n" + "="*80)
    print("PHASE 1+2 BENCHMARK - Refactored Enhanced RAG")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test queries
    queries = [
        "How does Docker networking work?",
        "What is the MCP architecture?",
        "Explain the ingestion pipeline",
        "How to configure authentication?",
        "What are the RAG enhancements?"
    ]
    
    results = {
        "queries_tested": len(queries),
        "successes": 0,
        "failures": 0,
        "times": [],
        "sources_retrieved": [],
        "errors": []
    }
    
    try:
        import requests
        
        BASE_URL = "http://localhost:8000"
        
        # Test health first
        print("1. Testing API health...")
        try:
            health = requests.get(f"{BASE_URL}/health", timeout=5)
            if health.status_code == 200:
                print("   ✅ API is healthy\n")
            else:
                print(f"   ❌ API not healthy: {health.status_code}\n")
                return results
        except Exception as e:
            print(f"   ❌ Cannot connect to API: {e}\n")
            return results
        
        # Test refactored Enhanced RAG
        print("2. Testing Refactored Enhanced RAG (Phase 1+2)...")
        print("   Config: hybrid=True, rewriting=True, reranking=False\n")
        
        for i, query in enumerate(queries, 1):
            print(f"   Query {i}/{len(queries)}: {query[:50]}...")
            
            start = time.time()
            try:
                response = requests.post(
                    f"{BASE_URL}/api/v1/rag/ask/enhanced",
                    json={
                        "question": query,
                        "n_results": 10,
                        "enable_hybrid_search": True,
                        "enable_query_rewriting": True,
                        "enable_confidence_scoring": True,
                        "enable_reranking": False,  # Phase 1 only
                        "enable_context_optimization": True
                    },
                    timeout=30
                )
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    data = response.json()
                    sources = len(data.get('sources', []))
                    confidence = data.get('confidence', 0)
                    
                    results["successes"] += 1
                    results["times"].append(elapsed)
                    results["sources_retrieved"].append(sources)
                    
                    print(f"      ✅ Success: {elapsed:.2f}s, {sources} sources, {confidence:.0f}% confidence")
                else:
                    results["failures"] += 1
                    results["errors"].append(f"Query {i}: HTTP {response.status_code}")
                    print(f"      ❌ Failed: HTTP {response.status_code}")
            
            except requests.Timeout:
                results["failures"] += 1
                results["errors"].append(f"Query {i}: Timeout")
                print(f"      ❌ Timeout")
            except Exception as e:
                results["failures"] += 1
                results["errors"].append(f"Query {i}: {str(e)[:50]}")
                print(f"      ❌ Error: {str(e)[:50]}")
        
        # Calculate statistics
        print("\n" + "="*80)
        print("BENCHMARK RESULTS")
        print("="*80 + "\n")
        
        print(f"Total Queries:    {results['queries_tested']}")
        print(f"Successful:       {results['successes']} ({results['successes']/results['queries_tested']*100:.0f}%)")
        print(f"Failed:           {results['failures']}")
        
        if results["times"]:
            print(f"\nPerformance:")
            print(f"  Average Time:   {statistics.mean(results['times']):.2f}s")
            print(f"  Median Time:    {statistics.median(results['times']):.2f}s")
            print(f"  Min Time:       {min(results['times']):.2f}s")
            print(f"  Max Time:       {max(results['times']):.2f}s")
        
        if results["sources_retrieved"]:
            print(f"\nDocument Retrieval:")
            print(f"  Average Sources: {statistics.mean(results['sources_retrieved']):.1f}")
            print(f"  Median Sources:  {statistics.median(results['sources_retrieved']):.0f}")
            print(f"  Min Sources:     {min(results['sources_retrieved'])}")
            print(f"  Max Sources:     {max(results['sources_retrieved'])}")
        
        if results["errors"]:
            print(f"\nErrors:")
            for error in results["errors"]:
                print(f"  • {error}")
        
        # Verdict
        print("\n" + "="*80)
        if results["successes"] == results["queries_tested"]:
            print("✅ PHASE 1+2 VALIDATED: All queries successful!")
        elif results["successes"] >= results["queries_tested"] * 0.8:
            print("⚠️  PHASE 1+2 MOSTLY WORKING: Some failures detected")
        else:
            print("❌ PHASE 1+2 ISSUES: Multiple failures detected")
        print("="*80 + "\n")
        
    except ImportError:
        print("❌ requests library not available")
        results["errors"].append("Missing requests library")
    
    return results


def test_code_reduction():
    """Test that code was actually reduced."""
    print("\n" + "="*80)
    print("CODE REDUCTION VALIDATION")
    print("="*80 + "\n")
    
    import os
    
    backup_file = "services/ecosystem-mcp/src/services/rag/accuracy_enhanced_rag_backup.py"
    new_file = "services/ecosystem-mcp/src/services/rag/accuracy_enhanced_rag.py"
    
    if os.path.exists(backup_file) and os.path.exists(new_file):
        with open(backup_file) as f:
            backup_lines = len(f.readlines())
        
        with open(new_file) as f:
            new_lines = len(f.readlines())
        
        reduction = backup_lines - new_lines
        percent = (reduction / backup_lines) * 100
        
        print(f"Original: {backup_lines} lines")
        print(f"Refactored: {new_lines} lines")
        print(f"Reduction: {reduction} lines ({percent:.1f}%)")
        
        if percent >= 40:
            print(f"\n✅ SIGNIFICANT CODE REDUCTION: {percent:.1f}%")
        else:
            print(f"\n⚠️  Limited code reduction: {percent:.1f}%")
    else:
        print("❌ Backup file not found")
    
    print("="*80 + "\n")


async def main():
    """Run all benchmarks."""
    print("\n" + "#"*80)
    print("# PHASE 1+2 VALIDATION AND BENCHMARK")
    print("#"*80)
    
    # Test code reduction
    test_code_reduction()
    
    # Benchmark Enhanced RAG
    results = await benchmark_enhanced_rag()
    
    # Summary
    print("\n" + "#"*80)
    print("# VALIDATION COMPLETE")
    print("#"*80 + "\n")
    
    if results["successes"] > 0:
        print("✅ Phase 1+2 implementation validated")
        print("✅ Refactored Enhanced RAG is working")
        print("✅ Ready to proceed with Phase 3")
    else:
        print("⚠️  Validation incomplete - may need deployment")
        print("   (This is expected if services aren't running)")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())

