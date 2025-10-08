#!/usr/bin/env python3
"""Audit all data store services for routing and connectivity issues."""

import requests
import json

services = [
    {"name": "doc_store", "port": 5087, "status": "✅ FIXED"},
    {"name": "prompt_store", "port": 5110, "status": "🔍 CHECKING"},
    {"name": "external-service-store", "port": 5140, "status": "🔍 CHECKING"},
    {"name": "memory-agent", "port": 5090, "status": "🔍 CHECKING"}
]

print("╔══════════════════════════════════════════════════════════════════════════════╗")
print("║                                                                              ║")
print("║               🔍 DATA STORE SERVICES COMPREHENSIVE AUDIT                     ║")
print("║                                                                              ║")
print("╚══════════════════════════════════════════════════════════════════════════════╝")
print()

results = []

for service in services:
    name = service["name"]
    port = service["port"]
    
    print(f"📊 {name.upper()} (Port {port})")
    print(f"   Initial Status: {service['status']}")
    
    result = {
        "name": name,
        "port": port,
        "health": "❌",
        "endpoints": 0,
        "has_create_endpoint": False,
        "has_list_endpoint": False,
        "issues": []
    }
    
    try:
        # Health check
        health_resp = requests.get(f"http://localhost:{port}/health", timeout=2)
        if health_resp.status_code == 200:
            result["health"] = "✅"
            print(f"   Health: ✅ Healthy")
        else:
            result["health"] = "⚠️"
            print(f"   Health: ⚠️ Status {health_resp.status_code}")
    except Exception as e:
        result["issues"].append(f"Health check failed: {str(e)}")
        print(f"   Health: ❌ Not responding")
    
    try:
        # OpenAPI check
        openapi_resp = requests.get(f"http://localhost:{port}/openapi.json", timeout=2)
        if openapi_resp.status_code == 200:
            openapi_data = openapi_resp.json()
            paths = openapi_data.get("paths", {})
            result["endpoints"] = len(paths)
            
            print(f"   Endpoints: {len(paths)} total")
            
            # Check for CRUD operations
            for path in paths.keys():
                if any(keyword in path.lower() for keyword in ["create", "post", "/api/v1/prompts", "/api/v1/documents", "/api/v1/services", "/api/v1/contexts"]):
                    if "post" in openapi_data["paths"][path]:
                        result["has_create_endpoint"] = True
                        
                if any(keyword in path.lower() for keyword in ["list", "get", "/prompts", "/documents", "/services", "/contexts"]):
                    if "get" in openapi_data["paths"][path]:
                        result["has_list_endpoint"] = True
            
            # Show sample endpoints
            sample_paths = list(paths.keys())[:5]
            print(f"   Sample Endpoints:")
            for p in sample_paths:
                print(f"     • {p}")
            
            # Check for potential issues
            if len(paths) < 5:
                result["issues"].append(f"Very few endpoints ({len(paths)})")
                print(f"   ⚠️  Warning: Only {len(paths)} endpoints (may have import issues)")
            
            if not result["has_create_endpoint"]:
                result["issues"].append("No create endpoint found")
                print(f"   ⚠️  Warning: No create/POST endpoint detected")
            
        else:
            result["issues"].append(f"OpenAPI returned {openapi_resp.status_code}")
            print(f"   OpenAPI: ⚠️ Status {openapi_resp.status_code}")
    except Exception as e:
        result["issues"].append(f"OpenAPI check failed: {str(e)}")
        print(f"   OpenAPI: ❌ Failed ({str(e)[:50]})")
    
    results.append(result)
    print()

# Summary
print("╔══════════════════════════════════════════════════════════════════════════════╗")
print("║                         📊 AUDIT SUMMARY                                     ║")
print("╚══════════════════════════════════════════════════════════════════════════════╝")
print()

healthy_count = sum(1 for r in results if r["health"] == "✅")
print(f"✅ Healthy Services: {healthy_count}/{len(results)}")
print()

print("| Service | Health | Endpoints | Create | List | Issues |")
print("|---------|--------|-----------|--------|------|--------|")
for r in results:
    create_status = "✅" if r["has_create_endpoint"] else "❌"
    list_status = "✅" if r["has_list_endpoint"] else "❌"
    issues_count = len(r["issues"])
    issues_str = f"{issues_count} issue(s)" if issues_count > 0 else "None"
    
    print(f"| {r['name']:19s} | {r['health']} | {r['endpoints']:9d} | {create_status} | {list_status} | {issues_str} |")

print()
print("=" * 80)
print()

# Recommendations
print("🎯 RECOMMENDATIONS:")
print()

for r in results:
    if r["issues"]:
        print(f"⚠️  {r['name']}:")
        for issue in r["issues"]:
            print(f"   • {issue}")
        print()

print("=" * 80)

