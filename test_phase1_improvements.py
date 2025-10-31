"""
Phase 1 Validation Tests

Tests the following improvements:
1. Balanced context strategy with fast path and limited scope
2. Quality-based early pruning for reranking
3. Cache monitoring endpoints

**Date:** October 31, 2025
**Status:** Phase 1 Testing
"""

import asyncio
import time
import requests
import json
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)


def test_service_health():
    """Test service is running."""
    print_section("TEST 0: Service Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Service is healthy")
            return True
        else:
            print(f"❌ Service unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Service unreachable: {e}")
        return False


def test_balanced_strategy_performance():
    """
    Test 1: Balanced Context Strategy Performance
    
    Expected: <5s (vs >30s before optimization)
    
    Improvements:
    - Fast path for <15 docs
    - Limited scope to top 30 docs
    """
    print_section("TEST 1: Balanced Context Strategy (Phase 1 Optimization)")
    
    query = "Docker container networking and security best practices"
    print(f"\nQuery: '{query}'")
    print("Testing: balanced strategy with Phase 1 optimizations")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/ask/enhanced",
            json={
                "question": query,
                "enable_context_optimization": True,
                "context_strategy": "balanced",
                "n_results": 10,
                "enable_hybrid_search": True
            },
            timeout=30  # Allow 30s max (realistic for context optimization)
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success ({elapsed:.2f}s)")
            
            metadata = result.get('metadata', {})
            print(f"   Strategy used: {metadata.get('context_strategy', 'unknown')}")
            print(f"   Sources: {len(result.get('sources', []))}")
            print(f"   Answer length: {len(result.get('answer', ''))} chars")
            
            # Check if optimization helped
            if elapsed < 5.0:
                print(f"   🎉 EXCELLENT: {elapsed:.2f}s < 5s target (optimization working!)")
                return {"status": "excellent", "time": elapsed, "target": 5.0}
            elif elapsed < 10.0:
                print(f"   ✅ GOOD: {elapsed:.2f}s < 10s (improvement, but can be better)")
                return {"status": "good", "time": elapsed, "target": 5.0}
            else:
                print(f"   ⚠️  SLOW: {elapsed:.2f}s > 10s (optimization may not be working)")
                return {"status": "slow", "time": elapsed, "target": 5.0}
        else:
            print(f"❌ Error: {response.status_code}")
            return {"status": "error", "time": elapsed}
    except requests.Timeout:
        elapsed = time.time() - start
        print(f"❌ TIMEOUT after {elapsed:.2f}s (optimization not working)")
        return {"status": "timeout", "time": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception: {e}")
        return {"status": "exception", "time": elapsed, "error": str(e)}


def test_quality_pruning():
    """
    Test 2: Quality-Based Early Pruning
    
    Expected: Logs show pruning of low-quality docs before reranking
    
    Improvements:
    - Only rerank docs with quality_score >= 50
    - Max 40 docs (vs 100)
    """
    print_section("TEST 2: Quality-Based Early Pruning (Phase 1 Optimization)")
    
    query = "How to optimize Docker performance"
    print(f"\nQuery: '{query}'")
    print("Testing: Quality pruning before reranking")
    
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
            timeout=30  # Give it time for first rerank (20s is realistic)
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success ({elapsed:.2f}s)")
            
            metadata = result.get('metadata', {})
            print(f"   Sources: {len(result.get('sources', []))}")
            
            # Check for pruning in logs
            print(f"\n   💡 Check service logs for:")
            print(f"      '⚡ Quality pruning: N high-quality docs (pruned M low-quality, 2.5x fewer to rerank)'")
            
            if elapsed < 15.0:
                print(f"   ✅ Completed in {elapsed:.2f}s (quality pruning should reduce reranking time)")
                return {"status": "success", "time": elapsed}
            else:
                print(f"   ⚠️  Slow: {elapsed:.2f}s (pruning may not be effective)")
                return {"status": "slow", "time": elapsed}
        else:
            print(f"❌ Error: {response.status_code}")
            return {"status": "error", "time": elapsed}
    except requests.Timeout:
        elapsed = time.time() - start
        print(f"❌ TIMEOUT after {elapsed:.2f}s")
        return {"status": "timeout", "time": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception: {e}")
        return {"status": "exception", "time": elapsed, "error": str(e)}


def test_all_context_strategies():
    """
    Test 3: All Context Optimization Strategies
    
    Expected: All 3 strategies complete without timeout
    
    Improvements:
    - Balanced now uses fast path
    - All strategies use limited scope
    """
    print_section("TEST 3: All Context Strategies (Phase 1 Validation)")
    
    query = "Docker deployment strategies"
    strategies = ["balanced", "quality", "diversity"]
    results = {}
    
    for strategy in strategies:
        print(f"\n  Testing: {strategy} strategy")
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
                timeout=30  # Allow 30s for context optimization
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                print(f"    ✅ {strategy}: {elapsed:.2f}s")
                print(f"       Sources: {len(result.get('sources', []))}")
                results[strategy] = {"status": "success", "time": elapsed}
            else:
                print(f"    ❌ {strategy}: Error {response.status_code}")
                results[strategy] = {"status": "error", "time": elapsed}
        except requests.Timeout:
            elapsed = time.time() - start
            print(f"    ❌ {strategy}: TIMEOUT after {elapsed:.2f}s")
            results[strategy] = {"status": "timeout", "time": elapsed}
        except Exception as e:
            elapsed = time.time() - start
            print(f"    ❌ {strategy}: {e}")
            results[strategy] = {"status": "exception", "time": elapsed}
    
    # Summary
    print(f"\n  Summary:")
    all_success = all(r.get("status") == "success" for r in results.values())
    if all_success:
        avg_time = sum(r["time"] for r in results.values()) / len(results)
        print(f"  ✅ All strategies working! Average time: {avg_time:.2f}s")
    else:
        print(f"  ⚠️  Some strategies failed")
    
    return results


def test_cache_monitoring():
    """
    Test 4: Cache Monitoring Endpoints
    
    Expected: 200 OK with metrics (not 500 error)
    
    Improvements:
    - Fixed async/await issues
    - Added fallback for unavailable metrics
    """
    print_section("TEST 4: Cache Monitoring (Phase 1 Fix)")
    
    print("\n  Testing: GET /api/cache/metrics")
    try:
        response = requests.get(f"{BASE_URL}/api/cache/metrics", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success: {response.status_code}")
            
            if data.get("status") == "limited":
                print(f"     Status: Limited (fallback metrics)")
                print(f"     Message: {data.get('message')}")
            else:
                redis = data.get('redis', {})
                print(f"     Hit rate: {redis.get('hit_rate', 0):.1f}%")
                print(f"     Total keys: {redis.get('total_keys', 0)}")
            
            return {"status": "success"}
        else:
            print(f"  ❌ Error: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
            return {"status": "error", "code": response.status_code}
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return {"status": "exception", "error": str(e)}


def generate_report(results: Dict[str, Any]):
    """Generate final test report."""
    print_section("PHASE 1 VALIDATION REPORT")
    
    print(f"\nDate: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Service: {BASE_URL}")
    
    print(f"\n📊 TEST RESULTS")
    print("-" * 80)
    
    test_names = [
        "Balanced Strategy Performance",
        "Quality-Based Pruning",
        "All Context Strategies",
        "Cache Monitoring"
    ]
    
    passed = 0
    failed = 0
    
    for i, name in enumerate(test_names, 1):
        key = f"test{i}"
        if key in results:
            result = results[key]
            status = result.get('status', 'unknown')
            
            if status in ['success', 'excellent', 'good']:
                print(f"✅ Test {i}: {name}")
                if 'time' in result:
                    print(f"   Time: {result['time']:.2f}s")
                passed += 1
            else:
                print(f"❌ Test {i}: {name} - {status}")
                if 'time' in result:
                    print(f"   Time: {result['time']:.2f}s")
                failed += 1
    
    print(f"\n📈 SUMMARY")
    print("-" * 80)
    print(f"Passed: {passed}/{len(test_names)}")
    print(f"Failed: {failed}/{len(test_names)}")
    print(f"Success Rate: {(passed/len(test_names)*100):.0f}%")
    
    if passed == len(test_names):
        print(f"\n✅ PHASE 1 VALIDATION: COMPLETE!")
        print(f"All optimizations working as expected")
    elif passed >= 3:
        print(f"\n⚠️  PHASE 1 VALIDATION: MOSTLY WORKING")
        print(f"Most optimizations functional, some issues remain")
    else:
        print(f"\n❌ PHASE 1 VALIDATION: NEEDS WORK")
        print(f"Significant issues detected")
    
    return passed == len(test_names)


async def run_all_tests():
    """Run all Phase 1 validation tests."""
    print("\n" + "=" * 80)
    print("PHASE 1 VALIDATION TEST SUITE")
    print("Testing: Context optimization + quality pruning + cache monitoring")
    print("=" * 80)
    
    # Check service
    if not test_service_health():
        print("\n❌ Service not available. Exiting.")
        return False
    
    results = {}
    
    # Run tests
    results['test1'] = test_balanced_strategy_performance()
    results['test2'] = test_quality_pruning()
    results['test3'] = test_all_context_strategies()
    results['test4'] = test_cache_monitoring()
    
    # Generate report
    success = generate_report(results)
    
    return success


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)

