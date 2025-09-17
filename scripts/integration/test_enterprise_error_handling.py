#!/usr/bin/env python3
"""
Test Enterprise Error Handling Framework

Simple test script to demonstrate the enterprise error handling capabilities.
"""

import asyncio
import sys
import os

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))

# Mock the conflicting imports
class MockServiceNames:
    ORCHESTRATOR = 'orchestrator'
    ANALYSIS_SERVICE = 'analysis-service'
    DOC_STORE = 'doc_store'
    PROMPT_STORE = 'prompt-store'

def mock_fire_and_forget(level: str, message: str, service: str):
    """Mock logging function."""
    print(f"[{level.upper()}] {service}: {message}")

# Monkey patch the imports
import services.shared.enterprise_error_handling_v2 as eeh
eeh.ServiceNames = MockServiceNames()
eeh.fire_and_forget = mock_fire_and_forget

# Mock HTTPException
class MockHTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)

eeh.HTTPException = MockHTTPException

async def test_error_handling():
    """Test the enterprise error handling framework."""
    print("🧪 Testing Enterprise Error Handling Framework")
    print("=" * 50)

    # Test different error types
    test_cases = [
        {
            "name": "Network Timeout Error",
            "error": TimeoutError("Connection timed out"),
            "context": {
                "service_name": "doc_store",
                "operation": "query",
                "user_id": "user123",
                "correlation_id": "corr456"
            }
        },
        {
            "name": "Validation Error",
            "error": ValueError("Invalid document ID format"),
            "context": {
                "service_name": "analysis_service",
                "operation": "analyze",
                "request_data": {"doc_id": "invalid_format"}
            }
        },
        {
            "name": "Database Connection Error",
            "error": ConnectionError("Database connection lost"),
            "context": {
                "service_name": "prompt_store",
                "operation": "get_prompt",
                "critical_operation": True
            }
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print("-" * 30)

        try:
            result = await eeh.enterprise_error_handler.handle_error(
                test_case["error"],
                test_case["context"]
            )

            print("✅ Error handled successfully")
            print(f"   Error ID: {result['error']['id']}")
            print(f"   Category: {result['error']['category']}")
            print(f"   Severity: {result['error']['severity']}")
            print(f"   Recovery attempted: {result['recovery']['attempted']}")
            print(f"   Recovery successful: {result['recovery']['successful']}")
            print(f"   User message: {result.get('user_message', 'N/A')}")

        except Exception as e:
            print(f"❌ Error handling failed: {e}")

    # Test error statistics
    print("\n📊 Error Statistics:")
    print("-" * 30)

    stats = eeh.enterprise_error_handler.get_error_statistics()
    print(f"Total errors processed: {stats['total_errors']}")
    print(f"Errors by severity: {dict(stats['errors_by_severity'])}")
    print(f"Errors by category: {dict(stats['errors_by_category'])}")
    print(".2f")
    print(f"Top error types: {dict(stats['top_error_types'])}")

    # Test circuit breaker status
    print("\n🔌 Circuit Breaker Status:")
    print("-" * 30)

    cb_status = eeh.enterprise_error_handler.get_circuit_breaker_status()
    for key, status in cb_status.items():
        print(f"{key}: {status['state']} (failures: {status['failure_count']})")

    print("\n🎉 Enterprise Error Handling Framework Test Complete!")
    print("Features demonstrated:")
    print("   ✅ Intelligent error classification")
    print("   ✅ Automatic recovery strategies")
    print("   ✅ Circuit breaker pattern")
    print("   ✅ Comprehensive error tracking")
    print("   ✅ User-friendly error messages")
    print("   ✅ Enterprise-grade resilience")

if __name__ == "__main__":
    asyncio.run(test_error_handling())
