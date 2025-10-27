#!/usr/bin/env python3
"""
Test script to validate both fixes:
1. Period generation with detailed logging
2. Temporal RAG ChromaDB query fix
"""

import httpx
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def test_period_generation():
    """Test period generation with logging."""
    print("\n" + "=" * 80)
    print("  TEST 1: Period Generation")
    print("=" * 80 + "\n")
    
    timeline_id = "d1739d94-638d-43fd-b076-dd48d4f11e07"
    
    print(f"📋 Timeline ID: {timeline_id}")
    print(f"🔗 Endpoint: POST /api/v1/timelines/{timeline_id}/periods/generate")
    
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/timelines/{timeline_id}/periods/generate",
            timeout=30.0
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📦 Response Body:")
        print(response.text[:500])
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"   Periods generated: {data.get('count', 0)}")
            print(f"   Strategy: {data.get('strategy', 'N/A')}")
            return True
        else:
            print(f"\n❌ FAILED!")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def test_temporal_rag():
    """Test temporal RAG with ChromaDB query fix."""
    print("\n" + "=" * 80)
    print("  TEST 2: Temporal RAG ChromaDB Query")
    print("=" * 80 + "\n")
    
    question = "What is the testing strategy?"
    as_of_date = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
    
    print(f"📋 Question: {question}")
    print(f"📅 As of date: {as_of_date[:10]}")
    print(f"🔗 Endpoint: POST /api/v1/rag/temporal/query")
    
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/rag/temporal/query",
            json={
                "question": question,
                "as_of_date": as_of_date,
                "service_name": "ecosystem-mcp",
                "limit": 10
            },
            timeout=30.0
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!")
            
            answer = data.get("answer", "")
            sources = data.get("sources", [])
            metadata = data.get("metadata", {})
            
            print(f"\n📊 Results:")
            print(f"   Sources found: {len(sources)}")
            print(f"   Temporal filter applied: {metadata.get('temporal_filter_applied', False)}")
            print(f"   As of date: {metadata.get('as_of_date', 'N/A')[:10]}")
            
            print(f"\n💬 Answer Preview:")
            print(f"   {answer[:300]}...")
            
            return True
        else:
            print(f"\n❌ FAILED!")
            print(f"📦 Error Response:")
            print(response.text[:500])
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def test_standard_vs_temporal():
    """Compare standard vs temporal RAG."""
    print("\n" + "=" * 80)
    print("  TEST 3: Standard vs Temporal RAG Comparison")
    print("=" * 80 + "\n")
    
    question = "What are the key features?"
    
    # Standard RAG
    print("🔵 Standard RAG:")
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/query/enhanced",
            json={"question": question, "n_results": 10},
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success")
            print(f"   Sources: {len(data.get('sources', []))}")
            print(f"   Answer length: {len(data.get('answer', ''))} chars")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Temporal RAG
    print("\n🟢 Temporal RAG:")
    as_of_date = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
    
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/rag/temporal/query",
            json={
                "question": question,
                "as_of_date": as_of_date,
                "service_name": "ecosystem-mcp",
                "limit": 10
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success")
            print(f"   Sources: {len(data.get('sources', []))}")
            print(f"   Answer length: {len(data.get('answer', ''))} chars")
            print(f"   Temporal aware: {data.get('metadata', {}).get('temporal_filter_applied', False)}")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("\n" + "=" * 80)
    print("  COMPREHENSIVE FIX VALIDATION")
    print("=" * 80)
    print("\n🎯 Testing both fixes:")
    print("   1. Period generation endpoint")
    print("   2. Temporal RAG ChromaDB query")
    
    results = {
        "period_generation": test_period_generation(),
        "temporal_rag": test_temporal_rag(),
        "comparison": test_standard_vs_temporal()
    }
    
    print("\n" + "=" * 80)
    print("  FINAL RESULTS")
    print("=" * 80 + "\n")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    success_count = sum(1 for p in results.values() if p)
    total_count = len(results)
    
    print(f"\n📊 Summary: {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        print(f"\n🎉 ALL TESTS PASSED! Both fixes working!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check logs above.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
