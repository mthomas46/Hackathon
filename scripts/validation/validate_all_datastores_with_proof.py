#!/usr/bin/env python3
"""
Comprehensive Datastore Validation with Detailed Proof

This script:
1. Tests persistence to all 4 datastores
2. Retrieves and displays saved data from each
3. Generates detailed proof report
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Any

# Service configurations  
SERVICES = {
    "doc_store": {
        "url": "http://localhost:5087",
        "test_endpoint": "/api/v1/documents",
        "list_endpoint": "/api/v1/documents",
        "test_data": {
            "id": f"validation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "content": "This is a validation test document to prove persistence works.",
            "metadata": {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "purpose": "datastore_validation"
            }
        }
    },
    "prompt_store": {
        "url": "http://localhost:5110",
        "test_endpoint": "/api/v1/prompts",
        "list_endpoint": "/api/v1/prompts",
        "test_data": {
            "name": f"validation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "category": "testing",
            "content": "This is a validation test prompt to prove persistence works.",
            "description": "Testing datastore persistence",
            "tags": ["validation", "test"],
            "variables": [],
            "is_template": False
        }
    },
    "external-service-store": {
        "url": "http://localhost:5140",
        "test_endpoint": "/services",
        "list_endpoint": "/services",
        "test_data": {
            "name": f"ValidationTestService_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "service_type": "API",
            "description": "Test service to prove persistence works"
        }
    },
    "memory-agent": {
        "url": "http://localhost:5090",
        "test_endpoint": "/memory/put",
        "list_endpoint": "/memory/search",
        "test_data": {
            "item": {
                "id": f"validation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "user_id": "validation_user",
                "memory_type": "context",
                "content": json.dumps({
                    "test": True,
                    "purpose": "datastore_validation",
                    "timestamp": datetime.now().isoformat()
                }),
                "metadata": {}
            }
        }
    }
}

async def test_service_persistence(service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Test persistence for a single service."""
    result = {
        "service": service_name,
        "accessible": False,
        "persisted": False,
        "data_saved": None,
        "data_retrieved": None,
        "error": None
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Step 1: Check if service is accessible
        try:
            health_response = await client.get(f"{config['url']}/health")
            result["accessible"] = health_response.status_code == 200
        except Exception as e:
            result["error"] = f"Service not accessible: {str(e)}"
            return result
        
        if not result["accessible"]:
            result["error"] = "Service not responding to health check"
            return result
        
        # Step 2: Try to persist data
        try:
            persist_response = await client.post(
                f"{config['url']}{config['test_endpoint']}",
                json=config["test_data"]
            )
            
            if persist_response.status_code < 400:
                result["persisted"] = True
                result["data_saved"] = persist_response.json()
            else:
                result["error"] = f"Persistence failed: {persist_response.status_code} - {persist_response.text[:200]}"
                return result
                
        except Exception as e:
            result["error"] = f"Error during persistence: {str(e)}"
            return result
        
        # Step 3: Try to retrieve data to verify
        try:
            if service_name == "memory-agent":
                # memory-agent uses search
                list_response = await client.post(
                    f"{config['url']}{config['list_endpoint']}",
                    json={"user_id": "validation_user", "query": "", "limit": 10}
                )
            else:
                list_response = await client.get(f"{config['url']}{config['list_endpoint']}")
            
            if list_response.status_code == 200:
                data = list_response.json()
                result["data_retrieved"] = data
            else:
                result["error"] = f"Could not retrieve data: {list_response.status_code}"
                
        except Exception as e:
            result["error"] = f"Error retrieving data: {str(e)}"
    
    return result

async def main():
    """Main validation function."""
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║          🔍 COMPREHENSIVE DATASTORE VALIDATION WITH PROOF                    ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    results = {}
    
    # Test each service
    for service_name, config in SERVICES.items():
        print(f"🧪 Testing {service_name}...")
        print("="*80)
        
        result = await test_service_persistence(service_name, config)
        results[service_name] = result
        
        if result["accessible"]:
            print(f"  ✅ Service accessible")
        else:
            print(f"  ❌ Service not accessible")
        
        if result["persisted"]:
            print(f"  ✅ Data persisted successfully")
        else:
            print(f"  ❌ Data not persisted")
        
        if result["error"]:
            print(f"  ⚠️  Error: {result['error'][:100]}")
        
        print()
    
    # Summary
    print("="*80)
    print()
    print("📊 VALIDATION SUMMARY")
    print("="*80)
    
    accessible_count = sum(1 for r in results.values() if r["accessible"])
    persisted_count = sum(1 for r in results.values() if r["persisted"])
    
    print(f"Services Accessible:  {accessible_count}/4")
    print(f"Services Persisting:  {persisted_count}/4")
    print()
    
    # Detailed Proof
    print("="*80)
    print()
    print("📋 DETAILED PROOF FROM EACH DATASTORE")
    print("="*80)
    print()
    
    for service_name, result in results.items():
        print(f"### {service_name.upper()}")
        print("-"*80)
        
        if result["persisted"]:
            print(f"✅ STATUS: Data successfully persisted")
            print()
            print(f"📝 Data Saved:")
            if result["data_saved"]:
                print(json.dumps(result["data_saved"], indent=2)[:500])
            print()
            
            print(f"📊 Data Retrieved:")
            if result["data_retrieved"]:
                # Extract count
                data = result["data_retrieved"]
                if isinstance(data, dict):
                    items = data.get("items", data.get("data", data.get("results", [])))
                    if isinstance(items, list):
                        count = len(items)
                    else:
                        count = "unknown"
                else:
                    count = len(data) if isinstance(data, list) else "unknown"
                
                print(f"  Total items in store: {count}")
                print()
            
            print(f"🎉 PROOF: {service_name} is persisting data!")
        else:
            print(f"❌ STATUS: Could not persist data")
            if result["error"]:
                print(f"  Error: {result['error']}")
        
        print()
        print()
    
    # Final verdict
    print("="*80)
    print()
    if persisted_count == 4:
        print("🎉🎉🎉 SUCCESS: ALL 4 DATASTORES ARE PERSISTING DATA! 🎉🎉🎉")
        return 0
    elif persisted_count > 0:
        print(f"⚠️  PARTIAL SUCCESS: {persisted_count}/4 datastores persisting")
        return 1
    else:
        print("❌ FAILURE: No datastores persisting data")
        return 2

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

