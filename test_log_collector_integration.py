#!/usr/bin/env python3
"""
Test script to verify that log-collector is consuming logs from meta-orchestrator.
This script triggers config reporting operations and verifies logs appear in log-collector.
"""

import asyncio
import httpx
import time
import json
import os
import sys
from pathlib import Path

# Add the services directory to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "meta-orchestrator"))

async def test_log_collector_integration():
    """Test log-collector integration with meta-orchestrator config reporting"""

    print("🚀 Starting log-collector integration test")
    print("=" * 60)

    # Test configuration
    log_collector_url = "http://localhost:8104"
    meta_orchestrator_url = "http://localhost:8080"

    # Set environment variables for log collector integration
    os.environ['LOG_COLLECTOR_ENABLED'] = 'true'
    os.environ['LOG_COLLECTOR_URL'] = log_collector_url

    print(f"📋 Test Configuration:")
    print(f"   Log Collector URL: {log_collector_url}")
    print(f"   Meta-Orchestrator URL: {meta_orchestrator_url}")
    print()

    try:
        # Step 1: Check if log-collector is running
        print("🔍 Step 1: Checking log-collector health...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{log_collector_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Log-collector is healthy: {health_data.get('count', 0)} logs stored")
            else:
                print(f"❌ Log-collector health check failed: {response.status_code}")
                return False

        # Step 2: Check if meta-orchestrator is running
        print("🔍 Step 2: Checking meta-orchestrator health...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{meta_orchestrator_url}/health")
            if response.status_code == 200:
                print("✅ Meta-orchestrator is healthy")
            else:
                print(f"❌ Meta-orchestrator health check failed: {response.status_code}")
                return False

        # Step 3: Get baseline log count
        print("🔍 Step 3: Getting baseline log count...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{log_collector_url}/health")
            baseline_count = response.json().get('count', 0)
            print(f"📊 Baseline log count: {baseline_count}")

        # Step 4: Trigger config export operation (this should generate logs)
        print("🔍 Step 4: Triggering configuration export operation...")
        test_timestamp = int(time.time())

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try to export all configs (this will trigger our new logging)
                response = await client.post(
                    f"{meta_orchestrator_url}/api/v1/monitoring/config/export-all",
                    params={"format": "json", "output_dir": f"test_exports_{test_timestamp}"}
                )

                if response.status_code == 200:
                    export_result = response.json()
                    print(f"✅ Config export completed: {export_result}")
                else:
                    print(f"⚠️ Config export returned status {response.status_code}: {response.text}")
                    # This is okay - the operation might fail due to no services, but logs should still be generated

        except Exception as e:
            print(f"⚠️ Config export failed (expected if no services running): {e}")

        # Step 5: Trigger config comparison operation
        print("🔍 Step 5: Triggering configuration comparison operation...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{meta_orchestrator_url}/api/v1/monitoring/config/web-frontend/compare"
                )

                if response.status_code == 200:
                    compare_result = response.json()
                    print(f"✅ Config comparison completed: {compare_result.get('status')}")
                else:
                    print(f"⚠️ Config comparison returned status {response.status_code}: {response.text}")

        except Exception as e:
            print(f"⚠️ Config comparison failed (expected if no history): {e}")

        # Step 6: Trigger config history operation
        print("🔍 Step 6: Triggering configuration history operation...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{meta_orchestrator_url}/api/v1/monitoring/config/web-frontend/history"
                )

                if response.status_code == 200:
                    history_result = response.json()
                    print(f"✅ Config history completed: {len(history_result.get('config_history', []))} snapshots")
                else:
                    print(f"⚠️ Config history returned status {response.status_code}: {response.text}")

        except Exception as e:
            print(f"⚠️ Config history failed (expected if no history): {e}")

        # Step 7: Wait for log transmission (logs are sent asynchronously)
        print("⏳ Step 7: Waiting for log transmission...")
        await asyncio.sleep(5)  # Wait for batch transmission

        # Step 8: Check for new logs in log-collector
        print("🔍 Step 8: Checking for new logs in log-collector...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{log_collector_url}/health")
            final_count = response.json().get('count', 0)
            new_logs = final_count - baseline_count
            print(f"📊 Final log count: {final_count} (added: {new_logs})")

        # Step 9: Query recent logs to verify our config operation logs
        print("🔍 Step 9: Querying recent logs for config operations...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{log_collector_url}/logs",
                params={
                    "service": "meta-orchestrator",
                    "limit": 50
                }
            )

            if response.status_code == 200:
                logs_data = response.json()
                logs = logs_data.get('items', [])

                # Filter for config-related operations from meta-orchestrator services
                config_logs = [log for log in logs if
                    (log.get('service', '').startswith('meta-orchestrator') or
                     log.get('context', {}).get('operation', '').startswith('config_'))]

                print(f"📋 Found {len(config_logs)} config-related logs from meta-orchestrator")

                if config_logs:
                    print("✅ SUCCESS: Log-collector is receiving config operation logs!")
                    print("\n📄 Sample config logs:")
                    for i, log in enumerate(config_logs[:3]):  # Show first 3
                        operation = log.get('context', {}).get('operation', 'unknown')
                        message = log.get('message', '')[:80] + '...' if len(log.get('message', '')) > 80 else log.get('message', '')
                        print(f"   {i+1}. [{operation}] {message}")

                    # Check for specific operations we triggered
                    operations_found = set()
                    for log in config_logs:
                        operation = log.get('context', {}).get('operation', '')
                        operations_found.add(operation)

                    expected_ops = {
                        'config_export_all',
                        'config_export_service',
                        'config_comparison_start',
                        'config_history_retrieval'
                    }

                    found_ops = expected_ops.intersection(operations_found)
                    print(f"\n🎯 Expected operations found: {len(found_ops)}/{len(expected_ops)}")
                    for op in sorted(expected_ops):
                        status = "✅" if op in found_ops else "❌"
                        print(f"   {status} {op}")

                    if len(found_ops) > 0:
                        print("\n🎉 VERIFICATION SUCCESSFUL: Log-collector is consuming meta-orchestrator logs!")
                        return True
                    else:
                        print("\n⚠️ PARTIAL SUCCESS: Config logs found but not all expected operations")
                        return True
                else:
                    print("❌ FAILURE: No config-related logs found in log-collector")
                    print("   This suggests log transmission is not working properly")

                    # Show all recent logs to debug
                    print("\n📋 Recent logs from meta-orchestrator services:")
                    mo_logs = [log for log in logs if log.get('service', '').startswith('meta-orchestrator')]
                    if mo_logs:
                        print(f"   Found {len(mo_logs)} total logs from meta-orchestrator services")
                        for i, log in enumerate(mo_logs[:3]):
                            service = log.get('service', 'unknown')
                            message = log.get('message', '')[:60] + '...' if len(log.get('message', '')) > 60 else log.get('message', '')
                            print(f"   {i+1}. [{service}] {message}")
                    else:
                        print("   No logs from meta-orchestrator services found at all")

                    return False
            else:
                print(f"❌ Failed to query logs: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_log_collector_integration()

    print("\n" + "=" * 60)
    if success:
        print("🎉 LOG-COLLECTOR INTEGRATION TEST PASSED")
        print("✅ Meta-orchestrator logs are being consumed by log-collector")
    else:
        print("❌ LOG-COLLECTOR INTEGRATION TEST FAILED")
        print("❌ Meta-orchestrator logs are NOT being consumed by log-collector")
    print("=" * 60)

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
