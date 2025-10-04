#!/usr/bin/env python3
"""
Check if required services are running for integration tests.

Usage:
    python3 tests/integration/check_services.py
"""

import httpx
import asyncio
from typing import Dict


# Service URLs
SERVICES = {
    "expert-finder": "http://localhost:5160",
    "user-store": "http://localhost:5150",
    "doc-store": "http://localhost:5087",
    "external-service-store": "http://localhost:5140",
    "log-collector": "http://localhost:8104"
}


async def check_service(name: str, url: str) -> Dict[str, any]:
    """Check if a service is running."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/health", timeout=2.0)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": name,
                    "url": url,
                    "status": "✅ RUNNING",
                    "version": data.get("version", "unknown"),
                    "healthy": True
                }
            else:
                return {
                    "name": name,
                    "url": url,
                    "status": f"⚠️ UNHEALTHY (HTTP {response.status_code})",
                    "healthy": False
                }
    except httpx.ConnectError:
        return {
            "name": name,
            "url": url,
            "status": "❌ NOT RUNNING",
            "healthy": False
        }
    except httpx.TimeoutException:
        return {
            "name": name,
            "url": url,
            "status": "⏱️ TIMEOUT",
            "healthy": False
        }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "status": f"❌ ERROR: {str(e)}",
            "healthy": False
        }


async def main():
    """Check all services and report status."""
    print("\n" + "=" * 80)
    print("CHECKING SERVICES FOR INTEGRATION TESTS")
    print("=" * 80 + "\n")
    
    tasks = [check_service(name, url) for name, url in SERVICES.items()]
    results = await asyncio.gather(*tasks)
    
    # Print results
    for result in results:
        name = result["name"].ljust(25)
        url = result["url"].ljust(35)
        status = result["status"]
        version = result.get("version", "")
        
        if version:
            print(f"{name} | {url} | {status} | v{version}")
        else:
            print(f"{name} | {url} | {status}")
    
    # Summary
    healthy_count = sum(1 for r in results if r["healthy"])
    total_count = len(results)
    
    print("\n" + "-" * 80)
    print(f"Services Running: {healthy_count}/{total_count}")
    print("-" * 80)
    
    # Required services for integration tests
    required_services = ["expert-finder", "user-store"]
    missing_required = [
        r["name"] for r in results 
        if r["name"] in required_services and not r["healthy"]
    ]
    
    if missing_required:
        print("\n⚠️  REQUIRED SERVICES NOT RUNNING:")
        for service in missing_required:
            print(f"   - {service}")
        print("\nIntegration tests will be skipped for missing services.")
        print("\nTo start services:")
        print("   docker-compose -f docker-compose.dev.yml up -d")
        print("   # Or for specific services:")
        print("   docker-compose -f docker-compose.dev.yml up -d expert-finder-service user-store")
        return 1
    else:
        print("\n✅ All required services are running!")
        print("\nYou can now run integration tests:")
        print("   pytest tests/integration/ -v -m integration")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

