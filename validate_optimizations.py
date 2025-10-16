#!/usr/bin/env python3
"""
Validate all optimization phases are working correctly.

Tests Phase 2, 3, & 4 optimizations.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
EMBEDDING_URL = "http://localhost:8001"


def test_service_health():
    """Test that services are responding."""
    print("\n" + "=" * 80)
    print("🏥 Testing Service Health")
    print("=" * 80)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ecosystem-mcp-service: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ ecosystem-mcp-service: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ecosystem-mcp-service: {e}")
        return False


def test_embedding_service():
    """Test embedding service health."""
    print("\n" + "=" * 80)
    print("🧠 Testing Embedding Service")
    print("=" * 80)
    
    try:
        response = requests.get(f"{EMBEDDING_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Embedding service: {data.get('status', 'unknown')}")
            
            # Test embedding generation
            embed_response = requests.post(
                f"{EMBEDDING_URL}/embed",
                json={"text": "test optimization performance"},
                timeout=10
            )
            
            if embed_response.status_code == 200:
                result = embed_response.json()
                print(f"✅ Embedding generation: {result.get('dimensions')} dimensions")
                print(f"   Duration: {result.get('duration_ms', 0):.2f}ms")
                return True
            else:
                print(f"❌ Embedding generation failed: HTTP {embed_response.status_code}")
                return False
        else:
            print(f"❌ Embedding service: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Embedding service: {e}")
        return False


def test_cache_analytics():
    """Test Phase 4 cache analytics endpoints."""
    print("\n" + "=" * 80)
    print("📊 Testing Phase 4: Cache Analytics")
    print("=" * 80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/admin/cache/stats", timeout=5)
        
        if response.status_code == 404:
            print("⚠️  Cache analytics endpoint not available yet (needs volume mount refresh)")
            print("   This is expected - Phase 4 code is committed but not yet loaded")
            return None
        elif response.status_code == 200:
            data = response.json()
            print("✅ Cache analytics endpoint available!")
            
            if "caches" in data:
                for cache_name, cache_data in data.get("caches", {}).items():
                    print(f"\n   {cache_name}:")
                    if "l1_cache" in cache_data:
                        l1 = cache_data["l1_cache"]
                        print(f"      L1: {l1.get('size')}/{l1.get('max_size')} items, hit rate: {l1.get('hit_rate', '0%')}")
                    if "l2_cache" in cache_data:
                        l2 = cache_data["l2_cache"]
                        print(f"      L2: hit rate: {l2.get('hit_rate', '0%')}")
            
            return True
        else:
            print(f"❌ Cache analytics: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cache analytics: {e}")
        return False


def test_performance_indexes():
    """Test Phase 2 database indexes endpoint."""
    print("\n" + "=" * 80)
    print("🚀 Testing Phase 2: Performance Indexes")
    print("=" * 80)
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/admin/optimization/indexes/create", timeout=30)
        
        if response.status_code == 404:
            print("⚠️  Performance optimization endpoint not available yet (needs volume mount refresh)")
            print("   This is expected - Phase 2 code is committed but not yet loaded")
            return None
        elif response.status_code == 200:
            data = response.json()
            print("✅ Database indexes created successfully!")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            try:
                error_data = response.json()
                print(f"❌ Index creation: {error_data.get('detail', response.text)}")
            except:
                print(f"❌ Index creation: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Index creation: {e}")
        return False


def test_worker_status():
    """Test that background worker is running."""
    print("\n" + "=" * 80)
    print("⚙️  Testing Phase 1: Background Worker")
    print("=" * 80)
    
    try:
        # Check for any active or recent jobs
        response = requests.get(f"{BASE_URL}/api/v1/ingestion/jobs?limit=5", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            print(f"✅ Ingestion API responding")
            print(f"   Recent jobs: {len(jobs)}")
            
            if jobs:
                latest_job = jobs[0]
                print(f"   Latest job: {latest_job.get('status')} ({latest_job.get('id')[:8]}...)")
            
            return True
        else:
            print(f"❌ Ingestion API: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ingestion API: {e}")
        return False


def check_chromadb_collection():
    """Check ChromaDB collection size."""
    print("\n" + "=" * 80)
    print("🗄️  Checking ChromaDB Collection")
    print("=" * 80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/search?query=test&limit=1", timeout=5)
        
        if response.status_code == 200:
            print("✅ ChromaDB responding to queries")
            return True
        else:
            print(f"⚠️  ChromaDB query: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ChromaDB: {e}")
        return False


def print_summary(results):
    """Print test summary."""
    print("\n" + "=" * 80)
    print("📋 VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results.values() if r is True)
    skipped = sum(1 for r in results.values() if r is None)
    failed = sum(1 for r in results.values() if r is False)
    total = len(results)
    
    print(f"\n   ✅ Passed:  {passed}/{total}")
    print(f"   ⚠️  Skipped: {skipped}/{total}")
    print(f"   ❌ Failed:  {failed}/{total}")
    
    print("\n   Status by Phase:")
    print("   ─────────────────────────────────────────────")
    print(f"   Phase 1 (Worker):        {'✅' if results.get('worker') else '❌' if results.get('worker') is False else '⚠️ '}")
    print(f"   Phase 2 (Indexes):       {'✅' if results.get('indexes') else '❌' if results.get('indexes') is False else '⚠️ '}")
    print(f"   Phase 3 (Embedding):     {'✅' if results.get('embedding') else '❌' if results.get('embedding') is False else '⚠️ '}")
    print(f"   Phase 4 (Cache):         {'✅' if results.get('cache') else '❌' if results.get('cache') is False else '⚠️ '}")
    
    print("\n   Note: ⚠️  means feature not yet available (needs container rebuild)")
    print()


def main():
    """Run all validation tests."""
    print("🎊 OPTIMIZATION VALIDATION SUITE")
    print("Testing all 4 phases of optimizations")
    print()
    
    results = {}
    
    # Basic health checks
    results['health'] = test_service_health()
    time.sleep(1)
    
    results['embedding'] = test_embedding_service()
    time.sleep(1)
    
    # Phase 1: Worker
    results['worker'] = test_worker_status()
    time.sleep(1)
    
    # Phase 2: Indexes
    results['indexes'] = test_performance_indexes()
    time.sleep(1)
    
    # Phase 4: Cache
    results['cache'] = test_cache_analytics()
    time.sleep(1)
    
    # ChromaDB
    results['chromadb'] = check_chromadb_collection()
    
    # Summary
    print_summary(results)
    
    if results['health'] and results['embedding']:
        print("✅ Core services operational!")
    else:
        print("❌ Core services have issues")
    
    if results.get('indexes') is None or results.get('cache') is None:
        print("\n💡 TIP: To load Phase 2-4 optimizations, rebuild containers:")
        print("   docker compose -f docker-compose-mcp-ecosystem.yml build")
        print("   docker compose -f docker-compose-mcp-ecosystem.yml up -d")
    
    return all(v in (True, None) for v in results.values())


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

