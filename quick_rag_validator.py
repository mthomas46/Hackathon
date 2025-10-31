#!/usr/bin/env python3
"""
Quick RAG Validation - Tests core RAG types only
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_QUERY = "How to configure Docker networking?"

def test_rag_type(name, url, payload, timeout=25):
    """Test a single RAG type."""
    print(f"\n{name}...", end=" ", flush=True)
    start = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            sources = len(data.get('sources', []))
            print(f"✅ {elapsed:.2f}s, {sources} sources")
            return {"success": True, "time": elapsed, "sources": sources}
        else:
            print(f"❌ HTTP {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except requests.Timeout:
        print(f"❌ Timeout ({timeout}s)")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"❌ {str(e)[:50]}")
        return {"success": False, "error": str(e)[:50]}

def main():
    print("\n" + "="*80)
    print("QUICK RAG VALIDATION - Core Types Only")
    print("="*80)
    print(f"Query: '{TEST_QUERY}'")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    
    results = {}
    
    # Test 1: Standard (baseline)
    results["standard"] = test_rag_type(
        "1. Standard RAG",
        f"{BASE_URL}/api/v1/rag/ask/standard",
        {"question": TEST_QUERY, "n_results": 10},
        timeout=20
    )
    
    # Test 2: Enhanced Phase 1
    results["phase1"] = test_rag_type(
        "2. Enhanced Phase 1",
        f"{BASE_URL}/api/v1/rag/ask/enhanced",
        {
            "question": TEST_QUERY,
            "n_results": 10,
            "enable_hybrid_search": True,
            "enable_query_rewriting": True,
            "enable_confidence_scoring": True
        },
        timeout=25
    )
    
    # Test 3: Enhanced Phase 1+2 (without comparative routing issue)
    results["phase1_2"] = test_rag_type(
        "3. Enhanced Phase 1+2",
        f"{BASE_URL}/api/v1/rag/ask/enhanced",
        {
            "question": TEST_QUERY,
            "n_results": 10,
            "enable_hybrid_search": True,
            "enable_query_rewriting": True,
            "enable_confidence_scoring": True,
            "enable_reranking": True,
            "enable_context_optimization": True,
            "context_strategy": "balanced"
        },
        timeout=30
    )
    
    # Test 4: Contextual (if exists)
    results["contextual"] = test_rag_type(
        "4. Contextual Query",
        f"{BASE_URL}/api/v1/query/enhanced",
        {
            "question": TEST_QUERY,
            "mode": "contextual",
            "n_results": 10
        },
        timeout=20
    )
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results.values() if r.get("success"))
    total = len(results)
    
    print(f"\nSuccess Rate: {successful}/{total} ({successful/total*100:.0f}%)")
    
    for name, result in results.items():
        status = "✅" if result.get("success") else "❌"
        time_str = f"{result.get('time', 0):.2f}s" if result.get("success") else "Failed"
        sources = f"{result.get('sources', 0)} src" if result.get("success") else ""
        print(f"  {status} {name:15} {time_str:>8}  {sources}")
    
    print("\n" + "="*80)
    
    if successful == total:
        print("🎉 ALL CORE RAG TYPES WORKING!")
    elif successful >= total * 0.75:
        print("✅ MOST RAG TYPES WORKING")
    else:
        print("⚠️  SOME ISSUES DETECTED")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Service not healthy!")
            exit(1)
    except Exception as e:
        print(f"❌ Cannot connect: {e}")
        exit(1)
    
    main()

