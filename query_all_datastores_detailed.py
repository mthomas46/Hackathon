#!/usr/bin/env python3
"""
Query All Datastores - Detailed Proof Script

Queries each datastore and shows exactly what data is persisted.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

async def query_prompt_store():
    """Query prompt_store for all prompts."""
    print("═"*80)
    print("1. PROMPT_STORE - Port 5110")
    print("═"*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Try to get list of prompts
            response = await client.get("http://localhost:5110/api/v1/prompts")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if data.get("success"):
                    items = data.get("data", {}).get("items", [])
                else:
                    items = []
                
                print(f"✅ Service responding: HTTP {response.status_code}")
                print(f"📊 TOTAL PROMPTS: {len(items)}")
                print()
                
                if items:
                    print("📝 ALL PROMPTS SAVED:")
                    print()
                    for idx, prompt in enumerate(items, 1):
                        print(f"  {idx}. Name: {prompt.get('name', 'N/A')}")
                        print(f"     Category: {prompt.get('category', 'N/A')}")
                        print(f"     ID: {prompt.get('id', 'N/A')}")
                        print(f"     Tags: {', '.join(prompt.get('tags', []))}")
                        print()
                    
                    print(f"🎉🎉🎉 PROOF: {len(items)} prompts successfully persisted! 🎉🎉🎉")
                else:
                    print("⚠️  No prompts found")
                    print("📄 Raw response:")
                    print(json.dumps(data, indent=2)[:500])
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print()

async def query_doc_store():
    """Query doc_store for all documents."""
    print("═"*80)
    print("2. DOC_STORE - Port 5087")
    print("═"*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Check health first
            health_response = await client.get("http://localhost:5087/health")
            print(f"✅ Service healthy: HTTP {health_response.status_code}")
            
            # Try to list documents - may need different endpoint
            response = await client.get("http://localhost:5087/api/v1/documents")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Response type: {type(data)}")
                print(f"📄 Raw response preview:")
                print(json.dumps(data, indent=2)[:500])
            else:
                print(f"⚠️  GET /api/v1/documents returned: HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
                # Try alternative endpoints
                print()
                print("🔍 Trying alternative endpoints...")
                for endpoint in ["/documents", "/api/documents", "/docs"]:
                    try:
                        alt_response = await client.get(f"http://localhost:5087{endpoint}")
                        if alt_response.status_code < 400:
                            print(f"  ✅ Found: {endpoint} - HTTP {alt_response.status_code}")
                            break
                    except:
                        pass
                else:
                    print("  ❌ No alternative endpoints found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print()

async def query_external_service_store():
    """Query external-service-store for all services."""
    print("═"*80)
    print("3. EXTERNAL-SERVICE-STORE - Port 5140")
    print("═"*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get("http://localhost:5140/services")
            
            if response.status_code == 200:
                data = response.json()
                items = data if isinstance(data, list) else data.get("services", [])
                
                print(f"✅ Service responding: HTTP {response.status_code}")
                print(f"📊 TOTAL SERVICES: {len(items) if isinstance(items, list) else 'unknown'}")
                
                if isinstance(items, list) and items:
                    print()
                    print("📝 ALL SERVICES SAVED:")
                    print()
                    for idx, service in enumerate(items, 1):
                        print(f"  {idx}. Name: {service.get('name', 'N/A')}")
                        print(f"     Type: {service.get('service_type', 'N/A')}")
                        print(f"     ID: {service.get('id', 'N/A')}")
                        print()
                    
                    print(f"🎉🎉🎉 PROOF: {len(items)} services successfully persisted! 🎉🎉🎉")
                else:
                    print("⚠️  No services found or unexpected format")
                    print(f"📄 Raw response preview:")
                    print(json.dumps(data, indent=2)[:500])
            else:
                print(f"❌ Service not responding: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Service not accessible: {e}")
    
    print()
    print()

async def query_memory_agent():
    """Query memory-agent for all contexts."""
    print("═"*80)
    print("4. MEMORY-AGENT - Port 5090")
    print("═"*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Check health first
            health_response = await client.get("http://localhost:5090/health")
            print(f"✅ Service healthy: HTTP {health_response.status_code}")
            
            # Try search endpoint
            response = await client.post(
                "http://localhost:5090/memory/search",
                json={"user_id": "demo_system", "query": "", "limit": 100}
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("results", data.get("items", []))
                
                print(f"📊 TOTAL CONTEXTS: {len(items) if isinstance(items, list) else 'unknown'}")
                
                if isinstance(items, list) and items:
                    print()
                    print("📝 ALL CONTEXTS SAVED:")
                    print()
                    for idx, item in enumerate(items, 1):
                        print(f"  {idx}. ID: {item.get('id', 'N/A')[:50]}")
                        print(f"     Type: {item.get('memory_type', 'N/A')}")
                        print()
                    
                    print(f"🎉🎉🎉 PROOF: {len(items)} contexts successfully persisted! 🎉🎉🎉")
                else:
                    print("⚠️  No contexts found")
                    print("📄 Raw response:")
                    print(json.dumps(data, indent=2)[:500])
            else:
                print(f"⚠️  Search endpoint returned: HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print()

async def main():
    """Main function."""
    print()
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║          🔍 DETAILED DATASTORE QUERY - SHOW ALL PERSISTED DATA               ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print()
    
    await query_prompt_store()
    await query_doc_store()
    await query_external_service_store()
    await query_memory_agent()
    
    print("="*80)
    print()
    print("✅ QUERY COMPLETE")
    print()

if __name__ == "__main__":
    asyncio.run(main())

