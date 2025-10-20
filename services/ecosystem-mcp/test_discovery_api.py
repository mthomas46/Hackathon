#!/usr/bin/env python3
"""
Test Discovery API endpoints.

Tests:
1. POST /api/v1/discovery/scan - Scan repository
2. GET /api/v1/discovery/plans - List processing plans
3. GET /api/v1/discovery/plans/{id} - Get plan details
"""

import asyncio
import sys
import httpx
from pathlib import Path


async def main():
    """Test discovery API."""
    print("=" * 80)
    print("🧪 TESTING DISCOVERY API")
    print("=" * 80)
    print()
    
    # API base URL
    base_url = "http://localhost:8000"
    
    # Test repository path (use src/services directory)
    test_repo = str(Path(__file__).parent / "src" / "services")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test 1: Health check
            print("1️⃣  Testing health endpoint...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print(f"   ✅ Health check passed: {response.json()}")
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return 1
            print()
            
            # Test 2: Scan repository
            print("2️⃣  Testing POST /api/v1/discovery/scan...")
            scan_request = {
                "repo_path": test_repo,
                "resolve_host_path": False,
                "save_to_db": True
            }
            response = await client.post(
                f"{base_url}/api/v1/discovery/scan",
                json=scan_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Scan successful!")
                print(f"   📊 Plan ID: {data['plan_id']}")
                print(f"   📄 Total Files: {data['summary']['total_files']}")
                print(f"   💾 Total Size: {data['summary']['total_size_mb']:.2f} MB")
                print(f"   📦 Sub-Jobs: {data['summary']['sub_jobs']}")
                print(f"   ⏱️  Estimated Time: {data['summary']['estimated_time_minutes']:.1f} minutes")
                print(f"   💾 Saved to DB: {data['saved_to_db']}")
                
                plan_id = data['plan_id']
            else:
                print(f"   ❌ Scan failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return 1
            print()
            
            # Test 3: List processing plans
            print("3️⃣  Testing GET /api/v1/discovery/plans...")
            response = await client.get(f"{base_url}/api/v1/discovery/plans")
            
            if response.status_code == 200:
                plans = response.json()
                print(f"   ✅ Found {len(plans)} processing plans")
                for plan in plans[:3]:  # Show first 3
                    print(f"   - {plan['id'][:8]}... | {plan['repo_path']} | {plan['total_files']} files")
            else:
                print(f"   ❌ List plans failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return 1
            print()
            
            # Test 4: Get plan details
            print("4️⃣  Testing GET /api/v1/discovery/plans/{id}...")
            response = await client.get(f"{base_url}/api/v1/discovery/plans/{plan_id}")
            
            if response.status_code == 200:
                plan = response.json()
                print(f"   ✅ Plan details retrieved")
                print(f"   📊 Total Files: {plan['total_files']}")
                print(f"   📦 Sub-Jobs: {len(plan['sub_jobs'])}")
                print()
                print(f"   Sub-Job Details:")
                for sj in plan['sub_jobs']:
                    print(f"     - {sj['sub_job_id']:20s} | {sj['file_count']:4d} files | Priority {sj['priority']}")
            else:
                print(f"   ❌ Get plan details failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return 1
            print()
            
            print("=" * 80)
            print("✅ ALL API TESTS PASSED!")
            print("=" * 80)
            
            return 0
            
        except httpx.ConnectError:
            print()
            print("=" * 80)
            print("❌ CONNECTION ERROR!")
            print("=" * 80)
            print()
            print("Could not connect to API at:", base_url)
            print()
            print("Make sure the service is running:")
            print("  cd services/ecosystem-mcp")
            print("  python -m src.api.main")
            print()
            return 1
            
        except Exception as e:
            print()
            print("=" * 80)
            print("❌ TEST FAILED!")
            print("=" * 80)
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

