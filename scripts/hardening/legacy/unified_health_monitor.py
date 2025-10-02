#!/usr/bin/env python3
"""
Unified Health Monitor for Hackathon Ecosystem

This script checks the health status of all services in the ecosystem
by making HTTP requests to their health endpoints.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, List, Tuple
import time

# Service health endpoints mapping
SERVICES = {
    "redis": {"port": 6379, "health_check": "ping", "protocol": "tcp"},
    "discovery-agent": {"port": 5045, "endpoint": "/health"},
    "doc_store": {"port": 5087, "endpoint": "/health"},
    "llm-gateway": {"port": 5055, "endpoint": "/health"},
    "code-analyzer": {"port": 5025, "endpoint": "/health"},
    "secure-analyzer": {"port": 5100, "endpoint": "/health"},
    "analysis-service": {"port": 5080, "endpoint": "/health"},
    "summarizer-hub": {"port": 5160, "endpoint": "/health"},
    "source-agent": {"port": 5085, "endpoint": "/health"},
    "memory-agent": {"port": 5090, "endpoint": "/health"},
    "prompt_store": {"port": 5110, "endpoint": "/health"},
    "log-collector": {"port": 5040, "endpoint": "/health"},
    "notification-service": {"port": 5130, "endpoint": "/health"},
    "mock-data-generator": {"port": 5065, "endpoint": "/health"},
    "project-simulation": {"port": 5075, "endpoint": "/health"},
    "orchestrator": {"port": 5099, "endpoint": "/health"},
    "architecture-digitizer": {"port": 5105, "endpoint": "/health"},
    "interpreter": {"port": 5120, "endpoint": "/health"},
    "frontend": {"port": 3000, "endpoint": "/health"},
    "unified-api-dashboard": {"port": 8000, "endpoint": "/health"},
    # Streamlit apps (different health check approach)
    "simulation-dashboard": {"port": 8501, "endpoint": "/", "streamlit": True},
    "data-services-dashboard": {"port": 8502, "endpoint": "/", "streamlit": True},
}

async def check_service_health(service_name: str, config: dict, session: aiohttp.ClientSession) -> Tuple[str, Dict]:
    """Check health of a single service."""
    try:
        port = config["port"]
        url = f"http://localhost:{port}{config.get('endpoint', '/health')}"

        # Special handling for streamlit apps
        if config.get("streamlit"):
            timeout = aiohttp.ClientTimeout(total=5, connect=2)
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    return service_name, {
                        "status": "healthy",
                        "port": port,
                        "response_time": None,
                        "details": f"Streamlit app responding on port {port}"
                    }
                else:
                    return service_name, {
                        "status": "unhealthy",
                        "port": port,
                        "error": f"HTTP {response.status}",
                        "details": f"Streamlit app not responding properly"
                    }
        else:
            # Regular API health check
            start_time = time.time()
            timeout = aiohttp.ClientTimeout(total=10, connect=3)
            async with session.get(url, timeout=timeout) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    try:
                        data = await response.json()
                        return service_name, {
                            "status": "healthy",
                            "port": port,
                            "response_time": round(response_time * 1000, 2),  # ms
                            "details": data.get("status", "OK")
                        }
                    except:
                        return service_name, {
                            "status": "healthy",
                            "port": port,
                            "response_time": round(response_time * 1000, 2),
                            "details": "Service responding (no JSON response)"
                        }
                else:
                    return service_name, {
                        "status": "unhealthy",
                        "port": port,
                        "error": f"HTTP {response.status}",
                        "response_time": round(response_time * 1000, 2),
                        "details": f"Service returned non-200 status"
                    }

    except aiohttp.ClientConnectorError:
        return service_name, {
            "status": "unhealthy",
            "port": port,
            "error": "Connection refused",
            "details": "Service not running or not accessible"
        }
    except asyncio.TimeoutError:
        return service_name, {
            "status": "unhealthy",
            "port": port,
            "error": "Timeout",
            "details": "Service took too long to respond"
        }
    except Exception as e:
        return service_name, {
            "status": "error",
            "port": port,
            "error": str(e),
            "details": f"Unexpected error: {str(e)}"
        }

async def check_redis_health() -> Tuple[str, Dict]:
    """Check Redis health using redis-cli if available."""
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "exec", "hackathon-redis-1", "redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and "PONG" in result.stdout:
            return "redis", {
                "status": "healthy",
                "port": 6379,
                "details": "Redis responding to PING"
            }
        else:
            return "redis", {
                "status": "unhealthy",
                "port": 6379,
                "error": "PING failed",
                "details": result.stdout.strip() or result.stderr.strip()
            }
    except Exception as e:
        return "redis", {
            "status": "error",
            "port": 6379,
            "error": str(e),
            "details": "Could not check Redis health"
        }

async def main():
    """Main health monitoring function."""
    print("🔍 Unified Health Monitor - Hackathon Ecosystem")
    print("=" * 50)

    connector = aiohttp.TCPConnector(limit=20)
    timeout = aiohttp.ClientTimeout(total=10, connect=3)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Check Redis separately
        print("📊 Checking Redis...")
        redis_result = await check_redis_health()
        results = [redis_result]

        # Check all HTTP services concurrently
        print("🌐 Checking HTTP services...")
        tasks = []
        for service_name, config in SERVICES.items():
            if service_name != "redis":
                tasks.append(check_service_health(service_name, config, session))

        http_results = await asyncio.gather(*tasks, return_exceptions=True)
        results.extend(http_results)

    # Process results
    healthy = []
    unhealthy = []
    errors = []

    print("\n📋 Health Check Results:")
    print("-" * 50)

    for service_name, result in results:
        status = result.get("status", "unknown")
        port = result.get("port", "N/A")

        if status == "healthy":
            healthy.append(service_name)
            response_time = result.get("response_time")
            time_str = f" ({response_time}ms)" if response_time else ""
            print(f"✅ {service_name:<25} [Port {port}] {time_str}")
        elif status == "unhealthy":
            unhealthy.append(service_name)
            error = result.get("error", "Unknown")
            print(f"❌ {service_name:<25} [Port {port}] - {error}")
        else:
            errors.append(service_name)
            error = result.get("error", "Unknown")
            print(f"⚠️  {service_name:<25} [Port {port}] - ERROR: {error}")

    # Summary
    total = len(results)
    healthy_count = len(healthy)
    unhealthy_count = len(unhealthy)
    error_count = len(errors)

    print("\n📊 Summary:")
    print(f"   Total Services: {total}")
    print(f"   Healthy: {healthy_count}")
    print(f"   Unhealthy: {unhealthy_count}")
    print(f"   Errors: {error_count}")

    success_rate = (healthy_count / total) * 100 if total > 0 else 0
    print(".1f")

    # Exit codes
    if unhealthy_count > 0 or error_count > 0:
        print("\n❌ Some services are not healthy!")
        sys.exit(1)
    else:
        print("\n✅ All services are healthy!")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
