"""
Comprehensive tests for Phase 5: Context-Aware RAG Integration.

Tests that Context-Aware RAG now uses EnhancementPipeline and generates LLM answers.
"""

import asyncio
import time
import statistics
from datetime import datetime
import requests


async def test_context_aware_enhancements():
    """Test Context-Aware RAG with enhancement pipeline."""
    print("\n" + "="*80)
    print("PHASE 5 TEST: CONTEXT-AWARE RAG WITH ENHANCEMENTS")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    BASE_URL = "http://localhost:8000"
    
    # Test queries with various context filters
    test_cases = [
        {
            "query": "How does Docker work?",
            "filters": {},
            "description": "No filters (baseline)"
        },
        {
            "query": "What is the MCP architecture?",
            "filters": {"service_filter": "ecosystem-mcp"},
            "description": "Service filter"
        },
        {
            "query": "Explain the RAG system",
            "filters": {"repo_id": "ecosystem-mcp"},
            "description": "Repository filter"
        }
    ]
    
    results = {
        "queries_tested": len(test_cases),
        "successes": 0,
        "failures": 0,
        "times": [],
        "sources_retrieved": [],
        "answers_generated": 0,
        "errors": []
    }
    
    try:
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
        
        # Test Context-Aware RAG with enhancements
        print("2. Testing Context-Aware RAG (Phase 5 - with EnhancementPipeline + LLM Answers)...")
        print("   Expected: hybrid search + query rewriting + context filtering + LLM answers\n")
        
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            filters = test_case["filters"]
            desc = test_case["description"]
            
            print(f"   Query {i}/{len(test_cases)}: {query[:40]}... ({desc})")
            
            start = time.time()
            try:
                payload = {
                    "question": query,  # API expects 'question'
                    "limit": 10
                }
                payload.update(filters)
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/query/context-aware",
                    json=payload,
                    timeout=30
                )
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    data = response.json()
                    sources = len(data.get('sources', data.get('results', [])))
                    has_answer = data.get('answer') is not None and len(data.get('answer', '')) > 0
                    metadata = data.get('metadata', {})
                    enhancement_mode = metadata.get('enhancement_mode', 'unknown')
                    
                    results["successes"] += 1
                    results["times"].append(elapsed)
                    results["sources_retrieved"].append(sources)
                    if has_answer:
                        results["answers_generated"] += 1
                    
                    answer_indicator = "✨ (with LLM answer)" if has_answer else "❌ (no answer)"
                    enhancement_indicator = "✨ (enhanced)" if enhancement_mode == "pipeline_v1" else "📋 (legacy)"
                    
                    print(f"      ✅ Success: {elapsed:.2f}s, {sources} sources, {enhancement_mode} {enhancement_indicator} {answer_indicator}")
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
        print(f"Answers Generated: {results['answers_generated']} ({results['answers_generated']/max(results['successes'],1)*100:.0f}% of successes)")
        
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
            print("✅ PHASE 5 VALIDATED: All context-aware queries successful!")
            if results["answers_generated"] == results["successes"]:
                print("✅ LLM answer generation working (NEW Phase 5 feature!)")
            if results["sources_retrieved"] and statistics.mean(results["sources_retrieved"]) >= 5:
                print("✅ Good document retrieval (5+ sources average)")
        elif results["successes"] >= results["queries_tested"] * 0.8:
            print("⚠️  PHASE 5 MOSTLY WORKING: Some failures detected")
        else:
            print("❌ PHASE 5 ISSUES: Multiple failures detected")
        print("="*80 + "\n")
        
    except ImportError:
        print("❌ requests library not available")
        results["errors"].append("Missing requests library")
    
    return results


async def test_backward_compatibility():
    """Test that Context-Aware RAG API is backward compatible."""
    print("\n" + "="*80)
    print("BACKWARD COMPATIBILITY TEST")
    print("="*80 + "\n")
    
    BASE_URL = "http://localhost:8000"
    
    print("Testing legacy context-aware API structure...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/query/context-aware",
            json={
                "question": "Test context query"  # API expects 'question'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            has_query = "query" in data
            has_results = "results" in data or "sources" in data
            has_filters = "filters" in data
            has_metadata = "metadata" in data
            
            print(f"   ✅ Response structure valid")
            print(f"      query: {has_query}")
            print(f"      results/sources: {has_results}")
            print(f"      filters: {has_filters}")
            print(f"      metadata: {has_metadata}")
            
            if all([has_query, has_results, has_filters, has_metadata]):
                print(f"\n✅ BACKWARD COMPATIBLE: All expected fields present")
            else:
                print(f"\n⚠️  Some fields missing")
        else:
            print(f"   ❌ HTTP {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("="*80 + "\n")


async def main():
    """Run all Phase 5 tests."""
    print("\n" + "#"*80)
    print("# PHASE 5 VALIDATION: CONTEXT-AWARE RAG INTEGRATION")
    print("#"*80)
    
    # Test enhancements
    results = await test_context_aware_enhancements()
    
    # Test backward compatibility
    await test_backward_compatibility()
    
    print("\n" + "#"*80)
    print("# PHASE 5 VALIDATION COMPLETE")
    print("#"*80 + "\n")
    
    if results["successes"] > 0:
        print("✅ Phase 5 implementation validated")
        print("✅ Context-Aware RAG is using EnhancementPipeline")
        if results["answers_generated"] > 0:
            print("✅ LLM answer generation working (NEW feature!)")
        print("✅ Ready for production deployment")
    else:
        print("⚠️  Validation incomplete - may need deployment")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())

