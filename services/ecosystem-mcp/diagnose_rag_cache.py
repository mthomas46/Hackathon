#!/usr/bin/env python3
"""
Diagnose RAG Caching Issue

This script investigates why RAG caching only provides 1.4x speedup vs expected 36x+.

Potential causes:
1. Cache keys not matching between requests
2. LLM non-determinism causing different responses
3. Temperature settings causing variations
4. Cache not being hit due to key generation issues
"""

import asyncio
import time
import httpx
import json
import hashlib

BASE_URL = "http://localhost:8000"


async def test_rag_cache_consistency():
    """
    Test if the same question generates the same cache key and hits cache.
    """
    print("="*80)
    print("RAG CACHE DIAGNOSTIC TEST")
    print("="*80)
    
    question = "What is the main purpose of ecosystem-mcp?"
    
    # Test parameters that should generate identical cache keys
    request_params = {
        "question": question,
        "n_results": 10,
        "prefer_recent": True,
        "temperature": 0.7
    }
    
    # Calculate expected cache key (matching the key generation logic)
    key_data = json.dumps(request_params, sort_keys=True)
    key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
    expected_key = f"rag:{key_hash}"
    
    print(f"\n📋 Test Parameters:")
    print(f"   Question: {question}")
    print(f"   n_results: {request_params['n_results']}")
    print(f"   prefer_recent: {request_params['prefer_recent']}")
    print(f"   temperature: {request_params['temperature']}")
    print(f"   Expected cache key: {expected_key}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Request 1
        print(f"\n🔹 Request 1 (should be cache MISS)...")
        start1 = time.time()
        response1 = await client.post(
            f"{BASE_URL}/api/v1/ask",
            json=request_params
        )
        time1 = time.time() - start1
        
        if response1.status_code != 200:
            print(f"❌ Request 1 failed: {response1.status_code} - {response1.text}")
            return
        
        answer1 = response1.json()["answer"]
        print(f"✅ Request 1 completed in {time1:.2f}s")
        print(f"   Answer length: {len(answer1)} chars")
        print(f"   First 100 chars: {answer1[:100]}...")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Request 2 (should hit cache)
        print(f"\n🔹 Request 2 (should be cache HIT)...")
        start2 = time.time()
        response2 = await client.post(
            f"{BASE_URL}/api/v1/ask",
            json=request_params
        )
        time2 = time.time() - start2
        
        if response2.status_code != 200:
            print(f"❌ Request 2 failed: {response2.status_code} - {response2.text}")
            return
        
        answer2 = response2.json()["answer"]
        print(f"✅ Request 2 completed in {time2:.2f}s")
        print(f"   Answer length: {len(answer2)} chars")
        print(f"   First 100 chars: {answer2[:100]}...")
        
        # Analysis
        print(f"\n{'='*80}")
        print("ANALYSIS")
        print(f"{'='*80}")
        
        speedup = time1 / time2 if time2 > 0 else 0
        answers_match = answer1 == answer2
        
        print(f"\n⏱️  Performance:")
        print(f"   Request 1: {time1:.2f}s")
        print(f"   Request 2: {time2:.2f}s")
        print(f"   Speedup: {speedup:.1f}x")
        
        print(f"\n🔍 Cache Behavior:")
        print(f"   Answers match: {'✅ Yes' if answers_match else '❌ No'}")
        print(f"   Answer length match: {'✅ Yes' if len(answer1) == len(answer2) else '❌ No'}")
        
        if speedup < 2:
            print(f"\n❌ ISSUE DETECTED: Speedup is only {speedup:.1f}x (expected >10x)")
            print(f"\nPossible causes:")
            
            if not answers_match:
                print(f"   1. ⚠️  Answers don't match - cache likely MISSED")
                print(f"      - LLM may be non-deterministic")
                print(f"      - Temperature={request_params['temperature']} may cause variation")
                print(f"      - Try setting temperature=0 for deterministic responses")
            
            if time2 > 1.0:
                print(f"   2. ⚠️  Request 2 took {time2:.2f}s - cache likely MISSED")
                print(f"      - Cache key generation may be inconsistent")
                print(f"      - Check if cache keys match in logs")
            
            print(f"\n💡 Recommendations:")
            print(f"   1. Check Redis logs for cache key: {expected_key}")
            print(f"   2. Check application logs for 'Cache HIT' vs 'Cache MISS'")
            print(f"   3. Try temperature=0 for deterministic responses")
            print(f"   4. Verify cache decorator is working correctly")
        
        elif speedup >= 10:
            print(f"\n✅ CACHE WORKING PERFECTLY! {speedup:.1f}x speedup")
        
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: {speedup:.1f}x speedup (expected >10x)")
            print(f"   Cache may be hitting but with overhead")
        
        # Test with temperature=0
        print(f"\n{'='*80}")
        print("DETERMINISTIC TEST (temperature=0)")
        print(f"{'='*80}")
        
        request_params_det = {
            **request_params,
            "temperature": 0.0
        }
        
        print(f"\n🔹 Request 3 (temperature=0, cache MISS)...")
        start3 = time.time()
        response3 = await client.post(
            f"{BASE_URL}/api/v1/ask",
            json=request_params_det
        )
        time3 = time.time() - start3
        
        if response3.status_code == 200:
            answer3 = response3.json()["answer"]
            print(f"✅ Request 3 completed in {time3:.2f}s")
            
            await asyncio.sleep(2)
            
            print(f"\n🔹 Request 4 (temperature=0, should cache HIT)...")
            start4 = time.time()
            response4 = await client.post(
                f"{BASE_URL}/api/v1/ask",
                json=request_params_det
            )
            time4 = time.time() - start4
            
            if response4.status_code == 200:
                answer4 = response4.json()["answer"]
                print(f"✅ Request 4 completed in {time4:.2f}s")
                
                speedup_det = time3 / time4 if time4 > 0 else 0
                answers_match_det = answer3 == answer4
                
                print(f"\n📊 Deterministic Results:")
                print(f"   Speedup: {speedup_det:.1f}x")
                print(f"   Answers match: {'✅ Yes' if answers_match_det else '❌ No'}")
                
                if speedup_det > speedup:
                    print(f"\n💡 INSIGHT: Deterministic mode ({speedup_det:.1f}x) is better than default ({speedup:.1f}x)")
                    print(f"   → Temperature is likely causing cache misses")
                    print(f"   → Consider using temperature=0 for cacheable queries")


async def main():
    """Run diagnostics."""
    try:
        await test_rag_cache_consistency()
        
        print(f"\n{'='*80}")
        print("DIAGNOSTIC COMPLETE")
        print(f"{'='*80}")
        print(f"\nNext steps:")
        print(f"1. Check logs for 'Cache HIT' and 'Cache MISS' messages")
        print(f"2. Monitor cache stats at: GET {BASE_URL}/api/v1/cache/stats")
        print(f"3. If cache is missing, investigate key generation")
        print(f"4. Consider temperature=0 for deterministic caching")
        
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

