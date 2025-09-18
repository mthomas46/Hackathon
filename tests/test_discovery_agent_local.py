#!/usr/bin/env python3
"""Local test for the enhanced Discovery Agent service.

This script runs the discovery agent locally and tests all the new endpoints.
"""

import asyncio
import os
import sys
import subprocess
import time
import requests
import signal
import atexit

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)


def start_service():
    """Start the discovery agent service locally."""
    print("🚀 Starting Discovery Agent service locally...")

    # Set environment variables
    env = os.environ.copy()
    env.update({
        'PYTHONPATH': project_root,
        'SERVICE_NAME': 'discovery-agent',
        'SERVICE_PORT': '5045',
        'REDIS_HOST': 'localhost',
        'ENVIRONMENT': 'development'
    })

    # Start the service
    main_py_path = os.path.join(project_root, 'services', 'discovery-agent', 'main.py')
    cmd = [sys.executable, main_py_path]
    process = subprocess.Popen(
        cmd,
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for service to start
    time.sleep(3)

    # Check if process is still running
    if process.poll() is None:
        print("✅ Service started successfully")
        return process
    else:
        stdout, stderr = process.communicate()
        print(f"❌ Service failed to start")
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        return None


def stop_service(process):
    """Stop the service process."""
    if process and process.poll() is None:
        print("🛑 Stopping service...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print("✅ Service stopped")


async def test_endpoints():
    """Test all the new endpoints."""
    base_url = "http://localhost:5045"
    results = []

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            results.append(("health", True))
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            results.append(("health", False))
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        results.append(("health", False))

    # Test ecosystem discovery
    try:
        response = requests.post(f"{base_url}/api/v1/discovery/ecosystem", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Ecosystem discovery working - found {data['data'].get('total_tools_discovered', 0)} tools")
                results.append(("ecosystem_discovery", True))
            else:
                print(f"❌ Ecosystem discovery returned success=false")
                results.append(("ecosystem_discovery", False))
        else:
            print(f"❌ Ecosystem discovery failed: {response.status_code}")
            results.append(("ecosystem_discovery", False))
    except Exception as e:
        print(f"❌ Ecosystem discovery error: {e}")
        results.append(("ecosystem_discovery", False))

    # Test orchestrator registration
    try:
        response = requests.post(f"{base_url}/api/v1/orchestrator/register-tools", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Orchestrator registration working - registered {data['data'].get('registered_tools', 0)} tools")
                results.append(("orchestrator_registration", True))
            else:
                print(f"❌ Orchestrator registration returned success=false")
                results.append(("orchestrator_registration", False))
        else:
            print(f"❌ Orchestrator registration failed: {response.status_code}")
            results.append(("orchestrator_registration", False))
    except Exception as e:
        print(f"❌ Orchestrator registration error: {e}")
        results.append(("orchestrator_registration", False))

    # Test AI workflow creation
    try:
        workflow_request = {
            "task_description": "Analyze all documents and create a summary report",
            "name": "test_workflow"
        }
        response = requests.post(
            f"{base_url}/api/v1/workflows/create-ai",
            json=workflow_request,
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ AI workflow creation working")
                results.append(("ai_workflow_creation", True))
            else:
                print(f"❌ AI workflow creation returned success=false: {data.get('error', 'Unknown error')}")
                results.append(("ai_workflow_creation", False))
        else:
            print(f"❌ AI workflow creation failed: {response.status_code}")
            results.append(("ai_workflow_creation", False))
    except Exception as e:
        print(f"❌ AI workflow creation error: {e}")
        results.append(("ai_workflow_creation", False))

    # Test semantic analysis
    try:
        response = requests.post(f"{base_url}/api/v1/analysis/semantic", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Semantic analysis working - analyzed {data['data'].get('analyzed_tools', 0)} tools")
                results.append(("semantic_analysis", True))
            else:
                print(f"❌ Semantic analysis returned success=false")
                results.append(("semantic_analysis", False))
        else:
            print(f"❌ Semantic analysis failed: {response.status_code}")
            results.append(("semantic_analysis", False))
    except Exception as e:
        print(f"❌ Semantic analysis error: {e}")
        results.append(("semantic_analysis", False))

    # Test performance optimization
    try:
        response = requests.post(f"{base_url}/api/v1/optimization/performance", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Performance optimization working")
                results.append(("performance_optimization", True))
            else:
                print(f"❌ Performance optimization returned success=false")
                results.append(("performance_optimization", False))
        else:
            print(f"❌ Performance optimization failed: {response.status_code}")
            results.append(("performance_optimization", False))
    except Exception as e:
        print(f"❌ Performance optimization error: {e}")
        results.append(("performance_optimization", False))

    # Test registry endpoints
    try:
        response = requests.get(f"{base_url}/api/v1/registry/tools", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Registry tools query working - found {data['data'].get('count', 0)} tools")
                results.append(("registry_tools", True))
            else:
                print(f"❌ Registry tools query returned success=false")
                results.append(("registry_tools", False))
        else:
            print(f"❌ Registry tools query failed: {response.status_code}")
            results.append(("registry_tools", False))
    except Exception as e:
        print(f"❌ Registry tools query error: {e}")
        results.append(("registry_tools", False))

    # Test monitoring dashboard
    try:
        response = requests.get(f"{base_url}/api/v1/monitoring/dashboard", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Monitoring dashboard working")
                results.append(("monitoring_dashboard", True))
            else:
                print(f"❌ Monitoring dashboard returned success=false")
                results.append(("monitoring_dashboard", False))
        else:
            print(f"❌ Monitoring dashboard failed: {response.status_code}")
            results.append(("monitoring_dashboard", False))
    except Exception as e:
        print(f"❌ Monitoring dashboard error: {e}")
        results.append(("monitoring_dashboard", False))

    return results


async def main():
    """Main test function."""
    service_process = None

    try:
        # Start the service
        service_process = start_service()
        if not service_process:
            print("❌ Failed to start service")
            return False

        # Wait a bit more for service to be ready
        time.sleep(2)

        # Run tests
        print("\n🧪 Running endpoint tests...")
        print("=" * 50)

        results = await test_endpoints()

        # Summary
        print("\n" + "=" * 50)
        passed = sum(1 for _, success in results if success)
        total = len(results)

        print(f"📊 Test Results: {passed}/{total} endpoints working")

        if passed == total:
            print("🎉 ALL ENDPOINTS WORKING! Discovery Agent is fully functional.")
            return True
        else:
            failed_tests = [name for name, success in results if not success]
            print(f"❌ Failed endpoints: {', '.join(failed_tests)}")
            return False

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if service_process:
            stop_service(service_process)


if __name__ == "__main__":
    # Register cleanup handler
    def cleanup():
        print("\n🧹 Cleaning up...")
        # Any cleanup logic here

    atexit.register(cleanup)

    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
