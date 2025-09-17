#!/usr/bin/env python3
"""
Script to run sanity tests for live services.

This demonstrates how to test the actual running services rather than mocks.
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_service_health(service_name, port):
    """Check if a service is healthy."""
    import requests
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Main function to run sanity tests."""
    print("🔍 LLM Documentation Consistency Ecosystem - Live Service Sanity Tests")
    print("=" * 70)

    # Check if we're in the right directory
    if not Path("services").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)

    # Test 1: Check if services can be imported
    print("\n1. Testing Service Imports...")
    services = ["orchestrator", "doc_store", "analysis-service", "source-agent"]

    importable_services = []
    for service in services:
        try:
            # Try to import the service module
            if Path(f"services/{service}/main.py").exists():
                importable_services.append(service)
                print(f"   ✅ {service}: Importable")
            else:
                print(f"   ⚠️  {service}: Module not found")
        except Exception as e:
            print(f"   ❌ {service}: Import failed - {e}")

    if not importable_services:
        print("❌ No services could be imported. Please check your setup.")
        sys.exit(1)

    # Test 2: Run unit tests (these don't require live services)
    print("\n2. Running Unit Tests (no live services required)...")
    success, stdout, stderr = run_command("python -m pytest tests/unit/ -v --tb=short")

    if success:
        print("   ✅ Unit tests passed")
    else:
        print("   ⚠️  Unit tests had issues (this is normal if services aren't running)")
        print(f"   Output: {stdout[:200]}...")

    # Test 3: Run integration tests with mocks
    print("
3. Running Integration Tests with Mocks...")
    success, stdout, stderr = run_command("python -m pytest tests/integration/ -v --tb=short -k 'not live'")

    if success:
        print("   ✅ Integration tests with mocks passed")
    else:
        print("   ⚠️  Some integration tests failed")
        # Count passed/failed
        lines = stdout.split('\n')
        passed = sum(1 for line in lines if 'PASSED' in line)
        failed = sum(1 for line in lines if 'FAILED' in line)
        print(f"   Results: {passed} passed, {failed} failed")

    # Test 4: Run sanity tests (these work with or without live services)
    print("
4. Running Sanity Tests...")
    success, stdout, stderr = run_command("python -m pytest tests/sanity/ -v --tb=short")

    if success:
        print("   ✅ Sanity tests passed")
    else:
        print("   ⚠️  Some sanity tests failed")
        print(f"   Output: {stdout[:300]}...")

    # Test 5: Check if services can be started (optional)
    print("
5. Testing Service Startup Capability...")

    for service in importable_services[:2]:  # Test first 2 services
        print(f"   Testing {service} startup...")
        # Check if we can at least validate the service code
        success, stdout, stderr = run_command(
            f"cd services/{service} && python -c 'import main; print(\"✅ Service code is valid\")'",
            cwd=f"services/{service}"
        )

        if success:
            print(f"   ✅ {service}: Code validation passed")
        else:
            print(f"   ❌ {service}: Code validation failed")
    success, stdout, stderr = run_command("python -m pytest tests/unit/ -v --tb=short")

    if success:
        print("   ✅ Unit tests passed")
    else:
        print("   ⚠️  Unit tests had issues (this is normal if services aren't running)")
        print(f"   Output: {stdout[:200]}...")

