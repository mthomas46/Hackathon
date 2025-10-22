"""
Test Script for Skip Review Feature

Tests documentation generation with and without review queue.
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"


async def test_skip_review():
    """Test skip_review parameter."""
    
    async with httpx.AsyncClient(timeout=60) as client:
        print("=" * 80)
        print("🧪 TESTING SKIP REVIEW FEATURE")
        print("=" * 80)
        
        # Step 1: Discovery scan
        print("\n🔍 Step 1: Discovery Scan...")
        resp1 = await client.post(
            f"{BASE_URL}/api/v1/discovery/scan",
            json={'repo_path': '/app', 'save_to_db': True}
        )
        
        if resp1.status_code != 200:
            print(f"❌ Discovery failed: {resp1.status_code}")
            return
        
        plan_id = resp1.json()['plan_id']
        print(f"✅ Plan ID: {plan_id}")
        
        # Step 2: Test WITH review (default behavior)
        print("\n" + "=" * 80)
        print("📝 TEST 1: Generate Documentation WITH Review Queue (default)")
        print("=" * 80)
        
        resp2 = await client.post(
            f"{BASE_URL}/api/v1/documentation/generate",
            json={
                'plan_id': plan_id,
                'repo_path': '/app',
                'passes': ['architecture'],
                'output_formats': ['markdown'],
                'skip_review': False  # Explicitly enable review (default)
            }
        )
        
        if resp2.status_code == 200:
            result1 = resp2.json()
            print(f"\n✅ Generation Result:")
            print(f"   Run ID: {result1.get('id')}")
            print(f"   Status: {result1.get('status')}")
            print(f"   Artifacts: {result1.get('total_artifacts', 0)}")
            print(f"   Quality: {result1.get('overall_quality_score', 0):.2f}/1.0")
        else:
            print(f"❌ Generation failed: {resp2.status_code}")
            print(f"   Error: {resp2.text}")
        
        # Step 3: Test WITHOUT review (skip_review=True)
        print("\n" + "=" * 80)
        print("📝 TEST 2: Generate Documentation WITHOUT Review Queue")
        print("=" * 80)
        
        # Need a new discovery scan for second test
        resp3 = await client.post(
            f"{BASE_URL}/api/v1/discovery/scan",
            json={'repo_path': '/app', 'save_to_db': True}
        )
        plan_id2 = resp3.json()['plan_id']
        
        resp4 = await client.post(
            f"{BASE_URL}/api/v1/documentation/generate",
            json={
                'plan_id': plan_id2,
                'repo_path': '/app',
                'passes': ['architecture'],
                'output_formats': ['markdown'],
                'skip_review': True  # Disable review queue
            }
        )
        
        if resp4.status_code == 200:
            result2 = resp4.json()
            print(f"\n✅ Generation Result:")
            print(f"   Run ID: {result2.get('id')}")
            print(f"   Status: {result2.get('status')}")
            print(f"   Artifacts: {result2.get('total_artifacts', 0)}")
            print(f"   Quality: {result2.get('overall_quality_score', 0):.2f}/1.0")
        else:
            print(f"❌ Generation failed: {resp4.status_code}")
            print(f"   Error: {resp4.text}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPARISON")
        print("=" * 80)
        
        if resp2.status_code == 200 and resp4.status_code == 200:
            print("\n✅ Both tests completed successfully!")
            print("\n📋 Test 1 (WITH review):")
            print(f"   - Artifacts generated: {result1.get('total_artifacts', 0)}")
            print(f"   - Check logs for: '📋 Queued for review'")
            
            print("\n⏭️  Test 2 (WITHOUT review):")
            print(f"   - Artifacts generated: {result2.get('total_artifacts', 0)}")
            print(f"   - Check logs for: '⏭️  Skipped review queue'")
            
            print("\n💡 TIP: Check Docker logs to see the difference:")
            print("   docker logs ecosystem-mcp-service 2>&1 | grep -E 'Queued for review|Skipped review'")
        else:
            print("\n⚠️  Some tests failed - check output above")


if __name__ == "__main__":
    asyncio.run(test_skip_review())

