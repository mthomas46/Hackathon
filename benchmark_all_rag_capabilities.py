"""
Comprehensive RAG Capabilities Benchmark

Tests all RAG enhancements across Phase 1, 2, and 3:
- Standard RAG
- Hybrid search (Phase 1)
- Query rewriting (Phase 1)
- Confidence scoring (Phase 1)
- Reranking (Phase 2)
- Context optimization (Phase 2)
- Intent classification (Phase 5R)
- Contradiction detection (Phase 7R)
- Difficulty estimation (Phase 7R)
- Document caching (Phase 3A)
- BM25 serialization (Phase 3B)
- Batch processing (Phase 3C)
- Cache monitoring
"""

import asyncio
import time
import requests
import json
from typing import List, Dict, Any
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Test queries of varying complexity
TEST_QUERIES = {
    "simple": [
        "What is Docker?",
        "What is Kubernetes?",
        "What is MCP?"
    ],
    "moderate": [
        "How do I deploy a Docker container?",
        "How does Kubernetes orchestration work?",
        "What are the benefits of using MCP?"
    ],
    "complex": [
        "Compare Docker and Kubernetes for production deployment",
        "Explain the architecture of Model Context Protocol",
        "What are best practices for container security?"
    ],
    "vague": [
        "something about containers",
        "stuff with orchestration",
        "things related to deployment"
    ]
}


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"{title}")
    print("="*80)


def test_service_health():
    """Verify service is running."""
    print_section("SERVICE HEALTH CHECK")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Service health: {response.status_code}")
        if response.status_code == 200:
            return True
    except Exception as e:
        print(f"❌ Service unreachable: {e}")
        return False
    
    return False


def test_standard_rag():
    """Test standard RAG without enhancements."""
    print_section("TEST 1: Standard RAG (Baseline)")
    
    query = "What is Docker?"
    print(f"\nQuery: '{query}'")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={"question": query},
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success ({elapsed:.3f}s)")
            print(f"   Answer length: {len(result.get('answer', ''))} chars")
            print(f"   Sources: {len(result.get('sources', []))}")
            return {"status": "success", "time": elapsed, "result": result}
        else:
            print(f"❌ Error: {response.status_code}")
            return {"status": "error", "time": elapsed, "error": response.status_code}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception: {e}")
        return {"status": "exception", "time": elapsed, "error": str(e)}


def test_hybrid_search():
    """Test Phase 1: Hybrid search."""
    print_section("TEST 2: Hybrid Search (Phase 1)")
    
    query = "Docker containers orchestration"
    print(f"\nQuery: '{query}'")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/ask/enhanced",
            json={
                "question": query,
                "enable_hybrid_search": True,
                "semantic_weight": 0.6,
                "keyword_weight": 0.4,
                "n_results": 10
            },
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            metadata = result.get('metadata', {})
            print(f"✅ Success ({elapsed:.3f}s)")
            print(f"   Search method: {metadata.get('search_method', 'unknown')}")
            print(f"   Sources: {len(result.get('sources', []))}")
            print(f"   Confidence: {result.get('confidence', 0):.1f}%")
            return {"status": "success", "time": elapsed, "result": result}
        else:
            print(f"❌ Error: {response.status_code}")
            return {"status": "error", "time": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception: {e}")
        return {"status": "exception", "time": elapsed, "error": str(e)}


def test_query_rewriting():
    """Test Phase 1: Query rewriting."""
    print_section("TEST 3: Query Rewriting (Phase 1)")
    
    query = "docker setup guide"
    print(f"\nQuery: '{query}'")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/ask/enhanced",
            json={
                "question": query,
                "enable_query_rewriting": True,
                "enable_hybrid_search": True,
                "n_results": 5
            },
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            metadata = result.get('metadata', {})
            print(f"✅ Success ({elapsed:.3f}s)")
            print(f"   Rewritten query used: {metadata.get('query_rewritten', False)}")
            print(f"   Sources: {len(result.get('sources', []))}")
            return {"status": "success", "time": elapsed, "result": result}
        else:
            print(f"❌ Error: {response.status_code}")
            return {"status": "error", "time": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception: {e}")
        return {"status": "exception", "time": elapsed, "error": str(e)}


def test_confidence_scoring():
    """Test Phase 1: Confidence scoring."""
    print_section("TEST 4: Confidence Scoring (Phase 1)")
    
    query = "What are Docker best practices?"
    print(f"\nQuery: '{query}'")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/ask/enhanced",
            json={
                "question": query,
                "enable_confidence_scoring": True,
                "enable_hybrid_search": True,
                "n_results": 10
            },
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success ({elapsed:.3f}s)")
            print(f"   Confidence: {result.get('confidence', 0):.1f}%")
            print(f"   Confidence level: {result.get('confidence_level', 'unknown')}")
            
            breakdown = result.get('confidence_breakdown', {})
            if breakdown:
                print(f"   Breakdown:")
                for key, value in breakdown.items():
                    print(f"     - {key}: {value:.2f}")
            
            return {"status": "success", "time": elapsed, "result": result}
        else:
            print(f"❌ Error: {response.status_code}")
            return {"status": "error", "time": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception: {e}")
        return {"status": "exception", "time": elapsed, "error": str(e)}


def test_reranking():
    """Test Phase 2: Cross-encoder reranking."""
    print_section("TEST 5: Cross-Encoder Reranking (Phase 2)")
    
    query = "How to optimize Docker performance?"
    print(f"\nQuery: '{query}'")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/ask/enhanced",
            json={
                "question": query,
                "enable_reranking": True,
                "enable_hybrid_search": True,
                "n_results": 10
            },
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            metadata = result.get('metadata', {})
            print(f"✅ Success ({elapsed:.3f}s)")
            print(f"   Reranking used: {metadata.get('reranking_enabled', False)}")
            print(f"   Sources: {len(result.get('sources', []))}")
            return {"status": "success", "time": elapsed, "result": result}
        else:
            print(f"❌ Error: {response.status_code}")
            return {"status": "error", "time": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception: {e}")
        return {"status": "exception", "time": elapsed, "error": str(e)}


def test_context_optimization():
    """Test Phase 2: Context optimization."""
    print_section("TEST 6: Context Optimization (Phase 2)")
    
    query = "Docker networking concepts"
    print(f"\nQuery: '{query}'")
    
    strategies = ["balanced", "quality", "diversity"]
    results = {}
    
    for strategy in strategies:
        print(f"\n  Testing strategy: {strategy}")
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/rag/ask/enhanced",
                json={
                    "question": query,
                    "enable_context_optimization": True,
                    "context_strategy": strategy,
                    "enable_hybrid_search": True,
                    "n_results": 10
                },
                timeout=30
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                metadata = result.get('metadata', {})
                print(f"    ✅ Success ({elapsed:.3f}s)")
                print(f"       Strategy used: {metadata.get('context_strategy', 'unknown')}")
                print(f"       Sources: {len(result.get('sources', []))}")
                results[strategy] = {"status": "success", "time": elapsed}
            else:
                print(f"    ❌ Error: {response.status_code}")
                results[strategy] = {"status": "error", "time": elapsed}
        except Exception as e:
            elapsed = time.time() - start
            print(f"    ❌ Exception: {e}")
            results[strategy] = {"status": "exception", "time": elapsed}
    
    return results


def test_intent_classification():
    """Test Phase 5R: Intent classification."""
    print_section("TEST 7: Intent Classification (Phase 5R)")
    
    test_cases = [
        ("What is Docker?", "factual"),
        ("How to install Docker?", "procedural"),
        ("Compare Docker vs Podman", "comparative"),
    ]
    
    results = []
    for query, expected_type in test_cases:
        print(f"\n  Query: '{query}' (expected: {expected_type})")
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/rag/ask/enhanced",
                json={
                    "question": query,
                    "enable_intent_classification": True,
                    "enable_hybrid_search": True,
                    "n_results": 5
                },
                timeout=30
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                metadata = result.get('metadata', {})
                intent = metadata.get('query_intent', {})
                print(f"    ✅ Success ({elapsed:.3f}s)")
                print(f"       Intent type: {intent.get('type', 'unknown')}")
                print(f"       Complexity: {intent.get('complexity', 'unknown')}")
                results.append({"status": "success", "time": elapsed, "intent": intent})
            else:
                print(f"    ❌ Error: {response.status_code}")
                results.append({"status": "error", "time": elapsed})
        except Exception as e:
            elapsed = time.time() - start
            print(f"    ❌ Exception: {e}")
            results.append({"status": "exception", "time": elapsed})
    
    return results


def test_difficulty_estimation():
    """Test Phase 7R: Query difficulty estimation."""
    print_section("TEST 8: Query Difficulty Estimation (Phase 7R)")
    
    test_cases = [
        ("What is Docker?", "easy"),
        ("something vague", "hard"),
    ]
    
    results = []
    for query, expected_level in test_cases:
        print(f"\n  Query: '{query}' (expected: {expected_level})")
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/rag/ask/enhanced",
                json={
                    "question": query,
                    "enable_difficulty_estimation": True,
                    "enable_hybrid_search": True,
                    "n_results": 5
                },
                timeout=30
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                metadata = result.get('metadata', {})
                difficulty = metadata.get('query_difficulty', {})
                print(f"    ✅ Success ({elapsed:.3f}s)")
                print(f"       Difficulty: {difficulty.get('difficulty_level', 'unknown')}")
                print(f"       Score: {difficulty.get('difficulty_score', 0)}")
                results.append({"status": "success", "time": elapsed, "difficulty": difficulty})
            else:
                print(f"    ❌ Error: {response.status_code}")
                results.append({"status": "error", "time": elapsed})
        except Exception as e:
            elapsed = time.time() - start
            print(f"    ❌ Exception: {e}")
            results.append({"status": "exception", "time": elapsed})
    
    return results


def test_all_enhancements_combined():
    """Test all enhancements enabled together."""
    print_section("TEST 9: All Enhancements Combined")
    
    query = "What are the best practices for Docker container security?"
    print(f"\nQuery: '{query}'")
    print("Enabling ALL enhancements...")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/ask/enhanced",
            json={
                "question": query,
                "n_results": 10,
                # Phase 1
                "enable_hybrid_search": True,
                "enable_query_rewriting": True,
                "enable_confidence_scoring": True,
                # Phase 2
                "enable_reranking": True,
                "enable_context_optimization": True,
                "enable_metadata_filtering": True,
                # Phase 5R & 7R
                "enable_intent_classification": True,
                "enable_difficulty_estimation": True,
                "enable_contradiction_detection": True,
                # Weights
                "semantic_weight": 0.6,
                "keyword_weight": 0.4,
                "context_strategy": "balanced"
            },
            timeout=60
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            metadata = result.get('metadata', {})
            
            print(f"✅ Success ({elapsed:.3f}s)")
            print(f"\n  Answer Preview:")
            answer = result.get('answer', '')
            print(f"  {answer[:200]}..." if len(answer) > 200 else f"  {answer}")
            
            print(f"\n  Metadata:")
            print(f"    Search method: {metadata.get('search_method', 'unknown')}")
            print(f"    Sources: {len(result.get('sources', []))}")
            print(f"    Confidence: {result.get('confidence', 0):.1f}%")
            
            if 'query_intent' in metadata:
                intent = metadata['query_intent']
                print(f"    Intent: {intent.get('type', 'unknown')}/{intent.get('complexity', 'unknown')}")
            
            if 'query_difficulty' in metadata:
                difficulty = metadata['query_difficulty']
                print(f"    Difficulty: {difficulty.get('difficulty_level', 'unknown')}")
            
            print(f"\n  Source Quality Scores:")
            for i, source in enumerate(result.get('sources', [])[:3], 1):
                score = source.get('quality_score', 0)
                path = source.get('file_path', 'unknown')
                print(f"    {i}. {path}: {score}/100")
            
            return {"status": "success", "time": elapsed, "result": result}
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return {"status": "error", "time": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception: {e}")
        return {"status": "exception", "time": elapsed, "error": str(e)}


def test_batch_processing():
    """Test Phase 3C: Batch processing."""
    print_section("TEST 10: Batch Processing (Phase 3C)")
    
    queries = [
        {"id": "q1", "question": "What is Docker?"},
        {"id": "q2", "question": "What is Kubernetes?"},
        {"id": "q3", "question": "What is container orchestration?"},
        {"id": "q4", "question": "How to deploy containers?"},
        {"id": "q5", "question": "Docker networking basics"}
    ]
    
    print(f"\nProcessing {len(queries)} queries in batch...")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/rag/ask/batch",
            json={
                "queries": queries,
                "max_parallel": 3,
                "enable_hybrid_search": True,
                "enable_confidence_scoring": True
            },
            timeout=60
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success ({elapsed:.3f}s)")
            print(f"   Total queries: {result.get('total_queries', 0)}")
            print(f"   Successful: {result.get('successful', 0)}")
            print(f"   Failed: {result.get('failed', 0)}")
            print(f"   Avg time per query: {result.get('avg_time_per_query_ms', 0)}ms")
            print(f"   Throughput: {len(queries) / elapsed:.1f} queries/sec")
            return {"status": "success", "time": elapsed, "result": result}
        else:
            print(f"❌ Error: {response.status_code}")
            return {"status": "error", "time": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception: {e}")
        return {"status": "exception", "time": elapsed, "error": str(e)}


def test_cache_metrics():
    """Test Phase 3: Cache monitoring."""
    print_section("TEST 11: Cache Metrics (Phase 3)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/cache/metrics", timeout=10)
        
        if response.status_code == 200:
            metrics = response.json()
            redis = metrics.get('redis', {})
            phase_metrics = metrics.get('phase_metrics', {})
            
            print(f"✅ Cache Metrics Retrieved")
            print(f"\n  Redis Stats:")
            print(f"    Hit rate: {redis.get('hit_rate', 0):.1f}%")
            print(f"    Total requests: {redis.get('total_requests', 0)}")
            print(f"    Hits: {redis.get('hits', 0)}")
            print(f"    Misses: {redis.get('misses', 0)}")
            print(f"    Used memory: {redis.get('used_memory', 'unknown')}")
            print(f"    Total keys: {redis.get('total_keys', 0)}")
            
            print(f"\n  Phase-Specific Cache Counts:")
            print(f"    Phase 1 answer cache: {phase_metrics.get('phase1_answer_cache', 0)}")
            print(f"    Phase 3A document cache: {phase_metrics.get('phase3a_document_cache', 0)}")
            print(f"    Phase 3B BM25 index cache: {phase_metrics.get('phase3b_bm25_index_cache', 0)}")
            print(f"    Embedding cache: {phase_metrics.get('embedding_cache', 0)}")
            print(f"    ChromaDB search cache: {phase_metrics.get('chroma_search_cache', 0)}")
            
            return {"status": "success", "metrics": metrics}
        else:
            print(f"❌ Error: {response.status_code}")
            return {"status": "error"}
    except Exception as e:
        print(f"❌ Exception: {e}")
        return {"status": "exception", "error": str(e)}


def generate_report(results: Dict[str, Any]):
    """Generate final benchmark report."""
    print_section("COMPREHENSIVE BENCHMARK REPORT")
    
    print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Service: {BASE_URL}")
    
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("-" * 80)
    
    test_names = [
        "Standard RAG",
        "Hybrid Search (Phase 1)",
        "Query Rewriting (Phase 1)",
        "Confidence Scoring (Phase 1)",
        "Reranking (Phase 2)",
        "Context Optimization (Phase 2)",
        "Intent Classification (Phase 5R)",
        "Difficulty Estimation (Phase 7R)",
        "All Enhancements Combined",
        "Batch Processing (Phase 3C)",
        "Cache Metrics (Phase 3)"
    ]
    
    for i, name in enumerate(test_names, 1):
        key = f"test{i}"
        if key in results:
            result = results[key]
            status = result.get('status', 'unknown')
            time_taken = result.get('time', 0)
            
            status_icon = "✅" if status == "success" else "❌"
            print(f"{status_icon} Test {i}: {name}")
            if status == "success":
                print(f"   Time: {time_taken:.3f}s")
        else:
            print(f"⚠️  Test {i}: {name} - Not run")
    
    print(f"\n📈 PERFORMANCE SUMMARY")
    print("-" * 80)
    
    times = [r.get('time', 0) for r in results.values() if r.get('status') == 'success' and 'time' in r]
    if times:
        print(f"Average response time: {sum(times) / len(times):.3f}s")
        print(f"Fastest: {min(times):.3f}s")
        print(f"Slowest: {max(times):.3f}s")
    
    print(f"\n✅ BENCHMARK COMPLETE")
    print("="*80)
    
    return results


async def run_all_benchmarks():
    """Run all benchmark tests."""
    print("\n" + "="*80)
    print("COMPREHENSIVE RAG CAPABILITIES BENCHMARK")
    print("Testing Phase 1 + 2 + 3 + 5R + 7R Enhancements")
    print("="*80)
    
    # Check service health
    if not test_service_health():
        print("\n❌ Service is not available. Exiting.")
        return
    
    results = {}
    
    # Run all tests
    results['test1'] = test_standard_rag()
    results['test2'] = test_hybrid_search()
    results['test3'] = test_query_rewriting()
    results['test4'] = test_confidence_scoring()
    results['test5'] = test_reranking()
    results['test6'] = test_context_optimization()
    results['test7'] = test_intent_classification()
    results['test8'] = test_difficulty_estimation()
    results['test9'] = test_all_enhancements_combined()
    results['test10'] = test_batch_processing()
    results['test11'] = test_cache_metrics()
    
    # Generate report
    generate_report(results)
    
    return results


if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())

