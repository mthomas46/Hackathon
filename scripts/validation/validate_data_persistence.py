#!/usr/bin/env python3
"""
Data Persistence Validation Script

This script validates that documents are actually being persisted to the
datastore services when the demo is executed.

Usage:
    python3 validate_data_persistence.py
"""

import httpx
import asyncio
from datetime import datetime
import json

# Service configurations
SERVICES = {
    "doc_store": {
        "url": "http://localhost:5087",
        "endpoints": {
            "create": "/api/v1/documents",
            "list": "/api/v1/documents",
            "count": "/api/v1/documents"
        }
    },
    "prompt_store": {
        "url": "http://localhost:5110",
        "endpoints": {
            "create": "/api/v1/prompts",
            "list": "/api/v1/prompts",
            "count": "/api/v1/prompts"
        }
    },
    "external-service-store": {
        "url": "http://localhost:5140",
        "endpoints": {
            "create": "/api/v1/services",
            "list": "/api/v1/services",
            "count": "/api/v1/services"
        }
    },
    "memory-agent": {
        "url": "http://localhost:5090",
        "endpoints": {
            "create": "/api/v1/memories",
            "list": "/api/v1/memories",
            "count": "/api/v1/memories"
        }
    }
}

async def get_current_counts():
    """Get current document counts from all services."""
    counts = {}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for service_name, config in SERVICES.items():
            try:
                # Try to get list endpoint to count
                response = await client.get(f"{config['url']}{config['endpoints']['list']}")
                
                if response.status_code == 200:
                    data = response.json()
                    # Different services have different response formats
                    if isinstance(data, list):
                        count = len(data)
                    elif isinstance(data, dict):
                        count = len(data.get('items', data.get('data', data.get('documents', data.get('prompts', data.get('services', data.get('memories', [])))))))
                    else:
                        count = 0
                    
                    counts[service_name] = {
                        "status": "✅ accessible",
                        "count": count,
                        "endpoint": config['endpoints']['list']
                    }
                else:
                    counts[service_name] = {
                        "status": f"⚠️ HTTP {response.status_code}",
                        "count": 0,
                        "endpoint": config['endpoints']['list']
                    }
                    
            except Exception as e:
                counts[service_name] = {
                    "status": f"❌ {type(e).__name__}",
                    "count": 0,
                    "error": str(e)
                }
    
    return counts

async def test_persistence():
    """Test if we can persist data to each service."""
    test_results = {}
    timestamp = datetime.now().isoformat()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test doc_store
        try:
            doc_payload = {
                "id": f"test_validation_{timestamp}",
                "content": "Test document for persistence validation",
                "metadata": {"source": "validation_script", "timestamp": timestamp}
            }
            response = await client.post(
                f"{SERVICES['doc_store']['url']}{SERVICES['doc_store']['endpoints']['create']}",
                json=doc_payload
            )
            test_results['doc_store'] = {
                "attempted": True,
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "response": response.text[:200]
            }
        except Exception as e:
            test_results['doc_store'] = {
                "attempted": True,
                "error": str(e),
                "success": False
            }
        
        # Test prompt_store
        try:
            prompt_payload = {
                "name": f"test_prompt_{timestamp}",
                "content": "Test prompt for persistence validation",
                "category": "validation"
            }
            response = await client.post(
                f"{SERVICES['prompt_store']['url']}{SERVICES['prompt_store']['endpoints']['create']}",
                json=prompt_payload
            )
            test_results['prompt_store'] = {
                "attempted": True,
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "response": response.text[:200]
            }
        except Exception as e:
            test_results['prompt_store'] = {
                "attempted": True,
                "error": str(e),
                "success": False
            }
        
        # Test external-service-store
        try:
            service_payload = {
                "name": f"test_service_{timestamp}",
                "service_type": "API",
                "description": "Test service for persistence validation"
            }
            response = await client.post(
                f"{SERVICES['external-service-store']['url']}{SERVICES['external-service-store']['endpoints']['create']}",
                json=service_payload
            )
            test_results['external-service-store'] = {
                "attempted": True,
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "response": response.text[:200]
            }
        except Exception as e:
            test_results['external-service-store'] = {
                "attempted": True,
                "error": str(e),
                "success": False
            }
        
        # Test memory-agent
        try:
            memory_payload = {
                "id": f"test_memory_{timestamp}",
                "user_id": "validation_user",
                "memory_type": "context",
                "content": json.dumps({"test": "data", "timestamp": timestamp})
            }
            response = await client.post(
                f"{SERVICES['memory-agent']['url']}{SERVICES['memory-agent']['endpoints']['create']}",
                json=memory_payload
            )
            test_results['memory-agent'] = {
                "attempted": True,
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "response": response.text[:200]
            }
        except Exception as e:
            test_results['memory-agent'] = {
                "attempted": True,
                "error": str(e),
                "success": False
            }
    
    return test_results

async def main():
    """Main validation function."""
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                          ║")
    print("║             📊 DATA PERSISTENCE VALIDATION                               ║")
    print("║                                                                          ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Step 1: Get current counts
    print("📊 STEP 1: Getting current document counts...")
    print("="*80)
    counts_before = await get_current_counts()
    
    for service, data in counts_before.items():
        status_icon = "✅" if data['count'] > 0 or data['status'] == "✅ accessible" else "⚠️"
        print(f"{status_icon} {service:30} Count: {data['count']:4}  Status: {data['status']}")
    
    print()
    print("="*80)
    print()
    
    # Step 2: Test persistence
    print("🧪 STEP 2: Testing data persistence...")
    print("="*80)
    test_results = await test_persistence()
    
    for service, result in test_results.items():
        if result['success']:
            print(f"✅ {service:30} Status: {result['status_code']} - Persisted successfully")
        else:
            print(f"❌ {service:30} Status: {result.get('status_code', 'N/A')} - Failed")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            else:
                print(f"   Response: {result.get('response', 'N/A')}")
    
    print()
    print("="*80)
    print()
    
    # Step 3: Verify counts increased
    print("🔍 STEP 3: Verifying document counts increased...")
    print("="*80)
    
    await asyncio.sleep(1)  # Give services time to persist
    counts_after = await get_current_counts()
    
    persistence_verified = {}
    for service in SERVICES.keys():
        before = counts_before.get(service, {}).get('count', 0)
        after = counts_after.get(service, {}).get('count', 0)
        increased = after > before
        
        persistence_verified[service] = {
            "before": before,
            "after": after,
            "increased": increased,
            "delta": after - before
        }
        
        if increased:
            print(f"✅ {service:30} Before: {before:4} → After: {after:4} (+{after-before})")
        else:
            print(f"⚠️  {service:30} Before: {before:4} → After: {after:4} (no change)")
    
    print()
    print("="*80)
    print()
    
    # Summary
    print("📋 SUMMARY")
    print("="*80)
    
    accessible_count = sum(1 for s in counts_before.values() if "accessible" in s['status'])
    persisted_count = sum(1 for r in test_results.values() if r['success'])
    verified_count = sum(1 for v in persistence_verified.values() if v['increased'])
    
    print(f"Services Accessible:     {accessible_count}/4")
    print(f"Data Persisted:          {persisted_count}/4")
    print(f"Persistence Verified:    {verified_count}/4")
    print()
    
    if verified_count == 4:
        print("🎉 SUCCESS: All services are persisting data correctly!")
    elif verified_count > 0:
        print("⚠️  PARTIAL: Some services are persisting data")
    else:
        print("❌ FAILED: No services are persisting data")
    
    print()
    print("="*80)
    
    # Data Flow Validation
    print()
    print("📊 DATA FLOW VALIDATION (Section 7.1)")
    print("="*80)
    print()
    print("The 'Complete Ecosystem Data Flow' diagram in section 7.1 shows:")
    print("  • Demo Data Generator → doc_store (documents)")
    print("  • Demo Data Generator → prompt_store (prompts)")
    print("  • Service Discovery → external-service-store (services)")
    print("  • Workflow Execution → memory-agent (contexts)")
    print()
    
    if verified_count == 4:
        print("✅ VALIDATED: Data flow is accurate - all stores are persisting")
    elif verified_count > 0:
        print("⚠️  PARTIALLY VALIDATED: Some stores are persisting")
        print()
        print("Not persisting:")
        for service, data in persistence_verified.items():
            if not data['increased']:
                print(f"  ❌ {service}")
    else:
        print("❌ NOT VALIDATED: Data flow diagram shows intended design,")
        print("   but no actual persistence is occurring")
    
    print()
    print("="*80)
    
    return {
        "accessible": accessible_count,
        "persisted": persisted_count,
        "verified": verified_count,
        "details": {
            "counts_before": counts_before,
            "test_results": test_results,
            "counts_after": counts_after,
            "persistence_verified": persistence_verified
        }
    }

if __name__ == "__main__":
    result = asyncio.run(main())

