#!/usr/bin/env python3
"""Quick service health check"""
import requests
import sys

services = {
    "doc_store": 5087,
    "prompt_store": 5110,
    "external-service-store": 5140,
    "memory-agent": 5090
}

print("🔍 Checking service health...\n")
all_healthy = True

for name, port in services.items():
    try:
        resp = requests.get(f"http://localhost:{port}/health", timeout=2)
        if resp.status_code == 200:
            print(f"✅ {name:25s} (port {port}) - healthy")
        else:
            print(f"⚠️  {name:25s} (port {port}) - status {resp.status_code}")
            all_healthy = False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name:25s} (port {port}) - not responding")
        all_healthy = False
    except requests.exceptions.Timeout:
        print(f"⏱️  {name:25s} (port {port}) - timeout")
        all_healthy = False
    except Exception as e:
        print(f"❌ {name:25s} (port {port}) - error: {e}")
        all_healthy = False

print()
if all_healthy:
    print("✅ All services ready!")
    sys.exit(0)
else:
    print("⚠️  Some services not ready, but continuing with demo...")
    sys.exit(0)  # Don't fail - demo can handle missing services

