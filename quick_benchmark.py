#!/usr/bin/env python3
"""
Quick RAG Benchmark: Standard vs Enhanced
Tests 3 queries to demonstrate the improvements quickly.
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

TEST_QUERIES = [
    {"question": "What is Docker?", "category": "simple"},
    {"question": "How to configure Docker networking?", "category": "moderate"},
    {"question": "Compare Docker Swarm vs Kubernetes", "category": "complex"}
]

def test_query(question, config_name, config):
    """Test a single query with given configuration."""
    print(f"    Testing {config_name}...", end=" ", flush=True)
    start = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/ask/enhanced",
            json={"question": question, **config},
            timeout=35
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            sources = len(data.get("sources", []))
            conf = data.get("confidence_score")
            conf_str = f", conf: {conf:.3f}" if conf else ""
            print(f"✅ {elapsed:.2f}s, {sources} sources{conf_str}")
            return {"success": True, "time": elapsed, "sources": sources, "confidence": conf}
        else:
            print(f"❌ HTTP {response.status_code}")
            return {"success": False, "time": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ {str(e)[:50]}")
        return {"success": False, "time": elapsed, "error": str(e)}

def main():
    print("\n" + "="*80)
    print("QUICK RAG BENCHMARK: Standard vs Enhanced")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test configurations
    configs = {
        "Standard (semantic only)": {
            "n_results": 10,
            "enable_hybrid_search": False,
            "enable_query_rewriting": False,
            "enable_reranking": False,
            "enable_context_optimization": False
        },
        "Enhanced Phase 1": {
            "n_results": 10,
            "enable_hybrid_search": True,
            "enable_query_rewriting": True,
            "enable_confidence_scoring": True,
            "semantic_weight": 0.7,
            "keyword_weight": 0.3
        },
        "Enhanced Phase 1+2": {
            "n_results": 10,
            "enable_hybrid_search": True,
            "enable_query_rewriting": True,
            "enable_confidence_scoring": True,
            "semantic_weight": 0.7,
            "keyword_weight": 0.3,
            "enable_reranking": True,
            "enable_context_optimization": True,
            "context_strategy": "balanced"
        }
    }
    
    results = {name: [] for name in configs.keys()}
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] Query: '{query['question']}'")
        print(f"  Category: {query['category']}")
        
        for config_name, config in configs.items():
            result = test_query(query['question'], config_name, config)
            results[config_name].append(result)
            time.sleep(0.5)  # Small delay between tests
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for config_name, config_results in results.items():
        successful = [r for r in config_results if r.get("success")]
        if successful:
            avg_time = sum(r["time"] for r in successful) / len(successful)
            avg_sources = sum(r.get("sources", 0) for r in successful) / len(successful)
            success_rate = len(successful) / len(config_results) * 100
            print(f"\n{config_name}:")
            print(f"  Success: {success_rate:.0f}% ({len(successful)}/{len(config_results)})")
            print(f"  Avg Time: {avg_time:.2f}s")
            print(f"  Avg Sources: {avg_sources:.1f}")
        else:
            print(f"\n{config_name}: ❌ All tests failed")
    
    print("\n" + "="*80)
    print("✅ BENCHMARK COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    # Quick health check
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Service not healthy!")
            exit(1)
    except Exception as e:
        print(f"❌ Cannot connect: {e}")
        exit(1)
    
    main()

